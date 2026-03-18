#!/usr/bin/env python3
"""
Nexus Semantic Router - 轻量级语义路由器

设计原则：
- 复用项目现有的 sentence_transformers
- 从 SCHEMA.json 自动构建路由
- 预计算工具 embedding，查询时毫秒级响应

用法:
    python3 bin/semantic_router.py "搜索 X 关于 AI Agent"
    
作为模块:
    from bin.semantic_router import SemanticRouter
    router = SemanticRouter()
    match = router.route("搜索 X 关于 AI Agent")
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# 延迟导入，避免启动时加载模型
_model = None
_encoder = None
_np = None

WORKSPACE_ROOT = Path(__file__).parent.parent
SKILLS_DIR = WORKSPACE_ROOT / "skills"
CACHE_DIR = WORKSPACE_ROOT / "knowledge" / ".router_cache"
MANIFEST_PATH = WORKSPACE_ROOT / "knowledge" / "tools_manifest.json"  # Level 1


def _get_numpy():
    """延迟加载 numpy"""
    global _np
    if _np is None:
        import numpy as np
        _np = np
    return _np


def _get_encoder():
    """延迟加载 encoder"""
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        # 使用与 vector_store.py 相同的模型
        _encoder = SentenceTransformer('all-MiniLM-L6-v2')
    return _encoder


def _cosine_similarity(a, b) -> float:
    """计算余弦相似度"""
    np = _get_numpy()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@dataclass
class RouteMatch:
    """路由匹配结果"""
    tool_name: str
    skill_name: str
    score: float
    tool_def: Dict[str, Any]
    extracted_args: Dict[str, Any]
    persona: Optional[str] = None  # 匹配的人格
    persona_content: Optional[str] = None  # SKILL.md 内容


class SemanticRouter:
    """
    语义路由器 - 基于向量相似度的意图匹配
    
    核心思想：
    1. 为每个工具构建语义表示（description + tags + tool_name）
    2. 预计算所有工具的 embedding
    3. 查询时计算 query embedding，返回最匹配的工具
    """
    
    def __init__(self, cache_enabled: bool = True):
        """
        Args:
            cache_enabled: 是否启用 embedding 缓存
        """
        self.cache_enabled = cache_enabled
        self.tools: Dict[str, Dict] = {}
        self.embeddings: Dict[str, Any] = {}  # numpy arrays, lazy loaded
        self.tool_texts: Dict[str, str] = {}
        self.personas: Dict[str, Dict] = {}  # 认知型人格
        
        # 加载工具、人格（轻量级，毫秒级）
        self._load_tools()
        self._load_personas()
        # 延迟加载 embedding（重量级，只在语义匹配时加载）
        self._embeddings_loaded = False
    
    def _get_intent_hints(self, tool_name: str, tool_desc: str, ai_hints: Dict = None) -> str:
        """为工具生成意图关键词，优先使用 ai_hints"""
        
        # 如果有 ai_hints.when_to_use，直接使用
        if ai_hints and "when_to_use" in ai_hints:
            return ai_hints["when_to_use"]
        
        # 兼容：基于工具名的意图推断
        hints = []
        name_lower = tool_name.lower()
        
        if 'search' in name_lower:
            hints.append("搜索 查找 检索")
        if 'scrape' in name_lower or 'fetch' in name_lower:
            hints.append("抓取 爬取 提取 网页")
        if 'gh' in name_lower or 'github' in name_lower or 'repo' in name_lower:
            hints.append("GitHub 仓库 代码库")
        if 'x_' in name_lower or 'twitter' in name_lower:
            hints.append("X 推特 Twitter")
        if 'view' in name_lower or 'get' in name_lower:
            hints.append("查看 获取")
        if 'post' in name_lower or 'publish' in name_lower:
            hints.append("发布 发送 推送")
        if 'memory' in name_lower or 'knowledge' in name_lower:
            hints.append("记忆 知识库 历史")
        if 'notify' in name_lower or 'send' in name_lower:
            hints.append("通知 消息 推送")
        
        return ' '.join(hints) if hints else ""
    
    def _load_tools(self):
        """
        从 SCHEMA.json 加载所有工具
        
        三级渐进式加载（Codex 风格）：
        - Level 1: tools_manifest.json（元数据，快速加载）
        - Level 2: SCHEMA.json（完整定义，按需加载）
        - Level 3: guidance.md（详细指导，按需加载）
        
        当前实现：直接加载 SCHEMA.json（兼容模式）
        TODO: 实现 Level 1 优先加载
        """
        for schema_path in SKILLS_DIR.glob("*/SCHEMA.json"):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                skill_name = schema.get("name", schema_path.parent.name)
                skill_dir = schema_path.parent.name
                skill_tags = schema.get("tags", [])
                skill_desc = schema.get("description", "")
                
                # 读取 ai_hints 和 requires（Codex 风格）
                skill_ai_hints = schema.get("ai_hints", {})
                skill_requires = schema.get("requires", {})
                
                for tool_name, tool_def in schema.get("tools", {}).items():
                    # 构建工具的语义文本
                    tool_desc = tool_def.get("description", "")
                    tool_tags = tool_def.get("tags", [])
                    
                    # 语义表示 = 工具名（分解关键词）+ 描述 + ai_hints
                    tool_keywords = tool_name.replace('_', ' ')  # gh_view -> gh view
                    
                    # 使用 ai_hints 生成语义文本
                    intent_hints = self._get_intent_hints(tool_name, tool_desc, skill_ai_hints)
                    
                    semantic_text = f"{tool_keywords}: {tool_desc}"
                    if skill_tags:
                        semantic_text += f" [tags: {', '.join(skill_tags)}]"
                    if intent_hints:
                        semantic_text += f" [intent: {intent_hints}]"
                    
                    self.tools[tool_name] = {
                        "skill": skill_name,
                        "skill_dir": skill_dir,
                        "skill_tags": skill_tags,
                        "tool_description": tool_desc,
                        "parameters": tool_def.get("parameters", {}).get("properties", {}),
                        "required": tool_def.get("parameters", {}).get("required", []),
                        "command": tool_def.get("command", ""),
                        "semantic_text": semantic_text,
                        # 新增：AI 指导（Codex 风格）
                        "ai_hints": skill_ai_hints,
                        # 新增：依赖检查（门控）
                        "requires": skill_requires
                    }
                    
            except Exception as e:
                print(f"⚠️  Error loading {schema_path}: {e}")
    
    def _load_personas(self):
        """
        加载认知型人格（type="cognitive" 的技能）
        
        这些是思维框架，不是可执行工具，用于注入到 system prompt
        """
        for schema_path in SKILLS_DIR.glob("*/SCHEMA.json"):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                # 只加载认知型
                if schema.get("type") != "cognitive":
                    continue
                
                skill_name = schema.get("name", schema_path.parent.name)
                skill_dir = schema_path.parent.name
                skill_file = schema.get("skill_file", "SKILL.md")
                
                # 加载 SKILL.md 内容
                skill_md_path = schema_path.parent / skill_file
                skill_content = ""
                if skill_md_path.exists():
                    with open(skill_md_path, 'r', encoding='utf-8') as f:
                        skill_content = f.read()
                
                self.personas[skill_name] = {
                    "skill_dir": skill_dir,
                    "description": schema.get("description", ""),
                    "content": skill_content,
                }
                
            except Exception as e:
                print(f"⚠️  Error loading persona {schema_path}: {e}")
    
    def _load_embeddings(self):
        """加载或计算工具 embedding"""
        encoder = _get_encoder()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = CACHE_DIR / "tool_embeddings.json"
        
        # 尝试从缓存加载
        cached = {}
        if self.cache_enabled and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
            except Exception:
                cached = {}
        
        # 检查是否需要重新计算
        need_compute = set(self.tools.keys()) - set(cached.keys())
        
        if need_compute:
            # 批量计算新工具的 embedding
            texts = [self.tools[t]["semantic_text"] for t in need_compute]
            if texts:
                new_embeddings = encoder.encode(texts)
                for i, tool_name in enumerate(need_compute):
                    cached[tool_name] = new_embeddings[i].tolist()
            
            # 保存缓存
            if self.cache_enabled:
                with open(cache_file, 'w') as f:
                    json.dump(cached, f)
        
        # 转换为 numpy 数组
        np = _get_numpy()
        for tool_name, emb_list in cached.items():
            if tool_name in self.tools:
                self.embeddings[tool_name] = np.array(emb_list)
    
    def _extract_args(self, query: str, tool_name: str, tool_def: Dict) -> Dict[str, Any]:
        """从查询中提取参数"""
        import re
        
        args = {}
        params = tool_def.get("parameters", {})
        required = tool_def.get("required", [])
        
        # URL 参数
        if "url" in params:
            url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', query)
            if url_match:
                args["url"] = url_match.group(0)
        
        # GitHub repo 参数
        if "repo" in params:
            repo_match = re.search(r'\b([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)\b', query)
            if repo_match:
                repo = repo_match.group(1)
                if '/' in repo and not repo.startswith('http'):
                    args["repo"] = repo
        
        # 查询参数
        if "query" in params:
            # 移除 URL 和 repo
            clean_query = re.sub(r'https?://[^\s]+', '', query)
            clean_query = re.sub(r'[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+', '', clean_query)
            # 过滤停用词
            stop_words = {'搜索', '查找', '关于', '的', '内容', '获取', '查看', '分析',
                         '上', '中', '里', '请', '帮我', '我要', '想要', '能不能', '可以',
                         '一下', '看看', '找找', '有没有', '有没有关于', '帮我'}
            words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z0-9]+', clean_query)
            filtered = [w for w in words if w not in stop_words and len(w) > 1]
            if filtered:
                args["query"] = ' '.join(filtered)
        
        # 递归参数（从关键词推断）
        if "recursive" in params and "recursive" not in args:
            if re.search(r'(递归|recursive|穿透|追踪|跟踪)', query, re.IGNORECASE):
                args["recursive"] = True
        
        # 深度参数（从数字提取）
        if "depth" in params and "depth" not in args:
            depth_match = re.search(r'(深度|depth)[^\d]*(\d+)', query, re.IGNORECASE)
            if depth_match:
                args["depth"] = int(depth_match.group(2))
        
        # 填充必需参数
        for param in required:
            if param not in args:
                if param in ("query", "q", "keyword", "keywords"):
                    args[param] = query  # 使用原始查询作为 fallback
        
        # 填充默认值（SCHEMA 中定义的 default）
        for param_name, param_def in params.items():
            if param_name not in args and "default" in param_def:
                args[param_name] = param_def["default"]
        
        return args
    
    # 人格规则：复杂任务匹配认知型人格
    PERSONA_RULES = [
        # 研究类
        (r"(深度|详细|完整|深入).*(研究|分析|调研|调查)", "agency-deep-researcher"),
        (r"(行业|市场|竞品).*(分析|研究|报告)", "agency-deep-researcher"),
        # 工程类
        (r"(重构|优化|实现|开发|编写).*(代码|模块|功能|系统)", "agency-engineering-ai-engineer"),
        (r"(修复|解决).*(bug|问题|错误)", "agency-engineering-ai-engineer"),
        # 测试类
        (r"(测试|验证|检查|确保|确认).*(正确|可用|工作)", "agency-testing-reality-checker"),
        (r"(审查|审核).*(代码|结果|产出)", "agency-testing-reality-checker"),
        # 增长类
        (r"(病毒|传播|爆款|增长|裂变)", "agency-viral-writer"),
        (r"(内容|文案).*(优化|爆款|传播)", "agency-viral-writer"),
        # GitHub 专项
        (r"(GitHub|gh).*(深度|详细|完整).*(分析|研究)", "agency-github-researcher"),
    ]
    
    # 规则层：高优先级的意图规则（按优先级排序，更具体的规则在前）
    INTENT_RULES = [
        # === 网页抓取（按防护情况区分）===
        (r"(隐身|stealth|防爬|绕过|突破).*(抓取|爬取|读取|获取)", "stealth_get"),
        (r"(小红书|xhs).*(抓取|爬取|获取|内容)", "stealth_get"),
        (r"(知乎).*(文章|内容|抓取)", "stealth_get"),
        (r"cloudflare.*(绕过|突破)", "stealth_get"),
        (r"(普通|标准|一般|简单).*(抓取|爬取|获取)", "scrape_url"),
        (r"(抓取|爬取|获取).*(网页|页面|https?://)", "scrape_url"),
        
        # === GitHub（深度分析 vs 快速查看）===
        (r"(深度|详细|完整|深入).*(github|仓库|repo).*(分析|研究)", "analyze_repo"),
        (r"github.*(文件|源码|code|内容)", "gh_contents"),
        (r"github.*(release|发布|版本)", "gh_releases"),
        (r"(查看|获取|分析).*(github|仓库|repo)", "gh_view"),
        (r"github.*(搜索|查找)", "gh_view"),
        
        # === X/Twitter ===
        (r"(搜索|查找|找).*(X|推特|twitter)", "x_search"),
        (r"(查看|获取).*(X|推特|twitter).*(用户|主页)", "x_user"),
        (r"(发布|发送|推).*(X|推特|twitter)", "post_thread"),
        
        # === 平台专用 ===
        (r"(提取|下载|获取).*(字幕|youtube|视频)", "extract"),
        (r"(B站|bilibili).*(字幕|subtitle)", "bilibili_subtitle"),
        (r"(渲染|js|动态).*(网页|页面)", "fetch"),
        
        # === 搜索 ===
        (r"(搜索|查找|检索).*(网页|网络|全网|深度)", "web_search"),
        (r"^(搜索|查找|检索)\s", "web_search"),  # 以搜索开头
        (r"(搜索|查询).*(知识库|历史|记忆)", "memory_query"),
        
        # === 记忆 ===
        (r"(保存|存储).*(记忆|知识|洞察)", "memory_save"),
    ]
    
    def _rule_match(self, query: str) -> Optional[Tuple[str, float]]:
        """规则匹配：快速、准确"""
        import re
        for pattern, tool_name in self.INTENT_RULES:
            if re.search(pattern, query, re.IGNORECASE):
                if tool_name in self.tools:
                    return tool_name, 1.0  # 规则匹配给满分
        return None
    
    def _match_persona(self, query: str) -> Optional[Tuple[str, str]]:
        """
        人格匹配：检测复杂任务，返回匹配的人格
        
        Returns:
            (persona_name, persona_content) 或 None
        """
        import re
        for pattern, persona_name in self.PERSONA_RULES:
            if re.search(pattern, query, re.IGNORECASE):
                if persona_name in self.personas:
                    persona_info = self.personas[persona_name]
                    return persona_name, persona_info.get("content", "")
        return None
    
    def route(self, query: str, top_k: int = 1, threshold: float = 0.3) -> Optional[RouteMatch]:
        """
        路由查询到最匹配的工具
        
        Args:
            query: 用户查询
            top_k: 返回前 k 个匹配
            threshold: 最低相似度阈值
        
        Returns:
            RouteMatch 或 None（包含可选的人格信息）
        """
        # 0. 人格匹配（优先检测复杂任务）
        persona_name, persona_content = None, None
        persona_result = self._match_persona(query)
        if persona_result:
            persona_name, persona_content = persona_result
        
        # 1. 规则匹配（优先，无需加载 embedding）
        rule_result = self._rule_match(query)
        if rule_result:
            tool_name, score = rule_result
            tool_info = self.tools[tool_name]
            return RouteMatch(
                tool_name=tool_name,
                skill_name=tool_info["skill"],
                score=score,
                tool_def=tool_info,
                extracted_args=self._extract_args(query, tool_name, tool_info),
                persona=persona_name,
                persona_content=persona_content
            )
        
        # 2. 语义匹配（兜底，延迟加载 embedding）
        if not self._embeddings_loaded:
            self._load_embeddings()
            self._embeddings_loaded = True
        
        if not self.embeddings:
            return None
        
        encoder = _get_encoder()
        query_embedding = encoder.encode(query)
        
        # 计算与所有工具的相似度
        scores: List[Tuple[str, float]] = []
        for tool_name, tool_embedding in self.embeddings.items():
            score = _cosine_similarity(query_embedding, tool_embedding)
            scores.append((tool_name, score))
        
        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if not scores or scores[0][1] < threshold:
            return None
        
        # 返回最佳匹配
        best_tool, best_score = scores[0]
        tool_info = self.tools[best_tool]
        
        return RouteMatch(
            tool_name=best_tool,
            skill_name=tool_info["skill"],
            score=best_score,
            tool_def=tool_info,
            extracted_args=self._extract_args(query, best_tool, tool_info),
            persona=persona_name,
            persona_content=persona_content
        )
    
    def route_all(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """返回所有工具的相似度排名"""
        encoder = _get_encoder()
        query_embedding = encoder.encode(query)
        
        scores = []
        for tool_name, tool_embedding in self.embeddings.items():
            score = _cosine_similarity(query_embedding, tool_embedding)
            scores.append((tool_name, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def route_by_tool_name(self, tool_name: str, args: Dict[str, Any] = None) -> Optional[RouteMatch]:
        """
        Direct routing by tool name (for MCP/API calls)
        
        Args:
            tool_name: Exact tool name to invoke
            args: Pre-parsed arguments (from MCP client)
        
        Returns:
            RouteMatch or None if tool not found
        """
        if tool_name not in self.tools:
            return None
        
        tool_info = self.tools[tool_name]
        return RouteMatch(
            tool_name=tool_name,
            skill_name=tool_info["skill"],
            score=1.0,  # Direct match
            tool_def=tool_info,
            extracted_args=args or {},
            persona=None,
            persona_content=None
        )
    
    def refresh(self):
        """刷新路由器（重新加载工具和 embedding）"""
        self.tools.clear()
        self.embeddings.clear()
        self._load_tools()
        self._load_embeddings()
    
    def stats(self) -> Dict[str, Any]:
        """返回路由器统计信息"""
        return {
            "tools_count": len(self.tools),
            "personas_count": len(self.personas),
            "embeddings_count": len(self.embeddings),
            "tools": list(self.tools.keys()),
            "personas": list(self.personas.keys())
        }


def check_requires(requires: Dict) -> Tuple[bool, List[str]]:
    """
    检查工具依赖是否满足（门控检查）
    
    Args:
        requires: {bins: [...], env: [...]}
    
    Returns:
        (satisfied, missing_list)
    """
    import shutil
    import os
    
    missing = []
    
    # 检查二进制依赖
    for bin_name in requires.get("bins", []):
        if not shutil.which(bin_name):
            missing.append(f"bin:{bin_name}")
    
    # 检查环境变量
    for env_name in requires.get("env", []):
        if not os.environ.get(env_name):
            missing.append(f"env:{env_name}")
    
    return len(missing) == 0, missing


def execute_tool(skill_dir: str, tool_name: str, args: Dict, tool_def: Dict) -> Dict:
    """执行工具 - 支持 shell 命令和 MCP 协议"""
    import subprocess
    import shlex
    import re
    
    # 门控检查：验证依赖是否满足
    requires = tool_def.get("requires", {})
    if requires:
        satisfied, missing = check_requires(requires)
        if not satisfied:
            return {
                "status": "error",
                "message": f"缺少依赖: {', '.join(missing)}",
                "requires": requires,
                "missing": missing
            }
    
    skill_path = SKILLS_DIR / skill_dir
    cmd_template = tool_def.get("command", "")
    
    if not cmd_template:
        return {"status": "error", "message": f"Tool '{tool_name}' has no command"}
    
    # === MCP 协议调用处理 ===
    if cmd_template.startswith("mcp://"):
        return _execute_mcp_tool(cmd_template, tool_name, args)
    
    # === 标准 Shell 命令处理 ===
    # 兼容性处理
    cmd_template = re.sub(r'<(\w+)>', r'{\1}', cmd_template)
    
    # 条件参数语法支持（与 nexus_executor.py 同步）
    def build_command(template: str, params: Dict[str, Any]) -> str:
        """Build command with conditional parameters"""
        result = template
        
        # Handle boolean flags: {param?--flag}
        for match in re.finditer(r'\{(\w+)\?\s*([^\}]+)\}', result):
            param_name, flag = match.groups()
            if params.get(param_name):
                result = result.replace(match.group(0), flag)
            else:
                result = result.replace(match.group(0), '')
        
        # Handle --option {param} patterns: skip entire pattern if param missing
        for match in re.finditer(r'--[\w-]+\s+\{(\w+)\}', result):
            param_name = match.group(1)
            if param_name not in params:
                result = result.replace(match.group(0), '')
        
        # Handle remaining value placeholders: {param}
        for match in re.finditer(r'\{(\w+)\}', result):
            param_name = match.group(1)
            if param_name in params:
                value = params[param_name]
                if isinstance(value, bool):
                    replacement = f'--{param_name.replace("_", "-")}' if value else ''
                else:
                    replacement = shlex.quote(str(value))
                result = result.replace(match.group(0), replacement)
            else:
                result = result.replace(match.group(0), '')
        
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    formatted_cmd = build_command(cmd_template, args)
    
    try:
        result = subprocess.run(
            formatted_cmd,
            shell=True,
            cwd=str(skill_path),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        status = "success" if result.returncode == 0 else "failure"
        return {
            "status": status,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout (120s)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _load_mcp_config() -> Dict:
    """加载 MCP 服务器配置"""
    config_paths = [
        WORKSPACE_ROOT / "config" / "mcp_servers.json",
        Path.home() / ".config" / "agent-hub" / "mcp_servers.json",
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception:
                continue
    
    # 默认配置
    return {
        "servers": {
            "chrome-devtools": {
                "command": ["npx", "chrome-devtools-mcp"],
                "args": ["--browserUrl", "http://127.0.0.1:9222"],
                "requires_chrome": True
            }
        },
        "default_timeout": 60
    }


def _execute_mcp_tool(cmd_template: str, tool_name: str, args: Dict) -> Dict:
    """执行 MCP 协议工具
    
    cmd_template 格式: mcp://server-name/tool-name
    例如: mcp://chrome-devtools/click
    """
    import subprocess
    import json
    
    # 解析 mcp://server/tool
    parts = cmd_template.replace("mcp://", "").split("/")
    if len(parts) < 2:
        return {"status": "error", "message": f"Invalid MCP URL: {cmd_template}"}
    
    server_name = parts[0]
    mcp_tool = parts[1] if len(parts) > 1 else tool_name
    
    # 加载 MCP 配置
    mcp_config = _load_mcp_config()
    servers = mcp_config.get("servers", {})
    
    server_config = servers.get(server_name)
    if not server_config:
        available = list(servers.keys())
        return {
            "status": "error", 
            "message": f"Unknown MCP server: {server_name}. Available: {available}",
            "hint": f"Add server config to config/mcp_servers.json"
        }
    
    # 检查 Chrome 是否运行（对于 chrome-devtools）
    if server_config.get("requires_chrome"):
        chrome_url = mcp_config.get("chrome_debug_port", "http://127.0.0.1:9222")
        try:
            import urllib.request
            urllib.request.urlopen(chrome_url, timeout=2)
        except:
            return {
                "status": "error",
                "message": f"Chrome DevTools 需要 Chrome 在调试模式下运行 ({chrome_url})",
                "hint": f"启动 Chrome: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={chrome_url.split(':')[-1]}"
            }
    
    # 构建 MCP JSON-RPC 请求
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": mcp_tool,
            "arguments": args
        }
    }
    
    # 构建命令
    cmd = server_config["command"] + server_config["args"]
    
    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"MCP server error: {result.stderr}",
                "stdout": result.stdout
            }
        
        # 解析 MCP 响应
        try:
            response = json.loads(result.stdout)
            if "result" in response:
                return {
                    "status": "success",
                    "stdout": json.dumps(response["result"], ensure_ascii=False),
                    "stderr": ""
                }
            elif "error" in response:
                return {
                    "status": "error",
                    "message": response["error"]
                }
            else:
                return {
                    "status": "success",
                    "stdout": result.stdout,
                    "stderr": ""
                }
        except json.JSONDecodeError:
            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "MCP timeout (60s)"}
    except Exception as e:
        return {"status": "error", "message": f"MCP execution error: {str(e)}"}


def main():
    import sys
    
    # 帮助信息函数
    def show_help():
        print("Agent-Hub - Write JSON, not glue code")
        print()
        print("用法:")
        print("  ah <查询>")
        print("  nexus <查询>")
        print()
        print("示例:")
        print('  ah "搜索 X 关于 AI Agent"')
        print('  ah "抓取 https://example.com"')
        print('  ah "深度研究 OpenAI 架构"')
        print()
        print("选项:")
        print("  -h, --help    显示帮助信息")
        print("  --top5        显示前 5 个匹配")
        print("  --stats       显示路由器统计")
        print("  --persona     仅显示人格匹配")
        print()
        print("更多信息: https://github.com/tong20242100/agent-hub")
        sys.exit(0)
    
    # 处理帮助参数
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        show_help()
    
    query = " ".join(sys.argv[1:])
    
    # 特殊命令
    if query == "--stats":
        router = SemanticRouter()
        stats = router.stats()
        print(f"📊 路由器统计:")
        print(f"   工具数: {stats['tools_count']}")
        print(f"   人格数: {len(router.personas)}")
        print(f"   Embedding 数: {stats['embeddings_count']}")
        return
    
    # 仅显示人格匹配
    if query == "--persona":
        router = SemanticRouter()
        print("🎭 可用人格:")
        for name, info in router.personas.items():
            desc = info.get("description", "")[:50]
            print(f"   {name}: {desc}...")
        return
    
    print(f"🎯 查询: {query}")
    print()
    
    router = SemanticRouter()
    
    # 显示 top 5
    if "--top5" in sys.argv:
        print("📍 前 5 个匹配:")
        for tool_name, score in router.route_all(query, top_k=5):
            tool_info = router.tools.get(tool_name, {})
            print(f"   {tool_name}: {score:.3f} ({tool_info.get('skill', '?')})")
        return
    
    # 正常路由
    match = router.route(query)
    
    if match:
        print(f"📍 最佳匹配:")
        print(f"   工具: {match.tool_name}")
        print(f"   技能: {match.skill_name}")
        print(f"   相似度: {match.score:.3f}")
        
        # 显示人格匹配
        if match.persona:
            print(f"   人格: {match.persona} (已激活)")
        
        # 显示 ai_hints（Codex 风格）
        ai_hints = match.tool_def.get("ai_hints", {})
        if ai_hints:
            if "when_to_use" in ai_hints:
                print(f"   使用场景: {ai_hints['when_to_use'][:60]}...")
            if "avoid" in ai_hints:
                print(f"   注意事项: {ai_hints['avoid'][:60]}...")
        
        print(f"   参数: {json.dumps(match.extracted_args, ensure_ascii=False)}")
        print()
        
        # 检查依赖
        requires = match.tool_def.get("requires", {})
        if requires:
            satisfied, missing = check_requires(requires)
            if not satisfied:
                print(f"⚠️  依赖检查失败: {', '.join(missing)}")
                print("   请安装缺少的依赖后再执行")
                return
            else:
                print(f"✅ 依赖检查通过")
        
        print("⚡ 执行中...")
        result = execute_tool(
            match.tool_def.get("skill_dir", ""),
            match.tool_name,
            match.extracted_args,
            match.tool_def
        )
        
        print()
        print("=" * 60)
        print("执行结果:")
        print("=" * 60)
        print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])
    else:
        print("❌ 未找到匹配的工具")
        print()
        print("前 5 个候选:")
        for tool_name, score in router.route_all(query, top_k=5):
            print(f"   {tool_name}: {score:.3f}")


if __name__ == "__main__":
    main()
