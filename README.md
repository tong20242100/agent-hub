<div align="center">

# Agent-Hub

**Write JSON, not glue code.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

**[English](README.md)** • **[中文](README_CN.md)**

</div>

---

Turn any CLI tool into an AI skill with one JSON file. No Python wrappers, no glue code.

**The problems you're facing:**

| Problem | What happens | Agent-Hub solution |
|---------|--------------|-------------------|
| **Tool discovery hell** | 100 scripts, AI doesn't know which one to use | Semantic router: natural language → right tool in <10ms |
| **Client fragmentation** | Cursor plugin ≠ Gemini skill ≠ Claude tool | One skill repo, all clients share |
| **Cross-client amnesia** | Yesterday's research in Gemini? Claude doesn't know | Unified memory layer (knowledge/vector_store.py) |
| **Lifecycle chaos** | GitHub/npm/pip/brew — different update flows | Unified package manager (apt/brew for AI skills) |

**The hidden power:** `skill_update_check` auto-detects version changes across GitHub Releases, npm, pip, and Homebrew — like `apt` or `brew`, but for AI skills.

---

## Quick Start

```bash
# Install
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .

# Or with ML features (semantic search, memory)
pip install -e ".[ml]"

# Try it
ah "search AI Agent news"
# → Routes to: web_search | Args: {"query": "AI Agent news", "limit": 10}

ah "scrape https://example.com"
# → Routes to: scrape_url | Args: {"url": "https://example.com"}

ah --stats
# → 📊 路由器统计: 工具数: 90, 人格数: 9
```

---

## Core Innovation: Conditional Syntax

One line of JSON replaces 10 lines of Python.

**Before (glue code):**
```python
def call_scrape(url, recursive=False, depth=2):
    cmd = ["./bin/scrape", url]
    if recursive:
        cmd.append("--recursive")
    if depth != 2:
        cmd.extend(["--depth", str(depth)])
    return subprocess.run(cmd, capture_output=True)
```

**After (Agent-Hub):**
```json
{
  "command": "bin/scrape {url} {recursive?--recursive} {depth?--depth {depth}}"
}
```

| Syntax | Meaning |
|--------|---------|
| `{param}` | Required parameter |
| `{param?--flag}` | Boolean: add flag if true |
| `{param?--opt {param}}` | Optional with value |

---

## How It Works

### Three-Level Progressive Loading

| Level | What loads | Token cost | When |
|-------|------------|------------|------|
| **L1** | Tool manifest (name + description + ai_hints) | ~2K | Router startup |
| **L2** | Matched SCHEMA.json (full parameters) | ~500 | After routing |
| **L3** | SKILL.md (detailed guidance, optional) | ~1K | Before execution |

**Result:** Fast startup, minimal context waste.

### Gate Checks

Before execution, `requires` field is validated:

```json
{
  "requires": {
    "bins": ["gh", "yt-dlp"],      // Must exist in PATH
    "env": ["GITHUB_TOKEN"]        // Must be set in environment
  }
}
```

Missing dependency? Clear error message, no silent failures.

### AI Native Fields

Every tool includes `ai_hints` — guidance for AI agents:

```json
{
  "ai_hints": {
    "when_to_use": "When user asks about GitHub repo info",
    "examples": [{"repo": "owner/repo"}],
    "avoid": "Don't use full URLs, use owner/repo format"
  }
}
```

AI reads this and knows exactly how to use the tool. No guessing.

---

## Key Features

- **Sub-100ms response** — Regex short-circuit + lazy loading + cached embeddings
- **Security by design** — Schema type enforcement, shlex sanitization, requires gate checks
- **Built-in package manager** — Auto-detect updates from GitHub Releases, npm, pip, Homebrew

```bash
python3 bin/skill_update_check        # Check for updates
python3 bin/skill_update_install      # Interactive install
python3 bin/skill_update_install --all
```

---

## Client Integration

### CLI (Gemini CLI, Claude Code, iFlow CLI)

After `pip install -e .`, use globally:
```bash
ah "search for AI Agent news"
nexus "scrape https://example.com"
```

### Claude Desktop / Cursor (via MCP)

Add to your MCP config:

```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/absolute/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

> Replace `/absolute/path/to` with your actual installation path.

### Python Module

```python
from bin.semantic_router import SemanticRouter

router = SemanticRouter()
match = router.route("search for AI news")
if match:
    print(match.tool_name, match.extracted_args)
```

---

## Add Your Own Skill

Create `skills/your-skill/SCHEMA.json`:

```json
{
  "name": "your-skill",
  "tools": {
    "your_tool": {
      "description": "What it does",
      "command": "your-binary {input} {verbose?--verbose}",
      "parameters": {
        "type": "object",
        "properties": {
          "input": {"type": "string", "description": "Input"},
          "verbose": {"type": "boolean", "default": false}
        },
        "required": ["input"]
      },
      "ai_hints": {
        "when_to_use": "When user needs to...",
        "examples": [{"input": "example"}]
      }
    }
  },
  "requires": {
    "bins": ["your-binary"],
    "env": ["OPTIONAL_API_KEY"]
  }
}
```

No Python required. See [CONTRIBUTING.md](CONTRIBUTING.md) for full syntax.

---

## Project Structure

```
skills/
├── agency-bin-search/     # Web search (SCHEMA.json)
├── agency-bin-scrape/     # Web scraping (SCHEMA.json)
├── agency-architecture-atlas/  # AI architecture knowledge (SCHEMA + SKILL.md)
├── agency-skill-armorer/  # Skill creation helper (SCHEMA + SKILL.md)
└── ...

bin/
├── semantic_router.py     # Intent → Tool mapping
├── mcp_server.py          # MCP protocol server
├── search                 # Web search wrapper (Tavily)
├── skill_update_check     # Package update checker
├── skill_update_install   # Package installer
└── kernel/
    └── nexus_executor.py  # Safe command execution

knowledge/
└── vector_store.py        # Cross-client memory (ChromaDB)
```

---

## Available Skills

| Skill | Type | Description |
|-------|------|-------------|
| `agency-bin-search` | Tool | Web search via Tavily API |
| `agency-bin-scrape` | Tool | Web scraping via Jina Reader |
| `agency-architecture-atlas` | Cognitive | AI Agent architecture knowledge base |
| `agency-skill-armorer` | Cognitive | Skill creation and schema generator |

---

## Optional Dependencies

Unlock advanced skills with these optional tools:

### CLI Tools

| Tool | Install | Enables |
|------|---------|---------|
| **GitHub CLI** | `brew install gh` | `gh_view`, `analyze_repo`, `verify` |
| **yt-dlp** | `brew install yt-dlp` | Video/audio extraction from YouTube, Bilibili, etc. |
| **Node.js** | `brew install node` | Browser automation (Chrome DevTools, BB Browser) |
| **scrapling** | `pip install scrapling` | Stealth web scraping (anti-bot bypass) |
| **OpenCLI** | `pip install opencli` | Generic CLI interface |

### Environment Variables

| Variable | Get from | Enables |
|----------|----------|---------|
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) | Web search (`web_search`) |
| `NVIDIA_API_KEY` | [NVIDIA](https://build.nvidia.com) | GPU optimization tools |

### Quick Install (macOS)

```bash
# Core tools
brew install gh node yt-dlp

# Python packages for stealth scraping
pip install scrapling patchright playwright-stealth

# Environment variables (add to ~/.zshrc or ~/.bashrc)
export TAVILY_API_KEY="your-key-here"
```

### Quick Install (Linux)

```bash
# Core tools
sudo apt install gh nodejs yt-dlp
# or
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg

# Python packages
pip install scrapling patchright playwright-stealth
```

> **Note:** Windows users can use `winget` or `scoop` for CLI tools. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for design philosophy and full syntax reference.

If this saves you from writing glue code, give it a ⭐.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## License

MIT License - see [LICENSE](LICENSE) file.