# OpenAPI 3.1 规范

## 什么是 OpenAPI？

OpenAPI（原为 Swagger）是描述 REST API 的标准。它实现：
- 交互式文档
- 代码生成（SDK、客户端、服务器）
- API 测试工具
- 契约验证
- Mock 服务器

## 基本结构

### 最小 OpenAPI 3.1 规范

```yaml
openapi: 3.1.0
info:
  title: My API
  version: 1.0.0
  description: 示例 API
  contact:
    name: API Support
    email: support@example.com
    url: https://example.com/support
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0.html

servers:
  - url: https://api.example.com/v1
    description: Production 服务器
  - url: https://staging-api.example.com/v1
    description: Staging 服务器
  - url: http://localhost:3000/v1
    description: 本地开发

paths:
  /users:
    get:
      summary: 列出用户
      description: 检索用户的分页列表
      operationId: listUsers
      tags:
        - Users
      responses:
        '200':
          description: 成功响应
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'

components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
      properties:
        id:
          type: integer
          format: int64
          example: 123
        email:
          type: string
          format: email
          example: john@example.com
        name:
          type: string
          example: John Doe
```

## Info 对象

关于 API 的元数据：

```yaml
info:
  title: Users API
  version: 1.0.0
  description: |
    # Users API

    此 API 管理用户账户和配置文件。

    ## 功能
    - 用户 CRUD 操作
    - JWT 身份验证
    - 基于角色的授权

  termsOfService: https://example.com/terms

  contact:
    name: API Support Team
    email: api-support@example.com
    url: https://example.com/support

  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

  x-api-id: users-api-v1
  x-audience: external
```

## Servers

定义 API 基本 URL：

```yaml
servers:
  - url: https://api.example.com/v1
    description: Production
    variables:
      version:
        default: v1
        enum:
          - v1
          - v2

  - url: https://{environment}.example.com/v1
    description: 动态环境
    variables:
      environment:
        default: api
        enum:
          - api
          - staging
          - dev
```

## 路径和操作

### 完整端点示例

```yaml
paths:
  /users:
    get:
      summary: 列出用户
      description: 检索带有可选过滤的用户分页列表
      operationId: listUsers
      tags:
        - Users

      parameters:
        - name: offset
          in: query
          description: 要跳过的项目数
          required: false
          schema:
            type: integer
            minimum: 0
            default: 0

        - name: limit
          in: query
          description: 要返回的最大项目数
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20

        - name: status
          in: query
          description: 按用户状态过滤
          required: false
          schema:
            type: string
            enum:
              - active
              - inactive
              - suspended

      security:
        - bearerAuth: []

      responses:
        '200':
          description: 成功响应
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
              examples:
                success:
                  $ref: '#/components/examples/UserListSuccess'

        '401':
          $ref: '#/components/responses/Unauthorized'

        '429':
          $ref: '#/components/responses/RateLimitExceeded'

    post:
      summary: 创建用户
      description: 创建新的用户账户
      operationId: createUser
      tags:
        - Users

      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
            examples:
              basic:
                $ref: '#/components/examples/CreateUserBasic'

      responses:
        '201':
          description: 用户创建成功
          headers:
            Location:
              description: 已创建用户的 URL
              schema:
                type: string
                format: uri
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

        '400':
          $ref: '#/components/responses/ValidationError'

        '409':
          description: 用户已存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'

  /users/{userId}:
    parameters:
      - name: userId
        in: path
        description: 用户 ID
        required: true
        schema:
          type: integer
          format: int64

    get:
      summary: 获取用户
      description: 按 ID 检索特定用户
      operationId: getUser
      tags:
        - Users

      responses:
        '200':
          description: 成功响应
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

        '404':
          $ref: '#/components/responses/NotFound'

    put:
      summary: 更新用户
      description: 替换用户数据
      operationId: updateUser
      tags:
        - Users

      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateUserRequest'

      responses:
        '200':
          description: 用户更新成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'

        '404':
          $ref: '#/components/responses/NotFound'

    delete:
      summary: 删除用户
      description: 删除用户账户
      operationId: deleteUser
      tags:
        - Users

      responses:
        '204':
          description: 用户删除成功

        '404':
          $ref: '#/components/responses/NotFound'
```

## 组件

API 规范的可重用组件。

### Schemas

```yaml
components:
  schemas:
    User:
      type: object
      required:
        - id
        - email
        - name
      properties:
        id:
          type: integer
          format: int64
          readOnly: true
          example: 123
        email:
          type: string
          format: email
          example: john@example.com
        name:
          type: string
          minLength: 1
          maxLength: 100
          example: John Doe
        status:
          type: string
          enum:
            - active
            - inactive
            - suspended
          default: active
        created_at:
          type: string
          format: date-time
          readOnly: true
          example: "2024-01-15T10:30:00Z"
        metadata:
          type: object
          additionalProperties:
            type: string

    CreateUserRequest:
      type: object
      required:
        - email
        - name
      properties:
        email:
          type: string
          format: email
        name:
          type: string
          minLength: 1
          maxLength: 100
        metadata:
          type: object
          additionalProperties:
            type: string

    UserListResponse:
      type: object
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/User'
        pagination:
          $ref: '#/components/schemas/Pagination'

    Pagination:
      type: object
      properties:
        offset:
          type: integer
          minimum: 0
        limit:
          type: integer
          minimum: 1
        total:
          type: integer
          minimum: 0
        has_more:
          type: boolean

    Error:
      type: object
      required:
        - error
      properties:
        error:
          type: object
          required:
            - code
            - message
          properties:
            code:
              type: string
              example: RESOURCE_NOT_FOUND
            message:
              type: string
              example: 找不到 ID 为 123 的用户
            details:
              type: object
            request_id:
              type: string
              example: req_abc123
```

### 安全方案

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT 访问令牌

    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
      description: 用于身份验证的 API 密钥

    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth/authorize
          tokenUrl: https://auth.example.com/oauth/token
          scopes:
            users:read: 读取用户数据
            users:write: 创建和更新用户
            users:delete: 删除用户
```

全局或按操作应用安全性：

```yaml
# 全局安全性
security:
  - bearerAuth: []

# 或按操作
paths:
  /users:
    get:
      security:
        - bearerAuth: []
        - apiKey: []  # 替代身份验证方法
```

### 响应

可重用的响应定义：

```yaml
components:
  responses:
    NotFound:
      description: 资源未找到
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: RESOURCE_NOT_FOUND
              message: 请求的资源未找到

    Unauthorized:
      description: 需要身份验证
      headers:
        WWW-Authenticate:
          schema:
            type: string
          description: 身份验证方法
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'

    ValidationError:
      description: 验证失败
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error:
              code: VALIDATION_ERROR
              message: 请求验证失败
              details:
                - field: email
                  code: INVALID_FORMAT
                  message: 电子邮件必须是有效的电子邮件地址

    RateLimitExceeded:
      description: 超过速率限制
      headers:
        X-RateLimit-Limit:
          schema:
            type: integer
          description: 每小时请求限制
        X-RateLimit-Remaining:
          schema:
            type: integer
          description: 剩余请求数
        X-RateLimit-Reset:
          schema:
            type: integer
            format: int64
          description: 限制重置时间（Unix 时间戳）
        Retry-After:
          schema:
            type: integer
          description: 重试前等待的秒数
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

### 示例

```yaml
components:
  examples:
    UserListSuccess:
      summary: 成功的用户列表响应
      value:
        data:
          - id: 1
            email: john@example.com
            name: John Doe
            status: active
            created_at: "2024-01-15T10:30:00Z"
          - id: 2
            email: jane@example.com
            name: Jane Smith
            status: active
            created_at: "2024-01-16T14:20:00Z"
        pagination:
          offset: 0
          limit: 20
          total: 150
          has_more: true

    CreateUserBasic:
      summary: 使用最小字段创建用户
      value:
        email: newuser@example.com
        name: New User
```

## 数据类型

### 基本类型

```yaml
# 字符串
type: string
example: "Hello World"

# 带格式的字符串
type: string
format: email
example: "user@example.com"

# 整数
type: integer
format: int64
example: 123

# 数字（浮点数）
type: number
format: double
example: 99.99

# 布尔值
type: boolean
example: true

# 日期时间
type: string
format: date-time
example: "2024-01-15T10:30:00Z"

# 日期
type: string
format: date
example: "2024-01-15"

# UUID
type: string
format: uuid
example: "550e8400-e29b-41d4-a716-446655440000"

# URI
type: string
format: uri
example: "https://example.com/users/123"
```

### 数组

```yaml
type: array
items:
  type: string
minItems: 1
maxItems: 10
uniqueItems: true
example: ["tag1", "tag2", "tag3"]

# 对象数组
type: array
items:
  $ref: '#/components/schemas/User'
```

### 对象

```yaml
type: object
required:
  - name
  - email
properties:
  name:
    type: string
  email:
    type: string
    format: email
  age:
    type: integer
    minimum: 0
    maximum: 120

# 附加属性
additionalProperties: false  # 严格 - 无额外属性
additionalProperties: true   # 允许任何额外属性
additionalProperties:        # 额外属性必须是字符串
  type: string
```

### 枚举

```yaml
type: string
enum:
  - active
  - inactive
  - suspended
default: active
```

### OneOf / AnyOf / AllOf

```yaml
# OneOf - 正好一个模式匹配
oneOf:
  - $ref: '#/components/schemas/CreditCard'
  - $ref: '#/components/schemas/BankAccount'

# AnyOf - 一个或多个模式匹配
anyOf:
  - $ref: '#/components/schemas/User'
  - $ref: '#/components/schemas/Organization'

# AllOf - 所有模式必须匹配（继承）
allOf:
  - $ref: '#/components/schemas/BaseUser'
  - type: object
    properties:
      admin_level:
        type: integer
```

## 验证

### 字符串验证

```yaml
type: string
minLength: 1
maxLength: 100
pattern: "^[a-zA-Z0-9_-]+$"
format: email
```

### 数字验证

```yaml
type: integer
minimum: 0
maximum: 100
exclusiveMinimum: true  # > 0 而不是 >= 0
multipleOf: 5
```

### 数组验证

```yaml
type: array
minItems: 1
maxItems: 10
uniqueItems: true
```

## 标签

将端点组织到逻辑组中：

```yaml
tags:
  - name: Users
    description: 用户管理操作
  - name: Orders
    description: 订单管理
  - name: Products
    description: 产品目录

paths:
  /users:
    get:
      tags:
        - Users
```

## 文档

### Markdown 支持

```yaml
description: |
  # 用户管理

  此端点允许您管理用户。

  ## 功能
  - 创建用户
  - 更新配置文件
  - 删除账户

  ## 身份验证
  需要 JWT 承载令牌。

  ## 示例
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com"
  }
  ```
```

## 代码生成

从 OpenAPI 规范生成 SDK：

```bash
# 生成 TypeScript 客户端
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./client

# 生成 Python 客户端
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./python-client

# 生成服务器存根
openapi-generator-cli generate \
  -i openapi.yaml \
  -g nodejs-express-server \
  -o ./server
```

## 验证工具

验证 OpenAPI 规范：

```bash
# 使用 Swagger CLI
swagger-cli validate openapi.yaml

# 使用 Spectral（高级 linting）
spectral lint openapi.yaml
```

## 最佳实践

1. **使用组件** - 重用 schemas、responses、parameters
2. **添加示例** - 为所有 schemas 包含现实的示例
3. **完整记录** - 每个端点、参数、响应
4. **对规范进行版本控制** - 跟踪规范更改
5. **定期验证** - 使用工具捕获错误
6. **使用 $ref** - 引用组件而不是重复
7. **包含错误响应** - 记录所有可能的错误
8. **添加 operationId** - 每个操作的唯一 ID（用于代码生成）
9. **标记端点** - 组织到逻辑组
10. **提供安全方案** - 清楚记录身份验证
