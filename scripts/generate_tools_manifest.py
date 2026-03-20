#!/usr/bin/env python3
"""
生成工具清单 - 三级渐进式加载的 Level 1

借鉴 Codex CLI 的设计：
- Level 1: tools_manifest.json（元数据，几十 token）
- Level 2: SCHEMA.json（完整定义，按需加载）
- Level 3: guidance.md（详细指导，按需加载）

用法：
    python3 scripts/generate_tools_manifest.py
"""

import json
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).parent.parent
SKILLS_DIR = WORKSPACE_ROOT / "skills"
OUTPUT_PATH = WORKSPACE_ROOT / "knowledge" / "tools_manifest.json"


def generate_manifest():
    """生成工具清单"""
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "version": "2.0",
        "tools": [],
    }

    for schema_path in SKILLS_DIR.glob("*/SCHEMA.json"):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

            # 跳过 cognitive 类型（方法论框架，不是可执行工具）
            if schema.get("type") == "cognitive":
                continue

            skill_name = schema.get("name", schema_path.parent.name)
            skill_dir = schema_path.parent.name

            for tool_name, tool_def in schema.get("tools", {}).items():
                tool_entry = {
                    "name": tool_name,
                    "skill": skill_name,
                    "skill_dir": skill_dir,
                    "description": tool_def.get("description", "")[:200],
                    "command": tool_def.get("command", ""),
                    "parameters": tool_def.get("parameters", {}),
                }

                # 添加 ai_hints（如果存在）
                if "ai_hints" in tool_def:
                    tool_entry["ai_hints"] = {
                        "when_to_use": tool_def["ai_hints"].get("when_to_use", ""),
                        "examples": tool_def["ai_hints"].get("examples", []),
                        "avoid": tool_def["ai_hints"].get("avoid", ""),
                    }

                # 添加 requires（如果存在）
                if "requires" in schema:
                    tool_entry["requires"] = schema["requires"]

                manifest["tools"].append(tool_entry)

        except Exception as e:
            print(f"⚠️  Error loading {schema_path}: {e}")

    # 按名称排序
    manifest["tools"].sort(key=lambda x: x["name"])
    manifest["total_tools"] = len(manifest["tools"])

    return manifest


def main():
    print("🔨 生成工具清单...")

    manifest = generate_manifest()

    # 确保输出目录存在
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成: {OUTPUT_PATH}")
    print(f"   工具数: {manifest['total_tools']}")
    print(f"   用途: 三级渐进式加载 Level 1")
    print()
    print("📝 使用方式:")
    print("   Level 1: 加载 tools_manifest.json（快速路由）")
    print("   Level 2: 匹配后加载 SCHEMA.json（获取参数）")
    print("   Level 3: 执行时加载 guidance.md（详细指导）")


if __name__ == "__main__":
    main()
