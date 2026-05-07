#!/usr/bin/env python3
"""
Agent-Hub MCP Server - Minimalist, Intent-Driven & Priority-Truncated
"""
import json
import asyncio
import sys
import subprocess
import shlex
import shutil
import re
import os
import time
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, Prompt, PromptMessage, PromptArgument
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
LOG_DIR = WORKSPACE_ROOT / "knowledge" / "logs"
MANIFEST_PATH = WORKSPACE_ROOT / "knowledge" / "tools_manifest.json"
SKILLS_DIRS = [WORKSPACE_ROOT / "skills", WORKSPACE_ROOT / "skills-cognitive"]

EXCLUDED_TOOLS = {
    "performance_start_trace", "performance_stop_trace", "performance_analyze_insight",
    "take_memory_snapshot", "bb_daemon", "bb_network", "update_check_json", "update_deps",
    "defuddle_extract_title", "defuddle_extract_author", "defuddle_extract_metadata",
}

server = Server("agent-hub")

def find_all_skill_dirs() -> List[Path]:
    dirs = []
    for b in SKILLS_DIRS:
        if b.exists(): dirs.extend([i for i in b.iterdir() if i.is_dir() and not i.name.startswith(".")])
    return dirs

def load_all_schemas(skill_filter: Optional[List[str]] = None) -> Dict[str, Dict]:
    schemas = {}
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
                for t in json.load(f).get("tools", []):
                    sk = t.get("skill")
                    if not sk or (skill_filter and sk not in skill_filter): continue
                    if sk not in schemas:
                        sdp = WORKSPACE_ROOT / "skills" / t.get("skill_dir", sk)
                        m_s, m_n, v, sp = None, None, "0.0.1", sdp / "SCHEMA.json"
                        if sp.exists():
                            try:
                                with open(sp) as f: ps = json.load(f); m_s, m_n, v = ps.get("mcp_strategy"), ps.get("merged_name"), ps.get("version", v)
                            except: pass
                        schemas[sk] = {"schema": {"name": sk, "version": v, "tools": {}, "mcp_strategy": m_s, "merged_name": m_n}, "skill_dir": str(sdp)}
                    schemas[sk]["schema"]["tools"][t["name"]] = {"description": t.get("description", ""), "parameters": t.get("parameters", {}), "ai_hints": t.get("ai_hints", {}), "command": t.get("command", "")}
            if schemas: return schemas
        except: pass
    for sd in find_all_skill_dirs():
        if not sd.is_dir() or (skill_filter and sd.name not in skill_filter): continue
        sp = sd / "SCHEMA.json"
        if sp.exists():
            try:
                with open(sp) as f:
                    s = json.load(f)
                    if s.get("type") != "cognitive": schemas[s.get("name", sd.name)] = {"schema": s, "skill_dir": str(sd)}
            except: pass
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
                        for p in s["prompts"]: pm[p["name"]] = {"instructions": p["instructions"], "description": p.get("description", "")}
            except: pass
    return pm

def build_tool_description(tool_name: str, tool_def: Dict, schema: Dict) -> str:
    """Priority Truncation: Metadata over Raw Description"""
    base_desc = tool_def.get("description", "").strip()
    tool_hints, root_hints = tool_def.get("ai_hints", {}), schema.get("ai_hints", {})
    intent = tool_hints.get("intent") or root_hints.get("intent") or ""
    checks = tool_hints.get("self_check") or root_hints.get("self_check") or []
    check_str = f" [Check]: {'; '.join(checks)}." if checks else ""
    prompt_ref = f" (Ref: {', '.join([p['name'] for p in schema['prompts']])})" if "prompts" in schema else ""
    
    core = f"| {intent}{check_str}{prompt_ref}"
    limit = 500
    budget = limit - len(core) - 1
    if len(base_desc) > budget: base_desc = f"{base_desc[:budget-3]}..."
    return f"{base_desc} {core}".strip()

def get_all_tools(skill_filter: Optional[List[str]] = None) -> List[Dict]:
    tools = []
    schemas = load_all_schemas(skill_filter)
    for sn, sd in schemas.items():
        s, sdir, v = sd["schema"], sd["skill_dir"], sd["schema"].get("version", "unknown")
        if s.get("mcp_strategy") == "merge":
            mn = s.get("merged_name", sn.replace("agency-bin-", ""))
            acts = [tn for tn, td in s.get("tools", {}).items() if not td.get("delegate_to") and tn not in EXCLUDED_TOOLS]
            desc = f"Merged capabilities for {sn}. Actions: {', '.join(acts)}. Refer to prompts for SOP."
            if len(desc) > 500: desc = desc[:497] + "..."
            tools.append({
                "tool_name": mn, "skill_name": sn, "skill_version": v, "skill_dir": sdir, "description": desc,
                "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": acts}, "payload": {"type": "object"}}, "required": ["action"]},
                "is_merged": True, "requires": s.get("requires", {}), "sub_tools": s.get("tools", {})
            })
        else:
            for tn, td in s.get("tools", {}).items():
                if not td.get("delegate_to") and tn not in EXCLUDED_TOOLS:
                    tools.append({"tool_name": tn, "skill_name": sn, "skill_version": v, "skill_dir": sdir, "description": build_tool_description(tn, td, s), "parameters": td.get("parameters", {"type": "object", "properties": {}}), "command": td.get("command", ""), "requires": s.get("requires", {})})
    return tools

def build_command(template: str, params: Dict[str, Any], skill_path: str = "") -> str:
    r, ap = template, {**params, "skill_path": skill_path}
    for m in re.finditer(r'\{(\w+)\?\s*([^\}]+)\}', r): r = r.replace(m.group(0), m.group(2) if ap.get(m.group(1)) else '')
    for m in re.finditer(r'--[\w-]+\s+\{(\w+)\}', r):
        if m.group(1) not in ap: r = r.replace(m.group(0), '')
    for m in re.finditer(r'\{(\w+)\}', r):
        p = m.group(1)
        if p in ap:
            v = ap[p]
            r = r.replace(m.group(0), shlex.quote(str(v)) if not isinstance(v, bool) else (f'--{p.replace("_", "-")}' if v else ''))
        else: r = r.replace(m.group(0), '')
    return re.sub(r'\s+', ' ', r).strip()

def validate_result(result: Dict) -> Dict:
    o, c = result.get("stdout", ""), result.get("exit_code", -1)
    checks = [{"check": "exit_code", "passed": c == 0}, {"check": "output_exists", "passed": len(o.strip()) > 10}]
    errs = [p for p in ["error:", "exception:", "traceback", "failed"] if p in o.lower()]
    checks.append({"check": "no_errors", "passed": not errs, "found": errs})
    return {"ok": all(c["passed"] for c in checks), "report": checks}

def record_action(ti: Dict, args: Dict, res: Dict, d: float, cmd: str = ""):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    le = {"timestamp": datetime.now().isoformat(), "tool": ti.get("tool_name"), "skill": ti.get("skill_name"), "version": ti.get("skill_version"), "arguments": args, "command_run": cmd, "duration_ms": round(d * 1000, 2), "status": res.get("status"), "exit_code": res.get("exit_code"), "audit": res.get("validation", {}), "system": {"os": platform.system(), "python": platform.python_version()}, "output_preview": {"stdout": (res.get("stdout") or "")[:500], "stderr": (res.get("stderr") or "")[:500]}}
    try:
        with open(LOG_DIR / f"evolution_{datetime.now().strftime('%Y%m%d')}.jsonl", "a", encoding="utf-8") as f: f.write(json.dumps(le, ensure_ascii=False) + "\n")
    except: pass

def execute_tool(ti: Dict, args: Dict) -> Dict:
    st, sd = time.time(), ti.get("skill_dir", "")
    fc = build_command(ti.get("command", ""), args, sd)
    cl = shlex.split(fc)
    if not cl: return {"status": "error", "message": "Empty command"}
    if cl[0].startswith("bin/"): cl[0] = str(WORKSPACE_ROOT / cl[0])
    elif "{skill_path}" not in ti.get("command", "") and "/" in cl[0] and not cl[0].startswith("/"):
        lp = Path(sd) / cl[0]
        if lp.exists(): cl[0] = str(lp)
    try:
        r = subprocess.run(cl, shell=False, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True, timeout=120)
        output = {"status": "success" if r.returncode == 0 else "failure", "exit_code": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
        output["validation"] = validate_result(output)
    except Exception as e: output = {"status": "error", "message": str(e)}
    record_action(ti, args, output, time.time() - st, " ".join(cl))
    return output

_tc, _pc, _sf = None, None, None

@server.list_tools()
async def list_tools() -> list[Tool]:
    global _tc
    if _tc is None: _tc = get_all_tools(_sf)
    return [Tool(name=t["tool_name"], description=t["description"], inputSchema=t["parameters"]) for t in _tc]

@server.call_tool()
async def call_tool(n: str, args: dict) -> list[TextContent]:
    global _tc
    if _tc is None: _tc = get_all_tools(_sf)
    ti = next((t for t in _tc if t["tool_name"] == n), None)
    if not ti: return [TextContent(type="text", text=f"Error: Tool {n} not found")]
    if ti.get("is_merged"):
        a, p = args.get("action"), args.get("payload", {})
        sd = ti.get("sub_tools", {}).get(a)
        if not sd: return [TextContent(type="text", text=f"Invalid action {a}")]
        res = execute_tool({"tool_name": f"{n}:{a}", "skill_name": ti["skill_name"], "skill_version": ti["skill_version"], "skill_dir": ti["skill_dir"], "command": sd.get("command", "")}, p)
    else: res = execute_tool(ti, args)
    return [TextContent(type="text", text=json.dumps(res, ensure_ascii=False, indent=2))]

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    global _pc
    if _pc is None: _pc = load_all_prompts()
    return [Prompt(name=n, description=p["description"]) for n, p in _pc.items()]

@server.get_prompt()
async def get_prompt(n: str, args: Optional[dict] = None) -> PromptMessage:
    global _pc
    if _pc is None: _pc = load_all_prompts()
    if n not in _pc: raise ValueError(f"Prompt {n} not found")
    return PromptMessage(role="assistant", content=TextContent(type="text", text=_pc[n]["instructions"]))

async def main():
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--skills"); p.add_argument("--list-skills", action="store_true")
    args, _ = p.parse_known_args()
    if args.list_skills:
        for s in sorted(load_all_schemas().keys()): print(f"- {s}")
        return
    global _sf
    if args.skills: _sf = [s.strip() for s in args.skills.split(",")]
    async with stdio_server() as (r, w): await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__": asyncio.run(main())
