# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 34 个技能（含 full-scan 全量扫描）
- 全量深度扫描工具 `ah full-scan`
- 更新检测与安装工具 `ah update [-i]`
- 技能卸载工具 `ah remove <skill>`
- `references/` 结构化数据层：`color_palette.json`、`output_template.json`、`research_checklist.json`
- `bin/analyze_content.py`：ljg-card 内容分析脚本（密度/结构/情绪自动判定）
- `generate_ai_hints.py --validate`：正/反向触发验证模式

### Changed
- 重构 `ah.py`，删除 sync 功能
- 更新 `agency-github-researcher`，添加 analyze_repo 实现
- 修复 `lightpanda` 路径问题

### Removed
- 旧架构文件：semantic_router.py, commander.py, nexus_executor.py
- 历史快照文件：ARMORY.json, manifest.json, .skills_store_lock.json
- 一次性脚本：scripts/ 目录全部内容
- 冗余配置文件：requirements.txt, CODE_OF_CONDUCT.md, TOOLS_MANIFEST.md

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
