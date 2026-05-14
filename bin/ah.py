#!/usr/bin/env python3
import click
import json
import logging
import os
import subprocess
import shutil
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent-hub.cli")

# 路径管理与核心导入
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from bin.core.auditor import audit_skill
    from bin.core.discovery import run_global_discovery, LocalFileScanner
    from bin.core.manager import (
        scan_all_agents,
        remove_skill,
        check_skill_update,
        onboard_skill,
        _sync_global_onboard,
    )
    from bin.core.evaluator import evaluate_hints
    from bin.core.analyzer import analyze_logs
except ImportError:
    # 尝试后备方案 (针对直接在 bin 目录下运行)
    try:
        sys.path.append(str(PROJECT_ROOT / "bin"))
        from core.auditor import audit_skill
        from core.discovery import run_global_discovery, LocalFileScanner
        from core.manager import (
            scan_all_agents,
            remove_skill,
            check_skill_update,
            onboard_skill,
            _sync_global_onboard,
        )
        from core.evaluator import evaluate_hints
        from core.analyzer import analyze_logs
    except ImportError as e:
        print(f"❌ 核心模块导入失败: {e}", file=sys.stderr)

        def audit_skill(*args, **kwargs):
            return ["模块不可用"], []

        def scan_all_agents():
            return {}

        def analyze_logs(*args, **kwargs):
            return {"error": "模块不可用"}


@click.group()
def cli():
    """Agent-Hub: 跨平台 Agent 技能中枢"""
    pass


@cli.command()
@click.argument("path")
def onboard(path):
    """正式上线一个新技能：移动/链接、注册清单、清理缓存"""
    ok, msg = onboard_skill(path)
    if ok:
        click.echo(f"✅ {msg}")
    else:
        click.echo(f"❌ {msg}")


@cli.command()
def scan():
    """快速扫描已注册的 Agent 技能目录"""
    skills = scan_all_agents()
    click.echo(f"🔍 发现 {len(skills)} 个技能项目。")


@cli.command()
@click.option("--json", "-j", "json_output", is_flag=True)
def list(json_output):
    """聚合显示本机所有已注册技能"""
    skills = scan_all_agents()
    if json_output:
        click.echo(
            json.dumps(
                {
                    n: {
                        "type": a.type,
                        "agents": a.agents,
                        "locations": [
                            {"agent": loc.agent, "path": loc.path, "version": loc.version}
                            for loc in a.locations
                        ],
                    }
                    for n, a in skills.items()
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        type_icons = {"tool": "⚙️", "cognitive": "🧠", "knowledge": "📖"}
        for name, agg in sorted(skills.items()):
            icon = type_icons.get(agg.type, "❓")
            click.echo(f"• {icon} {name} ({', '.join(agg.agents)})")


@cli.command()
@click.argument("skill")
@click.option("--force", is_flag=True)
def remove(skill, force):
    """从系统中彻底卸载技能"""
    ok, res = remove_skill(skill, scan_all_agents(), force=force)
    if ok:
        click.echo(f"✅ 已移除: {', '.join(res['removed'])}")


@cli.command()
@click.argument("skill", required=False)
def status(skill):
    """查看技能分布与健康状态"""
    skills = scan_all_agents()
    if skill:
        if skill not in skills:
            click.echo("❌ 技能不存在")
            return
        agg = skills[skill]
        type_icons = {"tool": "⚙️", "cognitive": "🧠", "knowledge": "📖"}
        click.echo(f"技能: {type_icons.get(agg.type, '❓')} {skill} (Type: {agg.type})")
        for loc in agg.locations:
            click.echo(f"  {loc.agent}: {loc.version} -> {loc.path}")
    else:
        type_icons = {"tool": "⚙️", "cognitive": "🧠", "knowledge": "📖"}
        for name, agg in sorted(skills.items()):
            icon = type_icons.get(agg.type, "❓")
            click.echo(
                f"{'✅' if len(agg.agents) > 1 else '⚠️'} {icon} {name}: {', '.join(agg.agents)}"
            )


@cli.command()
@click.option(
    "--install", "-i", "do_install", is_flag=True, help="发现更新后自动执行安装与同步"
)
def update(do_install):
    """检测并自动更新所有技能"""
    click.echo("🔍 检测中...\n")
    for d in (PROJECT_ROOT / "skills").glob("*/SCHEMA.json"):
        skill_name = d.parent.name
        info = check_skill_update(skill_name, d)
        if info is None:
            click.echo(f"⚠️ {skill_name}: 无法检测更新状态")
            continue
        if info.has_update:
            click.echo(
                f"🔴 {info.skill_name}: {info.current_version} -> {info.latest_version}"
            )
            if do_install:
                click.echo(f"  🚀 正在更新 {skill_name}...")
                install_cmd = [
                    str(PROJECT_ROOT / "bin" / "skill_update_install"),
                    skill_name,
                ]
                try:
                    res = subprocess.run(
                        install_cmd, capture_output=True, text=True, timeout=120
                    )
                    if res.returncode == 0:
                        _sync_global_onboard(d.parent)
                        click.echo(f"  ✅ {skill_name} 更新成功并已重新同步")
                    else:
                        click.echo(f"  ❌ 更新失败: {res.stderr}")
                except subprocess.TimeoutExpired:
                    click.echo("  ❌ 更新超时")
                    logger.error("Update command timed out for %s", skill_name)
        else:
            click.echo(f"✅ {info.skill_name} 已是最新")


@cli.command()
@click.option("--fix", is_flag=True)
def check(fix):
    """合规性审计"""
    click.echo("🔍 启动合规性审计...\n")
    for d in sorted((PROJECT_ROOT / "skills").iterdir()):
        if d.is_dir():
            err, warn = audit_skill(d, fix=fix)
            click.echo(f"{'❌' if err else '✅'} {d.name}")
            if fix and warn and "已尝试自动修复" in "".join(warn):
                _sync_global_onboard(d)
                click.echo("  ✨ 已同步更新至全局清单")


@cli.command()
def eval():
    """评估工具 Hint 质量与语义冲突"""
    click.echo("🧪 启动 Hint 质量压力测试...\n")
    manifest_path = PROJECT_ROOT / "knowledge" / "tools_manifest.json"
    report = evaluate_hints(manifest_path)

    if "error" in report:
        click.echo(f"❌ 评估失败: {report['error']}")
        return

    s = report["summary"]
    click.echo(
        f"📊 汇总报告: 总工具 {s['total_tools']} | 完美 Hint {s['perfect_score']} | 高风险 {s['at_risk']}"
    )

    if report["conflicts"]:
        click.echo("\n🚨 发现语义冲突 (Triggers 重叠):")
        for c in report["conflicts"]:
            click.echo(
                f"  • '{c['trigger']}' 被 {len(c['tools'])} 个工具共有: {', '.join(c['tools'])}"
            )

    risks = [d for d in report["diagnostics"] if d["score"] < 100]
    if risks:
        click.echo("\n⚠️ 质量改进建议:")
        for r in sorted(risks, key=lambda x: x["score"]):
            click.echo(f"  • {r['tool']} [{r['score']}分]: {', '.join(r['issues'])}")
    else:
        click.echo("\n✅ 所有工具 Hint 质量表现优异。")


@cli.command()
@click.argument("path", required=False)
@click.option("--onboard", "-o", "onboard_name", help="一键上线探测到的指定技能")
def discover(path, onboard_name):
    """全域探测其他 Agent 技能并支持一键上线"""
    res = run_global_discovery()
    all_discovered = []
    for p, items in res.items():
        click.echo(f"🔹 {p}: {[i['name'] for i in items]}")
        all_discovered.extend(items)

    if path:
        found = LocalFileScanner("Local").scan(Path(path))
        for r in found:
            click.echo(f"✨ 发现: {r['name']} -> {r['path']}")
            all_discovered.append(r)

    if onboard_name:
        target = next((i for i in all_discovered if i["name"] == onboard_name), None)
        if target and "path" in target:
            ok, msg = onboard_skill(target["path"])
            click.echo(f"{'✅' if ok else '❌'} {msg}")
        elif target:
            from bin.core.manager import AGENT_PATHS

            platform_name = target["platform"].lower()
            if platform_name in AGENT_PATHS:
                for p in AGENT_PATHS[platform_name]:
                    potential = Path(p).expanduser() / onboard_name
                    if potential.exists():
                        ok, msg = onboard_skill(str(potential))
                        click.echo(f"{'✅' if ok else '❌'} {msg}")
                        return
            click.echo(f"❌ 无法确定技能 '{onboard_name}' 的物理路径，无法自动 onboard")
        else:
            click.echo(f"❌ 未在探测结果中找到技能: {onboard_name}")


@cli.command()
@click.option("--force", is_flag=True, help="覆盖现有链接")
def link(force):
    """将 skills-cognitive 中的认知技能链接到全局目录，使其跨平台可用"""
    skills = scan_all_agents()
    target_dir = Path.home() / ".agents" / "skills" / "agent-hub-cognitive"
    target_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for name, agg in skills.items():
        if agg.type == "cognitive":
            loc = next(
                (
                    loc_item
                    for loc_item in agg.locations
                    if loc_item.agent == "agent-hub"
                ),
                None,
            )
            if loc:
                src = Path(loc.path)
                dst = target_dir / name
                if dst.exists():
                    if force:
                        if dst.is_symlink():
                            dst.unlink()
                        else:
                            shutil.rmtree(dst)
                    else:
                        click.echo(f"⚠️ {name} 已存在，跳过。使用 --force 覆盖。")
                        continue

                os.symlink(src, dst)
                click.echo(f"🔗 链接认知技能: {name}")
                count += 1

    click.echo(f"\n✅ 已成功链接 {count} 个认知技能到 {target_dir}")
    click.echo("💡 现在这些技能可以在 Claude Code / Gemini CLI 中自动识别。")


@cli.command()
@click.option("--json", "-j", "json_output", is_flag=True, help="输出原始 JSON 报告")
@click.option("--fix", is_flag=True, help="自动将 hints 改进建议写入对应 SCHEMA.json")
@click.option("--days", default=90, show_default=True, help="低频工具告警阈值（天）。专用工具可调高此值或忽略 LOW_FREQUENCY 提示")
def analyze(json_output, fix, days):
    """📊 日志驱动的自我诊断：失败率、burst 调用、耗时异常、零调用工具"""
    report = analyze_logs(PROJECT_ROOT, stale_days=days)

    if "error" in report:
        click.echo(f"❌ {report['error']}")
        return

    if json_output:
        click.echo(json.dumps(report, ensure_ascii=False, indent=2))
        return

    meta = report["meta"]
    health_pct = int(meta["health_rate"] * 100)
    health_icon = "✅" if health_pct >= 90 else ("🟡" if health_pct >= 70 else "🔴")
    click.echo(
        f"\n{health_icon} 系统健康度: {health_pct}%  "
        f"({meta['healthy_calls']}/{meta['total_log_entries']} 次调用正常) "
        f"| 注册工具: {meta['registered_tools']} 个\n"
    )

    # ── 失败率 ────────────────────────────────────────────────────────────────
    if report["failures"]:
        click.echo("🔴 工具失败报告:")
        for f in report["failures"]:
            click.echo(
                f"  • {f['severity']}  {f['tool']}  "
                f"失败率 {int(f['failure_rate']*100)}%  "
                f"(status_fail={f['status_failures']}, audit_fail={f['audit_failures']}, "
                f"total={f['total_calls']})"
            )
    else:
        click.echo("✅ 无工具失败记录")

    # ── Burst 调用 ────────────────────────────────────────────────────────────
    click.echo("")
    if report["bursts"]:
        click.echo("⚡ Burst 调用检测（AI 可能在反复重试）:")
        for b in report["bursts"]:
            click.echo(
                f"  • {b['tool']}  在 60s 内调用 {b['burst_count']} 次  "
                f"(首次: {b['window_start'][:19]})"
            )
            click.echo(f"    💡 {b['suggestion']}")
    else:
        click.echo("✅ 无异常 burst 调用")

    # ── 耗时异常 ──────────────────────────────────────────────────────────────
    click.echo("")
    if report["latency"]:
        click.echo("🐢 耗时异常工具:")
        for lat in report["latency"]:
            click.echo(
                f"  • {lat['tool']}  中位数 {lat['median_ms']}ms → 最慢 {lat['max_ms']}ms  "
                f"({lat['slow_ratio']}x)"
            )
            click.echo(f"    💡 {lat['suggestion']}")
    else:
        click.echo("✅ 无耗时异常")

    # ── 零调用工具 ────────────────────────────────────────────────────────────
    click.echo("")
    never_called = [s for s in report["stale_tools"] if s["signal"] == "NEVER_CALLED"]
    low_freq = [s for s in report["stale_tools"] if s["signal"] == "LOW_FREQUENCY"]

    if never_called:
        click.echo("🚫 从未调用的工具（强信号，建议核查）:")
        for s in never_called[:10]:
            click.echo(f"  • {s['tool']}")
        if len(never_called) > 10:
            click.echo(f"  ... 还有 {len(never_called) - 10} 个，用 --json 查看完整列表")
    else:
        click.echo("✅ 所有注册工具均有调用记录")

    if low_freq:
        click.echo(f"\n💤 低频工具（>{days}天未调用，专用工具可忽略）:")
        for s in low_freq[:5]:
            click.echo(f"  • {s['tool']}  最后调用: {s['last_seen']} ({s['days_since']}天前)")
        if len(low_freq) > 5:
            click.echo(f"  ... 还有 {len(low_freq) - 5} 个")

    # ── ai_hints 改进建议 ─────────────────────────────────────────────────────
    click.echo("")
    if report["hints_improvements"]:
        click.echo("🧠 ai_hints 改进建议:")
        for h in report["hints_improvements"]:
            click.echo(f"  • {h['tool']}:")
            for imp in h["improvements"]:
                click.echo(f"    - {imp}")

        if fix:
            click.echo("\n🔧 --fix 模式：将改进建议写入 SCHEMA.json 的 ai_hints.notes...")
            _apply_hints_fixes(report["hints_improvements"], PROJECT_ROOT)
    else:
        click.echo("✅ 无 ai_hints 改进建议")

    click.echo(f"\n📅 分析时间: {meta['analyzed_at'][:19]}")
    click.echo("💡 使用 `ah analyze --json` 获取完整机器可读报告")
    click.echo("💡 使用 `ah analyze --fix` 自动将建议写入 SCHEMA.json")


def _apply_hints_fixes(improvements: list, project_root: Path) -> None:
    """将 analyzer 的改进建议追加到对应 SCHEMA.json 的 ai_hints.notes 字段"""
    import json as _json

    for item in improvements:
        tool_name = item["tool"]
        # 在 skills/ 下找到包含此工具的 SCHEMA.json
        for schema_path in (project_root / "skills").glob("*/SCHEMA.json"):
            try:
                data = _json.loads(schema_path.read_text(encoding="utf-8"))
                if tool_name in data.get("tools", {}):
                    tool_def = data["tools"][tool_name]
                    hints = tool_def.setdefault("ai_hints", {})
                    existing_notes = hints.get("notes", [])
                    new_notes = [
                        n for n in item["improvements"]
                        if n not in existing_notes
                    ]
                    if new_notes:
                        hints["notes"] = existing_notes + new_notes
                        schema_path.write_text(
                            _json.dumps(data, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        click.echo(f"  ✅ 已更新 {schema_path.parent.name}/{tool_name}")
                    break
            except (OSError, _json.JSONDecodeError) as e:
                logger.warning("Cannot apply fix to %s: %s", schema_path, e)


if __name__ == "__main__":
    cli()
