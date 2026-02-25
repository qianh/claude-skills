---
name: web-to-obsidian
description: 将网页内容保存到 Obsidian 仓库。使用 web-reader MCP 或 chrome-devtools MCP 获取链接内容，转换为 Obsidian Markdown 格式保存到 John/Notes，并分析内容结构生成 JSON Canvas 到 John/Canvas。当用户提供网页链接并希望保存到 Obsidian、收藏文章、或需要将网页内容转为笔记和知识图谱时使用。触发词：保存网页、收藏文章、网页转笔记、保存到 Obsidian、生成知识图谱。
---

# Web to Obsidian

将网页内容转换为 Obsidian 笔记和 Canvas 知识图谱。

## 工作流程

### Step 1: 获取网页内容

优先使用 `mcp__web-reader__webReader` 工具获取内容：

```
mcp__web-reader__webReader:
  url: "<用户提供的URL>"
  return_format: "markdown"
  retain_images: true
  with_links_summary: true
```

如果 web-reader 失败（如需要登录或 JavaScript 渲染），使用 chrome-devtools MCP：

1. `mcp__chrome-devtools__new_page` 打开页面
2. `mcp__chrome-devtools__take_snapshot` 获取页面快照
3. 从快照中提取内容

### Step 2: 解析内容结构

从获取的内容中提取：

- **标题** (title): 文章主标题
- **作者** (author): 文章作者（如有）
- **发布日期** (date): 发布时间（如有）
- **来源** (source): 网站名称或域名
- **正文** (content): 主要内容
- **标签** (tags): 根据内容推断 2-5 个标签
- **关键概念**: 文章中的核心概念或术语（用于生成 Canvas）
- **内容结构**: 标题层级和章节划分

### Step 3: 生成 Obsidian Markdown

保持原文内容，仅添加必要的 frontmatter 元数据。

**文件路径**: `John/Notes/<标题>.md`

**文件内容模板**:

```markdown
---
title: <文章标题>
author: <作者>
source: <来源网站>
url: <原始URL>
saved: <保存日期 YYYY-MM-DD>
tags:
  - <tag1>
  - <tag2>
---

<原文内容，保持原有格式和标题层级，不做任何修改或添加>
```

**原则**: 忠实保留原文，不添加摘要、callout、分隔线等额外内容。

**文件命名规则**:

- 使用文章标题作为文件名
- 移除特殊字符: `/ \ : * ? " < > |`
- 长度限制: 最多 100 字符
- 重复文件: 添加 `(1)`, `(2)` 后缀

### Step 4: 生成 JSON Canvas

使用 json-canvas skill 的格式规范，创建清晰美观的知识图谱。

**文件路径**: `John/Canvas/<标题>.canvas`

---

#### 布局方案选择

根据内容类型选择合适的布局：

| 内容类型 | 推荐布局 | 示例 |
|---------|---------|------|
| 结构化内容（学习计划、教程、步骤流程） | **自上而下流式布局** | 阶段/步骤横向排列 |
| 文章/博客（观点发散、概念关联） | **中心发散式布局** | 核心观点居中，论点向外辐射 |

---

#### 布局 A：自上而下流式布局（结构化内容首选）

适用于：学习计划、教程、技术文档、步骤流程类内容。

**视觉结构**：
```
        ┌──────────────────────────┐
        │       📄 笔记文件         │  ← 文件节点，顶部居中
        └──────────────┬───────────┘
                       │
        ┌──────────────┴───────────┐
        │       核心主题（大）       │  ← 绿色，宽900+，高140+
        └──┬─────────┬──────┬──┬──┘
           │         │      │  │
     ┌─────┴──┐ ┌────┴──┐ ...  │     ← 分支节点，等宽均匀排列，同一 y 值
     │ 分支1  │ │ 分支2 │      │        青色，每个约 230w × 160h
     └────┬───┘ └───┬───┘      │
          │         │
     ┌────┴──┐ ┌────┴──┐            ← 概念节点，直接在所属分支正下方
     │ 概念A │ │ 概念B │               黄色，约 200w × 65h
     └───────┘ └───────┘
        ┌──────────────────────────┐
        │       💡 实用建议         │  ← 补充信息，橙色，宽820
        └──────────────┬───────────┘
                       │
        ┌──────────────┴───────────┐
        │       🔗 原文链接         │  ← link 节点，底部居中
        └──────────────────────────┘
```

**精确坐标计算规则**（假设 N 个分支节点，间距 GAP=30）：

```
BRANCH_W = (总宽度 - (N-1)*GAP) / N   // 每个分支等宽
总宽度建议 = max(900, N*230 + (N-1)*30)
LEFT_EDGE = 60                         // 左边距

// 各层 y 坐标（层间距 80px）
y_file    = -110
y_core    = 0      // core 高度 150
y_branch  = 230    // branch 高度 170
y_concept = 440    // concept 高度 65
y_tips    = 560    // tips 高度 130
y_link    = 740

// 分支 x 坐标（从 LEFT_EDGE 开始，等间距）
branch[i].x = LEFT_EDGE + i * (BRANCH_W + GAP)

// 概念 x 坐标（对齐到所属分支）
concept[i].x = branch[i].x
concept[i].width = branch[i].width

// 文件节点居中
file.x = LEFT_EDGE + 总宽度/2 - file.width/2

// 核心节点与分支等宽
core.x = LEFT_EDGE
core.width = 总宽度
```

**节点高度计算公式**（必须足够容纳全部文字，禁止截断）：

```
height = 32（上下内边距）+ 各行行高之和

行高参考值：
  H1 (#)  标题      → 44px
  H2 (##) 标题      → 36px
  H3 (###) 标题     → 30px
  普通文本 / 列表项  → 28px
  内联代码行         → 28px
  空行               → 20px

示例：1个H2 + 1行粗体 + 1空行 + 4个列表项
  = 32 + 36 + 28 + 20 + 28×4 = 228px → 取 h=230

原则：宁大勿小，多余空白比文字被截断好看。
```

**节点尺寸与颜色**：

| 节点类型  | 宽度       | 高度计算方式         | 颜色       |
|---------|-----------|-------------------|-----------|
| 文件节点  | 350       | 固定 70            | 无         |
| 核心主题  | = 总宽度   | 按公式计算，≥160    | `"4"` 绿色 |
| 分支节点  | 等分总宽度  | 按公式计算，≥220    | `"5"` 青色 |
| 概念节点  | = 分支宽度 | 按公式计算，≥85     | `"3"` 黄色 |
| 补充信息  | 800+      | 按公式计算，≥200    | `"2"` 橙色 |
| 链接节点  | 400       | 固定 60            | 无         |

**连接线规则**：
- file → core：file.bottom → core.top
- core → 每个 branch：core.bottom → branch.top
- branch → 其下方 concept：branch.bottom → concept.top
- tips → link：tips.bottom → link.top（加 label "原文"）

**4分支完整示例**（总宽=1060, BRANCH_W=235, GAP=30, LEFT_EDGE=60）：

```json
{
  "nodes": [
    {
      "id": "n_file",
      "type": "file",
      "x": 415, "y": -110,
      "width": 350, "height": 70,
      "file": "John/Notes/<标题>.md"
    },
    {
      "id": "n_core",
      "type": "text",
      "x": 60, "y": 0,
      "width": 1060, "height": 150,
      "text": "# 核心主题\n\n一句话描述核心价值与目标",
      "color": "4"
    },
    {
      "id": "n_b1",
      "type": "text",
      "x": 60, "y": 230,
      "width": 235, "height": 170,
      "text": "## 📚 分支一\n**副标题**\n\n- 要点 A\n- 要点 B\n- 要点 C",
      "color": "5"
    },
    {
      "id": "n_b2",
      "type": "text",
      "x": 325, "y": 230,
      "width": 235, "height": 170,
      "text": "## 🔍 分支二\n**副标题**\n\n- 要点 D\n- 要点 E\n- 要点 F",
      "color": "5"
    },
    {
      "id": "n_b3",
      "type": "text",
      "x": 590, "y": 230,
      "width": 235, "height": 170,
      "text": "## 🤖 分支三\n**副标题**\n\n- 要点 G\n- 要点 H",
      "color": "5"
    },
    {
      "id": "n_b4",
      "type": "text",
      "x": 855, "y": 230,
      "width": 265, "height": 170,
      "text": "## 🚀 分支四\n**副标题**\n\n- 要点 I\n- 要点 J",
      "color": "5"
    },
    {
      "id": "n_c1",
      "type": "text",
      "x": 60, "y": 440,
      "width": 235, "height": 65,
      "text": "**核心概念A**\n一句话说明",
      "color": "3"
    },
    {
      "id": "n_c2",
      "type": "text",
      "x": 325, "y": 440,
      "width": 235, "height": 65,
      "text": "**核心概念B**\n一句话说明",
      "color": "3"
    },
    {
      "id": "n_c3",
      "type": "text",
      "x": 590, "y": 440,
      "width": 235, "height": 65,
      "text": "**核心概念C**\n一句话说明",
      "color": "3"
    },
    {
      "id": "n_c4",
      "type": "text",
      "x": 855, "y": 440,
      "width": 265, "height": 65,
      "text": "**核心概念D**\n一句话说明",
      "color": "3"
    },
    {
      "id": "n_tips",
      "type": "text",
      "x": 170, "y": 560,
      "width": 840, "height": 130,
      "text": "## 💡 补充信息\n\n- 要点一\n- 要点二\n- 要点三",
      "color": "2"
    },
    {
      "id": "n_link",
      "type": "link",
      "x": 390, "y": 740,
      "width": 400, "height": 60,
      "url": "<原始URL>"
    }
  ],
  "edges": [
    {"id": "e1", "fromNode": "n_file", "fromSide": "bottom", "toNode": "n_core", "toSide": "top"},
    {"id": "e2", "fromNode": "n_core", "fromSide": "bottom", "toNode": "n_b1", "toSide": "top"},
    {"id": "e3", "fromNode": "n_core", "fromSide": "bottom", "toNode": "n_b2", "toSide": "top"},
    {"id": "e4", "fromNode": "n_core", "fromSide": "bottom", "toNode": "n_b3", "toSide": "top"},
    {"id": "e5", "fromNode": "n_core", "fromSide": "bottom", "toNode": "n_b4", "toSide": "top"},
    {"id": "e6", "fromNode": "n_b1", "fromSide": "bottom", "toNode": "n_c1", "toSide": "top"},
    {"id": "e7", "fromNode": "n_b2", "fromSide": "bottom", "toNode": "n_c2", "toSide": "top"},
    {"id": "e8", "fromNode": "n_b3", "fromSide": "bottom", "toNode": "n_c3", "toSide": "top"},
    {"id": "e9", "fromNode": "n_b4", "fromSide": "bottom", "toNode": "n_c4", "toSide": "top"},
    {"id": "e10", "fromNode": "n_tips", "fromSide": "bottom", "toNode": "n_link", "toSide": "top", "label": "原文"}
  ]
}
```

---

#### 布局 B：中心发散式布局（文章/博客首选）

适用于：观点类文章、概念解析、知识总结等发散性内容。

**视觉结构**：
```
              ┌──────────┐
              │ 左分支1  │
              └────┐     │
  ┌──────────┐     │     │   ┌──────────┐
  │ 左分支2  ├─────┤ 核心 ├───┤ 右分支1  │
  └──────────┘     │     │   └──────────┘
              ┌────┘     │
              │ 左分支3  │       ┌──────────┐
              └──────────┘       │ 右分支2  │
                                 └──────────┘
        ┌────────┐  ┌────────┐  ┌────────┐
        │ 概念1  │  │ 概念2  │  │ 概念3  │
        └────────┘  └────────┘  └────────┘
```

**坐标规则**：
```
核心主题（居中）: x=280, y=260, width=420, height=160

// 左侧分支（2-3个，上下错落，间距约160px）
左分支1: x=-60,  y=100,  width=280, height=130
左分支2: x=-80,  y=280,  width=280, height=130
左分支3: x=-40,  y=450,  width=260, height=110

// 右侧分支（2-3个，上下错落，间距约160px）
右分支1: x=740,  y=80,   width=280, height=130
右分支2: x=760,  y=260,  width=280, height=130
右分支3: x=720,  y=430,  width=260, height=110

// 概念标签（底部一行，等间距）
概念1: x=60,  y=680, width=180, height=65
概念2: x=270, y=680, width=180, height=65
概念3: x=480, y=680, width=180, height=65

// 文件节点（顶部居中）
文件: x=340, y=60, width=300, height=70

// 链接（底部居中）
链接: x=340, y=800, width=300, height=60
```

**连接线规则**：
- file → 核心：top/bottom
- 核心 → 左分支：core.left → branch.right
- 核心 → 右分支：core.right → branch.left
- 核心 → 概念：core.bottom → concept.top
- 核心 → 链接：core.bottom → link.top

---

#### 通用规则

1. **严格对齐**：同层级节点必须使用相同的 y 值，禁止随意偏移
2. **节点间距**：同行节点水平间距固定为 30px
3. **边连接方向**：节点在上方用 bottom→top，节点在左用 right→left
4. **ID 格式**：使用语义化短 ID，如 `n_core`、`n_b1`、`e_core_b1`
5. **文字内容**：分支节点标题用 emoji 增强可读性，概念节点用加粗短语+一行说明

### Step 5: 写入文件

使用 Write 工具写入两个文件：

1. Markdown 笔记: `/Users/john/private/md/John/Notes/<标题>.md`
2. Canvas 文件: `/Users/john/private/md/John/Canvas/<标题>.canvas`

### Step 6: 输出报告

完成后向用户报告：

```
📝 网页内容已保存到 Obsidian

笔记文件: John/Notes/<标题>.md
Canvas 文件: John/Canvas/<标题>.canvas

📊 内容摘要:
- 标题: <标题>
- 作者: <作者>
- 标签: #tag1 #tag2 #tag3
- 关键概念: <概念1>, <概念2>, <概念3>

✅ 保存完成！可在 Obsidian 中查看。
```

## 特殊处理

### 微信公众号文章

对于 `mp.weixin.qq.com` 链接：

- 提取公众号名称作为 author
- 提取发布日期
- 图片可能需要特殊处理（微信防盗链）

### 需要登录的页面

如果 web-reader 返回登录页面或错误：

1. 提示用户使用 chrome-devtools 方式
2. 用户在浏览器中登录后，使用 `take_snapshot` 获取内容

### 图片处理

- 保留图片的原始 URL
- 使用 Markdown 图片语法: `![alt](url)`
- 对于重要图片，可建议用户手动下载到 attachments

## ID 生成

Canvas 中的 node 和 edge ID 使用 16 位小写十六进制字符串：

```javascript
// 生成方式示例
Math.random().toString(16).substring(2, 18).padEnd(16, "0");
```

## 依赖的 Skills

- **obsidian-markdown**: Markdown 格式规范
- **json-canvas**: Canvas 文件格式规范

## 依赖的 MCP 工具

- **web-reader**: `mcp__web-reader__webReader`
- **chrome-devtools**: `mcp__chrome-devtools__*`

## 示例

### 输入

```
用户: 帮我把这篇文章保存到 Obsidian: https://mp.weixin.qq.com/s/zDoiLO6g06t_bWxFBCbtkA
```

### 处理过程

1. 使用 web-reader 获取文章内容
2. 解析标题、作者、正文
3. 生成 Markdown 笔记（含 frontmatter 和 callout）
4. 分析内容结构，提取关键概念
5. 生成 Canvas 知识图谱
6. 写入文件并报告结果

### 输出

```
📝 网页内容已保存到 Obsidian

笔记文件: John/Notes/如何高效学习编程.md
Canvas 文件: John/Canvas/如何高效学习编程.canvas

📊 内容摘要:
- 标题: 如何高效学习编程
- 作者: 技术博主
- 标签: #学习方法 #编程 #效率
- 关键概念: 刻意练习, 项目驱动, 代码复盘

✅ 保存完成！可在 Obsidian 中查看。
```
