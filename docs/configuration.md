# Agent 配置参考

本文档列出所有主流 AI Agent 的 MCP 配置方法。

## 快速配置提示词

**直接把下面这段发给你的 AI Agent，让它自己配置：**

```
请帮我配置 Agent-Hub MCP 服务器。项目路径是 /path/to/agent-hub。

你需要：
1. 确定你是哪个 Agent（Claude Code、Gemini CLI、Cursor、Codex、OpenClaw、Hermes 等）
2. 找到你的配置文件路径
3. 添加 MCP 服务器配置

配置格式：
- JSON 格式（Claude、Gemini、Cursor、OpenClaw）：
  {"mcpServers": {"agent-hub": {"command": "python3", "args": ["/path/to/agent-hub/bin/mcp_server.py"]}}}
  
- TOML 格式（Codex）：
  [mcp_servers.agent-hub]
  command = "python3"
  args = ["/path/to/agent-hub/bin/mcp_server.py"]
  
- YAML 格式（Hermes）：
  mcp_servers:
    agent-hub:
      command: "python3"
      args: ["/path/to/agent-hub/bin/mcp_server.py"]

配置完成后，验证工具是否可用：帮我搜索 "MCP protocol"
```

---

## Claude Code CLI

**配置文件**：`~/.claude.json`（用户级）或 `.mcp.json`（项目级）

**命令行方式**：
```bash
claude mcp add-json agent-hub --scope user '{
  "command": "python3",
  "args": ["/path/to/agent-hub/bin/mcp_server.py"]
}'
```

**手动配置**：
```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

**验证**：
```bash
claude mcp list
```

---

## Claude Desktop

**配置文件**：`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

重启 Claude Desktop 生效。

---

## Gemini CLI

**配置文件**：`~/.gemini/settings.json`

```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

**验证**：
```
/mcp list
```

---

## Cursor

**配置文件**：`~/.cursor/mcp.json`（用户级）或 `.cursor/mcp.json`（项目级）

```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

---

## Codex CLI (OpenAI)

**配置文件**：`~/.codex/config.toml`（用户级）或 `.codex/config.toml`（项目级）

**注意**：Codex 使用 **TOML 格式**，不是 JSON。

```toml
[mcp_servers.agent-hub]
command = "python3"
args = ["/path/to/agent-hub/bin/mcp_server.py"]
```

---

## OpenClaw Agent

**配置文件**：`~/.openclaw/openclaw.json`

OpenClaw 也可以通过 **MCPorter** 连接 MCP 服务器：

**方法 1：MCPorter 命令**
```bash
mcporter config add agent-hub \
  --command "python3" \
  --args "/path/to/agent-hub/bin/mcp_server.py" \
  --scope home
```

**方法 2：手动配置**
```json
{
  "mcpServers": {
    "agent-hub": {
      "command": "python3",
      "args": ["/path/to/agent-hub/bin/mcp_server.py"]
    }
  }
}
```

**验证**：
```bash
mcporter list agent-hub --schema
```

---

## Hermes Agent

**配置文件**：`~/.hermes/config.yaml`

**注意**：Hermes 使用 **YAML 格式**，不是 JSON。

```yaml
mcp_servers:
  agent-hub:
    command: "python3"
    args: ["/path/to/agent-hub/bin/mcp_server.py"]
```

**验证**：
```
/reload-mcp
```

---

## 其他 Agent

只要支持 MCP 协议的 Agent，配置方式类似：

1. 找到配置文件路径
2. 添加 `mcpServers` 块
3. 重启 Agent

常见配置格式：
- **JSON**：Claude、Gemini、Cursor、OpenClaw
- **TOML**：Codex
- **YAML**：Hermes
