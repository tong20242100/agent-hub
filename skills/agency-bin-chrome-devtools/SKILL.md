---
name: chrome-devtools
description: "Chrome DevTools MCP — Google 官方 MCP 服务器，让 AI Agent 控制和检查 Chrome 浏览器"
version: 0.20.0
author: ChromeDevTools (Google)
tags: [mcp, chrome, browser, devtools, automation, performance, debugging]
---

# Chrome DevTools MCP

> Google 官方 MCP 服务器，29,386 ⭐
> 让 AI Agent 控制和检查 Chrome 浏览器

## 安装

```bash
npm install -g chrome-devtools-mcp@latest
```

## MCP 配置

### 方式一：自动连接（推荐，Chrome 146+）

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--autoConnect"]
    }
  }
}
```

**前置条件：**
1. Chrome 146+
2. 打开 `chrome://inspect/#remote-debugging`，开启开关

### 方式二：手动连接（传统方式）

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--browser-url=http://127.0.0.1:9222"]
    }
  }
}
```

**前置条件：**
```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile
```

### 方式三：Headless 模式

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--headless", "--isolated"]
    }
  }
}
```

## 工具分类

### 输入自动化 (9 tools)
- `click` - 点击元素
- `drag` - 拖拽元素
- `fill` - 填充输入框
- `fill_form` - 批量填充表单
- `handle_dialog` - 处理对话框
- `hover` - 悬停
- `press_key` - 按键
- `type_text` - 输入文本
- `upload_file` - 上传文件

### 导航自动化 (6 tools)
- `close_page` - 关闭页面
- `list_pages` - 列出页面
- `navigate_page` - 导航
- `new_page` - 新建页面
- `select_page` - 选择页面
- `wait_for` - 等待条件

### 性能分析 (4 tools)
- `performance_start_trace` - 开始追踪
- `performance_stop_trace` - 停止追踪
- `performance_analyze_insight` - 分析洞察
- `take_memory_snapshot` - 内存快照

### 网络监控 (2 tools)
- `get_network_request` - 获取请求详情
- `list_network_requests` - 列出请求

### 调试 (6 tools)
- `evaluate_script` - 执行 JS
- `get_console_message` - 获取控制台消息
- `lighthouse_audit` - Lighthouse 审计
- `list_console_messages` - 列出控制台消息
- `take_screenshot` - 截图
- `take_snapshot` - 可访问性快照

### 模拟 (2 tools)
- `emulate` - 模拟设备
- `resize_page` - 调整大小

## 常用示例

```bash
# 列出所有标签页
list_pages

# 导航到网页
navigate_page url="https://example.com"

# 点击按钮
click selector="button#submit"

# 填充输入框
fill selector="input[name='q']" value="hello world"

# 截图
take_screenshot

# 执行 JavaScript
evaluate_script script="document.title"

# 等待元素出现
wait_for selector=".loaded"

# 性能分析
performance_start_trace
# ... 操作 ...
performance_stop_trace
performance_analyze_insight
```

## 配置选项

| 选项 | 说明 |
|---|---|
| `--autoConnect` | 自动连接当前 Chrome（Chrome 146+） |
| `--browser-url` | 连接指定 Chrome 实例 |
| `--headless` | 无头模式 |
| `--isolated` | 使用临时用户数据目录 |
| `--channel` | Chrome 通道（stable/beta/canary/dev） |
| `--viewport` | 初始视口大小（如 1280x720） |
| `--slim` | 精简模式（仅 3 个工具） |

## 与 chrome-cdp-skill 对比

| 维度 | chrome-cdp-skill | Chrome DevTools MCP |
|---|---|---|
| 作者 | 个人开发者 | **Google 官方** |
| Stars | 1,734 | **29,386** |
| 工具数 | 14 | **29** |
| 性能分析 | ❌ | ✅ |
| Lighthouse | ❌ | ✅ |
| Chrome 146+ 原生连接 | ❌ | ✅ (--autoConnect) |
| 弹窗问题 | Per-tab daemon 解决 | 官方原生解决 |
