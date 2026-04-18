---
name: defuddle
description: 网页内容提取器。从任意 URL 或 HTML 提取主要内容并转换为 Markdown。Obsidian 团队开发，Mozilla Readability 的现代替代。
version: "0.13.0"
protocol: nexus-2.0
---

# Defuddle — 内容提取

## 核心指令

从 URL 或 HTML 文件中提取主要内容，输出 Markdown 格式。适用于：
- 抓取文章、博客、文档的正文内容
- 去除导航、广告、侧边栏等噪音
- 提取标题、作者、发布日期等元数据

## 执行命令

```
defuddle parse {url} --markdown
```

### 可选参数

| 参数 | 用途 |
|------|------|
| `--markdown` / `-m` | 输出 Markdown（默认） |
| `--json` / `-j` | 输出 JSON（含元数据） |
| `--property {name}` | 提取特定属性（title/author/description） |
| `--output {file}` / `-o` | 保存到文件 |
| `--debug` | 调试模式 |

## 返回值属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `title` | string | 文章标题 |
| `author` | string | 作者 |
| `content` | string | 清理后的正文 |
| `description` | string | 摘要 |
| `published` | string | 发布日期 |
| `image` | string | 主图 URL |
| `language` | string | 语言代码 |
| `wordCount` | number | 字数 |

## 使用场景

- 用户要求"提取这篇文章的正文" → 使用 defuddle
- 用户要求"把网页转成 Markdown" → 使用 defuddle
- 已知具体 URL，不需要 JS 渲染 → 使用 defuddle（比 lightpanda 更快）

## 注意事项

- 需要 JS 渲染的页面先用 `lightpanda` 获取 HTML，再传给 defuddle
- 有反爬保护的页面用 `stealth_get` 获取 HTML，再传给 defuddle
