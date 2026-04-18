import os, json, shutil, platform, subprocess, tempfile
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Any

@dataclass
class SkillInfo:
    name: str; path: str; agent: str; version: Optional[str] = None; source: Optional[str] = None
    is_symlink: bool = False; link_target: Optional[str] = None; depth: int = 0

@dataclass
class SkillAggregate:
    name: str; locations: List[SkillInfo]
    @property
    def agents(self) -> List[str]: return [loc.agent for loc in self.locations]
    @property
    def versions(self) -> List[str]: return [loc.version for loc in self.locations if loc.version]

@dataclass
class UpdateInfo:
    skill_name: str; tool_type: str; current_version: str; latest_version: Optional[str] = None
    has_update: bool = False; source_url: Optional[str] = None; message: str = ""; schema_path: Optional[str] = None
    dependencies: Optional[List[Dict]] = None

AGENT_PATHS = {
    "claude": ["~/.claude/skills/", "~/.claude-code/skills/"],
    "gemini": ["~/.gemini/skills/"],
    "cursor": [".cursor/skills/", "~/.cursor/skills/"],
    "agent-hub": ["./skills/"],
}

def scan_all_agents() -> Dict[str, SkillAggregate]:
    skills: Dict[str, List[SkillInfo]] = {}
    for agent, paths in AGENT_PATHS.items():
        for path in paths:
            expanded = Path(path).expanduser()
            if expanded.exists() and expanded.is_dir():
                for skill_dir in expanded.iterdir():
                    if skill_dir.is_dir():
                        info = get_skill_info(skill_dir, agent)
                        if info.name not in skills: skills[info.name] = []
                        skills[info.name].append(info)
    return {name: SkillAggregate(name=name, locations=locs) for name, locs in skills.items()}

def get_skill_info(skill_dir: Path, agent: str) -> SkillInfo:
    is_symlink = skill_dir.is_symlink()
    link_target = str(skill_dir.resolve()) if is_symlink else None
    md_info = _parse_skill_md(skill_dir)
    json_info = _parse_schema_json(skill_dir)
    return SkillInfo(
        name=skill_dir.name, path=str(skill_dir), agent=agent,
        version=md_info.get("version") or json_info.get("version"),
        source=md_info.get("source") or json_info.get("source", {}).get("repo"),
        is_symlink=is_symlink, link_target=link_target
    )

def _parse_skill_md(skill_dir: Path) -> Dict[str, Any]:
    md = skill_dir / "SKILL.md"
    if not md.exists(): return {}
    try:
        content = md.read_text()
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                res = {}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        res[k.strip()] = v.strip().strip("'\"")
                return res
    except: pass
    return {}

def _parse_schema_json(skill_dir: Path) -> Dict[str, Any]:
    p = skill_dir / "SCHEMA.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text())
    except: return {}

def remove_skill(skill_name: str, skills: Dict[str, SkillAggregate], force: bool = False):
    if skill_name not in skills: return False, "未找到该技能"
    agg = skills[skill_name]
    results = {"removed": [], "failed": []}
    for loc in agg.locations:
        p = Path(loc.path)
        try:
            if loc.is_symlink: p.unlink()
            elif force: shutil.rmtree(p)
            else: continue
            results["removed"].append(loc.agent)
        except Exception as e: results["failed"].append((loc.agent, str(e)))
    return True, results

def check_skill_update(name: str, schema_path: Path) -> UpdateInfo:
    try:
        with open(schema_path) as f: data = json.load(f)
        current = data.get("version", "0.0.0")
        source = data.get("source", {})
        stype = source.get("type", "local")
        info = UpdateInfo(skill_name=name, tool_type=stype, current_version=current, schema_path=str(schema_path))
        if stype == "github_release":
            repo = source.get("repo")
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            r = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
            if r.returncode == 0:
                latest = json.loads(r.stdout).get("tag_name", "").lstrip("v")
                info.latest_version = latest
                info.has_update = (latest != current)
        return info
    except: return UpdateInfo(skill_name=name, tool_type="error", current_version="0.0.0")
