import json, os, re, shutil
from pathlib import Path

def audit_skill(skill_dir: Path, fix: bool = False):
    """
    审计单个技能的合规性
    返回: (errors, warnings)
    """
    schema_path = skill_dir / "SCHEMA.json"
    if not schema_path.exists():
        return ["SCHEMA.json 不存在"], []

    errors = []
    warnings = []
    forbidden = {"i", "me", "my", "we", "our", "you", "your", "你", "我", "我们", "你们", "我的", "你的"}
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        name = data.get("name")
        desc = data.get("description", "")
        ai_hints = data.get("ai_hints", {})
        
        # 1. 命名一致性
        if name != skill_dir.name:
            errors.append(f"命名不一致: SCHEMA.name='{name}' vs Dir='{skill_dir.name}'")
            
        # 2. 语气检查
        desc_lower = desc.lower()
        found_forbidden = []
        for word in forbidden:
            pattern = r'(?<!-)\b' + word + r'\b(?!-)'
            if re.search(pattern, desc_lower) or (ord(word[0]) > 127 and word in desc):
                found_forbidden.append(word)
        
        if found_forbidden:
            errors.append(f"语气非人化检查失败 (发现禁词: {found_forbidden})")
            if fix:
                new_desc = desc
                if "我的" in new_desc: new_desc = new_desc.replace("我的", "该")
                if "你的" in new_desc: new_desc = new_desc.replace("你的", "该")
                if "你可以" in new_desc: new_desc = new_desc.replace("你可以", "用于")
                if new_desc != desc:
                    data["description"] = new_desc
                    with open(schema_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    warnings.append("已尝试自动修复语气")

        # 3. 结构检查
        if "self_check" not in ai_hints:
            warnings.append("缺失 self_check 逻辑")
        
        # 4. 物理依赖检查 (核心：确保二进制可用)
        requires = data.get("requires", {})
        project_root = skill_dir.parent.parent
        for bin_name in requires.get("bins", []):
            in_path = shutil.which(bin_name)
            in_local = (project_root / "bin" / bin_name).exists()
            if not in_path and not in_local:
                errors.append(f"物理环境缺失: 找不到二进制 '{bin_name}'")

        # 5. 噪点文件检查 (对齐原则 5: 严禁在技能子目录出现 README)
        noise_files = ["README.md", "INSTALLATION.md", "CHANGELOG.md"]
        for noise in noise_files:
            if (skill_dir / noise).exists():
                warnings.append(f"发现噪音文件: {noise} (应迁移至 docs/ 或删除)")
                
    except Exception as e:
        errors.append(f"审计执行失败: {e}")
        
    return errors, warnings
