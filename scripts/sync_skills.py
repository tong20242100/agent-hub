#!/usr/bin/env python3
"""
Skill Sync Script - 同步 skills/ 到多个工具

用法:
    python3 scripts/sync_skills.py --target claude    # 同步到 Claude Code
    python3 scripts/sync_skills.py --target gemini    # 同步到 Gemini CLI (项目内)
    python3 scripts/sync_skills.py --target antigravity  # 同步到 Antigravity
    python3 scripts/sync_skills.py --target all       # 同步到所有工具
"""

import argparse
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SKILLS_DIR = PROJECT_ROOT / "skills"

# 目标路径配置
TARGETS = {
    "claude": {
        "path": Path.home() / ".claude" / "agents",
        "method": "symlink",
        "transform": lambda s: f"{s}.md"
    },
    "gemini": {
        "path": PROJECT_ROOT / ".gemini" / "skills",
        "method": "copy",
        "transform": lambda s: s
    },
    "antigravity": {
        "path": PROJECT_ROOT / ".antigravity" / "skills",
        "method": "symlink",
        "transform": lambda s: s
    }
}


def get_agency_skills():
    """获取所有 agency-* 开头的 skill 目录"""
    skills = []
    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir() and skill_dir.name.startswith("agency-"):
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                skills.append(skill_dir.name)
    return sorted(skills)


def sync_to_claude(skills):
    """同步到 Claude Code (~/.claude/agents/)"""
    target_dir = TARGETS["claude"]["path"]
    target_dir.mkdir(parents=True, exist_ok=True)
    
    synced = 0
    for skill in skills:
        source = SKILLS_DIR / skill / "SKILL.md"
        target = target_dir / TARGETS["claude"]["transform"](skill)
        
        # 移除旧的 link 或文件
        if target.exists() or target.is_symlink():
            target.unlink()
        
        # 创建 symlink
        target.symlink_to(source)
        synced += 1
        print(f"  ✓ {skill} -> {target}")
    
    print(f"\n[Claude Code] 同步完成: {synced} skills -> {target_dir}")


def sync_to_gemini(skills):
    """同步到 Gemini CLI (项目内 .gemini/skills/)"""
    target_base = TARGETS["gemini"]["path"]
    
    synced = 0
    for skill in skills:
        source_dir = SKILLS_DIR / skill
        target_dir = target_base / skill
        
        # 移除旧目录
        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir)
        
        # 复制目录
        import shutil
        shutil.copytree(source_dir, target_dir)
        synced += 1
        print(f"  ✓ {skill} -> {target_dir}")
    
    print(f"\n[Gemini CLI] 同步完成: {synced} skills -> {target_base}")


def sync_to_antigravity(skills):
    """同步到 Antigravity (agents/)"""
    target_dir = TARGETS["antigravity"]["path"]
    target_dir.mkdir(parents=True, exist_ok=True)
    
    synced = 0
    for skill in skills:
        source = SKILLS_DIR / skill
        target = target_dir / skill
        
        # 移除旧的 link 或目录
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                target.unlink()
            else:
                import shutil
                shutil.rmtree(target)
        
        # 创建 symlink
        target.symlink_to(source)
        synced += 1
        print(f"  ✓ {skill} -> {target}")
    
    print(f"\n[Antigravity] 同步完成: {synced} skills -> {target_dir}")


def main():
    parser = argparse.ArgumentParser(description="同步 skills 到多个工具")
    parser.add_argument("--target", choices=["claude", "gemini", "antigravity", "all"], 
                        default="all", help="同步目标")
    args = parser.parse_args()
    
    skills = get_agency_skills()
    print(f"发现 {len(skills)} 个 agency-* skills\n")
    
    if args.target == "all":
        print("=== 同步到 Claude Code ===")
        sync_to_claude(skills)
        print()
        print("=== 同步到 Gemini CLI ===")
        sync_to_gemini(skills)
        print()
        print("=== 同步到 Antigravity ===")
        sync_to_antigravity(skills)
    elif args.target == "claude":
        sync_to_claude(skills)
    elif args.target == "gemini":
        sync_to_gemini(skills)
    elif args.target == "antigravity":
        sync_to_antigravity(skills)
    
    print("\n✅ 同步完成！")


if __name__ == "__main__":
    main()
