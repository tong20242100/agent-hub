<div align="center">

# Agent-Hub

**一次安装，所有 AI Agent 共享**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

</div>

---

## 这是什么

一个 MCP 服务器，让你写的 CLI 工具能被所有 AI Agent 共享使用。

支持：Claude Code、Claude Desktop、Gemini CLI、Cursor、Codex CLI、**OpenClaw Agent**、**Hermes Agent** 等。

**写一次 SCHEMA.json，所有 Agent 都能调用。**

---

## 为什么需要

你安装了 Claude、Gemini、Cursor、OpenClaw、Hermes 多个 Agent，每个都要重复配置工具。同一个工具装 N 遍，版本还不一致。

Agent-Hub 解决这个问题：**工具只需安装一次，所有 Agent 通过 MCP 共享。**

---

## 开箱即用

**34 个技能包**，配置后立刻可用：

| 功能 | 技能包 |
|------|--------|
| 网页搜索 | `agency-bin-search` (Tavily API) |
| 网页抓取 | `agency-bin-scrape`, `agency-bin-scrapling-stealth` |
| 浏览器控制 | `agency-bin-chrome-devtools` (29 个操作) |
| GitHub | `agency-bin-gh`, `agency-github-researcher` |
| 小红书 | `agency-bin-xiaohongshu-mcp` |
| 跨 Agent 记忆 | `agency-bin-memory` |

---

## 核心价值

### 1. 声明式定义

**传统方式**：写 Python glue code，注册工具，处理参数...

**Agent-Hub 方式**：写一个 SCHEMA.json，完事。

```json
{
  "name": "my-search",
  "tools": {
    "search": {
      "description": "搜索网页",
      "command": "bin/search {query}",
      "parameters": {
        "type": "object",
        "properties": { "query": {"type": "string"} },
        "required": ["query"]
      }
    }
  }
}
```

MCP Server 自动发现，自动暴露。

### 2. AI 自描述工具

每个工具都有 `ai_hints`，告诉 LLM **何时用、怎么用、何时不用**：

```json
{
  "ai_hints": {
    "when_to_use": "用户需要获取最新网页信息",
    "avoid": "不要用于已知的静态页面"
  }
}
```

**工具主动告诉 AI 怎么用自己。** 这是 Agent-Hub 独有的差异化。

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

### 2. 配置 Agent

**方法 1：让 Agent 自己配置（推荐）**

直接把下面这段发给你的 Agent：

```
请帮我配置 Agent-Hub MCP 服务器。项目路径是 /path/to/agent-hub。

你需要：
1. 确定你是哪个 Agent（Claude Code、Gemini CLI、Cursor、Codex、OpenClaw、Hermes 等）
2. 找到你的配置文件路径
3. 添加 MCP 服务器配置

配置完成后，验证工具是否可用：帮我搜索 "MCP protocol"
```

**方法 2：手动配置**

编辑对应配置文件，添加：

```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

| Agent | 配置格式 | 配置文件 |
|-------|---------|---------|
| Claude Code CLI | JSON | `~/.claude.json` |
| Claude Desktop | JSON | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Gemini CLI | JSON | `~/.gemini/settings.json` |
| Cursor | JSON | `~/.cursor/mcp.json` |
| Codex CLI | TOML | `~/.codex/config.toml` |
| OpenClaw Agent | JSON | `~/.openclaw/openclaw.json` |
| Hermes Agent | YAML | `~/.hermes/config.yaml` |

**注意**：Codex 用 TOML，Hermes 用 YAML，格式略有不同。详见 [配置文档](docs/configuration.md)。

### 3. 验证

在 Agent 中测试：

```
帮我搜索 "MCP protocol latest news"
```

---

## 统一管理

```bash
ah scan           # 扫描所有工具
ah list           # 查看列表
ah update         # 检测更新
ah update -i      # 一键更新所有
ah remove <name>  # 卸载
```

一处更新，处处生效。

---

## License

MIT