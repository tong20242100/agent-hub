<div align="center">

# Agent-Hub

**Agent Skill Gateway & Execution Observability System**

English | [中文](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)
[![Agent Skills](https://img.shields.io/badge/Standard-Agent%20Skills-orange.svg)](https://github.com/google/skills)
[![Observability](https://img.shields.io/badge/Debug-Observability-blue.svg)](https://agent-hub.io)

</div>

---

## 🏛️ Project Vision

**Agent-Hub** is a production-grade gateway for Agent skill orchestration. It deeply integrates with the **Agent Skills** open standard pioneered by Anthropic/Google, utilizing a "Separation of Hand and Brain" architecture to decouple **MCP execution tools** from **cognitive decision protocols**.

### Three Core Pillars

1.  **Global Skill Orchestration**: Unified management of local MCP tools (⚙️), built-in cognitive protocols (🧠), and external knowledge bases (📖).
2.  **Thought-Action Alignment**: Guiding Agent decision logic via cognitive protocols (e.g., Atlas Architect Protocol) and automatically aligning with Google WAF global best practices.
3.  **Full Traceability**: Recording shell instruction snapshots, multi-dimensional audit reports, and environment fingerprints for every tool invocation.

---

## 🚀 Core Engineering Features

### 1. Agent Skills Standard Integration
The project adopts the **Progressive Disclosure** architecture to significantly reduce model token consumption:
- **Name-Match Activation**: Only loads skill metadata (approx. 80-100 tokens) by default.
- **On-Demand Knowledge Injection**: Splits instructions between `SKILL.md` and `references/`, loading details only when required.

### 2. Standardized CLI Toolchain (`ah`)
Full lifecycle management via the `ah` command-line tool:
- `ah list`: **Panoramic View**. Uses icons to distinguish between Tools (⚙️), Cognitive Protocols (🧠), and Knowledge (📖).
- `ah discover`: **Radar Discovery**. Globally searches for Claude, Cursor, Gemini, and standard skills on your machine.
- `ah link`: **Global Sync**. One-click synchronization of local cognitive protocols to `~/.agents/skills/` for cross-platform availability.
- `ah check & eval`: **Quality Audit**. Stress-tests tool hints to eliminate semantic conflicts and hallucinations.

### 3. Execution Recorder
The generated `evolution_*.jsonl` logs include:
- **Instruction Snapshots**: Full absolute-path commands with parameter escaping.
- **Multi-Dimensional Audits**: Exit codes, output purity checks, system environment fingerprints, and duration.

---

## 📦 Skill Taxonomy

| Type | Representative Modules | Role |
|:---:|---|---|
| **⚙️ Tool** | `agency-bin-search`, `chrome-devtools` | **"Hand"**: Physical operations via MCP protocol |
| **🧠 Cognitive** | `agency-architecture-atlas`, `ai-engineer` | **"Brain"**: Guides Agent thinking patterns and engineering standards |
| **📖 Knowledge** | `google-cloud-waf`, `gemini-api` | **"Eye"**: authoritative knowledge and WAF compliance from Google |

---

## Quick Start

### 1. Environment Setup
```bash
git clone https://github.com/tong20242100/agent-hub.git
cd agent-hub
pip install -e .
```

### 2. Common Operations
- `ah list`: View all ready capabilities.
- `ah link`: Sync internal cognitive protocols to global storage for Claude/Gemini.
- `python3 bin/mcp_server.py`: Start the MCP service gateway in StdIO mode.

### 3. Google WAF Alignment
Internal cognitive protocols (like Atlas) explicitly reference Google's official WAF skills:
- Automatically aligns with **Security**, **Reliability**, and **Cost Optimization** standards during decision-making.

---

## 📜 License
MIT License. Built with an "AI-Native first" and "JSON, not glue code" philosophy.
