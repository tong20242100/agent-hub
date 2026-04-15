---
name: Memory
description: 跨工具共享知识层 - 一次记住，到处可用
version: 1.0.0
protocol: nexus-2.0
---

# Memory: 跨工具知识层

## 定位

为 VS Code、iFlow、Antigravity 等多个 AI 工具提供**统一的知识服务**：
- 语义检索历史研究、决策、代码片段
- 跨工具共享用户偏好
- 持久化记忆，永不丢失

## 工具列表

| 工具 | 用途 | 示例 |
|------|------|------|
| `memory_query` | 语义搜索知识库 | `"浏览器自动化工具"` |
| `memory_save` | 保存记忆/洞察 | `type=insight, content="..."` |
| `memory_profile` | 获取/更新用户偏好 | `action=get` |
| `memory_index` | 重建向量索引 | 新增知识后调用 |

## 使用场景

### 场景 1: 跨工具知识检索

```
# 在 VS Code 中研究 Lightpanda
用户: "研究 lightpanda-io/browser"
AI: 调用 agency-bin-gh, 保存研究结果...

# 在 iFlow 中查询
用户: "上次研究的浏览器工具是什么？"
AI: 调用 memory_query("浏览器工具")
    ← 返回 Lightpanda 研究报告
```

### 场景 2: 偏好同步

```
# 在任意工具设置偏好
用户: "记住，我以后都要简洁输出"
AI: 调用 memory_profile(action=update, updates={"preferences":{"tone":"direct"}})

# 其他工具自动适配
AI: 调用 memory_profile(action=get)
    ← {"tone": "direct"}
    → 注入到 system prompt
```

### 场景 3: 主动记忆

```
用户: "记住这个项目结构很重要"
AI: 调用 memory_save(type=insight, content="...", tags=["architecture"])
```

## 技术实现

- **向量引擎**: ChromaDB + sentence-transformers (all-MiniLM-L6-v2)
- **存储位置**: `knowledge/.chroma_db/` + `knowledge/notes/`
- **用户偏好**: `knowledge/user_profile.json`

## 首次使用

```bash
# 索引现有知识库
python3 knowledge/vector_store.py index --force
```

## MCP 接入

在支持 MCP 的工具中配置：

```json
{
  "mcpServers": {
    "agent-hub-memory": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/kernel/nexus_executor.py", "--skill", "agency-bin-memory", "--tool"]
    }
  }
}
```
