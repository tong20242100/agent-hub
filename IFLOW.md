请强制阅读本项目的 `NEXUS.md` 作为你的操作系统核心法典。它是你的认知基础。

**🚀 意图驱动调用（推荐）**
```bash
python3 bin/semantic_router.py "搜索 X 关于 AI Agent"
python3 bin/semantic_router.py "查看 GitHub 仓库 owner/repo"
python3 bin/semantic_router.py "隐身抓取小红书页面"
```

**🔧 精确调用（高级）**
```bash
python3 bin/kernel/nexus_executor.py --skill <SKILL> --tool <TOOL> --args '{"key": "value"}'
```

**行动指南**：
1. 执行研究必须遵守 `NEXUS.md` 的【证据等级 L1-L4】
2. 使用 `ai_hints` 字段了解工具的正确用法
3. 注意 `requires` 门控检查，确保依赖可用