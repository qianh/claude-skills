---
name: codebase-analyzer
description: 深度分析项目代码库，生成完整的开发指导手册。使用 LLM 理解每个文件，通过多代理协作支持任意规模代码库分析，提取所有组件/库/Hook 的使用示例，输出数据驱动的 Markdown 开发手册。当用户请求"分析项目"、"生成开发手册"、"了解项目结构"、"提取编码规范"、"分析代码库"时使用此技能。
---

# Codebase Analyzer

分析项目代码库，生成数据驱动的开发指导手册，包含场景索引和组件选择器。

## 核心原则

1. **收集使用示例，而非组件定义**：重点是"组件如何被使用"，而非"组件如何被定义"
2. **场景驱动**：按页面类型（列表页、表单页、详情页等）组织组件，帮助 AI 根据 PRD 选择合适组件
3. **全量覆盖**：所有被使用的组件、Hook、工具都必须有使用示例，无论使用频率高低
4. **多代理协作**：通过批次化分析支持任意规模代码库

---

## 阶段 0：规模评估（强制执行）

**在所有分析开始前，必须先执行规模评估。**

### 步骤

1. 统计代码文件数量：

```bash
find src -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.vue" \) | wc -l
```

如果没有 `src` 目录，使用项目根目录：

```bash
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.vue" \) -not -path "*/node_modules/*" -not -path "*/.git/*" | wc -l
```

2. **根据规模确定批次策略**：

| 文件数 | 批次大小 | 汇总层级 |
| ------ | -------- | -------- |
| < 50   | 逐个读取 | 单层汇总 |
| 50-200 | 10 个/批 | 单层汇总 |
| 200+   | 20 个/批 | 多层汇总 |

---

## 阶段 1：全量扫描

使用 Glob 工具获取所有代码文件列表，排除以下目录：

- `node_modules/`
- `dist/` / `build/` / `.next/` / `.nuxt/`
- `.git/`
- `coverage/`
- `.umi/`（Umi 生成文件）

### 扫描命令

```
**/*.{ts,tsx,js,jsx,vue,svelte}
```

---

## 阶段 2：批次化分析（多代理协作）

**关键原则**：提取每个文件中"使用了哪些组件/Hook"以及"如何使用的代码片段"。

### ⚠️ 核心区分：定义 vs 使用

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

### 子代理任务模板

```
请分析以下文件批次，返回结构化汇总：

文件列表：
- src/pages/user/list.tsx
- src/pages/order/detail.tsx
- ...

分析任务：

1. **识别页面场景**：根据文件路径和内容判断页面类型
   - 列表页（list/index + 表格组件）
   - 详情页（detail + 描述/卡片组件）
   - 表单页（form/add/edit + 表单组件）
   - 弹窗组件（Modal/Drawer）
   - 其他

2. **提取组件使用**：找出 JSX 中使用的所有组件，提取使用代码片段
   - 包含完整的 props 配置
   - 代码片段应该能独立理解
   - 优先提取配置丰富、有代表性的使用

3. **提取 Hook 使用**：找出所有 Hook 调用，提取使用代码片段
   - 包含 Hook 的参数和返回值解构
   - 包含 Hook 结果的实际使用

4. **提取工具函数使用**：找出所有工具函数调用

返回格式（JSON）：
{
  "filePath": "src/pages/user/list.tsx",
  "scenario": {
    "type": "list",  // list | detail | form | modal | other
    "description": "用户列表页，支持搜索、分页、批量操作"
  },
  "componentUsages": [
    {
      "name": "TableTemplatePro",
      "importFrom": "@dzg/gm-template",
      "code": "<TableTemplatePro\n  title=\"用户列表\"\n  fetchPageUrl=\"/api/user/list\"\n  columns={columns}\n  rowKey=\"id\"\n  displayHeader={true}\n  tableOperations={buttonList}\n/>",
      "props": ["title", "fetchPageUrl", "columns", "rowKey", "displayHeader", "tableOperations"],
      "description": "带搜索和批量操作的用户列表"
    },
    {
      "name": "Modal",
      "importFrom": "antd",
      "code": "<Modal\n  visible={visible}\n  title=\"编辑用户\"\n  onOk={handleSubmit}\n  onCancel={handleClose}\n>\n  <Form>...</Form>\n</Modal>",
      "props": ["visible", "title", "onOk", "onCancel"],
      "description": "编辑用户的弹窗表单"
    }
  ],
  "hookUsages": [
    {
      "name": "useRequest",
      "importFrom": "ahooks",
      "code": "const { loading, data, run } = useRequest(getUserList, {\n  manual: true,\n  debounceInterval: 500\n});",
      "description": "手动触发的防抖请求"
    }
  ],
  "utilUsages": [
    {
      "name": "formatDate",
      "importFrom": "@/utils/date",
      "code": "formatDate(record.createTime, 'YYYY-MM-DD HH:mm')",
      "description": "格式化日期时间"
    }
  ]
}

**重要规则**：
1. 只收集"使用"代码，不收集"定义"代码
2. 代码片段必须是实际的 JSX 或调用代码，不是整个函数
3. 代码片段应该简洁但完整，能独立理解
4. 每个组件/Hook 在同一文件中可能有多个不同用法，都要收集
5. 必须标注 importFrom 来源
```

### 批次分配策略

| 文件数   | 每批文件数 | 说明               |
| -------- | ---------- | ------------------ |
| < 50     | 逐个处理   | 每个文件单独分析   |
| 50-200   | 10 个/批   | 平衡速度和准确性   |
| 200+     | 20 个/批   | 高效处理大规模项目 |

---

## 阶段 3：汇总与分类

### 汇总数据结构

```json
{
  "scenarios": {
    "list": {
      "description": "列表页场景",
      "files": ["src/pages/user/list.tsx", "src/pages/order/list.tsx"],
      "components": ["TableTemplatePro", "SearchForm", "BatchOperation"],
      "hooks": ["useRequest", "useState"]
    },
    "form": {
      "description": "表单页场景",
      "files": ["src/pages/user/add.tsx"],
      "components": ["Form", "DzgForm", "Select"],
      "hooks": ["useForm", "useRequest"]
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
          "props": ["title", "fetchPageUrl", "columns"],
          "description": "用户列表页"
        }
      ]
    }
  },
  "hookIndex": {
    "useRequest": {
      "importFrom": "ahooks",
      "usageCount": 45,
      "scenarios": ["list", "form", "detail"],
      "usages": [...]
    }
  }
}
```

### 组件分类规则

根据组件名称和使用场景自动分类：

| 分类     | 关键词                                       |
| -------- | -------------------------------------------- |
| 表格类   | Table, List, Grid, DataView                  |
| 表单类   | Form, Input, Select, DatePicker, Upload      |
| 弹窗类   | Modal, Drawer, Popover, Popconfirm           |
| 布局类   | Row, Col, Space, Flex, Layout, Card          |
| 导航类   | Menu, Tabs, Breadcrumb, Steps                |
| 反馈类   | Alert, Message, Notification, Spin, Skeleton |
| 数据展示 | Descriptions, Statistic, Tag, Badge          |
| 业务组件 | 其他自定义组件                               |

### 场景识别规则

| 场景     | 识别规则                                             |
| -------- | ---------------------------------------------------- |
| list     | 路径含 list/index + 使用表格组件                     |
| detail   | 路径含 detail + 使用 Descriptions/Card               |
| form     | 路径含 form/add/edit/create + 使用表单组件           |
| modal    | 文件导出 Modal 组件或主要内容是 Modal                |
| dashboard| 路径含 dashboard/home + 使用统计/图表组件            |

---

## 阶段 4：生成文档

### 输出目录结构

```
.ai-docs/
├── DEV-GUIDE.md              # 开发手册总入口
├── COMPONENT-SELECTOR.md     # 组件选择器（帮助 AI 选择组件）
├── inventory.md              # 完整物资清单
├── scenarios/                # 场景文档
│   ├── list.md              # 列表页开发指南
│   ├── form.md              # 表单页开发指南
│   ├── detail.md            # 详情页开发指南
│   └── modal.md             # 弹窗开发指南
├── components/               # 组件使用文档
│   ├── TableTemplatePro.md
│   ├── Form.md
│   └── ...
├── hooks/                    # Hook 使用文档
│   ├── useRequest.md
│   └── ...
└── utils/                    # 工具函数文档
    ├── formatDate.md
    └── ...
```

### 文档模板

#### 1. 组件选择器（COMPONENT-SELECTOR.md）

**这是最重要的文档，帮助 AI 根据 PRD 需求选择合适的组件。**

```markdown
# 组件选择器

> 根据开发需求快速找到合适的组件。本文档按场景和功能分类，帮助你在开发新功能时选择正确的组件。

## 按场景选择

### 我要开发列表页

| 需求 | 推荐组件 | 使用频率 | 特点 | 文档 |
| --- | --- | --- | --- | --- |
| 标准数据列表 | TableTemplatePro | 61次 | 内置分页、搜索、批量操作 | [查看](components/TableTemplatePro.md) |
| 简单表格 | Table | 54次 | Antd 原生表格，需手动处理分页 | [查看](components/Table.md) |
| 虚拟滚动大数据 | VirtualTable | 3次 | 适合 1000+ 行数据 | [查看](components/VirtualTable.md) |

**选择建议**：
- 管理后台列表页 → TableTemplatePro（首选）
- 简单展示表格 → Table
- 大数据量 → VirtualTable

### 我要开发表单页

| 需求 | 推荐组件 | 使用频率 | 特点 | 文档 |
| --- | --- | --- | --- | --- |
| 标准表单 | Form + Form.Item | 115次 | Antd 原生表单 | [查看](components/Form.md) |
| 动态表单 | DzgForm | 30次 | 支持 JSON Schema 配置 | [查看](components/DzgForm.md) |

### 我要开发详情页

...

### 我要开发弹窗

...

## 按功能选择

### 数据请求

| 需求 | 推荐 Hook | 使用频率 | 特点 | 文档 |
| --- | --- | --- | --- | --- |
| 普通请求 | useRequest | 45次 | 支持 loading、防抖、轮询 | [查看](hooks/useRequest.md) |
| 表格数据 | useAntdTable | 12次 | 专为表格设计，自动分页 | [查看](hooks/useAntdTable.md) |

### 状态管理

...

### 权限控制

| 需求 | 推荐组件 | 使用频率 | 特点 | 文档 |
| --- | --- | --- | --- | --- |
| 按钮权限 | PermissionWrapper | 54次 | 包裹需要权限控制的元素 | [查看](components/PermissionWrapper.md) |

## 同类组件对比

### 表格组件对比

| 组件 | 来源 | 内置搜索 | 内置分页 | 批量操作 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| TableTemplatePro | @dzg/gm-template | ✅ | ✅ | ✅ | 管理后台列表页 |
| Table | antd | ❌ | 手动 | ❌ | 简单数据展示 |
| ProTable | @ant-design/pro-table | ✅ | ✅ | ✅ | 通用管理后台 |

### 表单组件对比

| 组件 | 来源 | 动态字段 | 校验 | 布局 | 适用场景 |
| --- | --- | --- | --- | --- | --- |
| Form | antd | 手动 | ✅ | 灵活 | 自定义表单 |
| DzgForm | @dzg/dzg-form | ✅ JSON | ✅ | 固定 | 配置化表单 |
```

#### 2. 场景文档模板（scenarios/list.md）

```markdown
# 列表页开发指南

> 本文档介绍如何开发列表页，包含推荐组件、代码模式和完整示例。

## 推荐技术栈

| 功能 | 组件/Hook | 文档 |
| --- | --- | --- |
| 表格 | TableTemplatePro | [查看](../components/TableTemplatePro.md) |
| 数据请求 | useRequest | [查看](../hooks/useRequest.md) |
| 批量操作 | BatchOperation | [查看](../components/BatchOperation.md) |
| 权限控制 | PermissionWrapper | [查看](../components/PermissionWrapper.md) |

## 完整示例

### 示例 1：标准列表页（用户管理）

**来源**：`src/pages/user/list.tsx`

```tsx
import { TableTemplatePro } from '@dzg/gm-template';
import { PermissionWrapper } from '@/components/PermissionWrapper';

const UserList: React.FC = () => {
  const tableRef = useRef<any>(null);
  const [selectedRows, setSelectedRows] = useState<any[]>([]);

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ];

  const buttonList = [
    <PermissionWrapper key="add" permission="user:add">
      <Button type="primary" onClick={() => handleAdd()}>新增</Button>
    </PermissionWrapper>,
    <Button key="export" onClick={() => handleExport()}>导出</Button>,
  ];

  return (
    <TableTemplatePro
      ref={tableRef}
      title="用户列表"
      columns={columns}
      fetchPageUrl="/api/user/list"
      rowKey="id"
      displayHeader={true}
      displayCommonSetting={true}
      tableOperations={buttonList}
      onSelectChange={({ selectedRows }) => setSelectedRows(selectedRows)}
    />
  );
};
```

### 示例 2：带复杂筛选的列表页

**来源**：`src/pages/order/list.tsx`

...

## 常见模式

### 刷新列表

```tsx
tableRef.current?.fetchPage({});
```

### 获取选中行

```tsx
const selectedRows = tableRef.current?.getSelectedRows();
```

### 自定义单元格渲染

```tsx
const cellRenderer = ({ cellData, column, rowData }) => {
  if (column.dataIndex === 'status') {
    return <Tag color={statusColorMap[cellData]}>{cellData}</Tag>;
  }
  return cellData;
};
```
```

#### 3. 组件文档模板（components/TableTemplatePro.md）

```markdown
# TableTemplatePro

> 企业级表格模板组件，内置搜索、分页、批量操作等功能。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 来源 | `@dzg/gm-template` |
| 使用频率 | 61 次 |
| 适用场景 | 列表页 |
| 同类组件 | Table, ProTable |

## 使用场景

- ✅ 管理后台数据列表
- ✅ 需要搜索、分页、批量操作
- ✅ 需要列设置、视图切换
- ❌ 简单数据展示（用 Table）
- ❌ 树形数据（考虑 TreeTable）

## 代码示例

### 示例 1：基础列表

**来源**：`src/pages/carrier-route/index.tsx`
**场景**：简单的 CRUD 列表

```tsx
import { TableTemplatePro } from '@dzg/gm-template';

<TableTemplatePro
  title="船公司航线"
  displayHeader={true}
  displayCommonSetting={true}
  fetchPageUrl="/dzg-orgbase-rest/baseCarrierRoute/pagedQuery"
  rowKey="id"
  columns={columns}
  cellRenderer={cellRenderer}
  tableOperations={buttonList}
  onSelectChange={row => setChecked(row.selectedRows.map(item => item.id))}
/>
```

### 示例 2：复杂配置

**来源**：`src/pages/order-list/index.tsx`
**场景**：带自定义渲染、行展开、双击跳转的订单列表

```tsx
<TableTemplatePro
  ref={tableRef}
  title="订单列表"
  displayHeader={true}
  displayView={true}
  displayCommonSetting={true}
  defaultQueryParams={queryParams}
  expandColumnKey="businessNo"
  expandedRowKeys={expandedRowKeys}
  onExpandedRowsChange={setExpandedRowKeys}
  cellRendererMini={getCellRendererMini({ handleClick })}
  onRowDoubleClick={({ rowData }) => {
    window.open(`/detail?id=${rowData.casenumber}`, '_blank');
  }}
  canCellCopy
  rowClassName={rowCustomizedStyle}
  fetchPageUrl="/api/order/list"
  rowKey="casenumber"
  tableOperations={buttonList}
  renderSelectedSummaryInfo={renderTeu}
  isColumnFilterable
/>
```

## 常用 Props

| Prop | 类型 | 说明 | 必填 |
| --- | --- | --- | --- |
| title | string | 表格标题 | 是 |
| fetchPageUrl | string | 数据接口地址 | 是 |
| columns | Column[] | 列配置 | 是 |
| rowKey | string | 行唯一标识字段 | 是 |
| displayHeader | boolean | 显示头部 | 否 |
| displayCommonSetting | boolean | 显示设置按钮 | 否 |
| tableOperations | ReactNode[] | 操作按钮 | 否 |
| cellRenderer | function | 单元格渲染器 | 否 |
| onSelectChange | function | 选中行变化回调 | 否 |

## 常用方法（ref）

| 方法 | 说明 |
| --- | --- |
| fetchPage({}) | 刷新表格数据 |
| getSelectedRows() | 获取选中行 |
| getQueryParams() | 获取当前查询参数 |
```

#### 4. Hook 文档模板（hooks/useRequest.md）

```markdown
# useRequest

> 强大的异步数据请求 Hook，支持 loading、防抖、轮询等功能。

## 基本信息

| 属性 | 值 |
| --- | --- |
| 来源 | `ahooks` 或 `@/hooks/useRequest` |
| 使用频率 | 45 次 |
| 适用场景 | 数据请求、表单提交、定时刷新 |

## 代码示例

### 示例 1：手动触发请求

**来源**：`src/pages/carrier-route/index.tsx`

```tsx
import { useRequest } from 'ahooks';

const { loading, data, run, reset } = useRequest<CarrierListProps[]>(
  fetchCarrierList,
  {
    manual: true,          // 手动触发
    debounceInterval: 500, // 防抖 500ms
  }
);

// 触发请求
run(searchKeyword);

// 重置数据
reset();
```

### 示例 2：自动请求 + 依赖刷新

**来源**：`src/pages/user/detail.tsx`

```tsx
const { loading, data } = useRequest(
  () => getUserDetail(userId),
  {
    refreshDeps: [userId], // userId 变化时自动刷新
  }
);
```

### 示例 3：轮询

```tsx
const { data } = useRequest(getStatus, {
  pollingInterval: 3000, // 每 3 秒轮询
  pollingWhenHidden: false, // 页面隐藏时停止
});
```

## 常用配置

| 配置项 | 类型 | 说明 |
| --- | --- | --- |
| manual | boolean | 是否手动触发，默认 false |
| debounceInterval | number | 防抖时间（ms） |
| throttleInterval | number | 节流时间（ms） |
| pollingInterval | number | 轮询间隔（ms） |
| refreshDeps | any[] | 依赖变化时自动刷新 |
| onSuccess | function | 成功回调 |
| onError | function | 失败回调 |

## 返回值

| 属性 | 类型 | 说明 |
| --- | --- | --- |
| data | T | 请求结果 |
| loading | boolean | 是否加载中 |
| error | Error | 错误信息 |
| run | function | 手动触发请求 |
| reset | function | 重置状态 |
| refresh | function | 使用上次参数重新请求 |
```

---

## 分析检查清单

完成分析前，确认以下内容已生成：

### 必须生成的文档

- [ ] `COMPONENT-SELECTOR.md` - 组件选择器（**最重要**）
- [ ] `inventory.md` - 完整物资清单
- [ ] `DEV-GUIDE.md` - 开发手册入口
- [ ] `scenarios/` - 至少包含 list.md, form.md

### 组件文档要求

- [ ] 每个使用超过 3 次的组件都有独立文档
- [ ] 每个文档至少包含 2 个不同场景的使用示例
- [ ] 示例代码是"使用代码"，不是"定义代码"
- [ ] 示例代码包含完整 import 和关键 props

### 场景文档要求

- [ ] 每个场景列出推荐技术栈
- [ ] 每个场景至少有 1 个完整示例
- [ ] 示例来源标注清楚（文件路径）

### 组件选择器要求

- [ ] 按场景分类（列表页、表单页、详情页等）
- [ ] 同类组件有对比表
- [ ] 有明确的选择建议

---

## ⚠️ 严禁的做法

- ❌ 把组件的"定义代码"当作"使用示例"
- ❌ 只收集组件定义所在文件，忽略使用位置
- ❌ 示例代码是整个文件或整个函数
- ❌ 忽略第三方组件（如 antd 的 Modal、Form）
- ❌ 没有 COMPONENT-SELECTOR.md

## ✅ 正确的做法

- ✅ 收集组件在其他文件中的使用代码
- ✅ 示例代码简洁但完整，能独立理解
- ✅ 为所有使用过的组件生成文档（包括第三方）
- ✅ 按场景组织，帮助 AI 选择合适组件
- ✅ 同类组件有对比和选择建议

---

## 输出

输出到项目的 `.ai-docs/` 目录：

```
.ai-docs/
├── DEV-GUIDE.md              # 开发手册总入口
├── COMPONENT-SELECTOR.md     # 组件选择器（核心文档）
├── inventory.md              # 完整物资清单
├── scenarios/                # 场景文档
│   ├── list.md
│   ├── form.md
│   ├── detail.md
│   └── modal.md
├── components/               # 组件使用文档
│   ├── TableTemplatePro.md
│   ├── Form.md
│   ├── Modal.md
│   └── ...
├── hooks/                    # Hook 使用文档
│   ├── useRequest.md
│   ├── useState.md
│   └── ...
└── utils/                    # 工具函数文档
    └── ...
```
