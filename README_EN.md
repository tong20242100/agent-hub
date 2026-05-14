<div align="center">

# Agent-Hub

**Turn any CLI tool into an AI skill. Write JSON, not glue code.**

English | [中文](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org)

</div>

---

## What is This

Agent-Hub is a local **MCP skill gateway** that solves a concrete problem:

> You have a bunch of CLI tools (search, browser, GitHub, notifications…), but AI doesn't know they exist or when to use them.

Agent-Hub's approach: Write a `SCHEMA.json` for each tool declaring what it does, when to use it, and when not to. Once the MCP Server starts, AI can route autonomously without you manually specifying tools each time.

```
You say: "Research this GitHub repo for me"
AI decides on its own: call gh_view → call web_search → call cross-verify
No need to tell it which tool to use
```

---

## Three-Layer Architecture

The project separates AI capabilities into three independent layers:

| Layer | Type | Count | Role |
|---|---|---|---|
| ⚙️ **Tool** | MCP Execution Tools | 33 | Execute physical operations: search, browser, scraping, notifications… |
| 🧠 **Cognitive** | Cognitive Protocols | 11 | Inject thinking frameworks: architect, growth hacker, reality checker… |
| 📖 **Knowledge** | External Knowledge Docs | 13 | On-demand authority injection: Google WAF, Gemini API… |

**Tool** is the hand, responsible for execution. **Cognitive** is the brain, responsible for decision frameworks. **Knowledge** is the eye, responsible for external standards. All three are decoupled and can be updated independently.

---

## Core Tools Overview

| Scenario | Tool | Description |
|---|---|---|
| Web Search | `web_search` | Tavily protocol, returns structured summaries |
| Browser Automation | `chrome-devtools` | 29 operations: click, screenshot, audit |
| Anti-Scraping | `scrapling-stealth` | Bypass Cloudflare |
| X/Twitter | `xreach` | Search tweets |
| Xiaohongshu | `xiaohongshu-mcp` | QR code login, search notes |
| GitHub Deep Analysis | `gh_view`, `analyze_repo` | Repository structure and code logic |
| Media Extraction | `media-extract` | YouTube/Bilibili subtitles and metadata |
| Hallucination Verification | `cross-verify` | Force-scan knowledge base to verify claims |
| Notifications | `notify` | Feishu / Bark |
| Long-term Memory | `memory` | Vector semantic search knowledge base |

---

## `ai_hints`: The Key to AI Self-Routing

Each tool's `SCHEMA.json` contains an `ai_hints` field—the core mechanism of the entire system:

```json
{
  "ai_hints": {
    "intent": "Collect structured real-time internet evidence via Tavily protocol",
    "when_to_use": "When verifying time-sensitive facts or obtaining raw URL collections",
    "avoid": [
      "Known URLs (use scrape_url)",
      "Local knowledge base queries (use memory_query)",
      "Deep X/Twitter retrieval (use xreach)"
    ],
    "self_check": [
      "Does the task involve verifying current facts?",
      "Do you need structured data with original sources?"
    ]
  }
}
```

When AI reads this description, it knows: when to use this tool, when not to use it, and what to self-check before calling. No need to repeatedly explain in your Prompt.

---

## `ah` CLI: Full Skill Lifecycle Management

```bash
ah list              # View all registered skills (⚙️/🧠/📖 categorized)
ah onboard <path>    # Onboard new skill: register + sync manifest + clean cache
ah check             # Compliance audit: naming, tone, hint quality, dependencies
ah eval              # Hint quality stress test: detect semantic conflicts
ah discover          # Global discovery: scan Claude/Cursor/Gemini/Kiro existing skills
ah link              # Sync cognitive protocols to ~/.agents/skills/ for cross-platform use
ah analyze           # Log diagnostics: failure rates, burst calls, never-called tools
ah update            # Detect and update all skills
```

`ah analyze` is the system's self-diagnosis entry point, reading execution logs and outputting:

```
✅ System Health: 92%  (11/12 calls healthy) | Registered Tools: 103

🔴 Tool Failure Report:
  • 🔴 HIGH  read_elite_prompt  failure rate 100%

🚫 Never-Called Tools (recommend review):
  • take_snapshot / memory_save / ...
```

---

## Quick Start

```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

**Start MCP Server (integrate with Claude/Cursor/Kiro):**

```bash
python3 bin/mcp_server.py
```

Point your AI client's MCP configuration to this process, and all skills become immediately available.

**View currently ready capabilities:**

```bash
ah list
```

**Sync cognitive protocols to global storage (let Claude Code / Gemini CLI auto-discover):**

```bash
ah link
```

---

## Execution Traceability

Every tool invocation writes to `knowledge/logs/evolution_*.jsonl`:

```json
{
  "tool": "web_search",
  "duration_ms": 2969,
  "status": "success",
  "audit": { "ok": true },
  "command_run": "/Users/.../bin/search 'CEFR graded sentences dataset'",
  "output_preview": { "stdout": "🔍 Search results..." }
}
```

Includes full command snapshots, exit codes, output purity checks, and execution duration. `ah analyze` reads these logs for system diagnostics.

---

## Design Principles

- **AI Self-Routing**: Tools self-describe via `ai_hints`, AI decides what to call without manual specification
- **Single Source of Truth**: `knowledge/tools_manifest.json` is the only registry for all tools, automatically maintained by `ah onboard/remove`
- **Hand-Brain Separation**: Execution tools (Tool) and thinking frameworks (Cognitive) are decoupled and independent
- **No Nested Agents in Tools**: Tools perform only atomic operations, never secretly call LLM for secondary decisions

---

## License

MIT
