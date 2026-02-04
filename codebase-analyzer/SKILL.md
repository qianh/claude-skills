---
name: codebase-analyzer
description: 深度分析项目代码库，生成完整的开发指导手册。使用 LLM 理解每个文件，通过多代理协作支持任意规模代码库分析，提取所有组件/库/Hook 的使用示例，输出数据驱动的 Markdown 开发手册。当用户请求"分析项目"、"生成开发手册"、"了解项目结构"、"提取编码规范"、"分析代码库"时使用此技能。
---

# Codebase Analyzer

分析项目代码库，生成数据驱动的开发指导手册，包含场景索引和组件选择器。

## 核心原则

1. **强制全量分析**：每个文件都必须被 Read 工具读取，不允许采样或跳过
2. **Import 驱动分析**：先用 Grep 提取 import 行，再逐条对照分析，杜绝遗漏
3. **销项机制**：使用待办列表追踪进度，处理完就物理删除
4. **断点续传**：支持中断后继续
5. **质量校验**：每批次自动验证结果非空率，不合格必须重做
6. **数据驱动文档**：最终文档必须从汇总数据生成，禁止凭印象编写

---

## 反偷懒机制（本 Skill 的核心防线）

```
上一次执行本 Skill 时，LLM 在 92% 的文件上产出了空结果（componentUsages: []），
而实际上这些文件明确 import 并使用了大量组件。这是因为 LLM "偷懒"了——
走完了流程但没有真正分析文件内容。

本次修订引入以下硬性防线：

防线 1：Import 预提取
  - 在 LLM 分析每个文件之前，先用 Grep 工具提取该文件的所有 import 行
  - 将 import 行作为"必须覆盖的清单"写入批次结果
  - LLM 必须对照 import 清单逐条说明每个 import 在文件中的使用方式

防线 2：小批次（每批 3 个文件）
  - 旧版本每批 10 个文件，LLM 后面几个文件容易敷衍
  - 新版本每批只处理 3 个文件，每个文件都必须被充分分析

防线 3：逐文件 Read
  - 每个文件必须单独调用 Read 工具读取完整内容
  - 严禁"我已经知道这个文件的内容"或"这个文件和上一个类似"
  - 每个 Read 调用的结果必须在分析中被引用

防线 4：自动质量校验
  - 每批次写入 JSON 后，用 Python 脚本验证：
    a) .tsx/.jsx 文件的 imports 数组不能为空
    b) 如果 imports 中有非 react/非类型的导入，componentUsages 或 hookUsages 不能全空
  - 校验不通过则该批次必须重做

防线 5：Import 行原文保留
  - 每个文件的分析结果必须包含 imports 字段，保存该文件的所有 import 行原文
  - 这样在汇总阶段可以交叉验证
```

---

## 工作目录结构

所有中间文件存储在 `.ai-docs/` 目录：

```
.ai-docs/
├── _todo.txt              # 待处理文件列表（销项清单）
├── _done.txt              # 已处理文件列表（断点续传用）
├── _errors.txt            # 处理失败的文件
├── _progress.md           # 进度追踪报告
├── _batches/              # 批次分析结果
│   ├── batch_001.json
│   ├── batch_002.json
│   └── ...
├── _aggregated.json       # 汇总后的完整数据
│
├── COMPONENT-SELECTOR.md  # 【最终输出】组件选择器
├── DEV-GUIDE.md           # 【最终输出】开发手册入口
├── inventory.md           # 【最终输出】物资清单
├── scenarios/             # 【最终输出】场景文档
├── components/            # 【最终输出】组件文档
├── hooks/                 # 【最终输出】Hook 文档
└── utils/                 # 【最终输出】工具函数文档
```

---

## 阶段 0：初始化检查（必须执行）

### 步骤 0.1：检查是否存在进行中的分析

```bash
if [ -s .ai-docs/_todo.txt ]; then
  echo "发现未完成的分析任务，将继续执行..."
  # 进入断点续传模式，跳到阶段 2
else
  echo "开始全新分析..."
  # 进入全新分析模式，执行阶段 1
fi
```

### 步骤 0.2：创建工作目录

```bash
mkdir -p .ai-docs/_batches .ai-docs/scenarios .ai-docs/components .ai-docs/hooks .ai-docs/utils
```

---

## 阶段 1：创建待办列表（全新分析时执行）

### 步骤 1.1：扫描所有代码文件

使用 Glob 工具扫描，排除以下目录：
- `node_modules/`、`dist/`、`build/`、`.next/`、`.nuxt/`
- `.git/`、`coverage/`、`.umi/`、`.ai-docs/`

扫描模式：
```
src/**/*.{ts,tsx,js,jsx,vue,svelte}
```

如果没有 `src` 目录，扫描项目根目录。

### 步骤 1.2：写入待办列表

将所有文件路径写入 `.ai-docs/_todo.txt`，每行一个文件。

### 步骤 1.3：初始化进度报告

创建 `.ai-docs/_progress.md`：

```markdown
# 代码分析进度报告

开始时间：{当前时间}
总文件数：{文件数量}
已完成：0
待处理：{文件数量}

## 批次记录

| 批次 | 文件数 | imports提取数 | usages提取数 | 质量校验 | 完成时间 |
| ---- | ------ | ------------- | ------------ | -------- | -------- |
```

### 步骤 1.4：清空已完成列表

```bash
> .ai-docs/_done.txt
> .ai-docs/_errors.txt
```

---

## 阶段 2：批次化分析（核心循环）

### 批次大小：3 个文件

每批只处理 3 个文件。这是为了确保每个文件都被充分分析。

### 完整的单批次流程

对于每一批（3 个文件），严格按以下顺序执行：

#### 步骤 2.1：读取待办列表

```bash
head -3 .ai-docs/_todo.txt
```

如果 `_todo.txt` 为空，跳到阶段 3。

#### 步骤 2.2：对每个文件执行"三步分析法"

对于批次中的每一个文件（假设为 `FILE`），严格执行以下三步：

**第一步：Grep 预提取 import 行**

使用 Grep 工具搜索该文件的所有 import 行：

```
Grep pattern="^import " path="FILE" output_mode="content"
```

将结果保存为该文件的 `imports` 数组。

例如，对于 `src/pages/work-flow/components/FormWorkFlowTask/ModalTaskEdit.tsx`，Grep 应返回：

```
import I18N from '@/utils/I18N';
import { message, validatorHelper } from '@dzg/common-utils';
import { DzgForm } from '@dzg/dzg-form';
import { Form, Modal, Select, InputNumber, FormInstance, SelectProps, Input } from 'antd';
import React, { useEffect, useImperativeHandle, useRef, useState } from 'react';
import TinyEditor, { TinyEditorRef } from '@/components/TinyEditor';
import { useRequest } from 'umi';
...
```

**第二步：Read 完整文件内容**

使用 Read 工具读取该文件的完整内容。

**第三步：对照 import 清单逐条分析**

拿着第一步的 import 清单和第二步的文件内容，逐条分析：

- 对于每个 import 的组件/函数/Hook，在文件正文中找到它的**使用位置**
- 提取使用代码片段（JSX 片段 或 函数调用片段）
- 记录使用的 props 或参数
- 标注 import 来源

```
【分析清单示例】

import { DzgForm } from '@dzg/dzg-form'
  → 使用位置：第 135 行
  → 使用代码：<DzgForm schema={getFormConfig(form)} form={form} labelWidth={6} />
  → props: schema, form, labelWidth
  → 类别：表单组件

import { Form, Modal, Select, InputNumber, Input } from 'antd'
  → Modal 使用位置：第 120 行
  → Modal 使用代码：<Modal visible={visible} title={...} onCancel={onClose} onOk={handleSave}>
  → Modal props: visible, title, onCancel, onOk, maskClosable
  → Select 使用位置：第 145 行
  → ...（每个导出都要分析）

import TinyEditor from '@/components/TinyEditor'
  → 使用位置：第 361 行
  → 使用代码：<TinyEditor ref={tinyRef} height="360px" disabled={hasAccessDisabled} />
  → props: ref, height, disabled
  → 类别：业务组件

import { useRequest } from 'umi'
  → 使用位置：第 30 行
  → 使用代码：const { data, run } = useRequest(apiDesignatedPersonOptions, { manual: true })
  → 类别：Hook
```

对于以下 import 可以跳过详细分析（但仍必须记录在 imports 数组中）：
- `import React` / `import { useState, useEffect, ... } from 'react'` — 基础 React Hooks，记录使用但不需要提取代码片段
- `import type` / `import { I... }` — 纯类型导入
- `import './xxx.less'` / `import './xxx.css'` — 样式导入
- `import css from './xxx.less'` — CSS Modules 导入

对于以下 import 必须详细分析：
- 所有 antd 组件（Modal, Table, Form, Button, Select 等）
- 所有 @dzg/* 组件
- 所有 @/components/* 组件
- 所有 @/hooks/* 或自定义 Hook（use* 开头）
- 所有 @/utils/* 或 @/utils-business/* 工具函数
- 所有第三方库的功能组件（非 React 基础库）

#### 步骤 2.3：写入批次结果 JSON

将分析结果写入 `.ai-docs/_batches/batch_XXX.json`。

**JSON 结构**（注意新增的 `imports` 字段和 `importCount` / `usageCount` 统计字段）：

```json
{
  "batchId": 1,
  "timestamp": "2024-01-27T10:30:00Z",
  "files": [
    {
      "filePath": "src/pages/work-flow/components/FormWorkFlowTask/ModalTaskEdit.tsx",
      "fileType": "tsx",
      "scenario": {
        "type": "modal",
        "description": "工作流任务编辑弹窗"
      },
      "imports": [
        "import I18N from '@/utils/I18N';",
        "import { message, validatorHelper } from '@dzg/common-utils';",
        "import { DzgForm } from '@dzg/dzg-form';",
        "import { Form, Modal, Select, InputNumber, FormInstance, SelectProps, Input } from 'antd';",
        "import React, { useEffect, useImperativeHandle, useRef, useState } from 'react';",
        "import TinyEditor, { TinyEditorRef } from '@/components/TinyEditor';",
        "import { useRequest } from 'umi';"
      ],
      "importCount": 7,
      "componentUsages": [
        {
          "name": "TinyEditor",
          "importFrom": "@/components/TinyEditor",
          "code": "<TinyEditor ref={tinyRef} height=\"360px\" disabled={hasAccessDisabled} />",
          "props": ["ref", "height", "disabled"],
          "description": "富文本编辑器，用于编辑任务描述"
        },
        {
          "name": "DzgForm",
          "importFrom": "@dzg/dzg-form",
          "code": "<DzgForm schema={getFormConfig(form)} form={form} labelWidth={6} />",
          "props": ["schema", "form", "labelWidth"],
          "description": "动态表单组件"
        },
        {
          "name": "Modal",
          "importFrom": "antd",
          "code": "<Modal visible={visible} title={isEdit ? '编辑' : '新增'} onCancel={onClose} onOk={handleSave} maskClosable={false}>",
          "props": ["visible", "title", "onCancel", "onOk", "maskClosable"],
          "description": "编辑任务弹窗"
        },
        {
          "name": "Select",
          "importFrom": "antd",
          "code": "<Select options={staffTypeOptions} onChange={handleStaffTypeChange} />",
          "props": ["options", "onChange"],
          "description": "人员类型选择"
        },
        {
          "name": "InputNumber",
          "importFrom": "antd",
          "code": "<InputNumber min={0} max={999} />",
          "props": ["min", "max"],
          "description": "数字输入"
        },
        {
          "name": "Input",
          "importFrom": "antd",
          "code": "<Input placeholder=\"请输入\" />",
          "props": ["placeholder"],
          "description": "文本输入"
        }
      ],
      "hookUsages": [
        {
          "name": "useRequest",
          "importFrom": "umi",
          "code": "const { data: personOptions, run: fetchPersonOptions } = useRequest(apiDesignatedPersonOptions, { manual: true });",
          "params": "apiDesignatedPersonOptions, { manual: true }",
          "returnValues": ["data", "run"],
          "description": "手动触发获取指定人选项"
        }
      ],
      "utilUsages": [
        {
          "name": "I18N",
          "importFrom": "@/utils/I18N",
          "code": "I18N.work_flow.ModalTaskEdit.title",
          "description": "国际化文案"
        },
        {
          "name": "validatorHelper",
          "importFrom": "@dzg/common-utils",
          "code": "validatorHelper({ required: true })",
          "description": "表单校验规则生成"
        }
      ],
      "usageCount": 8
    }
  ]
}
```

**关键约束**：
- `imports` 数组必须包含 Grep 预提取的所有 import 行原文
- `importCount` 必须等于 `imports` 数组长度
- `usageCount` = componentUsages.length + hookUsages.length + utilUsages.length
- 对于 .tsx/.jsx 文件，如果 imports 中有非 react/非类型/非样式的导入，则 usageCount 不能为 0

#### 步骤 2.4：质量校验（每批必须执行）

写入 JSON 后，立即使用 Bash 执行以下 Python 校验脚本：

```bash
python3 -c "
import json, sys

with open('.ai-docs/_batches/batch_XXX.json') as f:
    data = json.load(f)

errors = []
for file_info in data['files']:
    fp = file_info['filePath']
    ft = file_info.get('fileType', '')
    imports = file_info.get('imports', [])
    import_count = file_info.get('importCount', 0)
    usage_count = file_info.get('usageCount', 0)

    # 检查 1：imports 数组不能为空（除非文件是纯类型定义）
    if not imports and ft in ('tsx', 'jsx'):
        errors.append(f'  {fp}: imports 为空，但文件类型是 {ft}')

    # 检查 2：importCount 必须匹配
    if import_count != len(imports):
        errors.append(f'  {fp}: importCount({import_count}) != len(imports)({len(imports)})')

    # 检查 3：有非基础 import 时，usageCount 不能为 0
    meaningful_imports = [i for i in imports
        if not i.strip().startswith('import React')
        and 'from \\'react\\'' not in i
        and 'import type' not in i
        and '.less' not in i and '.css' not in i and '.scss' not in i]
    if meaningful_imports and usage_count == 0 and ft in ('tsx', 'jsx'):
        errors.append(f'  {fp}: 有 {len(meaningful_imports)} 个有效 import 但 usageCount=0')
        for mi in meaningful_imports[:5]:
            errors.append(f'    - {mi.strip()}')

if errors:
    print('QUALITY CHECK FAILED:')
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print('QUALITY CHECK PASSED')
"
```

**如果校验失败**：
1. 输出错误信息
2. 删除该批次 JSON
3. 重新执行步骤 2.2 ~ 2.3 分析这 3 个文件
4. 重新校验，直到通过

#### 步骤 2.5：更新销项文件

校验通过后：

```bash
# 追加到 _done.txt
head -3 .ai-docs/_todo.txt >> .ai-docs/_done.txt

# 从 _todo.txt 删除已处理的行
tail -n +4 .ai-docs/_todo.txt > .ai-docs/_todo.tmp && mv .ai-docs/_todo.tmp .ai-docs/_todo.txt
```

更新 `_progress.md`，在批次表格中添加一行，包含 imports 提取数和 usages 提取数。

#### 步骤 2.6：检查是否继续

```bash
if [ -s .ai-docs/_todo.txt ]; then
  echo "还有文件待处理，继续执行..."
  # 【必须】返回步骤 2.1
else
  echo "所有文件处理完成，进入汇总阶段"
  # 进入阶段 3
fi
```

#### 步骤 2.7：向用户报告进度

每完成 5 个批次（15 个文件），输出一次进度：

```
批次 {N} 完成
已处理：{已处理数} / {总数} ({百分比}%)
本轮提取：{imports数} 个 import, {usages数} 个使用记录
质量校验：全部通过
```

---

## 非 JSX 文件的简化处理

以下类型的文件可以简化分析（但仍必须 Read 并记录 imports）：

| 文件类型 | 特征 | 分析要求 |
|----------|------|----------|
| 纯类型文件 | `.d.ts`、`type.ts`、`types.ts`、`interface.ts` | 只记录 imports，不需要提取使用 |
| 常量文件 | `constants.ts`、`enum.ts` | 记录 imports + 导出的常量名 |
| 样式文件 | `.less`、`.css`（不在扫描范围内） | 跳过 |
| API 文件 | `api.ts`、`service.ts` | 记录 imports + 使用的请求工具 |
| 纯 .ts 工具文件 | `utils.ts`、`helper.ts` | 记录 imports + 导出的函数签名 |
| .tsx/.jsx 文件 | 包含 JSX | **必须完整分析所有组件使用** |

对于 .ts（非 .tsx）文件，如果确实没有组件使用，componentUsages 为空是合理的，但必须：
- `imports` 数组仍然必须填写
- `hookUsages` 和 `utilUsages` 仍然需要检查

---

## 阶段 3：汇总数据（仅当 _todo.txt 为空时执行）

### 前置检查

```bash
if [ -s .ai-docs/_todo.txt ]; then
  echo "错误：还有文件未处理，不能进入汇总阶段"
  # 必须返回阶段 2
fi
```

### 步骤 3.1：使用脚本汇总所有批次数据

使用 Python 脚本读取所有 batch JSON 并汇总（不要手动读取再凭印象总结）：

```bash
python3 -c "
import json, glob, os
from collections import defaultdict

batch_files = sorted(glob.glob('.ai-docs/_batches/batch_*.json'))

# 汇总结构
scenarios = defaultdict(lambda: {'files': [], 'components': set(), 'hooks': set()})
component_index = defaultdict(lambda: {
    'importFrom': '', 'usages': [], 'props_union': set(), 'scenarios': set()
})
hook_index = defaultdict(lambda: {
    'importFrom': '', 'usages': [], 'scenarios': set()
})
util_index = defaultdict(lambda: {
    'importFrom': '', 'usages': []
})

total_files = 0
total_usages = 0

for bf in batch_files:
    with open(bf) as f:
        data = json.load(f)
    for file_info in data.get('files', []):
        total_files += 1
        fp = file_info['filePath']
        scenario_type = file_info.get('scenario', {}).get('type', 'other')
        scenario_desc = file_info.get('scenario', {}).get('description', '')

        scenarios[scenario_type]['files'].append(fp)

        for cu in file_info.get('componentUsages', []):
            name = cu['name']
            total_usages += 1
            component_index[name]['importFrom'] = cu.get('importFrom', '')
            component_index[name]['usages'].append({
                'filePath': fp,
                'scenario': scenario_type,
                'code': cu.get('code', ''),
                'props': cu.get('props', []),
                'description': cu.get('description', '')
            })
            component_index[name]['props_union'].update(cu.get('props', []))
            component_index[name]['scenarios'].add(scenario_type)
            scenarios[scenario_type]['components'].add(name)

        for hu in file_info.get('hookUsages', []):
            name = hu['name']
            total_usages += 1
            hook_index[name]['importFrom'] = hu.get('importFrom', '')
            hook_index[name]['usages'].append({
                'filePath': fp,
                'scenario': scenario_type,
                'code': hu.get('code', ''),
                'description': hu.get('description', '')
            })
            hook_index[name]['scenarios'].add(scenario_type)
            scenarios[scenario_type]['hooks'].add(name)

        for uu in file_info.get('utilUsages', []):
            name = uu['name']
            total_usages += 1
            util_index[name]['importFrom'] = uu.get('importFrom', '')
            util_index[name]['usages'].append({
                'filePath': fp,
                'code': uu.get('code', ''),
                'description': uu.get('description', '')
            })

# 转为可序列化格式
result = {
    'stats': {
        'totalFiles': total_files,
        'totalUsages': total_usages,
        'uniqueComponents': len(component_index),
        'uniqueHooks': len(hook_index),
        'uniqueUtils': len(util_index),
    },
    'scenarios': {k: {
        'description': '',
        'files': v['files'],
        'components': sorted(v['components']),
        'hooks': sorted(v['hooks'])
    } for k, v in scenarios.items()},
    'componentIndex': {k: {
        'importFrom': v['importFrom'],
        'usageCount': len(v['usages']),
        'allProps': sorted(v['props_union']),
        'scenarios': sorted(v['scenarios']),
        'usages': v['usages']
    } for k, v in sorted(component_index.items(), key=lambda x: -len(x[1]['usages']))},
    'hookIndex': {k: {
        'importFrom': v['importFrom'],
        'usageCount': len(v['usages']),
        'scenarios': sorted(v['scenarios']),
        'usages': v['usages']
    } for k, v in sorted(hook_index.items(), key=lambda x: -len(x[1]['usages']))},
    'utilIndex': {k: {
        'importFrom': v['importFrom'],
        'usageCount': len(v['usages']),
        'usages': v['usages']
    } for k, v in sorted(util_index.items(), key=lambda x: -len(x[1]['usages']))}
}

with open('.ai-docs/_aggregated.json', 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f'汇总完成：')
print(f'  文件总数: {total_files}')
print(f'  使用记录总数: {total_usages}')
print(f'  独立组件数: {len(component_index)}')
print(f'  独立 Hook 数: {len(hook_index)}')
print(f'  独立工具函数数: {len(util_index)}')

# 输出 Top 20 组件
print(f'\\nTop 20 高频组件:')
for name, info in sorted(component_index.items(), key=lambda x: -len(x[1]['usages']))[:20]:
    print(f'  {name}: {len(info[\"usages\"])}次, from {info[\"importFrom\"]}')
"
```

### 步骤 3.2：验证汇总数据

```bash
python3 -c "
import json
with open('.ai-docs/_aggregated.json') as f:
    data = json.load(f)
stats = data['stats']
print(f'汇总验证:')
print(f'  totalFiles: {stats[\"totalFiles\"]}')
print(f'  totalUsages: {stats[\"totalUsages\"]}')
print(f'  uniqueComponents: {stats[\"uniqueComponents\"]}')

# 基本合理性检查
if stats['totalUsages'] < stats['totalFiles'] * 0.5:
    print(f'  警告: 平均每文件使用记录不足 0.5 条，可能存在分析遗漏')
if stats['uniqueComponents'] < 20:
    print(f'  警告: 独立组件数不足 20，对于中大型项目可能偏少')
"
```

---

## 阶段 4：生成最终文档

**核心规则：所有文档内容必须从 `_aggregated.json` 中读取数据生成，严禁凭记忆或印象编写。**

### 步骤 4.0：读取汇总数据

先 Read 读取 `.ai-docs/_aggregated.json`，将其内容作为后续所有文档生成的数据源。

### 步骤 4.1：生成 COMPONENT-SELECTOR.md（组件选择器）

从 `_aggregated.json` 的 `componentIndex` 中：
- 按 `usageCount` 降序排列
- 按类别分组
- 为每个组件列出：名称、来源、使用次数、所有 props、适用场景

组件分类规则：

| 分类     | 关键词                                       |
| -------- | -------------------------------------------- |
| 表格类   | Table, List, Grid, DataView                  |
| 表单类   | Form, Input, Select, DatePicker, Upload      |
| 弹窗类   | Modal, Drawer, Popover, Popconfirm           |
| 布局类   | Row, Col, Space, Flex, Layout, Card          |
| 导航类   | Menu, Tabs, Breadcrumb, Steps                |
| 反馈类   | Alert, Message, Notification, Spin, Skeleton |
| 数据展示 | Descriptions, Statistic, Tag, Badge          |
| 富文本   | Editor, TinyEditor, RichText, Markdown       |
| 业务组件 | 其他                                         |

模板：

```markdown
# 组件选择器

> 基于 {totalFiles} 个文件的全量分析，提取了 {uniqueComponents} 个组件的 {totalUsages} 条使用记录。

## 按场景选择

### 列表页
| 组件 | 来源 | 使用次数 | 可用 Props | 说明 |
|------|------|----------|-----------|------|
| {name} | {importFrom} | {usageCount} | {allProps} | {description} |

### 表单页
...

### 弹窗
...

## 全部组件索引

| 组件 | 来源 | 使用次数 | 类别 | 详细文档 |
|------|------|----------|------|----------|
| {name} | {importFrom} | {usageCount} | {category} | [查看](components/{name}.md) |
```

### 步骤 4.2：为每个组件生成独立文档

**条件**：`usageCount >= 1` 的所有组件都生成独立文档（不仅仅是 >= 3）。

文件路径：`.ai-docs/components/{ComponentName}.md`

内容必须从 `_aggregated.json` 的 `componentIndex[name].usages` 数组中提取：

````markdown
# {ComponentName}

## 基本信息

| 属性 | 值 |
|------|------|
| 来源 | `{importFrom}` |
| 使用次数 | {usageCount} |
| 适用场景 | {scenarios} |
| 所有已知 Props | {allProps} |

## 使用示例

### 示例 1：{description}

**来源**：`{filePath}`
**场景**：{scenario}

```tsx
{code}
```

### 示例 2：...
（列出所有 usages，不要省略）
````

### 步骤 4.3：为 Hook 生成文档

文件路径：`.ai-docs/hooks/{HookName}.md`

### 步骤 4.4：生成场景文档

文件路径：`.ai-docs/scenarios/{scenario_type}.md`

从 `_aggregated.json` 的 `scenarios` 中提取，列出该场景下的所有文件、使用的组件和 Hook。

### 步骤 4.5：生成 DEV-GUIDE.md（开发手册入口）

汇总所有信息的入口文档，包含：
- 项目概览（技术栈、目录结构）
- 核心组件使用指南（从 componentIndex 中取 Top 10 高频组件，附带真实使用代码）
- 页面开发模式（从 scenarios 中总结）
- Hook 使用指南（从 hookIndex 中取高频 Hook）
- 工具函数索引（从 utilIndex 中取）
- 业务模块索引

**再次强调**：所有示例代码必须从 `_aggregated.json` 的 usages 中复制，不允许自行编写示例代码。

### 步骤 4.6：生成 inventory.md（物资清单）

列出所有发现的组件、Hook、工具函数的完整清单。

---

## 断点续传说明

如果分析过程中断：

1. 下次运行时，检测到 `_todo.txt` 存在且不为空
2. 自动进入断点续传模式
3. 跳过阶段 1，直接进入阶段 2
4. 从 `_todo.txt` 剩余的文件继续分析

如果想重新开始：

```bash
rm -rf .ai-docs/_todo.txt .ai-docs/_done.txt .ai-docs/_batches/ .ai-docs/_errors.txt
```

---

## 完成标志

当以下条件全部满足时，分析完成：

- [ ] `_todo.txt` 为空或不存在
- [ ] `_done.txt` 行数等于总文件数
- [ ] `_aggregated.json` 已生成且 `totalUsages > 0`
- [ ] `COMPONENT-SELECTOR.md` 已生成
- [ ] 每个组件都有独立文档（在 `components/` 目录下）
- [ ] `DEV-GUIDE.md` 中的所有示例代码都来自 `_aggregated.json`

---

## 错误处理

### Token 不足

如果 Token 即将耗尽：

1. 完成当前批次的保存和质量校验
2. 更新 `_progress.md`
3. 告知用户当前进度和剩余文件数
4. **不要跳过文件**

用户下次运行时会从断点继续。

### 文件读取失败

如果某个文件读取失败：

1. 将该文件路径追加到 `_errors.txt`
2. 在 `_progress.md` 中记录错误
3. 继续处理其他文件

### 质量校验失败

如果批次质量校验失败：

1. 删除该批次 JSON
2. 重新读取并分析这 3 个文件
3. 重新校验
4. 如果连续 3 次失败，将失败文件记入 `_errors.txt` 并跳过

---

## 严禁的做法

- 不要在 `_todo.txt` 不为空时进入阶段 3
- 不要跳过任何文件（"这个文件不重要"）
- 不要采样分析（"分析前 100 个文件就够了"）
- 不要把组件"定义代码"当作"使用示例"
- 不要忽略第三方组件（antd、自定义库等）
- 不要在没有 Read 文件的情况下填写分析结果
- 不要在 componentUsages 中省略 Grep 预提取发现的有效 import 对应的使用
- 不要在最终文档中编写未出现在 `_aggregated.json` 中的示例代码
- 不要在 imports 数组中遗漏 Grep 提取到的 import 行

## 正确的做法

- 每个文件先 Grep 提取 import，再 Read 完整内容，再对照分析
- 每批 3 个文件，逐文件处理
- 每批次写入后执行质量校验脚本
- 校验失败必须重做，不能跳过
- 最终文档 100% 基于 `_aggregated.json` 生成
- 所有示例代码都是从真实文件中提取的使用代码
