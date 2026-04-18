#!/usr/bin/env python3
"""
用 LLM 批量生成 AI 原生的 ai_hints

用法:
    python3 bin/generate_ai_hints.py              # 预览模式
    python3 bin/generate_ai_hints.py --apply      # 实际修改
    python3 bin/generate_ai_hints.py --apply --name stealth_get  # 单个工具
    python3 bin/generate_ai_hints.py --validate   # 验证现有 hints（正/反向触发测试）
"""

import json
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "knowledge" / "tools_manifest.json"
CONFIG_PATH = PROJECT_ROOT / "config" / "model_router.json"


def call_llm(prompt: str) -> str:
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)

    base_url = config.get("proxy_config", {}).get(
        "base_url", "http://127.0.0.1:18788/v1"
    )
    timeout = config.get("proxy_config", {}).get("timeout_ms", 300000) // 1000

    url = f"{base_url}/chat/completions"
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]


def generate_ai_hints_with_llm(tool: dict) -> dict:
    name = tool.get("name", "")
    desc = tool.get("description", "")
    command = tool.get("command", "")
    params = tool.get("parameters", {})

    prompt = f"""你是一个 AI Agent 工具配置生成器。你要为 AI Agent 生成工具使用指南。

注意：这份指南是给 AI 看的，不是给人看的。AI 需要：
1. 精确的触发条件（什么输入 → 用这个工具）
2. 可直接使用的参数示例
3. 容易犯的错误

工具信息：
- 名称: {name}
- 描述: {desc}
- 命令: {command}
- 参数: {json.dumps(params, ensure_ascii=False)[:500] if params else "无"}

输出 JSON：
{{
  "self_check": ["自检 1", "自检 2"],
  "when_to_use": "触发条件。格式：'当输入包含 X / 用户说 Y / 任务需要 Z 时调用'",
  "examples": [{{"参数名": "可直接使用的值"}}],
  "avoid": "容易犯的错，简短直接"
}}

示例（好的 self_check）：
- "你有原生搜索能力（如 Google Search）吗？有则优先用自己的"
- "你需要抓取的是否为需要 JS 渲染的 SPA 页面？是则调此工具"

示例（好的 when_to_use）：
- "用户要求抓取被 Cloudflare 保护的网页"
- "用户要搜索 X/Twitter 上的推文"
- "用户要查看 GitHub 仓库的 README 和目录结构"

示例（坏的 when_to_use）：
- "当你需要获取网页内容时"（太宽泛）
- "该工具用于搜索推文"（复述功能）

只输出 JSON，不要其他内容。"""

    response = call_llm(prompt)

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        return json.loads(response[start:end])
    except:
        return {"when_to_use": desc.split("。")[0] if desc else f"使用 {name}"}


def validate_ai_hints(tool: dict) -> dict:
    """对现有 ai_hints 做正/反向触发验证。"""
    name = tool.get("name", "")
    desc = tool.get("description", "")
    hints = tool.get("ai_hints", {})
    when_to_use = hints.get("when_to_use", desc)

    prompt = f"""你是一个 AI Agent 工具配置验证器。测试以下工具的 ai_hints 是否会误触发或漏触发。

工具信息：
- 名称: {name}
- 描述: {desc}
- when_to_use: {when_to_use}

基于以上描述，做以下测试：
1. 生成 3 个真实用户提示，你 100% 确定应该触发这个工具
2. 生成 3 个看起来相似但不应该触发这个工具的提示（负向触发）
3. 评价 when_to_use 描述：太宽泛？太窄？给出优化建议

输出 JSON 格式：
{{
  "positive_triggers": ["提示1", "提示2", "提示3"],
  "negative_triggers": ["提示1", "提示2", "提示3"],
  "critique": "评价和优化建议",
  "optimized_when_to_use": "优化后的 when_to_use（如需要）"
}}

只输出 JSON，不要其他内容。"""

    response = call_llm(prompt)

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        return json.loads(response[start:end])
    except:
        return {"error": f"LLM 返回解析失败: {response[:200]}"}


def main():
    validate_mode = "--validate" in sys.argv
    apply_mode = "--apply" in sys.argv
    single_name = None
    if "--name" in sys.argv:
        idx = sys.argv.index("--name")
        if idx + 1 < len(sys.argv):
            single_name = sys.argv[idx + 1]

    with open(MANIFEST_PATH) as f:
        data = json.load(f)

    tools = data.get("tools", [])

    if validate_mode:
        # 验证模式
        if single_name:
            to_process = [t for t in tools if t.get("name") == single_name]
        else:
            to_process = [t for t in tools if t.get("ai_hints")]

        print(f"验证模式: {len(to_process)} 个工具\n")

        results = []
        for i, tool in enumerate(to_process, 1):
            name = tool.get("name", "")
            print(f"[{i}/{len(to_process)}] {name}...", end=" ", flush=True)

            try:
                result = validate_ai_hints(tool)
                results.append({"name": name, "result": result})
                if "error" in result:
                    print(f"❌ {result['error']}")
                else:
                    print(f"✅ 正: {len(result.get('positive_triggers', []))} 反: {len(result.get('negative_triggers', []))}")
            except Exception as e:
                print(f"❌ {e}")

        # 打印汇总
        print(f"\n\n{'='*60}")
        print("验证结果汇总")
        print(f"{'='*60}\n")
        for r in results:
            print(f"\n## {r['name']}")
            if "error" in r["result"]:
                print(f"  ❌ {r['result']['error']}")
            else:
                print(f"  ✅ 正: {r['result'].get('positive_triggers', [])}")
                print(f"  ❌ 反: {r['result'].get('negative_triggers', [])}")
                if r["result"].get("optimized_when_to_use"):
                    print(f"  💡 优化: {r['result']['optimized_when_to_use']}")

    else:
        # 生成模式
        if single_name:
            to_process = [t for t in tools if t.get("name") == single_name]
            if not to_process:
                print(f"❌ 找不到工具: {single_name}")
                return
        else:
            # 处理所有 ai_hints 质量不高的工具
            to_process = [
                t
                for t in tools
                if not t.get("ai_hints")
                or (isinstance(t.get("ai_hints"), dict) and len(t["ai_hints"]) <= 1)
                or (
                    isinstance(t.get("ai_hints"), dict)
                    and "当你需要" in t["ai_hints"].get("when_to_use", "")
                )
            ]

        print(f"需要生成: {len(to_process)} 个工具\n")

        for i, tool in enumerate(to_process, 1):
            name = tool.get("name", "")
            print(f"[{i}/{len(to_process)}] {name}...", end=" ", flush=True)

            try:
                hints = generate_ai_hints_with_llm(tool)
                tool["ai_hints"] = hints
                print(f"✅ {hints.get('when_to_use', '')[:60]}")
            except Exception as e:
                print(f"❌ {e}")

        if apply_mode:
            with open(MANIFEST_PATH, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 已写入 {MANIFEST_PATH}")
        else:
            print(f"\n💡 加 --apply 参数实际修改文件")


if __name__ == "__main__":
    main()
