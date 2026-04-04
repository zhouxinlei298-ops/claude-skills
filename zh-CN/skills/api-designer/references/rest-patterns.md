# REST 设计模式

## 面向资源的架构

REST API 围绕资源而非操作构建。资源是 API 的名词。

### 资源标识

**良好的资源 URI：**
```
GET    /users                  # 集合
GET    /users/{id}             # 单个资源
GET    /users/{id}/orders      # 嵌套集合
POST   /users                  # 创建资源
PUT    /users/{id}             # 替换资源
PATCH  /users/{id}             # 更新资源
DELETE /users/{id}             # 删除资源
```

**糟糕的资源 URI：**
```
POST   /getUser                # URI 中的动词
POST   /createUser             # URI 中的动词
GET    /user?action=delete     # 查询参数作为操作
```

### 资源命名约定

- 集合使用复数名词：`/users`、`/orders`、`/products`
- 使用小写和连字符以提高可读性：`/shipping-addresses`
- 避免深层嵌套（最多 2-3 层）：`/users/{id}/orders/{orderId}`
- 使用查询参数进行过滤：`/users?status=active&role=admin`

## HTTP 方法语义

### 安全和幂等方法

| 方法 | 安全 | 幂等 | 用例 |
|--------|------|------------|----------|
| GET | 是 | 是 | 检索资源 |
| POST | 否 | 否 | 创建资源、非幂等操作 |
| PUT | 否 | 是 | 替换整个资源 |
| PATCH | 否 | 否 | 部分更新 |
| DELETE | 否 | 是 | 移除资源 |
| HEAD | 是 | 是 | 仅获取元数据 |
| OPTIONS | 是 | 是 | 获取允许的方法 |

### 方法使用

**GET - 检索资源**
```http
GET /users/123
Accept: application/json

响应：200 OK
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**POST - 创建资源**
```http
POST /users
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane@example.com"
}

响应：201 Created
Location: /users/124
{
  "id": 124,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "created_at": "2024-01-16T14:20:00Z"
}
```

**PUT - 替换资源**
```http
PUT /users/123
Content-Type: application/json

{
  "name": "John Doe Updated",
  "email": "john.new@example.com"
}

响应：200 OK
{
  "id": 123,
  "name": "John Doe Updated",
  "email": "john.new@example.com",
  "updated_at": "2024-01-17T09:15:00Z"
}
```

**PATCH - 部分更新**
```http
PATCH /users/123
Content-Type: application/json

{
  "email": "john.updated@example.com"
}

响应：200 OK
{
  "id": 123,
  "name": "John Doe",
  "email": "john.updated@example.com",
  "updated_at": "2024-01-17T10:00:00Z"
}
```

**DELETE - 移除资源**
```http
DELETE /users/123

响应：204 No Content
```

## HTTP 状态码

### 成功代码（2xx）

- **200 OK** - 请求成功（GET、PUT、PATCH）
- **201 Created** - 资源已创建（POST），包含 Location 头
- **202 Accepted** - 请求已接受进行异步处理
- **204 No Content** - 成功但无响应体（DELETE）

### 重定向（3xx）

- **301 Moved Permanently** - 资源已永久移动
- **302 Found** - 临时重定向
- **304 Not Modified** - 缓存版本仍然有效

### 客户端错误（4xx）

- **400 Bad Request** - 无效的请求语法或验证错误
- **401 Unauthorized** - 需要身份验证或验证失败
- **403 Forbidden** - 已身份验证但未授权
- **404 Not Found** - 资源不存在
- **405 Method Not Allowed** - HTTP 方法不受资源支持
- **409 Conflict** - 请求与当前状态冲突（如重复）
- **422 Unprocessable Entity** - 语法有效但存在语义错误
- **429 Too Many Requests** - 超过速率限制

### 服务器错误（5xx）

- **500 Internal Server Error** - 意外的服务器错误
- **502 Bad Gateway** - 来自上游服务器的无效响应
- **503 Service Unavailable** - 服务器暂时不可用
- **504 Gateway Timeout** - 上游服务器超时

## HATEOAS（超媒体）

### 超媒体驱动的 API

包含到相关资源和可用操作的链接：

```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "_links": {
    "self": { "href": "/users/123" },
    "orders": { "href": "/users/123/orders" },
    "update": { "href": "/users/123", "method": "PATCH" },
    "delete": { "href": "/users/123", "method": "DELETE" }
  }
}
```

### HAL（超文本应用语言）

```json
{
  "id": 123,
  "name": "John Doe",
  "_links": {
    "self": { "href": "/users/123" }
  },
  "_embedded": {
    "orders": [
      {
        "id": 456,
        "total": 99.99,
        "_links": {
          "self": { "href": "/orders/456" }
        }
      }
    ]
  }
}
```

## 内容协商

### Accept 头

```http
GET /users/123
Accept: application/json

GET /users/123
Accept: application/xml

GET /users/123
Accept: application/hal+json
```

### 响应 Content-Type

```http
Content-Type: application/json; charset=utf-8
Content-Type: application/problem+json
Content-Type: application/hal+json
```

## 幂等性

### 幂等操作

**PUT - 始终幂等：**
多次相同的 PUT 请求产生与单次请求相同的结果。

**DELETE - 幂等：**
第一次 DELETE 返回 204，后续 DELETE 返回 404（相同结束状态）。

**POST - 默认非幂等：**
使用 `Idempotency-Key` 头进行幂等 POST：

```http
POST /payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "amount": 100.00,
  "currency": "USD"
}
```

服务器存储幂等性密钥并为重复请求返回相同响应。

## 缓存控制

### 缓存头

```http
Cache-Control: public, max-age=3600
Cache-Control: private, no-cache
Cache-Control: no-store
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Last-Modified: Wed, 15 Jan 2024 10:30:00 GMT
```

### 条件请求

```http
GET /users/123
If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"

响应：304 Not Modified
```

```http
PUT /users/123
If-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Content-Type: application/json

{
  "name": "Updated Name"
}

响应：412 Precondition Failed（如果 ETag 不匹配）
```

## URI 模式

### 一致的 URI 结构

```
/{version}/{resource}
/{version}/{resource}/{id}
/{version}/{resource}/{id}/{sub-resource}
/{version}/{resource}/{id}/{sub-resource}/{sub-id}
```

### 查询参数

**过滤：**
```
GET /users?status=active&role=admin
GET /products?category=electronics&price_min=100&price_max=500
```

**排序：**
```
GET /users?sort=created_at
GET /users?sort=-created_at          # 降序
GET /users?sort=name,created_at      # 多个字段
```

**字段选择：**
```
GET /users?fields=id,name,email
GET /users?exclude=password,social_security_number
```

**搜索：**
```
GET /users?q=john
GET /products?search=laptop
```

## 最佳实践

1. **使用名词，不使用动词** - 资源是名词，方法是动词
2. **集合使用复数** - 使用 `/users` 而不是 `/user`
3. **一致的命名** - 选择 snake_case 或 camelCase 并保持一致
4. **正确的状态码** - 使用适当的 HTTP 状态码
5. **包含元数据** - 响应中的分页、过滤、排序信息
6. **对 API 进行版本控制** - 从第一天开始规划演进
7. **记录所有内容** - OpenAPI 规范、示例、错误代码
8. **默认安全** - HTTPS、身份验证、速率限制
9. **支持过滤** - 使客户端能够准确获取所需内容
10. **实现 HATEOAS** - 使 API 自记录和可发现
