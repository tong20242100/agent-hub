---
name: ljg-card
description: 内容铸卡。将内容转为 PNG 视觉卡片。六种模具：长图、信息图、多卡、视觉笔记、漫画、白板。输出到 ~/Downloads/。触发词：'铸'、'做成图'、'做成卡片'。
version: "1.0.0"
protocol: nexus-2.0
---

# ljg-card — 内容铸卡

## 核心指令

将内容转为 PNG 视觉卡片。模具决定视觉形式。

## 模具选择

| 参数 | 模具 | 尺寸 | 适用内容 |
|------|------|------|----------|
| `-l`（默认） | 长图 | 1080×auto | 单张阅读卡 |
| `-i` | 信息图 | 1080×auto | 数据驱动的可视化 |
| `-m` | 多卡 | 1080×1440 | 需拆分的多点内容 |
| `-v` | 视觉笔记 | 1080×auto | 手绘风格 sketchnote |
| `-c` | 漫画 | 1080×auto | 日式黑白漫画 |
| `-w` | 白板 | 1080×auto | 白板马克笔风格 |

## 执行流程

### 1. 获取内容

- URL → `scrape_url` 或 `web_fetch` 获取
- 粘贴文本 → 直接使用
- 文件路径 → `read_file` 获取

### 2. 检查依赖

检查 Playwright 是否安装。如未安装，执行 `npm install playwright && npx playwright install chromium`（工作目录：`skills/agency-ljg-card/`）。

### 3. 读取品味准则

必须先读取 `references/taste.md`，作为视觉质量底线。

### 4. 分析内容

运行 `bin/analyze_content.py`，传入内容，输出 JSON：
```
{"density": "medium", "structure": "contrast", "emotion": "技术", "word_count": 150}
```

### 5. 选择色调

读取 `references/color_palette.json`，根据第 4 步返回的 `emotion` 字段选择对应色调。

### 6. 读取模具指南

根据参数读取对应 mode 文件：

| 参数 | mode 文件 | template 文件 |
|------|-----------|---------------|
| `-l` | `references/mode-long.md` | `assets/long_template.html` |
| `-i` | `references/mode-infograph.md` | `assets/infograph_template.html` |
| `-m` | `references/mode-poster.md` | `assets/poster_template.html` |
| `-v` | `references/mode-sketchnote.md` | `assets/sketchnote_template.html` |
| `-c` | `references/mode-comic.md` | `assets/comic_template.html` |
| `-w` | `references/mode-whiteboard.md` | `assets/whiteboard_template.html` |

### 7. 生成 HTML

根据 mode 文件指导和第 4-5 步的分析结果：
1. 使用第 4 步的 `density`、`structure` 值确定布局结构
2. 使用第 5 步选择的色调
3. 设计画面
4. 编写 HTML

文件命名：从内容提取标题（中文，去标点，≤ 20 字符）
写入：`/tmp/ljg_cast_{mode}_{name}.html`

### 8. 截图

```
node assets/capture.js /tmp/ljg_cast_{mode}_{name}.html ~/Downloads/{name}.png 1080 800 fullpage
```

### 9. 交付

报告路径：`~/Downloads/{name}.png`

### 10. 反模式检查

生成后必须检查，参考 `references/color_palette.json` 中的 `rules` 字段。
