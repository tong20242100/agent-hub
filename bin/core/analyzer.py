"""
analyzer.py — 日志驱动的自我诊断引擎

读取 knowledge/logs/evolution_*.jsonl，从运行数据中提取信号：
- 工具失败率 / audit 静默失败
- 高频连续调用（AI 在反复尝试同一件事）
- 耗时异常（P95 vs 中位数）
- 零调用工具（候选下线）
- 自动生成 ai_hints 改进建议
"""

import json
import logging
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent-hub.analyzer")

# ── 常量 ──────────────────────────────────────────────────────────────────────

STALE_DAYS = 90          # 超过此天数零调用 → 候选下线（专用工具可能低频，阈值设宽）
BURST_WINDOW_SEC = 60    # 同一工具在此窗口内连续调用 N 次 → 视为 burst
BURST_THRESHOLD = 3      # burst 阈值
SLOW_RATIO = 5.0         # duration > median * SLOW_RATIO → 慢调用


# ── 数据加载 ──────────────────────────────────────────────────────────────────

def load_logs(log_dir: Path) -> list[dict[str, Any]]:
    """加载所有 evolution_*.jsonl，按时间升序排列"""
    entries: list[dict[str, Any]] = []
    for f in sorted(log_dir.glob("evolution_*.jsonl")):
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning("Skipping malformed log line in %s: %s", f.name, e)
        except OSError as e:
            logger.error("Cannot read log file %s: %s", f, e)
    entries.sort(key=lambda x: x.get("timestamp", ""))
    return entries


# ── 分析器 ────────────────────────────────────────────────────────────────────

class LogAnalyzer:
    def __init__(self, entries: list[dict[str, Any]], manifest_tools: list[str]):
        self.entries = entries
        self.manifest_tools = set(manifest_tools)
        self._now = datetime.now()

    # ── 1. 失败率分析 ─────────────────────────────────────────────────────────

    def failure_report(self) -> list[dict[str, Any]]:
        """
        两类失败：
        - status != success（命令本身失败）
        - audit.ok == False（命令成功但输出为空/含错误关键词）
        """
        counters: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "status_fail": 0, "audit_fail": 0}
        )
        for e in self.entries:
            tool = e.get("tool", "unknown")
            counters[tool]["total"] += 1
            if e.get("status") != "success":
                counters[tool]["status_fail"] += 1
            if not e.get("audit", {}).get("ok", True):
                counters[tool]["audit_fail"] += 1

        results = []
        for tool, c in counters.items():
            total = c["total"]
            fail = c["status_fail"] + c["audit_fail"]
            if fail == 0:
                continue
            results.append({
                "tool": tool,
                "total_calls": total,
                "status_failures": c["status_fail"],
                "audit_failures": c["audit_fail"],
                "failure_rate": round(fail / total, 2),
                "severity": "🔴 HIGH" if fail / total >= 0.5 else "🟡 MEDIUM",
            })
        return sorted(results, key=lambda x: x["failure_rate"], reverse=True)

    # ── 2. Burst 检测（AI 在反复重试同一工具）────────────────────────────────

    def burst_report(self) -> list[dict[str, Any]]:
        """
        在 BURST_WINDOW_SEC 秒内同一工具被调用 >= BURST_THRESHOLD 次
        → AI 可能在反复尝试，说明工具输出不够清晰或 ai_hints 不准确
        """
        bursts = []
        tool_times: dict[str, list[datetime]] = defaultdict(list)

        for e in self.entries:
            tool = e.get("tool", "unknown")
            ts_str = e.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
            except ValueError:
                continue
            tool_times[tool].append(ts)

        for tool, times in tool_times.items():
            times.sort()
            # 滑动窗口
            for i in range(len(times)):
                window = [
                    t for t in times[i:]
                    if (t - times[i]).total_seconds() <= BURST_WINDOW_SEC
                ]
                if len(window) >= BURST_THRESHOLD:
                    bursts.append({
                        "tool": tool,
                        "burst_count": len(window),
                        "window_start": times[i].isoformat(),
                        "suggestion": (
                            f"工具在 {BURST_WINDOW_SEC}s 内被调用 {len(window)} 次，"
                            "建议检查 ai_hints.avoid 是否明确了单次调用的边界条件"
                        ),
                    })
                    break  # 每个工具只报告一次最大 burst

        return sorted(bursts, key=lambda x: x["burst_count"], reverse=True)

    # ── 3. 耗时分析 ───────────────────────────────────────────────────────────

    def latency_report(self) -> list[dict[str, Any]]:
        """找出耗时异常的工具（相对于自身中位数的倍数）"""
        tool_durations: dict[str, list[float]] = defaultdict(list)
        for e in self.entries:
            d = e.get("duration_ms")
            if d is not None:
                tool_durations[e.get("tool", "unknown")].append(float(d))

        results = []
        for tool, durations in tool_durations.items():
            if len(durations) < 2:
                continue
            median = statistics.median(durations)
            p95 = sorted(durations)[int(len(durations) * 0.95)]
            max_d = max(durations)
            if median > 0 and max_d / median >= SLOW_RATIO:
                results.append({
                    "tool": tool,
                    "calls": len(durations),
                    "median_ms": round(median, 1),
                    "p95_ms": round(p95, 1),
                    "max_ms": round(max_d, 1),
                    "slow_ratio": round(max_d / median, 1),
                    "suggestion": (
                        f"最慢调用是中位数的 {round(max_d / median, 1)}x，"
                        "建议检查网络超时或增加 timeout 参数"
                    ),
                })
        return sorted(results, key=lambda x: x["slow_ratio"], reverse=True)

    # ── 4. 零调用工具（候选下线）─────────────────────────────────────────────

    def stale_tools_report(self, stale_days: int = STALE_DAYS) -> list[dict[str, Any]]:
        """
        在 manifest 中注册但从未出现在日志里的工具，或超过 stale_days 天未调用的工具。

        注意：低频专用工具（如 lighthouse_audit）不应被误判。
        只有「从未调用」才是强信号；「低频」只是弱信号，需结合 stale_days 阈值判断。
        """
        cutoff = self._now - timedelta(days=stale_days)

        # 统计每个工具的最后调用时间
        last_seen: dict[str, datetime] = {}
        for e in self.entries:
            tool = e.get("tool", "")
            ts_str = e.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str)
                if tool not in last_seen or ts > last_seen[tool]:
                    last_seen[tool] = ts
            except ValueError:
                continue

        stale = []
        for tool in self.manifest_tools:
            if tool not in last_seen:
                # 从未调用 — 强信号
                stale.append({
                    "tool": tool,
                    "last_seen": "从未调用",
                    "signal": "NEVER_CALLED",
                    "suggestion": "从未出现在执行日志中，建议确认是否仍有使用场景",
                })
            elif last_seen[tool] < cutoff:
                # 超过阈值未调用 — 弱信号，仅供参考
                days_ago = (self._now - last_seen[tool]).days
                stale.append({
                    "tool": tool,
                    "last_seen": last_seen[tool].isoformat()[:10],
                    "days_since": days_ago,
                    "signal": "LOW_FREQUENCY",
                    "suggestion": f"{days_ago} 天未调用（阈值 {stale_days} 天），低频专用工具可忽略此提示",
                })

        # 优先展示从未调用的，其次按最后调用时间排序
        return sorted(
            stale,
            key=lambda x: (0 if x["signal"] == "NEVER_CALLED" else 1, x.get("days_since", 0)),
            reverse=False,
        )

    # ── 5. ai_hints 改进建议（基于失败 + burst 信号）─────────────────────────

    def hints_improvement_report(
        self,
        failures: list[dict],
        bursts: list[dict],
    ) -> list[dict[str, Any]]:
        """
        综合失败率和 burst 信号，生成具体的 ai_hints 改进建议
        """
        suggestions: dict[str, list[str]] = defaultdict(list)

        for f in failures:
            tool = f["tool"]
            if f["audit_failures"] > 0:
                suggestions[tool].append(
                    "audit.ok=False 说明工具输出为空或含错误关键词，"
                    "检查命令路径和依赖是否正常"
                )
            if f["status_failures"] > 0:
                suggestions[tool].append(
                    "status=failure 说明命令执行失败，"
                    "建议在 ai_hints.self_check 中加入前置条件检查"
                )

        for b in bursts:
            tool = b["tool"]
            suggestions[tool].append(
                "高频 burst 调用：ai_hints.avoid 应明确"
                "「单次调用已能满足需求时不要重复调用」"
            )

        return [
            {"tool": tool, "improvements": items}
            for tool, items in suggestions.items()
        ]

    # ── 汇总入口 ──────────────────────────────────────────────────────────────

    def run(self, stale_days: int = STALE_DAYS) -> dict[str, Any]:
        failures = self.failure_report()
        bursts = self.burst_report()
        latency = self.latency_report()
        stale = self.stale_tools_report(stale_days=stale_days)
        hints = self.hints_improvement_report(failures, bursts)

        total = len(self.entries)
        healthy = sum(
            1 for e in self.entries
            if e.get("status") == "success" and e.get("audit", {}).get("ok", True)
        )

        return {
            "meta": {
                "analyzed_at": self._now.isoformat(),
                "total_log_entries": total,
                "healthy_calls": healthy,
                "health_rate": round(healthy / total, 2) if total else 0,
                "registered_tools": len(self.manifest_tools),
            },
            "failures": failures,
            "bursts": bursts,
            "latency": latency,
            "stale_tools": stale,
            "hints_improvements": hints,
        }


# ── 公开入口 ──────────────────────────────────────────────────────────────────

def analyze_logs(project_root: Path, stale_days: int = STALE_DAYS) -> dict[str, Any]:
    log_dir = project_root / "knowledge" / "logs"
    manifest_path = project_root / "knowledge" / "tools_manifest.json"

    entries = load_logs(log_dir)
    if not entries:
        return {"error": "没有找到任何日志记录，请先运行一些工具调用"}

    manifest_tools: list[str] = []
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_tools = [t["name"] for t in data.get("tools", [])]
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Cannot load manifest for stale tool detection: %s", e)

    analyzer = LogAnalyzer(entries, manifest_tools)
    return analyzer.run(stale_days=stale_days)
