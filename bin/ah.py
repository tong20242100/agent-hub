#!/usr/bin/env python3
import click, sys, json, os
from pathlib import Path

# 路径管理与核心导入
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from bin.core.auditor import audit_skill
    from bin.core.discovery import run_global_discovery, LocalFileScanner
    from bin.core.manager import (
        scan_all_agents, remove_skill, check_skill_update, AGENT_PATHS, asdict
    )
except ImportError:
    # 尝试后备方案 (针对直接在 bin 目录下运行)
    try:
        sys.path.append(str(PROJECT_ROOT / "bin"))
        from core.auditor import audit_skill
        from core.discovery import run_global_discovery, LocalFileScanner
        from core.manager import scan_all_agents, remove_skill, check_skill_update, AGENT_PATHS, asdict
    except ImportError as e:
        print(f"❌ 核心模块导入失败: {e}", file=sys.stderr)
        def audit_skill(*args, **kwargs): return ["模块不可用"], []
        def scan_all_agents(): return {}

@click.group()
def cli():
    """Agent-Hub: 跨平台 Agent 技能中枢"""
    pass

@cli.command()
def scan():
    """快速扫描已注册的 Agent 技能目录"""
    skills = scan_all_agents()
    click.echo(f"🔍 发现 {len(skills)} 个技能项目。")

@cli.command()
@click.option("--json", "-j", "json_output", is_flag=True)
def list(json_output):
    """聚合显示本机所有已注册技能"""
    skills = scan_all_agents()
    if json_output:
        click.echo(json.dumps({n: asdict(a) for n, a in skills.items()}, indent=2, ensure_ascii=False))
    else:
        for name, agg in sorted(skills.items()):
            click.echo(f"• {name} ({', '.join(agg.agents)})")

@cli.command()
@click.argument("skill")
@click.option("--force", is_flag=True)
def remove(skill, force):
    """从系统中彻底卸载技能"""
    ok, res = remove_skill(skill, scan_all_agents(), force=force)
    if ok:
        click.echo(f"✅ 已移除: {', '.join(res['removed'])}")

@cli.command()
@click.argument("skill", required=False)
def status(skill):
    """查看技能分布与健康状态"""
    skills = scan_all_agents()
    if skill:
        if skill not in skills:
            click.echo("❌ 技能不存在")
            return
        agg = skills[skill]
        for loc in agg.locations:
            click.echo(f"  {loc.agent}: {loc.version} -> {loc.path}")
    else:
        for name, agg in sorted(skills.items()):
            click.echo(f"{'✅' if len(agg.agents) > 1 else '⚠️'} {name}: {', '.join(agg.agents)}")

@cli.command()
def update():
    """检测 GitHub/NPM 技能更新"""
    click.echo("🔍 检测中...\n")
    for d in (PROJECT_ROOT / "skills").glob("*/SCHEMA.json"):
        info = check_skill_update(d.parent.name, d)
        if info.has_update:
            click.echo(f"🔴 {info.skill_name}: {info.current_version} -> {info.latest_version}")
        else:
            click.echo(f"✅ {info.skill_name} 已是最新")

@cli.command()
@click.option("--fix", is_flag=True)
def check(fix):
    """合规性审计"""
    click.echo("🔍 启动合规性审计...\n")
    for d in sorted((PROJECT_ROOT / "skills").iterdir()):
        if d.is_dir():
            err, _ = audit_skill(d, fix=fix)
            click.echo(f"{'❌' if err else '✅'} {d.name}")

@cli.command()
@click.argument("path", required=False)
def discover(path):
    """全域探测其他 Agent 技能"""
    res = run_global_discovery()
    for p, items in res.items():
        click.echo(f"🔹 {p}: {[i['name'] for i in items]}")
    if path:
        found = LocalFileScanner("Local").scan(Path(path))
        for r in found:
            click.echo(f"✨ 发现: {r['name']} -> {r['path']}")

if __name__ == "__main__":
    cli()
