<div align="center">

# Agent-Hub

**把任何 CLI 工具变成 AI 技能。写 JSON，不写胶水代码。**

[English](README_EN.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)

</div>

---

## 这是什么

Agent-Hub 是一个运行在本地的 **MCP 技能网关**，解决一个具体问题：

> 你有一堆 CLI 工具（搜索、浏览器、GitHub、通知……），但 AI 不知道它们存在，也不知道什么时候该用哪个。

Agent-Hub 的做法是：每个工具写一个 `SCHEMA.json`，声明它能做什么、什么时候用、什么时候不用。MCP Server 启动后，AI 就能自主路由，不需要你每次手动指定。

```
你说："帮我研究一下这个 GitHub 仓库"
AI 自己决定：调 gh_view → 调 web_search → 调 cross-verify
不需要你告诉它用哪个工具
```

---

## 三层架构

项目把 AI 的能力分成三类，互不干扰：

| 层 | 类型 | 数量 | 作用 |
|---|---|---|---|
| ⚙️ **Tool** | MCP 执行工具 | 33 个 | 执行物理操作：搜索、浏览器、抓取、通知… |
| 🧠 **Cognitive** | 认知协议 | 11 个 | 注入思维框架：架构师、增长黑客、现实检验… |
| 📖 **Knowledge** | 外部知识文档 | 13 个 | 按需注入权威规范：Google WAF、Gemini API… |

**Tool** 是手，负责执行。**Cognitive** 是脑，负责决策框架。**Knowledge** 是眼，负责引入外部标准。三者解耦，可以独立更新。

---

## 核心工具一览

| 场景 | 工具 | 说明 |
|---|---|---|
| 全网搜索 | `web_search` | Tavily 协议，返回结构化摘要 |
| 浏览器自动化 | `chrome-devtools` | 29 个操作，点击/截图/审计 |
| 反爬抓取 | `scrapling-stealth` | 绕过 Cloudflare |
| X/Twitter | `xreach` | 搜索推文 |
| 小红书 | `xiaohongshu-mcp` | 扫码登录，搜索笔记 |
| GitHub 深度分析 | `gh_view`, `analyze_repo` | 仓库结构与代码逻辑 |
| 媒体提取 | `media-extract` | YouTube/B站字幕与元数据 |
| 幻觉验证 | `cross-verify` | 强制扫库验证单边结论 |
| 通知推送 | `notify` | 飞书 / Bark |
| 长期记忆 | `memory` | 向量语义搜索知识库 |

---

## `ai_hints`：让 AI 自主路由的关键

每个工具的 `SCHEMA.json` 里有一个 `ai_hints` 字段，这是整个系统的核心机制：

```json
{
  "ai_hints": {
    "intent": "通过 Tavily 协议采集结构化互联网实时证据",
    "when_to_use": "需要验证时效性事实、获取原始 URL 集合时",
    "avoid": [
      "已知具体 URL（用 scrape_url）",
      "查本地知识库（用 memory_query）",
      "X/Twitter 深度检索（用 xreach）"
    ],
    "self_check": [
      "任务是否涉及当前事实的验证？",
      "是否需要获取包含原始来源的结构化数据？"
    ]
  }
}
```

AI 读到这个描述，就知道：这个工具在什么场景下用，在什么场景下不用，调用前要自检什么。不需要你在 Prompt 里反复解释。

---

## `ah` CLI：技能全生命周期管理

```bash
ah list              # 查看所有已注册技能（⚙️/🧠/📖 分类）
ah onboard <path>    # 上线新技能：注册 + 同步清单 + 清理缓存
ah check             # 合规性审计：命名、语气、Hint 质量、依赖检查
ah eval              # Hint 质量压力测试：检测语义冲突
ah discover          # 全域探测：扫描 Claude/Cursor/Gemini/Kiro 的已有技能
ah link              # 将认知协议同步至 ~/.agents/skills/，跨平台通用
ah analyze           # 日志诊断：失败率、burst 调用、从未调用的工具
ah update            # 检测并更新所有技能
```

`ah analyze` 是系统的自我诊断入口，读取执行日志，输出：

```
✅ 系统健康度: 92%  (11/12 次调用正常) | 注册工具: 103 个

🔴 工具失败报告:
  • 🔴 HIGH  read_elite_prompt  失败率 100%

🚫 从未调用的工具（建议核查）:
  • take_snapshot / memory_save / ...
```

---

## 快速开始

```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

**启动 MCP Server（接入 Claude/Cursor/Kiro）：**

```bash
python3 bin/mcp_server.py
```

在你的 AI 客户端 MCP 配置里指向这个进程，所有技能立即可用。

**查看当前就绪的能力：**

```bash
ah list
```

**将认知协议同步至全局（让 Claude Code / Gemini CLI 自动识别）：**

```bash
ah link
```

---

## 执行轨迹

每次工具调用都会写入 `knowledge/logs/evolution_*.jsonl`：

```json
{
  "tool": "web_search",
  "duration_ms": 2969,
  "status": "success",
  "audit": { "ok": true },
  "command_run": "/Users/.../bin/search 'CEFR graded sentences dataset'",
  "output_preview": { "stdout": "🔍 搜索结果..." }
}
```

包含完整命令快照、退出码、输出纯度校验、执行耗时。`ah analyze` 读取这些日志做系统诊断。

---

## 设计原则

- **AI 自主路由**：工具通过 `ai_hints` 自描述，AI 自己决定调什么，不依赖人工指定
- **单点真相**：`knowledge/tools_manifest.json` 是所有工具的唯一注册表，`ah onboard/remove` 自动维护
- **手脑分离**：执行工具（Tool）和思维框架（Cognitive）解耦，互不干扰
- **工具内禁止套娃**：工具只做原子操作，不在内部隐秘调用 LLM 做二次决策

---

## 许可证

MIT
