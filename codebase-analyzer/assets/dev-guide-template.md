# {项目名称} 开发操作手册

> 本手册由 AI 自动分析生成，包含项目中所有开发场景的**完整代码示例**。
> 新功能开发时，请严格参照本手册中的模式执行。
>
> 生成时间：{生成时间}

---

## 快速导航

| 我想要...       | 跳转到                                |
| --------------- | ------------------------------------- |
| 新建一个页面    | [如何新建页面](#如何新建页面)         |
| 创建一个组件    | [如何创建组件](#如何创建组件)         |
| 添加一个表单    | [如何创建表单](#如何创建表单)         |
| 添加一个表格    | [如何创建表格](#如何创建表格)         |
| 添加新接口      | [如何添加接口](#如何添加接口)         |
| 写组件样式      | [如何编写样式](#如何编写样式)         |
| 配置新路由      | [如何添加路由](#如何添加路由)         |
| 使用全局状态    | [如何使用状态管理](#如何使用状态管理) |
| 创建弹窗/抽屉   | [如何创建弹窗](#如何创建弹窗)         |
| 编写自定义 Hook | [如何编写 Hooks](#如何编写hooks)      |

---

## 项目概览

### 技术栈

| 类别     | 技术                        | 版本   |
| -------- | --------------------------- | ------ |
| 框架     | {React/Vue/Next.js}         | {版本} |
| 语言     | {TypeScript/JavaScript}     | {版本} |
| UI 库    | {Ant Design/Element Plus}   | {版本} |
| 状态管理 | {Redux/Zustand/Pinia}       | {版本} |
| 样式方案 | {LESS/Tailwind/CSS Modules} | -      |
| 构建工具 | {Vite/Webpack}              | {版本} |

### 目录结构

```
src/
├── components/     # 公共组件（新建组件放这里）
├── pages/          # 页面（新建页面放这里）
├── service/        # API 接口定义（新建接口放这里）
├── hooks/          # 自定义 Hooks
├── store/          # 状态管理
├── utils/          # 工具函数
├── types/          # 类型定义
└── styles/         # 全局样式
```

---

## 如何新建页面

### 步骤

1. 在 `src/pages/` 下创建页面目录，如 `src/pages/user-management/`
2. 创建页面主文件 `index.tsx`
3. 在路由配置中添加路由（见 [如何添加路由](#如何添加路由)）

### 代码示例

**来源**：`{实际文件路径}`

```tsx
{
  从项目中提取的完整页面代码;
}
```

### 页面结构说明

```tsx
// 1. 导入依赖
import React, { useState, useEffect, useRef } from "react";
import { Form, Button, message } from "antd";
import { xxxListPost } from "@/service/xxx";

// 2. 定义类型（如果有）
interface PageProps {
  // ...
}

// 3. 页面组件
const XxxPage: React.FC<PageProps> = () => {
  // 3.1 状态定义
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  // 3.2 生命周期
  useEffect(() => {
    // 初始化逻辑
  }, []);

  // 3.3 事件处理
  const handleSubmit = async () => {
    // ...
  };

  // 3.4 渲染
  return <div>{/* 页面内容 */}</div>;
};

export default XxxPage;
```

---

## 如何创建组件

### 步骤

1. 在 `src/components/` 下创建组件目录，如 `src/components/UserCard/`
2. 创建组件文件 `index.tsx`
3. 定义 Props 接口
4. 导出组件

### 代码示例

**来源**：`{实际文件路径}`

```tsx
{从项目中提取的完整组件代码，包含 Props 定义}
```

### 组件结构说明

```tsx
import React from "react";
import styles from "./index.module.less";

// 1. Props 类型定义（必须）
interface UserCardProps {
  name: string;
  avatar?: string;
  onClick?: () => void;
}

// 2. 组件实现
const UserCard: React.FC<UserCardProps> = ({ name, avatar, onClick }) => {
  return (
    <div className={styles.card} onClick={onClick}>
      <img src={avatar} alt={name} />
      <span>{name}</span>
    </div>
  );
};

export default UserCard;
```

---

## 如何创建表单

### 步骤

1. 使用 `Form.useForm()` 创建表单实例
2. 使用 `<Form>` 和 `<Form.Item>` 构建表单结构
3. 定义 `onFinish` 处理提交

### 代码示例

**来源**：`{实际文件路径}`

```tsx
{
  从项目中提取的完整表单代码;
}
```

### 表单结构说明

```tsx
import { Form, Input, Button, message } from "antd";

const MyForm: React.FC = () => {
  // 1. 创建表单实例
  const [form] = Form.useForm();

  // 2. 提交处理
  const onFinish = async (values: any) => {
    try {
      await submitApi(values);
      message.success("提交成功");
    } catch (error) {
      message.error("提交失败");
    }
  };

  // 3. 表单结构
  return (
    <Form form={form} onFinish={onFinish} layout="vertical">
      <Form.Item
        name="username"
        label="用户名"
        rules={[{ required: true, message: "请输入用户名" }]}
      >
        <Input placeholder="请输入用户名" />
      </Form.Item>

      <Form.Item
        name="email"
        label="邮箱"
        rules={[
          { required: true, message: "请输入邮箱" },
          { type: "email", message: "邮箱格式不正确" },
        ]}
      >
        <Input placeholder="请输入邮箱" />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          提交
        </Button>
      </Form.Item>
    </Form>
  );
};
```

---

## 如何创建表格

### 步骤

1. 定义 `columns` 配置
2. 获取数据源 `dataSource`
3. 配置分页、筛选等功能

### 代码示例

**来源**：`{实际文件路径}`

```tsx
{从项目中提取的完整表格代码，包含 columns 定义}
```

### 表格结构说明

```tsx
import { Table } from "antd";
import type { ColumnsType } from "antd/es/table";

// 1. 定义数据类型
interface UserRecord {
  id: number;
  name: string;
  email: string;
  status: string;
}

// 2. 定义列配置
const columns: ColumnsType<UserRecord> = [
  {
    title: "姓名",
    dataIndex: "name",
    key: "name",
  },
  {
    title: "邮箱",
    dataIndex: "email",
    key: "email",
  },
  {
    title: "状态",
    dataIndex: "status",
    key: "status",
    render: (status) => (
      <Tag color={status === "active" ? "green" : "red"}>{status}</Tag>
    ),
  },
  {
    title: "操作",
    key: "action",
    render: (_, record) => (
      <Space>
        <Button type="link" onClick={() => handleEdit(record)}>
          编辑
        </Button>
        <Button type="link" danger onClick={() => handleDelete(record.id)}>
          删除
        </Button>
      </Space>
    ),
  },
];

// 3. 使用表格
<Table
  columns={columns}
  dataSource={dataSource}
  rowKey="id"
  pagination={{
    current: page,
    pageSize: 10,
    total: total,
    onChange: (page) => setPage(page),
  }}
  loading={loading}
/>;
```

---

## 如何添加接口

### 步骤

1. 在 `src/service/` 下找到或创建对应模块文件
2. 定义接口函数
3. 在组件中导入并调用

### 接口定义示例

**来源**：`{实际文件路径}`

```typescript
{从项目中提取的完整 Service 定义代码}
```

### 接口定义结构说明

```typescript
// src/service/user.ts
import request from "@/service/request";

// 定义 URL 常量
const USER_URLS = {
  list: "/api/user/list",
  detail: "/api/user/detail",
  create: "/api/user/create",
  update: "/api/user/update",
  delete: "/api/user/delete",
};

// 获取用户列表
export function userListPost(params: UserListParams) {
  return request({
    url: USER_URLS.list,
    method: "POST",
    data: params,
  });
}

// 获取用户详情
export function userDetailGet(id: number) {
  return request({
    url: `${USER_URLS.detail}/${id}`,
    method: "GET",
  });
}
```

### 接口调用示例

**来源**：`{实际文件路径}`

```tsx
{
  从项目中提取的完整接口调用代码;
}
```

### 接口调用结构说明

```tsx
import { useState, useEffect } from 'react';
import { message } from 'antd';
import { userListPost } from '@/service/user';

const UserList: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState([]);

  // 获取数据
  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await userListPost({ page: 1, pageSize: 10 });
      if (res.code === 0) {
        setDataSource(res.data.list);
      } else {
        message.error(res.message);
      }
    } catch (error) {
      message.error('请求失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    // ...
  );
};
```

---

## 如何编写样式

### 步骤

1. 在组件目录下创建样式文件（如 `index.less` 或 `index.module.less`）
2. 编写样式类
3. 在组件中导入并使用

### 代码示例

**来源**：`{实际文件路径}`

```less
{从项目中提取的完整样式代码}
```

### 样式结构说明

```less
// src/components/UserCard/index.less

// 使用嵌套结构
.user-card {
  padding: 16px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  &-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
  }

  &-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
  }

  &-name {
    font-size: 16px;
    font-weight: 500;
    color: #333;
  }

  // 悬停状态
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}
```

### 在组件中使用

```tsx
import './index.less';
// 或 CSS Modules
import styles from './index.module.less';

// 普通 LESS
<div className="user-card">...</div>

// CSS Modules
<div className={styles.userCard}>...</div>
```

---

## 如何添加路由

### 步骤

1. 在路由配置文件中添加路由项
2. 确保页面组件已创建

### 代码示例

**来源**：`{实际路由配置文件路径}`

```typescript
{
  从项目中提取的完整路由配置代码;
}
```

### 路由配置结构说明

```typescript
// config/routes.ts 或 src/routes.ts

export default [
  {
    path: "/",
    redirect: "/home",
  },
  {
    path: "/home",
    component: "./home",
    name: "首页",
  },
  {
    path: "/user",
    name: "用户管理",
    routes: [
      {
        path: "/user/list",
        component: "./user/list",
        name: "用户列表",
      },
      {
        path: "/user/detail/:id",
        component: "./user/detail",
        name: "用户详情",
      },
    ],
  },
];
```

---

## 如何使用状态管理

### 步骤

1. 在 `src/store/` 或 `src/models/` 下定义 Store
2. 在组件中使用 `useSelector` 获取状态
3. 使用 `dispatch` 更新状态

### Store 定义示例

**来源**：`{实际文件路径}`

```typescript
{从项目中提取的完整 Store 定义代码}
```

### Store 使用示例

**来源**：`{实际文件路径}`

```tsx
{从项目中提取的完整 Store 使用代码}
```

### 结构说明

```typescript
// src/store/user.ts
import { createSlice } from "@reduxjs/toolkit";

const userSlice = createSlice({
  name: "user",
  initialState: {
    currentUser: null,
    loading: false,
  },
  reducers: {
    setCurrentUser: (state, action) => {
      state.currentUser = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
  },
});

export const { setCurrentUser, setLoading } = userSlice.actions;
export default userSlice.reducer;

// 在组件中使用
import { useSelector, useDispatch } from "react-redux";
import { setCurrentUser } from "@/store/user";

const MyComponent = () => {
  const currentUser = useSelector((state) => state.user.currentUser);
  const dispatch = useDispatch();

  const updateUser = (user) => {
    dispatch(setCurrentUser(user));
  };
};
```

---

## 如何创建弹窗

### 步骤

1. 定义弹窗显示状态 `visible` / `open`
2. 配置 Modal/Drawer 组件
3. 处理确认和取消回调

### 代码示例

**来源**：`{实际文件路径}`

```tsx
{从项目中提取的完整 Modal/Drawer 代码}
```

### 弹窗结构说明

```tsx
import { useState } from "react";
import { Modal, Form, Input, message } from "antd";

interface EditModalProps {
  visible: boolean;
  record?: UserRecord;
  onCancel: () => void;
  onSuccess: () => void;
}

const EditModal: React.FC<EditModalProps> = ({
  visible,
  record,
  onCancel,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // 打开时填充表单
  useEffect(() => {
    if (visible && record) {
      form.setFieldsValue(record);
    }
  }, [visible, record]);

  // 提交
  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      await updateUserApi(values);
      message.success("保存成功");
      onSuccess();
    } catch (error) {
      message.error("保存失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="编辑用户"
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      confirmLoading={loading}
      destroyOnClose
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
};
```

---

## 如何编写 Hooks

### 步骤

1. 在 `src/hooks/` 下创建 Hook 文件
2. 以 `use` 开头命名
3. 导出 Hook 函数

### 代码示例

**来源**：`{实际文件路径}`

```typescript
{从项目中提取的完整 Hook 代码}
```

### Hook 结构说明

```typescript
// src/hooks/useRequest.ts
import { useState, useCallback } from "react";
import { message } from "antd";

interface UseRequestOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export function useRequest<T>(
  apiFn: (...args: any[]) => Promise<T>,
  options?: UseRequestOptions<T>,
) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const run = useCallback(
    async (...args: any[]) => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFn(...args);
        setData(result);
        options?.onSuccess?.(result);
        return result;
      } catch (err) {
        setError(err as Error);
        options?.onError?.(err as Error);
        message.error("请求失败");
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFn],
  );

  return { loading, data, error, run };
}

// 使用示例
const { loading, data, run } = useRequest(getUserList);
useEffect(() => {
  run();
}, []);
```

---

## 附录：类型定义规范

### 代码示例

**来源**：`{实际文件路径}`

```typescript
{
  从项目中提取的完整类型定义代码;
}
```

### 类型定义结构说明

```typescript
// src/types/user.ts

// 接口响应类型
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

// 分页响应
export interface PaginatedResponse<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

// 实体类型
export interface User {
  id: number;
  name: string;
  email: string;
  avatar?: string;
  status: "active" | "inactive";
  createdAt: string;
  updatedAt: string;
}

// 请求参数类型
export interface UserListParams {
  page?: number;
  pageSize?: number;
  keyword?: string;
  status?: string;
}
```

---

## 附录：项目特有约定

### 命名规范

| 类型     | 规范                    | 示例            |
| -------- | ----------------------- | --------------- |
| 组件文件 | PascalCase              | `UserCard.tsx`  |
| 工具函数 | camelCase               | `formatDate.ts` |
| 样式文件 | kebab-case 或与组件同名 | `index.less`    |
| 接口函数 | camelCase + 动词        | `userListPost`  |
| 常量     | UPPER_SNAKE_CASE        | `MAX_PAGE_SIZE` |

### 注意事项

{从项目分析中提取的特有约定和注意事项}

---

> 本手册自动生成，如有疑问请参考对应的源代码文件。
