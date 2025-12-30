# Swagger 解析模式

## 接口识别规则

### CRUD 接口模式

```yaml
# 标准 CRUD 接口命名
patterns:
  - path: "*/page"
    method: POST
    type: "分页查询"
    
  - path: "*/list"
    method: POST|GET
    type: "列表查询"
    
  - path: "*/detail"
    method: POST|GET
    params: "id"
    type: "详情查询"
    
  - path: "*/insert"
    method: POST
    type: "新增"
    
  - path: "*/update"
    method: POST|PUT
    type: "更新"
    
  - path: "*/deletes"
    method: POST|DELETE
    params: "ids"
    type: "批量删除"
    
  - path: "*/delete"
    method: POST|DELETE
    params: "id"
    type: "单条删除"
```

### 下拉选项接口

```yaml
patterns:
  - path: "**/select"
    type: "下拉选项"
    
  - path: "**/options"
    type: "下拉选项"
    
  - path: "**/fuzzy/*"
    type: "模糊搜索"
    params: "searchValue"
```

## Schema 类型映射

### 基础类型

| Swagger Type | Swagger Format | TypeScript Type |
|--------------|----------------|-----------------|
| integer | int32 | number |
| integer | int64 | number |
| number | float | number |
| number | double | number |
| string | - | string |
| string | date | string |
| string | date-time | string |
| string | email | string |
| string | uri | string |
| boolean | - | boolean |

### 复合类型

| Swagger Type | TypeScript Type |
|--------------|-----------------|
| array | T[] |
| object | interface |
| $ref | 引用对应 interface |
| additionalProperties | Record<string, T> |
| enum | 联合类型 |

### 枚举处理

```json
// Swagger
{
  "type": "string",
  "enum": ["ACTIVE", "INACTIVE"]
}

// TypeScript
type Status = 'ACTIVE' | 'INACTIVE';
```

```json
// Swagger (带 title 标注)
{
  "title": "ENUM/com.example.StatusEnum",
  "type": "integer",
  "format": "int32"
}

// TypeScript - 识别为枚举，生成注释说明
/** 状态枚举 @see StatusEnum */
status?: number;
```

## Schema 命名规范识别

### 常见后缀

```yaml
suffixes:
  "VO": "响应数据对象"
  "DTO": "数据传输对象"
  "Param": "请求参数"
  "InsertParam": "新增参数"
  "UpdateParam": "更新参数"
  "Query": "查询参数"
  "PageQuery": "分页查询参数"
  "Request": "请求对象"
  "Response": "响应对象"
```

### 生成策略

```typescript
// InsertParam → 必填字段不加 ?
export interface UserInsertParam {
  name: string;      // 必填
  email: string;     // 必填
  phone?: string;    // 选填
}

// UpdateParam → 继承 InsertParam + id
export interface UserUpdateParam extends UserInsertParam {
  id: number;
}

// VO → 所有字段可能为可选（来自数据库）
export interface UserVO {
  id: number;
  name?: string;
  email?: string;
  createTime?: string;
}
```

## 响应结构解析

### 通用响应包装

```json
{
  "ResultXxx": {
    "properties": {
      "resultCode": { "type": "integer" },
      "resultMsg": { "type": "string" },
      "data": { "$ref": "#/.../Xxx" },
      "success": { "type": "boolean" }
    }
  }
}
```

生成：
```typescript
// 通用响应类型
export interface Result<T> {
  resultCode: number;
  resultMsg: string;
  data: T;
  success: boolean;
}
```

### 分页响应

```json
{
  "PageInfo": {
    "properties": {
      "list": { "type": "array", "items": {...} },
      "total": { "type": "integer" },
      "pageNum": { "type": "integer" },
      "pageSize": { "type": "integer" }
    }
  }
}
```

生成：
```typescript
export interface PageResult<T> {
  list: T[];
  total: number;
  pageNum: number;
  pageSize: number;
}
```

## 参数解析

### Query 参数

```json
{
  "parameters": [
    {
      "name": "id",
      "in": "query",
      "required": true,
      "schema": { "type": "integer" }
    }
  ]
}
```

生成：
```typescript
export async function getDetail(id: number) {
  return request.post('/detail', null, { params: { id } });
}
```

### Body 参数

```json
{
  "requestBody": {
    "content": {
      "application/json": {
        "schema": { "$ref": "#/.../InsertParam" }
      }
    }
  }
}
```

生成：
```typescript
export async function insert(data: InsertParam) {
  return request.post('/insert', data);
}
```

### Path 参数

```json
{
  "path": "/user/{id}",
  "parameters": [
    {
      "name": "id",
      "in": "path",
      "required": true
    }
  ]
}
```

生成：
```typescript
export async function getUser(id: number) {
  return request.get(`/user/${id}`);
}
```

## Tag 分组

根据 Swagger tags 将接口分组到不同模块：

```json
{
  "tags": [
    { "name": "用户管理", "description": "用户相关接口" },
    { "name": "订单管理", "description": "订单相关接口" }
  ]
}
```

```
生成目录结构：
src/pages/
├── UserManagement/
│   ├── api.ts         # 用户管理相关接口
│   └── types.ts
└── OrderManagement/
    ├── api.ts         # 订单管理相关接口
    └── types.ts
```

## 字段注释保留

```json
{
  "properties": {
    "companyName": {
      "type": "string",
      "description": "公司名称",
      "maxLength": 100
    }
  }
}
```

生成：
```typescript
export interface CompanyVO {
  /** 公司名称 */
  companyName?: string;
}
```
