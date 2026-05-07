# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.6.0] - 2026-04-29

### 🔍 执行可观测性 (Execution Observability)
- **进化记录仪 (Evolution Recorder)**: 新增自动化日志系统。实时捕获每一次调用的完整绝对路径 Shell 指令、多维审计结果（退出码、输出质量）、执行耗时及系统环境指纹。
- **日志持久化**: 日志以 JSONL 格式存储于 `knowledge/logs/evolution_*.jsonl`，为 AI 自我优化提供法证级数据支持。

### 🧩 语义聚合架构 (Semantic Aggregation)
- **Schema 驱动合并**: 引入 `mcp_strategy: merge` 配置。自动将 Chrome DevTools (28+ 工具)、Browser Bridge、XReach 等原子化工具聚合为语义化“元工具”。
- **突破客户端限制**: 成功将默认暴露工具数量从 102 个降低至 51 个，彻底解决 Antigravity/Cursor 等客户端的 100 工具数量硬上限报错。
- **Action/Payload 协议**: 统一聚合工具的调用模式，提升 AI 在复杂交互场景下的决策确定性。

### ⚙️ 核心引擎优化 (Core Engine)
- **智能路径发现**: `mcp_server.py` 支持 `{skill_path}` 占位符与自动路径补全，实现技能包内二进制文件的“即插即用”。
- **修复函数缺失**: 补全了 `find_all_skill_dirs` 核心逻辑，增强了扫描的健壮性。

### 📜 协议与文档 (Protocols & Docs)
- **`GEMINI.md`**: 注入“设计师思维”与“全局工具调用金律”，强制 AI 执行意图探测与分层调度。
- **README 重构**: 全面转向“技能管理网关与执行追踪系统”定位，更新双语文档及架构图。

## [2.5.0] - 2026-04-28

### 🚀 全链路生命周期固化 (Lifecycle Solidification)
- **`ah onboard <path>` (新增)**: 一键上线新技能。自动同步清单 (`tools_manifest.json`)、能力地图 (`TOOL_MAP.md`)、双语 README 架构图、并自动写入 MCP 配置与刷新缓存。
- **`ah remove <skill>` (增强)**: 真正的物理与逻辑全链路下线，确保清单、文档、配置零残留。
- **`ah eval` (新增)**: Agent 原生质量评估工具。不依赖外部 LLM，通过语义重叠与结构审计对全量工具进行风险分级。
- **`ah discover --onboard` (增强)**: 支持一键捕获并上线探测到的外部 Agent 技能。
- **`ah update --install` (增强)**: 升级为自动更新并同步全链路元数据。

### 🎨 AI 原生设计套件 (True Design Suite)
- **`agency-design-advisor`**: 审美决策顾问。基于内容摘要自动匹配全球最高级的设计基因。
- **`agency-design-system-md`**: 内置 Apple, Stripe, Linear 等 69 个品牌的设计规范库（DESIGN.md）。
- **`agency-huashu-design`**: 高保真交互原型与 Cinematic 产品动画工程引擎。
- **`agency-guizang-ppt`**: 电子杂志美学 HTML 幻灯片生成器。

### 🧠 AI Hint 资产质量跃迁
- **全量开光**: 系统内 97 个工具的 Hint 全部达到 **100 分（完美）** 评级。
- **冲突消解**: 实施 `Namespace:Action` 精准触发机制，彻底解决 DevTools 与 Browser 家族的语义重叠。
- **`bin/generate_ai_hints.py`**: 重构为“主 Agent 驱动”模式，支持双写固化到物理 SCHEMA.json。

### 🧹 架构纯粹化与去虚名化
- **唯一决策中心**: 删除了 `config/model_router.json`，拒绝“大脑套娃”，所有推理权重回归当前主 Agent。
- **统一运行时**: `mcp_server.py` 切换为“清单驱动（Single Source of Truth）”加载逻辑。
- **清理残留**: 物理抹除 `.iflow`, `.sc`, `.mcp.json`, `setup.sh` 等环境依赖。
- **原则确立**: 固化 `docs/principles.md` (AI 原生开发宣言)。

## [2.1.0] - 2026-04-15

### AI Hints 质量全面优化

基于 [skills-best-practices](https://github.com/mgechev/skills-best-practices) 的最佳实践，
全面升级所有 SCHEMA.json 的 `ai_hints` 和 SKILL.md。

#### 核心改进

- **消除"当你需要"模式**：全部 15 个 SCHEMA.json 的 `when_to_use` 改为第三人称指令式，
  如"用户需要搜索网页时"而非"当你需要搜索网页时"
- **统一 hints 结构**：所有工具现在都有明确的 `when_to_use`（含真实场景示例）、
  `examples`（真实 URL/参数）、`avoid`（明确的负向条件）
- **修复损坏的 hints**：修复 `notebook-ops` 和 `runner` 的截断/乱码 `when_to_use` 和空 `examples`

#### SKILL.md 渐进披露重构

- **全部 11 个 SKILL.md 重写**：改为第三人称指令式，消除人类文档风格
- **复杂逻辑抽到 references/**：色调表（`color_palette.json`）、研究 checklist（`research_checklist.json`）、
  输出模板（`output_template.json`）从 SKILL.md 移出
- **确定性逻辑脚本化**：ljg-card 的密度/结构/情绪判断逻辑抽到 `bin/analyze_content.py`

#### 验证机制

- `generate_ai_hints.py` 新增 `--validate` 模式，批量测试现有 hints 的正/反向触发准确性

### SKILL.md 重写清单

| 文件 | 行数变化 | 主要改进 |
|------|---------|---------|
| `agency-deep-researcher` | 407→127 | 四阶段流程引用 `research_checklist.json` |
| `agency-bin-chrome-devtools` | 233→110 | 删除安装配置说明，保留 Agent 指令 |
| `agency-github-researcher` | 115→57 | 引用 `output_template.json` |
| `agency-ljg-card` | 90→85 | 引用 `color_palette.json`，新增 `analyze_content.py` |
| `agency-bin-defuddle` | 112→55 | 删除纯人类文档风格 |
| `agency-bin-opencli` | 115→75 | 删除安装指南，保留指令 |
| `agency-bin-update` | 118→60 | 删除配置指南段 |
| `agency-bin-memory` | 96→60 | 删除 MCP 配置段 |
| `agency-bin-lightpanda` | 71→50 | 删除对比表，保留指令 |
| `agency-bin-xiaohongshu-mcp` | 65→45 | 补充完整流程 |
| `agency-bin-bb-browser` | 162→80 | 删除纯人类文档，新增指令流程 |

### ai_hints 修复清单

| 文件 | 修复内容 |
|------|---------|
| `agency-bin-notebook-ops` | 修复截断 `when_to_use`，补充 `examples` |
| `agency-bin-runner` | 修复截断 `when_to_use`，补充 `examples` |
| `agency-bin-search` | 添加 `when_to_use`/`avoid` |
| `agency-bin-scrape` | 替换 placeholder URL 为真实示例，添加 `when_to_use`/`avoid` |
| `agency-bin-scrapling-stealth` | 替换 placeholder URL，完善 `when_to_use` |
| `agency-bin-media-extract` | 完善 `when_to_use`，`avoid` 改为真正的负向条件 |
| `agency-bin-xreach` | 替换 `conditions` 为 `when_to_use`，添加 `avoid` |
| `agency-bin-x-article` | 添加 `when_to_use`/`avoid` |
| `agency-bin-nvidia` | 替换 `conditions` 为 `when_to_use`，添加 `avoid` |
| `agency-bin-cross-verify` | 完善 `when_to_use`，`avoid` 改为真正的负向条件 |
| `agency-bin-notify` | 完善 `when_to_use`，`avoid` 改为真正的负向条件 |
| `agency-bin-full-scan` | 完善 `when_to_use`/`examples` |
| `agency-ljg-card` | 添加 `avoid`，完善 `when_to_use` |
| `agency-bin-lightpanda` | 替换 placeholder URL，完善 `when_to_use` |
| `agency-deep-researcher` | 添加 `when_to_use`/`examples`/`avoid`/`before_call`（两级） |

## [2.0.0] - 2026-04-14

### 重大变更
- 全面清理历史架构，采用纯 SCHEMA.json 驱动
- 使用 `pyproject.toml` 作为唯一依赖源
- 删除所有冗余脚本和缓存文件
