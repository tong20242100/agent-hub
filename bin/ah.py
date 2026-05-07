#!/usr/bin/env python3
import click, sys, json, os, subprocess, shutil
from pathlib import Path

# 路径管理与核心导入
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from bin.core.auditor import audit_skill
    from bin.core.discovery import run_global_discovery, LocalFileScanner
    from bin.core.manager import (
        scan_all_agents, remove_skill, check_skill_update, onboard_skill, 
        _sync_global_onboard, AGENT_PATHS, asdict
    )
    from bin.core.evaluator import evaluate_hints
except ImportError:
    # 尝试后备方案 (针对直接在 bin 目录下运行)
    try:
        sys.path.append(str(PROJECT_ROOT / "bin"))
        from core.auditor import audit_skill
        from core.discovery import run_global_discovery, LocalFileScanner
        from core.manager import scan_all_agents, remove_skill, check_skill_update, onboard_skill, AGENT_PATHS, asdict
        from core.evaluator import evaluate_hints
    except ImportError as e:
        print(f"❌ 核心模块导入失败: {e}", file=sys.stderr)
        def audit_skill(*args, **kwargs): return ["模块不可用"], []
        def scan_all_agents(): return {}

@click.group()
def cli():
    """Agent-Hub: 跨平台 Agent 技能中枢"""
    pass

@cli.command()
@click.argument("path")
def onboard(path):
    """正式上线一个新技能：移动/链接、注册清单、清理缓存"""
    ok, msg = onboard_skill(path)
    if ok:
        click.echo(f"✅ {msg}")
    else:
        click.echo(f"❌ {msg}")

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
        type_icons = {"tool": "⚙️", "cognitive": "🧠", "knowledge": "📖"}
        for name, agg in sorted(skills.items()):
            icon = type_icons.get(agg.type, "❓")
            click.echo(f"• {icon} {name} ({', '.join(agg.agents)})")

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
        type_icons = {"tool": "⚙️", "cognitive": "🧠", "knowledge": "📖"}
        click.echo(f"技能: {type_icons.get(agg.type, '❓')} {skill} (Type: {agg.type})")
        for loc in agg.locations:
            click.echo(f"  {loc.agent}: {loc.version} -> {loc.path}")
    else:
        type_icons = {"tool": "⚙️", "cognitive": "🧠", "knowledge": "📖"}
        for name, agg in sorted(skills.items()):
            icon = type_icons.get(agg.type, "❓")
            click.echo(f"{'✅' if len(agg.agents) > 1 else '⚠️'} {icon} {name}: {', '.join(agg.agents)}")

@cli.command()
@click.option("--install", "-i", "do_install", is_flag=True, help="发现更新后自动执行安装与同步")
def update(do_install):
    """检测并自动更新所有技能"""
    click.echo("🔍 检测中...\n")
    for d in (PROJECT_ROOT / "skills").glob("*/SCHEMA.json"):
        skill_name = d.parent.name
        info = check_skill_update(skill_name, d)
        if info.has_update:
            click.echo(f"🔴 {info.skill_name}: {info.current_version} -> {info.latest_version}")
            if do_install:
                click.echo(f"  🚀 正在更新 {skill_name}...")
                # 调用项目内置的安装脚本
                install_cmd = [str(PROJECT_ROOT / "bin" / "skill_update_install"), skill_name]
                res = subprocess.run(install_cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    _sync_global_onboard(d.parent)
                    click.echo(f"  ✅ {skill_name} 更新成功并已重新同步")
                else:
                    click.echo(f"  ❌ 更新失败: {res.stderr}")
        else:
            click.echo(f"✅ {info.skill_name} 已是最新")

@cli.command()
@click.option("--fix", is_flag=True)
def check(fix):
    """合规性审计"""
    click.echo("🔍 启动合规性审计...\n")
    for d in sorted((PROJECT_ROOT / "skills").iterdir()):
        if d.is_dir():
            err, warn = audit_skill(d, fix=fix)
            click.echo(f"{'❌' if err else '✅'} {d.name}")
            if fix and warn and "已尝试自动修复" in "".join(warn):
                _sync_global_onboard(d)
                click.echo(f"  ✨ 已同步更新至全局清单")

@cli.command()
def eval():
    """评估工具 Hint 质量与语义冲突"""
    click.echo("🧪 启动 Hint 质量压力测试...\n")
    manifest_path = PROJECT_ROOT / "knowledge" / "tools_manifest.json"
    report = evaluate_hints(manifest_path)
    
    if "error" in report:
        click.echo(f"❌ 评估失败: {report['error']}")
        return

    # 打印汇总
    s = report["summary"]
    click.echo(f"📊 汇总报告: 总工具 {s['total_tools']} | 完美 Hint {s['perfect_score']} | 高风险 {s['at_risk']}")
    
    # 打印冲突
    if report["conflicts"]:
        click.echo("\n🚨 发现语义冲突 (Triggers 重叠):")
        for c in report["conflicts"]:
            click.echo(f"  • '{c['trigger']}' 被 {len(c['tools'])} 个工具共有: {', '.join(c['tools'])}")

    # 打印低分项
    risks = [d for d in report["diagnostics"] if d["score"] < 100]
    if risks:
        click.echo("\n⚠️ 质量改进建议:")
        for r in sorted(risks, key=lambda x: x["score"]):
            click.echo(f"  • {r['tool']} [{r['score']}分]: {', '.join(r['issues'])}")
    else:
        click.echo("\n✅ 所有工具 Hint 质量表现优异。")

@cli.command()
@click.argument("path", required=False)
@click.option("--onboard", "-o", "onboard_name", help="一键上线探测到的指定技能")
def discover(path, onboard_name):
    """全域探测其他 Agent 技能并支持一键上线"""
    res = run_global_discovery()
    all_discovered = []
    for p, items in res.items():
        click.echo(f"🔹 {p}: {[i['name'] for i in items]}")
        all_discovered.extend(items)
    
    if path:
        found = LocalFileScanner("Local").scan(Path(path))
        for r in found:
            click.echo(f"✨ 发现: {r['name']} -> {r['path']}")
            all_discovered.append(r)
            
    if onboard_name:
        target = next((i for i in all_discovered if i["name"] == onboard_name), None)
        if target and "path" in target:
            ok, msg = onboard_skill(target["path"])
            click.echo(f"{'✅' if ok else '❌'} {msg}")
        elif target:
            # 尝试根据平台路径推断
            from bin.core.manager import AGENT_PATHS
            platform = target["platform"].lower()
            if platform in AGENT_PATHS:
                for p in AGENT_PATHS[platform]:
                    potential = Path(p).expanduser() / onboard_name
                    if potential.exists():
                        ok, msg = onboard_skill(str(potential))
                        click.echo(f"{'✅' if ok else '❌'} {msg}")
                        return
            click.echo(f"❌ 无法确定技能 '{onboard_name}' 的物理路径，无法自动 onboard")
        else:
            click.echo(f"❌ 未在探测结果中找到技能: {onboard_name}")

@cli.command()
@click.option("--force", is_flag=True, help="覆盖现有链接")
def link(force):
    """将 skills-cognitive 中的认知技能链接到全局目录，使其跨平台可用"""
    skills = scan_all_agents()
    target_dir = Path.home() / ".agents" / "skills" / "agent-hub-cognitive"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for name, agg in skills.items():
        if agg.type == "cognitive":
            # 找到在 agent-hub 下的物理路径
            loc = next((l for l in agg.locations if l.agent == "agent-hub"), None)
            if loc:
                src = Path(loc.path)
                dst = target_dir / name
                if dst.exists():
                    if force:
                        if dst.is_symlink(): dst.unlink()
                        else: shutil.rmtree(dst)
                    else:
                        click.echo(f"⚠️ {name} 已存在，跳过。使用 --force 覆盖。")
                        continue
                
                os.symlink(src, dst)
                click.echo(f"🔗 链接认知技能: {name}")
                count += 1
    
    click.echo(f"\n✅ 已成功链接 {count} 个认知技能到 {target_dir}")
    click.echo("💡 现在这些技能可以在 Claude Code / Gemini CLI 中自动识别。")

if __name__ == "__main__":
    cli()
