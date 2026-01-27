---
name: codebase-analyzer
description: 深度分析项目代码库，生成完整的开发指导手册。扫描所有代码文件，提取技术框架、编码风格、组件模式、路由配置、状态管理、API调用方式等信息，识别同一场景的多种实现方案，输出结构化的 Markdown 开发手册供 AI 后续开发参考。当用户请求"分析项目"、"生成开发手册"、"了解项目结构"、"提取编码规范"、"分析代码库"时使用此技能。
---

# Codebase Analyzer

分析项目代码库，生成开发指导手册。

## 核心原则

1. **避免上下文溢出**：本技能设计为支持任意规模的代码库分析。通过脚本化分析和多代理协作，确保即使分析 10000+ 文件也不会导致上下文累积过大。

2. **禁止污染项目目录**：
   - ❌ 禁止复制脚本到项目目录（如 `_codebase_scanner.js`）
   - ❌ 禁止在项目目录创建临时文件（如 `_codebase_analysis.json`）
   - ✅ 所有脚本直接从 `~/.claude/skills/` 原位置执行
   - ✅ 所有输出文件写入 `/tmp/` 目录

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

2. **分支判断**：

| 规模   | 文件数 | 策略                                     |
| ------ | ------ | ---------------------------------------- |
| 小规模 | < 50   | 使用**传统分析模式**（阶段 1-5）         |
| 大规模 | >= 50  | 强制进入**脚本化分析模式**（阶段 S1-S4） |

---

## 传统分析模式（小规模项目 < 50 文件）

适用于小型项目，允许逐个读取文件进行分析。

### 阶段 1：项目识别

1. 读取 `package.json`（前端/Node.js）或其他配置文件识别技术栈
2. 读取 `tsconfig.json` / `vite.config.*` / `next.config.*` / `webpack.config.*` 等构建配置
3. 读取 `.eslintrc*` / `.prettierrc*` / `biome.json` 等代码规范配置
4. 确定项目类型：React / Vue / Next.js / Nuxt / Angular / Node.js / 其他

### 阶段 2：全量扫描

使用 Glob 工具扫描所有代码文件，排除以下目录：

- `node_modules/`
- `dist/` / `build/` / `.next/` / `.nuxt/`
- `.git/`
- `coverage/`
- `*.min.js` / `*.bundle.js`

扫描的文件类型：

```
**/*.{ts,tsx,js,jsx,vue,svelte,css,scss,less,json}
```

### 阶段 3：分维度分析

按以下维度逐一分析：

#### 3.1 技术栈识别

从 `package.json` 的 dependencies/devDependencies 提取：

- 框架：react / vue / angular / svelte
- 构建：vite / webpack / esbuild / turbopack
- 样式：tailwindcss / styled-components / emotion / css-modules
- 状态：zustand / redux / pinia / mobx / jotai
- 路由：react-router / vue-router / next (内置)
- 请求：axios / ky / got / @tanstack/react-query
- UI 库：antd / @mui/material / element-plus / shadcn

#### 3.2 目录结构分析

识别常见目录约定：

- `src/components/` - 组件
- `src/pages/` / `src/views/` / `app/` - 页面
- `src/hooks/` / `src/composables/` - 自定义 Hooks
- `src/stores/` / `src/store/` - 状态管理
- `src/services/` / `src/api/` - API 调用
- `src/utils/` / `src/lib/` - 工具函数
- `src/types/` - 类型定义
- `src/styles/` - 全局样式

#### 3.3 编码风格提取

从实际代码中识别：

- 文件命名：kebab-case / PascalCase / camelCase
- 组件命名：PascalCase
- 函数命名：camelCase / snake_case
- 导出方式：named export / default export
- 导入顺序：第三方库 → 内部模块 → 相对路径 → 样式

#### 3.4 组件模式识别

识别项目中使用的组件形式：

- 函数组件 + Hooks
- 类组件
- HOC 模式
- Render Props
- Compound Components
- Vue Options API / Composition API

**重点**：从代码中提取真实示例，不要编造。

#### 3.5 路由配置提取

根据框架类型：

- React Router：查找 `<Route>` / `createBrowserRouter` 配置
- Next.js：分析 `app/` 或 `pages/` 目录结构
- Vue Router：查找 `router/index.ts` 配置
- 提取所有路由路径及对应组件

#### 3.6 状态管理分析

识别 store 定义和使用方式：

- 查找 store 定义文件
- 提取 state 结构
- 提取 actions / mutations / selectors 使用示例

#### 3.7 API 调用方式

识别请求封装：

- 查找 axios 实例配置
- 查找 fetch 封装
- 查找 API 定义文件
- 提取请求拦截器、错误处理方式

#### 3.8 样式方案分析

识别样式使用方式：

- CSS Modules：`*.module.css`
- Tailwind：className 中的 utility classes
- CSS-in-JS：styled-components / emotion
- 全局样式文件位置

### 阶段 4：多方案识别

**关键任务**：对于同一场景，识别是否存在多种实现方式。

检查点：

- 列表组件是否有多种实现？
- 表单处理是否有多种方式？
- 弹窗/对话框是否有多种组件？
- 数据获取是否有多种模式？
- 样式是否混用多种方案？

对于发现的多方案场景：

1. 记录每种方案的文件位置
2. 提取代码示例
3. 分析使用频率
4. 标注推荐方案（基于使用频率或代码注释）

### 阶段 5：生成开发手册

参考 `assets/dev-guide-template.md` 模板结构，生成完整的开发指导手册。

输出要求：

1. 所有代码示例必须从项目中提取，不要编造
2. 标注代码来源文件路径
3. 多方案场景必须分别记录
4. 表格数据要完整填写
5. 输出为单个 Markdown 文件

输出文件命名：`DEV-GUIDE.md`（放在项目根目录）

---

## 脚本化分析模式（大规模项目 >= 50 文件）

**严禁使用 Read/view_file 遍历文件进行定量分析。**

### ⚠️ 重要：不要污染项目目录

执行脚本时必须遵守以下规则：

1. **禁止复制脚本到项目目录** - 直接从 `~/.claude/skills/` 原位置执行
2. **禁止在项目目录创建任何文件** - 所有输出必须写入 `/tmp/` 目录
3. **执行完成后检查** - 确保项目目录没有新增任何 `_*.js` 或 `_*.json` 文件

### 阶段 S1：全量索引（Exhaustive Indexing）

**不依赖任何预设关键词**，暴力扫描所有文件，提取所有 import 语句，生成完整的"项目物资清单"。

#### 执行命令（直接从原位置执行，禁止复制脚本）

```bash
# ✅ 正确：直接从原位置执行
node ~/.claude/skills/codebase-analyzer/assets/analyzer-scripts/codebase-scanner.js --dir . --output /tmp/_codebase_analysis.json

# ❌ 错误：不要复制脚本到项目目录
# cp ~/.claude/skills/.../codebase-scanner.js ./_codebase_scanner.js  ← 禁止
```

#### 读取分析结果

```bash
cat /tmp/_codebase_analysis.json
```

#### 全量索引输出内容

脚本会**无差别扫描**所有文件，输出完整的物资清单：

| 字段                | 说明                       | 示例                                                                    |
| ------------------- | -------------------------- | ----------------------------------------------------------------------- |
| `importSources`     | 所有导入来源及使用次数     | `{ "antd": 156, "@/components/TableTemplatePro": 38 }`                  |
| `importedItems`     | 所有导入项及使用次数       | `{ "Form (from antd)": 115, "MyRareComponent (from @/components)": 1 }` |
| `jsxComponents`     | 所有 JSX 组件及使用次数    | `{ "Table": 89, "MyCustomList": 3 }`                                    |
| `hooks`             | 所有 Hooks 及使用次数      | `{ "useState": 234, "useMyCustomHook": 5 }`                             |
| `componentUsageMap` | 每个组件在哪些文件中使用   | `{ "TableTemplatePro": ["src/pages/a.tsx", "src/pages/b.tsx"] }`        |
| `hookUsageMap`      | 每个 Hook 在哪些文件中使用 | `{ "useRequest": ["src/pages/a.tsx", ...] }`                            |

**关键点**：即使一个组件只被使用 1 次，也会被完整记录。

### 阶段 S2：自适应模式提取（数据驱动）

**根据 S1 的全量索引结果，自适应地提取代码示例。**

不是我（Agent）在猜项目用了什么，而是**数据告诉我是什么**。

#### 执行命令（直接从原位置执行，禁止复制脚本）

```bash
# ✅ 正确：直接从原位置执行，必须指定 --analysis 参数
node ~/.claude/skills/codebase-analyzer/assets/analyzer-scripts/pattern-extractor.js --dir . --analysis /tmp/_codebase_analysis.json --output /tmp/_dev_patterns.json

# ❌ 错误：不要复制脚本到项目目录
# cp ~/.claude/skills/.../pattern-extractor.js ./_pattern_extractor.js  ← 禁止
```

#### 读取模式提取结果

```bash
cat /tmp/_dev_patterns.json
```

#### 自适应提取逻辑

S2 脚本会读取 S1 的物资清单，**根据实际数据决定提取什么**：

| S1 发现                       | S2 动作                                          |
| ----------------------------- | ------------------------------------------------ |
| `TableTemplatePro` 使用 38 次 | 找使用 `TableTemplatePro` 的文件作为"列表页范例" |
| `MyCustomForm` 使用 5 次      | 提取 `MyCustomForm` 的使用示例                   |
| `useMyRareHook` 只使用 1 次   | **也会提取**这唯一一次使用的示例                 |

#### 输出内容

```json
{
  "inventory": {
    "importSources": { ... },   // 完整物资清单
    "jsxComponents": { ... },
    "hooks": { ... }
  },
  "developmentScenarios": {
    "listPage": {
      "name": "列表页开发",
      "description": "使用 TableTemplatePro 的列表页示例",
      "component": "TableTemplatePro",
      "example": {
        "filePath": "src/pages/user/list.tsx",
        "code": { "fullContent": "完整代码..." }
      }
    },
    "formPage": { ... },
    "modalUsage": { ... },
    "apiUsage": { ... },
    "serviceDefinition": { ... },
    "routeConfig": { ... },
    "styleWriting": { ... },
    "customHook": { ... }
  },
  "categories": {
    "customComponents": {
      "items": [
        {
          "name": "MyRareComponent",
          "count": 1,
          "examples": [{ "filePath": "...", "code": "..." }]
        }
      ]
    }
  }
}
```

**关键点**：每个组件/库，无论使用频率高低，都会有对应的使用示例。

### 阶段 S3：多代理协作深度分析（可选）

对于需要 AI 理解能力的复杂分析（如代码风格、模式识别），使用多代理协作。

#### 工作流程

1. **主 Agent** 根据脚本分析结果，将文件按批次分配给子代理
2. **子代理** 独立分析每批文件，返回结构化汇总（不返回原始代码）
3. **主 Agent** 汇总所有子代理的结果

#### 批次分配策略

- 默认每批 20 个文件
- 根据文件复杂度动态调整（复杂文件减少批次大小）
- 每个子代理分析完成后立即汇总，释放上下文

#### 子代理任务模板

```
分析以下文件批次，返回结构化汇总：

文件列表：
- src/components/Button.tsx
- src/components/Input.tsx
- ...

分析维度：
1. 组件形态（函数组件/类组件/HOC）
2. 样式方案（CSS Modules/Tailwind/CSS-in-JS）
3. 状态管理（local state/context/store）
4. 代码风格特征（命名规范、导出方式）

返回格式（JSON）：
{
  "componentPatterns": { "functional": 15, "class": 2 },
  "stylePatterns": { "tailwind": 10, "cssModules": 5 },
  "codeStyle": {
    "naming": "camelCase for functions, PascalCase for components",
    "exports": "mostly named exports"
  },
  "notableFiles": ["src/components/Button.tsx - 良好的组件示例"]
}
```

#### 汇总策略

当子代理数量过多时，采用层级汇总：

```
批次 1-5 的汇总 → 中间汇总 A
批次 6-10 的汇总 → 中间汇总 B
中间汇总 A + B → 最终汇总
```

### 阶段 S4：生成实操开发手册（数据驱动）

**核心原则**：章节结构由 S1/S2 的数据决定，不使用预定义的章节列表。

#### 输出结构必须遵循以下规则

**规则 1：完整物资清单**

首先输出 S1 生成的完整物资清单，让读者知道项目用了什么：

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

**规则 2：为每个物资项提供使用示例**

**不是预定义的场景（表单/表格/弹窗），而是遍历物资清单中的每一项。**

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
（完整的使用代码，包含 import、props 传递、回调函数等）
\`\`\`

---

### MyRareComponent（使用 1 次）

**来源**：`@/components/MyRareComponent`

**使用位置**：

- src/pages/special/index.tsx

**代码示例**（来自 `src/pages/special/index.tsx`）：

\`\`\`tsx
（完整的使用代码）
\`\`\`
```

**规则 3：为每个 Hook 提供使用示例**

```markdown
## Hooks 使用示例

### useRequest（使用 45 次）

**代码示例**（来自 `src/pages/xxx.tsx`）：

\`\`\`tsx
（完整代码）
\`\`\`

---

### useMyCustomHook（使用 1 次）

**代码示例**（来自 `src/hooks/useMyCustomHook.ts`）：

\`\`\`tsx
（完整定义 + 使用示例）
\`\`\`
```

**规则 4：接口定义和调用示例**

遍历 `@/service/` 下的所有导入，为每个接口模块提供示例。

#### ⚠️ 禁止的做法

- ❌ 使用预定义的章节列表（"如何新建页面"、"如何创建表单"）
- ❌ 只输出高频组件，忽略低频组件
- ❌ 用统计数字代替代码示例

#### ✅ 正确的做法

- ✅ 遍历物资清单中的每一项
- ✅ 即使只使用 1 次的组件，也提供完整的使用示例
- ✅ 章节结构由数据决定，而不是模板决定

### 阶段 S5：清理临时文件

```bash
rm -f /tmp/_codebase_analysis.json /tmp/_dev_patterns.json /tmp/_codebase_analysis_batch_*.json
```

---

## Shell 工具辅助（所有模式适用）

对于简单的统计查询，优先使用 grep / ripgrep，而不是读取文件。

### 示例指令

| 需求            | 错误做法                   | 正确做法                                              |
| --------------- | -------------------------- | ----------------------------------------------------- |
| 确认路由库      | 打开文件看看用了什么路由库 | `grep -r "react-router" package.json src/`            |
| 统计组件数量    | 逐个打开组件文件           | `find src/components -name "*.tsx" \| wc -l`          |
| 查找 API 调用   | 读取所有 service 文件      | `grep -r "import.*axios" src/`                        |
| 统计 Hooks 使用 | 遍历所有文件               | `grep -rn "use[A-Z]" src/ --include="*.ts*" \| wc -l` |

---

## view_file 使用边界（重要）

**Read/view_file 只能用于定性分析（Qualitative Analysis），不能用于定量分析（Quantitative Analysis）。**

### 允许的使用场景

- 读取 `src/app.ts` 或 `src/layouts/index.tsx` 来理解"代码风格"（缩进、命名规范、注释习惯）
- 读取配置文件（`package.json`、`tsconfig.json`）了解项目配置
- 读取抽样脚本选中的代表性文件

### 禁止的使用场景

- 为了统计"有多少个页面使用了表格组件"而通过 view_file 打开每一页
- 为了统计组件数量而逐个打开组件文件
- 任何目的为"统计"或"计数"的文件遍历

---

## 分析检查清单

完成分析前，确认以下信息已提取：

- [ ] 技术栈版本信息
- [ ] 项目目录结构
- [ ] 文件/函数/组件命名规范
- [ ] 组件定义和使用示例（至少 3 个）
- [ ] 路由配置完整列表
- [ ] 状态管理使用示例
- [ ] API 调用封装和使用示例
- [ ] 样式方案和使用示例
- [ ] 多方案场景记录（如有）
- [ ] 关键文件索引

---

## 输出模板

模板位于：`assets/dev-guide-template.md`

根据实际分析结果填充模板，删除不适用的章节。

输出文件命名：`DEV-GUIDE.md`（放在项目根目录）
