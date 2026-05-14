#!/usr/bin/env python3
"""
Agent-Hub MCP Server - Minimalist, Intent-Driven & Priority-Truncated
"""

import asyncio
import json
import logging
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Prompt, Tool
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agent-hub.mcp")

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
LOG_DIR = WORKSPACE_ROOT / "knowledge" / "logs"
MANIFEST_PATH = WORKSPACE_ROOT / "knowledge" / "tools_manifest.json"
SKILLS_DIRS = [WORKSPACE_ROOT / "skills", WORKSPACE_ROOT / "skills-cognitive"]

EXCLUDED_TOOLS = {
    "performance_start_trace",
    "performance_stop_trace",
    "performance_analyze_insight",
    "take_memory_snapshot",
    "bb_daemon",
    "bb_network",
    "update_check_json",
    "update_deps",
    "defuddle_extract_title",
    "defuddle_extract_author",
    "defuddle_extract_metadata",
}

# Cache with TTL
_CACHE: Dict[str, Any] = {}
_CACHE_TTL: Dict[str, float] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _get_cache(key: str) -> Optional[Any]:
    if key in _CACHE:
        if time.time() - _CACHE_TTL.get(key, 0) < CACHE_TTL_SECONDS:
            return _CACHE[key]
        del _CACHE[key]
        _CACHE_TTL.pop(key, None)
    return None


def _set_cache(key: str, value: Any) -> None:
    _CACHE[key] = value
    _CACHE_TTL[key] = time.time()


def _invalidate_cache(key: str) -> None:
    _CACHE.pop(key, None)
    _CACHE_TTL.pop(key, None)


def find_all_skill_dirs() -> List[Path]:
    dirs = []
    for b in SKILLS_DIRS:
        if b.exists():
            dirs.extend(
                [i for i in b.iterdir() if i.is_dir() and not i.name.startswith(".")]
            )
    return dirs


def load_all_schemas(
    skill_filter: Optional[List[str]] = None,
) -> Dict[str, Dict]:
    schemas = {}
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                for t in json.load(f).get("tools", []):
                    sk = t.get("skill")
                    if not sk or (skill_filter and sk not in skill_filter):
                        continue
                    if sk not in schemas:
                        sdp = WORKSPACE_ROOT / "skills" / t.get("skill_dir", sk)
                        m_s, m_n, v, sp = None, None, "0.0.1", sdp / "SCHEMA.json"
                        if sp.exists():
                            try:
                                with open(sp) as fp:
                                    ps = json.load(fp)
                                m_s, m_n, v = (
                                    ps.get("mcp_strategy"),
                                    ps.get("merged_name"),
                                    ps.get("version", v),
                                )
                            except json.JSONDecodeError as e:
                                logger.warning("Malformed SCHEMA.json at %s: %s", sp, e)
                            except PermissionError as e:
                                logger.error("Permission denied reading %s: %s", sp, e)
                        schemas[sk] = {
                            "schema": {
                                "name": sk,
                                "version": v,
                                "tools": {},
                                "mcp_strategy": m_s,
                                "merged_name": m_n,
                            },
                            "skill_dir": str(sdp),
                        }
                    schemas[sk]["schema"]["tools"][t["name"]] = {
                        "description": t.get("description", ""),
                        "parameters": t.get("parameters", {}),
                        "ai_hints": t.get("ai_hints", {}),
                        "command": t.get("command", ""),
                    }
        except (json.JSONDecodeError, PermissionError) as e:
            logger.error("Failed to load manifest %s: %s", MANIFEST_PATH, e)

    for sd in find_all_skill_dirs():
        if not sd.is_dir() or (skill_filter and sd.name not in skill_filter):
            continue
        sp = sd / "SCHEMA.json"
        if sp.exists():
            try:
                with open(sp) as f:
                    s = json.load(f)
                    if s.get("type") != "cognitive":
                        schemas[s.get("name", sd.name)] = {
                            "schema": s,
                            "skill_dir": str(sd),
                        }
            except json.JSONDecodeError as e:
                logger.warning("Malformed SCHEMA.json at %s: %s", sp, e)
            except PermissionError as e:
                logger.error("Permission denied reading %s: %s", sp, e)
    return schemas


def load_all_prompts() -> Dict[str, Dict]:
    pm = {}
    for sd in find_all_skill_dirs():
        sp = sd / "SCHEMA.json"
        if sp.exists():
            try:
                with open(sp) as f:
                    s = json.load(f)
                    if "prompts" in s:
                        for p in s["prompts"]:
                            pm[p["name"]] = {
                                "instructions": p["instructions"],
                                "description": p.get("description", ""),
                            }
            except json.JSONDecodeError as e:
                logger.warning("Malformed SCHEMA.json at %s: %s", sp, e)
            except PermissionError as e:
                logger.error("Permission denied reading %s: %s", sp, e)
    return pm


def build_tool_description(tool_name: str, tool_def: Dict, schema: Dict) -> str:
    """Priority Truncation: Metadata over Raw Description"""
    base_desc = tool_def.get("description", "").strip()
    tool_hints, root_hints = (
        tool_def.get("ai_hints", {}),
        schema.get("ai_hints", {}),
    )
    intent = tool_hints.get("intent") or root_hints.get("intent") or ""
    checks = tool_hints.get("self_check") or root_hints.get("self_check") or []
    check_str = f" [Check]: {'; '.join(checks)}." if checks else ""
    prompt_ref = (
        f" (Ref: {', '.join([p['name'] for p in schema['prompts']])})"
        if "prompts" in schema
        else ""
    )

    core = f"| {intent}{check_str}{prompt_ref}"
    limit = 500
    budget = limit - len(core) - 1
    if len(base_desc) > budget:
        base_desc = f"{base_desc[: budget - 3]}..."
    return f"{base_desc} {core}".strip()


def get_all_tools(skill_filter: Optional[List[str]] = None) -> List[Dict]:
    tools = []
    schemas = load_all_schemas(skill_filter)
    for sn, sd in schemas.items():
        s, sdir, v = (
            sd["schema"],
            sd["skill_dir"],
            sd["schema"].get("version", "unknown"),
        )
        if s.get("mcp_strategy") == "merge":
            mn = s.get("merged_name", sn.replace("agency-bin-", ""))
            acts = [
                tn
                for tn, td in s.get("tools", {}).items()
                if not td.get("delegate_to") and tn not in EXCLUDED_TOOLS
            ]
            desc = (
                f"Merged capabilities for {sn}. Actions: {', '.join(acts)}."
                " Refer to prompts for SOP."
            )
            if len(desc) > 500:
                desc = desc[:497] + "..."
            tools.append(
                {
                    "tool_name": mn,
                    "skill_name": sn,
                    "skill_version": v,
                    "skill_dir": sdir,
                    "description": desc,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": acts},
                            "payload": {"type": "object"},
                        },
                        "required": ["action"],
                    },
                    "is_merged": True,
                    "requires": s.get("requires", {}),
                    "sub_tools": s.get("tools", {}),
                }
            )
        else:
            for tn, td in s.get("tools", {}).items():
                if not td.get("delegate_to") and tn not in EXCLUDED_TOOLS:
                    tools.append(
                        {
                            "tool_name": tn,
                            "skill_name": sn,
                            "skill_version": v,
                            "skill_dir": sdir,
                            "description": build_tool_description(tn, td, s),
                            "parameters": td.get(
                                "parameters", {"type": "object", "properties": {}}
                            ),
                            "command": td.get("command", ""),
                            "requires": s.get("requires", {}),
                        }
                    )

        # ── Workflow 工具注册 ──────────────────────────────────────────────────
        # SCHEMA.json 中声明的 workflows 被暴露为独立 MCP Tool
        # 调用时按 steps 顺序执行，前一步的 stdout 作为下一步的上下文注入
        for wf_name, wf_def in s.get("workflows", {}).items():
            wf_tool_name = f"workflow__{sn.replace('agency-', '').replace('-', '_')}__{wf_name}"
            steps_summary = " → ".join(
                step.get("tool", "?") for step in wf_def.get("steps", [])
            )
            wf_desc = (
                f"[Workflow] {wf_def.get('description', wf_name)}. "
                f"Steps: {steps_summary}"
            )
            if len(wf_desc) > 500:
                wf_desc = wf_desc[:497] + "..."
            tools.append(
                {
                    "tool_name": wf_tool_name,
                    "skill_name": sn,
                    "skill_version": v,
                    "skill_dir": sdir,
                    "description": wf_desc,
                    "parameters": wf_def.get(
                        "parameters",
                        {
                            "type": "object",
                            "properties": {
                                "inputs": {
                                    "type": "object",
                                    "description": "工作流初始输入参数",
                                }
                            },
                        },
                    ),
                    "is_workflow": True,
                    "workflow_def": wf_def,
                    "all_schemas": schemas,  # 执行时需要查找子工具
                }
            )

    return tools


def build_command(template: str, params: Dict[str, Any], skill_path: str = "") -> str:
    r, ap = template, {**params, "skill_path": skill_path}
    for m in re.finditer(r"\{(\w+)\?\s*([^\}]+)\}", r):
        r = r.replace(m.group(0), m.group(2) if ap.get(m.group(1)) else "")
    for m in re.finditer(r"--[\w-]+\s+\{(\w+)\}", r):
        if m.group(1) not in ap:
            r = r.replace(m.group(0), "")
    for m in re.finditer(r"\{(\w+)\}", r):
        p = m.group(1)
        if p in ap:
            v = ap[p]
            r = r.replace(
                m.group(0),
                shlex.quote(str(v))
                if not isinstance(v, bool)
                else (f"--{p.replace('_', '-')}" if v else ""),
            )
        else:
            r = r.replace(m.group(0), "")
    return re.sub(r"\s+", " ", r).strip()


def validate_result(result: Dict) -> Dict:
    o, c = result.get("stdout", ""), result.get("exit_code", -1)
    checks = [
        {"check": "exit_code", "passed": c == 0},
        {"check": "output_exists", "passed": len(o.strip()) > 10},
    ]
    errs = [
        p for p in ["error:", "exception:", "traceback", "failed"] if p in o.lower()
    ]
    checks.append({"check": "no_errors", "passed": not errs, "found": errs})
    return {"ok": all(c["passed"] for c in checks), "report": checks}


def record_action(ti: Dict, args: Dict, res: Dict, d: float, cmd: str = ""):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    le = {
        "timestamp": datetime.now().isoformat(),
        "tool": ti.get("tool_name"),
        "skill": ti.get("skill_name"),
        "version": ti.get("skill_version"),
        "arguments": args,
        "command_run": cmd,
        "duration_ms": round(d * 1000, 2),
        "status": res.get("status"),
        "exit_code": res.get("exit_code"),
        "audit": res.get("validation", {}),
        "system": {"os": "Linux", "python": "3.10+"},
        "output_preview": {
            "stdout": (res.get("stdout") or "")[:500],
            "stderr": (res.get("stderr") or "")[:500],
        },
    }
    try:
        log_path = LOG_DIR / f"evolution_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(le, ensure_ascii=False) + "\n")
    except (OSError, PermissionError) as e:
        logger.warning("Failed to record action log: %s", e)


async def execute_tool(ti: Dict, args: Dict) -> Dict:
    st = time.time()
    sd = ti.get("skill_dir", "")
    fc = build_command(ti.get("command", ""), args, sd)
    cl = shlex.split(fc)
    if not cl:
        return {"status": "error", "message": "Empty command"}

    # Resolve command path
    if cl[0].startswith("bin/"):
        cl[0] = str(WORKSPACE_ROOT / cl[0])
    elif (
        "{skill_path}" not in ti.get("command", "")
        and "/" in cl[0]
        and not cl[0].startswith("/")
    ):
        lp = Path(sd) / cl[0]
        if lp.exists():
            cl[0] = str(lp)

    logger.info("Executing: %s", " ".join(cl))
    try:
        proc = await asyncio.create_subprocess_exec(
            *cl,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(WORKSPACE_ROOT),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {
                "status": "timeout",
                "exit_code": -1,
                "stdout": "",
                "stderr": "Command timed out after 120s",
                "validation": validate_result(
                    {
                        "stdout": "",
                        "exit_code": -1,
                        "stderr": "Command timed out after 120s",
                    }
                ),
            }

        output = {
            "status": "success" if proc.returncode == 0 else "failure",
            "exit_code": proc.returncode,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }
        output["validation"] = validate_result(output)
    except (OSError, subprocess.SubprocessError) as e:
        logger.error("Subprocess execution failed: %s", e)
        output = {"status": "error", "message": str(e)}

    record_action(ti, args, output, time.time() - st, " ".join(cl))
    return output


server = Server("agent-hub")


@server.list_tools()
async def list_tools() -> list[Tool]:
    cache_key = "tools"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    result = [
        Tool(
            name=t["tool_name"],
            description=t["description"],
            inputSchema=t["parameters"],
        )
        for t in get_all_tools(None)
    ]
    _set_cache(cache_key, result)
    return result


@server.call_tool()
async def call_tool(n: str, args: dict) -> list[TextContent]:
    cache_key = "tools"
    cached = _get_cache(cache_key)
    all_tools = cached if cached is not None else get_all_tools(None)
    _set_cache(cache_key, all_tools)

    ti = next((t for t in all_tools if t["tool_name"] == n), None)
    if not ti:
        return [TextContent(type="text", text=f"Error: Tool {n} not found")]

    # ── Workflow 执行 ──────────────────────────────────────────────────────────
    if ti.get("is_workflow"):
        res = await execute_workflow(ti, args, all_tools)
        return [TextContent(type="text", text=json.dumps(res, ensure_ascii=False, indent=2))]

    if ti.get("is_merged"):
        a, p = args.get("action"), args.get("payload", {})
        sd = ti.get("sub_tools", {}).get(a)
        if not sd:
            return [TextContent(type="text", text=f"Invalid action {a}")]
        res = await execute_tool(
            {
                "tool_name": f"{n}:{a}",
                "skill_name": ti["skill_name"],
                "skill_version": ti["skill_version"],
                "skill_dir": ti["skill_dir"],
                "command": sd.get("command", ""),
            },
            p,
        )
    else:
        res = await execute_tool(ti, args)
    return [
        TextContent(type="text", text=json.dumps(res, ensure_ascii=False, indent=2))
    ]


async def execute_workflow(
    wf_ti: Dict, initial_args: Dict, all_tools: List[Dict]
) -> Dict:
    """
    按 SCHEMA.json workflows.steps 顺序执行工具链。

    step 格式：
      { "tool": "tool_name", "input_from": "prev" | null, "parallel": false }

    - input_from="prev"：将上一步的 stdout 作为 "context" 注入本步参数
    - parallel=true：与前一步并行执行（当前实现为 asyncio.gather）
    """
    wf_def = wf_ti["workflow_def"]
    steps = wf_def.get("steps", [])
    inputs = initial_args.get("inputs", {})

    step_results: list[Dict] = []
    prev_stdout = ""

    # 收集并行组
    i = 0
    while i < len(steps):
        step = steps[i]
        tool_name = step.get("tool", "")
        use_prev = step.get("input_from") == "prev"

        # 构建本步参数
        step_args = {**inputs}
        if use_prev and prev_stdout:
            step_args["context"] = prev_stdout

        # 查找工具定义
        step_ti = next((t for t in all_tools if t["tool_name"] == tool_name), None)
        if not step_ti:
            step_results.append({
                "step": i,
                "tool": tool_name,
                "status": "error",
                "message": f"Workflow step tool not found: {tool_name}",
            })
            break

        # 并行组：收集连续 parallel=true 的步骤
        parallel_group = [step]
        while (
            i + len(parallel_group) < len(steps)
            and steps[i + len(parallel_group)].get("parallel")
        ):
            parallel_group.append(steps[i + len(parallel_group)])

        if len(parallel_group) > 1:
            # 并行执行
            tasks = []
            for ps in parallel_group:
                ps_ti = next(
                    (t for t in all_tools if t["tool_name"] == ps.get("tool", "")),
                    None,
                )
                if ps_ti:
                    tasks.append(execute_tool(ps_ti, step_args))
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
            for j, pr in enumerate(parallel_results):
                if isinstance(pr, Exception):
                    step_results.append({
                        "step": i + j,
                        "tool": parallel_group[j].get("tool"),
                        "status": "error",
                        "message": str(pr),
                    })
                else:
                    step_results.append({"step": i + j, "tool": parallel_group[j].get("tool"), **pr})
                    prev_stdout = pr.get("stdout", "")
            i += len(parallel_group)
        else:
            # 串行执行
            result = await execute_tool(step_ti, step_args)
            step_results.append({"step": i, "tool": tool_name, **result})
            prev_stdout = result.get("stdout", "")
            i += 1

    overall_ok = all(r.get("status") == "success" for r in step_results)
    return {
        "workflow": wf_ti["tool_name"],
        "status": "success" if overall_ok else "partial_failure",
        "steps_executed": len(step_results),
        "results": step_results,
    }


@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    cache_key = "prompts"
    cached = _get_cache(cache_key)
    if cached is not None:
        return [Prompt(name=n, description=p["description"]) for n, p in cached.items()]

    result = load_all_prompts()
    _set_cache(cache_key, result)
    return [Prompt(name=n, description=p["description"]) for n, p in result.items()]


@server.get_prompt()
async def get_prompt(n: str, args: Optional[dict] = None):
    from mcp.types import PromptMessage, TextContent

    cache_key = "prompts"
    cached = _get_cache(cache_key)
    prompts = cached if cached is not None else load_all_prompts()
    _set_cache(cache_key, prompts)

    if n not in prompts:
        raise ValueError(f"Prompt {n} not found")

    return PromptMessage(
        role="assistant",
        content=TextContent(type="text", text=prompts[n]["instructions"]),
    )


async def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--skills")
    p.add_argument("--list-skills", action="store_true")
    args, _ = p.parse_known_args()

    if args.list_skills:
        for s in sorted(load_all_schemas().keys()):
            print(f"- {s}")
        return

    if args.skills:
        skill_filter = [s.strip() for s in args.skills.split(",")]
        _set_cache("skill_filter", skill_filter)

    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
