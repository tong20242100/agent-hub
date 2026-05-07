import json
import re
from pathlib import Path

class HintEvaluator:
    def __init__(self):
        # 严厉打击：拟人化、禁令、说教逻辑、营销词、复读机语法
        self.BULLSHIT_PATTERNS = [
            r"你[需应该想]", r"请[调启用参]", r"务必", r"禁止", r"不准", r"必须", 
            r"严禁", r"禁用", r"不要", r"是\s*->", r"调此工具", r"立即使用",
            r"顶级", r"极致", r"30年", r"级", r"需要需要", r"任务是否需要任务"
        ]
        self.AI_NATIVE_SIGNALS = [r"任务是否", r"是否需要", r"架构", r"规范", r"协议"]

    def _calculate_score(self, hints):
        if not hints: return 0, ["CRITICAL: 缺失 ai_hints"]
        score = 100
        issues = []

        text_blob = str(hints)
        
        # 1. 违禁词审计 (含新增禁令与垃圾逻辑)
        for pattern in self.BULLSHIT_PATTERNS:
            match = re.search(pattern, text_blob)
            if match:
                score -= 20
                issues.append(f"包含垃圾词汇/逻辑: '{match.group()}'")

        # 2. Intent 质量
        intent = hints.get("intent", "")
        if len(intent) > 40 or re.search(r"级|年|顶级", intent):
            score -= 15
            issues.append(f"intent 质量低 (太长或含营销词): '{intent}'")

        # 3. Self-Check 诊断性审计
        checks = hints.get("self_check", [])
        if isinstance(checks, list):
            for c in checks:
                if not str(c).startswith("任务是否") and not str(c).startswith("是否"):
                    score -= 10
                    issues.append(f"self_check 格式错误: '{str(c)[:15]}...'")
                if "？" not in str(c):
                    score -= 5
                    issues.append("self_check 缺失问号")

        return max(0, score), list(set(issues))

    def evaluate(self, manifest_path: Path):
        try:
            with open(manifest_path, "r") as f:
                data = json.load(f)
            score, issues = self._calculate_score(data.get("ai_hints", {}))
            return {
                "skill": data.get("name", manifest_path.parent.name),
                "score": score,
                "purity": "HIGH" if score >= 90 else "LOW",
                "diagnostics": issues
            }
        except Exception as e:
            return {"error": str(e)}

def evaluate_hints(manifest_path: Path):
    return HintEvaluator().evaluate(manifest_path)
