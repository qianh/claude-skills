# UI 组件映射规则

## PRD 元素识别

### 表格相关

| PRD 描述 | 识别特征 | 组件类型 |
|----------|----------|----------|
| 数据列表/表格 | 行列结构、表头、分页 | Table |
| 操作列 | "操作"/"Actions" 列 | Table Actions |
| 表格筛选 | 表头带筛选图标 | Column Filter |
| 表格排序 | 表头带排序图标 | Column Sorter |
| 选择行 | 复选框列 | rowSelection |

### 表单相关

| PRD 描述 | 识别特征 | 组件类型 |
|----------|----------|----------|
| 文本输入框 | 单行输入、placeholder | Input |
| 多行文本 | 多行输入区域 | Input.TextArea |
| 密码输入 | 密码、**** 显示 | Input.Password |
| 数字输入 | 数字、计数器 | InputNumber |
| 下拉选择 | 下拉框、选项列表 | Select |
| 远程搜索下拉 | "可输入搜索"、"模糊搜索" | Select + onSearch |
| 日期选择 | 日期、日历图标 | DatePicker |
| 日期范围 | 开始/结束日期 | DatePicker.RangePicker |
| 时间选择 | 时间、时分秒 | TimePicker |
| 开关 | 开/关、启用/禁用 | Switch |
| 单选 | 单选按钮组 | Radio.Group |
| 多选 | 复选框组 | Checkbox.Group |
| 文件上传 | 上传、附件 | Upload |

### 布局相关

| PRD 描述 | 识别特征 | 组件类型 |
|----------|----------|----------|
| 标签页 | Tab 切换 | Tabs |
| 卡片区域 | 带边框的区块 | Card |
| 折叠面板 | 可展开/收起 | Collapse |
| 步骤条 | 步骤1、2、3 | Steps |
| 弹窗 | 对话框、模态框 | Modal |
| 抽屉 | 侧边滑出 | Drawer |

### 反馈相关

| PRD 描述 | 识别特征 | 组件类型 |
|----------|----------|----------|
| 确认框 | "确认删除?" | Modal.confirm / Popconfirm |
| 提示信息 | 成功/失败提示 | message |
| 通知 | 右上角通知 | notification |
| 加载中 | loading 状态 | Spin / Loading |

## 字段类型推断

### 从字段名推断

```yaml
patterns:
  # 日期时间
  - names: ["*Time", "*Date", "*At", "createTime", "updateTime"]
    type: DatePicker
    format: "YYYY-MM-DD HH:mm:ss"
    
  # 日期（无时间）
  - names: ["birthday", "startDate", "endDate"]
    type: DatePicker
    format: "YYYY-MM-DD"
    
  # 邮箱
  - names: ["*email*", "*Email*"]
    type: Input
    rules: [{ type: 'email' }]
    
  # 手机号
  - names: ["*phone*", "*mobile*", "*tel*"]
    type: Input
    rules: [{ pattern: /^1\d{10}$/ }]
    
  # 金额
  - names: ["*amount*", "*price*", "*fee*", "*cost*"]
    type: InputNumber
    precision: 2
    
  # 数量
  - names: ["*count*", "*num*", "*qty*", "*quantity*"]
    type: InputNumber
    precision: 0
    min: 0
    
  # 百分比
  - names: ["*rate*", "*ratio*", "*percent*"]
    type: InputNumber
    precision: 2
    min: 0
    max: 100
    
  # 状态
  - names: ["status", "state", "*Status"]
    type: Select
    
  # 类型
  - names: ["type", "*Type"]
    type: Select
    
  # 备注
  - names: ["remark", "note", "description", "memo"]
    type: Input.TextArea
    
  # 密码
  - names: ["*password*", "*pwd*"]
    type: Input.Password
    
  # 开关
  - names: ["is*", "has*", "*Enable*", "*Enabled*"]
    type: Switch
```

### 从 Swagger 类型推断

```yaml
swagger_to_component:
  - swagger: { type: "string", format: "date-time" }
    component: DatePicker
    props: { showTime: true }
    
  - swagger: { type: "string", format: "date" }
    component: DatePicker
    
  - swagger: { type: "boolean" }
    component: Switch
    
  - swagger: { type: "integer" }
    component: InputNumber
    props: { precision: 0 }
    
  - swagger: { type: "number" }
    component: InputNumber
    props: { precision: 2 }
    
  - swagger: { type: "array" }
    component: Select
    props: { mode: "multiple" }
    
  - swagger: { enum: [...] }
    component: Select
    options: "从 enum 生成"
```

## PRD 描述映射

### 必填标识

```yaml
required_patterns:
  - "*"                    # 标注星号
  - "必填"
  - "required"
  - "不能为空"
  - "必须填写"
```

### 校验规则描述

```yaml
validation_patterns:
  - pattern: "最多{n}个字符"
    rule: { max: n }
    
  - pattern: "最少{n}个字符"
    rule: { min: n }
    
  - pattern: "{min}-{max}个字符"
    rule: { min: min, max: max }
    
  - pattern: "邮箱格式"
    rule: { type: 'email' }
    
  - pattern: "手机号格式"
    rule: { pattern: /^1\d{10}$/ }
```

### 交互描述

```yaml
interaction_patterns:
  - pattern: "点击【XX】按钮"
    action: "onClick handler"
    
  - pattern: "选择后自动填充"
    action: "onChange + 联动更新"
    
  - pattern: "输入时搜索"
    action: "onSearch + 防抖"
    
  - pattern: "下拉项从XX获取"
    action: "远程加载选项"
    
  - pattern: "根据XX显示/隐藏"
    action: "条件渲染"
```

## 组件代码生成

### 表格列定义

```typescript
// 基础列
{ title: 'ID', dataIndex: 'id', width: 80 }

// 带格式化
{ 
  title: '金额', 
  dataIndex: 'amount',
  render: (val) => val?.toLocaleString()
}

// 带标签
{
  title: '状态',
  dataIndex: 'status',
  render: (val) => <Tag color={statusColorMap[val]}>{statusTextMap[val]}</Tag>
}

// 日期格式化
{
  title: '创建时间',
  dataIndex: 'createTime',
  render: (val) => val ? dayjs(val).format('YYYY-MM-DD HH:mm:ss') : '-'
}

// 操作列
{
  title: '操作',
  key: 'action',
  fixed: 'right',
  width: 150,
  render: (_, record) => (
    <Space>
      <a onClick={() => handleEdit(record)}>编辑</a>
      <a onClick={() => handleDelete([record.id])}>删除</a>
    </Space>
  )
}
```

### 表单项定义

```typescript
// 必填输入框
<Form.Item
  name="name"
  label="名称"
  rules={[{ required: true, message: '请输入名称' }]}
>
  <Input placeholder="请输入名称" maxLength={50} />
</Form.Item>

// 下拉选择
<Form.Item name="type" label="类型">
  <Select options={typeOptions} placeholder="请选择类型" />
</Form.Item>

// 远程搜索
<Form.Item name="userId" label="用户">
  <SearchSelect
    request={fetchUserOptions}
    placeholder="请输入搜索"
  />
</Form.Item>

// 日期范围
<Form.Item name="dateRange" label="日期范围">
  <DatePicker.RangePicker style={{ width: '100%' }} />
</Form.Item>

// 开关
<Form.Item name="isEnable" label="启用" valuePropName="checked">
  <Switch />
</Form.Item>
```

## 规范适配

当识别到项目使用特定组件时，替换为对应组件：

```yaml
component_mapping:
  # 检测到使用 StandardTable
  - detect: "import StandardTable from '@/components/StandardTable'"
    replace_table: StandardTable
    
  # 检测到使用 SearchSelect
  - detect: "import SearchSelect from '@/components/SearchSelect'"
    replace_remote_select: SearchSelect
    
  # 检测到使用 FormFields
  - detect: "import { InputFormItem } from '@/components/FormFields'"
    replace_form_items: true
    
  # 检测到使用 useModalSet
  - detect: "import { useModalSet } from '@/hooks/ModalHooks'"
    replace_modal_management: useModalSet
```
