# 🦞 Agent-Hub: AI 原生开发宣言

## 1. 大脑优先 (Brain First, Finger Second)
系统内所有的工具不是为了让用户在终端运行，而是为了让 AI 在逻辑流中调用。
- **禁忌**: 严禁设计依赖人类手动选择参数的工具。
- **要求**: 工具必须具备“自解释性”，通过 `ai_hints` 主动宣告其边界。

## 2. 审美自治 (Aesthetic Autonomy)
UI 的产出不应取决于 Prompt 的好坏，而应取决于系统内“设计顾问”的智力高度。
- **流程**: 任务进入 -> AI 调用 Advisor 确定风格 -> 匹配 System MD 提取参数 -> 工程实现。

## 3. 全链路自同步 (Solidified Lifecycle)
所有的上线 (`onboard`)、审计 (`check`) 和下线 (`remove`) 动作都必须由当前主 Agent (Gemini/Claude) 执行并同步全量元数据。
- **单点真相**: `knowledge/tools_manifest.json` 是系统的唯一真理，所有运行时均以此为准。

## 4. 拒绝套娃 (No Nested Agents)
主 Agent 是唯一的决策中心。
- **工具定位**: 工具是“肌肉”，负责 DOM 操作、文件读写、渲染等原子动作。
- **决策外理**: 严禁在工具内部再次隐秘调用 LLM 进行二次决策（特殊情况除外），所有的推理权重应回归主脑。

---
*Agent-Hub | AI-Native Driven*
