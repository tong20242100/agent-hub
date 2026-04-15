#!/usr/bin/env python3
"""
Agent-Hub CLI - 跨 Agent Skill 管理器

核心功能：
- scan:       扫描所有Agent的skill目录
- full-scan:  全量深度扫描（含嵌套目录、符号链接追踪）
- list:       聚合显示本机所有skill
- update:     检测skill更新（GitHub releases、npm、pip、brew）
- remove:     卸载skill

用法：
    ah scan                      # 扫描所有Agent
    ah full-scan                 # 全量深度扫描
    ah list                      # 聚合显示
    ah list -j                   # JSON输出
    ah update                    # 检测更新
    ah update --install          # 检测并安装更新
    ah remove <skill>            # 卸载skill
    ah status [skill]            # 查看状态
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import platform
import click
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


# ============ Agent 配置 ============

# 已知的 Agent skill 目录
AGENT_PATHS = {
    "claude": [
        "~/.claude/skills/",
        "~/.claude-code/skills/",
        "./claude-code/skills/",
    ],
    "gemini": [
        "~/.gemini/skills/",
    ],
    "cursor": [
        ".cursor/skills/",
        "~/.cursor/skills/",
    ],
    "codex": [
        "~/.codex/skills/",
        "./codex/skills/",
    ],
    "opencode": [
        "~/opencode/skills/",
        "./opencode/skills/",
    ],
    "antigravity": [
        "~/.antigravity/skills/",
    ],
    "agent-hub": [
        "./skills/",  # 项目级
    ],
}

# 项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"
CACHE_PATH = PROJECT_ROOT / "knowledge" / ".update_cache.json"


# ============ 数据结构 ============

@dataclass
class SkillInfo:
    """Skill 信息"""
    name: str
    path: str
    agent: str
    version: Optional[str] = None
    source: Optional[str] = None
    is_symlink: bool = False
    link_target: Optional[str] = None
    depth: int = 0  # 嵌套深度


@dataclass
class SkillAggregate:
    """聚合的 Skill 信息"""
    name: str
    locations: List[SkillInfo]

    @property
    def agents(self) -> List[str]:
        return [loc.agent for loc in self.locations]

    @property
    def versions(self) -> List[str]:
        return [loc.version for loc in self.locations if loc.version]


@dataclass
class UpdateInfo:
    """更新信息"""
    skill_name: str
    tool_type: str
    current_version: str
    latest_version: Optional[str]
    has_update: bool
    source_url: Optional[str]
    message: str
    schema_path: Optional[str] = None
    dependencies: Optional[List[Dict]] = None


# ============ 核心功能 ============

def parse_skill_md(skill_dir: Path) -> Dict[str, Any]:
    """解析 SKILL.md 文件"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {}
    
    try:
        content = skill_md.read_text()
        
        # 解析 YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                import re
                frontmatter = parts[1]
                
                result = {}
                # 简单解析
                for line in frontmatter.strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        result[key.strip()] = value.strip().strip('"\'')
                
                return result
    except Exception:
        pass
    
    return {}


def parse_schema_json(skill_dir: Path) -> Dict[str, Any]:
    """解析 SCHEMA.json 文件"""
    schema_json = skill_dir / "SCHEMA.json"
    if not schema_json.exists():
        return {}
    
    try:
        return json.loads(schema_json.read_text())
    except Exception:
        return {}


def get_skill_info(skill_dir: Path, agent: str) -> SkillInfo:
    """获取单个 skill 的信息"""
    # 检查是否是符号链接
    is_symlink = skill_dir.is_symlink()
    link_target = str(skill_dir.resolve()) if is_symlink else None
    
    # 尝试从 SKILL.md 获取信息
    skill_md_info = parse_skill_md(skill_dir)
    
    # 尝试从 SCHEMA.json 获取信息
    schema_info = parse_schema_json(skill_dir)
    
    # 合并信息
    version = skill_md_info.get("version") or schema_info.get("version")
    source = skill_md_info.get("source") or schema_info.get("source", {}).get("repo")
    
    return SkillInfo(
        name=skill_dir.name,
        path=str(skill_dir),
        agent=agent,
        version=version,
        source=source,
        is_symlink=is_symlink,
        link_target=link_target,
    )


def scan_all_agents() -> Dict[str, SkillAggregate]:
    """扫描所有 Agent 的 skill 目录"""
    skills: Dict[str, List[SkillInfo]] = {}
    
    for agent, paths in AGENT_PATHS.items():
        for path in paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                for skill_dir in expanded.iterdir():
                    if skill_dir.is_dir():
                        info = get_skill_info(skill_dir, agent)
                        
                        if info.name not in skills:
                            skills[info.name] = []
                        skills[info.name].append(info)
    
    # 转换为 SkillAggregate
    return {
        name: SkillAggregate(name=name, locations=locs)
        for name, locs in skills.items()
    }


def find_best_source(skills: Dict[str, SkillAggregate], skill_name: str) -> Optional[Path]:
    """找到最佳源路径（优先选择非符号链接的）"""
    if skill_name not in skills:
        return None

    aggregate = skills[skill_name]

    # 优先选择非符号链接的
    for loc in aggregate.locations:
        if not loc.is_symlink:
            return Path(loc.path)

    # 都是符号链接，选第一个
    if aggregate.locations:
        return Path(aggregate.locations[0].path)

    return None


# ============ 更新检测 ============

def check_brew_package(name: str) -> Dict:
    """检查 brew 包"""
    try:
        r = subprocess.run(["brew", "list", "--versions", name], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split()
            current = parts[-1] if len(parts) > 1 else "installed"
            outdated = subprocess.run(["brew", "outdated", name], capture_output=True, text=True, timeout=10)
            has_update = outdated.returncode == 0 and outdated.stdout.strip()
            return {"name": name, "type": "brew", "installed": True, "current_version": current,
                    "has_update": bool(has_update), "update_cmd": f"brew upgrade {name}"}
    except Exception:
        pass
    return {"name": name, "type": "brew", "installed": False, "update_cmd": f"brew install {name}"}


def check_pip_package(name: str) -> Dict:
    """检查 pip 包"""
    try:
        r = subprocess.run(["pip", "show", name], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            current = None
            for line in r.stdout.split("\n"):
                if line.startswith("Version:"):
                    current = line.split(":", 1)[1].strip()
                    break
            outdated = subprocess.run(["pip", "list", "--outdated", "--format=json"], capture_output=True, text=True, timeout=30)
            has_update, latest = False, None
            if outdated.returncode == 0:
                for pkg in json.loads(outdated.stdout):
                    if pkg.get("name", "").lower() == name.lower():
                        has_update, latest = True, pkg.get("latest_version")
                        break
            return {"name": name, "type": "pip", "installed": True, "current_version": current,
                    "latest_version": latest, "has_update": has_update, "update_cmd": f"pip install --upgrade {name}"}
    except Exception:
        pass
    return {"name": name, "type": "pip", "installed": False, "update_cmd": f"pip install {name}"}


def check_npm_package(name: str) -> Dict:
    """检查 npm 全局包"""
    try:
        r = subprocess.run(["npm", "list", "-g", name, "--depth=0"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and name in r.stdout:
            import re
            match = re.search(rf"{name}@([\d.]+)", r.stdout)
            current = match.group(1) if match else "installed"
            lr = subprocess.run(["npm", "view", name, "version"], capture_output=True, text=True, timeout=10)
            latest = lr.stdout.strip() if lr.returncode == 0 else None
            return {"name": name, "type": "npm", "installed": True, "current_version": current,
                    "latest_version": latest, "has_update": latest and latest != current,
                    "update_cmd": f"npm update -g {name}"}
    except Exception:
        pass
    return {"name": name, "type": "npm", "installed": False, "update_cmd": f"npm install -g {name}"}


def check_dependencies(deps: List[Dict]) -> List[Dict]:
    """检查所有依赖"""
    results = []
    for dep in deps:
        name, dtype = dep.get("name", ""), dep.get("type", "custom")
        if dtype == "brew":
            results.append(check_brew_package(name))
        elif dtype == "pip":
            results.append(check_pip_package(name))
        elif dtype == "npm":
            results.append(check_npm_package(name))
        else:
            cmd = dep.get("check_command", f"{name} --version")
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                results.append({"name": name, "type": "custom", "installed": r.returncode == 0,
                               "current_version": r.stdout.strip()[:50] if r.stdout else None})
            except Exception:
                results.append({"name": name, "type": "custom", "installed": False})
    return results


def get_github_release(repo: str) -> Optional[Dict]:
    """获取 GitHub 最新 Release"""
    try:
        r = subprocess.run(["gh", "release", "view", "--repo", repo, "--json", "tagName,assets,url"],
                          capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout) if r.returncode == 0 else None
    except Exception:
        return None


def get_npm_version(package: str) -> Optional[str]:
    """获取 npm 包最新版本"""
    try:
        r = subprocess.run(["npm", "view", package, "version"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def check_skill_update(name: str, schema: Dict) -> UpdateInfo:
    """检查单个技能更新状态"""
    version = schema.get("version", "unknown")
    source = schema.get("source", {})
    deps = schema.get("dependencies", [])

    # 有外部来源
    if source:
        stype = source.get("type", "")

        if stype == "github_release":
            repo = source.get("repo", "")
            if not repo:
                return UpdateInfo(name, "github_release", version, None, False, None, "缺少 repo")

            release = get_github_release(repo)
            if not release:
                return UpdateInfo(name, "github_release", version, None, False, f"https://github.com/{repo}",
                                 "无法获取版本")

            latest = release.get("tagName", "")
            current = source.get("installed_version", version)
            has_update = latest and latest != current

            return UpdateInfo(name, "github_release", current, latest, bool(has_update),
                             f"https://github.com/{repo}/releases",
                             f"可更新到 {latest}" if has_update else "已是最新")

        elif stype == "npm":
            pkg = source.get("package", "")
            if not pkg:
                return UpdateInfo(name, "npm", version, None, False, None, "缺少 package")

            latest = get_npm_version(pkg)
            current = source.get("installed_version", version)
            has_update = latest and latest != current

            return UpdateInfo(name, "npm", current, latest, bool(has_update),
                             f"https://www.npmjs.com/package/{pkg}",
                             f"可更新到 {latest}" if has_update else "已是最新")

    # 本地脚本 - 检查依赖
    dep_results = check_dependencies(deps) if deps else None
    missing = [d for d in (dep_results or []) if not d.get("installed")]
    updateable = [d for d in (dep_results or []) if d.get("has_update")]

    if missing:
        msg = f"缺少依赖: {', '.join(d['name'] for d in missing)}"
    elif updateable:
        msg = f"依赖可更新: {', '.join(d['name'] for d in updateable)}"
    else:
        msg = "依赖完整" if deps else "本地技能"

    return UpdateInfo(name, "local_script", version, None, len(updateable) > 0, None, msg, None, dep_results)


# ============ CLI 命令 ============

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Agent-Hub: 跨 Agent Skill 管理器"""
    pass


@cli.command()
def scan():
    """扫描所有 Agent 的 skill 目录"""
    click.echo("🔍 扫描所有 Agent...\n")

    found_any = False
    for agent, paths in AGENT_PATHS.items():
        for path in paths:
            expanded = Path(path).expanduser()
            if expanded.exists():
                skill_dirs = [d for d in expanded.iterdir() if d.is_dir()]
                if skill_dirs:
                    found_any = True
                    click.echo(f"📦 {agent}: {path}")
                    for skill_dir in skill_dirs:
                        link_marker = " →" if skill_dir.is_symlink() else ""
                        click.echo(f"   - {skill_dir.name}{link_marker}")
                    click.echo()

    if not found_any:
        click.echo("❌ 未找到任何 Agent 的 skill 目录")


@cli.command("full-scan")
@click.option("--follow-links", "-f", is_flag=True, help="跟踪符号链接")
@click.option("--max-depth", "-d", default=3, help="最大扫描深度")
def full_scan(follow_links: bool, max_depth: int):
    """全量深度扫描所有Agent技能目录"""
    click.echo(f"🔍 全量扫描所有 Agent (max_depth={max_depth}, follow_links={follow_links})...\n")

    all_skills: List[Dict[str, Any]] = []

    for agent, paths in AGENT_PATHS.items():
        for path in paths:
            expanded = Path(path).expanduser()
            if not expanded.exists():
                continue

            click.echo(f"📦 扫描 {agent}: {path}")

            # 递归扫描
            for skill_dir in _scan_directory(expanded, depth=0, max_depth=max_depth, follow_links=follow_links):
                has_schema = (skill_dir / "SCHEMA.json").exists()
                has_skill_md = (skill_dir / "SKILL.md").exists()

                all_skills.append({
                    "name": skill_dir.name,
                    "path": str(skill_dir),
                    "agent": agent,
                    "depth": _get_depth(expanded, skill_dir),
                    "has_schema": has_schema,
                    "has_skill_md": has_skill_md,
                    "is_symlink": skill_dir.is_symlink(),
                })

                status_icon = "✅" if has_schema else "⚠️"
                click.echo(f"   {status_icon} {skill_dir.name} (depth={_get_depth(expanded, skill_dir)})")

            click.echo()

    # 汇总
    click.echo(f"\n📊 扫描结果: {len(all_skills)} 个技能")
    with_schema = sum(1 for s in all_skills if s["has_schema"])
    without_schema = len(all_skills) - with_schema
    if without_schema > 0:
        click.echo(f"   ✅ 有 SCHEMA.json: {with_schema}")
        click.echo(f"   ⚠️  缺少 SCHEMA.json: {without_schema}")


def _scan_directory(base_path: Path, depth: int, max_depth: int, follow_links: bool) -> List[Path]:
    """递归扫描目录，返回包含 SCHEMA.json 或 SKILL.md 的目录"""
    if depth > max_depth:
        return []

    results = []
    try:
        for item in sorted(base_path.iterdir()):
            if item.is_dir() or (follow_links and item.is_symlink() and item.resolve().is_dir()):
                # 检查是否是技能目录
                if (item / "SCHEMA.json").exists() or (item / "SKILL.md").exists():
                    results.append(item)
                # 继续递归
                if depth < max_depth:
                    results.extend(_scan_directory(item, depth + 1, max_depth, follow_links))
    except PermissionError:
        pass
    return results


def _get_depth(base_path: Path, skill_dir: Path) -> int:
    """计算目录相对于基路径的深度"""
    try:
        rel = skill_dir.relative_to(base_path)
        return len(rel.parts)
    except ValueError:
        return 0


@cli.command()
@click.option("--json", "-j", "json_output", is_flag=True, help="JSON 输出")
def list(json_output: bool):
    """聚合显示本机所有 skill"""
    skills = scan_all_agents()

    if not skills:
        click.echo("❌ 未找到任何 skill")
        return

    if json_output:
        output = {
            name: {
                "agents": agg.agents,
                "versions": agg.versions,
                "locations": [asdict(loc) for loc in agg.locations],
            }
            for name, agg in skills.items()
        }
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
        return

    click.echo(f"📋 本机共有 {len(skills)} 个 skill\n")

    for name, agg in sorted(skills.items()):
        agents_str = ", ".join(agg.agents)
        version_str = agg.versions[0] if agg.versions else "unknown"

        # 检测版本不一致
        if len(set(agg.versions)) > 1:
            version_str += " ⚠️"

        click.echo(f"• {name} ({version_str})")
        click.echo(f"  Agents: {agents_str}")

        # 显示符号链接关系
        for loc in agg.locations:
            if loc.is_symlink:
                click.echo(f"    {loc.agent}: → {loc.link_target}")


@cli.command()
@click.option("--install", "-i", is_flag=True, help="检测并安装更新")
@click.option("--json", "-j", "json_output", is_flag=True, help="JSON 输出")
def update(install: bool, json_output: bool):
    """检测 skill 更新"""
    click.echo("🔍 检测更新中...\n")

    results: List[UpdateInfo] = []
    for schema_file in SKILLS_DIR.glob("*/SCHEMA.json"):
        try:
            with open(schema_file) as f:
                data = json.load(f)
            name = data.get("name", schema_file.parent.name)
            info = check_skill_update(name, data)
            info.schema_path = str(schema_file)
            results.append(info)
        except Exception:
            pass

    # 缓存结果
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, 'w') as f:
        json.dump({
            "last_check": datetime.now().isoformat(),
            "results": [asdict(r) for r in results]
        }, f, ensure_ascii=False)

    if json_output:
        click.echo(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
        return

    # Markdown 报告
    updates = [r for r in results if r.has_update]
    if updates:
        click.echo("## 🔴 需要更新\n")
        click.echo("| 技能 | 当前 | 最新 |")
        click.echo("|------|------|------|")
        for r in updates:
            click.echo(f"| {r.skill_name} | {r.current_version} | {r.latest_version or '-'} |")
        click.echo()

    local = [r for r in results if r.tool_type == "local_script"]
    if local:
        click.echo("## 📦 本地技能\n")
        for r in local:
            deps_info = ""
            if r.dependencies:
                missing = [d for d in r.dependencies if not d.get("installed")]
                updateable = [d for d in r.dependencies if d.get("has_update")]
                if missing:
                    deps_info = f" (缺: {', '.join(d['name'] for d in missing)})"
                elif updateable:
                    deps_info = f" (可更新: {', '.join(d['name'] for d in updateable)})"
            click.echo(f"• {r.skill_name} ({r.current_version}){deps_info}")
        click.echo()

    ok = [r for r in results if not r.has_update and r.tool_type in ("github_release", "npm")]
    if ok:
        click.echo("## ✅ 已是最新\n")
        for r in ok:
            click.echo(f"• {r.skill_name} ({r.current_version})")

    click.echo(f"\n📊 共检测 {len(results)} 个技能")
    if updates:
        click.echo(f"🔴 {len(updates)} 个可更新")
        if install:
            click.echo("\n🔧 开始安装更新...")
            for r in updates:
                click.echo(f"\n📦 {r.skill_name}")
                _install_skill(r)
    else:
        click.echo("✅ 所有技能已是最新")


def _get_platform_suffix() -> str:
    """获取平台后缀"""
    s, m = platform.system().lower(), platform.machine().lower()
    if s == "darwin":
        return "darwin-arm64" if m in ["arm64", "aarch64"] else "darwin-x64"
    elif s == "linux":
        return "linux-arm64" if m in ["arm64", "aarch64"] else "linux-x64"
    return f"{s}-{m}"


def _download_file(url: str, dest: Path) -> bool:
    """下载文件"""
    try:
        r = subprocess.run(["curl", "-L", "-o", str(dest), url], capture_output=True, text=True, timeout=300)
        return r.returncode == 0
    except Exception:
        return False


def _install_binary(url: str, name: str) -> bool:
    """安装二进制文件"""
    bin_dir = PROJECT_ROOT / "bin"
    tmp = Path(tempfile.mktemp(suffix=".download"))
    try:
        if not _download_file(url, tmp):
            return False

        dest = bin_dir / name

        if url.endswith((".tar.gz", ".tgz")):
            import tarfile
            with tarfile.open(tmp, "r:gz") as tar:
                for m in tar.getmembers():
                    if m.isfile() and not m.name.startswith("."):
                        tar.extract(m, bin_dir)
                        extracted = bin_dir / m.name
                        extracted.chmod(0o755)
                        if extracted.name != name:
                            extracted.rename(dest)
                        break
        elif url.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(tmp) as zf:
                for n in zf.namelist():
                    if not n.startswith(".") and not n.endswith("/"):
                        zf.extract(n, bin_dir)
                        extracted = bin_dir / n
                        extracted.chmod(0o755)
                        if extracted.name != name:
                            extracted.rename(dest)
                        break
        else:
            shutil.move(str(tmp), str(dest))
            dest.chmod(0o755)

        return True
    except Exception:
        return False
    finally:
        tmp.unlink(missing_ok=True)


def _update_schema_version(schema_path: str, version: str):
    """更新 SCHEMA 版本"""
    try:
        with open(schema_path) as f:
            data = json.load(f)
        data["version"] = version
        if "source" in data:
            data["source"]["installed_version"] = version
            data["source"]["installed_at"] = datetime.now().strftime("%Y-%m-%d")
        with open(schema_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _install_skill(result: UpdateInfo):
    """安装/更新指定技能"""
    if not result.schema_path:
        click.echo("  ⏭️  无 SCHEMA 路径")
        return

    try:
        with open(result.schema_path) as f:
            schema = json.load(f)
    except Exception:
        click.echo("  ❌ 无法读取 SCHEMA")
        return

    source = schema.get("source", {})
    stype = source.get("type", "")

    if stype == "github_release":
        repo = source.get("repo", "")
        if not repo:
            click.echo("  ❌ 缺少 repo 配置")
            return

        release = get_github_release(repo)
        if not release:
            click.echo("  ❌ 无法获取 Release")
            return

        latest = release.get("tagName", "")
        suffix = _get_platform_suffix()
        url = None
        for asset in release.get("assets", []):
            name = asset.get("name", "").lower()
            if suffix in name:
                url = asset.get("browserDownloadUrl") or asset.get("url")
                break

        if not url:
            click.echo(f"  ❌ 未找到匹配的资源 (平台: {suffix})")
            return

        name = url.split("/")[-1].split(".")[0]
        for sfx in ["-darwin-arm64", "-darwin-x64", "-linux-arm64", "-linux-x64"]:
            name = name.replace(sfx, "")

        if _install_binary(url, name):
            _update_schema_version(result.schema_path, latest)
            click.echo(f"  ✅ 安装成功: {latest}")
        else:
            click.echo("  ❌ 安装失败")

    elif stype == "npm":
        pkg = source.get("package", "")
        cmd = source.get("update_command", f"npm update -g {pkg}")
        click.echo(f"  🔧 {cmd}")
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            if r.returncode == 0:
                vr = subprocess.run(["npm", "view", pkg, "version"], capture_output=True, text=True)
                if vr.returncode == 0:
                    _update_schema_version(result.schema_path, vr.stdout.strip())
                click.echo("  ✅ 更新成功")
            else:
                click.echo(f"  ❌ 失败: {r.stderr[:100]}")
        except Exception as e:
            click.echo(f"  ❌ 执行失败: {e}")

    elif result.dependencies:
        updateable = [d for d in result.dependencies if d.get("has_update")]
        for dep in updateable:
            cmd = dep.get("update_cmd")
            if cmd:
                click.echo(f"  🔧 {cmd}")
                try:
                    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
                    if r.returncode == 0:
                        click.echo(f"  ✅ {dep['name']} 更新成功")
                    else:
                        click.echo(f"  ❌ 失败: {r.stderr[:100]}")
                except Exception as e:
                    click.echo(f"  ❌ 执行失败: {e}")


@cli.command()
@click.argument("skill")
@click.option("--agent", "-a", "target_agent", help="指定要卸载的 Agent")
@click.option("--force", is_flag=True, help="强制删除（包括非符号链接）")
def remove(skill: str, target_agent: Optional[str], force: bool):
    """卸载 skill（从指定或所有 Agent 中移除）"""
    skills = scan_all_agents()

    if skill not in skills:
        click.echo(f"❌ 未找到 skill: {skill}")
        return

    agg = skills[skill]
    agents_to_remove = [target_agent] if target_agent else agg.agents

    removed = []
    skipped = []
    failed = []

    for agent in agents_to_remove:
        for loc in agg.locations:
            if loc.agent != agent:
                continue

            target_path = Path(loc.path)

            if loc.is_symlink:
                # 符号链接，直接删除
                try:
                    target_path.unlink()
                    removed.append(agent)
                except Exception as e:
                    failed.append((agent, str(e)))
            elif force:
                # 强制删除
                try:
                    shutil.rmtree(target_path)
                    removed.append(agent)
                except Exception as e:
                    failed.append((agent, str(e)))
            else:
                skipped.append((agent, "非符号链接，使用 --force 删除"))
                break

    if removed:
        click.echo(f"✅ 已从以下 Agent 移除 {skill}: {', '.join(removed)}")
    if skipped:
        for agent, reason in skipped:
            click.echo(f"⏭️  {agent}: {reason}")
    if failed:
        for agent, error in failed:
            click.echo(f"❌ {agent}: {error}")
    if not removed and not skipped and not failed:
        click.echo(f"⏭️  {skill} 在指定 Agent 中不存在")


@cli.command()
@click.argument("skill", required=False)
def status(skill: Optional[str]):
    """查看 skill 分布状态"""
    skills = scan_all_agents()

    if not skills:
        click.echo("❌ 未找到任何 skill")
        return

    if skill:
        # 显示单个 skill 的状态
        if skill not in skills:
            click.echo(f"❌ 未找到 skill: {skill}")
            return

        agg = skills[skill]
        click.echo(f"📦 {skill}\n")

        for loc in agg.locations:
            version = loc.version or "unknown"
            link_info = f" → {loc.link_target}" if loc.is_symlink else ""
            click.echo(f"  {loc.agent}: {version}{link_info}")
            click.echo(f"    路径: {loc.path}")

        # 检测问题
        versions = set(agg.versions)
        if len(versions) > 1:
            click.echo(f"\n  ⚠️  版本不一致: {versions}")

        # 检测缺失的 Agent
        missing = set(AGENT_PATHS.keys()) - set(agg.agents)
        if missing:
            click.echo(f"\n  💡 缺失 Agent: {', '.join(missing)}")

    else:
        # 显示所有 skill 的状态摘要
        click.echo("📊 Skill 状态摘要\n")

        all_agents = set(AGENT_PATHS.keys())

        for name, agg in sorted(skills.items()):
            agents_with = set(agg.agents)
            agents_missing = all_agents - agents_with

            # 状态指示
            if len(agents_missing) == 0:
                status_icon = "✅"
            elif len(agents_with) == 1:
                status_icon = "⚠️"
            else:
                status_icon = "🔄"

            agents_str = ", ".join(sorted(agents_with))
            missing_str = f" (缺: {', '.join(sorted(agents_missing))})" if agents_missing else ""

            click.echo(f"{status_icon} {name}: {agents_str}{missing_str}")


# ============ 入口 ============

if __name__ == "__main__":
    cli()
