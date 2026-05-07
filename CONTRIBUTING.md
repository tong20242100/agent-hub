# Contributing to Agent-Hub

Thank you for your interest in contributing to Agent-Hub!

## 🚀 Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/agent-hub.git`
3. Install: `pip install -e .`
4. Create a branch: `git checkout -b feature/your-feature`
5. Make changes and commit
6. Push and create a Pull Request

## 🧠 Core Principles

See [docs/principles.md](docs/principles.md) for our AI-Native manifesto.

1. **Schema-Driven**: Avoid Python `if/else` wrappers. Define tools via `SCHEMA.json`.
2. **Brain First**: Design tools for AI to call, not for humans to type. Use precise `ai_hints`.
3. **Solidified Registry**: Every skill MUST be onboarded via `ah onboard`.

## 📝 Adding New Skills

1. Create directory: `skills/agency-YOUR-SKILL-NAME/`
2. Add `SCHEMA.json` (The Muscle) and `SKILL.md` (The Soul).
3. Place binaries in `skills/agency-YOUR-SKILL-NAME/bin/`.
4. **MANDATORY**: Run `python3 bin/ah.py onboard skills/agency-YOUR-SKILL-NAME` to register with the registry, sync docs, and refresh MCP cache.

### SCHEMA.json Example

```json
{
  "name": "agency-bin-my-tool",
  "version": "1.0.0",
  "description": "Brief description",
  "tools": {
    "my_command": {
      "description": "What this command does",
      "command": "bin/my-binary {url} {verbose?--verbose}",
      "parameters": {
        "type": "object",
        "properties": {
          "url": {"type": "string"},
          "verbose": {"type": "boolean", "default": false}
        },
        "required": ["url"]
      },
      "ai_hints": {
        "when_to_use": "When user needs to..."
      }
    }
  },
  "requires": {
    "bins": ["my-binary"]
  }
}
```

### Command Template Syntax

- **Required**: `{param}` — simple replacement
- **Boolean**: `{param?--flag}` — adds flag when true
- **Optional**: `--option {param}` — pair included only when param exists

All values are automatically escaped with `shlex.quote()` for security.

## 💬 Questions?

Open an issue with the `question` label.

Thank you for contributing! 🎉
