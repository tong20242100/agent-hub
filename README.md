<div align="center">

# Agent-Hub

**Agent 技能中枢与执行可观测系统 (Agent Skill Gateway & Observability System)**

[English](README_EN.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Agent Skills](https://img.shields.io/badge/Standard-Agent%20Skills-orange.svg)](https://github.com/google/skills)
[![Observability](https://img.shields.io/badge/Debug-Observability-blue.svg)](https://agent-hub.io)

</div>

---

## 🏛️ 项目定位

**Agent-Hub** 是一个面向生产环境的 Agent 技能调度与管理网关。它深度接入 Anthropic/Google 主导的 **Agent Skills** 开放标准，通过“手脑分离”架构，将 **MCP 执行工具** 与 **认知决策协议** 完美解耦。

### 三大核心价值

1.  **全域技能调度 (Skill Orchestration)**：统一管理本地 MCP 工具 (⚙️)、内置认知协议 (🧠) 与外部知识库 (📖)。
2.  **思维与执行对齐 (Thought-Action Alignment)**：通过认知协议引导 Agent 的决策逻辑（如 Atlas 架构师协议），并自动对齐 Google WAF 全球最佳实践。
3.  **执行全过程回溯 (Full Traceability)**：记录每一次工具调用的 Shell 指令快照、多维审计报告与环境指纹。

---

## 🚀 核心工程特性

### 1. 深度适配 Agent Skills 开放标准
项目采用 **Progressive Disclosure（渐进式披露）** 架构，大幅降低模型 Token 消耗：
- **名称匹配激活**：默认仅加载技能元数据（约 80-100 tokens）。
- **按需知识注入**：通过 `SKILL.md` 与 `references/` 拆分，只有在真正需要时才加载详细指令。

### 2. 标准化管理工具链 (`ah` CLI)
通过 `ah` 命令行工具实现技能的全生命周期管理：
- `ah list`: **全景视图**。使用图标区分执行工具 (⚙️)、认知协议 (🧠) 与外部知识 (📖)。
- `ah discover`: **雷达探测**。全域搜索本机的 Claude, Cursor, Gemini 及标准 Skills 技能。
- `ah link`: **全局同步**。一键将本地认知协议同步至 `~/.agents/skills/`，实现跨平台通用。
- `ah check & eval`: **质量审计**。对工具 Hint 进行压力测试，排除语义冲突与幻觉。

### 3. 执行轨迹追踪 (Execution Recorder)
生成的 `evolution_*.jsonl` 日志包含：
- **指令快照**：后台执行的完整命令（含参数转义现场）。
- **多维审计**：退出码、输出纯度校验、系统环境指纹、执行耗时。

---

## 📦 技能分类全景

| 类型 | 代表模块 | 作用 |
|:---:|---|---|
| **⚙️ Tool** | `agency-bin-search`, `chrome-devtools` | **“手”**：通过 MCP 协议执行物理操作 |
| **🧠 Cognitive** | `agency-architecture-atlas`, `ai-engineer` | **“脑”**：引导 Agent 的思考模式与工程标准 |
| **📖 Knowledge** | `google-cloud-waf`, `gemini-api` | **“眼”**：引入 Google 官方的权威知识与 WAF 规范 |

---

## 快速开始

### 1. 环境准备
```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

### 2. 常用操作
- `ah list`: 查看当前就绪的所有能力。
- `ah link`: 将内置认知协议同步至全局，让 Claude/Gemini 自动识别。
- `python3 bin/mcp_server.py`: 启动 StdIO 模式下的 MCP 服务网关。

### 3. Google WAF 对齐
本项目内置的认知协议（如 Atlas 架构师）已显式引用 Google 官方 WAF 技能：
- 决策时自动对齐 **Security**、**Reliability** 与 **Cost Optimization** 标准。

---

## 📜 许可证
遵循 MIT 协议。项目设计坚持 AI-Native 优先与“JSON, not glue code”的设计哲学。
