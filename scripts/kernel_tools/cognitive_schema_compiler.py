#!/usr/bin/env python3
import os
import json
import glob

def compile_cognitive_schema(skill_path):
    manifest_path = os.path.join(skill_path, "manifest.json")
    if not os.path.exists(manifest_path):
        return
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    # 跳过已经升级的物理武器
    if manifest.get("protocol") == "nexus-2.0":
        return
        
    # 跳过已经认知升级的技能
    if manifest.get("protocol") == "nexus-cognitive-2.0":
        return
        
    skill_name = manifest.get("name", os.path.basename(os.path.normpath(skill_path)))
    
    # 构建认知型 Schema 契约
    schema = {
        "name": skill_name,
        "version": "2.0.0",
        "protocol": "nexus-cognitive-2.0",
        "type": "cognitive",
        "interface": {
            "inputs": {
                "type": "object",
                "properties": {
                    "task_objective": {
                        "type": "string",
                        "description": "必须明确的任务目标或研究命题"
                    },
                    "context_data": {
                        "type": "string",
                        "description": "可选的上下文信息、前置研报路径或原始代码"
                    }
                },
                "required": ["task_objective"]
            },
            "outputs": {
                "type": "object",
                "properties": {
                    "deliverables": {
                        "type": "array",
                        "items": { "type": "string" },
                        "description": "最终生成的物理产物路径（如 .md, .py 文件路径）"
                    },
                    "executive_summary": {
                        "type": "string",
                        "description": "针对此次认知任务的高度浓缩总结"
                    }
                }
            }
        },
        "guidance": "SKILL.md"
    }
    
    # 写入 SCHEMA.json
    schema_path = os.path.join(skill_path, "SCHEMA.json")
    with open(schema_path, 'w') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
        
    # 升级 manifest.json
    manifest["version"] = "2.0.0"
    manifest["protocol"] = "nexus-cognitive-2.0"
    manifest["schema"] = "SCHEMA.json"
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    print(f"[+] Cognified: {skill_name}")

if __name__ == "__main__":
    for skill_dir in glob.glob("skills/*/"):
        compile_cognitive_schema(skill_dir)
