---
name: Update Checker
description: 版本更新检测器。检测 GitHub Release、npm 包、brew/pip 依赖的版本更新。生成 JSON 或 Markdown 报告。
version: "2.0.0"
protocol: nexus-2.0
---

# Update Checker — 版本更新检测

## 核心指令

检测已安装工具和依赖的版本更新。支持 GitHub Release、npm、pip、brew 四种来源。

## 工具选择

| 工具 | 输出 | 用途 |
|------|------|------|
| `update_check` | JSON | 程序解析 |
| `update_report` | Markdown | 人类阅读 |

## 执行命令

```
python3 bin/skill_update_check          # Markdown 报告
python3 bin/skill_update_check --json   # JSON 输出
python3 bin/skill_update_check -i       # 交互式更新
```

## 配置要求

每个 skill 的 `SCHEMA.json` 必须定义 `source` 字段：

### GitHub Release

```json
{
  "source": {
    "type": "github_release",
    "repo": "owner/repo",
    "asset_patterns": ["darwin-arm64"],
    "installed_version": "v1.0.0"
  }
}
```

### npm 包

```json
{
  "source": {
    "type": "npm",
    "package": "package-name",
    "repo": "owner/repo",
    "installed_version": "0.6.2",
    "update_command": "npm update -g package-name"
  }
}
```

### 依赖检测

```json
{
  "dependencies": [
    {"name": "gh", "type": "brew"},
    {"name": "yt-dlp", "type": "pip"},
    {"name": "opencli", "type": "npm"}
  ]
}
```

## 缓存

结果缓存到 `knowledge/.update_cache.json`，避免重复请求。
