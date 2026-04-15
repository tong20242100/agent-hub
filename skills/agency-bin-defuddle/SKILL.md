---
name: defuddle
description: "Defuddle — Obsidian 官方内容提取工具，从任意网页提取主要内容并转换为 Markdown"
version: 0.13.0
author: kepano (Obsidian Team)
tags: [content-extraction, markdown, readability, obsidian, web-clipper, html]
---

# Defuddle

> de·​fud·dle /diˈfʌdl/ *transitive verb*  
> to remove unnecessary elements from a web page, and make it easily readable.

Obsidian 团队开发的内容提取工具，**5,136 ⭐**，Mozilla Readability 的现代替代方案。

## 安装

```bash
npm install -g defuddle
```

## CLI 使用

```bash
# 解析 URL 并输出 Markdown
defuddle parse https://example.com/article --markdown

# 解析本地 HTML 文件
defuddle parse page.html --markdown

# 输出 JSON（含元数据）
defuddle parse https://example.com --json

# 提取特定属性
defuddle parse https://example.com --property title
defuddle parse https://example.com --property author
defuddle parse https://example.com --property description

# 保存到文件
defuddle parse https://example.com --markdown -o article.md

# 调试模式
defuddle parse https://example.com --debug
```

## CLI 选项

| 选项 | 别名 | 说明 |
|---|---|---|
| `--output <file>` | `-o` | 输出到文件 |
| `--markdown` | `-m` | Markdown 格式 |
| `--json` | `-j` | JSON 格式（含元数据） |
| `--property <name>` | `-p` | 提取特定属性 |
| `--debug` | | 调试模式 |

## Node.js API

```javascript
import { parseHTML } from 'linkedom';
import { Defuddle } from 'defuddle/node';

const { document } = parseHTML(html);
const result = await Defuddle(document, 'https://example.com/article', {
  markdown: true
});

console.log(result.content);      // Markdown 内容
console.log(result.title);        // 标题
console.log(result.author);       // 作者
console.log(result.published);    // 发布日期
console.log(result.schemaOrgData);// schema.org 数据
```

## 返回数据

| 属性 | 类型 | 说明 |
|---|---|---|
| `title` | string | 文章标题 |
| `author` | string | 作者 |
| `content` | string | 清理后的内容 |
| `description` | string | 摘要 |
| `domain` | string | 域名 |
| `image` | string | 主图 URL |
| `published` | string | 发布日期 |
| `site` | string | 网站名称 |
| `language` | string | 语言代码 |
| `wordCount` | number | 字数 |
| `schemaOrgData` | object | schema.org 数据 |

## 与 Mozilla Readability 对比

| 维度 | Readability | Defuddle |
|---|---|---|
| 策略 | 激进删除 | **更宽容** |
| 脚注标准化 | ❌ | ✅ |
| 数学公式 | ❌ | ✅ |
| 代码块标准化 | ❌ | ✅ |
| schema.org | ❌ | ✅ |
| CLI | ❌ | ✅ |

## 典型用途

- Web Clipper / 网页剪藏
- 内容聚合 / RSS
- AI 训练数据准备
- 网页转 Markdown
- 文章阅读模式
