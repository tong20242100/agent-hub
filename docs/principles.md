# Agent-Hub 技能开发原则 (Skill Development Principles)

为了确保 Agent-Hub 能够精准地被各类 AI Agent（如 Claude、Gemini、Hermes）识别并高效调用，所有存放在 `skills/` 目录下的技能必须遵循以下核心原则。

> [!NOTE]
> 本原则深度参考并对齐了 [skills-best-practices](https://github.com/tong20242100/skills-best-practices) 中的 Agentic 交互规范，是该最佳实践在 Agent-Hub 项目中的本地化落地。

## 1. 非人化语气：第三人称命令式 (Third-Person Imperative)

**核心：不要把技能描述写成“给人的说明书”，而要写成“给机器的指令”。**

*   **禁止使用第一/二人称**：严禁出现 "I", "me", "my", "you", "your", "你", "我", "我们"。
*   **使用动词开头**：描述应以“提供...能力”、“用于...”、“执行...”开头。
    *   ❌ *错误例*："我可以帮你搜索网页，如果你需要最新消息请找我。"
    *   ✅ *正确例*："执行全网搜索，获取最新网页信息及结构化摘要。"
*   **作用**：减少 AI 在处理 RAG 时的冗余干扰，提高触发权重（Triggers）的敏感度。

## 2. 自检机制 (The Self-Check Mechanism)

**核心：每个工具在调用前，必须强制 AI 进行“能力边界”自我评估。**

在 `SCHEMA.json` 的 `ai_hints` 中必须包含 `self_check` 列表，引导 AI 优先使用原生能力：
*   **逻辑**：
    1.  如果 AI 自身拥有原生搜索能力，则跳过 `web_search` 工具。
    2.  如果 AI 需要结构化数据或自身能力受限（如知识库过期），则调用工具。
*   **模板**：
    ```json
    "self_check": [
      "环境是否支持原生渲染？支持 -> 优先用原生的",
      "目标是否为简单静态页？是 -> 优先用 scrape_url"
    ]
    ```

## 3. 渐进式披露 (Progressive Disclosure)

**核心：保持提示词（Prompt）精简，将复杂性转移到物理文件。**

*   **主逻辑精简**：`SKILL.md` 指令文件建议控制在 500 行以内。
*   **外挂资源**：
    *   `references/`：存放复杂的配置映射、错误代码表。
    *   `assets/`：存放输出模板、JSON 示例。
*   **调用逻辑**：只有当 AI 逻辑运行到特定分支时，才发出指令让 AI 调用 `read_file` 工具去读取物理文件。
*   **原则**：**不要在初次加载时把所有细节塞给 AI，要让 AI 在需要时自己去“看”证据。**

## 4. 物理路径硬化 (Physical Path Hardening)

**核心：技能必须是“绿色便携”的。**

*   **路径解析**：所有 `bin/` 下的脚本必须能够通过 `SCRIPT_DIR` 自定位。
*   **零耦合**：技能不应依赖全局环境变量，所有依赖项（如 `mcp` 库、`pip` 包）必须在 `SCHEMA.json` 的 `dependencies` 字段中声明。

## 5. 纯净技能域 (Noise Reduction)

**核心：技能目录是给 Agent 读的，不是给人看的。**

*   **禁止 human-centric 文档**：在 `skills/<name>/` 目录下，严禁出现 `README.md`, `INSTALLATION.md` 或 `CHANGELOG.md`。
*   **文档去向**：所有的项目级说明应统一放在项目根目录的 `docs/` 下。

---

*最后更新：2026-04-15*
*遵循规范：Agent-Hub v1.0 Standard*
*参考来源：[skills-best-practices](https://github.com/tong20242100/skills-best-practices)*
