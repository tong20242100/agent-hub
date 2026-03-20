#!/usr/bin/env python3
"""
LLM Router - 用小型 LLM 替代正则做工具路由和参数提取

设计原则：
- 单次 LLM 调用完成工具选择 + 参数提取
- 失败时降级到原有正则方案
- 通过 config/model_router.json 配置

用法:
    from bin.llm_router import LLMRouter
    router = LLMRouter()
    result = router.route("搜索 AI Agent 最新进展")
"""
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

WORKSPACE_ROOT = Path(__file__).parent.parent
CONFIG_PATH = WORKSPACE_ROOT / "config" / "model_router.json"
MANIFEST_PATH = WORKSPACE_ROOT / "knowledge" / "tools_manifest.json"
SKILLS_DIR = WORKSPACE_ROOT / "skills"


@dataclass
class LLMRouteResult:
    """LLM 路由结果"""
    tool_name: str
    args: Dict[str, Any]
    reasoning: str
    confidence: float
    latency_ms: float
    backend: str  # "llm" or "fallback"
    persona: Optional[str] = None  # 显式指定的 persona


class LLMRouter:
    """
    基于 LLM 的智能路由器
    
    一次调用完成：
    1. 工具选择（理解用户意图）
    2. 参数提取（理解参数语义）
    """
    
    def __init__(self, backend: str = "auto"):
        """
        Args:
            backend: "auto" | "llm" | "fallback"
        """
        self.backend = backend
        self.config = self._load_config()
        self.tools_manifest = self._load_manifest()
        self.personas = self._load_personas()
        self._fallback_router = None
    
    def _load_config(self) -> Dict:
        """加载模型路由配置"""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH) as f:
                return json.load(f)
        return {
            "proxy_config": {
                "base_url": "http://127.0.0.1:18788/v1",
                "timeout_ms": 30000
            },
            "mission_routing": {
                "triage": ["openai/gpt-oss-20b"]
            }
        }
    
    def _load_manifest(self) -> List[Dict]:
        """加载工具清单"""
        if MANIFEST_PATH.exists():
            with open(MANIFEST_PATH) as f:
                return json.load(f).get("tools", [])
        return []
    
    def _load_personas(self) -> Dict[str, Dict]:
        """加载认知型人格（显式指定时使用）"""
        personas = {}
        for schema_path in SKILLS_DIR.glob("*/SCHEMA.json"):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = json.load(f)
                
                if schema.get("type") != "cognitive":
                    continue
                
                skill_name = schema.get("name", schema_path.parent.name)
                skill_file = schema.get("skill_file", "SKILL.md")
                
                # 加载 SKILL.md 内容
                skill_md_path = schema_path.parent / skill_file
                skill_content = ""
                if skill_md_path.exists():
                    with open(skill_md_path, 'r', encoding='utf-8') as f:
                        skill_content = f.read()
                
                personas[skill_name] = {
                    "description": schema.get("description", ""),
                    "content": skill_content,
                }
            except Exception:
                continue
        
        return personas
    
    def get_persona(self, name: str) -> Optional[str]:
        """获取指定 persona 的内容"""
        return self.personas.get(name, {}).get("content")
    
    def list_personas(self) -> List[str]:
        """列出所有可用的 persona"""
        return list(self.personas.keys())
    
    def _build_tools_description(self) -> str:
        """构建精简工具列表（优先高频工具）"""
        # 高频工具优先
        priority_tools = [
            "web_search", "scrape_url", "stealth_get", "fetch",
            "gh_view", "analyze_repo", 
            "x_search", "x_user", "x_tweet",
            "memory_query", "memory_save",
            "extract",
        ]
        
        # 先放优先工具
        lines = []
        seen = set()
        
        for tool in self.tools_manifest:
            name = tool.get("name", "")
            if name in priority_tools and name not in seen:
                desc = tool.get("description", "")[:40]
                lines.append(f"{name}: {desc}")
                seen.add(name)
        
        # 再放其他工具（限制总数）
        for tool in self.tools_manifest[:30]:
            name = tool.get("name", "")
            if name not in seen and len(lines) < 25:
                desc = tool.get("description", "")[:40]
                lines.append(f"{name}: {desc}")
                seen.add(name)
        
        return "\n".join(lines)
    
    def _build_prompt(self, query: str) -> str:
        """构建路由 prompt"""
        tools_desc = self._build_tools_description()
        
        return f"""你是工具路由器。分析请求，选择工具并提取参数。

工具列表:
{tools_desc}

请求: {query}

返回 JSON:
{{"tool": "工具名", "args": {{}}, "reason": "理由", "confidence": 0.9}}

规则:
1. tool 必须在上述列表中
2. 只返回 JSON
3. confidence 0-1"""
    
    def _call_llm(self, prompt: str) -> Optional[Dict]:
        """调用 LLM"""
        proxy_url = self.config.get("proxy_config", {}).get(
            "base_url", "http://127.0.0.1:18788/v1"
        )
        timeout_s = self.config.get("proxy_config", {}).get("timeout_ms", 30000) / 1000
        
        # 明确指定工具路由模型
        model = self.config.get("agent_hub", {}).get("tool_router", "openai/gpt-oss-20b")
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.0
        }
        
        try:
            cmd = [
                "curl", "-s", "-X", "POST",
                f"{proxy_url}/chat/completions",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
                "--max-time", str(timeout_s)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s + 5)
            body = json.loads(result.stdout)
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # 解析 JSON
            if content:
                # 移除 thinking 前缀
                if '---' in content:
                    content = content.split('---')[-1].strip()
                
                # 尝试提取 JSON（支持嵌套）
                import re
                # 找到最后一个完整的 JSON 对象
                brace_count = 0
                json_start = -1
                for i, c in enumerate(content):
                    if c == '{':
                        if brace_count == 0:
                            json_start = i
                        brace_count += 1
                    elif c == '}':
                        brace_count -= 1
                        if brace_count == 0 and json_start >= 0:
                            json_str = content[json_start:i+1]
                            try:
                                return json.loads(json_str)
                            except:
                                continue
                return None
            return None
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return None
    
    def _fallback_route(self, query: str) -> Optional[tuple]:
        """降级到正则路由"""
        if self._fallback_router is None:
            from bin.semantic_router import SemanticRouter
            self._fallback_router = SemanticRouter()
        
        match = self._fallback_router.route(query)
        if match:
            return match.tool_name, match.extracted_args
        return None
    
    def route(self, query: str, persona: str = None) -> Optional[LLMRouteResult]:
        """
        路由查询到最合适的工具
        
        Args:
            query: 用户查询
            persona: 显式指定的 persona 名称（可选）
        """
        # 优先 LLM
        if self.backend in ("auto", "llm"):
            prompt = self._build_prompt(query)
            start = time.time()
            result = self._call_llm(prompt)
            latency_ms = (time.time() - start) * 1000
            
            if result and result.get("tool"):
                return LLMRouteResult(
                    tool_name=result["tool"],
                    args=result.get("args", {}),
                    reasoning=result.get("reason", ""),
                    confidence=result.get("confidence", 0.5),
                    latency_ms=latency_ms,
                    backend="llm",
                    persona=persona
                )
        
        # 降级正则
        if self.backend in ("auto", "fallback"):
            start = time.time()
            fallback = self._fallback_route(query)
            latency_ms = (time.time() - start) * 1000
            
            if fallback:
                tool_name, args = fallback
                return LLMRouteResult(
                    tool_name=tool_name,
                    args=args,
                    reasoning="Fallback to regex",
                    confidence=0.3,
                    latency_ms=latency_ms,
                    backend="fallback",
                    persona=persona
                )
        
        return None


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("LLM Router - 用小型 LLM 做工具路由")
        print("\n用法:")
        print("  python3 bin/llm_router.py '搜索 AI Agent 最新进展'")
        print("  python3 bin/llm_router.py --persona linus '审查这段代码'")
        print("\n可用 persona:")
        router = LLMRouter()
        for name in router.list_personas():
            print(f"  - {name}")
        sys.exit(0)
    
    # 解析参数
    persona = None
    args = sys.argv[1:]
    
    if args and args[0] == "--persona":
        if len(args) >= 2:
            persona = args[1]
            args = args[2:]
        else:
            print("❌ --persona 需要指定 persona 名称")
            sys.exit(1)
    
    if not args:
        print("❌ 缺少查询内容")
        sys.exit(1)
    
    query = " ".join(args)
    print(f"🎯 {query}")
    if persona:
        print(f"👤 Persona: {persona}")
    print()
    
    router = LLMRouter()
    result = router.route(query, persona=persona)
    
    if result:
        print(f"📍 工具: {result.tool_name}")
        print(f"   参数: {json.dumps(result.args, ensure_ascii=False)}")
        print(f"   理由: {result.reasoning}")
        print(f"   置信: {result.confidence:.2f}")
        print(f"   延迟: {result.latency_ms:.0f}ms ({result.backend})")
        
        if persona:
            persona_content = router.get_persona(persona)
            if persona_content:
                print(f"\n📝 Persona 内容 ({len(persona_content)} chars):")
                print(persona_content[:200] + "...")
    else:
        print("❌ 路由失败")


if __name__ == "__main__":
    main()
