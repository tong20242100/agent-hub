#!/usr/bin/env python3
"""
Commander - 认知型人格指挥官模式

复杂任务 workflow:
1. 匹配认知型人格 (deep-researcher, viral-writer 等)
2. 人格作为指挥官分析任务
3. 指挥官决定调用哪些工具链
4. 整合所有工具输出，生成最终报告
"""

import os
import sys
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 添加项目路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(SCRIPT_DIR))

from bin.semantic_router import SemanticRouter, RouteMatch


@dataclass
class ToolCall:
    """工具调用计划"""
    tool_name: str
    reason: str  # 为什么调用这个工具
    args: Dict[str, Any]


@dataclass
class ExecutionPlan:
    """执行计划"""
    steps: List[ToolCall]
    reasoning: str  # 整体策略说明


class PersonaCommander:
    """认知型人格指挥官"""
    
    def __init__(self, persona_name: str, persona_content: str, router: SemanticRouter):
        self.persona_name = persona_name
        self.persona_content = persona_content
        self.router = router
        self.execution_history: List[Dict] = []
    
    def analyze_task(self, query: str) -> ExecutionPlan:
        """
        分析任务，制定执行计划
        使用简单的规则引擎，实际应该用LLM
        """
        steps = []
        
        # 基于人格类型的策略
        if "deep-researcher" in self.persona_name:
            # 深度研究员策略：多源信息收集
            steps = self._plan_research(query)
        elif "viral-writer" in self.persona_name:
            # 病毒写手策略：热点+创作
            steps = self._plan_viral_content(query)
        elif "github-researcher" in self.persona_name:
            # GitHub研究员策略：代码分析
            steps = self._plan_github_research(query)
        elif "engineering" in self.persona_name:
            # AI工程师策略：技术实现
            steps = self._plan_engineering(query)
        else:
            # 默认策略：直接匹配最佳工具
            steps = self._plan_default(query)
        
        reasoning = self._generate_reasoning(query, steps)
        return ExecutionPlan(steps=steps, reasoning=reasoning)
    
    def _plan_research(self, query: str) -> List[ToolCall]:
        """深度研究计划：搜索 → 抓取 → 分析"""
        steps = []
        
        # Step 1: 全网搜索获取最新信息
        steps.append(ToolCall(
            tool_name="search",
            reason="获取主题的最新全网信息",
            args={"query": query, "max": 10}
        ))
        
        # Step 2: 检查本地知识库
        steps.append(ToolCall(
            tool_name="memory_query",
            reason="查询本地知识库是否有相关研究",
            args={"query": query}
        ))
        
        return steps
    
    def _plan_viral_content(self, query: str) -> List[ToolCall]:
        """病毒内容计划：热点分析 → 内容创作"""
        steps = []
        
        # Step 1: 搜索热点话题
        steps.append(ToolCall(
            tool_name="search",
            reason="分析当前热点和相关话题",
            args={"query": f"{query} 热点 趋势", "max": 5}
        ))
        
        # Step 2: 病毒内容引擎（如果有）
        if "viral-engine" in self.router.tools:
            steps.append(ToolCall(
                tool_name="viral-engine",
                reason="分析病毒传播潜力",
                args={"topic": query}
            ))
        
        return steps
    
    def _plan_github_research(self, query: str) -> List[ToolCall]:
        """GitHub研究计划：仓库搜索 → 代码分析"""
        steps = []
        
        # Step 1: 提取仓库名或搜索
        repo_match = re.search(r'([\w-]+/[\w-]+)', query)
        if repo_match:
            repo = repo_match.group(1)
            steps.append(ToolCall(
                tool_name="gh_repo",
                reason=f"获取仓库 {repo} 信息",
                args={"repo": repo}
            ))
        else:
            steps.append(ToolCall(
                tool_name="search",
                reason=f"搜索 GitHub 相关项目: {query}",
                args={"query": f"{query} github", "max": 5}
            ))
        
        return steps
    
    def _plan_engineering(self, query: str) -> List[ToolCall]:
        """工程实现计划：需求分析 → 方案设计"""
        steps = []
        
        # 技术问题通常需要搜索最佳实践
        steps.append(ToolCall(
            tool_name="search",
            reason="搜索技术方案和最佳实践",
            args={"query": query, "max": 5}
        ))
        
        # 检查是否需要代码分析
        if "github" in query.lower() or "代码" in query:
            steps.append(ToolCall(
                tool_name="gh_repo",
                reason="分析相关开源实现",
                args={"repo": "placeholder"}  # 需要动态提取
            ))
        
        return steps
    
    def _plan_default(self, query: str) -> List[ToolCall]:
        """默认计划：直接匹配最佳工具"""
        match = self.router.route(query)
        if match:
            return [ToolCall(
                tool_name=match.tool_name,
                reason="直接匹配的最佳工具",
                args=match.extracted_args
            )]
        return []
    
    def _generate_reasoning(self, query: str, steps: List[ToolCall]) -> str:
        """生成策略说明"""
        persona_title = self.persona_name.replace("agency-", "").replace("-", " ").title()
        
        if not steps:
            return f"{persona_title}: 未找到合适的执行策略"
        
        tool_list = ", ".join([s.tool_name for s in steps])
        return f"{persona_title} 策略: 通过 [{tool_list}] 完成 '{query}'"
    
    def _execute_local_bin(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """直接执行本地 bin/ 目录下的脚本"""
        import subprocess
        
        WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bin_path = os.path.join(WORKSPACE_ROOT, "bin", tool_name)
        
        if not os.path.exists(bin_path):
            return {"status": "error", "message": f"Tool not found: {bin_path}"}
        
        # 构建命令列表 (不使用 shell=True)
        cmd_list = [bin_path]
        
        # 添加参数
        if tool_name == "search":
            if "query" in args:
                cmd_list.append(args["query"])
            if "max" in args:
                cmd_list.extend(["--max", str(args["max"])])
            if args.get("json"):
                cmd_list.append("--json")
        elif tool_name == "scrape":
            if "url" in args:
                cmd_list.append(args["url"])
            if args.get("recursive"):
                cmd_list.append("--recursive")
        elif tool_name == "gh":
            # gh 命令直接传递
            for v in args.values():
                cmd_list.append(str(v))
        else:
            # 通用参数传递
            for value in args.values():
                cmd_list.append(str(value))
        
        try:
            result = subprocess.run(
                cmd_list,
                shell=False,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "status": "success" if result.returncode == 0 else "failure",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "context": {
                    "command": " ".join(cmd_list[:5]) + ("..." if len(cmd_list) > 5 else ""),
                    "tool": tool_name
                }
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Timeout (60s)",
                "context": {
                    "command": " ".join(cmd_list[:5]) + ("..." if len(cmd_list) > 5 else ""),
                    "tool": tool_name
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "context": {
                    "command": " ".join(cmd_list[:5]) + ("..." if len(cmd_list) > 5 else ""),
                    "tool": tool_name
                }
            }
    
    def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """执行计划，收集所有工具输出"""
        results = {
            "commander": self.persona_name,
            "strategy": plan.reasoning,
            "steps": [],
            "final_output": None
        }
        
        print(f"\n🎭 {self.persona_name.replace('agency-', '').replace('-', ' ').title()} 指挥官")
        print(f"📋 策略: {plan.reasoning}")
        print(f"🔧 计划执行 {len(plan.steps)} 个工具\n")
        
        # 定义本地 bin 工具
        LOCAL_BIN_TOOLS = {"search", "scrape", "gh", "nvidia", "runner"}
        
        # 从 semantic_router 导入 execute_tool
        from bin.semantic_router import execute_tool as router_execute_tool
        
        for i, step in enumerate(plan.steps, 1):
            print(f"  Step {i}/{len(plan.steps)}: {step.tool_name}")
            print(f"    目的: {step.reason}")
            
            # 判断使用哪种执行方式
            try:
                if step.tool_name in LOCAL_BIN_TOOLS:
                    # 直接执行本地 bin 工具
                    result = self._execute_local_bin(step.tool_name, step.args)
                else:
                    # 使用 router 执行其他工具
                    tool_def = self.router.tools.get(step.tool_name, {})
                    if not tool_def:
                        print(f"    ❌ 工具未找到")
                        continue
                    
                    skill_dir = tool_def.get("skill_dir", "")
                    result = router_execute_tool(skill_dir, step.tool_name, step.args, tool_def)
                
                # 记录结果
                step_result = {
                    "step": i,
                    "tool": step.tool_name,
                    "status": result.get("status", "unknown"),
                    "output": result.get("stdout", "")[:500],  # 截断
                    "error": result.get("stderr", "")[:200] if result.get("stderr") else None
                }
                results["steps"].append(step_result)
                
                if result.get("status") == "success":
                    print(f"    ✅ 成功")
                else:
                    print(f"    ⚠️  {result.get('status', 'unknown')}")
                
                self.execution_history.append({
                    "tool": step.tool_name,
                    "result": result
                })
                
            except Exception as e:
                print(f"    ❌ 错误: {e}")
                results["steps"].append({
                    "step": i,
                    "tool": step.tool_name,
                    "status": "error",
                    "error": str(e)
                })
        
        # 生成最终输出（简单整合，实际应该用LLM）
        results["final_output"] = self._synthesize_output(results["steps"])
        
        return results
    
    def _synthesize_output(self, steps: List[Dict]) -> str:
        """整合所有步骤输出为最终报告"""
        outputs = []
        for step in steps:
            if step.get("status") == "success" and step.get("output"):
                outputs.append(f"## {step['tool']}\n{step['output'][:800]}\n")
        
        if not outputs:
            return "未收集到有效信息"
        
        header = f"# {self.persona_name.replace('agency-', '').replace('-', ' ').title()} 报告\n\n"
        return header + "\n".join(outputs)


def execute_with_commander(query: str, router: SemanticRouter) -> Optional[Dict[str, Any]]:
    """
    指挥官模式入口
    
    如果匹配到认知型人格，使用指挥官模式
    否则使用普通工具执行
    """
    # 首先尝试匹配人格
    persona_name = None
    persona_content = None
    
    # 使用 router 的人格匹配
    persona_result = router._match_persona(query)
    if persona_result:
        persona_name, persona_content = persona_result
    
    # 如果没有匹配到人格，使用普通模式
    if not persona_name:
        match = router.route(query)
        if not match:
            return None
        
        from bin.semantic_router import execute_tool
        result = execute_tool(
            match.tool_def.get("skill_dir", ""),
            match.tool_name,
            match.extracted_args,
            match.tool_def
        )
        return {
            "mode": "direct",
            "tool": match.tool_name,
            "result": result
        }
    
    # 指挥官模式
    commander = PersonaCommander(persona_name, persona_content, router)
    plan = commander.analyze_task(query)
    return commander.execute_plan(plan)


if __name__ == "__main__":
    # 测试
    if len(sys.argv) < 2:
        print("用法: python3 bin/commander.py <查询>")
        print()
        print('示例: python3 bin/commander.py "深度研究 AI Agent"')
        print('      python3 bin/commander.py "写病毒推文关于 Claude Code"')
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    print(f"🎯 任务: {query}")
    print("=" * 60)
    
    router = SemanticRouter()
    result = execute_with_commander(query, router)
    
    if result:
        print("\n" + "=" * 60)
        print("执行完成")
        if result.get("mode") == "direct":
            print(f"模式: 直接工具调用 ({result['tool']})")
        else:
            print(f"模式: 指挥官模式 ({result.get('commander', 'unknown')})")
            print("\n最终输出:")
            print(result.get("final_output", "无输出")[:2000])
    else:
        print("❌ 未找到匹配")
