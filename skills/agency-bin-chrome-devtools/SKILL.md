---
name: chrome-devtools
description: 控制 Chrome 浏览器。29 个工具：点击、填充、导航、截图、性能分析、Lighthouse 审计。通过 MCP 协议调用外部 chrome-devtools-mcp。
version: "0.20.0"
protocol: nexus-2.0
---

# Chrome DevTools — 浏览器控制

## 核心指令

通过 MCP 协议调用外部 `chrome-devtools-mcp` 服务器，控制用户已打开的 Chrome 浏览器。

## 连接前提

1. Chrome 必须运行且开启远程调试（`--remote-debugging-port=9222`）
2. Chrome 146+ 可使用 `--autoConnect` 自动连接
3. 验证连接：调用 `list_pages`

## 工具分组

按任务类型选择工具：

### 页面操作

| 工具 | 用途 | 示例 |
|------|------|------|
| `navigate_page` | 导航到 URL | `navigate_page url="https://example.com"` |
| `new_page` | 新建标签页 | `new_page` |
| `list_pages` | 列出所有页面 | `list_pages` |
| `select_page` | 切换页面 | `select_page page_id=1` |
| `close_page` | 关闭页面 | `close_page page_id=1` |
| `wait_for` | 等待元素 | `wait_for selector=".loaded"` |

### 输入操作

| 工具 | 用途 | 示例 |
|------|------|------|
| `click` | 点击元素 | `click selector="button#submit"` |
| `fill` | 填充输入框 | `fill selector="input[name=q]" value="hello"` |
| `fill_form` | 批量填充表单 | 见 SCHEMA.json |
| `type_text` | 逐字输入 | `type_text text="hello"` |
| `press_key` | 按键 | `press_key key="Enter"` |
| `hover` | 悬停 | `hover selector="a#menu"` |
| `drag` | 拖拽 | 见 SCHEMA.json |
| `upload_file` | 上传文件 | 见 SCHEMA.json |
| `handle_dialog` | 处理对话框 | 见 SCHEMA.json |

### 信息获取

| 工具 | 用途 | 示例 |
|------|------|------|
| `take_screenshot` | 截图 | `take_screenshot` |
| `evaluate_script` | 执行 JS | `evaluate_script script="document.title"` |
| `get_console_message` | 获取控制台消息 | 见 SCHEMA.json |
| `list_console_messages` | 列出所有控制台消息 | 见 SCHEMA.json |
| `take_snapshot` | 可访问性快照 | 见 SCHEMA.json |
| `list_network_requests` | 列出网络请求 | 见 SCHEMA.json |
| `get_network_request` | 获取请求详情 | 见 SCHEMA.json |

### 性能与审计

| 工具 | 用途 |
|------|------|
| `performance_start_trace` | 开始性能追踪 |
| `performance_stop_trace` | 停止并分析 |
| `performance_analyze_insight` | 分析洞察 |
| `take_memory_snapshot` | 内存快照 |
| `lighthouse_audit` | Lighthouse 审计 |

### 模拟

| 工具 | 用途 |
|------|------|
| `emulate` | 模拟设备 |
| `resize_page` | 调整视口大小 |

## 典型工作流

```
1. navigate_page url="https://example.com"
2. wait_for selector="body"
3. take_screenshot
4. click selector="button#login"
5. fill selector="input[name=username]" value="user"
6. fill selector="input[name=password]" value="pass"
7. press_key key="Enter"
8. wait_for selector=".dashboard"
9. take_screenshot
```

## 注意事项

- 选择器优先使用 CSS 选择器，其次使用可访问性树中的 role/name
- 每次操作后验证页面状态（截图或 `list_pages`）
- 网络请求需要 `list_network_requests` 先执行，再用 `get_network_request` 获取详情
