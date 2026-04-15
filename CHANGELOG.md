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

### Changed
- 重构 `ah.py`，删除 sync 功能
- 更新 `agency-github-researcher`，添加 analyze_repo 实现
- 修复 `lightpanda` 路径问题

### Removed
- 旧架构文件：semantic_router.py, commander.py, nexus_executor.py
- 历史快照文件：ARMORY.json, manifest.json, .skills_store_lock.json
- 一次性脚本：scripts/ 目录全部内容
- 冗余配置文件：requirements.txt, CODE_OF_CONDUCT.md, TOOLS_MANIFEST.md

## [2.0.0] - 2026-04-14

### 重大变更
- 全面清理历史架构，采用纯 SCHEMA.json 驱动
- 使用 `pyproject.toml` 作为唯一依赖源
- 删除所有冗余脚本和缓存文件
