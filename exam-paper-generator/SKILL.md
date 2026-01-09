---
name: exam-paper-generator
description: 智能试题生成器，根据用户提供的教材、教科书、指导说明等文档，以及往年试题参考，自动分析并生成符合要求的试题。适用于用户请求"生成试题"、"出试卷"、"制作考卷"、"根据教材出题"、"参考往年试题出卷"时使用。支持多种题型，自动生成图例题目（占20%-30%），并输出Word或PDF格式的完整试卷（含详细参考答案）。
---

# 试题生成器 (Exam Paper Generator)

## 概述

这个 skill 帮助你基于教材、往年试题等参考资料，系统化地生成高质量的试卷。

**核心架构：数据驱动设计**

```
用户输入（教材 + 往年试题 + 要求）
    ↓
Skill 分析和生成
    ↓
exam_data.json  ← 纯数据文件（包含所有题目、答案、图例描述）
    ↓
generate_exam.py  ← 通用渲染引擎（可复用）
    ↓
final_exam.pdf / final_exam.docx
```

**关键特性：**
- ✅ 数据与逻辑分离：试卷内容用 JSON 描述，渲染引擎通用复用
- ✅ 声明式图例：图例用规格参数描述，由渲染器自动生成
- ✅ 可编辑性：用户可直接编辑 JSON 微调内容
- ✅ 多格式输出：同一数据可生成 PDF、Word 等多种格式

## 工作流程

### 第一步：收集和分析源材料

首先，需要理解用户提供的所有参考资料。询问用户：

**必要材料：**
- 教材/教科书/指导说明文件（PDF、Word、图片等格式）
- 考试范围说明（如果有）

**可选材料：**
- 往年试题/参考试卷
- 评分标准或答题要求
- 特殊要求（题型分布、难度比例等）

**分析要点：**
1. 仔细阅读所有提供的文档
2. 识别核心知识点和章节结构
3. 如果有往年试题，分析其题型分布、难度层次、问题表述风格
4. 提取关键概念、术语、公式、图表等

### 第二步：生成试卷数据文件（JSON）

基于分析结果，生成符合 `schemas/exam_schema.json` 规范的数据文件。

**数据文件结构：**

```json
{
  "meta": {
    "title": "2024年普通高中学业水平考试",
    "subject": "化学",
    "duration": 90,
    "total_score": 100,
    "notes": ["考生须知1", "考生须知2"],
    "constants": {"H": 1, "C": 12, "O": 16}
  },
  "sections": [
    {
      "title": "一、选择题",
      "type": "multiple_choice",
      "total_points": 30,
      "points_per_question": 2,
      "instructions": "每小题只有一个选项符合题意",
      "questions": [
        {
          "number": 1,
          "content": "按物质的分类，NaOH属于",
          "difficulty": "easy",
          "options": [
            {"label": "A", "content": "单质"},
            {"label": "B", "content": "氧化物"},
            {"label": "C", "content": "酸"},
            {"label": "D", "content": "碱"}
          ],
          "answer": {
            "content": "D",
            "explanation": "NaOH由钠离子和氢氧根离子组成，属于碱类物质。"
          }
        }
      ]
    }
  ]
}
```

**关键要求：**
- 图例题必须占总分的 20%-30%
- 题型分布应合理，覆盖主要知识点
- 难度梯度清晰（easy/medium/hard）
- 如果有往年试题，保持格式和风格一致

### 第三步：定义图例（声明式）

图例不需要手写代码，只需在 JSON 中声明规格参数：

**原子结构图示例：**
```json
{
  "diagram": {
    "type": "atom_structure",
    "title": "钠原子结构示意图",
    "width_cm": 6,
    "position": "after_content",
    "spec": {
      "element": "Na",
      "nucleus_charge": 11,
      "electron_shells": [2, 8, 1],
      "show_label": true
    }
  }
}
```

**流程图示例：**
```json
{
  "diagram": {
    "type": "flowchart",
    "title": "合成氨工业流程图",
    "width_cm": 14,
    "spec": {
      "nodes": [
        {"id": "input", "label": "N₂ + H₂\n(原料气)", "shape": "box"},
        {"id": "compress", "label": "压缩\n加压", "shape": "box"},
        {"id": "heat", "label": "加热\n催化剂", "shape": "box"}
      ],
      "edges": [
        {"from": "input", "to": "compress"},
        {"from": "compress", "to": "heat"}
      ],
      "direction": "LR"
    }
  }
}
```

**支持的图例类型：**

| 类型 | 说明 | 主要参数 |
|------|------|----------|
| `atom_structure` | 原子结构示意图 | element, nucleus_charge, electron_shells |
| `periodic_table` | 元素周期表（局部） | highlight_elements, show_periods |
| `experiment_setup` | 实验装置图 | apparatus, connections, layout |
| `flowchart` | 流程图 | nodes, edges, direction |
| `function_graph` | 函数图像 | functions, x_range, y_range |
| `coordinate_system` | 坐标系 | points, vectors, lines |
| `bar_chart` | 柱状图 | data, labels, xlabel, ylabel |
| `line_chart` | 折线图 | data_series, x_values |
| `pie_chart` | 饼图 | data, labels |
| `geometry` | 几何图形 | shapes, points |

### 第四步：渲染生成最终文档

使用通用渲染引擎生成 PDF 或 Word：

```bash
# 生成试卷（不含答案）
python scripts/generate_exam.py exam_data.json -o 化学试卷.pdf

# 生成试卷（含答案页）
python scripts/generate_exam.py exam_data.json -o 化学试卷.pdf --with-answers

# 生成 Word 格式（开发中）
python scripts/generate_exam.py exam_data.json -o 化学试卷.docx --format word
```

## 目录结构

```
exam-paper-generator/
├── SKILL.md                    # 本文档
├── schemas/
│   └── exam_schema.json        # 数据格式规范（JSON Schema）
├── scripts/
│   ├── generate_exam.py        # 通用渲染引擎
│   ├── generate_word.py        # Word 格式生成（辅助）
│   └── diagram_renderers/      # 图例渲染器模块
│       ├── __init__.py
│       ├── base.py             # 渲染器基类
│       ├── factory.py          # 渲染器工厂
│       ├── chemistry.py        # 化学类渲染器
│       ├── charts.py           # 图表类渲染器
│       ├── math.py             # 数学类渲染器
│       └── flowchart.py        # 流程图渲染器
├── examples/
│   └── chemistry_exam_example.json  # 示例数据文件
└── outputs/                    # 生成的文件存放处
    ├── *.json                  # 试卷数据文件
    └── *.pdf                   # 最终试卷
```

## 数据格式规范

详细规范见 `schemas/exam_schema.json`，主要结构：

### meta（元数据）
```json
{
  "title": "试卷标题",
  "subject": "科目",
  "duration": 90,
  "total_score": 100,
  "notes": ["考生须知..."],
  "constants": {"H": 1}
}
```

### section（大题部分）
```json
{
  "title": "一、选择题",
  "type": "multiple_choice",
  "total_points": 30,
  "points_per_question": 2,
  "instructions": "说明文字",
  "questions": [...]
}
```

**支持的题型（type）：**
- `multiple_choice` - 选择题
- `fill_blank` - 填空题
- `short_answer` - 简答题
- `calculation` - 计算题
- `essay` - 论述题
- `experiment` - 实验题
- `comprehensive` - 综合题

### question（题目）
```json
{
  "number": 1,
  "content": "题干内容",
  "content_continued": "题干续行（可选）",
  "points": 5,
  "difficulty": "medium",
  "is_diagram_question": true,
  "diagram": {...},
  "options": [...],
  "sub_questions": [...],
  "answer": {...}
}
```

### answer（答案）
```json
{
  "content": "答案内容",
  "explanation": "解析",
  "scoring_criteria": [
    {"point": "要点1", "score": 2},
    {"point": "要点2", "score": 3}
  ]
}
```

## 常见题型生成指南

### 选择题
- 题干简洁明确
- 选项数量通常 4 个（A/B/C/D）
- 干扰项有一定迷惑性但不误导

### 填空题
- 空格处为关键概念或数值
- 一题不超过 3 个空
- 答案明确唯一

### 简答题
- 问题开放度适中
- 有明确的评分点
- 答案长度合理

### 图例题
- 图例类型在 `diagram.type` 中指定
- 图例参数在 `diagram.spec` 中定义
- 渲染器自动生成专业图像

## 质量检查清单

生成数据文件后，检查：

- [ ] 总分正确，各部分分值加总无误
- [ ] 图例题占比在 20%-30% 范围内
- [ ] 所有图例定义完整，有 type 和 spec
- [ ] 题目表述清晰，无语法错误
- [ ] 答案准确，评分标准明确
- [ ] 难度分布合理
- [ ] 知识点覆盖全面
- [ ] 如有往年试题参考，格式风格保持一致

## 示例工作流

```
用户："帮我根据这份高中化学教材第三章的内容，参考去年的期中试卷格式，生成一份新的期中试卷"

Step 1: 请求材料
"请提供：
1. 高中化学教材第三章的PDF或截图
2. 去年期中试卷的文件
3. 本次考试的具体要求（时长、总分、重点章节等）"

Step 2: 分析材料后生成数据文件
基于分析结果，生成 chemistry_midterm_2024.json，包含：
- 元数据（科目、时长、总分等）
- 各大题结构
- 所有题目内容
- 图例定义（原子结构图、实验装置图等）
- 参考答案和评分标准

Step 3: 渲染生成 PDF
执行：python scripts/generate_exam.py chemistry_midterm_2024.json -o 化学期中试卷.pdf --with-answers

Step 4: 交付
"试卷已生成！
文件：化学期中试卷.pdf
- 试卷正文（含3道图例题）
- 参考答案及评分标准

数据文件：chemistry_midterm_2024.json
- 如需微调，可直接编辑此文件后重新渲染"
```

## 技术依赖

```bash
# 核心依赖
pip install reportlab matplotlib numpy

# 可选依赖（Word格式）
pip install python-docx pillow
```

### 中文字体配置

渲染引擎会自动检测系统中文字体：
- **macOS**: STHeiti, Songti
- **Windows**: SimHei, SimSun
- **Linux**: Noto Sans CJK

如果中文显示异常，请确保系统安装了中文字体。

## 与旧版本的区别

| 维度 | 旧版本（动态生成脚本） | 新版本（数据驱动） |
|------|----------------------|-------------------|
| 输出 | 438行 Python 脚本 | ~150行 JSON 数据 |
| 可读性 | 低（混合代码和数据） | 高（纯数据） |
| 可编辑 | 需要懂 Python | 编辑 JSON 即可 |
| 渲染 bug 修复 | 需要重新生成脚本 | 只修改渲染引擎 |
| 多格式支持 | 困难 | 容易（同一数据多种输出） |
| 版本管理 | Git diff 困难 | Git diff 清晰 |

## 注意事项

1. **版权和原创性**：生成的题目应基于教材内容，但避免直接照搬原文例题
2. **难度适配**：根据教育阶段调整题目难度和表述方式
3. **学科差异**：不同学科的题型和答案格式有所不同，需灵活调整
4. **图例质量**：确保图例定义参数完整，渲染器会自动生成专业图像
5. **数据验证**：生成的 JSON 应符合 `schemas/exam_schema.json` 规范
