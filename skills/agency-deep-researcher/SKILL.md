# 深度研究方法论 (Deep Research Methodology)

> 基于 DeerFlow 深度研究方法论，适配 Agent-Hub 架构

---

## 一、核心理念

**永远不要仅凭通用知识生成内容。** 输出质量直接取决于研究的质量和数量。单次搜索永远不够。

---

## 二、四阶段研究法

### Phase 1: 广度探索 (Broad Exploration)

**目标**：理解全局，识别维度

**工具组合**：
```bash
# 1. 原生搜索（主要）
web_search "AI Agent 架构设计 2026"

# 2. GitHub搜索（必须补充）← 获取实际项目
gh search repos "AI Agent architecture" --limit 10

# 3. Twitter/X搜索（必须补充）← 获取最新动态
# 见 agency-bin-x-article skill

# 4. Reddit搜索（必须补充）← 获取社区讨论
python3 bin/search "site:reddit.com AI Agent architecture"

# 5. 本地知识库（如有）
python3 bin/kernel/nexus_executor.py --skill agency-bin-memory --tool memory_query --args '{"query": "AI Agent"}'
```

**步骤**：
1. 用原生搜索进行初步探索
2. 用 `gh search repos` 搜索 GitHub 相关项目（必须）
3. 用 Reddit/Twitter 搜索获取社区讨论（必须）
4. 从结果中识别关键子主题、角度、利益相关方
5. 绘制研究领域地图

**输出检查点**：
```markdown
## Phase 1 多源覆盖
- [ ] 原生搜索已执行
- [ ] GitHub搜索已执行（必须）
- [ ] Twitter/X搜索已执行（必须）
- [ ] Reddit搜索已执行（必须）
- [ ] 本地知识库已查询（如适用）
```

**示例**：
```
主题: "AI Agent 架构设计"
初始搜索:
- "AI Agent architecture patterns 2026"
- "LLM agent framework design"
- "autonomous agent system architecture"

识别维度:
- 多 Agent 协作模式
- 记忆系统设计
- 工具调用机制
- 安全与沙箱
- 评估与测试
```

### Phase 2: 深度挖掘 (Deep Dive)

**目标**：每个维度深入调查

**工具组合**：
```bash
# 1. 原生搜索 + 原生抓取（主要）
web_search "multi-agent orchestration patterns"
web_fetch "https://example.com/article"

# 2. GitHub深度搜索（必须补充）← 获取代码实现
gh search repos "multi-agent orchestration" --limit 5
gh search code "orchestration pattern" --limit 10

# 3. Twitter/X专家观点（必须补充）
python3 bin/search "site:twitter.com OR site:x.com multi-agent"

# 4. Reddit实际经验（必须补充）
python3 bin/search "site:reddit.com multi-agent experience"
```

**步骤**：
1. 用原生搜索+抓取深入阅读权威来源
2. 用 GitHub 搜索获取实际代码实现（必须）
3. 用 Twitter/Reddit 获取真实使用经验（必须）
4. 对关键论文/项目深入阅读

**输出检查点**：
```markdown
## Phase 2 多源覆盖
- [ ] 原生搜索已执行
- [ ] 至少3个权威来源已完整抓取
- [ ] GitHub代码搜索已执行（必须）
- [ ] Twitter/X专家观点已搜索（必须）
- [ ] Reddit使用经验已搜索（必须）
```

**示例**：
```
维度: "多 Agent 协作模式"
精准搜索:
- "multi-agent orchestration patterns"
- "agent communication protocol design"
- "hierarchical agent architecture"

然后抓取阅读:
- 关键研究论文
- 开源项目 README
- 实际案例研究
```

### Phase 3: 多样性与验证 (Diversity & Validation)

**目标**：确保全面覆盖

**工具组合**：
```bash
# 原生搜索（主要）
web_search "AI coding adoption statistics 2026 data market size"
web_search "AI coding challenges limitations failures 2026"
web_search "Andrej Karpathy AI coding future 2026"

# GitHub实际案例（必须补充）
gh search repos "AI coding workflow template" --limit 10
gh search repos "claude-code-skills" --limit 10

# Reddit真实反馈（必须补充）
python3 bin/search "site:reddit.com AI coding workflow experience"
python3 bin/search "site:reddit.com Claude Code vs Cursor"

# Twitter/X最新动态（必须补充）
python3 bin/search "site:twitter.com OR site:x.com AI coding 2026"
```

| 信息类型 | 目的 | 原生搜索 + 平台补充 |
|----------|------|---------------------|
| **事实与数据** | 具体证据 | 原生搜索 + GitHub stars/forks数据 |
| **案例与实例** | 实际应用 | GitHub搜索实际项目 |
| **专家观点** | 权威视角 | 原生搜索 + Twitter/X |
| **趋势预测** | 未来方向 | 原生搜索 + Twitter/X |
| **对比分析** | 上下文 | 原生搜索 + Reddit讨论 |
| **挑战批评** | 平衡视角 | Reddit真实踩坑经验 |

**输出检查点**：
```markdown
## Phase 3 多源覆盖
- [ ] 数据统计已搜索
- [ ] 挑战限制已搜索
- [ ] 专家观点已搜索
- [ ] GitHub案例搜索已执行（必须）
- [ ] Reddit真实反馈已搜索（必须）
- [ ] Twitter/X最新动态已搜索（必须）
```

### Phase 4: 综合检查 (Synthesis Check)

**生成内容前必须验证**：

- [ ] 是否从 3-5 个不同角度搜索？
- [ ] 是否读取了最重要来源的完整内容？
- [ ] 是否有具体数据、案例、专家观点？
- [ ] 是否探索了正面和负面/挑战？
- [ ] 信息是否最新且来源权威？

**⚠️ 多源覆盖必须验证**：

```markdown
## 多源覆盖审计（必须填写）

| 来源 | 使用情况 | 获取到的关键信息 |
|------|----------|------------------|
| 原生搜索 | ___次 | |
| GitHub | ___次 | |
| Twitter/X | ___次 | |
| Reddit | ___次 | |
| 本地知识库 | ___次/N/A | |

**强制补充规则**：
- GitHub搜索 = 0次 → 必须补充，搜索实际项目和代码
- Twitter/X搜索 = 0次 → 必须补充，获取最新动态和专家观点
- Reddit搜索 = 0次 → 必须补充，获取用户真实反馈和踩坑经验
```

**如果有任何 NO 或平台搜索为0次，继续研究后再生成内容。**

---

## 三、搜索策略技巧

### 有效查询模式

```bash
# 带上下文的具体查询
❌ "AI trends"
✅ "enterprise AI adoption trends 2026"

# 包含权威来源提示
"[topic] research paper"
"[topic] McKinsey report"
"[topic] industry analysis"

# 搜索特定内容类型
"[topic] case study"
"[topic] statistics"
"[topic] expert interview"
```

### 时间感知

**始终检查当前日期**，在搜索查询中使用：

| 用户意图 | 时间精度 | 示例查询 |
|----------|----------|----------|
| "今天/刚发布" | 月+日+年 | "tech news March 19 2026" |
| "本周" | 周范围 | "technology releases week of Mar 15 2026" |
| "最近/最新" | 月 | "AI breakthroughs March 2026" |
| "今年/趋势" | 年 | "software trends 2026" |

### 何时使用网页抓取

使用 `scrape_url` 或 `web_fetch` 当：
- 搜索结果高度相关且权威
- 需要摘要之外的详细信息
- 来源包含数据、案例研究、专家分析

---

## 四、迭代优化

研究是迭代的：
1. 回顾已学内容
2. 识别理解空白
3. 制定新的精准查询
4. 重复直到全面覆盖

---

## 五、质量标准

研究充分当你能自信回答：
- 关键事实和数据点是什么？
- 有哪些 2-3 个具体实际案例？
- 专家怎么说？
- 当前趋势和未来方向？
- 有哪些挑战或限制？
- 为什么这个话题现在相关/重要？

---

## 六、常见错误

- ❌ 1-2 次搜索后停止
- ❌ 仅依赖搜索摘要而不读取完整来源
- ❌ 只搜索多面话题的一个方面
- ❌ 忽略矛盾观点或挑战
- ❌ 有新数据时使用过时信息
- ❌ 研究完成前就开始生成内容

---

## 七、Agent-Hub 工具调用指南

### ⚠️ 多源强制补充

**原生搜索（web_search）效率高，但必须补充以下平台搜索：**

| 平台 | 为什么必须 | 命令 |
|------|-----------|------|
| **GitHub** | 代码实现、实际项目、最佳实践案例 | `gh search repos "{query}" --limit 10` |
| **Twitter/X** | 最新动态、专家实时观点、趋势 | 见 agency-bin-x-article |
| **Reddit** | 真实用户反馈、社区讨论、踩坑经验 | `python3 bin/search "site:reddit.com {query}"` |
| **本地知识库** | 项目特定知识、历史积累 | `python3 bin/kernel/nexus_executor.py --skill agency-bin-memory --tool memory_query` |

### 强制补充规则

```
研究流程
├─ 原生 web_search（主要来源，效率高）
├─ ➕ GitHub搜索（必须补充）← 获取代码实现和真实项目
├─ ➕ Twitter/X搜索（必须补充）← 获取最新动态和专家观点  
├─ ➕ Reddit搜索（必须补充）← 获取用户真实反馈
└─ ➕ 本地知识库（如有相关内容）
```

### 检查点机制

**每完成一个Phase，必须验证多源覆盖：**

```markdown
## 多源搜索检查

| 来源类型 | 使用情况 | 获取到的关键信息 |
|----------|----------|------------------|
| 原生搜索 | ✅ ___次 | |
| GitHub | ✅/❌ | 如❌必须补充 |
| Twitter/X | ✅/❌ | 如❌必须补充 |
| Reddit | ✅/❌ | 如❌必须补充 |
| 本地知识库 | ✅/❌/N/A | |

**强制规则**：
- GitHub搜索 = 0次 → 必须补充，搜索实际项目
- Twitter/X搜索 = 0次 → 必须补充，获取最新动态
- Reddit搜索 = 0次 → 必须补充，获取社区讨论
```

### 网页抓取选择

```
网页抓取
├─ 原生 web_fetch（主要方式，效率高）
├─ 静态页面（无防护）
│   └─ python3 bin/scrape "{url}" ← 备用
├─ 有防护（Cloudflare/小红书/知乎）
│   └─ stealth_get (Scrapling) ← 反爬专用
└─ 需要 JS 渲染
    └─ lightpanda ← 轻量无头浏览器
```

---

## 八、证据等级标注

所有研究输出必须标注证据等级：

- **🟢 L1 实证**: 官方文档/GitHub 源码/物理运行日志
- **🟡 L2 共识**: 3 个以上独立专业来源的交叉验证
- **🟠 L3 推断**: 基于现有事实的逻辑闭环推演
- **🔴 L4 假说**: 尚未验证的猜测，必须标注"需进一步验证"

---

## 九、输出模板

研究完成后，应该有：

```markdown
# [主题] 研究报告

> 研究日期: YYYY-MM-DD
> 证据等级: L1/L2/L3/L4

## 一、核心发现
...

## 二、关键数据
...

## 三、案例分析
...

## 四、专家观点
...

## 五、趋势与挑战
...

## 六、结论与建议
...

---
*研究方法：[使用的工具和方法]*
```

---

*方法论来源：DeerFlow Deep Research Skill + Agent-Hub 适配*
