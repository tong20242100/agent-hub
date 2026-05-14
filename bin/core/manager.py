import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("agent-hub.manager")


@dataclass
class SkillInfo:
    name: str
    path: str
    agent: str
    version: Optional[str] = None
    source: Optional[str] = None
    is_symlink: bool = False
    link_target: Optional[str] = None
    depth: int = 0
    type: str = "tool"  # tool, cognitive, knowledge


@dataclass
class SkillAggregate:
    name: str
    locations: List[SkillInfo] = field(default_factory=list)

    @property
    def agents(self) -> List[str]:
        return [loc.agent for loc in self.locations]

    @property
    def type(self) -> str:
        return self.locations[0].type if self.locations else "unknown"


# --- 全局路径配置 ---
AGENT_PATHS = {
    "agent-hub": ["skills", "skills-cognitive"],
    "claude": ["~/.claude/skills"],
    "cursor": [
        "~/.cursor/skills",
        "~/Library/Application Support/Cursor/User/globalStorage/ms-vscode.js-debug/bootloader.bundle.cdp/skills",
    ],
    "gemini": ["~/.gemini/skills"],
    "standard": ["~/.agents/skills"],
}


# ================= 核心管理逻辑 =================


def scan_all_agents() -> Dict[str, SkillAggregate]:
    """全域扫描所有 Agent 的技能目录"""
    results: Dict[str, SkillAggregate] = {}
    for agent, paths in AGENT_PATHS.items():
        for p_str in paths:
            p = Path(p_str).expanduser()
            if not p.exists():
                continue
            for d in p.iterdir():
                if not d.is_dir():
                    continue

                info = None
                if (d / "SCHEMA.json").exists():
                    info = _parse_skill(d, agent)
                    if "skills-cognitive" in str(d):
                        info.type = "cognitive"
                elif (d / "SKILL.md").exists():
                    info = _parse_knowledge_skill(d, agent)

                if info:
                    if info.name not in results:
                        results[info.name] = SkillAggregate(info.name)
                    results[info.name].locations.append(info)
    return results


def onboard_skill(path: str) -> tuple:
    """正式上线一个新技能：物理安置、注册、同步、激活"""
    project_root = Path(__file__).resolve().parent.parent.parent
    src_path = Path(path).resolve()
    if not src_path.exists():
        return False, "路径不存在"

    skill_name = src_path.name
    dest_path = project_root / "skills" / skill_name

    if not str(src_path).startswith(str(project_root / "skills")):
        if not dest_path.exists():
            os.symlink(src_path, dest_path)

    _sync_all(skill_name, dest_path, action="onboard")
    return True, f"技能 {skill_name} 已上线"


def remove_skill(
    skill_name: str, skills: Dict[str, SkillAggregate], force: bool = False
):
    """全链路下线技能"""
    if skill_name not in skills:
        return False, "未找到该技能"
    results = {"removed": [], "failed": []}

    for loc in skills[skill_name].locations:
        p = Path(loc.path)
        try:
            if loc.is_symlink:
                p.unlink()
            elif force or loc.agent == "agent-hub":
                shutil.rmtree(p)
            results["removed"].append(loc.agent)
        except Exception as e:
            results["failed"].append((loc.agent, str(e)))

    if results["removed"]:
        _sync_all(skill_name, action="remove")
    return True, results


# ================= 全链路同步私有逻辑 =================


def _sync_all(
    skill_name: str, skill_dir: Optional[Path] = None, action: str = "onboard"
):
    """统一同步入口"""
    project_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = project_root / "knowledge" / "tools_manifest.json"
    mcp_path = project_root / "config" / "mcp_servers.json"

    if action == "onboard":
        if not skill_dir or not skill_dir.exists():
            logger.warning("onboard requested but skill_dir missing: %s", skill_dir)
            return
        schema = _load_json(skill_dir / "SCHEMA.json")
        _update_manifest(manifest_path, skill_name, schema)
        _update_mcp_config(mcp_path, skill_name, schema)
        _update_docs(project_root, skill_name, schema, action="add")
    else:
        _update_manifest(manifest_path, skill_name, None)
        _update_mcp_config(mcp_path, skill_name, None)
        _update_docs(project_root, skill_name, None, action="remove")

    _clear_cache(project_root)


def _sync_global_onboard(skill_dir: Path):
    """全局同步上线（不移动文件，仅刷新配置与清单）"""
    project_root = Path(__file__).resolve().parent.parent.parent
    skill_name = skill_dir.name
    manifest_path = project_root / "knowledge" / "tools_manifest.json"
    mcp_path = project_root / "config" / "mcp_servers.json"

    schema = _load_json(skill_dir / "SCHEMA.json")
    _update_manifest(manifest_path, skill_name, schema)
    _update_mcp_config(mcp_path, skill_name, schema)
    _update_docs(project_root, skill_name, schema, action="add")
    _clear_cache(project_root)


def _update_manifest(path: Path, skill_name: str, schema: Optional[Dict]):
    """同步 tools_manifest.json"""
    if not path.exists():
        return
    data = _load_json(path)
    data["tools"] = [t for t in data.get("tools", []) if t.get("skill") != skill_name]
    if schema:
        for t_name, t_def in schema.get("tools", {}).items():
            data["tools"].append(
                {
                    "name": t_name,
                    "skill": skill_name,
                    "skill_dir": skill_name,
                    "description": t_def.get("description", ""),
                    "command": t_def.get("command", ""),
                    "parameters": t_def.get("parameters", {}),
                    "ai_hints": {
                        **schema.get("ai_hints", {}),
                        **t_def.get("ai_hints", {}),
                    },
                }
            )
    try:
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except (OSError, PermissionError) as e:
        logger.error("Failed to write manifest %s: %s", path, e)


def _update_mcp_config(path: Path, skill_name: str, schema: Optional[Dict]):
    """同步 mcp_servers.json"""
    if not path.exists():
        return
    config = _load_json(path)
    short_name = skill_name.replace("agency-bin-", "").replace("agency-", "")

    if schema:
        is_mcp = any(
            str(t.get("command", "")).startswith("mcp://")
            for t in schema.get("tools", {}).values()
        )
        if is_mcp:
            source = schema.get("source", {})
            cmd = (
                ["npx", source.get("package")] if source.get("type") == "npm" else None
            )
            if cmd:
                config.setdefault("servers", {})[short_name] = {
                    "command": cmd,
                    "args": [],
                    "description": schema.get("description"),
                }
    else:
        if short_name in config.get("servers", {}):
            del config["servers"][short_name]

    try:
        with open(path, "w") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except (OSError, PermissionError) as e:
        logger.error("Failed to write MCP config %s: %s", path, e)


def _update_docs(root: Path, skill_name: str, schema: Optional[Dict], action: str):
    """同步 TOOL_MAP.md"""
    map_path = root / "tools" / "TOOL_MAP.md"
    if not map_path.exists():
        return
    lines = map_path.read_text().splitlines()
    if action == "remove":
        new_lines = [line for line in lines if skill_name not in line]
    else:
        if not any(skill_name in line for line in lines):
            desc = schema.get("description", "新技能") if schema else "New Skill"
            new_lines = lines + [f"| **{skill_name}** | `multiple` | {desc} |"]
        else:
            new_lines = lines
    try:
        map_path.write_text("\n".join(new_lines) + "\n")
    except (OSError, PermissionError) as e:
        logger.error("Failed to write TOOL_MAP %s: %s", map_path, e)


def _clear_cache(root: Path):
    """清理路由缓存"""
    cache_dir = root / "knowledge" / ".router_cache"
    if cache_dir.exists():
        for f in cache_dir.glob("*"):
            if f.is_file():
                try:
                    f.unlink()
                except OSError as e:
                    logger.warning("Failed to remove cache file %s: %s", f, e)


def _load_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning("Malformed JSON at %s: %s", path, e)
        return {}
    except (OSError, PermissionError) as e:
        logger.warning("Cannot read %s: %s", path, e)
        return {}


def _parse_skill(skill_dir: Path, agent: str) -> SkillInfo:
    data = _load_json(skill_dir / "SCHEMA.json")
    return SkillInfo(
        name=data.get("name", skill_dir.name),
        path=str(skill_dir),
        agent=agent,
        version=data.get("version"),
        source=data.get("source", {}).get("type"),
        is_symlink=skill_dir.is_symlink(),
    )


def _parse_knowledge_skill(skill_dir: Path, agent: str) -> SkillInfo:
    skill_file = skill_dir / "SKILL.md"
    name = skill_dir.name
    version = "1.0.0"

    if not skill_file.exists():
        return SkillInfo(
            name=name,
            path=str(skill_dir),
            agent=agent,
            version=version,
            type="knowledge",
            is_symlink=skill_dir.is_symlink(),
        )

    try:
        content = skill_file.read_text()
        if "name:" in content:
            match = re.search(r"name:\s*(.*)", content)
            if match:
                name = match.group(1).strip()
        if "version:" in content:
            match = re.search(r"version:\s*(.*)", content)
            if match:
                version = match.group(1).strip()
    except (OSError, PermissionError) as e:
        logger.warning("Cannot read skill file %s: %s", skill_file, e)

    return SkillInfo(
        name=name,
        path=str(skill_dir),
        agent=agent,
        version=version,
        type="knowledge",
        is_symlink=skill_dir.is_symlink(),
    )


def check_skill_update(name: str, schema_path: Path):
    """检测单个技能的更新状态"""
    data = _load_json(schema_path)
    if not data:
        return None

    version = data.get("version", "0.0.0")
    source = data.get("source", {})

    @dataclass
    class SimpleUpdateInfo:
        skill_name: str
        current_version: str
        latest_version: str = ""
        has_update: bool = False

    if source:
        stype = source.get("type")
        if stype == "npm":
            pkg = source.get("package")
            try:
                r = subprocess.run(
                    ["npm", "view", pkg, "version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                latest = r.stdout.strip() if r.returncode == 0 else None
                return SimpleUpdateInfo(
                    name, version, latest, latest and latest != version
                )
            except subprocess.TimeoutExpired:
                logger.warning("npm view timeout for package %s", pkg)
                return SimpleUpdateInfo(name, version)

    # 检查依赖
    deps = data.get("dependencies", [])
    has_dep_update = False
    if deps:
        for dep in deps:
            if dep.get("type") == "npm":
                dep_pkg = dep.get("name")
                try:
                    r = subprocess.run(
                        ["npm", "list", "-g", dep_pkg, "--depth=0"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    current = "0.0.0"
                    if r.returncode == 0 and dep_pkg in r.stdout:
                        match = re.search(rf"{dep_pkg}@([\d.]+)", r.stdout)
                        current = match.group(1) if match else "0.0.0"
                    lr = subprocess.run(
                        ["npm", "view", dep_pkg, "version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    latest = lr.stdout.strip() if lr.returncode == 0 else None
                    if latest and latest != current:
                        has_dep_update = True
                        break
                except subprocess.TimeoutExpired:
                    logger.warning("npm view timeout for dependency %s", dep_pkg)

    return SimpleUpdateInfo(name, version, has_dep_update=has_dep_update)
