# Agent-Hub — AI Native Skills System

> Turn any CLI tool into an AI skill with one JSON file.

---

## Quick Reference

### Intent-Driven (Recommended)

```bash
python3 bin/semantic_router.py "search AI Agent news"
python3 bin/semantic_router.py "scrape https://example.com"
```

### Precise Call (Advanced)

```bash
python3 bin/kernel/nexus_executor.py --skill <SKILL> --tool <TOOL> --args '{"key": "value"}'
```

---

## Architecture

### Three-Level Progressive Loading

| Level | What loads | Token cost | When |
|-------|------------|------------|------|
| **L1** | Tool manifest (name + description + ai_hints) | ~2K | Router startup |
| **L2** | Matched SCHEMA.json (full parameters) | ~500 | After routing |
| **L3** | SKILL.md (detailed guidance, optional) | ~1K | Before execution |

### Gate Checks

Before execution, `requires` field is validated:

```json
{
  "requires": {
    "bins": ["gh"],           // Must exist in PATH
    "env": ["GITHUB_TOKEN"]   // Must be set
  }
}
```

### AI Native Fields

Every tool includes `ai_hints` for AI guidance:

```json
{
  "ai_hints": {
    "when_to_use": "When user needs to search the web",
    "examples": [{"query": "AI news", "limit": 10}],
    "avoid": "Don't use for GitHub-specific searches"
  }
}
```

---

## Tool Selection

### Web Search

```
Web Search
└─ web_search (Tavily API) ← AI-powered search with summarization
```

### Web Scraping

```
Web Scraping
└─ scrape_url (Jina Reader) ← Clean markdown extraction
```

### GitHub Operations

Use your native API (`read_file`, `search_file_content`, `web_fetch`) for GitHub operations. For advanced needs, extend with custom skills.

### Local Knowledge

```
Local Knowledge
└─ vector_store (ChromaDB) ← Semantic search over stored documents
```

---

## Evidence Levels

All research outputs should be annotated with evidence level:

- **L1 Verified**: Official docs / source code / execution logs
- **L2 Consensus**: 3+ independent professional sources
- **L3 Inferred**: Logical deduction from verified facts
- **L4 Hypothesis**: Unverified guesses, must note "needs validation"

---

## Extending Agent-Hub

### Add a New Skill

1. Create `skills/your-skill/SCHEMA.json`
2. Define tools with `ai_hints` and `requires`
3. Run `python3 scripts/generate_tools_manifest.py`

See [CONTRIBUTING.md](CONTRIBUTING.md) for full syntax.

### Example SCHEMA.json

```json
{
  "name": "my-tool",
  "version": "1.0.0",
  "protocol": "nexus-2.0",
  "tools": {
    "my_search": {
      "description": "Search my custom database",
      "command": "bin/my_search {query} {limit?--limit {limit}}",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "Search query"},
          "limit": {"type": "integer", "default": 10}
        },
        "required": ["query"]
      },
      "ai_hints": {
        "when_to_use": "When user needs to search my database",
        "examples": [{"query": "example"}]
      }
    }
  },
  "requires": {
    "bins": ["my_search"],
    "env": ["MY_API_KEY"]
  }
}
```

---

## Core Components

| Component | File | Purpose |
|-----------|------|---------|
| Semantic Router | `bin/semantic_router.py` | Intent → Tool mapping |
| Hardened Kernel | `bin/kernel/nexus_executor.py` | Safe command execution |
| MCP Server | `bin/mcp_server.py` | MCP protocol support |
| Vector Memory | `knowledge/vector_store.py` | Cross-client knowledge |
| Package Manager | `bin/skill_update_*` | Skill lifecycle management |

---

## Open Source Skills

| Skill | Type | Description |
|-------|------|-------------|
| `agency-bin-search` | Tool | Web search via Tavily API |
| `agency-bin-scrape` | Tool | Web scraping via Jina Reader |
| `agency-architecture-atlas` | Cognitive | AI Agent architecture knowledge |
| `agency-skill-armorer` | Cognitive | Skill creation helper |

---

## Inspiration

This project draws from:

| Project | Borrowed Concepts |
|---------|------------------|
| **Claude Code** | Minimalism, permission system, CLAUDE.md memory |
| **Codex CLI** | Skills system, three-level loading, AGENTS.md |

---

*Agent-Hub — Write JSON, not glue code.*
