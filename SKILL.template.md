# Skill: [Skill Name]

## 1. 核心使命 (Mission)
[简述该技能解决的核心问题，以及它在 Agent-Hub 生态中的唯一地位。]

## 2. 决策树 (Decision Tree)
引导 AI 在不同分支下做出决定：
- **场景 A**：[条件] -> 执行 [动作]
- **场景 B**：[条件] -> 调用外部工具 [名称]
- **降级方案**：如果 [异常] 发生 -> 执行 [补救措施]

## 3. 物理调查指南 (Investigation)
指导 AI 读取关联文件：
- 复杂映射表：读取 `references/mapping.json`
- 输出模板：读取 `assets/template.md`

## 4. 自卫检查 (Resilience)
- **频率限制处理**：[具体策略]
- **内容截断处理**：[具体策略]
- **错误排查**：查询 `references/errors.md` 中的错误代码定义。
