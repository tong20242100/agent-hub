---
name: Update Checker
description: 技能与工具更新检测器 - 一键检测 GitHub Release、npm 包和本地脚本依赖更新
version: 2.0.0
protocol: nexus-2.0
---

# Update Checker: 技能更新检测

## 定位

自动检测技能和工具的版本更新，支持：
- **GitHub Release**: 二进制工具自动检测最新版本
- **npm 包**: Node.js 包版本检测
- **本地脚本依赖**: 检测 brew/pip/npm 依赖更新

## 工具列表

| 工具 | 用途 | 输出格式 |
|------|------|----------|
| `update_check` | 检查更新状态 | JSON |
| `update_report` | 生成可读报告 | Markdown |

## 使用示例

### 检查更新

```bash
# JSON 输出（适合程序解析）
python3 bin/skill_update_check --json

# Markdown 报告（适合人类阅读）
python3 bin/skill_update_check

# 交互式更新
python3 bin/skill_update_check -i
```

### 报告示例

```
# 🔍 技能更新检测报告

## 🔴 需要更新
| 工具 | 当前版本 | 最新版本 | 操作 |
|------|----------|----------|------|
| agency-bin-lightpanda | nightly-20260310 | nightly-20260317 | [下载](...) |

## 📦 本地技能
| 工具 | 版本 | 状态 |
|------|------|------|
| agency-bin-media-extract | 2.0.2 | 🔄 依赖可更新: yt-dlp |
|   └ yt-dlp | 2026.2.21 | 🔄 pip |
| agency-bin-deep-scout | 2.0.3 | 🔄 依赖可更新: beautifulsoup4 |
|   └ beautifulsoup4 | 4.12.3 | 🔄 pip |

## ✅ 已是最新
| 工具 | 版本 | 状态 |
|------|------|------|
| agency-bin-xiaohongshu-mcp | v2026.02 | 已是最新 |
```

## 配置更新源

在 `SCHEMA.json` 中添加 `source` 字段：

### GitHub Release

```json
{
  "source": {
    "type": "github_release",
    "repo": "lightpanda-io/browser",
    "asset_patterns": ["darwin-arm64", "macos-arm64"],
    "installed_version": "nightly-20260315",
    "installed_at": "2026-03-16"
  }
}
```

### npm 包

```json
{
  "source": {
    "type": "npm",
    "package": "opencli",
    "repo": "jackwener/opencli",
    "installed_version": "0.6.2",
    "installed_at": "2026-03-15",
    "update_command": "npm update -g opencli"
  }
}
```

### 本地脚本依赖

在 `SCHEMA.json` 中添加 `dependencies` 字段：

```json
{
  "source": {
    "type": "local_script"
  },
  "dependencies": [
    {"name": "gh", "type": "brew"},
    {"name": "yt-dlp", "type": "pip"},
    {"name": "opencli", "type": "npm"},
    {"name": "xreach", "type": "custom", "check_command": "xreach --version"}
  ]
}
```

#### 支持的依赖类型

| 类型 | 检测方式 | 更新命令 |
|------|----------|----------|
| `brew` | `brew list --versions` | `brew upgrade <name>` |
| `pip` | `pip show` + `pip list --outdated` | `pip install --upgrade <name>` |
| `npm` | `npm list -g` + `npm view` | `npm update -g <name>` |
| `custom` | 自定义 `check_command` | 需手动处理 |

## 技术实现

- **GitHub API**: 使用 `gh release view` 获取最新版本
- **npm**: 使用 `npm view <package> version` 获取版本
- **依赖检测**: 
  - brew: `brew outdated <name>`
  - pip: `pip list --outdated --format=json`
  - npm: `npm view <package> version`
- **缓存**: 结果缓存到 `knowledge/.update_cache.json`

## 自动化

建议配置定期检查：

```bash
# 每天检查一次 (添加到 crontab)
0 9 * * * python3 /path/to/agent-hub/skills/agency-bin-update/bin/skill_update_check --json > /tmp/update_check.json 2>&1
```