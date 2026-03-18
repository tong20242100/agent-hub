#!/usr/bin/env python3
"""
Nexus Protocol Executor - 执行 SCHEMA.json 定义的工具

借鉴 Codex CLI 的门控设计：
1. 验证参数（Schema Validation）
2. 检查依赖（Requires Gating）
3. 执行命令
4. 返回结果
"""
import json
import os
import sys
import subprocess
import argparse
import shlex
import re
import shutil
from jsonschema import validate, ValidationError
from typing import Dict, List, Tuple, Any


def check_requires(requires: Dict) -> Tuple[bool, List[str]]:
    """
    检查工具依赖是否满足（门控检查）
    
    借鉴 Codex CLI 的设计：
    - bins: 检查二进制是否在 PATH 中
    - env: 检查环境变量是否设置
    
    Args:
        requires: {bins: [...], env: [...]}
    
    Returns:
        (satisfied, missing_list)
    """
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


def run_tool(skill_name, tool_name, args_json):
    workspace_root = os.getcwd()
    skill_dir = os.path.join(workspace_root, "skills", skill_name)
    schema_path = os.path.join(skill_dir, "SCHEMA.json")

    if not os.path.exists(schema_path):
        return {"status": "error", "message": f"Skill '{skill_name}' missing SCHEMA.json"}

    with open(schema_path, 'r') as f:
        schema_data = json.load(f)

    if tool_name not in schema_data["tools"]:
        return {"status": "error", "message": f"Tool '{tool_name}' not defined"}

    tool_def = schema_data["tools"][tool_name]
    
    # 1. Check Requires (门控检查 - Codex 风格)
    requires = schema_data.get("requires", {})
    if requires:
        satisfied, missing = check_requires(requires)
        if not satisfied:
            return {
                "status": "error",
                "message": f"缺少依赖: {', '.join(missing)}",
                "requires": requires,
                "missing": missing,
                "hint": f"请安装缺少的依赖后重试。bins 可通过 brew/apt 安装，env 需要在环境变量中设置。"
            }
    
    # 2. Validate Args
    try:
        args = json.loads(args_json)
        validate(instance=args, schema=tool_def["parameters"])
    except ValidationError as e:
        return {"status": "error", "message": f"Schema validation failed: {e.message}"}

    # 2. Command Sanitization & Formatting
    cmd_template = tool_def["command"]
    
    # Compatibility: Convert <param> to {param}
    cmd_template = re.sub(r'<(\w+)>', r'{\1}', cmd_template)
    
    # Build command with conditional parameter support
    # Syntax: {param?--flag} - adds --flag if param is truthy
    # Syntax: --option {param} - replaced with value, skipped if param not in args
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
        # Match: --option {param} where param might not be in args
        for match in re.finditer(r'--[\w-]+\s+\{(\w+)\}', result):
            param_name = match.group(1)
            if param_name not in params:
                result = result.replace(match.group(0), '')
        
        # Handle remaining value placeholders: {param}
        for match in re.finditer(r'\{(\w+)\}', result):
            param_name = match.group(1)
            if param_name in params:
                value = params[param_name]
                # Boolean true becomes the param name as flag
                if isinstance(value, bool):
                    replacement = f'--{param_name.replace("_", "-")}' if value else ''
                else:
                    replacement = shlex.quote(str(value))
                result = result.replace(match.group(0), replacement)
            else:
                # Param not found, remove the placeholder
                result = result.replace(match.group(0), '')
        
        # Clean up multiple spaces and trailing/leading options
        result = re.sub(r'\s+', ' ', result).strip()
        return result
    
    formatted_cmd = build_command(cmd_template, args)

    # 3. Execute (使用 shell=False 避免命令注入风险)
    try:
        # 将命令字符串转换为列表，避免 shell=True
        cmd_list = shlex.split(formatted_cmd)
        result = subprocess.run(
            cmd_list,
            shell=False,
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=120  # 添加超时保护
        )
        
        stdout_trimmed = result.stdout.strip()
        is_empty_json = stdout_trimmed in ["{}", "[]", "null", ""]
        is_too_short = len(stdout_trimmed) < 20 and tool_name in ["scrape_url", "stealth_get", "x_search"]
        
        status = "success" if result.returncode == 0 else "failure"
        if status == "success" and (is_empty_json or is_too_short):
            status = "suspicious_empty" # 命中风控降级判定

        return {
            "status": status,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "is_empty": is_empty_json or is_too_short,
            "context": {
                "command": formatted_cmd[:200],  # 截断防止过长
                "cwd": skill_dir,
                "tool": tool_name
            }
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Timeout (120s)",
            "context": {
                "command": formatted_cmd[:200],
                "cwd": skill_dir,
                "tool": tool_name
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "context": {
                "command": formatted_cmd[:200] if 'formatted_cmd' in dir() else "unknown",
                "cwd": skill_dir,
                "tool": tool_name
            }
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nexus Protocol Executor")
    parser.add_argument("--skill", required=True, help="Skill folder name")
    parser.add_argument("--tool", required=True, help="Tool name within SCHEMA.json")
    parser.add_argument("--args", required=True, help="JSON string of arguments")

    args = parser.parse_args()
    
    output = run_tool(args.skill, args.tool, args.args)
    print(json.dumps(output, ensure_ascii=False, indent=2))
