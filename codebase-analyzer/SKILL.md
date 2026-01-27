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

## 阶段 4：生成数据驱动的开发手册

**核心原则**：章节结构由阶段 3 的汇总数据决定，不使用预定义模板。

### 输出规则

#### 规则 1：完整物资清单

首先输出完整的物资清单，让读者知道项目用了什么。

```markdown
## 项目物资清单

### 导入来源（按使用频率排序）

| 来源                          | 使用次数 | 类型       |
| ----------------------------- | -------- | ---------- |
| antd                          | 156      | UI 库      |
| @/components/TableTemplatePro | 38       | 自定义组件 |
| @/service/user                | 25       | 接口       |
| ...                           | ...      | ...        |
| @/components/MyRareWidget     | 1        | 自定义组件 |

### JSX 组件（按使用频率排序）

| 组件             | 使用次数 |
| ---------------- | -------- |
| Form             | 115      |
| TableTemplatePro | 38       |
| ...              | ...      |
| MyRareComponent  | 1        |

### Hooks（按使用频率排序）

| Hook            | 使用次数 |
| --------------- | -------- |
| useState        | 234      |
| useRequest      | 45       |
| useMyCustomHook | 1        |
```

#### 规则 2：为每个物资项提供使用示例

**遍历物资清单中的每一项，提供完整代码示例。**

```markdown
## 组件使用示例

### TableTemplatePro（使用 38 次）

**来源**：`@/components/TableTemplatePro`

**使用位置**：

- src/pages/user/list.tsx
- src/pages/order/list.tsx
- ...

**代码示例**（来自 `src/pages/user/list.tsx`）：

\`\`\`tsx
import { TableTemplatePro } from '@/components/TableTemplatePro';
import { userListPost } from '@/service/user';

const UserList = () => {
const [loading, setLoading] = useState(false);

const columns = [
{ title: '姓名', dataIndex: 'name', key: 'name' },
{ title: '邮箱', dataIndex: 'email', key: 'email' },
];

return (
<TableTemplatePro
      columns={columns}
      request={userListPost}
      rowKey="id"
    />
);
};
\`\`\`

---

### MyRareComponent（使用 1 次）

**来源**：`@/components/MyRareComponent`

**使用位置**：

- src/pages/special/index.tsx

**代码示例**（来自 `src/pages/special/index.tsx`）：

\`\`\`tsx
import { MyRareComponent } from '@/components/MyRareComponent';

const SpecialPage = () => {
return <MyRareComponent prop1="value1" prop2={123} />;
};
\`\`\`
```

#### 规则 3：为每个 Hook 提供使用示例

```markdown
## Hooks 使用示例

### useRequest（使用 45 次）

**代码示例**（来自 `src/pages/user/list.tsx`）：

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

---

### useMyCustomHook（使用 1 次）

**定义**（来自 `src/hooks/useMyCustomHook.ts`）：

\`\`\`tsx
export function useMyCustomHook(options: Options) {
const [state, setState] = useState(initialState);
// ... 完整实现
}
\`\`\`

**使用示例**（来自 `src/pages/special/index.tsx`）：

\`\`\`tsx
import { useMyCustomHook } from '@/hooks/useMyCustomHook';

const SpecialPage = () => {
const result = useMyCustomHook({ option1: 'value1' });
return <div>{result.data}</div>;
};
\`\`\`
```

#### 规则 4：接口定义和调用示例

```markdown
## API 接口使用示例

### user 服务模块

**定义位置**：`src/service/user.ts`

**接口列表**：

- `userListPost` - 获取用户列表（使用 15 次）
- `userDetailGet` - 获取用户详情（使用 8 次）
- `userCreatePost` - 创建用户（使用 3 次）

**代码示例**（来自 `src/service/user.ts`）：

\`\`\`typescript
import request from '@/service/request';

export function userListPost(params: UserListParams) {
return request({
url: '/api/user/list',
method: 'POST',
data: params,
});
}
\`\`\`

**调用示例**（来自 `src/pages/user/list.tsx`）：

\`\`\`tsx
import { userListPost } from '@/service/user';

const { data, run } = useRequest(userListPost);
run({ page: 1, pageSize: 10 });
\`\`\`
```

### ⚠️ 禁止的做法

- ❌ 使用预定义的章节列表（"如何新建页面"、"如何创建表单"）
- ❌ 只输出高频组件，忽略低频组件
- ❌ 用统计数字代替代码示例
- ❌ 遗漏任何组件、库或 Hook

### ✅ 正确的做法

- ✅ 遍历物资清单中的每一项
- ✅ 即使只使用 1 次的组件，也提供完整的使用示例
- ✅ 章节结构由数据决定，而不是模板决定
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

输出文件命名：`DEV-GUIDE.md`（放在项目根目录）
