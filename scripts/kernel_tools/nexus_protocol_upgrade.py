#!/usr/bin/env python3
import os
import json
import glob

def upgrade_skill(skill_path):
    manifest_path = os.path.join(skill_path, "manifest.json")
    if not os.path.exists(manifest_path):
        return
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Skip if already upgraded
    if manifest.get("protocol") == "nexus-2.0":
        print(f"[-] Skill '{os.path.basename(skill_path)}' is already 2.0")
        return

    skill_name = manifest.get("name")
    commands = manifest.get("commands", [])
    bin_path = manifest.get("bin_path", "bin/" + os.path.basename(skill_path).replace("agency-bin-", ""))
    
    schema = {
        "name": skill_name,
        "version": "2.0.0",
        "protocol": "nexus-2.0",
        "tools": {}
    }

    # Simple inference of tools from commands
    # e.g. "agent-reach x \"query\"" -> tool name "x", param "query"
    for cmd in commands:
        parts = cmd.split()
        if len(parts) < 2: continue
        
        # Take the second part as tool name if it exists (e.g. 'search' or 'x')
        # Otherwise use the skill's base name
        tool_name = parts[1] if len(parts) > 1 else os.path.basename(skill_path).replace("agency-bin-", "")
        tool_name = tool_name.replace("-", "_").strip('"').strip("'")
        
        # Handle duplicate tool names
        if tool_name in schema["tools"]:
            tool_name = f"{tool_name}_{len(schema['tools'])}"

        # Infer params (look for "query", "url", etc in quotes)
        # This is a heuristic.
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Find placeholders like "query", "url", "target"
        # We replace them with {key} for SCHEMA.json command
        formatted_cmd = bin_path
        for i, part in enumerate(parts[1:]):
            if '"' in part or "'" in part or "query" in part or "url" in part:
                key = part.strip('"').strip("'")
                if not key: key = "arg" + str(i)
                parameters["properties"][key] = {"type": "string", "description": f"Parameter: {key}"}
                parameters["required"].append(key)
                formatted_cmd += f" {{{key}}}"
            else:
                formatted_cmd += f" {part}"

        schema["tools"][tool_name] = {
            "description": f"Heuristically inferred tool from '{cmd}'",
            "command": formatted_cmd,
            "parameters": parameters
        }

    # Write SCHEMA.json
    schema_path = os.path.join(skill_path, "SCHEMA.json")
    with open(schema_path, 'w') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    
    # Update manifest.json
    manifest["version"] = "2.0.0"
    manifest["protocol"] = "nexus-2.0"
    manifest["schema"] = "SCHEMA.json"
    # Clear old commands to reduce noise
    if "commands" in manifest: del manifest["commands"]
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[+] Upgraded '{os.path.basename(skill_path)}' to Nexus 2.0")

if __name__ == "__main__":
    skill_dirs = glob.glob("skills/agency-bin-*")
    for skill_dir in skill_dirs:
        upgrade_skill(skill_dir)
