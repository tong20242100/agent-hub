import os, json, yaml
from pathlib import Path
from typing import List, Dict, Any

class BaseScanner:
    def __init__(self, name: str):
        self.name = name

    def scan(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

class ClaudeScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        paths = [
            Path.home() / "Library/Application Support/Claude/config.json",
            Path.home() / "AppData/Roaming/Claude/config.json" # Windows 兼容
        ]
        for config_path in paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    return self._parse(config)
                except: continue
        return []

    def _parse(self, config):
        found = []
        servers = config.get("mcpServers", {})
        for name, info in servers.items():
            found.append({"name": name, "platform": "Claude", "command": info.get("command")})
        return found

class CursorScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        # Cursor 的 MCP 配置路径
        path = Path.home() / "Library/Application Support/Cursor/User/globalStorage/cursor-client/mcpServers.json"
        if not path.exists(): return []
        found = []
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            # Cursor 的结构通常是 {"mcpServers": {...}}
            servers = data.get("mcpServers", {})
            for name, info in servers.items():
                found.append({"name": name, "platform": "Cursor", "command": info.get("command")})
        except: pass
        return found

class GeminiScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".gemini/settings.json"
        if not path.exists(): return []
        found = []
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            servers = data.get("mcpServers", {})
            for name, info in servers.items():
                found.append({"name": name, "platform": "Gemini", "command": info.get("command")})
        except: pass
        return found

class HermesScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        path = Path.home() / ".hermes/config.yaml"
        if not path.exists(): return []
        found = []
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            servers = config.get("mcp_servers", {}) or config.get("mcpServers", {})
            for name, info in servers.items():
                found.append({"name": name, "platform": "Hermes", "command": info.get("command")})
        except: pass
        return found

class OpenClawScanner(BaseScanner):
    def scan(self) -> List[Dict[str, Any]]:
        # 探测 OpenClaw 常见配置路径
        path = Path.home() / ".openclaw/config.json"
        if not path.exists(): return []
        found = []
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            for name, info in data.get("mcp", {}).items():
                found.append({"name": name, "platform": "OpenClaw", "command": info.get("command")})
        except: pass
        return found

class LocalFileScanner(BaseScanner):
    def scan(self, search_path: Path) -> List[Dict[str, Any]]:
        found = []
        # 限制深度以防锁死
        for schema_path in search_path.glob("**/SCHEMA.json"):
            try:
                with open(schema_path, 'r') as f:
                    data = json.load(f)
                found.append({
                    "name": data.get("name", schema_path.parent.name),
                    "platform": "Local",
                    "path": str(schema_path.parent)
                })
            except: pass
        return found

def run_global_discovery():
    """全域雷达启动"""
    scanners = [
        ClaudeScanner("Claude"), 
        HermesScanner("Hermes"), 
        CursorScanner("Cursor"),
        GeminiScanner("Gemini"),
        OpenClawScanner("OpenClaw")
    ]
    results = {}
    for scanner in scanners:
        found = scanner.scan()
        if found:
            results[scanner.name] = found
    return results
