import json
import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger("agent-hub.auditor")


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
    forbidden = {
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "你",
        "我",
        "我们",
        "你们",
        "我的",
        "你的",
    }

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"SCHEMA.json 格式错误: {e}")
        return errors, warnings
    except (OSError, PermissionError) as e:
        errors.append(f"无法读取 SCHEMA.json: {e}")
        return errors, warnings

    name = data.get("name")
    desc = data.get("description", "")

    # 1. 命名一致性
    if name != skill_dir.name:
        errors.append(f"命名不一致: SCHEMA.name='{name}' vs Dir='{skill_dir.name}'")

    # 2. 语气检查
    desc_lower = desc.lower()
    found_forbidden = []
    for word in forbidden:
        pattern = r"(?<!-)\b" + word + r"\b(?!-)"
        if re.search(pattern, desc_lower) or (ord(word[0]) > 127 and word in desc):
            found_forbidden.append(word)

    if found_forbidden:
        errors.append(f"语气非人化检查失败 (发现禁词: {found_forbidden})")
        if fix:
            new_desc = desc
            if "我的" in new_desc:
                new_desc = new_desc.replace("我的", "该")
            if "你的" in new_desc:
                new_desc = new_desc.replace("你的", "该")
            if "你可以" in new_desc:
                new_desc = new_desc.replace("你可以", "用于")
            if new_desc != desc:
                data["description"] = new_desc
                try:
                    with open(schema_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    warnings.append("已尝试自动修复语气")
                except (OSError, PermissionError) as e:
                    logger.error("Failed to write fixed schema %s: %s", schema_path, e)

    # 3. 结构检查与 Hint 质量守卫
    tool_defs = data.get("tools", {})
    root_hints = data.get("ai_hints", {})

    for t_name, t_def in tool_defs.items():
        merged_hints = {**root_hints, **t_def.get("ai_hints", {})}

        if not merged_hints:
            errors.append(f"工具 '{t_name}' 完全缺失 ai_hints")
            continue

        wtu = merged_hints.get("when_to_use", "")
        if len(wtu) < 20:
            errors.append(f"工具 '{t_name}' Hint 质量低：when_to_use 过短或缺失")

        if not merged_hints.get("examples"):
            errors.append(f"工具 '{t_name}' 缺失 examples")

        if "avoid" not in merged_hints:
            warnings.append(f"工具 '{t_name}' 建议加入 avoid 逻辑")

    # 4. 物理依赖检查
    requires = data.get("requires", {})
    project_root = skill_dir.parent.parent
    for bin_name in requires.get("bins", []):
        in_path = shutil.which(bin_name)
        in_local = (project_root / "bin" / bin_name).exists()
        if not in_path and not in_local:
            errors.append(f"物理环境缺失: 找不到二进制 '{bin_name}'")

    # 5. 噪点文件检查
    noise_files = ["README.md", "INSTALLATION.md", "CHANGELOG.md"]
    for noise in noise_files:
        if (skill_dir / noise).exists():
            warnings.append(f"发现噪音文件: {noise} (应迁移至 docs/ 或删除)")

    return errors, warnings
