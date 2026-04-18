---
name: memory
description: 跨工具知识层。语义检索、保存洞察、同步用户偏好。基于 ChromaDB，为所有 AI 工具提供统一的知识服务。
version: "1.0.0"
protocol: nexus-2.0
---

# Memory — 跨工具知识层

## 核心指令

为多个 AI 工具提供统一的知识服务。所有研究结果、用户偏好、决策记录都存储于此，跨工具共享。

## 工具选择

| 工具 | 用途 | 示例 |
|------|------|------|
| `memory_query` | 语义搜索知识库 | `memory_query query="AI Agent 架构"` |
| `memory_save` | 保存洞察/决策/代码 | `memory_save type=insight content="..."` |
| `memory_profile` | 获取/更新用户偏好 | `memory_profile action=get` |
| `memory_index` | 重建向量索引 | `memory_index` |

## 记忆类型

| 类型 | 用途 | 示例 |
|------|------|------|
| `insight` | 研究发现、技术洞察 | "Lightpanda 内存占用是 Chrome 的 1/9" |
| `preference` | 用户偏好 | "用户偏好简洁输出，不要过多解释" |
| `decision` | 技术决策 | "选择 FastAPI 而非 Flask 作为后端" |
| `snippet` | 代码片段 | "ChromaDB 查询示例代码" |

## 典型工作流

### 研究后保存

```
1. 完成研究（gh_view / web_search / scrape_url）
2. memory_save type=insight content="{研究摘要}" tags=["主题"]
```

### 查询历史研究

```
1. 用户问"上次研究的 X 是什么？"
2. memory_query query="X"
3. 返回研究结果
```

### 偏好同步

```
1. 用户设置偏好 → memory_profile action=update
2. 下次会话开始 → memory_profile action=get
3. 注入到 system prompt
```

## 技术实现

- 向量引擎：ChromaDB + sentence-transformers (all-MiniLM-L6-v2)
- 存储位置：`knowledge/.chroma_db/` + `knowledge/notes/`
- 用户偏好：`knowledge/user_profile.json`
