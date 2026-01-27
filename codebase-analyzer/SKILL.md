---
name: codebase-analyzer
description: 深度分析项目代码库，生成完整的开发指导手册。扫描所有代码文件，提取技术框架、编码风格、组件模式、路由配置、状态管理、API调用方式等信息，识别同一场景的多种实现方案，输出结构化的 Markdown 开发手册供 AI 后续开发参考。当用户请求"分析项目"、"生成开发手册"、"了解项目结构"、"提取编码规范"、"分析代码库"时使用此技能。
---

# Codebase Analyzer

分析项目代码库，生成开发指导手册。

## 工作流程

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

## 输出模板

模板位于：`assets/dev-guide-template.md`

根据实际分析结果填充模板，删除不适用的章节。
