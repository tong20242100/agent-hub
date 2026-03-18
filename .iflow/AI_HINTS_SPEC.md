# AI Native ai_hints 规范 (v1.0)

> **核心原则**：AI 不需要"理解"自然语言，只需要"匹配"结构化字段。

---

## 标准结构

```json
{
  "ai_hints": {
    "triggers": ["关键词1", "关键词2"],
    "intent": "意图描述（一句话）",
    "conditions": {
      "use_this": ["条件1", "条件2"],
      "use_alternative": {
        "tool_name": "条件描述"
      }
    },
    "examples": [
      {"param1": "value1"}
    ]
  }
}
```

---

## 字段说明

| 字段 | 类型 | 必需 | 用途 |
|------|------|------|------|
| `triggers` | `string[]` | ✅ | 用户输入关键词匹配（中英文） |
| `intent` | `string` | ✅ | 一句话意图，用于语义路由 |
| `conditions.use_this` | `string[]` | ✅ | 使用此工具的场景条件 |
| `conditions.use_alternative` | `object` | ⚪ | 替代工具及场景 |
| `examples` | `object[]` | ✅ | 参数示例 |

---

## 写作原则

### 1. Triggers：覆盖中英文，覆盖同义词

```json
// ❌ 不好
"triggers": ["click"]

// ✅ 好
"triggers": ["点击", "click", "按钮", "button", "按键", "触发"]
```

### 2. Intent：一句话，无歧义

```json
// ❌ 不好
"intent": "当用户需要在浏览器中点击按钮、链接或其他可交互元素时"

// ✅ 好
"intent": "点击浏览器中的可交互元素"
```

### 3. Conditions：明确的条件分支

```json
// ❌ 不好
"conditions": {
  "use_this": ["需要交互"],
  "use_alternative": {
    "scrape_url": "静态页面更快"
  }
}

// ✅ 好
"conditions": {
  "use_this": ["有按钮需要点击", "有表单需要填写", "有下拉菜单"],
  "use_alternative": {
    "scrape_url": "静态内容，无需交互",
    "stealth_get": "有反爬保护"
  }
}
```

### 4. Examples：真实可用的参数组合

```json
// ❌ 不好
"examples": [{}]

// ✅ 好
"examples": [
  {"selector": "button#submit"},
  {"selector": "a.more-link"},
  {"selector": "[data-testid='accept-cookies']"}
]
```

---

## 工具分类标准

### 按交互程度

| 类型 | 工具 | 特征 |
|------|------|------|
| 零交互 | `scrape_url` | 只读，无 JS，无保护 |
| 轻交互 | `stealth_get` | 只读，可能有 JS，有保护 |
| 中交互 | `lightpanda` | 只读，JS 渲染 |
| 重交互 | `chrome-devtools` | 读写，完整浏览器控制 |

### 按数据源

| 源 | 主工具 | 备选 |
|------|------|------|
| 静态网页 | `scrape_url` | - |
| 有保护网页 | `stealth_get` | - |
| GitHub 快览 | `agent-reach/gh_view` | - |
| GitHub 深析 | `agency-bin-gh` | `agency-github-researcher` |
| X/Twitter | `x_search` / `x_user` | - |
| 全网搜索 | `search_web` | - |
| 本地知识 | `memory_query` | - |

---

## 模板

### 零交互工具模板

```json
{
  "ai_hints": {
    "triggers": ["抓取", "scrape", "爬取", "获取", "fetch", "网页", "page"],
    "intent": "快速提取静态网页内容",
    "conditions": {
      "use_this": ["静态页面", "无反爬保护", "无 JS 渲染需求"],
      "use_alternative": {
        "stealth_get": "有 Cloudflare/小红书/知乎保护",
        "lightpanda": "需要 JS 渲染",
        "chrome-devtools": "需要点击/填写等交互"
      }
    },
    "examples": [
      {"url": "https://example.com"},
      {"url": "https://blog.example.com/article/123"}
    ]
  }
}
```

### 重交互工具模板

```json
{
  "ai_hints": {
    "triggers": ["点击", "click", "填写", "fill", "浏览器", "browser", "交互"],
    "intent": "在浏览器中执行交互操作",
    "conditions": {
      "use_this": ["需要点击按钮", "需要填写表单", "需要等待加载", "需要调试页面"],
      "use_alternative": {
        "scrape_url": "静态内容，无需交互",
        "stealth_get": "有保护但无需交互"
      }
    },
    "examples": [
      {"action": "click", "selector": "button#submit"},
      {"action": "fill", "selector": "input[name='q']", "value": "search term"}
    ]
  }
}
```

### 数据源工具模板

```json
{
  "ai_hints": {
    "triggers": ["github", "仓库", "repo", "代码", "code"],
    "intent": "快速查看 GitHub 仓库信息",
    "conditions": {
      "use_this": ["查看仓库基本信息", "查看 README"],
      "use_alternative": {
        "agency-bin-gh": "需要查看文件结构/源码/Release",
        "agency-github-researcher": "需要深度实证研究报告"
      }
    },
    "examples": [
      {"repo": "owner/repo"}
    ]
  }
}
```

---

## 验证清单

每个 ai_hints 必须通过以下检查：

- [ ] `triggers` 至少包含 3 个关键词（中英文混合）
- [ ] `intent` 不超过 15 个字
- [ ] `conditions.use_this` 至少 1 条明确条件
- [ ] `conditions.use_alternative` 覆盖主要替代场景
- [ ] `examples` 至少 1 个真实可用示例
- [ ] 无"相关功能时"、"请参考工具描述"等废话

---

*Version 1.0 | 2026-03-17*
