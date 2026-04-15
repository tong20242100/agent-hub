---
name: Lightpanda
description: Zig 编写的无头浏览器，内存占用 1/9 Chrome，速度 11x。专为 AI Agent 和自动化设计。
version: "1.0.0"
emoji: 🐼
---

# Lightpanda 使用指南

## 核心优势
- **内存**: 215MB vs Chrome 2GB (9x 节省)
- **速度**: 11x faster than Chrome
- **兼容**: Puppeteer / Playwright / chromedp (CDP 协议)

## 三种模式

### 1. fetch - 快速抓取
```bash
# Markdown 输出
bin/lightpanda fetch --dump markdown https://example.com

# HTML 输出
bin/lightpanda fetch --dump html https://example.com

# 遵守 robots.txt
bin/lightpanda fetch --dump markdown --obey_robots https://example.com
```

### 2. serve - CDP 服务器
```bash
# 启动服务
bin/lightpanda serve --host 127.0.0.1 --port 9222

# Puppeteer 连接
const browser = await puppeteer.connect({
  browserWSEndpoint: "ws://127.0.0.1:9222"
});
```

### 3. mcp - AI Agent 调用
```bash
# MCP stdio 模式
bin/lightpanda mcp
```

## 与现有工具对比

| 场景 | 推荐工具 |
|------|----------|
| 快速抓取，零依赖 | `agency-bin-scrape` (Jina Reader) |
| JS 渲染、反爬 | `agency-bin-lightpanda` |
| AI Agent 自动化 | `agency-bin-lightpanda` (MCP 模式) |
| 大规模爬取 | `agency-bin-lightpanda` (serve 模式) |

## 注意事项
- Beta 阶段，部分网站可能不兼容
- Web API 覆盖不完整（无 WebGL）
- 遇到问题提 issue: https://github.com/lightpanda-io/browser/issues
