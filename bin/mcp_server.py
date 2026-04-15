#!/usr/bin/env python3
"""
Agent-Hub MCP Server - Expose skills to Claude Desktop / Gemini CLI / Cursor

设计原则（Linus 式）：
1. 数据驱动：从 SCHEMA.json 自动发现，不硬编码
2. 信任 Agent：让 LLM 自己选择工具，不预判断
3. 消除特殊情况：统一的加载逻辑

架构：
  MCP 客户端 → mcp_server.py → SCHEMA.json → 执行工具

Usage:
    # Claude Desktop config:
    {
      "mcpServers": {
        "agent-hub": {
          "command": "python3",
          "args": ["/path/to/agent-hub/bin/mcp_server.py"]
        }
      }
    }
"""
import json
import asyncio
import sys
import subprocess
import shlex
import shutil
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
SKILLS_DIR = WORKSPACE_ROOT / "skills"

# Initialize MCP server
server = Server("agent-hub")


def load_all_schemas() -> Dict[str, Dict]:
    """
    加载所有 skills 的 SCHEMA.json
    
    只排除 type="cognitive" 的技能（思维框架，不是可执行工具）
    """
    schemas = {}
    
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        
        schema_path = skill_dir / "SCHEMA.json"
        if not schema_path.exists():
            continue
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # 跳过认知型技能（思维框架，不是可执行工具）
            if schema.get("type") == "cognitive":
                continue
            
            skill_name = schema.get("name", skill_dir.name)
            schemas[skill_name] = {
                "schema": schema,
                "skill_dir": str(skill_dir),
            }
        except Exception as e:
            print(f"Warning: Failed to load {schema_path}: {e}", file=sys.stderr)
    
    return schemas


def build_tool_description(tool_name: str, tool_def: Dict, schema: Dict) -> str:
    """构建工具描述，包含 ai_hints 让 LLM 能精准选择"""
    parts = []
    
    base_desc = tool_def.get("description", "")
    if base_desc:
        parts.append(base_desc)
    
    ai_hints = tool_def.get("ai_hints", {})
    
    if ai_hints.get("when_to_use"):
        parts.append(f"\n使用场景: {ai_hints['when_to_use']}")
    
    if ai_hints.get("examples"):
        examples = ai_hints["examples"]
        if examples:
            example_str = json.dumps(examples[0], ensure_ascii=False)
            parts.append(f"\n示例: {example_str}")
    
    if ai_hints.get("avoid"):
        parts.append(f"\n注意: {ai_hints['avoid']}")
    
    return "".join(parts)


def get_all_tools() -> List[Dict]:
    """从 SCHEMA.json 自动发现所有可执行工具"""
    tools = []
    schemas = load_all_schemas()
    
    for skill_name, skill_data in schemas.items():
        schema = skill_data["schema"]
        skill_dir = skill_data["skill_dir"]
        
        for tool_name, tool_def in schema.get("tools", {}).items():
            # 跳过委托型工具（delegate_to 是说明，不是实现）
            if tool_def.get("delegate_to"):
                continue
            
            tools.append({
                "tool_name": tool_name,
                "skill_name": skill_name,
                "skill_dir": skill_dir,
                "description": build_tool_description(tool_name, tool_def, schema),
                "parameters": tool_def.get("parameters", {
                    "type": "object",
                    "properties": {},
                    "required": []
                }),
                "command": tool_def.get("command", ""),
                "requires": schema.get("requires", {}),
            })
    
    return tools


def check_requires(requires: Dict) -> tuple[bool, List[str]]:
    """检查工具依赖是否满足"""
    missing = []
    
    for bin_name in requires.get("bins", []):
        if not shutil.which(bin_name):
            missing.append(f"bin:{bin_name}")
    
    for env_name in requires.get("env", []):
        if not os.environ.get(env_name):
            missing.append(f"env:{env_name}")
    
    return len(missing) == 0, missing


def build_command(template: str, params: Dict[str, Any]) -> str:
    """构建命令，支持条件参数语法"""
    result = template
    
    # Handle boolean flags: {param?--flag}
    for match in re.finditer(r'\{(\w+)\?\s*([^\}]+)\}', result):
        param_name, flag = match.groups()
        if params.get(param_name):
            result = result.replace(match.group(0), flag)
        else:
            result = result.replace(match.group(0), '')
    
    # Handle --option {param} patterns
    for match in re.finditer(r'--[\w-]+\s+\{(\w+)\}', result):
        param_name = match.group(1)
        if param_name not in params:
            result = result.replace(match.group(0), '')
    
    # Handle value placeholders: {param}
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


def validate_result(result: Dict) -> Dict:
    """快速验证执行结果（内联 reality check）"""
    checks = []
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)
    
    # Check 1: 输出长度
    if not stdout or len(stdout.strip()) < 50:
        checks.append({"check": "output_length", "result": "FAIL", "concern": "输出过短"})
    else:
        checks.append({"check": "output_length", "result": "PASS"})
    
    # Check 2: 退出码
    if exit_code != 0:
        checks.append({"check": "exit_code", "result": "FAIL", "concern": f"Exit code: {exit_code}"})
    else:
        checks.append({"check": "exit_code", "result": "PASS"})
    
    # Check 3: 无错误关键词
    error_patterns = ["error:", "exception:", "traceback", "undefined", "null"]
    stdout_lower = stdout.lower()
    found = [p for p in error_patterns if p in stdout_lower]
    if found:
        checks.append({"check": "no_errors", "result": "FAIL", "concern": f"发现错误关键词: {found[:2]}"})
    else:
        checks.append({"check": "no_errors", "result": "PASS"})
    
    passed = sum(1 for c in checks if c["result"] == "PASS")
    return {"checks": checks, "passed": passed, "total": len(checks), "ok": passed == len(checks)}


def execute_tool(tool_info: Dict, arguments: Dict) -> Dict:
    """执行工具"""
    skill_dir = tool_info["skill_dir"]
    command_template = tool_info["command"]
    
    formatted_cmd = build_command(command_template, arguments)
    
    cmd_list = shlex.split(formatted_cmd)
    if not cmd_list:
        return {"status": "error", "message": "Failed to build a valid command from template"}
        
    if cmd_list[0].startswith("bin/"):
        cmd_list[0] = str(WORKSPACE_ROOT / cmd_list[0])
    
    try:
        result = subprocess.run(
            cmd_list,
            shell=False,
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        cmd_str = " ".join(cmd_list[:5]) + ("..." if len(cmd_list) > 5 else "")
        output = {
            "status": "success" if result.returncode == 0 else "failure",
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "context": {
                "command": cmd_str[:200],
                "tool": tool_info["tool_name"],
            }
        }
        # 自动验证
        output["validation"] = validate_result(output)
        return output
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Timeout (120s)"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============ MCP Handlers ============

_tools_cache: Optional[List[Dict]] = None


@server.list_tools()
async def list_tools() -> list[Tool]:
    """返回所有可用工具给 MCP 客户端"""
    global _tools_cache
    
    if _tools_cache is None:
        _tools_cache = get_all_tools()
    
    tools = []
    for tool_info in _tools_cache:
        tool = Tool(
            name=tool_info["tool_name"],
            description=tool_info["description"],
            inputSchema=tool_info["parameters"]
        )
        tools.append(tool)
    
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """执行工具"""
    global _tools_cache
    
    try:
        if _tools_cache is None:
            _tools_cache = get_all_tools()
        
        tool_info = None
        for t in _tools_cache:
            if t["tool_name"] == name:
                tool_info = t
                break
        
        if not tool_info:
            return [TextContent(type="text", text=f"Error: Tool '{name}' not found")]
        
        # 检查依赖
        requires = tool_info.get("requires", {})
        if requires:
            satisfied, missing = check_requires(requires)
            if not satisfied:
                return [TextContent(
                    type="text",
                    text=f"Error: Missing dependencies: {', '.join(missing)}"
                )]
        
        result = execute_tool(tool_info, arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============ 入口 ============

async def main():
    """Run MCP server over stdio"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
