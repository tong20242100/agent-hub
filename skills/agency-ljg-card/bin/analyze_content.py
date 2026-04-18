#!/usr/bin/env python3
"""
分析输入内容的密度、结构、情绪，输出 JSON。
供 ljg-card 流程步骤 3 使用。

用法:
    echo "内容" | python3 bin/analyze_content.py
    python3 bin/analyze_content.py --file /path/to/content.txt
"""

import json
import sys
import argparse
from pathlib import Path


def analyze_density(text: str) -> str:
    """稀(≤50字) / 中(50-200字) / 密(200+字)"""
    # 去空白字符后计数
    content_len = len(text.strip())
    if content_len <= 50:
        return "sparse"
    elif content_len <= 200:
        return "medium"
    else:
        return "dense"


def analyze_structure(text: str) -> str:
    """识别内容结构类型"""
    lines = text.strip().split("\n")
    has_numbers = any(line.strip().startswith(tuple("0123456789")) for line in lines)
    has_bullets = any(line.strip().startswith(("-", "*", "•")) for line in lines)
    has_comparison = "vs" in text.lower() or "对比" in text or "比较" in text
    has_steps = "第一步" in text or "step 1" in text.lower() or "首先" in text

    if has_comparison:
        return "contrast"
    elif has_steps:
        return "flow"
    elif has_numbers:
        return "hierarchy"
    elif has_bullets:
        return "parallel"
    else:
        return "single"


def analyze_emotion(text: str) -> str:
    """根据关键词判断内容情绪"""
    emotion_keywords = {
        "沉思": ["哲学", "认知", "本质", "思考", "反思", "理解"],
        "锐利": ["批判", "解构", "争议", "问题", "错误", "陷阱"],
        "温暖": ["人文", "情感", "故事", "感受", "体验", "温暖"],
        "技术": ["架构", "系统", "代码", "实现", "部署", "性能"],
        "科研": ["论文", "实验", "研究", "数据", "方法", "结果"],
        "创意": ["艺术", "设计", "美学", "创意", "灵感", "视觉"],
        "商业": ["商业", "金融", "战略", "市场", "增长", "收入"],
    }

    scores = {}
    for emotion, keywords in emotion_keywords.items():
        score = sum(text.count(kw) for kw in keywords)
        if score > 0:
            scores[emotion] = score

    if scores:
        return max(scores, key=scores.get)
    return "默认"


def main():
    parser = argparse.ArgumentParser(description="分析输入内容，输出密度/结构/情绪")
    parser.add_argument("--file", help="内容文件路径")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text()
    else:
        text = sys.stdin.read()

    if not text.strip():
        print(json.dumps({"error": "内容为空"}, ensure_ascii=False))
        sys.exit(1)

    result = {
        "density": analyze_density(text),
        "structure": analyze_structure(text),
        "emotion": analyze_emotion(text),
        "word_count": len(text.strip()),
    }

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
