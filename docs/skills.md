# 技能清单

34 个技能，按功能域组织。

> **💡 MCP 聚合模式说明**
> 为了兼容 Antigravity/Cursor 等客户端的 100 个工具数量限制，部分复杂技能在 MCP 环境下会聚合为一个“元工具”，采用 `action/payload` 模式调用。详情请见下表中的 **MCP:** 标识。

## 搜索与抓取

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-bin-search | 3.0.0 | Tavily 全网搜索 | web_search |
| agency-bin-scrape | 3.0.0 | 网页静态抓取 | scrape_url |
| agency-bin-scrapling-stealth | 2.0.2 | 隐身爬虫（反爬） | stealth_get |
| agency-bin-defuddle | 0.14.0 | Obsidian 官方内容提取 | parse, extract_title, to_markdown |
| agency-bin-lightpanda | 1.0.0 | Zig 无头浏览器，11x 速度 | fetch, serve, mcp |

## 浏览器控制

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-bin-chrome-devtools | 0.20.1 | Google 官方 Chrome DevTools MCP | **MCP: chrome_devtools** (聚合 28 个操作) |
| agency-bin-bb-browser | 0.8.3 | 浏览器即 API，AI 控制 Chrome | **MCP: bb_browser** (聚合 13 个操作) |

## 社交媒体

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-bin-xiaohongshu-mcp | 2.1.0 | 小红书 MCP 标准化工具 | login, search, publish_image |
| agency-bin-x-article | 1.0.0 | X/Twitter 长文获取 | x_article |
| agency-bin-xreach | 1.0.0 | X/Twitter 数据采集 | **MCP: x_twitter_ops** (聚合 7 个操作) |
| agency-bin-opencli | 0.6.2 | 17 个网站一键 API 化 | 23 个站点 |

## 开发工具

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-bin-gh | 2.0.2 | GitHub 仓库探测 | gh_view |
| agency-github-researcher | 1.0.0 | GitHub L1 实证研究 | analyze_repo |
| agency-bin-mcp-server | 2.1.0 | MCP 协议适配器 | list_tools, call_tool |
| agency-bin-runner | 2.0.2 | 物理代码执行器 | run_code |

## 研究与情报

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-deep-researcher | 2.0.0 | 多源深度研究报告 | deep_research, web_search, web_fetch, github_search |
| agency-bin-nvidia | 1.0.0 | NVIDIA GPU 情报站 | scout, probe, advise, rank |
| agency-bin-cross-verify | 2.0.2 | 反证据验证工具 | verify |

## 记忆与通知

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-bin-memory | 1.0.0 | 跨工具共享知识层 | query, save, profile, index |
| agency-bin-notify | 2.0.2 | 多端消息推送（飞书/Bark） | send |
| agency-bin-notebook-ops | 2.1.0 | NotebookLM 自动化 | auth, query, clean |

## 系统管理

| 技能 | 版本 | 描述 | 工具 |
|------|------|------|------|
| agency-bin-update | 2.1.0 | 技能更新检测与安装 | check, install, deps |
| agency-bin-full-scan | 1.0.0 | 全量深度扫描 | full_scan |
| agency-bin-media-extract | 2.0.2 | 音视频与 YouTube 提取 | extract |
| agency-bin-viral-engine | 2.0.2 | 内容裂变引擎 | transform |

---

## 致谢

感谢所有开源项目的开发者：Lightpanda、Chrome DevTools MCP、bb-browser、Defuddle、OpenCLI、xiaohongshu-mcp 等。

## 🎨 AI-Native Design & UI

| Skill | Tool | Role |
|-------|------|------|
| **Design Advisor** | `recommend_design_dna` | 审美决策顾问，根据内容匹配最佳品牌基因。 |
| **Design System MD** | `get_brand_design` | 跨品牌视觉规范库，内置 Apple, Stripe 等 69+ 品牌指南。 |
| **Huashu Design** | `design_prototype` | 高保真工程引擎，生成可点击 HTML 原型与发布动画。 |
| **Guizang PPT** | `generate_magazine_ppt` | 演示专家，生成电子杂志美学的 HTML 幻灯片。 |

