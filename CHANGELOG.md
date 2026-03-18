# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open source release
- Semantic Router with rule-based and vector semantic matching
- 10 cognitive personas (Deep Researcher, AI Engineer, Viral Writer, etc.)
- 32 skills (23 tool-type + 9 cognitive-type)
- Cross-tool memory system with ChromaDB
- Hardened execution kernel with injection prevention
- MCP protocol support for Chrome DevTools

### Infrastructure
- `pyproject.toml` for pip install support
- Global CLI commands: `ah` and `nexus`
- Optional ML dependencies: `pip install -e ".[ml]"`
- MIT License
- Bilingual README (English/Chinese)
- Setup script (`setup.sh`)
- CI/CD with GitHub Actions
- Issue templates for bugs, features, and skill requests
- Contributing guidelines

## [0.1.0] - 2026-03-18

### Initial Release
- Project foundation
- Core semantic routing capability
- Tool execution framework
- Memory and vector storage
