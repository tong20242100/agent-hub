---
name: Lightpanda
description: Zig 编写的无头浏览器。fetch 模式快速抓取，serve 模式提供 CDP 服务器，mcp 模式供 AI Agent 调用。内存占用 1/9 Chrome，速度 11x。
version: "1.0.0"
protocol: nexus-2.0
---

# Lightpanda — 轻量无头浏览器

## 核心指令

Zig 编写的无头浏览器，适用于三种场景：
1. 快速抓取（fetch 模式）
2. CDP 服务器（serve 模式）
3. AI Agent 调用（mcp 模式）

## 模式选择

### fetch — 快速抓取

适用于需要 JS 渲染但无交互的页面。

```
bin/lightpanda fetch --dump markdown {url}
bin/lightpanda fetch --dump html {url}
bin/lightpanda fetch --dump markdown --obey_robots {url}
```

### serve — CDP 服务器

适用于 Puppeteer/Playwright 连接。

```
bin/lightpanda serve --host 127.0.0.1 --port 9222
```

连接示例：
```javascript
const browser = await puppeteer.connect({
  browserWSEndpoint: "ws://127.0.0.1:9222"
});
```

### mcp — AI Agent 调用

```
bin/lightpanda mcp
```

## 对比参考

- 静态页面（无 JS 渲染）→ 用 `scrape_url`，更快
- 需要 JS 渲染 → 用 `lightpanda` fetch 模式
- 需要交互 → 用 `chrome-devtools`
- 有反爬保护 → 用 `stealth_get`

## 限制

- Beta 阶段，部分网站不兼容
- 无 WebGL 支持
- Web API 覆盖不完整
