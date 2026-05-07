<div align="center">

# Agent-Hub

**Agent 技能管理网关与执行追踪系统 (Agent Skill Management Gateway & Execution Tracing System)**

[English](README_EN.md) | 中文

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Observability](https://img.shields.io/badge/Debug-Observability-blue.svg)](https://agent-hub.io)

</div>

---

## 🏛️ 项目定位

**Agent-Hub** 是一个面向生产环境的 Agent 工具网关。它通过语义聚合、标准化生命周期管理和执行轨迹追踪，解决 Agent 在复杂工具链下的“决策失准”与“难以调试”问题，提升系统的运行可靠性。

### 三大技术支柱

1.  **能力聚合 (Semantic Aggregation)**：将底层原子 API 聚类为具有语义深度的能力模块。降低 LLM 的决策压力，减少无效调用。
2.  **生命周期管理 (Unified Lifecycle)**：通过 `ah` CLI 实现技能的标准化集成、全域扫描、自动更新与安全卸载。
3.  **执行可观测性 (Execution Observability)**：实时记录工具调用的 Shell 指令快照、多维审计报告与环境指纹，实现执行过程的完全回溯。

---

## 🚀 核心工程特性

### 1. 基于 Schema 的插件式架构
每个技能通过 `SCHEMA.json` 实现自解释：
- **边界感知**：利用 `ai_hints` 明确工具的触发场景与资源成本。
- **动态聚合**：通过 **Schema-Driven Merging** 策略自动合并复杂操作，适配 MCP 客户端 100 工具的硬性限制。
- **路径自发现**：支持 `{skill_path}` 占位符，实现技能包的即插即用，无需手动配置绝对路径。

### 2. 标准化管理工具链 (CLI)
通过 `ah` 命令行工具，将碎片化的脚本转化为受管技能：
- `ah onboard <path>`: 标准化集成新的技能包。
- `ah scan`: 自动化全域发现，建立本地能力索引。
- `ah update -i`: 追踪 GitHub/NPM 动态，实现技能版本对齐。
- `ah remove <name>`: 物理级卸载。

### 3. 执行轨迹追踪仪 (Execution Recorder)
为每一次工具调用提供详细的“诊断报告”：
- **指令快照**：捕捉后台执行的完整绝对路径指令（含参数转义现场）。
- **多维审计**：记录退出码、输出质量校验（长度、错误词匹配）等结果。
- **环境快照**：包含 OS 版本、Python 环境及执行耗时。

---

## 📦 内置能力模块

| 模块名称 | 核心工具 (MCP) | 技术价值 |
|--------|------|------|
| **设计顾问** | `design_advisor` | 提供视觉决策参考，提升 UI 生成的一致性 |
| **浏览器控制** | `chrome_devtools` | **[聚合模式]** 编排复杂交互，提高填表与截图效率 |
| **社媒采集** | `x_twitter_ops` | **[深度聚合]** 结构化提取 X (Twitter) 数据链 |
| **代码审计** | `analyze_repo` | 提取 GitHub 源码证据，降低 AI 幻觉 |
| **交付表现** | `huashu_design` | 自动化生成交互原型与产品演示动画 |

---

## 快速开始

### 1. 安装环境
```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

### 2. 服务管理
- `ah server`: 启动 MCP 协议网关。
- `ah scan`: 校验并查看当前已就绪的技能索引。

### 3. 开发建议
在处理涉及设计、调研等模糊任务时，建议利用 `design_advisor` 等工具先进行意图对齐，利用 `evolution_*.jsonl` 日志进行错误诊断。

---

## 📜 许可证
遵循 MIT 协议。项目设计坚持数据驱动（Data-Driven）与解耦原则。
