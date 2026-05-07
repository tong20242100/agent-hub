import json
import re
from pathlib import Path

def clean_text(text):
    if not text: return ""
    # 1. 强力删除所有禁令词汇
    text = re.sub(r"(禁止|不能|不准|不要|必须|严禁|禁用|请|务必|建议|记得)", "", text)
    # 2. 强力删除说教式后缀
    text = re.sub(r"是\s*->.*", "", text)
    text = re.sub(r"调此工具|立即使用|优先用.*", "", text)
    # 3. 修复复读机语法
    text = re.sub(r"任务是否需要任务", "任务是否涉及", text)
    text = re.sub(r"是否需要需要", "是否需要", text)
    text = re.sub(r"任务是否需要涉及", "任务是否涉及", text)
    # 4. 语义脱水
    text = re.sub(r"(顶级|极致|30年|实验室级|官方|级)", "", text)
    return text.strip().rstrip("？").rstrip("。")

def convert_to_ai_native(schema):
    desc = schema.get("description", "")
    hints = schema.get("ai_hints", {})
    
    # 1. 净化 Intent
    intent = hints.get("intent", "")
    if not intent or any(x in intent for x in ["30年", "级", "顶级"]):
        clean_intent = desc.split("-")[-1].split("。")[0].strip()
        clean_intent = re.sub(r"^(提供|用于|是一个|帮助用户|实现了)", "", clean_intent)
        intent = clean_text(clean_intent)
    hints["intent"] = intent if intent else "执行特定领域任务"

    # 2. 净化 Avoid (转为场景描述)
    avoid = hints.get("avoid", [])
    if isinstance(avoid, (str, list)):
        avoid_list = [avoid] if isinstance(avoid, str) else avoid
        new_avoid = []
        for item in avoid_list:
            cleaned = clean_text(item)
            if cleaned: new_avoid.append(cleaned)
        hints["avoid"] = list(set(new_avoid))

    # 3. 净化 Self-check (强力诊断化)
    checks = hints.get("self_check", [])
    if isinstance(checks, list):
        new_checks = []
        for c in checks:
            cleaned = clean_text(str(c))
            if not cleaned: continue
            # 强制转换为标准诊断问句
            if not cleaned.startswith("任务是否") and not cleaned.startswith("是否"):
                cleaned = f"任务是否涉及{cleaned}"
            new_checks.append(f"{cleaned}？")
        hints["self_check"] = new_checks

    schema["ai_hints"] = hints
    return schema

def main():
    skills_dirs = ['skills', 'skills-cognitive']
    count = 0
    for d in skills_dirs:
        p = Path(d)
        if not p.exists(): continue
        for f in p.rglob("SCHEMA.json"):
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                
                # 排除已经手动确认没问题的标杆
                if data.get("name") == "Anthropic Design":
                    continue
                
                updated_data = convert_to_ai_native(data)
                
                with open(f, "w") as fp:
                    json.dump(updated_data, fp, indent=2, ensure_ascii=False)
                
                print(f"✅ Deep Cleaned: {f}")
                count += 1
            except Exception as e:
                print(f"❌ Failed: {f} - {e}")
    
    print(f"\n🚀 Total {count} schemas deep-cleaned and re-indexed.")

if __name__ == "__main__":
    main()
