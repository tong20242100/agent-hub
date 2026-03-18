# Contributing to Nexus Agentic OS

Thank you for your interest in contributing to Nexus Agentic OS! This document provides guidelines and instructions for contributing.

## 🚀 Quick Start

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/agent-hub.git`
3. Install dependencies: `./setup.sh`
4. Create a branch: `git checkout -b feature/your-feature`
5. Make your changes and commit
6. Push and create a Pull Request

## 🧠 The Nexus Philosophy (Read Before Coding)

Nexus Agentic OS is built on a very specific set of principles. Before you submit a Pull Request, please ensure your contribution aligns with these maxims:

1. **Schema-Driven over Hardcoded**: Avoid writing Python `if/else` wrappers for tool parameters. If a tool has 20 flags, map them using the `{param?--flag}` Conditional Syntax in `SCHEMA.json`. Let the data structure dictate the physical execution.
2. **Skill Equals Binary (Decoupled Logic)**: Do not stuff heavy business logic, complex integrations, or long-running state management into Python scripts inside the hub. Write powerful standalone binaries (in Go, Rust, Node, etc.) and let `agent-hub` simply orchestrate them via a standardized schema.
3. **Millisecond Obsession**: Do not add heavy imports (`torch`, `transformers`, large datasets) at the global level of executable scripts. Everything expensive must be **lazy-loaded** to preserve the `<160ms` short-circuit routing performance of the OS kernel.

---

## 📝 Contribution Guidelines

### Reporting Bugs

- Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md)
- Include steps to reproduce
- Include your environment details (OS, Python version)
- Include error messages and logs

### Suggesting Features

- Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md)
- Describe the use case
- Explain why existing solutions don't work
- Be open to discussion

### Adding New Skills

Skills are the core extension mechanism of Nexus. To add a new skill:

1. Create a new directory under `skills/agency-YOUR-SKILL-NAME/`
2. Add a `SCHEMA.json` defining the skill's tools and parameters
3. (Optional) Add a `SKILL.md` with cognitive guidance for AI agents
4. If your skill has binaries, place them in `skills/agency-YOUR-SKILL-NAME/bin/`
5. Update `knowledge/tools_manifest.json` via `python3 scripts/generate_tools_manifest.py`
6. Test your skill thoroughly

#### Skill Schema Example

```json
{
  "name": "agency-bin-my-tool",
  "version": "1.0.0",
  "protocol": "nexus-2.0",
  "description": "Brief description of what your tool does",
  "tools": {
    "my_command": {
      "description": "What this command does",
      "command": "my-binary {parameter}",
      "parameters": {
        "type": "object",
        "properties": {
          "parameter": {
            "type": "string",
            "description": "Parameter description"
          }
        },
        "required": ["parameter"]
      }
    }
  },
  "requires": {
    "bins": ["my-binary"],
    "env": ["OPTIONAL_ENV_VAR"]
  }
}
```

#### Command Template Syntax

The `command` field in SCHEMA.json supports special syntax for handling optional parameters:

**1. Required Parameters: `{param}`**

Simple placeholder replacement. The value is automatically quoted for shell safety.

```json
"command": "my-tool {url}"
// Input: {"url": "https://example.com"}
// Output: my-tool 'https://example.com'
```

**2. Boolean Flags: `{param?--flag}`**

Adds `--flag` only when the parameter is truthy.

```json
"command": "my-tool {url} {verbose?--verbose}"
// Input: {"url": "https://example.com", "verbose": true}
// Output: my-tool 'https://example.com' --verbose

// Input: {"url": "https://example.com", "verbose": false}
// Output: my-tool 'https://example.com'
```

**3. Optional Values: `--option {param}`**

The entire `--option value` pair is included only when the parameter exists.

```json
"command": "my-tool {url} --depth {depth}"
// Input: {"url": "https://example.com", "depth": 3}
// Output: my-tool 'https://example.com' --depth 3

// Input: {"url": "https://example.com"}
// Output: my-tool 'https://example.com'
// (--depth is omitted entirely)
```

**4. Combined Example:**

```json
{
  "command": "scrape {url} {recursive?--recursive} --depth {depth}",
  "parameters": {
    "properties": {
      "url": {"type": "string"},
      "recursive": {"type": "boolean", "default": false},
      "depth": {"type": "integer", "default": 2}
    },
    "required": ["url"]
  }
}
```

```bash
# Input: {"url": "https://example.com"}
# Output: scrape 'https://example.com'

# Input: {"url": "https://example.com", "recursive": true, "depth": 5}
# Output: scrape 'https://example.com' --recursive --depth 5
```

**Important:** All values are automatically escaped with `shlex.quote()` for security. Never manually quote parameters in the template.

### Code Style

- Python: Follow PEP 8
- Use type hints where appropriate
- Add docstrings for public functions
- Keep functions focused and small

### Testing

- Add tests for new functionality in `scripts/tests/`
- Ensure existing tests pass: `python3 -m pytest scripts/tests/`
- Test your changes manually before submitting

## 🏗️ Architecture Overview

```
Nexus Agentic OS
├── bin/                    # Executable entry points
│   ├── semantic_router.py  # Core routing logic
│   ├── commander.py        # Persona-based orchestration
│   └── ...
├── skills/                 # Skill modules
│   ├── agency-bin-*/       # Tool-type skills
│   └── agency-*/           # Cognitive-type skills
├── knowledge/              # Vector store and memory
├── scripts/                # Utility scripts
└── config/                 # Configuration files
```

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 💬 Questions?

- Open an issue with the `question` label
- Join our community discussions

Thank you for contributing! 🎉
