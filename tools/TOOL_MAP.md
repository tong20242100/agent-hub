# Agent-Hub 能力地图

**这不是工具列表，这是 Agent 没有的能力。**

---

## 🎯 核心差异化（Agent 必定没有）

| 场景 | 工具 | 说明 |
|------|------|------|
| **小红书** | `xiaohongshu_search` | 搜索小红书笔记 |
| **X/Twitter** | `x_search`, `x_user`, `x_tweet` | X 搜索、用户、推文 |
| **反爬** | `stealth_get` | 绕过 Cloudflare |
| **GitHub 深度** | `gh_view`, `analyze_repo` | 仓库深度分析 |

---

## 🔧 增强能力（Agent 有，但这个更好）

| 场景 | Agent 原生 | Agent-Hub | 选择建议 |
|------|-----------|-----------|----------|
| **搜索** | Google Search | `web_search` (Tavily) | 需要 AI 摘要用 Tavily |
| **浏览器** | 无 | `chrome-devtools` (29 个) | 需要交互/调试用 |

---

## 🚫 不需要的能力（Agent 已有，不要重复）

| 场景 | Agent 原生 | Agent-Hub | 建议 |
|------|-----------|-----------|------|
| **文件操作** | `read_file`, `list_directory` | — | 用 Agent 原生 |
| **网页抓取** | `web_fetch` | `scrape_url` | 用 Agent 原生 |
| **记忆** | 内置记忆 | `memory_*` | 用 Agent 原生 |

---

## 🧭 选择指南

```
用户需求: "搜索 X 上关于 AI Agent 的讨论"
  └── Agent 判断: 这是 X 平台
      └── 调用: x_search ✓

用户需求: "搜索最新的 AI 新闻"
  └── Agent 判断: 这是全网搜索
      └── 选择: Google Search (原生) 或 web_search (Tavily)
          ├── 需要快速结果 → Google Search
          └── 需要 AI 摘要 → web_search

用户需求: "抓取小红书页面"
  └── Agent 判断: 这是反爬场景
      └── 调用: stealth_get ✓

用户需求: "读取项目文件"
  └── Agent 判断: 这是文件操作
      └── 调用: read_file (原生) ✓
      └── 不要调用: scrape_url ✗
```

---

## 📊 工具统计

| 类别 | 数量 | 暴露策略 |
|------|------|----------|
| 核心差异化 | 10 | ✅ 必须暴露 |
| 增强能力 | 40 | ✅ 按需暴露 |
| 重复能力 | 5 | ❌ 不暴露（或标记为备选） |
| 人格认知 | 8 | ❌ 不暴露（注入 system prompt） |

---

## 🔄 动态加载

```
Agent 启动时:
  ├── 加载工具列表（92 个）
  └── 加载能力地图（本文档）

Agent 调用时:
  ├── 读取能力地图，定位场景
  └── 选择合适的工具
```

---

*这是给 Agent 的导航图，不是约束。Agent 自己决定何时用什么。*
Test line
| **agency-huashu-design** | `multiple` | 生成高保真交互原型 (HTML/CSS/JS) |
| **agency-guizang-ppt** | `multiple` | 基于归藏模版生成单文件 HTML PPT |
| **agency-bin-search** | `multiple` | 全网搜索。返回 AI 摘要和相关来源。 |
| **agency-bin-chrome-devtools** | `multiple` | 点击页面元素。例如: click(selector='button#submit') |
| **agency-bin-browser-harness** | `multiple` | 运行 Python 代码直接控制浏览器。helpers 已预导入。例如: bh(python_code='new_tab("https://google.com"); wait_for_load(); print(page_info())') |
| **agency-bin-cross-verify** | `multiple` | 强制扫库验证单边结论，杜绝幻觉。例如: verify(claim='AI 将取代程序员') |
| **agency-bin-nvidia** | `multiple` | 搜索可用模型。latest=最新模型，stable=推荐模型 |
| **agency-bin-media-extract** | `multiple` | 提取 YouTube/B站 等媒体的字幕与元数据。例如: extract(url='https://youtube.com/...') |
| **agency-bin-opencli** | `multiple` | OpenCLI 统一入口。支持 17 个网站: bilibili/twitter/xiaohongshu/zhihu/weibo/reddit/v2ex/xueqiu/youtube/hackernews/bbc/reuters/smzdm/ctrip/boss/coupang/yahoo-finance。用法: opencli <site> <command> [args] |
| **agency-bin-bb-browser** | `multiple` | 执行站点命令。例如: bb_site(command='twitter/search', args=['AI agent']) |
| **agency-bin-scrapling-stealth** | `multiple` | 绕过 Cloudflare 盾牌提取网页。支持主动交互（点击、滚动等）。 |
| **agency-bin-xiaohongshu-mcp** | `multiple` | 【安全禁令：扫码唯一性】启动物理浏览器扫码登录。禁止使用账号密码自动填充。登录后必须确保此账号在其他浏览器页签中已退出，严禁多端网页登录。 |
| **agency-bin-xreach** | `multiple` | 搜索 X/Twitter 推文 |
| **agency-ljg-card** | `multiple` | 将内容铸成 PNG 视觉卡片。默认长图模式，-i 信息图、-m 多卡、-v 视觉笔记、-c 漫画、-w 白板。 |
| **agency-bin-notify** | `multiple` | 推送通知至飞书/Bark 等通讯端。例如: send(message='任务完成') |
| **agency-bin-read-file** | `multiple` | 读取本地文本文件内容。例如: read_file(path='README.md') |
| **agency-bin-x-article** | `multiple` | 获取 X Article 文章完整内容。支持 /i/article/ 和 /status/ 两种 URL 格式，返回标题、正文、Grok摘要、所有图片URL、作者信息、发布时间和互动统计。 |
| **agency-bin-mcp-server** | `multiple` | 列出所有可用的 MCP 工具。 |
| **agency-bin-notebook-ops** | `multiple` | 启动 Google 登录认证流程，保存 NotebookLM 登录状态。 |
| **agency-github-researcher** | `multiple` | 对 GitHub 仓库进行 L1 级实证研究：分析 README、目录树、关键配置文件及核心代码逻辑。 |
| **agency-bin-memory** | `multiple` | 语义搜索知识库。输入自然语言查询，返回最相关的知识片段。支持跨工具共享，一次记住到处可用。 |
| **agency-bin-update** | `multiple` | 检测所有技能和工具的更新状态，返回需要更新的列表。 |
| **agency-bin-full-scan** | `multiple` | 全量扫描所有Agent技能目录，检测嵌套技能和符号链接 |
| **agency-bin-gh** | `multiple` | 查看 GitHub 仓库信息。例如: gh_view(repo='owner/repo') |
| **agency-bin-runner** | `multiple` | 物理执行 Python 脚本并捕获日志。例如: run_code(file='test.py') |
| **agency-bin-lightpanda** | `multiple` | 抓取网页内容。支持 html/markdown/semantic_tree 输出。例如: fetch(url='https://example.com', dump='markdown') |
| **agency-bin-scrape** | `multiple` | 提取网页内容为 Markdown。支持 --recursive 递归追踪外部链接 |
| **agency-bin-defuddle** | `multiple` | 解析网页内容。例如: defuddle_parse(url='https://example.com', format='markdown') |
| **agency-design-system-md** | `multiple` | 获取指定品牌的设计系统规范。输入 '--list' 查看所有 69 个支持品牌。 |
| **agency-design-radar** | `multiple` | 在设计雷达中搜索系统。关键词可为品牌名或标签（如 Enterprise, Mobile）。 |
| **agency-design-advisor** | `multiple` | 基于内容摘要推荐最佳匹配的设计系统 DNA。 |
| **agency-architect-vault** | `multiple` | The Architect Vault - 顶级 AI 架构师原力库。存储全球主流厂商 (OpenAI, Anthropic, Google) 的原始泄露 System Prompts 与工具规范。 |
| **agency-openai-brain** | `multiple` | 基于大模型协议的长期记忆引擎。实现自然语言级的用户画像刻画与偏好对齐。 |
| **agency-infograph** | `multiple` | New Skill |
