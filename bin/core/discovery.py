import logging
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger("agent-hub.discovery")


class BaseScanner:
    def __init__(self, name: str):
        self.name = name

    def scan(self) -> List[Dict[str, Any]]:
        raise NotImplementedError


class ClaudeScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        paths = [
            Path.home() / "Library/Application Support/Claude/config.json",
            Path.home() / "AppData/Roaming/Claude/config.json",
        ]
        for config_path in paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)
                    return self._parse(config)
                except json.JSONDecodeError as e:
                    logger.warning("Malformed Claude config at %s: %s", config_path, e)
                except (OSError, PermissionError) as e:
                    logger.warning("Cannot read %s: %s", config_path, e)
                except Exception as e:
                    logger.warning("Unexpected error scanning Claude: %s", e)
        return []

    def _parse(self, config):
        found = []
        servers = config.get("mcpServers", {})
        for name, info in servers.items():
            found.append(
                {"name": name, "platform": "Claude", "command": info.get("command")}
            )
        return found


class CursorScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = (
            Path.home()
            / "Library/Application Support/Cursor/User/globalStorage/cursor-client/mcpServers.json"
        )
        if not path.exists():
            return []
        found = []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            for name, info in servers.items():
                found.append(
                    {"name": name, "platform": "Cursor", "command": info.get("command")}
                )
        except json.JSONDecodeError as e:
            logger.warning("Malformed Cursor MCP config at %s: %s", path, e)
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", path, e)
        except Exception as e:
            logger.warning("Unexpected error scanning Cursor: %s", e)
        return found


class GeminiScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".gemini/settings.json"
        if not path.exists():
            return []
        found = []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            for name, info in servers.items():
                found.append(
                    {"name": name, "platform": "Gemini", "command": info.get("command")}
                )
        except json.JSONDecodeError as e:
            logger.warning("Malformed Gemini config at %s: %s", path, e)
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", path, e)
        except Exception as e:
            logger.warning("Unexpected error scanning Gemini: %s", e)
        return found


class HermesScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".hermes/config.yaml"
        if not path.exists():
            return []
        found = []
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
            servers = config.get("mcp_servers", {}) or config.get("mcpServers", {})
            for name, info in servers.items():
                found.append(
                    {"name": name, "platform": "Hermes", "command": info.get("command")}
                )
        except json.JSONDecodeError as e:
            logger.warning("Malformed Hermes config at %s: %s", path, e)
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", path, e)
        except Exception as e:
            logger.warning("Unexpected error scanning Hermes: %s", e)
        return found


class OpenClawScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".openclaw/config.json"
        if not path.exists():
            return []
        found = []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            for name, info in data.get("mcp", {}).items():
                found.append(
                    {
                        "name": name,
                        "platform": "OpenClaw",
                        "command": info.get("command"),
                    }
                )
        except json.JSONDecodeError as e:
            logger.warning("Malformed OpenClaw config at %s: %s", path, e)
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", path, e)
        except Exception as e:
            logger.warning("Unexpected error scanning OpenClaw: %s", e)
        return found


class KiroScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".kiro" / "settings" / "mcp.json"
        if not path.exists():
            return []
        found = []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            for name, info in servers.items():
                found.append(
                    {"name": name, "platform": "Kiro", "command": info.get("command")}
                )
        except json.JSONDecodeError as e:
            logger.warning("Malformed Kiro MCP config at %s: %s", path, e)
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", path, e)
        except Exception as e:
            logger.warning("Unexpected error scanning Kiro: %s", e)
        return found


class WindsurfScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
        if not path.exists():
            return []
        found = []
        try:
            with open(path, "r") as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            for name, info in servers.items():
                found.append(
                    {
                        "name": name,
                        "platform": "Windsurf",
                        "command": info.get("command"),
                    }
                )
        except json.JSONDecodeError as e:
            logger.warning("Malformed Windsurf MCP config at %s: %s", path, e)
        except (OSError, PermissionError) as e:
            logger.warning("Cannot read %s: %s", path, e)
        except Exception as e:
            logger.warning("Unexpected error scanning Windsurf: %s", e)
        return found


class LocalFileScanner(BaseScanner):
    def scan(self, search_path: Path) -> List[Dict[str, Any]]:
        found = []
        for schema_path in search_path.glob("**/SCHEMA.json"):
            try:
                with open(schema_path, "r") as f:
                    data = json.load(f)
                found.append(
                    {
                        "name": data.get("name", schema_path.parent.name),
                        "platform": "Local",
                        "path": str(schema_path.parent),
                    }
                )
            except json.JSONDecodeError as e:
                logger.warning("Malformed SCHEMA.json at %s: %s", schema_path, e)
            except (OSError, PermissionError) as e:
                logger.warning("Cannot read %s: %s", schema_path, e)
            except Exception as e:
                logger.warning(
                    "Unexpected error scanning local file %s: %s", schema_path, e
                )
        return found


class AgentSkillsScanner(BaseScanner):
    """扫描 ~/.agents/skills/ 下的 Anthropic/Google 格式技能"""

    def scan(self) -> List[Dict[str, Any]]:
        base = Path.home() / ".agents" / "skills"
        if not base.exists():
            return []
        found = []
        for skill_file in base.rglob("SKILL.md"):
            try:
                content = skill_file.read_text()
                name = skill_file.parent.name
                if "name:" in content:
                    import re

                    match = re.search(r"name:\s*(.*)", content)
                    if match:
                        name = match.group(1).strip()
                found.append(
                    {
                        "name": name,
                        "platform": "AgentSkills",
                        "path": str(skill_file.parent),
                        "type": "knowledge",
                    }
                )
            except (OSError, PermissionError) as e:
                logger.warning("Cannot read %s: %s", skill_file, e)
            except Exception as e:
                logger.warning("Unexpected error scanning %s: %s", skill_file, e)
        return found


def run_global_discovery():
    """全域雷达启动"""
    scanners = [
        ClaudeScanner("Claude"),
        HermesScanner("Hermes"),
        CursorScanner("Cursor"),
        GeminiScanner("Gemini"),
        OpenClawScanner("OpenClaw"),
        KiroScanner("Kiro"),
        WindsurfScanner("Windsurf"),
        AgentSkillsScanner("AgentSkills"),
    ]
    results = {}
    for scanner in scanners:
        found = scanner.scan()
        if found:
            results[scanner.name] = found
    return results
