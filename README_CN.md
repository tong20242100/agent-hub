<div align="center">

# Agent-Hub

**写 JSON，不写胶水代码。**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

**[English](README.md)** • **[中文](README_CN.md)**

</div>

---

用一个 JSON 文件把任何 CLI 工具变成 AI 技能。无需 Python 封装，无需胶水代码。

**你面临的问题：**

| 问题 | 现象 | Agent-Hub 解决方案 |
|------|------|-------------------|
| **工具发现地狱** | 100 个脚本，AI 不知道该用哪个 | 语义路由：自然语言 → 正确工具 <10ms |
| **多客户端割裂** | Cursor 插件 ≠ Gemini 技能 ≠ Claude 工具 | 一个技能仓库，所有客户端共享 |
| **跨端失忆症** | 昨天在 Gemini 的研究，Claude 今天就忘了 | 统一记忆底座（knowledge/vector_store.py） |
| **生命周期混乱** | GitHub/npm/pip/brew 各有各的更新流程 | 统一包管理器（AI 技能界的 apt/brew） |

**隐藏能力：** `skill_update_check` 自动检测 GitHub Releases、npm、pip、Homebrew 的版本变化 —— 就像 `apt` 或 `brew`，但为 AI 技能而生。

---

## 快速开始

```bash
# 安装
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .

# 或安装 ML 功能（语义搜索、记忆）
pip install -e ".[ml]"

# 试试看
ah "搜索 AI Agent 新闻"
# → 路由到: web_search | 参数: {"query": "AI Agent 新闻", "limit": 10}

ah "抓取 https://example.com"
# → 路由到: scrape_url | 参数: {"url": "https://example.com"}

ah --stats
# → 📊 路由器统计: 工具数: 90, 人格数: 9
```

---

## 核心创新：条件参数语法

一行 JSON 替代十行 Python。

**之前（胶水代码）：**
```python
def call_scrape(url, recursive=False, depth=2):
    cmd = ["./bin/scrape", url]
    if recursive:
        cmd.append("--recursive")
    if depth != 2:
        cmd.extend(["--depth", str(depth)])
    return subprocess.run(cmd, capture_output=True)
```

**之后（Agent-Hub）：**
```json
{
  "command": "bin/scrape {url} {recursive?--recursive} {depth?--depth {depth}}"
}
```

| 语法 | 含义 |
|------|------|
| `{param}` | 必需参数 |
| `{param?--flag}` | 布尔：为真则添加 flag |
| `{param?--opt {param}}` | 可选值参数 |

---

## 工作原理

### 三级渐进式加载

| 层级 | 加载内容 | Token 消耗 | 时机 |
|------|----------|------------|------|
| **L1** | 工具清单（名称 + 描述 + ai_hints） | ~2K | 路由器启动 |
| **L2** | 匹配的 SCHEMA.json（完整参数） | ~500 | 路由匹配后 |
| **L3** | SKILL.md（详细指导，可选） | ~1K | 执行前 |

**结果：** 快速启动，最小化上下文浪费。

### 门控检查

执行前自动验证 `requires` 字段：

```json
{
  "requires": {
    "bins": ["gh", "yt-dlp"],      // 必须存在于 PATH
    "env": ["GITHUB_TOKEN"]        // 必须设置环境变量
  }
}
```

缺少依赖？清晰的错误提示，不会静默失败。

### AI Native 字段

每个工具都包含 `ai_hints` —— 给 AI Agent 的使用指南：

```json
{
  "ai_hints": {
    "when_to_use": "当用户询问 GitHub 仓库信息时",
    "examples": [{"repo": "owner/repo"}],
    "avoid": "不要使用完整 URL，使用 owner/repo 格式"
  }
}
```

AI 读完就知道怎么用，无需猜测。

---

## 核心特性

- **亚百毫秒响应** — 正则短路 + 延迟加载 + 缓存向量
- **安全设计** — Schema 类型校验、shlex 防注入、requires 门控检查
- **内置包管理器** — 自动检测 GitHub Releases、npm、pip、Homebrew 更新

```bash
python3 bin/skill_update_check        # 检测更新
python3 bin/skill_update_install      # 交互式安装
python3 bin/skill_update_install --all
```

---

## 客户端接入

### CLI（Gemini CLI、Claude Code、iFlow CLI）

安装后全局可用：
```bash
ah "搜索 AI Agent 新闻"
nexus "抓取 https://example.com"
```

### Claude Desktop / Cursor（通过 MCP）

添加到 MCP 配置：

```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/绝对路径/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

> 将 `/绝对路径/` 替换为你真实的安装路径。

### Python 模块

```python
from bin.semantic_router import SemanticRouter

router = SemanticRouter()
match = router.route("搜索 AI 新闻")
if match:
    print(match.tool_name, match.extracted_args)
```

---

## 添加自定义技能

创建 `skills/your-skill/SCHEMA.json`：

```json
{
  "name": "your-skill",
  "tools": {
    "your_tool": {
      "description": "工具描述",
      "command": "your-binary {input} {verbose?--verbose}",
      "parameters": {
        "type": "object",
        "properties": {
          "input": {"type": "string", "description": "输入"},
          "verbose": {"type": "boolean", "default": false}
        },
        "required": ["input"]
      },
      "ai_hints": {
        "when_to_use": "当用户需要...",
        "examples": [{"input": "示例"}]
      }
    }
  },
  "requires": {
    "bins": ["your-binary"],
    "env": ["OPTIONAL_API_KEY"]
  }
}
```

无需 Python。完整语法见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 项目结构

```
skills/
├── agency-bin-search/     # 网页搜索（SCHEMA.json）
├── agency-bin-scrape/     # 网页抓取（SCHEMA.json）
├── agency-architecture-atlas/  # AI 架构知识库（SCHEMA + SKILL.md）
├── agency-skill-armorer/  # 技能创建助手（SCHEMA + SKILL.md）
└── ...

bin/
├── semantic_router.py     # 意图 → 工具映射
├── mcp_server.py          # MCP 协议服务器
├── search                 # 网页搜索封包工具 (Tavily)
├── skill_update_check     # 包更新检测器
├── skill_update_install   # 包安装器
└── kernel/
    └── nexus_executor.py  # 安全命令执行

knowledge/
└── vector_store.py        # 跨客户端记忆（ChromaDB）
```

---

## 可用技能

| 技能 | 类型 | 描述 |
|------|------|------|
| `agency-bin-search` | 工具型 | Tavily API 网页搜索 |
| `agency-bin-scrape` | 工具型 | Jina Reader 网页抓取 |
| `agency-architecture-atlas` | 认知型 | AI Agent 架构知识库 |
| `agency-skill-armorer` | 认知型 | 技能创建和 Schema 生成器 |

---

## 可选依赖

安装以下工具解锁高级技能：

### CLI 工具

| 工具 | 安装方式 | 解锁功能 |
|------|----------|----------|
| **GitHub CLI** | `brew install gh` | `gh_view`、`analyze_repo`、`verify` |
| **yt-dlp** | `brew install yt-dlp` | YouTube、B站等视频/音频提取 |
| **Node.js** | `brew install node` | 浏览器自动化（Chrome DevTools、BB Browser） |
| **scrapling** | `pip install scrapling` | 隐身爬虫（绕过反爬检测） |
| **OpenCLI** | `pip install opencli` | 通用 CLI 接口 |

### 环境变量

| 变量 | 获取地址 | 解锁功能 |
|------|----------|----------|
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | 网页搜索 (`web_search`) |
| `NVIDIA_API_KEY` | [NVIDIA](https://build.nvidia.com) | GPU 优化工具 |

### macOS 快速安装

```bash
# 核心工具
brew install gh node yt-dlp

# Python 隐身爬虫包
pip install scrapling patchright playwright-stealth

# 环境变量（添加到 ~/.zshrc）
export TAVILY_API_KEY="your-key-here"
```

### Linux 快速安装

```bash
# 核心工具
sudo apt install gh nodejs yt-dlp

# 或使用 GitHub 官方源
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg

# Python 包
pip install scrapling patchright playwright-stealth
```

> **注意：** Windows 用户可使用 `winget` 或 `scoop` 安装 CLI 工具。

---

## 贡献

欢迎 PR。设计哲学和完整语法见 [CONTRIBUTING.md](CONTRIBUTING.md)。

如果帮你省去了写胶水代码的痛苦，给个 ⭐ 吧。

---

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史。

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。