<div align="center">

# Agent-Hub

**Agent Skill Management Gateway & Execution Tracing System**

English | [中文](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Observability](https://img.shields.io/badge/Debug-Observability-blue.svg)](https://agent-hub.io)

</div>

---

## 🏛️ Positioning

**Agent-Hub** is a production-oriented tool gateway for AI Agents. It addresses "decision paralysis" and "debugging opacity" in complex toolchains through semantic aggregation, standardized lifecycle management, and execution tracing, significantly enhancing system reliability.

### Three Technical Pillars

1.  **Semantic Aggregation**: Clusters atomic APIs into high-level capability modules, reducing LLM decision pressure and eliminating redundant calls.
2.  **Unified Lifecycle**: Provides a standardized CLI (`ah`) for skill integration, global discovery, automated updates, and safe removal.
3.  **Execution Observability**: Records real-time snapshots of shell commands, multi-dimensional audit reports, and environment fingerprints for complete execution playback.

---

## 🚀 Key Engineering Features

### 1. Schema-Driven Plugin Architecture
Every skill self-describes via `SCHEMA.json`:
- **Boundary Awareness**: Uses `ai_hints` to define triggers, resource costs, and negative conditions.
- **Dynamic Merging**: Automatically aggregates complex operations via **Schema-Driven Merging** to stay within the 100-tool limit of MCP clients.
- **Path Discovery**: Supports `{skill_path}` placeholders for "plug-and-play" deployment without hardcoding absolute paths.

### 2. Standardized Management CLI
The `ah` tool transforms fragmented scripts into managed assets:
- `ah onboard <path>`: Standardized integration of new skill packages.
- `ah scan`: Automated global discovery and local capability indexing.
- `ah update -i`: Tracks GitHub/NPM releases to align skill versions.
- `ah remove <name>`: Clean physical uninstallation.

### 3. Execution Recorder (Black Box)
Provides a "diagnostic report" for every single tool call:
- **Command Snapshot**: Captures the exact shell command run in the background (including escaped parameters).
- **Multi-Dimensional Audit**: Records exit codes and output quality checks (length, error keyword matching).
- **Environment Context**: Logs OS version, Python environment, and execution latency.

---

## 📦 Built-in Capability Modules

| Module | Core Tool (MCP) | Engineering Value |
|--------|------|------|
| **Design Advisor** | `design_advisor` | Visual decision reference to enhance UI consistency. |
| **Browser Control** | `chrome_devtools` | **[Merged]** Orchestrates complex interactions (fill/click) reliably. |
| **Social Intelligence** | `x_twitter_ops` | **[Merged]** Structured extraction of X (Twitter) data chains. |
| **Code Auditing** | `analyze_repo` | Extracts source evidence from GitHub to reduce AI hallucinations. |
| **Presentation** | `huashu_design` | Automated generation of interactive prototypes and animations. |

---

## Quick Start

### 1. Installation
```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

### 2. Service Management
- `ah server`: Start the MCP Protocol Gateway.
- `ah scan`: Verify and view the currently indexed skills.

### 3. Development Tip
For vague tasks like design or research, leverage `design_advisor` for intent alignment and use `evolution_*.jsonl` logs for error diagnosis.

---

## 📜 License
MIT License. Designed with a data-driven and decoupled philosophy.
