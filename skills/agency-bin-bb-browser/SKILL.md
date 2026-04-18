---
name: bb-browser
description: 通过 Chrome 扩展控制已登录浏览器。106 个站点适配器覆盖搜索、社交、开发、视频、金融平台。无 API Key，复用用户登录态。
version: "0.8.3"
protocol: nexus-2.0
---

# bb-browser — 浏览器即 API

## 核心指令

通过 Chrome 扩展直接操作用户已登录的浏览器实例。无需 API Key，复用用户登录态。

## 前置条件

1. Chrome 必须打开且已登录目标网站
2. bb-browser Chrome 扩展必须安装并启用
3. 验证：执行 `bb-browser snapshot -i`

## 站点命令

### 选择规则

- 搜索类任务 → `bb-browser site {platform}/search "{query}"`
- 浏览类任务 → `bb-browser site {platform}/{action} [args]`
- 浏览器自动化 → `bb-browser {command}`

### 常用平台

| 命令 | 用途 | 示例 |
|------|------|------|
| `site google/search` | Google 搜索 | `bb-browser site google/search "AI agent"` |
| `site twitter/search` | Twitter 搜索 | `bb-browser site twitter/search "claude code"` |
| `site twitter/user` | 查看用户 | `bb-browser site twitter/user elonmusk` |
| `site reddit/hot` | Reddit 热门 | `bb-browser site reddit/hot` |
| `site github/repo` | GitHub 仓库 | `bb-browser site github/repo owner/repo` |
| `site youtube/search` | YouTube 搜索 | `bb-browser site youtube/search "rust tutorial"` |
| `site youtube/transcript` | 获取字幕 | `bb-browser site youtube/transcript VIDEO_ID` |
| `site zhihu/hot` | 知乎热榜 | `bb-browser site zhihu/hot` |
| `site xiaohongshu/feed` | 小红书 | `bb-browser site xiaohongshu/feed` |
| `site bilibili/search` | B 站搜索 | `bb-browser site bilibili/search 编程` |
| `site douban/top250` | 豆瓣 Top250 | `bb-browser site douban/top250` |
| `site hackernews/top` | HN 热门 | `bb-browser site hackernews/top 10` |

### 浏览器操作

| 命令 | 用途 |
|------|------|
| `open URL` | 打开页面 |
| `snapshot -i` | 可访问性树 |
| `click @N` | 点击元素 N |
| `fill @N "text"` | 填充输入 |
| `eval "js"` | 执行 JS |
| `fetch URL --json` | 带 Cookie 请求 |
| `screenshot` | 截图 |

## 认证层级

| 层级 | 方式 | 示例平台 |
|------|------|----------|
| Tier 1 | Cookie fetch | Reddit, GitHub |
| Tier 2 | Bearer + CSRF | Twitter, 知乎 |
| Tier 3 | Webpack/Pinia | 小红书 |
