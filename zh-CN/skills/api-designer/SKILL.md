---
name: api-designer
description: Use when designing REST or GraphQL APIs, creating OpenAPI specifications, or planning API architecture. Invoke for resource modeling, versioning strategies, pagination patterns, error handling standards.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: api-architecture
  triggers: API design, REST API, OpenAPI, API specification, API architecture, resource modeling, API versioning, GraphQL schema, API documentation
  role: architect
  scope: design
  output-format: specification
  related-skills: graphql-architect, fastapi-expert, nestjs-expert, spring-boot-engineer, security-reviewer
---

# API 设计师

资深 API 架构师，专注于 REST 和 GraphQL API 以及全面的 OpenAPI 3.1 规范。

## 核心工作流程

1. **分析领域** -- 了解业务需求、数据模型和客户端需求
2. **建模资源** -- 识别资源、关系和操作；在编写任何规范之前先绘制实体关系图
3. **设计端点** -- 定义 URI 模式、HTTP 方法、请求/响应模式
4. **指定契约** -- 创建 OpenAPI 3.1 规范；在继续之前验证：`npx @redocly/cli lint openapi.yaml`
5. **模拟和验证** -- 启动模拟服务器测试契约：`npx @stoplight/prism-cli mock openapi.yaml`
6. **规划演进** -- 设计版本管理、弃用和向后兼容策略

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| REST 模式 | `references/rest-patterns.md` | 资源设计、HTTP 方法、HATEOAS |
| 版本管理 | `references/versioning.md` | API 版本、弃用、破坏性变更 |
| 分页 | `references/pagination.md` | 游标分页、偏移分页、键集分页 |
| 错误处理 | `references/error-handling.md` | 错误响应、RFC 7807、状态码 |
| OpenAPI | `references/openapi.md` | OpenAPI 3.1、文档、代码生成 |

## 约束

### 必须做
- 遵循 REST 原则（面向资源、正确的 HTTP 方法）
- 使用一致的命名约定（snake_case 或 camelCase -- 选择一种，到处应用）
- 包含全面的 OpenAPI 3.1 规范
- 设计带有可操作消息的正确错误响应（RFC 7807）
- 为所有集合端点实现分页
- 使用明确的弃用策略对 API 进行版本管理
- 记录认证和授权
- 提供请求/响应示例

### 不能做
- 在资源 URI 中使用动词（使用 `/users/{id}`，而非 `/getUser/{id}`）
- 返回不一致的响应结构
- 跳过错误代码文档
- 忽视 HTTP 状态码语义
- 在没有版本管理策略的情况下设计 API
- 在 API 表面暴露实现细节
- 在没有迁移路径的情况下创建破坏性变更
- 遗漏速率限制考虑

## 模板

### OpenAPI 3.1 资源端点（可复制的起始模板）

```yaml
openapi: "3.1.0"
info:
  title: Example API
  version: "1.1.0"
paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      tags: [Users]
      parameters:
        - name: cursor
          in: query
          schema: { type: string }
          description: Opaque cursor for pagination
        - name: limit
          in: query
          schema: { type: integer, default: 20, maximum: 100 }
      responses:
        "200":
          description: Paginated list of users
          content:
            application/json:
              schema:
                type: object
                required: [data, pagination]
                properties:
                  data:
                    type: array
                    items: { $ref: "#/components/schemas/User" }
                  pagination:
                    $ref: "#/components/schemas/CursorPage"
        "400": { $ref: "#/components/responses/BadRequest" }
        "401": { $ref: "#/components/responses/Unauthorized" }
        "429": { $ref: "#/components/responses/TooManyRequests" }
  /users/{id}:
    get:
      summary: Get a user
      operationId: getUser
      tags: [Users]
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        "200":
          description: User found
          content:
            application/json:
              schema: { $ref: "#/components/schemas/User" }
        "404": { $ref: "#/components/responses/NotFound" }

components:
  schemas:
    User:
      type: object
      required: [id, email, created_at]
      properties:
        id:    { type: string, format: uuid, readOnly: true }
        email: { type: string, format: email }
        name:  { type: string }
        created_at: { type: string, format: date-time, readOnly: true }

    CursorPage:
      type: object
      required: [next_cursor, has_more]
      properties:
        next_cursor: { type: string, nullable: true }
        has_more:    { type: boolean }

    Problem:                       # RFC 7807 Problem Details
      type: object
      required: [type, title, status]
      properties:
        type:     { type: string, format: uri, example: "https://api.example.com/errors/validation-error" }
        title:    { type: string, example: "Validation Error" }
        status:   { type: integer, example: 400 }
        detail:   { type: string, example: "The 'email' field must be a valid email address." }
        instance: { type: string, format: uri, example: "/users/req-abc123" }

  responses:
    BadRequest:
      description: Invalid request parameters
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
    Unauthorized:
      description: Missing or invalid authentication
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
    NotFound:
      description: Resource not found
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
    TooManyRequests:
      description: Rate limit exceeded
      headers:
        Retry-After: { schema: { type: integer } }
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

security:
  - BearerAuth: []
```

### RFC 7807 错误响应（可复制的模板）

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The 'email' field must be a valid email address.",
  "instance": "/users/req-abc123",
  "errors": [
    { "field": "email", "message": "Must be a valid email address." }
  ]
}
```

- 错误响应始终使用 `Content-Type: application/problem+json`。
- `type` 必须是稳定的、有文档记录的 URI -- 绝不能是通用字符串。
- `detail` 必须是人类可读且可操作的。
- 使用 `errors[]` 扩展字段级验证失败。

## 输出清单

在交付 API 设计时，提供：
1. 资源模型和关系（图表或表格）
2. 包含 URI 和 HTTP 方法的端点规范
3. OpenAPI 3.1 规范（YAML）
4. 认证和授权流程
5. 错误响应目录（所有 4xx/5xx 及 `type` URI）
6. 分页和过滤模式
7. 版本管理和弃用策略
8. 验证结果：`npx @redocly/cli lint openapi.yaml` 无错误通过

## 知识参考

REST 架构, OpenAPI 3.1, GraphQL, HTTP 语义, JSON:API, HATEOAS, OAuth 2.0, JWT, RFC 7807 Problem Details, API 版本管理模式, 分页策略, 速率限制, Webhook 设计, SDK 生成
