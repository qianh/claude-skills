# 默认代码约定

当用户未提供开发规范文档时，使用以下默认约定生成代码。

## 项目结构

```
src/
├── pages/
│   └── {ModuleName}/
│       ├── index.tsx          # 页面入口
│       ├── api.ts             # API 调用
│       ├── types.ts           # 类型定义
│       └── components/        # 子组件
│           ├── EditModal.tsx
│           └── SearchForm.tsx
├── components/                # 共享组件
├── services/                  # 通用 API
│   └── request.ts
├── hooks/                     # 自定义 Hooks
└── utils/                     # 工具函数
```

## 技术栈

- React 18+
- TypeScript 4+
- Ant Design 5+
- 状态管理: React Hooks (useState, useEffect, useCallback)

## 导入规范

```typescript
// React
import React, { useState, useEffect, useCallback } from 'react';

// Ant Design
import { Card, Table, Button, Space, Form, Input, Select, Modal, message } from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

// 项目内部
import request from '@/services/request';
import type { ... } from './types';
import { ... } from './api';
```

## API 封装 (默认)

```typescript
// services/request.ts
import axios from 'axios';

const instance = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

instance.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
);

export default instance;
```

## API 调用模式

```typescript
// pages/XXX/api.ts
import request from '@/services/request';
import type { QueryParam, ItemVO, InsertParam, UpdateParam } from './types';

const BASE_URL = '/module';

/** 分页查询 */
export async function queryPage(params: QueryParam) {
  return request.post(`${BASE_URL}/page`, params);
}

/** 详情 */
export async function getDetail(id: number) {
  return request.post(`${BASE_URL}/detail`, null, { params: { id } });
}

/** 新增 */
export async function insert(data: InsertParam) {
  return request.post(`${BASE_URL}/insert`, data);
}

/** 更新 */
export async function update(data: UpdateParam) {
  return request.post(`${BASE_URL}/update`, data);
}

/** 删除 */
export async function remove(ids: number[]) {
  return request.post(`${BASE_URL}/deletes`, null, { params: { ids } });
}
```

## 类型定义模式

```typescript
// pages/XXX/types.ts

/** 通用响应 */
export interface Result<T = unknown> {
  resultCode: number;
  resultMsg: string;
  data: T;
  success: boolean;
}

/** 分页响应 */
export interface PageResult<T> {
  list: T[];
  total: number;
  pageNum: number;
  pageSize: number;
}

/** 查询参数 */
export interface QueryParam {
  pageNum?: number;
  pageSize?: number;
  // ... 查询字段
}

/** 实体 VO */
export interface ItemVO {
  id: number;
  // ... 字段
  createBy?: string;
  createTime?: string;
  modifyBy?: string;
  modifyTime?: string;
}

/** 新增参数 */
export interface InsertParam {
  // 必填字段无 ?
  // 选填字段有 ?
}

/** 更新参数 */
export interface UpdateParam extends InsertParam {
  id: number;
}
```

## 页面组件模式

```tsx
// pages/XXX/index.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Form, Modal, message } from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { queryPage, remove } from './api';
import type { ItemVO, QueryParam } from './types';
import EditModal from './components/EditModal';

const Page: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [dataSource, setDataSource] = useState<ItemVO[]>([]);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20 });
  const [modalVisible, setModalVisible] = useState(false);
  const [currentRecord, setCurrentRecord] = useState<ItemVO>();

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const values = form.getFieldsValue();
      const params: QueryParam = {
        ...values,
        pageNum: pagination.current,
        pageSize: pagination.pageSize,
      };
      const res = await queryPage(params);
      if (res.success) {
        setDataSource(res.data?.list || []);
        setTotal(res.data?.total || 0);
      }
    } catch (error) {
      message.error('查询失败');
    } finally {
      setLoading(false);
    }
  }, [form, pagination]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSearch = () => {
    setPagination((prev) => ({ ...prev, current: 1 }));
  };

  const handleReset = () => {
    form.resetFields();
    setPagination({ current: 1, pageSize: 20 });
  };

  const handleAdd = () => {
    setCurrentRecord(undefined);
    setModalVisible(true);
  };

  const handleEdit = (record: ItemVO) => {
    setCurrentRecord(record);
    setModalVisible(true);
  };

  const handleDelete = (ids: number[]) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除选中的 ${ids.length} 条记录吗？`,
      onOk: async () => {
        await remove(ids);
        message.success('删除成功');
        fetchData();
      },
    });
  };

  const columns: ColumnsType<ItemVO> = [
    // 根据 PRD 生成
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <a onClick={() => handleEdit(record)}>编辑</a>
          <a onClick={() => handleDelete([record.id])}>删除</a>
        </Space>
      ),
    },
  ];

  return (
    <Card title="页面标题">
      {/* 搜索表单 */}
      <Form form={form} layout="inline" style={{ marginBottom: 16 }}>
        {/* 根据 PRD 生成搜索字段 */}
        <Form.Item>
          <Space>
            <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
              查询
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {/* 操作按钮 */}
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增
        </Button>
      </Space>

      {/* 数据表格 */}
      <Table
        loading={loading}
        dataSource={dataSource}
        columns={columns}
        rowKey="id"
        pagination={{
          ...pagination,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (t) => `共 ${t} 条`,
          onChange: (page, pageSize) => setPagination({ current: page, pageSize }),
        }}
      />

      {/* 编辑弹窗 */}
      <EditModal
        visible={modalVisible}
        record={currentRecord}
        onCancel={() => setModalVisible(false)}
        onSuccess={() => {
          setModalVisible(false);
          fetchData();
        }}
      />
    </Card>
  );
};

export default Page;
```

## 弹窗组件模式

```tsx
// pages/XXX/components/EditModal.tsx
import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Select, message, Spin } from 'antd';
import { getDetail, insert, update } from '../api';
import type { ItemVO, InsertParam, UpdateParam } from '../types';

interface Props {
  visible: boolean;
  record?: ItemVO;
  onCancel: () => void;
  onSuccess: () => void;
}

const EditModal: React.FC<Props> = ({ visible, record, onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const isEdit = !!record?.id;

  useEffect(() => {
    if (visible && record?.id) {
      setDetailLoading(true);
      getDetail(record.id)
        .then((res) => {
          if (res.success) {
            form.setFieldsValue(res.data);
          }
        })
        .finally(() => setDetailLoading(false));
    } else if (!visible) {
      form.resetFields();
    }
  }, [visible, record, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      if (isEdit) {
        await update({ ...values, id: record!.id });
        message.success('更新成功');
      } else {
        await insert(values);
        message.success('新增成功');
      }
      onSuccess();
    } catch (error: any) {
      if (!error.errorFields) {
        message.error('操作失败');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑' : '新增'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      destroyOnClose
      width={600}
    >
      <Spin spinning={detailLoading}>
        <Form form={form} layout="vertical">
          {/* 根据 PRD 生成表单字段 */}
        </Form>
      </Spin>
    </Modal>
  );
};

export default EditModal;
```

## 远程搜索 Select

```tsx
import React, { useState, useMemo } from 'react';
import { Select, Spin } from 'antd';
import { debounce } from 'lodash';

interface Props {
  value?: number;
  onChange?: (value: number) => void;
  fetchOptions: (keyword: string) => Promise<{ label: string; value: number }[]>;
}

const RemoteSelect: React.FC<Props> = ({ value, onChange, fetchOptions }) => {
  const [options, setOptions] = useState<{ label: string; value: number }[]>([]);
  const [fetching, setFetching] = useState(false);

  const handleSearch = useMemo(
    () =>
      debounce(async (keyword: string) => {
        if (!keyword?.trim()) {
          setOptions([]);
          return;
        }
        setFetching(true);
        try {
          const result = await fetchOptions(keyword);
          setOptions(result);
        } finally {
          setFetching(false);
        }
      }, 300),
    [fetchOptions]
  );

  return (
    <Select
      showSearch
      value={value}
      onChange={onChange}
      onSearch={handleSearch}
      filterOption={false}
      notFoundContent={fetching ? <Spin size="small" /> : '无匹配结果'}
      options={options}
      placeholder="请输入搜索"
      allowClear
    />
  );
};

export default RemoteSelect;
```
