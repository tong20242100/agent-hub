<div align="center">

# Agent-Hub

**AI 原生的工具共享层 — 一个 MCP，所有 Agent 共享**

[English](README_EN.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

</div>

---

## 这是什么

两层角色：

1. **MCP Server** - 为 AI Agent 提供统一的工具接口，暴露搜索、抓取、社媒、浏览器控制等能力
2. **工具管理器** - 用 `ah` 命令管理本地所有工具（扫描、更新、卸载）

支持 Claude、Gemini、Cursor、Codex、OpenClaw、Hermes 等所有主流 Agent。

---

## 架构

```mermaid
graph LR
    A[Claude Code] -->|MCP| C(Agent-Hub Server)
    B[Cursor / Gemini] -->|MCP| C
    D[OpenClaw / Hermes] -->|MCP| C
    C --> E[web_search]
    C --> F[scrape_url]
    C --> G[chrome-devtools]
    C --> H[xiaohongshu-mcp]
    C --> I[Custom Tool...]
```

所有 Agent 连接同一个 MCP Server，共享同一套工具。

### 模块化设计

```
bin/
├── ah.py              # CLI 入口
└── core/              # 核心逻辑
    ├── auditor.py     # 合规审计
    ├── discovery.py   # 跨平台探测
    └── manager.py     # 技能管理
```

---

## 核心价值

### AI 原生：工具告诉 AI 怎么用自己

每个工具都有 `ai_hints`，让 AI 精准选择：

```json
{
  "ai_hints": {
    "self_check": [
      "你有原生搜索能力吗？有 → 优先用自己的",
      "需要 JSON 结构化输出？是 → 用此工具"
    ],
    "when_to_use": "你没有原生搜索能力时，或需要 Tavily 结构化输出时",
    "examples": [{"query": "AI Agent 最新进展"}],
    "avoid": "你有原生能力时不要用；已知 URL 用 scrape_url"
  }
}
```

`self_check` 让 AI 在调用工具前**强制自检**，避免滥用外部工具。

AI 自己选择工具，不需要路由器、不需要向量检索。

### 统一管理：人类知道本地有什么

```bash
ah scan           # 扫描本地所有工具（包括各 Agent 安装的）
ah list           # 查看工具列表和分布
ah status [name]  # 查看技能分布状态
ah update         # 检测哪些工具需要更新
ah update -i      # 一键更新所有工具
ah check --fix    # 合规性审计（检查 SCHEMA 格式、语气等）
ah discover       # 全域探测其他 Agent 的技能
ah remove <name>  # 卸载工具
```

**解决问题**：
- 本地装了多少工具？分布在哪些 Agent？
- 哪些工具有更新？
- 如何统一卸载？

一处更新，所有 Agent 生效。

### 声明式定义：封装自己的工具

想封装自己的 CLI 工具？在 `skills/<your-tool>/SCHEMA.json` 写一个配置文件：

```
skills/
  my-search/
    SCHEMA.json    ← 工具定义
    bin/
      search       ← 你的脚本
```

MCP Server 自动发现、自动暴露。

---

## 内置工具

覆盖搜索、社媒、浏览器、开发等场景：

| 功能域 | 工具 |
|--------|------|
| 搜索与抓取 | web_search, scrape_url, stealth_get, lightpanda |
| 浏览器控制 | chrome-devtools, bb-browser |
| 社交媒体 | xiaohongshu-mcp, x-article, xreach |
| 开发工具 | gh, deep-researcher, mcp-server |
| 研究与情报 | nvidia, cross-verify |
| 记忆与通知 | memory, notify |

详见 [完整工具清单](docs/skills.md)

---

## 快速开始

### 前置要求

- Python 3.10+
- pip

### 1. 安装

```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

### 2. 启动 MCP Server

```bash
python3 bin/mcp_server.py
```

或使用命令：

```bash
ah server
```

### 3. 配置 Agent

**方法 1：让 Agent 自己配置（推荐）**

把下面这段发给你的 Agent：

```
请帮我配置 Agent-Hub MCP 服务器。项目路径是 /path/to/agent-hub。

你需要：
1. 确定你是哪个 Agent
2. 找到你的配置文件路径
3. 添加 MCP 服务器配置
4. 重启自己

配置完成后，验证：帮我搜索 "MCP protocol"
```

**方法 2：手动配置**

编辑 Agent 配置文件，添加：

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

### 4. 验证

```
帮我搜索 "MCP protocol latest news"
```

---

## 配置参考

详见 [配置文档](docs/configuration.md)，包含所有 Agent 的完整配置示例。

---

## License

MIT
