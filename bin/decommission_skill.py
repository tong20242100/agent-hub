#!/usr/bin/env python3
import json
import os
import shutil
import sys
from pathlib import Path

def decommission(skill_name):
    project_root = Path(__file__).parent.parent
    print(f"🚀 开始全链路下线技能: {skill_name}")

    # 1. 清理清单 (Registry)
    manifest_path = project_root / "knowledge" / "tools_manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
            original_count = len(data.get("tools", []))
            data["tools"] = [t for t in data.get("tools", []) if t.get("skill") != skill_name]
            with open(manifest_path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ 清单同步：移除了 {original_count - len(data['tools'])} 个工具定义")
        except Exception as e:
            print(f"  ❌ 清单清理失败: {e}")

    # 2. 清理地图 (Mapping)
    map_path = project_root / "tools" / "TOOL_MAP.md"
    if map_path.exists():
        content = map_path.read_text()
        new_lines = [l for l in content.splitlines() if skill_name not in l]
        map_path.write_text("\n".join(new_lines) + "\n")
        print("  ✅ 地图同步：已从 TOOL_MAP.md 中抹除")

    # 3. 文档清理 (Documentation)
    readme_path = project_root / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        new_lines = [l for l in content.splitlines() if skill_name not in l]
        readme_path.write_text("\n".join(new_lines) + "\n")
        print("  ✅ 文档同步：已从 README.md 中清理")

    # 4. 物理移除 (Physical)
    skill_dir = project_root / "skills" / skill_name
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
        print(f"  ✅ 物理清理：已删除目录 {skill_dir}")
    else:
        print(f"  ⚠️ 物理清理：未找到目录 {skill_dir}，可能已手动删除")

    # 5. 缓存刷新 (Runtime)
    cache_dir = project_root / "knowledge" / ".router_cache"
    if cache_dir.exists():
        for f in cache_dir.glob("*"):
            if f.is_file():
                f.unlink()
        print("  ✅ 运行时同步：已清空路由缓存")

    print(f"\n✨ 技能 {skill_name} 已完成全链路下线。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 bin/decommission_skill.py <skill_name>")
        sys.exit(1)
    decommission(sys.argv[1])
