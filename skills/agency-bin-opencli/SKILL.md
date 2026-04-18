---
name: opencli
description: 网站 CLI 封装器。复用 Chrome 登录态，将任意网站功能封装为 CLI 命令。支持 B 站、知乎、小红书、Twitter、Reddit 等 18 个平台。
version: "0.6.2"
protocol: nexus-2.0
---

# OpenCLI — 网站即 CLI

## 核心指令

通过复用 Chrome 浏览器登录态，将网站功能暴露为 CLI 命令。

## 前置条件

1. Chrome 必须打开且已登录目标网站
2. Playwright MCP Bridge 扩展必须安装
3. 已运行 `opencli setup` 完成初始化

## 命令选择

### 公开 API（无需浏览器）

| 命令 | 用途 | 示例 |
|------|------|------|
| `hackernews top --limit N` | HN 热门 | `opencli hackernews top --limit 10` |
| `v2ex hot --limit N` | V2EX 热门 | `opencli v2ex hot --limit 10` |

### 浏览器命令（需要登录）

| 命令 | 用途 | 示例 |
|------|------|------|
| `bilibili hot --limit N` | B 站热门 | `opencli bilibili hot --limit 10` |
| `zhihu hot --limit N` | 知乎热榜 | `opencli zhihu hot --limit 10` |
| `xiaohongshu search --keyword K` | 小红书搜索 | `opencli xiaohongshu search --keyword "美食"` |
| `twitter trending --limit N` | Twitter 趋势 | `opencli twitter trending --limit 10` |
| `reddit hot --subreddit S` | Reddit 热门 | `opencli reddit hot --subreddit programming` |
| `weibo hot --limit N` | 微博热搜 | `opencli weibo hot --limit 10` |
| `xueqiu hot-stock --limit N` | 雪球热门 | `opencli xueqiu hot-stock --limit 10` |

### 输出格式

| 参数 | 格式 |
|------|------|
| `-f table` | 表格（默认） |
| `-f json` | JSON（可管道给 jq 或 LLM） |
| `-f yaml` | YAML |
| `-f md` | Markdown |
| `-f csv` | CSV |

### 高级命令

| 命令 | 用途 |
|------|------|
| `explore URL --site NAME` | 探索新网站，生成适配器 |
| `synthesize NAME` | 合成已发现的命令 |
| `generate URL --goal GOAL` | 从目标生成命令 |
| `cascade URL` | 级联 API 调用 |

## 认证层级

| Tier | 方式 | 示例 |
|------|------|------|
| 1 public | 无需认证 | Hacker News, V2EX |
| 2 cookie | Cookie fetch | B 站, 知乎 |
| 3 header | 自定义请求头 | Twitter GraphQL |
| 4 intercept | XHR 拦截 | 小红书 Pinia |
| 5 ui | 全 UI 自动化 | 最后手段 |
