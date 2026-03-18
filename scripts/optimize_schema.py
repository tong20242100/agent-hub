#!/usr/bin/env python3
"""
SCHEMA.json 优化脚本

借鉴 Claude Code 和 Codex CLI 的设计：
1. 添加 ai_hints 字段（AI 使用指导）
2. 添加 requires 字段（门控检查）
3. 删除 _consolidated 疤痕
4. 标准化字段顺序

用法：
    python3 scripts/optimize_schema.py --dry-run  # 预览改动
    python3 scripts/optimize_schema.py --apply    # 执行改动
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re


# 标准字段顺序
STANDARD_FIELD_ORDER = [
    "name",
    "version", 
    "protocol",
    "description",
    "tools",
    "ai_hints",
    "requires",
    "source",
    "dependencies",
    "type",
    "bin_path",
]


def generate_ai_hints(skill_name: str, description: str, tools: Dict) -> Dict:
    """根据技能信息生成 ai_hints"""
    
    # 从技能名称提取关键信息
    name_lower = skill_name.lower()
    
    # 预定义的 ai_hints 模板
    hints_templates = {
        "gh": {
            "when_to_use": "当用户询问 GitHub 仓库、代码库、开源项目、PR、Issue 信息时",
            "examples": [{"repo": "owner/repo"}],
            "avoid": "不要使用完整 URL（如 https://github.com/...），只需要 owner/repo 格式"
        },
        "scrape": {
            "when_to_use": "当用户需要抓取、爬取、提取网页内容时",
            "examples": [{"url": "https://example.com"}],
            "avoid": "如果网页有 Cloudflare 等防护，使用 stealth_get 而不是 scrape_url"
        },
        "stealth": {
            "when_to_use": "当用户需要抓取有防护的网页（小红书、知乎、Cloudflare 盾牌）时",
            "examples": [{"url": "https://xiaohongshu.com/..."}],
            "avoid": "普通网页不需要用这个，用 scrape_url 即可"
        },
        "search": {
            "when_to_use": "当用户需要搜索网络信息、查找资料时",
            "examples": [{"query": "Python best practices"}],
            "avoid": "如果需要深度研究，考虑使用 deep-scout"
        },
        "media": {
            "when_to_use": "当用户需要提取视频、音频、字幕时",
            "examples": [{"url": "https://youtube.com/..."}],
            "avoid": "确保视频 URL 是公开可访问的"
        },
        "x": {
            "when_to_use": "当用户需要搜索 X/Twitter 内容时",
            "examples": [{"query": "AI agents"}],
            "avoid": "需要配置 X API 凭证"
        },
        "mcp": {
            "when_to_use": "当用户需要启动或管理 MCP 服务器时",
            "examples": [{"server": "context7"}],
            "avoid": "确保 MCP 服务器已正确配置"
        },
        "knowledge": {
            "when_to_use": "当用户需要查询本地知识库、记忆时",
            "examples": [{"query": "项目架构"}],
            "avoid": "这是一个本地工具，不涉及网络请求"
        },
        "notify": {
            "when_to_use": "当用户需要发送通知、提醒时",
            "examples": [{"message": "任务完成"}],
            "avoid": "确保通知服务已配置"
        },
        "viral": {
            "when_to_use": "当用户需要生成病毒式传播内容、社交媒体文案时",
            "examples": [{"topic": "AI 趋势"}],
            "avoid": "生成的内容需要人工审核"
        },
        "deep-scout": {
            "when_to_use": "当用户需要深度研究、全面分析某个主题时",
            "examples": [{"topic": "RAG 技术"}],
            "avoid": "这是一个重型工具，简单查询用 search 即可"
        },
        "cross-verify": {
            "when_to_use": "当用户需要交叉验证信息、核实事实时",
            "examples": [{"claim": "Python 3.12 发布日期"}],
            "avoid": "需要多个信息源才能有效验证"
        },
        "lightpanda": {
            "when_to_use": "当用户需要浏览器自动化、网页交互时",
            "examples": [{"url": "https://example.com", "action": "click"}],
            "avoid": "简单抓取用 scrape，复杂交互用这个"
        }
    }
    
    # 匹配模板
    for key, hints in hints_templates.items():
        if key in name_lower:
            return hints
    
    # 默认生成
    return {
        "when_to_use": f"当用户需要使用 {description[:50]}... 相关功能时",
        "examples": [],
        "avoid": "请参考工具描述了解正确用法"
    }


def extract_requires(dependencies: List[Dict]) -> Dict:
    """从 dependencies 提取 requires 字段"""
    
    bins = []
    env = []
    
    for dep in dependencies:
        dep_type = dep.get("type", "")
        dep_name = dep.get("name", "")
        
        if dep_type in ["brew", "npm", "pip", "binary", "system"]:
            bins.append(dep_name)
        elif dep_type == "env":
            env.append(dep_name)
    
    result = {}
    if bins:
        result["bins"] = bins
    if env:
        result["env"] = env
    
    return result


def optimize_schema(schema: Dict) -> Dict:
    """优化单个 SCHEMA.json"""
    
    optimized = {}
    
    # 1. 复制核心字段
    for field in ["name", "version", "protocol", "description", "tools", "source", "dependencies", "type", "bin_path"]:
        if field in schema:
            optimized[field] = schema[field]
    
    # 2. 生成 ai_hints
    if "tools" in schema:
        # 合并所有工具的描述作为上下文
        all_descriptions = []
        for tool_name, tool_def in schema["tools"].items():
            if "description" in tool_def:
                all_descriptions.append(tool_def["description"])
        
        combined_desc = schema.get("description", "")
        if all_descriptions:
            combined_desc += " " + " ".join(all_descriptions)
        
        optimized["ai_hints"] = generate_ai_hints(
            schema.get("name", ""),
            combined_desc,
            schema["tools"]
        )
    
    # 3. 提取 requires
    if "dependencies" in schema:
        requires = extract_requires(schema["dependencies"])
        if requires:
            optimized["requires"] = requires
    
    # 4. 删除 _consolidated 疤痕
    # (不复制到 optimized 中)
    
    # 5. 标准化字段顺序
    ordered = {}
    for field in STANDARD_FIELD_ORDER:
        if field in optimized:
            ordered[field] = optimized[field]
    
    # 添加其他未识别的字段
    for key, value in optimized.items():
        if key not in ordered:
            ordered[key] = value
    
    return ordered


def main():
    parser = argparse.ArgumentParser(description="优化 SCHEMA.json 文件")
    parser.add_argument("--dry-run", action="store_true", help="预览改动不执行")
    parser.add_argument("--apply", action="store_true", help="执行改动")
    parser.add_argument("--skill", type=str, help="只处理指定技能")
    args = parser.parse_args()
    
    skills_dir = Path("skills")
    
    if args.skill:
        skill_dirs = [skills_dir / args.skill]
    else:
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    
    stats = {
        "total": 0,
        "modified": 0,
        "ai_hints_added": 0,
        "requires_added": 0,
        "consolidated_removed": 0
    }
    
    for skill_dir in skill_dirs:
        schema_path = skill_dir / "SCHEMA.json"
        if not schema_path.exists():
            continue
        
        stats["total"] += 1
        
        with open(schema_path, "r", encoding="utf-8") as f:
            original = json.load(f)
        
        optimized = optimize_schema(original)
        
        # 检查是否有变化
        has_changes = (
            "ai_hints" in optimized and "ai_hints" not in original
        ) or (
            "requires" in optimized and "requires" not in original
        ) or (
            "_consolidated" in original
        )
        
        if has_changes:
            stats["modified"] += 1
            if "ai_hints" in optimized and "ai_hints" not in original:
                stats["ai_hints_added"] += 1
            if "requires" in optimized and "requires" not in original:
                stats["requires_added"] += 1
            if "_consolidated" in original:
                stats["consolidated_removed"] += 1
            
            if args.dry_run:
                print(f"\n{'='*60}")
                print(f"技能: {skill_dir.name}")
                print(f"{'='*60}")
                
                if "_consolidated" in original:
                    print("❌ 删除 _consolidated 疤痕")
                
                if "ai_hints" in optimized and "ai_hints" not in original:
                    print(f"✅ 添加 ai_hints:")
                    for k, v in optimized["ai_hints"].items():
                        print(f"   {k}: {v[:60]}..." if isinstance(v, str) and len(v) > 60 else f"   {k}: {v}")
                
                if "requires" in optimized and "requires" not in original:
                    print(f"✅ 添加 requires: {optimized['requires']}")
            
            elif args.apply:
                with open(schema_path, "w", encoding="utf-8") as f:
                    json.dump(optimized, f, indent=2, ensure_ascii=False)
                print(f"✅ 已优化: {skill_dir.name}")
    
    print(f"\n{'='*60}")
    print("统计")
    print(f"{'='*60}")
    print(f"处理技能: {stats['total']}")
    print(f"有变化: {stats['modified']}")
    print(f"添加 ai_hints: {stats['ai_hints_added']}")
    print(f"添加 requires: {stats['requires_added']}")
    print(f"删除 _consolidated: {stats['consolidated_removed']}")
    
    if args.dry_run:
        print("\n使用 --apply 执行改动")


if __name__ == "__main__":
    main()
