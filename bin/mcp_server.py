#!/usr/bin/env python3
"""
Agent-Hub MCP Server - Expose skills to Claude Desktop / Cursor

Usage:
    # Add to Claude Desktop config:
    {
      "mcpServers": {
        "agent-hub": {
          "command": "python3",
          "args": ["/path/to/agent-hub/bin/mcp_server.py"]
        }
      }
    }
"""
import json
import asyncio
import sys
from pathlib import Path
from typing import Any

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Local imports
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from bin.semantic_router import SemanticRouter

# Initialize
server = Server("agent-hub")
router = None


def get_router():
    """Lazy load router (avoid loading model on import)"""
    global router
    if router is None:
        router = SemanticRouter()
    return router


def load_tools_manifest() -> list[dict]:
    """Load tools from manifest (Level 1 - lightweight)"""
    manifest_path = WORKSPACE_ROOT / "knowledge" / "tools_manifest.json"
    if not manifest_path.exists():
        return []
    
    with open(manifest_path) as f:
        return json.load(f).get("tools", [])


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return all available tools to MCP client"""
    tools = []
    
    for tool_def in load_tools_manifest():
        # Build MCP Tool from schema
        tool = Tool(
            name=tool_def["tool_name"],
            description=tool_def.get("description", ""),
            inputSchema=tool_def.get("parameters", {
                "type": "object",
                "properties": {},
                "required": []
            })
        )
        tools.append(tool)
    
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a tool via semantic router"""
    try:
        r = get_router()
        
        # Route by tool name (direct match)
        match = r.route_by_tool_name(name, arguments)
        
        if not match:
            return [TextContent(
                type="text",
                text=f"Error: Tool '{name}' not found"
            )]
        
        # Execute
        from bin.semantic_router import execute_tool, check_requires
        
        # Check requires
        requires = match.tool_def.get("requires", {})
        if requires:
            satisfied, missing = check_requires(requires)
            if not satisfied:
                return [TextContent(
                    type="text",
                    text=f"Error: Missing dependencies: {', '.join(missing)}"
                )]
        
        # Run tool
        result = execute_tool(
            match.tool_def.get("skill_dir", ""),
            match.tool_name,
            match.extracted_args,
            match.tool_def
        )
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run MCP server over stdio"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
