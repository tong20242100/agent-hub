---
name: bb-browser
description: "bb-browser — Your browser is the API. CLI + MCP server for AI agents to control Chrome with your login state."
version: 0.8.3
author: epiral
tags: [browser, automation, ai, agent, chrome, extension, mcp, cdp]
---

# bb-browser (BadBoy Browser)

> **Your browser is the API. No keys. No bots. No scrapers.**

让 AI Agent 直接使用你已登录的 Chrome 浏览器。**849 ⭐**，**106 个适配器 / 36 平台**。

## 安装

```bash
npm install -g bb-browser
bb-browser site update    # 安装社区适配器
```

## Chrome 扩展

1. 从 [Releases](https://github.com/epiral/bb-browser/releases/latest) 下载
2. `chrome://extensions/` → 开发者模式 → 加载已解压的扩展

## MCP 配置

```json
{
  "mcpServers": {
    "bb-browser": {
      "command": "npx",
      "args": ["-y", "bb-browser", "--mcp"]
    }
  }
}
```

## 站点命令（106 个）

### 搜索
```bash
bb-browser site google/search "AI agent"
bb-browser site baidu/search "人工智能"
bb-browser site arxiv/search "transformer"
```

### 社交
```bash
bb-browser site twitter/search "claude code"
bb-browser site twitter/user elonmusk
bb-browser site reddit/hot
bb-browser site weibo/hot
bb-browser site zhihu/hot
bb-browser site xiaohongshu/feed
```

### 开发
```bash
bb-browser site github/repo epiral/bb-browser
bb-browser site github/issues owner/repo
bb-browser site hackernews/top 10
bb-browser site stackoverflow/search "async await"
bb-browser site npm/search "react state"
```

### 视频
```bash
bb-browser site youtube/search "rust tutorial"
bb-browser site youtube/transcript VIDEO_ID
bb-browser site bilibili/search 编程
bb-browser site bilibili/video BV1xxx
```

### 金融
```bash
bb-browser site xueqiu/hot-stock 5
bb-browser site eastmoney/stock 茅台
bb-browser site yahoo-finance/quote AAPL
```

### 娱乐
```bash
bb-browser site douban/top250
bb-browser site douban/movie 泰坦尼克号
```

## 浏览器自动化

```bash
bb-browser open https://example.com     # 打开页面
bb-browser snapshot -i                  # 可访问性树
bb-browser click @3                     # 点击元素
bb-browser fill @5 "hello"              # 填充输入
bb-browser eval "document.title"        # 执行 JS
bb-browser fetch URL --json             # 带 Cookie fetch
bb-browser network requests --with-body # 捕获网络
bb-browser screenshot                   # 截图
```

## 适配器三层复杂度

| 层级 | 认证方式 | 示例 | 时间 |
|---|---|---|---|
| Tier 1 | Cookie fetch | Reddit, GitHub | ~1 分钟 |
| Tier 2 | Bearer + CSRF | Twitter, 知乎 | ~3 分钟 |
| Tier 3 | Webpack/Pinia | 小红书 | ~10 分钟 |

## 与 OpenCLI 对比

| 维度 | OpenCLI | bb-browser |
|---|---|---|
| 连接方式 | Playwright MCP Bridge | Chrome Extension |
| 适配器数量 | ~52 | **106** |
| 平台数量 | 18 | **36** |
| OpenClaw 集成 | ❌ | ✅ |
| 适配器格式 | YAML/TS | **JS 函数** |

## OpenClaw 模式

```bash
bb-browser site reddit/hot --openclaw
bb-browser site xueqiu/hot-stock 5 --openclaw --jq '.items[] | {name}'
```

## Daemon

```bash
bb-browser daemon                        # 默认 localhost:19824
bb-browser daemon --host 127.0.0.1      # IPv4 only
bb-browser daemon --host 0.0.0.0        # 远程访问
```
