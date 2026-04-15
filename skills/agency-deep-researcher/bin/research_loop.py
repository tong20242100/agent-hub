#!/usr/bin/env python3
"""
研究编排器 v7.0 - 先确认需求，再多源搜索，生成有实际价值的报告

核心能力：
1. 需求确认：先理解用户背景和期望，再执行搜索
2. 多源搜索：Tavily + GitHub + Twitter + Reddit 并行
3. 智能抓取：优先抓取 L1 来源全文（GitHub 源码、官方文档、学术论文）
4. 三维评估：覆盖度 / 深度 / 可操作性，三项都达标才算充分
5. 交叉验证：对关键信息多源核实

用法:
    python3 research_loop.py "研究主题"                    # 交互模式（先确认再搜索）
    python3 research_loop.py "研究主题" --no-interactive   # 自动模式（Agent 调用）
    python3 research_loop.py "研究主题" --max-iterations 4 # 增加迭代深度
    python3 research_loop.py --resume <thread_id>          # 恢复会话
    python3 research_loop.py --list                        # 列出历史会话
"""

__version__ = "7.0"
import json
import argparse
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field, asdict
import uuid
import concurrent.futures

# =============================================================================
# 路径配置
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "model_router.json"
CHECKPOINT_DIR = PROJECT_ROOT / "knowledge" / ".research_checkpoints"
RESEARCH_DIR = PROJECT_ROOT / "knowledge" / "research"

# 工具路径
BIN_DIR = PROJECT_ROOT / "bin"
SEARCH_BIN = BIN_DIR / "search"
SCRAPE_BIN = BIN_DIR / "scrape"
STEALTH_BIN = BIN_DIR / "scrapling-stealth"
LIGHTPANDA_BIN = BIN_DIR / "lightpanda"
MEMORY_BIN = BIN_DIR / "memory"
CROSS_VERIFY_BIN = BIN_DIR / "cross-verify"

# 外部工具
GH_BIN = Path(shutil.which("gh") or "/opt/homebrew/bin/gh")
XREACH_BIN = Path(shutil.which("xreach") or "/opt/homebrew/bin/xreach")

DEFAULT_BASE_URL = "http://127.0.0.1:18788/v1"
DEFAULT_MODEL = "moonshotai/kimi-k2-thinking"  # 带思考模式，适合研究任务

# 证据等级域名映射
# L1: 官方文档、学术论文、源码仓库（可验证的实证来源）
L1_DOMAINS = [
    "github.com",
    "docs.python.org",
    "arxiv.org",
    "dl.acm.org",
    "ieee.org",
    "springer.com",
]
# L2: 权威社区、技术博客（有审核机制或社区共识）
L2_DOMAINS = [
    "stackoverflow.com",
    "medium.com",
    "dev.to",
    "reddit.com",
    "news.ycombinator.com",
    "x.com",
    "twitter.com",
]

# 需要反爬的域名
STEALTH_DOMAINS = ["xiaohongshu.com", "zhihu.com", "weibo.com", "juejin.cn"]


# =============================================================================
# 数据结构
# =============================================================================


@dataclass
class Source:
    """单个来源"""

    url: str = ""
    title: str = ""
    content: str = ""
    evidence_level: str = "L3"
    source_type: str = (
        "search_summary"  # search_summary / full_text / github / twitter / reddit
    )
    query: str = ""
    engine: str = ""  # tavily / github / xreach / reddit / memory
    error: str = ""  # 搜索/抓取失败原因

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "Source":
        valid_fields = {
            "url",
            "title",
            "content",
            "evidence_level",
            "source_type",
            "query",
            "engine",
            "error",
        }
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class ResearchSession:
    """研究会话"""

    task: str
    iteration: int = 0
    max_iterations: int = 3
    sources: List[Dict] = field(default_factory=list)
    used_queries: List[str] = field(default_factory=list)
    enabled_sources: List[str] = field(
        default_factory=lambda: ["tavily", "github", "xreach", "reddit"]
    )
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 多源强制检查
    source_usage: Dict[str, int] = field(
        default_factory=lambda: {
            "tavily": 0,
            "github": 0,
            "xreach": 0,
            "reddit": 0,
            "memory": 0,
        }
    )

    def check_source_coverage(self) -> List[str]:
        """检查哪些来源未使用，返回缺失的来源列表"""
        missing = []
        for src in ["github", "xreach", "reddit"]:  # 这三个必须
            if self.source_usage.get(src, 0) == 0:
                missing.append(src)
        return missing

    def save(self, path: Path):
        with open(path, "w") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ResearchSession":
        with open(path) as f:
            data = json.load(f)
        for k in ["used_queries", "enabled_sources", "source_usage"]:
            if k not in data:
                data[k] = {} if k == "source_usage" else []
        return cls(**data)


# =============================================================================
# LLM 调用
# =============================================================================


def call_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    import urllib.request

    config = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                config = json.load(f)
        except Exception:
            pass

    base_url = config.get("proxy_config", {}).get("base_url", DEFAULT_BASE_URL)
    timeout = config.get("proxy_config", {}).get("timeout_ms", 300000) // 1000

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"LLM 调用失败: {e}"


# =============================================================================
# 多源搜索
# =============================================================================


def run_command(
    cmd: List[str], timeout: int = 60, name: str = "command"
) -> Optional[str]:
    """
    运行命令并返回 stdout，失败时输出错误到 stderr

    返回: 成功时返回 stdout，失败时返回 None
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout
        print(
            f"⚠️ {name} 失败 (exit {result.returncode}): {result.stderr[:100]}",
            file=__import__("sys").stderr,
        )
    except Exception as e:
        print(f"⚠️ {name} 异常: {e}", file=__import__("sys").stderr)
    return None


def search_tavily(query: str, max_results: int = 5) -> List[Source]:
    """Tavily 全网搜索"""
    output = run_command(
        [str(SEARCH_BIN), query, "--max", str(max_results), "--json"],
        timeout=60,
        name="tavily",
    )
    if not output:
        return []

    sources = []
    try:
        data = json.loads(output)
        for item in data.get("results", []):
            sources.append(
                Source(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    evidence_level=classify_evidence(item.get("url", "")),
                    source_type="search_summary",
                    query=query,
                    engine="tavily",
                )
            )
    except json.JSONDecodeError as e:
        print(f"⚠️ tavily JSON 解析失败: {e}", file=__import__("sys").stderr)
    return sources


def search_github(query: str, max_results: int = 10) -> List[Source]:
    """GitHub 仓库/代码搜索"""
    if not GH_BIN.exists():
        return []

    output = run_command(
        [
            str(GH_BIN),
            "search",
            "repos",
            query,
            "--limit",
            str(max_results),
            "--json",
            "name,description,url,stargazersCount",
        ],
        timeout=30,
        name="github",
    )
    if not output:
        return []

    sources = []
    try:
        repos = json.loads(output)
        for repo in repos:
            sources.append(
                Source(
                    url=repo.get("url", ""),
                    title=repo.get("name", ""),
                    content=repo.get("description", "")
                    + f" (⭐ {repo.get('stargazersCount', 0)})",
                    evidence_level="L1",  # GitHub 是官方来源
                    source_type="github",
                    query=query,
                    engine="github",
                )
            )
    except json.JSONDecodeError as e:
        print(f"⚠️ github JSON 解析失败: {e}", file=__import__("sys").stderr)
    return sources


def search_twitter(query: str, max_results: int = 10) -> List[Source]:
    """Twitter/X 搜索"""
    if not XREACH_BIN.exists():
        return []

    output = run_command(
        [str(XREACH_BIN), "search", "--count", str(max_results), query],
        timeout=30,
        name="xreach",
    )
    if not output:
        return []

    sources = []
    lines = output.strip().split("\n")
    for line in lines[:max_results]:
        if line.strip():
            sources.append(
                Source(
                    url="",
                    title=line[:100],
                    content=line,
                    evidence_level="L2",
                    source_type="twitter",
                    query=query,
                    engine="xreach",
                )
            )
    return sources


def search_reddit(query: str, max_results: int = 5) -> List[Source]:
    """Reddit 搜索（通过 Tavily site: 过滤）"""
    output = run_command(
        [
            str(SEARCH_BIN),
            f"site:reddit.com {query}",
            "--max",
            str(max_results),
            "--json",
        ],
        timeout=60,
        name="reddit",
    )
    if not output:
        return []

    sources = []
    try:
        data = json.loads(output)
        for item in data.get("results", []):
            sources.append(
                Source(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    evidence_level="L2",
                    source_type="reddit",
                    query=query,
                    engine="reddit",
                )
            )
    except json.JSONDecodeError as e:
        print(f"⚠️ reddit JSON 解析失败: {e}", file=__import__("sys").stderr)
    return sources


def search_memory(query: str) -> List[Source]:
    """本地知识库检索"""
    sources = []
    if not MEMORY_BIN.exists():
        return sources

    try:
        # memory 目前主要是 save/profile 命令，这里简化处理
        # 如果有向量检索功能，可以调用
        pass
    except Exception:
        pass
    return sources


def search_multi_source(
    query: str, sources: List[str], max_results: int = 5
) -> List[Source]:
    """
    多源并行搜索

    参数:
        query: 搜索关键词
        sources: 来源列表 ["tavily", "github", "twitter", "reddit", "memory"]
        max_results: 每个来源的最大结果数
    """
    all_sources = []

    # 构建搜索任务
    tasks = []
    if "tavily" in sources:
        tasks.append(("tavily", search_tavily, query, max_results))
    if "github" in sources:
        tasks.append(("github", search_github, query, max_results))
    if "xreach" in sources:
        tasks.append(("xreach", search_twitter, query, max_results))
    if "reddit" in sources:
        tasks.append(("reddit", search_reddit, query, max_results))
    if "memory" in sources:
        tasks.append(("memory", search_memory, query, max_results))

    # 并行执行
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        future_to_source = {
            executor.submit(func, q, max_results): name
            for name, func, q, max_results in tasks
        }

        for future in concurrent.futures.as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                results = future.result()
                all_sources.extend(results)
            except Exception as e:
                print(
                    f"⚠️ {source_name} 并行搜索异常: {e}", file=__import__("sys").stderr
                )

    return all_sources


# =============================================================================
# 智能抓取
# =============================================================================


def classify_evidence(url: str) -> str:
    """按 URL 域名分类证据等级"""
    url_lower = url.lower()

    for domain in L1_DOMAINS:
        if domain in url_lower:
            return "L1"

    for domain in L2_DOMAINS:
        if domain in url_lower:
            return "L2"

    return "L3"


def needs_stealth(url: str) -> bool:
    """判断是否需要反爬"""
    url_lower = url.lower()
    return any(domain in url_lower for domain in STEALTH_DOMAINS)


def scrape_static(url: str) -> str:
    """静态抓取 - Jina Reader"""
    output = run_command([str(SCRAPE_BIN), url], timeout=30, name=f"scrape({url[:40]})")
    return output or ""


def scrape_stealth(url: str) -> str:
    """反爬抓取 - Scrapling"""
    if not STEALTH_BIN.exists():
        return scrape_static(url)  # fallback

    output = run_command(
        [str(STEALTH_BIN), url], timeout=60, name=f"stealth({url[:40]})"
    )
    return output or ""


def scrape_js_render(url: str) -> str:
    """JS 渲染抓取 - Lightpanda"""
    if not LIGHTPANDA_BIN.exists():
        return scrape_static(url)  # fallback

    output = run_command(
        [str(LIGHTPANDA_BIN), "fetch", "--dump", "markdown", url],
        timeout=60,
        name=f"lightpanda({url[:40]})",
    )
    return output or ""


def smart_scrape(url: str, force_method: str = None) -> str:
    """
    智能抓取选择

    参数:
        url: 目标 URL
        force_method: 强制方法 ("static" / "stealth" / "js")
    """
    if force_method == "static":
        return scrape_static(url)
    elif force_method == "stealth":
        return scrape_stealth(url)
    elif force_method == "js":
        return scrape_js_render(url)

    # 自动选择
    if needs_stealth(url):
        return scrape_stealth(url)

    # 默认静态抓取
    return scrape_static(url)


def deep_read(sources: List[Source], top_n: int = 3) -> List[Source]:
    """
    对 TOP N 结果抓取全文（并行，智能选择抓取方式）
    """
    # 按 evidence_level 排序
    sorted_sources = sorted(
        sources,
        key=lambda s: 0
        if s.evidence_level == "L1"
        else (1 if s.evidence_level == "L2" else 2),
    )

    # 过滤掉没有 URL 的
    valid_sources = [s for s in sorted_sources if s.url]

    # 并行抓取
    full_texts: List[Source] = []
    seen_urls: Set[str] = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=top_n) as executor:
        future_to_source = {}

        for s in valid_sources[: top_n * 2]:
            if s.url in seen_urls:
                continue
            seen_urls.add(s.url)
            future_to_source[executor.submit(smart_scrape, s.url)] = s

            if len(future_to_source) >= top_n:
                break

        for future in concurrent.futures.as_completed(future_to_source):
            if len(full_texts) >= top_n:
                break

            original_source = future_to_source[future]
            try:
                content = future.result()
                if content and not content.startswith("❌") and len(content) > 200:
                    full_texts.append(
                        Source(
                            url=original_source.url,
                            title=original_source.title,
                            content=content[:8000],
                            evidence_level=original_source.evidence_level,
                            source_type="full_text",
                            query=original_source.query,
                            engine=original_source.engine,
                        )
                    )
            except Exception as e:
                print(
                    f"⚠️ deep_read 抓取异常 ({original_source.url[:50]}): {e}",
                    file=__import__("sys").stderr,
                )

    return full_texts


# =============================================================================
# 交叉验证
# =============================================================================


def cross_verify(claim: str) -> Dict[str, Any]:
    """
    对关键信息进行交叉验证

    返回:
        {
            "claim": str,
            "supporting": List[str],  # 支持证据
            "contradicting": List[str],  # 矛盾证据
            "verdict": str  # "verified" / "disputed" / "unverified"
        }
    """
    result = {
        "claim": claim,
        "supporting": [],
        "contradicting": [],
        "verdict": "unverified",
    }

    if not CROSS_VERIFY_BIN.exists():
        return result

    output = run_command(
        [str(CROSS_VERIFY_BIN), claim], timeout=60, name="cross_verify"
    )
    if not output:
        return result

    # 简单解析输出
    if (
        "conflict" in output.lower()
        or "issue" in output.lower()
        or "problem" in output.lower()
    ):
        result["verdict"] = "disputed"
        result["contradicting"].append(output[:500])
    elif output.strip():
        result["verdict"] = "verified"
        result["supporting"].append(output[:500])

    return result


def verify_key_claims(sources: List[Source]) -> List[Dict]:
    """对关键信息进行交叉验证"""
    # 提取可能需要验证的关键声明
    claims = []

    for s in sources:
        # 从内容中提取可能的声明（简化：取前 100 字符）
        if s.content and len(s.content) > 50:
            # 只验证 L1/L2 来源的关键信息
            if s.evidence_level in ["L1", "L2"]:
                claims.append({"claim": s.content[:100] + "...", "source": s.url})

    # 最多验证 3 个
    verified = []
    for c in claims[:3]:
        result = cross_verify(c["claim"])
        result["source"] = c["source"]
        verified.append(result)

    return verified


# =============================================================================
# 核心流程
# =============================================================================


# GitHub 查询的中→英关键词映射（每个中文关键词对应多个英文候选）
_GITHUB_KEYWORD_MAP = {
    "agent": ["autonomous agent", "LLM agent", "AI agent"],
    "智能体": ["autonomous agent", "AI agent"],
    "框架": ["framework", "toolkit"],
    "代码生成": ["code generation", "AI coding"],
    "编程": ["AI coding", "code generation"],
    "深度学习": ["deep learning", "neural network"],
    "机器学习": ["machine learning"],
    "爬虫": ["web scraper", "crawler"],
    "cli": ["cli tool", "terminal tool"],
    "命令行": ["cli tool", "terminal"],
    "web开发": ["web framework", "fullstack"],
    "全栈": ["fullstack", "web framework"],
    "测试": ["testing", "test framework"],
    "部署": ["deployment", "devops"],
    "监控": ["monitoring", "observability"],
    "数据库": ["database", "db"],
    "缓存": ["cache", "redis"],
    "消息队列": ["message queue", "kafka"],
    "微服务": ["microservice", "distributed"],
}


def _task_to_github_queries(task: str) -> List[str]:
    """
    将中文任务转换为多个简洁的英文 GitHub 查询关键词

    返回: 候选关键词列表（按优先级排序），搜索时依次尝试直到有结果
    """
    import re

    task_lower = task.lower()
    candidates = []

    # 尝试关键词映射（收集所有匹配的候选）
    matched = False
    for cn, en_list in _GITHUB_KEYWORD_MAP.items():
        if cn in task_lower:
            candidates.extend(en_list)
            matched = True

    if matched:
        # 去重但保持顺序
        seen = set()
        unique = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique

    # 提取英文单词（至少 2 个字符）
    en_words = re.findall(r"[a-zA-Z]{2,}", task)
    if en_words:
        stop = {
            "the",
            "and",
            "for",
            "with",
            "from",
            "how",
            "what",
            "best",
            "new",
            "latest",
        }
        filtered = [w for w in en_words if w.lower() not in stop]
        if filtered:
            return [" ".join(filtered[:4])]

    # 兜底
    return [task[:30]]


def plan_queries(task: str, gap: str, used_queries: List[str]) -> List[Dict[str, Any]]:
    """
    生成搜索查询 + 智能来源选择

    返回: [{"query": "xxx", "sources": ["tavily", "github"]}, ...]

    来源选择规则：
    - 技术框架/代码 → github
    - 社区讨论/体验 → reddit, twitter
    - 学术/官方文档 → tavily
    - 通用搜索 → tavily
    """
    used_str = "\n".join(f"- {q}" for q in used_queries[-10:]) if used_queries else "无"

    source_guide = """
来源选择：
- tavily: 全网搜索（支持中文），通用查询、新闻、文档
- github: 代码仓库、开源项目（⚠️ 必须英文，2-4 词，如 "AI coding"、"web scraper"）
- xreach: Twitter/X 实时动态、专家观点
- reddit: 深度讨论、用户踩坑经验

GitHub 英文关键词示例：
- "AI Agent 框架" → "autonomous agent" 或 "LLM agent"
- "代码生成" → "code generation"
- "Web 开发" → "web framework"
- "爬虫" → "web scraper"
- 禁止：repository, best practices, comparison, implementation
"""

    if not gap:
        prompt = f"""为研究任务生成 3-5 个搜索查询，每个查询选择最合适的来源。

任务: {task}

已用查询（不要重复）:
{used_str}

{source_guide}

输出 JSON 数组:
[
  {{"query": "搜索词", "sources": ["tavily", "github"]}},
  {{"query": "search term", "sources": ["github"]}}
]"""
    else:
        prompt = f"""研究任务: {task}
当前缺口: {gap}

已用查询（不要重复）:
{used_str}

{source_guide}

生成 2-3 个精准查询填补缺口，每个查询选择最合适的来源。

输出 JSON 数组:
[
  {{"query": "搜索词", "sources": ["来源1", "来源2"]}}
]"""

    response = call_llm(prompt)

    try:
        start, end = response.find("["), response.rfind("]") + 1
        queries = json.loads(response[start:end])

        # 验证格式
        valid_queries = []
        used_set = set(q.lower() for q in used_queries)

        for item in queries:
            if isinstance(item, dict) and "query" in item:
                q = item["query"]
                if q.lower() not in used_set:
                    valid_queries.append(
                        {"query": q, "sources": item.get("sources", ["tavily"])}
                    )
            elif isinstance(item, str):
                # 兼容旧格式
                if item.lower() not in used_set:
                    valid_queries.append(
                        {
                            "query": item,
                            "sources": ["tavily"],  # 默认来源
                        }
                    )

        return (
            valid_queries if valid_queries else [{"query": task, "sources": ["tavily"]}]
        )
    except:
        return [{"query": task, "sources": ["tavily"]}]


def evaluate_gap(task: str, sources: List[Source], iteration: int) -> Optional[str]:
    """LLM 评估研究是否充分"""
    if not sources:
        return "没有找到相关信息"

    summaries = []
    for s in sources[-15:]:
        prefix = {
            "full_text": "📖",
            "github": "📦",
            "twitter": "🐦",
            "reddit": "💬",
        }.get(s.source_type, "📄")
        title = s.title[:50] if s.title else "无标题"
        content = s.content[:200] if s.content else ""
        src_type = "📖全文" if s.source_type == "full_text" else "📄摘要"
        summaries.append(
            f"{prefix} [{s.evidence_level}|{src_type}] {title}: {content}..."
        )

    summary_text = "\n".join(summaries)

    # 统计来源质量
    full_text_count = sum(1 for s in sources if s.source_type == "full_text")
    l1_count = sum(1 for s in sources if s.evidence_level == "L1")
    total = len(sources)

    prompt = f"""评估当前研究是否足够深入、有应用价值。

任务：{task}
状态：第 {iteration} 轮 | 来源 {total} 条 | 全文 {full_text_count} 篇 | L1 {l1_count} 条

已收集信息：
{summary_text}

## 评分标准（0-10）
- **覆盖度**：是否从多个角度搜索？（不同来源、不同子话题）
- **深度**：关键来源是否读了全文？不能只靠摘要下结论
- **可操作性**：用户看完能直接动手吗？（有具体步骤/工具/对比/数据）

## 输出（严格 JSON）
{{
  "coverage_score": 0-10,
  "depth_score": 0-10,
  "actionable_score": 0-10,
  "gap": "具体缺什么，下一步应该搜什么"
}}

三个分数都 >= 7 才算充分。"""

    response = call_llm(prompt)

    try:
        start, end = response.find("{"), response.rfind("}") + 1
        result = json.loads(response[start:end])
        coverage = result.get("coverage_score", 0)
        depth = result.get("depth_score", 0)
        actionable = result.get("actionable_score", 0)

        # 三个分数都 >= 7 才算充分
        if coverage >= 7 and depth >= 7 and actionable >= 7:
            return None

        gap = result.get("gap", "信息不完整")
        scores = f"(覆盖:{coverage} 深度:{depth} 可操作:{actionable})"
        return f"{scores} {gap}"
    except:
        return "需要更多信息"


def review_with_human(
    gap: Optional[str], iteration: int, sources: List[Source]
) -> Optional[str]:
    """人审批"""
    l1_count = sum(1 for s in sources if s.evidence_level == "L1")
    l2_count = sum(1 for s in sources if s.evidence_level == "L2")
    full_text_count = sum(1 for s in sources if s.source_type == "full_text")

    # 统计各来源
    source_stats = {}
    for s in sources:
        engine = s.engine or "unknown"
        source_stats[engine] = source_stats.get(engine, 0) + 1

    print("\n" + "━" * 50)
    print(f"📋 研究审核（迭代 {iteration}）")
    print("━" * 50)
    print(f"来源: {len(sources)} 条 (全文: {full_text_count})")
    print(f"证据: 🟢 L1 {l1_count} | 🟡 L2 {l2_count}")
    print(f"引擎: {', '.join(f'{k}:{v}' for k, v in source_stats.items())}")

    if gap is None:
        print("\n✅ LLM 认为研究充分")
        print("━" * 50)
        print("操作: [Enter] 完成 | [c] 继续深入")

        try:
            choice = input("> ").strip().lower()
        except EOFError:
            return None

        if choice == "c":
            return "用户要求继续深入"
        return None
    else:
        print(f"\n缺口: {gap}")
        print("━" * 50)
        print("操作: [Enter] 继续迭代 | [d] 完成 | [输入新方向]")

        try:
            choice = input("> ").strip()
        except EOFError:
            return None

        if choice.lower() == "d":
            return None
        elif choice == "":
            return gap
        else:
            return choice


def synthesize_report(
    task: str, sources: List[Source], verified: List[Dict] = None
) -> str:
    """生成综合报告"""
    if not sources:
        return f"# {task}\n\n未找到相关信息。"

    # 构建来源列表（URL 用 Markdown 链接格式，方便 LLM 直接引用）
    indexed_sources = []
    for i, s in enumerate(sources, 1):
        level_icon = {"L1": "🟢", "L2": "🟡", "L3": "🟠", "L4": "🔴"}.get(
            s.evidence_level, "⚪"
        )
        engine_icon = {"github": "📦", "twitter": "🐦", "reddit": "💬"}.get(
            s.engine, "📄"
        )
        title = s.title if s.title else "无标题"
        content = s.content[:500] if s.content else ""
        url = s.url if s.url else "无链接"
        indexed_sources.append(
            f"[{i}] {level_icon} {engine_icon} {title}\n"
            f"    🔗 {url}\n"
            f"    📝 {content}..."
        )

    sources_text = "\n\n".join(indexed_sources)

    # 交叉验证结果
    verify_text = ""
    if verified:
        verify_lines = ["\n## 交叉验证结果\n"]
        for v in verified:
            status = {"verified": "✅", "disputed": "⚠️", "unverified": "❓"}.get(
                v["verdict"], "❓"
            )
            verify_lines.append(f"- {status} {v['claim'][:50]}... ({v['verdict']})")
        verify_text = "\n".join(verify_lines)

    prompt = f"""基于以下来源，为用户生成一份高质量的研究报告。

用户的问题："{task}"

## 来源
{sources_text}
{verify_text}

## 规则
1. **每句话必须有出处**：正文用 `[1][2]` 编号引用，不要放链接
2. **不许编造**：所有内容必须来自上面的来源
3. **不许偷懒**：禁止"值得注意的是"、"一般来说"等空话
4. **不许套模板**：根据内容自行组织结构
5. **要有深度**：分析、对比、给出可操作结论

## 输出格式
- 根据问题性质自行组织结构
- 正文引用：`星标达到 33,000 [7]`
- 末尾列出引用来源（可点击链接）：
  ```
  ## 引用来源
  [1] 标题 https://...
  [2] 标题 https://...
  ```"""

    return call_llm(prompt)


def save_report(report: str, task: str) -> Path:
    """保存报告"""
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^\w\s-]", "", task.lower())
    slug = re.sub(r"[-\s]+", "_", slug)[:50]
    date_str = datetime.now().strftime("%Y%m%d")

    report_path = RESEARCH_DIR / f"{slug}_{date_str}.md"

    if report_path.exists():
        i = 1
        while True:
            report_path = RESEARCH_DIR / f"{slug}_{date_str}_{i}.md"
            if not report_path.exists():
                break
            i += 1

    report_path.write_text(report, encoding="utf-8")
    return report_path


# =============================================================================
# 主流程
# =============================================================================


def research(
    task: str,
    max_iter: int = 3,
    interactive: bool = True,
    enabled_sources: List[str] = None,
    existing_sources: List[Source] = None,
    existing_queries: List[str] = None,
    start_iteration: int = 0,
    json_output: bool = False,
) -> str:
    """完整研究流程"""

    # 日志函数（统一输出控制）
    def log(msg: str = ""):
        if not json_output:
            print(msg)

    # 默认启用所有来源
    if enabled_sources is None:
        enabled_sources = ["tavily", "github", "xreach", "reddit"]  # 必须包含这4个

    all_sources: List[Source] = existing_sources or []
    used_queries: List[str] = existing_queries or []
    session = ResearchSession(
        task=task,
        max_iterations=max_iter,
        iteration=start_iteration,
        enabled_sources=enabled_sources,
    )
    gap = ""

    # ─────────────────────────────────────────────────────
    # 阶段 0：理解确认（先问用户，再由 LLM 确认）
    # ─────────────────────────────────────────────────────
    if start_iteration == 0:  # 只在新任务时确认，恢复时不重复
        log(f"🔬 研究任务: {task}")

        user_context = ""

        # 交互模式：先问用户
        if interactive and not json_output:
            log(f"\n{'━' * 50}")
            log("在开始大规模搜索之前，我需要了解你的具体情况：")
            log(f"{'━' * 50}")
            log("")
            log("1. 你是谁？（角色/技术水平）")
            log("   例：'5年经验的全栈开发' / '技术经理，不写代码' / '刚入门的学生'")
            log("")

            try:
                role_input = input("   > ").strip()
            except EOFError:
                role_input = ""

            log("")
            log("2. 你想要什么样的结果？")
            log("   例：'各角色专家的工作指南' / '工具对比选型' / '一个完整的操作手册'")
            log("")

            try:
                goal_input = input("   > ").strip()
            except EOFError:
                goal_input = ""

            if role_input or goal_input:
                user_context = f"用户背景：{role_input or '未说明'}。期望结果：{goal_input or '未说明'}。"
                task = f"{task}（{user_context}）"
            log("")

        # LLM 根据任务 + 用户信息生成确认方案
        clarify_prompt = f"""任务："{task}"
{f"用户信息：{user_context}" if user_context else ""}

分析并输出 JSON：
{{
  "target_reader": "目标读者是谁，什么水平",
  "core_need": "用户真正想解决的问题",
  "dimensions": ["研究维度1", "维度2", ...],
  "deliverable": "用户拿到报告后能直接做什么"
}}"""

        clarify_response = call_llm(clarify_prompt)

        try:
            start = clarify_response.find("{")
            end = clarify_response.rfind("}") + 1
            clarify_result = json.loads(clarify_response[start:end])
        except:
            clarify_result = {
                "target_reader": "开发者",
                "core_need": task,
                "dimensions": ["核心概念", "实践案例", "工具选型"],
                "deliverable": "技术研究报告",
            }

        target_reader = clarify_result.get("target_reader", "")
        core_need = clarify_result.get("core_need", task)
        dimensions = clarify_result.get("dimensions", [])
        deliverable = clarify_result.get("deliverable", "")

        log(f"{'━' * 50}")
        log(f"📋 我的理解：")
        log(f"   👤 目标读者：{target_reader}")
        log(f"   🎯 核心需求：{core_need}")
        log(f"   🔍 研究维度：")
        for i, dim in enumerate(dimensions, 1):
            log(f"      {i}. {dim}")
        log(f"   📦 最终交付：{deliverable}")

        # 交互模式：让用户最终确认
        if interactive and not json_output:
            log(f"\n{'━' * 50}")
            log("操作: [Enter] 确认 | [输入] 补充或修正")
            log(f"{'━' * 50}")

            try:
                final_input = input("> ").strip()
            except EOFError:
                final_input = ""

            if final_input:
                task = f"{task}（补充：{final_input}）"
                log(f"✅ 已补充: {final_input}")
            else:
                log("✅ 确认，开始研究...")
        else:
            log("✅ 自动确认，开始研究...")

        log("━" * 50 + "\n")

    log(f"🔬 启动研究: {task}")
    log(f"来源: {', '.join(enabled_sources)} | 最大迭代: {max_iter}")
    if start_iteration > 0:
        log(f"   恢复自第 {start_iteration} 轮")
    log("━" * 50 + "\n")

    while session.iteration < session.max_iterations:
        session.iteration += 1
        log(f"\n📍 迭代 {session.iteration}")

        # 1. 生成查询 + 智能来源选择
        query_plans = plan_queries(task, gap, used_queries)

        # 打印查询计划
        log("🔍 查询计划:")
        for p in query_plans:
            src_str = ",".join(p["sources"])
            log(f"   [{src_str}] {p['query'][:50]}")

        # 记录已用查询
        used_queries.extend([p["query"] for p in query_plans])

        # 2. 多源并行搜索（每个查询使用推荐的来源）
        new_sources = []
        for plan in query_plans:
            q = plan["query"]
            sources = plan["sources"]
            log(f"🔎 搜索 '{q[:30]}...' → {', '.join(sources)}")
            results = search_multi_source(q, sources, max_results=5)
            new_sources.extend(results)

            # 更新来源使用统计
            for s in results:
                if s.engine:
                    session.source_usage[s.engine] = (
                        session.source_usage.get(s.engine, 0) + 1
                    )

        log(f"   本轮找到 {len(new_sources)} 条结果")
        all_sources.extend(new_sources)

        # 3. 智能抓取全文（优先抓取 L1 来源：GitHub、官方文档、学术论文）
        log("📖 抓取 TOP 5 全文...")
        full_texts = deep_read(all_sources, top_n=5)
        log(f"   获取 {len(full_texts)} 篇全文")
        all_sources.extend(full_texts)

        # 4. ⚠️ 多源强制检查
        missing_sources = session.check_source_coverage()
        if missing_sources:
            log(f"\n⚠️ 缺少来源覆盖: {', '.join(missing_sources)}")
            log("   强制补充搜索...")

            # 为缺失来源生成补充查询
            for missing_src in missing_sources:
                if missing_src == "github":
                    # GitHub: 多候选关键词依次尝试
                    candidates = _task_to_github_queries(task)
                    found = False
                    for q in candidates:
                        log(f"   补充 [github]: {q}")
                        results = search_github(q, max_results=3)
                        if results:
                            all_sources.extend(results)
                            session.source_usage["github"] = session.source_usage.get(
                                "github", 0
                            ) + len(results)
                            found = True
                            break
                    if not found:
                        log(f"   ⚠️ github 所有候选均无结果: {candidates}")
                elif missing_src == "xreach":
                    supplement_query = f"site:twitter.com OR site:x.com {task}"
                    log(f"   补充 [xreach]: {supplement_query[:40]}")
                    results = search_multi_source(
                        supplement_query, ["xreach"], max_results=3
                    )
                    all_sources.extend(results)
                    session.source_usage["xreach"] = session.source_usage.get(
                        "xreach", 0
                    ) + len(results)
                elif missing_src == "reddit":
                    supplement_query = f"site:reddit.com {task} experience discussion"
                    log(f"   补充 [reddit]: {supplement_query[:40]}")
                    results = search_multi_source(
                        supplement_query, ["reddit"], max_results=3
                    )
                    all_sources.extend(results)
                    session.source_usage["reddit"] = session.source_usage.get(
                        "reddit", 0
                    ) + len(results)

        # 5. LLM 评估
        gap = evaluate_gap(task, all_sources, session.iteration)

        # 自动模式打印评估
        if not interactive and gap:
            log(f"📊 评估: {gap[:80]}...")

        # 6. 人审批
        if interactive:
            gap = review_with_human(gap, session.iteration, all_sources)

        # 7. 决定是否继续
        if gap is None:
            log("\n✅ 研究充分，生成报告...")
            break
        else:
            log(f"🔄 继续迭代，缺口: {gap[:50]}...")

    # 8. 最终补充检查（兜底：确保关键来源至少有 1 条）
    missing_sources = session.check_source_coverage()
    if missing_sources:
        log(f"\n⚠️ 最终补充: 缺少 {', '.join(missing_sources)}")
        for missing_src in missing_sources:
            if missing_src == "github":
                candidates = _task_to_github_queries(task)
                found = False
                for q in candidates:
                    log(f"   补充 [github]: {q}")
                    results = search_github(q, max_results=3)
                    if results:
                        all_sources.extend(results)
                        session.source_usage["github"] = session.source_usage.get(
                            "github", 0
                        ) + len(results)
                        found = True
                        break
                if not found:
                    log(f"   ⚠️ github 所有候选均无结果: {candidates}")
            elif missing_src == "xreach":
                supplement_query = f"site:twitter.com OR site:x.com {task}"
                log(f"   补充 [xreach]: {supplement_query[:40]}")
                results = search_multi_source(
                    supplement_query, ["xreach"], max_results=3
                )
                all_sources.extend(results)
                session.source_usage["xreach"] = session.source_usage.get(
                    "xreach", 0
                ) + len(results)
            elif missing_src == "reddit":
                supplement_query = f"site:reddit.com {task} experience discussion"
                log(f"   补充 [reddit]: {supplement_query[:40]}")
                results = search_multi_source(
                    supplement_query, ["reddit"], max_results=3
                )
                all_sources.extend(results)
                session.source_usage["reddit"] = session.source_usage.get(
                    "reddit", 0
                ) + len(results)

    # 9. 最终多源覆盖报告
    log("\n📊 多源覆盖统计:")
    for src, count in session.source_usage.items():
        status = "✅" if count > 0 else "❌"
        log(f"   {status} {src}: {count} 条")

    # 9. 交叉验证
    log("\n⚖️ 交叉验证关键信息...")
    verified = verify_key_claims(all_sources)
    log(f"   验证 {len(verified)} 条声明")

    # 保存会话
    session.sources = [s.to_dict() for s in all_sources]
    session.used_queries = used_queries
    thread_id = str(uuid.uuid4())[:8]
    checkpoint_path = CHECKPOINT_DIR / f"{thread_id}.json"
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    session.save(checkpoint_path)
    log(f"\n💾 已保存会话: {thread_id}")

    # 生成报告
    report = synthesize_report(task, all_sources, verified)

    # 保存报告
    report_path = save_report(report, task)
    log(f"📄 已保存报告: {report_path.relative_to(PROJECT_ROOT)}")

    # JSON 输出模式（供 AI 调用）
    if json_output:
        result = {
            "report": report,
            "report_path": str(report_path),
            "thread_id": thread_id,
            "source_coverage": session.source_usage,
            "total_sources": len(all_sources),
            "iterations": session.iteration,
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    return report


def list_sessions():
    """列出所有研究线程"""
    if not CHECKPOINT_DIR.exists():
        print("暂无研究线程")
        return

    threads = []
    for path in CHECKPOINT_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            threads.append(
                {
                    "thread_id": path.stem,
                    "task": data.get("task", "未知"),
                    "iteration": data.get("iteration", 0),
                    "sources": data.get("enabled_sources", []),
                    "updated_at": datetime.fromtimestamp(
                        path.stat().st_mtime
                    ).isoformat(),
                }
            )
        except:
            pass

    if not threads:
        print("暂无研究线程")
        return

    threads.sort(key=lambda x: x["updated_at"], reverse=True)
    print(f"共 {len(threads)} 个研究线程:\n")
    for t in threads:
        src_str = ",".join(t["sources"]) if t["sources"] else "default"
        print(
            f"  [{t['thread_id']}] {t['task'][:40]} (迭代 {t['iteration']}, 来源: {src_str})"
        )


def resume_session(thread_id: str, interactive: bool = True):
    """恢复研究线程"""
    checkpoint_path = CHECKPOINT_DIR / f"{thread_id}.json"
    if not checkpoint_path.exists():
        print(f"❌ 未找到线程: {thread_id}")
        return

    session = ResearchSession.load(checkpoint_path)
    print(f"📂 恢复研究: {session.task}")
    print(f"   已完成 {session.iteration} 轮迭代")

    existing_sources = [Source.from_dict(s) for s in session.sources]

    return research(
        task=session.task,
        max_iter=session.max_iterations,
        interactive=interactive,
        enabled_sources=session.enabled_sources,
        existing_sources=existing_sources,
        existing_queries=session.used_queries,
        start_iteration=session.iteration,
    )


def main():
    parser = argparse.ArgumentParser(
        description=f"研究编排器 v{__version__} - 多源强制搜索 + 智能抓取"
    )
    parser.add_argument("task", nargs="?", default="", help="研究任务")
    parser.add_argument("--resume", "-r", help="恢复研究线程")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有线程")
    parser.add_argument("--max-iterations", type=int, default=3, help="最大迭代次数")
    parser.add_argument("--no-interactive", action="store_true", help="Agent 自动模式")
    parser.add_argument(
        "--sources",
        default="",
        help="[可选] 覆盖自动来源选择，逗号分隔: tavily,github,twitter,reddit,memory",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM 模型")
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="输出 JSON 格式（供 AI 调用，包含来源覆盖统计）",
    )
    args = parser.parse_args()

    if args.list:
        list_sessions()
        return

    if args.resume:
        resume_session(args.resume, interactive=not args.no_interactive)
        return

    if not args.task:
        parser.print_help()
        return

    # 解析来源（可选覆盖）
    enabled_sources = (
        [s.strip() for s in args.sources.split(",")] if args.sources else None
    )

    report = research(
        task=args.task,
        max_iter=args.max_iterations,
        interactive=not args.no_interactive,
        enabled_sources=enabled_sources,
        json_output=args.json,
    )

    # JSON 模式直接输出
    if args.json:
        print(report)
    else:
        print("\n" + "━" * 50)
        print("📝 研究报告")
        print("━" * 50)
        print(report)


if __name__ == "__main__":
    main()
