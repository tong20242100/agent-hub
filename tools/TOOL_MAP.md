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
| **研究** | 自己迭代 | `deep_research` | 需要自动化多源研究 |

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
