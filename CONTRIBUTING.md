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

1. **Schema-Driven**: Avoid Python `if/else` wrappers. Define tools via `SCHEMA.json` with `{param?--flag}` conditional syntax.
2. **Skill Equals Binary**: Write standalone binaries (Go, Rust, Node, etc.). Agent-Hub orchestrates them via standardized schema.
3. **Fast Execution**: Never add heavy imports (`torch`, `transformers`) at global level. Everything must be lazy-loaded.

## 📝 Adding New Skills

1. Create directory: `skills/agency-YOUR-SKILL-NAME/`
2. Add `SCHEMA.json` with tool definitions
3. (Optional) Add `SKILL.md` with AI guidance
4. If your skill has binaries, place in `skills/agency-YOUR-SKILL-NAME/bin/`

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
