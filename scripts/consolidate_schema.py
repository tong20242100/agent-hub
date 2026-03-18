#!/usr/bin/env python3
"""
SCHEMA.json 合并工具 - 将 manifest.json 的额外字段合并到 SCHEMA.json

执行后删除所有 manifest.json，实现单一数据源。

用法:
    python3 scripts/consolidate_schema.py        # 预览模式（不修改文件）
    python3 scripts/consolidate_schema.py --apply # 执行合并
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# 需要从 manifest.json 合并到 SCHEMA.json 的字段
FIELDS_TO_MERGE = [
    "description",
    "tags",
    "capability",
    "commands",
    "type",
    "bin_path",
    "dependencies",
    "source",
]

def merge_manifest_to_schema(skill_dir: Path, apply: bool = False) -> dict:
    """
    将 manifest.json 的字段合并到 SCHEMA.json
    
    Returns:
        dict: 合并结果统计
    """
    manifest_path = skill_dir / "manifest.json"
    schema_path = skill_dir / "SCHEMA.json"
    
    result = {
        "skill": skill_dir.name,
        "status": "skipped",
        "merged_fields": [],
        "errors": []
    }
    
    # 检查文件是否存在
    if not manifest_path.exists():
        result["status"] = "no_manifest"
        return result
    
    if not schema_path.exists():
        result["status"] = "no_schema"
        result["errors"].append("SCHEMA.json missing")
        return result
    
    try:
        # 读取两个文件
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # 合并字段
        merged = []
        for field in FIELDS_TO_MERGE:
            if field in manifest and field not in schema:
                schema[field] = manifest[field]
                merged.append(field)
        
        if merged:
            result["merged_fields"] = merged
            result["status"] = "merged"
            
            if apply:
                # 添加合并元数据
                schema["_consolidated"] = {
                    "merged_at": datetime.now().isoformat(),
                    "source": "manifest.json",
                    "fields_merged": merged
                }
                
                # 写回 SCHEMA.json
                with open(schema_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, ensure_ascii=False, indent=2)
                
                # 删除 manifest.json
                manifest_path.unlink()
                result["status"] = "applied"
        else:
            result["status"] = "no_new_fields"
            
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
    
    return result


def generate_root_manifest() -> dict:
    """
    从所有 SCHEMA.json 生成根目录的 skills/manifest.json
    """
    skills = []
    
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        
        schema_path = skill_dir / "SCHEMA.json"
        if not schema_path.exists():
            continue
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # 提取关键信息
            skill_entry = {
                "name": schema.get("name", skill_dir.name),
                "version": schema.get("version", "1.0.0"),
                "protocol": schema.get("protocol", "nexus-2.0"),
            }
            
            # 可选字段
            if "description" in schema:
                skill_entry["description"] = schema["description"][:200]  # 截断
            if "tags" in schema:
                skill_entry["tags"] = schema["tags"]
            if "capability" in schema:
                skill_entry["capability"] = schema["capability"]
            if "type" in schema:
                skill_entry["type"] = schema["type"]
            if "tools" in schema:
                skill_entry["tools"] = list(schema["tools"].keys())
            
            skills.append(skill_entry)
            
        except Exception as e:
            print(f"  ⚠️  Error reading {skill_dir.name}: {e}")
    
    return {
        "version": "2.1.0",
        "generated_at": datetime.now().isoformat(),
        "total": len(skills),
        "skills": skills
    }


def generate_mcp_manifest() -> dict:
    """
    从所有 SCHEMA.json 生成 MCP 协议清单 (tools/mcp_manifest.json)
    """
    tools = []
    
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        
        schema_path = skill_dir / "SCHEMA.json"
        if not schema_path.exists():
            continue
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            skill_name = schema.get("name", skill_dir.name)
            skill_description = schema.get("description", "")
            
            for tool_name, tool_def in schema.get("tools", {}).items():
                # 构建 input_schema
                params = tool_def.get("parameters", {})
                properties = params.get("properties", {})
                required = params.get("required", [])
                
                # 将 properties 转换为 MCP 格式的 input_schema
                input_schema = {
                    "type": "object",
                    "properties": {},
                    "required": required
                }
                
                for param_name, param_def in properties.items():
                    input_schema["properties"][param_name] = {
                        "type": param_def.get("type", "string"),
                        "description": param_def.get("description", "")
                    }
                
                # 如果没有参数，简化为单一 args 参数（兼容旧格式）
                if not properties:
                    input_schema = {
                        "type": "object",
                        "properties": {
                            "args": {
                                "type": "string",
                                "description": f"工具参数"
                            }
                        }
                    }
                
                tools.append({
                    "name": tool_name,
                    "skill": skill_name,
                    "description": tool_def.get("description", skill_description),
                    "input_schema": input_schema
                })
                
        except Exception as e:
            print(f"  ⚠️  Error reading {skill_dir.name}: {e}")
    
    return {
        "mcp_version": "1.2",
        "generated_at": datetime.now().isoformat(),
        "tools_count": len(tools),
        "tools": tools
    }


def main():
    parser = argparse.ArgumentParser(description="合并 manifest.json 到 SCHEMA.json")
    parser.add_argument("--apply", action="store_true", help="执行实际合并（默认为预览模式）")
    parser.add_argument("--generate-root", action="store_true", help="重新生成根目录 manifest.json")
    args = parser.parse_args()
    
    print("=" * 60)
    print("SCHEMA.json 合并工具")
    print("=" * 60)
    
    if not args.apply:
        print("\n📋 预览模式（使用 --apply 执行实际合并）\n")
    else:
        print("\n⚡ 执行模式\n")
    
    # 统计
    stats = {
        "merged": 0,
        "applied": 0,
        "no_manifest": 0,
        "no_new_fields": 0,
        "errors": 0
    }
    
    # 遍历所有技能目录
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith('.'):
            continue
        
        result = merge_manifest_to_schema(skill_dir, apply=args.apply)
        
        # 更新统计
        if result["status"] in ["merged", "applied"]:
            stats[result["status"]] += 1
            symbol = "✅" if args.apply else "🔄"
            print(f"{symbol} {result['skill']}: 合并字段 {result['merged_fields']}")
        elif result["status"] == "no_manifest":
            stats["no_manifest"] += 1
        elif result["status"] == "no_new_fields":
            stats["no_new_fields"] += 1
        else:
            stats["errors"] += 1
            print(f"❌ {result['skill']}: {result['errors']}")
    
    # 打印统计
    print("\n" + "-" * 60)
    print("📊 统计:")
    print(f"  合并成功: {stats['merged'] + stats['applied']}")
    print(f"  无 manifest.json: {stats['no_manifest']}")
    print(f"  无新字段: {stats['no_new_fields']}")
    print(f"  错误: {stats['errors']}")
    
    # 生成根目录 manifest.json
    if args.apply or args.generate_root:
        print("\n" + "-" * 60)
        print("📝 生成 skills/manifest.json...")
        
        root_manifest = generate_root_manifest()
        root_path = SKILLS_DIR / "manifest.json"
        
        with open(root_path, 'w', encoding='utf-8') as f:
            json.dump(root_manifest, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已生成: {root_path}")
        print(f"   技能总数: {root_manifest['total']}")
        
        # 生成 MCP manifest
        print("\n📝 生成 tools/mcp_manifest.json...")
        
        mcp_manifest = generate_mcp_manifest()
        mcp_path = Path(__file__).parent.parent / "tools" / "mcp_manifest.json"
        mcp_path.parent.mkdir(exist_ok=True)
        
        with open(mcp_path, 'w', encoding='utf-8') as f:
            json.dump(mcp_manifest, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已生成: {mcp_path}")
        print(f"   工具总数: {mcp_manifest['tools_count']}")
        
        # 生成 tools_manifest.json（三级渐进式加载 Level 1）
        print("\n📝 生成 knowledge/tools_manifest.json...")
        import subprocess
        result = subprocess.run(
            ["python3", str(Path(__file__).parent / "generate_tools_manifest.py")],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"⚠️  生成失败: {result.stderr}")


if __name__ == "__main__":
    main()
