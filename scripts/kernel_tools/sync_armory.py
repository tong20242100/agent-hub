#!/usr/bin/env python3
import os
import json
import glob
from datetime import datetime

def sync_armory():
    armory_path = "ARMORY.json"
    skills_dir = "skills/"
    
    all_skill_paths = glob.glob(os.path.join(skills_dir, "*/"))
    active_skills = []
    physical_weapons = []
    cognitive_skills = []
    legacy_skills = []
    
    for path in all_skill_paths:
        manifest_path = os.path.join(path, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                name = manifest.get("name")
                active_skills.append(name)
                
                protocol = manifest.get("protocol")
                if protocol == "nexus-2.0":
                    physical_weapons.append(name)
                elif protocol == "nexus-cognitive-2.0":
                    cognitive_skills.append(name)
                else:
                    legacy_skills.append(name)
    
    new_armory = {
        "system_version": "10.0-Protocol-Native",
        "last_sync": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "architecture": "Schema-Driven (Physical + Cognitive)",
        "stats": {
            "total_active": len(active_skills),
            "physical_weapons": len(physical_weapons),
            "cognitive_skills": len(cognitive_skills),
            "legacy": len(legacy_skills)
        },
        "registry": {
            "nexus_physical_2.0": sorted(physical_weapons),
            "nexus_cognitive_2.0": sorted(cognitive_skills),
            "legacy_untyped": sorted(legacy_skills)
        }
    }

    with open(armory_path, 'w') as f:
        json.dump(new_armory, f, ensure_ascii=False, indent=2)

    print(f"[+] ARMORY Synced. Physical: {len(physical_weapons)}, Cognitive: {len(cognitive_skills)}")

if __name__ == "__main__":
    sync_armory()
