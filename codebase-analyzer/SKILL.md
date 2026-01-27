---
name: codebase-analyzer
description: 深度分析项目代码库，生成完整的开发指导手册。使用 LLM 理解每个文件，通过多代理协作支持任意规模代码库分析，提取所有组件/库/Hook 的使用示例，输出数据驱动的 Markdown 开发手册。当用户请求"分析项目"、"生成开发手册"、"了解项目结构"、"提取编码规范"、"分析代码库"时使用此技能。
---

# Codebase Analyzer

分析项目代码库，生成数据驱动的开发指导手册，包含场景索引和组件选择器。

## 核心原则

1. **强制全量分析**：每个文件都必须被读取和分析，不允许采样或跳过
2. **销项机制**：使用待办列表文件追踪进度，处理完一批就物理删除，确保不遗漏
3. **断点续传**：支持中断后继续，从上次停止的地方恢复
4. **收集使用示例**：重点是"组件如何被使用"，而非"组件如何被定义"

---

## ⚠️ 强制执行规则（严禁违反）

```
本 Skill 的核心约束：

1. 必须处理 _todo.txt 中的每一个文件，不允许跳过
2. 每处理完一批文件，必须从 _todo.txt 中删除对应行
3. 只有当 _todo.txt 为空时，才能进入文档生成阶段
4. 不允许"采样分析"或"选择性分析"
5. 如果 Token 不足，应该停止并告知用户，而不是跳过文件
```

---

## 工作目录结构

所有中间文件存储在 `.ai-docs/` 目录：

```
.ai-docs/
├── _todo.txt              # 待处理文件列表（销项清单）
├── _done.txt              # 已处理文件列表（断点续传用）
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
# 检查 _todo.txt 是否存在且不为空
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
mkdir -p .ai-docs/_batches
```

---

## 阶段 1：创建待办列表（全新分析时执行）

### 步骤 1.1：扫描所有代码文件

使用 Glob 工具扫描，排除以下目录：

- `node_modules/`
- `dist/` / `build/` / `.next/` / `.nuxt/`
- `.git/`
- `coverage/`
- `.umi/`
- `.ai-docs/`

扫描模式：

```
src/**/*.{ts,tsx,js,jsx,vue,svelte}
```

如果没有 `src` 目录，扫描项目根目录。

### 步骤 1.2：写入待办列表

将所有文件路径写入 `.ai-docs/_todo.txt`，每行一个文件：

```
src/pages/user/list.tsx
src/pages/user/detail.tsx
src/pages/order/list.tsx
src/components/Button.tsx
src/hooks/useRequest.ts
...
```

### 步骤 1.3：初始化进度报告

创建 `.ai-docs/_progress.md`：

```markdown
# 代码分析进度报告

开始时间：{当前时间}
总文件数：{文件数量}
已完成：0
待处理：{文件数量}

## 批次记录

| 批次 | 文件数 | 状态 | 完成时间 |
| ---- | ------ | ---- | -------- |
```

### 步骤 1.4：清空已完成列表

```bash
> .ai-docs/_done.txt
```

---

## 阶段 2：批次化分析（死循环，严禁跳过）

### ⚠️ 核心约束

```
【死循环规则】

执行以下步骤，直到 _todo.txt 为空：

1. 读取 _todo.txt
2. 如果有内容：
   a. 取前 10 行（10个文件）
   b. 读取并分析这 10 个文件
   c. 将结果写入 _batches/batch_XXX.json
   d. 将这 10 行追加到 _done.txt
   e. 从 _todo.txt 删除这 10 行
   f. 更新 _progress.md
   g. 【必须】返回步骤 1，继续循环
3. 如果为空：
   → 才能进入阶段 3

【严禁】在 _todo.txt 不为空时进入阶段 3
【严禁】跳过任何文件
【严禁】采样分析
```

### 步骤 2.1：读取待办列表

```bash
# 读取前 10 行
head -10 .ai-docs/_todo.txt
```

### 步骤 2.2：分析文件批次

对于取出的 10 个文件，逐个使用 Read 工具读取，然后分析：

**分析任务**：

1. **识别页面场景**：根据文件路径和内容判断
   - list（列表页）
   - detail（详情页）
   - form（表单页）
   - modal（弹窗）
   - other（其他）

2. **提取组件使用**（重点！）：
   - 找出 JSX 中使用的所有组件
   - 提取使用代码片段（不是整个函数）
   - 记录使用的 props
   - 标注 import 来源

3. **提取 Hook 使用**：
   - 找出所有 Hook 调用
   - 提取调用代码和返回值解构

4. **提取工具函数使用**

### ⚠️ 关键区分：定义 vs 使用

```tsx
// ❌ 这是"定义" - 不是我们要收集的重点
export const TableTemplatePro = (props) => { ... }

// ✅ 这是"使用" - 这才是我们要收集的示例
<TableTemplatePro
  columns={columns}
  fetchPageUrl="/api/list"
  rowKey="id"
/>
```

### 步骤 2.3：保存批次结果

将分析结果写入 `.ai-docs/_batches/batch_XXX.json`：

```json
{
  "batchId": 1,
  "timestamp": "2024-01-27T10:30:00Z",
  "files": [
    {
      "filePath": "src/pages/user/list.tsx",
      "scenario": {
        "type": "list",
        "description": "用户列表页"
      },
      "componentUsages": [
        {
          "name": "TableTemplatePro",
          "importFrom": "@dzg/gm-template",
          "code": "<TableTemplatePro\n  title=\"用户列表\"\n  fetchPageUrl=\"/api/user/list\"\n  columns={columns}\n  rowKey=\"id\"\n/>",
          "props": ["title", "fetchPageUrl", "columns", "rowKey"],
          "description": "带分页的用户列表"
        }
      ],
      "hookUsages": [
        {
          "name": "useRequest",
          "importFrom": "ahooks",
          "code": "const { loading, data, run } = useRequest(fetchUser, { manual: true });",
          "description": "手动触发请求"
        }
      ],
      "utilUsages": []
    }
  ]
}
```

### 步骤 2.4：更新进度文件

**追加到 \_done.txt**：

```bash
# 将已处理的文件追加到 _done.txt
head -10 .ai-docs/_todo.txt >> .ai-docs/_done.txt
```

**从 \_todo.txt 删除已处理的行**：

```bash
# 删除前 10 行
sed -i '' '1,10d' .ai-docs/_todo.txt  # macOS
# 或
sed -i '1,10d' .ai-docs/_todo.txt     # Linux
```

或者使用更可靠的方式：

```bash
tail -n +11 .ai-docs/_todo.txt > .ai-docs/_todo.tmp && mv .ai-docs/_todo.tmp .ai-docs/_todo.txt
```

**更新 \_progress.md**：

在批次记录表格中添加一行，更新统计数字。

### 步骤 2.5：检查是否继续

```bash
# 检查 _todo.txt 是否还有内容
if [ -s .ai-docs/_todo.txt ]; then
  echo "还有文件待处理，继续执行..."
  # 【必须】返回步骤 2.1
else
  echo "所有文件处理完成，进入汇总阶段"
  # 进入阶段 3
fi
```

### 步骤 2.6：向用户报告进度

每完成一个批次，输出当前进度：

```
📊 批次 {N} 完成
已处理：{已处理数} / {总数} ({百分比}%)
当前批次文件：
  - src/pages/user/list.tsx ✓
  - src/pages/user/detail.tsx ✓
  ...
```

---

## 阶段 3：汇总数据（仅当 \_todo.txt 为空时执行）

### 前置检查

```bash
# 必须检查！
if [ -s .ai-docs/_todo.txt ]; then
  echo "❌ 错误：还有文件未处理，不能进入汇总阶段"
  exit 1
fi
```

### 步骤 3.1：读取所有批次结果

```bash
ls .ai-docs/_batches/*.json
```

读取每个 batch_XXX.json 文件。

### 步骤 3.2：合并数据

创建 `.ai-docs/_aggregated.json`，包含：

```json
{
  "scenarios": {
    "list": {
      "description": "列表页场景",
      "files": ["src/pages/user/list.tsx", ...],
      "components": ["TableTemplatePro", ...],
      "hooks": ["useRequest", ...]
    }
  },
  "componentIndex": {
    "TableTemplatePro": {
      "category": "表格类",
      "importFrom": "@dzg/gm-template",
      "usageCount": 61,
      "scenarios": ["list"],
      "alternatives": ["Table", "ProTable"],
      "usages": [
        {
          "filePath": "src/pages/user/list.tsx",
          "scenario": "list",
          "code": "...",
          "props": [...],
          "description": "..."
        }
      ]
    }
  },
  "hookIndex": {...},
  "utilIndex": {...}
}
```

### 组件分类规则

| 分类     | 关键词                                       |
| -------- | -------------------------------------------- |
| 表格类   | Table, List, Grid, DataView                  |
| 表单类   | Form, Input, Select, DatePicker, Upload      |
| 弹窗类   | Modal, Drawer, Popover, Popconfirm           |
| 布局类   | Row, Col, Space, Flex, Layout, Card          |
| 导航类   | Menu, Tabs, Breadcrumb, Steps                |
| 反馈类   | Alert, Message, Notification, Spin, Skeleton |
| 数据展示 | Descriptions, Statistic, Tag, Badge          |
| 业务组件 | 其他                                         |

---

## 阶段 4：生成最终文档

基于 `_aggregated.json` 生成用户可用的文档。

### 4.1 生成 COMPONENT-SELECTOR.md（最重要）

帮助 AI 根据 PRD 需求选择合适组件：

```markdown
# 组件选择器

> 根据开发需求快速找到合适的组件。

## 按场景选择

### 我要开发列表页

| 需求         | 推荐组件         | 使用频率 | 特点           | 文档                                   |
| ------------ | ---------------- | -------- | -------------- | -------------------------------------- |
| 标准数据列表 | TableTemplatePro | 61次     | 内置分页、搜索 | [查看](components/TableTemplatePro.md) |
| 简单表格     | Table            | 54次     | Antd 原生      | [查看](components/Table.md)            |

**选择建议**：

- 管理后台 → TableTemplatePro
- 简单展示 → Table

### 我要开发表单页

...

## 同类组件对比

### 表格组件对比

| 组件             | 来源             | 内置搜索 | 内置分页 | 适用场景 |
| ---------------- | ---------------- | -------- | -------- | -------- |
| TableTemplatePro | @dzg/gm-template | ✅       | ✅       | 管理后台 |
| Table            | antd             | ❌       | 手动     | 简单展示 |
```

### 4.2 生成组件文档

为每个使用超过 3 次的组件生成 `components/XXX.md`：

````markdown
# TableTemplatePro

> 企业级表格模板组件

## 基本信息

| 属性     | 值                 |
| -------- | ------------------ |
| 来源     | `@dzg/gm-template` |
| 使用频率 | 61 次              |
| 适用场景 | 列表页             |

## 使用示例

### 示例 1：基础列表

**来源**：`src/pages/user/list.tsx`

```tsx
<TableTemplatePro
  title="用户列表"
  fetchPageUrl="/api/user/list"
  columns={columns}
  rowKey="id"
/>
```
````

### 示例 2：复杂配置

...

````

### 4.3 生成场景文档

为每个场景生成 `scenarios/XXX.md`。

### 4.4 生成 inventory.md 和 DEV-GUIDE.md

---

## 断点续传说明

如果分析过程中断：

1. 下次运行时，skill 检测到 `_todo.txt` 存在且不为空
2. 自动进入断点续传模式
3. 跳过阶段 1，直接进入阶段 2
4. 从 `_todo.txt` 剩余的文件继续分析

如果想重新开始：
```bash
rm -rf .ai-docs/_todo.txt .ai-docs/_done.txt .ai-docs/_batches/
````

---

## 完成标志

当以下条件满足时，分析完成：

- [ ] `_todo.txt` 为空或不存在
- [ ] `_done.txt` 包含所有代码文件
- [ ] `_batches/` 包含所有批次结果
- [ ] `COMPONENT-SELECTOR.md` 已生成
- [ ] 每个高频组件都有独立文档

---

## 错误处理

### Token 不足

如果 Token 即将耗尽：

1. 完成当前批次的保存
2. 更新 `_progress.md`
3. 告知用户当前进度
4. **不要跳过文件**

用户下次运行时会从断点继续。

### 文件读取失败

如果某个文件读取失败：

1. 在 `_progress.md` 中记录错误
2. 将该文件移到 `_errors.txt`
3. 继续处理其他文件

---

## 检查清单

执行完成前，确认：

- [ ] `_todo.txt` 为空（所有文件已处理）
- [ ] `COMPONENT-SELECTOR.md` 存在且内容完整
- [ ] 每个使用超过 3 次的组件都有文档
- [ ] 每个场景都有文档
- [ ] 示例代码是"使用代码"，不是"定义代码"

---

## ⚠️ 严禁的做法

- ❌ 在 `_todo.txt` 不为空时进入阶段 3
- ❌ 跳过任何文件（"这个文件不重要"）
- ❌ 采样分析（"分析前 100 个文件就够了"）
- ❌ 把组件"定义代码"当作"使用示例"
- ❌ 忽略第三方组件（antd、自定义库等）

## ✅ 正确的做法

- ✅ 严格按照死循环规则执行，直到 `_todo.txt` 为空
- ✅ 每批处理后物理删除已处理的行
- ✅ 收集组件在其他文件中的使用代码
- ✅ 为所有使用过的组件生成文档
- ✅ 按场景组织，帮助 AI 选择组件
