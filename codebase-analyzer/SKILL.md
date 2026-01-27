---
name: codebase-analyzer
description: 深度分析项目代码库，生成完整的开发指导手册。使用 LLM 理解每个文件，通过多代理协作支持任意规模代码库分析，提取所有组件/库/Hook 的使用示例，输出数据驱动的 Markdown 开发手册。当用户请求"分析项目"、"生成开发手册"、"了解项目结构"、"提取编码规范"、"分析代码库"时使用此技能。
---

# Codebase Analyzer

分析项目代码库，生成数据驱动的开发指导手册。

## 核心原则

1. **LLM 全量理解**：每个文件都使用 LLM（Read 工具）理解，确保不遗漏任何组件、库或 Hook。

2. **多代理协作**：通过批次化分析和层级汇总，支持任意规模代码库（10000+ 文件）而不会上下文溢出。

3. **数据驱动输出**：章节结构由实际代码库数据决定，不使用预定义模板。

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

### 扫描命令

```
**/*.{ts,tsx,js,jsx,vue,svelte}
```

### 输出

完整的文件路径列表，如：

- `src/components/Button.tsx`
- `src/pages/user/list.tsx`
- `src/service/user.ts`
- ...

---

## 阶段 2：批次化分析（多代理协作）

**关键原则**：不遗漏任何文件，每个文件都用 LLM 理解。

### 工作流程

```
主 Agent
  │
  ├─→ 将文件列表分批（每批 10-20 个文件）
  │
  ├─→ 为每批创建子代理任务
  │
  └─→ 收集所有子代理的汇总结果
```

### 子代理任务模板

```
请分析以下文件批次，返回结构化汇总：

文件列表：
- src/components/Button.tsx
- src/components/Input.tsx
- src/pages/user/list.tsx
- ...

分析任务：
1. 提取所有 import 语句（包括动态 import）
2. 提取所有 JSX 组件使用
3. 提取所有 Hooks 调用
4. 提取组件定义（含 Props 类型）
5. 提取接口定义和调用
6. 识别代码风格特征

返回格式（JSON）：
{
  "imports": {
    "sources": { "react": 2, "antd": 5, "@/components/Button": 1 },
    "items": { "useState (from react)": 1, "Button (from antd)": 3 }
  },
  "components": {
    "used": { "Form": 5, "Table": 2, "Button": 8 },
    "defined": ["Button", "Input", "UserCard"]
  },
  "hooks": { "useState": 3, "useEffect": 1, "useRequest": 2 },
  "apis": { "userListPost": 1, "userDetailGet": 1 },
  "codeStyle": {
    "naming": "PascalCase for components",
    "export": "default export",
    "importOrder": "third-party → internal → relative"
  },
  "examples": {
    "Button": { "filePath": "src/pages/user/list.tsx", "code": "..." },
    "useRequest": { "filePath": "src/pages/user/list.tsx", "code": "..." }
  }
}

**重要**：
- 不要遗漏任何 import、组件或 Hook
- 为每个发现的项提供至少一个完整代码示例
- 代码示例必须包含 import 语句和实际使用代码
```

### 批次分配策略

| 文件数 | 每批文件数 | 说明               |
| ------ | ---------- | ------------------ |
| < 50   | 逐个处理   | 每个文件单独分析   |
| 50-200 | 10 个/批   | 平衡速度和准确性   |
| 200+   | 20 个/批   | 高效处理大规模项目 |

---

## 阶段 3：层级汇总

**当子代理数量过多时，使用层级汇总避免上下文溢出。**

### 单层汇总（< 10 个子代理）

```
子代理 1 汇总 ─┐
子代理 2 汇总 ─┤
子代理 3 汇总 ─┼─→ 最终汇总
...           ─┤
子代理 N 汇总 ─┘
```

### 多层汇总（10+ 个子代理）

```
批次 1-5    → 中间汇总 A ─┐
批次 6-10   → 中间汇总 B ─┤
批次 11-15  → 中间汇总 C ─┼─→ 最终汇总
...                         ─┤
批次 N-4 到 N → 中间汇总 Z ─┘
```

### 汇总逻辑

1. **合并物资清单**：所有 importSources、jsxComponents、hooks
2. **合并使用位置**：记录每个组件/Hook 在哪些文件中被使用
3. **去重代码示例**：相同组件保留 1-3 个最佳示例

### 最终汇总输出

```json
{
  "inventory": {
    "importSources": {
      "react": 120,
      "antd": 85,
      "@/components/TableTemplatePro": 38,
      "@/components/MyRareWidget": 1
    },
    "jsxComponents": {
      "Form": 115,
      "Table": 89,
      "TableTemplatePro": 38,
      "MyRareComponent": 1
    },
    "hooks": {
      "useState": 234,
      "useRequest": 45,
      "useMyCustomHook": 1
    }
  },
  "usageLocations": {
    "TableTemplatePro": ["src/pages/user/list.tsx", "src/pages/order/list.tsx"],
    "MyRareComponent": ["src/pages/special/index.tsx"]
  },
  "examples": {
    "TableTemplatePro": {
      "filePath": "src/pages/user/list.tsx",
      "code": "完整的使用代码..."
    }
  }
}
```

---

## 阶段 4：生成数据驱动的开发文档

**核心原则**：

1. 章节结构由阶段 3 的汇总数据决定，不使用预定义模板
2. 每个组件/库/Hook 的使用示例写入独立文件，便于维护和 AI 快速查找

### 文件结构

```
docs/
├── components/           # 组件使用文档
│   ├── TableTemplatePro.md
│   ├── MyRareComponent.md
│   └── ...
├── hooks/               # Hook 使用文档
│   ├── useRequest.md
│   ├── useMyCustomHook.md
│   └── ...
├── apis/                # 接口使用文档
│   ├── user.md
│   ├── order.md
│   └── ...
├── inventory.md         # 完整物资清单（索引）
└── DEV-GUIDE.md         # 开发手册总入口
```

### 输出规则

#### 规则 1：生成完整物资清单（inventory.md）

```markdown
# 项目物资清单

生成时间：2024-01-27

## 导入来源（按使用频率排序）

| 来源                          | 使用次数 | 类型       | 文档                                               |
| ----------------------------- | -------- | ---------- | -------------------------------------------------- |
| antd                          | 156      | UI 库      | -                                                  |
| @/components/TableTemplatePro | 38       | 自定义组件 | [TableTemplatePro](components/TableTemplatePro.md) |
| @/service/user                | 25       | 接口       | [user](apis/user.md)                               |
| @/components/MyRareWidget     | 1        | 自定义组件 | [MyRareWidget](components/MyRareWidget.md)         |

## JSX 组件（按使用频率排序）

| 组件             | 使用次数 | 文档                                                  |
| ---------------- | -------- | ----------------------------------------------------- |
| Form             | 115      | - (第三方库)                                          |
| TableTemplatePro | 38       | [TableTemplatePro.md](components/TableTemplatePro.md) |
| MyRareComponent  | 1        | [MyRareComponent.md](components/MyRareComponent.md)   |

## Hooks（按使用频率排序）

| Hook            | 使用次数 | 文档                                           |
| --------------- | -------- | ---------------------------------------------- |
| useState        | 234      | - (React 内置)                                 |
| useRequest      | 45       | [useRequest.md](hooks/useRequest.md)           |
| useMyCustomHook | 1        | [useMyCustomHook.md](hooks/useMyCustomHook.md) |
```

#### 规则 2：为每个组件生成独立文档

**遍历物资清单中的每一项，生成独立的 Markdown 文件。**

##### 组件文档模板

文件路径：`docs/components/TableTemplatePro.md`

```markdown
# TableTemplatePro

**来源**：`@/components/TableTemplatePro`

**使用频率**：38 次

**使用位置**：

- src/pages/user/list.tsx
- src/pages/order/list.tsx
- src/pages/product/list.tsx

## 代码示例

### 示例 1：用户列表页

**来源**：`src/pages/user/list.tsx`

\`\`\`tsx
import { TableTemplatePro } from '@/components/TableTemplatePro';
import { userListPost } from '@/service/user';

const UserList = () => {
const [loading, setLoading] = useState(false);

const columns = [
{ title: '姓名', dataIndex: 'name', key: 'name' },
{ title: '邮箱', dataIndex: 'email', key: 'email' },
{ title: '状态', dataIndex: 'status', key: 'status' },
];

return (
<TableTemplatePro
      columns={columns}
      request={userListPost}
      rowKey="id"
      loading={loading}
    />
);
};
\`\`\`

### 示例 2：订单列表页（带筛选）

**来源**：`src/pages/order/list.tsx`

\`\`\`tsx
（如果有不同的使用方式，提供第二个示例）
\`\`\`
```

##### Hook 文档模板

文件路径：`docs/hooks/useRequest.md`

```markdown
# useRequest

**来源**：`@/hooks/useRequest`

**使用频率**：45 次

**使用位置**：

- src/pages/user/list.tsx
- src/pages/order/detail.tsx
- ...

## 定义

**来源**：`src/hooks/useRequest.ts`

\`\`\`tsx
export function useRequest<T>(
apiFn: (...args: any[]) => Promise<T>,
options?: UseRequestOptions<T>
) {
const [loading, setLoading] = useState(false);
const [data, setData] = useState<T | null>(null);

const run = useCallback(async (...args: any[]) => {
setLoading(true);
try {
const result = await apiFn(...args);
setData(result);
return result;
} finally {
setLoading(false);
}
}, [apiFn]);

return { loading, data, run };
}
\`\`\`

## 使用示例

### 示例 1：基础用法

**来源**：`src/pages/user/list.tsx`

\`\`\`tsx
import { useRequest } from '@/hooks/useRequest';
import { userListPost } from '@/service/user';

const UserList = () => {
const { loading, data, run } = useRequest(userListPost);

useEffect(() => {
run({ page: 1, pageSize: 10 });
}, []);

return <Table loading={loading} dataSource={data?.list} />;
};
\`\`\`
```

##### API 文档模板

文件路径：`docs/apis/user.md`

```markdown
# user 接口模块

**定义位置**：`src/service/user.ts`

## 接口列表

| 接口           | 说明         | 使用次数 |
| -------------- | ------------ | -------- |
| userListPost   | 获取用户列表 | 15       |
| userDetailGet  | 获取用户详情 | 8        |
| userCreatePost | 创建用户     | 3        |

## 接口定义

**来源**：`src/service/user.ts`

\`\`\`typescript
import request from '@/service/request';

export function userListPost(params: UserListParams) {
return request({
url: '/api/user/list',
method: 'POST',
data: params,
});
}

export function userDetailGet(id: number) {
return request({
url: `/api/user/detail/${id}`,
method: 'GET',
});
}
\`\`\`

## 使用示例

### userListPost

**来源**：`src/pages/user/list.tsx`

\`\`\`tsx
import { userListPost } from '@/service/user';

const { data, run } = useRequest(userListPost);
run({ page: 1, pageSize: 10 });
\`\`\`
```

#### 规则 3：生成总入口文档（DEV-GUIDE.md）

**提供快速导航和项目概览，详细内容链接到独立文档。**

```markdown
# {项目名称} 开发手册

> 本文档由 AI 自动分析生成，包含项目中所有组件、Hook 和接口的使用文档。
> 生成时间：{生成时间}

## 快速导航

| 我想...          | 查看文档                     |
| ---------------- | ---------------------------- |
| 查看完整物资清单 | [inventory.md](inventory.md) |
| 查找组件用法     | [components/](components/)   |
| 查找 Hook 用法   | [hooks/](hooks/)             |
| 查找接口用法     | [apis/](apis/)               |

## 项目概览

### 技术栈

| 类别     | 技术            | 版本   |
| -------- | --------------- | ------ |
| 框架     | {React/Vue}     | {版本} |
| UI 库    | {Ant Design}    | {版本} |
| 状态管理 | {Redux/Zustand} | {版本} |
| 构建工具 | {Vite/Webpack}  | {版本} |

### 目录结构
```

src/
├── components/ # 公共组件
├── pages/ # 页面
├── hooks/ # 自定义 Hooks
├── service/ # API 接口
├── store/ # 状态管理
└── utils/ # 工具函数

```

## 常用组件速查

| 组件             | 使用次数 | 文档                                 |
| ---------------- | -------- | ------------------------------------ |
| TableTemplatePro | 38       | [查看](components/TableTemplatePro.md) |
| MyRareComponent  | 1        | [查看](components/MyRareComponent.md)  |

## 常用 Hooks 速查

| Hook            | 使用次数 | 文档                               |
| --------------- | -------- | ---------------------------------- |
| useRequest      | 45       | [查看](hooks/useRequest.md)         |
| useMyCustomHook | 1        | [查看](hooks/useMyCustomHook.md)    |

## 接口模块速查

| 模块 | 接口数量 | 文档                    |
| ---- | -------- | ----------------------- |
| user | 3        | [查看](apis/user.md)    |
| order| 5        | [查看](apis/order.md)   |

---

**详细文档请查看对应的独立文件。**
```

### ⚠️ 禁止的做法

- ❌ 使用预定义的章节列表（"如何新建页面"、"如何创建表单"）
- ❌ 只输出高频组件，忽略低频组件
- ❌ 用统计数字代替代码示例
- ❌ 遗漏任何组件、库或 Hook
- ❌ 所有内容塞到一个文件

### ✅ 正确的做法

- ✅ 遍历物资清单中的每一项
- ✅ 即使只使用 1 次的组件，也生成独立文档
- ✅ 每个组件/Hook/API 都有独立的 Markdown 文件
- ✅ 总入口文档提供导航链接
- ✅ 所有代码示例从实际文件中提取，标注来源

---

## Shell 工具辅助

对于简单的统计查询，可以使用 grep/ripgrep 加速。

### 示例

| 需求            | 命令                                                 |
| --------------- | ---------------------------------------------------- | ------ |
| 确认路由库      | `grep -r "react-router" package.json src/`           |
| 统计文件数量    | `find src -name "\*.tsx"                             | wc -l` |
| 快速查找 import | `grep -rn "import.*from.*@/" src/ --include="*.ts*"` |

**注意**：Shell 工具仅用于辅助，最终分析必须用 LLM 理解每个文件。

---

## 分析检查清单

完成分析前，确认以下信息已提取：

- [ ] 完整的物资清单（所有 import、组件、Hook）
- [ ] 每个组件的使用示例（包括只用 1 次的）
- [ ] 每个 Hook 的使用示例（包括只用 1 次的）
- [ ] 每个接口的定义和调用示例
- [ ] 代码风格特征（命名、导出、导入顺序）
- [ ] 技术栈版本信息
- [ ] 项目目录结构

---

## 输出

输出到项目的 `docs/` 目录：

```
docs/
├── DEV-GUIDE.md         # 总入口文档
├── inventory.md         # 完整物资清单（索引）
├── components/          # 组件文档目录
│   ├── TableTemplatePro.md
│   ├── MyRareComponent.md
│   └── ...
├── hooks/              # Hook 文档目录
│   ├── useRequest.md
│   ├── useMyCustomHook.md
│   └── ...
└── apis/               # API 文档目录
    ├── user.md
    ├── order.md
    └── ...
```
