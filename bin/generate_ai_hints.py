#!/usr/bin/env python3
"""
用 LLM 批量生成 AI 原生的 ai_hints

用法:
    python3 bin/generate_ai_hints.py              # 预览模式
    python3 bin/generate_ai_hints.py --apply      # 实际修改
    python3 bin/generate_ai_hints.py --apply --name stealth_get  # 单个工具
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
  "when_to_use": "触发条件。格式：'当输入包含 X / 用户说 Y / 任务需要 Z 时调用'",
  "examples": [{{"参数名": "可直接使用的值"}}],
  "avoid": "容易犯的错，简短直接"
}}

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


def main():
    apply_mode = "--apply" in sys.argv
    single_name = None
    if "--name" in sys.argv:
        idx = sys.argv.index("--name")
        if idx + 1 < len(sys.argv):
            single_name = sys.argv[idx + 1]

    with open(MANIFEST_PATH) as f:
        data = json.load(f)

    tools = data.get("tools", [])

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
