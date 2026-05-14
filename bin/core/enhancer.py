import logging
import json
from pathlib import Path

logger = logging.getLogger("agent-hub.enhancer")


def enhance_tool_hints(skill_name, tool_name, new_hints):
    project_root = Path(__file__).resolve().parent.parent.parent

    # 1. 同步 SCHEMA.json
    schema_path = project_root / "skills" / skill_name / "SCHEMA.json"
    if schema_path.exists():
        try:
            with open(schema_path, "r") as f:
                data = json.load(f)

            if tool_name == "root":
                data["ai_hints"] = new_hints
            elif "tools" in data and tool_name in data["tools"]:
                data["tools"][tool_name]["ai_hints"] = new_hints

            with open(schema_path, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  ✅ SCHEMA 同步: {skill_name}/{tool_name}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ❌ SCHEMA 同步失败 ({skill_name}): {e}")
            logger.error("SCHEMA sync failed for %s/%s: %s", skill_name, tool_name, e)

    # 2. 同步 tools_manifest.json
    manifest_path = project_root / "knowledge" / "tools_manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                m_data = json.load(f)

            updated = False
            for t in m_data.get("tools", []):
                if t.get("name") == tool_name:
                    t["ai_hints"] = new_hints
                    updated = True

            if updated:
                with open(manifest_path, "w") as f:
                    json.dump(m_data, f, ensure_ascii=False, indent=2)
                print(f"  ✅ 清单同步: {tool_name}")
            else:
                logger.debug("Tool %s not found in manifest, skipping sync", tool_name)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ❌ 清单同步失败 ({tool_name}): {e}")
            logger.error("Manifest sync failed for %s: %s", tool_name, e)


if __name__ == "__main__":
    # 该模块供 Python 脚本导入或直接执行
    pass
