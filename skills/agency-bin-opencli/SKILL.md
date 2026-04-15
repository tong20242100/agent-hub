---
name: opencli
description: "OpenCLI — Make any website your CLI. Zero risk, AI-powered, reuse Chrome login."
version: 0.6.2
author: jackwener
tags: [cli, browser, web, mcp, playwright, bilibili, zhihu, twitter, xiaohongshu, xueqiu, AI, agent]
---

# OpenCLI

> Make any website your CLI. Reuse Chrome login, zero risk, AI-powered discovery.

## Install & Run

```bash
# npm global install (recommended)
npm install -g @jackwener/opencli
opencli

# Update to latest
npm update -g @jackwener/opencli
```

## Prerequisites

Browser commands require:
1. Chrome browser running **(logged into target sites)**
2. [Playwright MCP Bridge](https://chromewebstore.google.com/detail/playwright-mcp-bridge/mmlmfjhmonkocbjadbfplnigmagldckm) extension installed
3. Run `opencli setup` to auto-discover token and configure all tools

> **Note**: You must be logged into the target website in Chrome before running commands.

Public API commands (`hackernews`, `v2ex`) need no browser.

## Quick Commands

```bash
# 公开 API（无需浏览器）
opencli hackernews top --limit 10
opencli v2ex hot --limit 10

# 浏览器命令（需要登录）
opencli bilibili hot --limit 10
opencli zhihu hot --limit 10
opencli xiaohongshu search --keyword "美食"
opencli twitter trending --limit 10
opencli reddit hot --subreddit programming
opencli weibo hot --limit 10
opencli xueqiu hot-stock --limit 10

# AI Agent 工作流
opencli explore https://example.com --site mysite
opencli synthesize mysite
opencli generate https://example.com --goal "hot"
opencli cascade https://api.example.com/data
```

## Output Formats

```bash
opencli bilibili hot -f table   # Default: rich terminal table
opencli bilibili hot -f json    # JSON (pipe to jq or LLMs)
opencli bilibili hot -f yaml    # YAML (human-readable)
opencli bilibili hot -f md      # Markdown
opencli bilibili hot -f csv     # CSV
opencli bilibili hot -v         # Verbose: show pipeline steps
```

## 5-Tier Authentication Strategy

| Tier | Name | Method | Example |
|------|------|--------|---------|
| 1 | `public` | No auth, Node.js fetch | Hacker News, V2EX |
| 2 | `cookie` | Browser fetch with `credentials: include` | Bilibili, Zhihu |
| 3 | `header` | Custom headers (ct0, Bearer) | Twitter GraphQL |
| 4 | `intercept` | XHR interception + store mutation | 小红书 Pinia |
| 5 | `ui` | Full UI automation (click/type/scroll) | Last resort |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Timed out connecting to browser` | 1) Chrome must be open 2) Install MCP Bridge extension |
| Empty data returns | Check login status in Chrome |
| Token issues | Run `opencli doctor` |
