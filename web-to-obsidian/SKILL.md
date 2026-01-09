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

使用 json-canvas skill 的格式规范，创建优雅的思维导图风格知识图谱。

**文件路径**: `John/Canvas/<标题>.canvas`

**Canvas 设计原则**:

1. **中心发散布局** - 核心主题居中，内容向四周自然延展
2. **有机错落感** - 节点位置有自然偏移，避免机械对齐
3. **大小层次分明** - 核心大、分支中、细节小
4. **连接线自然流动** - 根据节点位置选择最自然的连接方向
5. **留白呼吸感** - 节点间保持舒适距离，不拥挤

**布局风格 - 思维导图式**:

```
                    ┌─────────┐
                    │ 笔记文件 │
                    └────┬────┘
                         │
    ┌──────────┐    ┌────┴────┐    ┌──────────┐
    │  左上    │────│  核心   │────│  右上    │
    │  分支1   │    │  主题   │    │  分支2   │
    └──────────┘    └────┬────┘    └──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────┴────┐    ┌─────┴────┐    ┌────┴────┐
    │ 概念1   │    │  概念2   │    │ 概念3   │
    └─────────┘    └──────────┘    └─────────┘
                         │
                    ┌────┴────┐
                    │ 原文链接 │
                    └─────────┘
```

**节点尺寸参考**（可根据内容调整）:

| 节点类型  | 宽度范围 | 高度范围 | 颜色       |
| --------- | -------- | -------- | ---------- |
| 核心主题  | 360-450  | 140-180  | `"4"` 绿色 |
| 主要分支  | 240-320  | 100-160  | `"5"` 青色 |
| 关键概念  | 120-180  | 50-80    | `"3"` 黄色 |
| 补充信息  | 200-280  | 80-120   | `"2"` 橙色 |
| 文件/链接 | 200-300  | 60-100   | 无         |

**位置布局参考**:

```
// 画布中心点: (500, 400)
// 核心主题放置在中心

核心主题: x=280, y=320 (居中)

// 分支节点围绕核心，有角度错落
左上分支: x=0,   y=120  (偏左上)
右上分支: x=680, y=80   (偏右上)
左下分支: x=40,  y=520  (偏左下)
右下分支: x=640, y=560  (偏右下)

// 概念节点在下方散开，有高低错落
概念1: x=80,  y=700
概念2: x=280, y=740  (稍低)
概念3: x=480, y=710
概念4: x=680, y=750  (稍低)

// 文件节点在上方
笔记文件: x=340, y=60

// 链接在底部居中
原文链接: x=300, y=880
```

**连接线规则**:

1. 根据节点相对位置选择连接边（left/right/top/bottom）
2. 核心向四周发散，概念从分支延伸
3. 只在重要连接添加标签
4. 避免连接线过长或交叉

**Canvas JSON 示例**:

```json
{
  "nodes": [
    {
      "id": "center01",
      "type": "text",
      "x": 280,
      "y": 320,
      "width": 400,
      "height": 160,
      "text": "# 文章核心主题\n\n一句话概括文章的核心价值",
      "color": "4"
    },
    {
      "id": "file01",
      "type": "file",
      "x": 340,
      "y": 60,
      "width": 280,
      "height": 80,
      "file": "John/Notes/<标题>.md"
    },
    {
      "id": "branch01",
      "type": "text",
      "x": 0,
      "y": 140,
      "width": 260,
      "height": 140,
      "text": "## 分支主题1\n\n- 要点A\n- 要点B",
      "color": "5"
    },
    {
      "id": "branch02",
      "type": "text",
      "x": 700,
      "y": 100,
      "width": 280,
      "height": 120,
      "text": "## 分支主题2\n\n- 要点C\n- 要点D",
      "color": "5"
    },
    {
      "id": "branch03",
      "type": "text",
      "x": 20,
      "y": 540,
      "width": 240,
      "height": 120,
      "text": "## 分支主题3\n\n- 要点E",
      "color": "5"
    },
    {
      "id": "concept01",
      "type": "text",
      "x": 340,
      "y": 700,
      "width": 140,
      "height": 60,
      "text": "**概念1**",
      "color": "3"
    },
    {
      "id": "concept02",
      "type": "text",
      "x": 520,
      "y": 740,
      "width": 160,
      "height": 60,
      "text": "**概念2**",
      "color": "3"
    },
    {
      "id": "link01",
      "type": "link",
      "x": 340,
      "y": 880,
      "width": 280,
      "height": 80,
      "url": "<原始URL>"
    }
  ],
  "edges": [
    {
      "id": "e01",
      "fromNode": "center01",
      "fromSide": "top",
      "toNode": "file01",
      "toSide": "bottom"
    },
    {
      "id": "e02",
      "fromNode": "center01",
      "fromSide": "left",
      "toNode": "branch01",
      "toSide": "right"
    },
    {
      "id": "e03",
      "fromNode": "center01",
      "fromSide": "right",
      "toNode": "branch02",
      "toSide": "left"
    },
    {
      "id": "e04",
      "fromNode": "center01",
      "fromSide": "left",
      "toNode": "branch03",
      "toSide": "right"
    },
    {
      "id": "e05",
      "fromNode": "center01",
      "fromSide": "bottom",
      "toNode": "concept01",
      "toSide": "top"
    },
    {
      "id": "e06",
      "fromNode": "center01",
      "fromSide": "bottom",
      "toNode": "concept02",
      "toSide": "top"
    },
    {
      "id": "e07",
      "fromNode": "center01",
      "fromSide": "bottom",
      "toNode": "link01",
      "toSide": "top",
      "label": "原文"
    }
  ]
}
```

**布局技巧**:

- 主要分支 2-4 个，分布在核心的左右两侧
- 概念标签 3-6 个，在下方自然散开
- 位置添加 ±20~50 的随机偏移，增加自然感
- 内容多的节点可以更大，内容少的更紧凑

### Step 5: 写入文件

使用 Write 工具写入两个文件：

1. Markdown 笔记: `/Users/hong/John/md/John/Notes/<标题>.md`
2. Canvas 文件: `/Users/hong/John/md/John/Canvas/<标题>.canvas`

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
