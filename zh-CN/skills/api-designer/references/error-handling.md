# API 错误处理

## 错误响应设计

一致、信息丰富的错误响应对于 API 可用性至关重要。

## 标准错误格式

### 基本错误响应

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "找不到 ID 为 123 的用户",
    "details": null
  }
}
```

### RFC 7807 问题详情

标准化错误格式（application/problem+json）：

```http
HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{
  "type": "https://api.example.com/errors/resource-not-found",
  "title": "资源未找到",
  "status": 404,
  "detail": "ID 为 123 的用户不存在",
  "instance": "/users/123"
}
```

**字段：**
- `type` - 标识错误类型的 URI 引用
- `title` - 简短、人类可读的摘要
- `status` - HTTP 状态码
- `detail` - 对此特定事件的人类可读解释
- `instance` - 此特定事件的 URI 引用

### 扩展错误响应

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求验证失败",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "电子邮件必须是有效的电子邮件地址"
      },
      {
        "field": "age",
        "code": "OUT_OF_RANGE",
        "message": "年龄必须在 18 到 120 之间"
      }
    ],
    "request_id": "req_123456",
    "timestamp": "2024-01-15T10:30:00Z",
    "documentation_url": "https://api.example.com/docs/errors#validation-error"
  }
}
```

## 错误类别

### 1. 验证错误（400 Bad Request）

客户端发送了无效数据。

```http
POST /users
Content-Type: application/json

{
  "name": "",
  "email": "invalid-email",
  "age": 15
}

响应：400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求验证失败",
    "details": [
      {
        "field": "name",
        "code": "REQUIRED",
        "message": "名称是必需的"
      },
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "电子邮件必须是有效的电子邮件地址"
      },
      {
        "field": "age",
        "code": "OUT_OF_RANGE",
        "message": "年龄必须至少为 18",
        "constraints": {
          "min": 18,
          "max": 120
        }
      }
    ]
  }
}
```

### 2. 身份验证错误（401 Unauthorized）

缺少或无效的身份验证凭据。

```http
GET /users/123
Authorization: Bearer invalid_token

响应：401 Unauthorized
WWW-Authenticate: Bearer realm="api", error="invalid_token"

{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "访问令牌无效或已过期",
    "details": {
      "reason": "token_expired",
      "expired_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

**常见身份验证错误代码：**
- `MISSING_TOKEN` - 未提供身份验证令牌
- `INVALID_TOKEN` - 令牌格式错误或无效
- `EXPIRED_TOKEN` - 令牌已过期
- `REVOKED_TOKEN` - 令牌已被撤销

### 3. 授权错误（403 Forbidden）

已身份验证但无权执行操作。

```http
DELETE /users/123
Authorization: Bearer valid_token

响应：403 Forbidden
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "message": "您没有权限删除此用户",
    "details": {
      "required_permission": "users:delete",
      "your_permissions": ["users:read", "users:update"]
    }
  }
}
```

### 4. 未找到错误（404 Not Found）

资源不存在。

```http
GET /users/99999

响应：404 Not Found
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "找不到 ID 为 99999 的用户",
    "details": {
      "resource_type": "User",
      "resource_id": "99999"
    }
  }
}
```

### 5. 冲突错误（409 Conflict）

请求与当前状态冲突。

```http
POST /users
Content-Type: application/json

{
  "email": "existing@example.com",
  "name": "John Doe"
}

响应：409 Conflict
{
  "error": {
    "code": "RESOURCE_ALREADY_EXISTS",
    "message": "电子邮件为 'existing@example.com' 的用户已存在",
    "details": {
      "field": "email",
      "value": "existing@example.com",
      "existing_resource": "/users/123"
    }
  }
}
```

### 6. 速率限制（429 Too Many Requests）

客户端超出速率限制。

```http
GET /users

响应：429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705320000

{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "您已超出速率限制",
    "details": {
      "limit": 100,
      "window": "1 小时",
      "retry_after": 60,
      "reset_at": "2024-01-15T11:00:00Z"
    }
  }
}
```

### 7. 服务器错误（500 Internal Server Error）

意外的服务器错误。

```http
GET /users/123

响应：500 Internal Server Error
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "发生了意外错误。请稍后重试。",
    "request_id": "req_123456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**绝不要暴露：**
- 堆栈跟踪
- 数据库错误
- 内部路径
- 敏感配置

### 8. 服务不可用（503 Service Unavailable）

服务暂时不可用。

```http
GET /users

响应：503 Service Unavailable
Retry-After: 300

{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "由于维护，服务暂时不可用",
    "details": {
      "retry_after": 300,
      "maintenance_end": "2024-01-15T12:00:00Z"
    }
  }
}
```

## 错误代码目录

为 API 定义标准错误代码：

```json
{
  "VALIDATION_ERROR": {
    "status": 400,
    "description": "请求验证失败",
    "subcodes": {
      "REQUIRED": "缺少必需字段",
      "INVALID_FORMAT": "字段格式无效",
      "OUT_OF_RANGE": "值超出允许范围",
      "INVALID_ENUM": "值不在允许的集合中"
    }
  },
  "AUTHENTICATION_ERROR": {
    "status": 401,
    "description": "身份验证失败",
    "subcodes": {
      "MISSING_TOKEN": "未提供身份验证令牌",
      "INVALID_TOKEN": "令牌无效",
      "EXPIRED_TOKEN": "令牌已过期"
    }
  },
  "AUTHORIZATION_ERROR": {
    "status": 403,
    "description": "权限不足",
    "subcodes": {
      "INSUFFICIENT_PERMISSIONS": "缺少所需权限",
      "RESOURCE_FORBIDDEN": "禁止访问资源"
    }
  },
  "RESOURCE_NOT_FOUND": {
    "status": 404,
    "description": "资源未找到"
  },
  "CONFLICT_ERROR": {
    "status": 409,
    "description": "请求与当前状态冲突",
    "subcodes": {
      "RESOURCE_ALREADY_EXISTS": "资源已存在",
      "CONCURRENT_MODIFICATION": "资源已被另一个请求修改"
    }
  },
  "RATE_LIMIT_EXCEEDED": {
    "status": 429,
    "description": "超出速率限制"
  },
  "INTERNAL_SERVER_ERROR": {
    "status": 500,
    "description": "内部服务器错误"
  }
}
```

## 验证错误详情

### 字段级验证

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求验证失败",
    "details": [
      {
        "field": "credit_card.number",
        "code": "INVALID_FORMAT",
        "message": "信用卡号必须是 16 位",
        "value_provided": "1234",
        "constraints": {
          "pattern": "^[0-9]{16}$"
        }
      },
      {
        "field": "items[0].quantity",
        "code": "OUT_OF_RANGE",
        "message": "数量必须至少为 1",
        "value_provided": 0,
        "constraints": {
          "min": 1,
          "max": 1000
        }
      }
    ]
  }
}
```

### 跨字段验证

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求验证失败",
    "details": [
      {
        "fields": ["start_date", "end_date"],
        "code": "INVALID_RANGE",
        "message": "结束日期必须在开始日期之后",
        "values_provided": {
          "start_date": "2024-01-20",
          "end_date": "2024-01-15"
        }
      }
    ]
  }
}
```

## 请求 ID 跟踪

始终包含请求 ID 以进行调试：

```http
响应头：
X-Request-ID: req_abc123

响应体：
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "发生了意外错误",
    "request_id": "req_abc123"
  }
}
```

客户端可以在支持工单中引用请求 ID。

## 错误文档

为每个端点记录所有可能的错误：

```yaml
/users/{id}:
  get:
    responses:
      '200':
        description: 成功
      '401':
        description: 身份验证失败
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
            examples:
              missing_token:
                value:
                  error:
                    code: MISSING_TOKEN
                    message: 未提供身份验证令牌
              invalid_token:
                value:
                  error:
                    code: INVALID_TOKEN
                    message: 令牌无效或已过期
      '404':
        description: 用户未找到
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Error'
            examples:
              not_found:
                value:
                  error:
                    code: RESOURCE_NOT_FOUND
                    message: 找不到 ID 为 123 的用户
```

## 重试指导

帮助客户端了解是否应该重试：

```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "服务暂时不可用",
    "retry": {
      "retryable": true,
      "retry_after": 60,
      "max_retries": 3,
      "backoff": "exponential"
    }
  }
}
```

### 可重试错误

- 408 请求超时
- 429 Too Many Requests（带有 Retry-After）
- 500 Internal Server Error（有时）
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

### 不可重试错误

- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 409 Conflict
- 422 Unprocessable Entity

## 多语言支持

支持多种语言的错误消息：

```http
GET /users/invalid
Accept-Language: es

响应：404 Not Found
Content-Language: es
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "No se encontró el usuario con ID 'invalid'"
  }
}
```

始终包含 `code`，以便客户端可以实现自己的翻译。

## 最佳实践

1. **使用标准 HTTP 状态码** - 不要为错误返回 200
2. **包含机器可读的代码** - 用于客户端逻辑的错误代码
3. **提供人类可读的消息** - 清楚的解释
4. **具体但安全** - 不要暴露敏感信息
5. **包含请求 ID** - 用于跟踪和调试
6. **记录所有错误** - 每个端点的每个可能错误
7. **保持一致** - 所有端点相同格式
8. **帮助客户端重试** - 指示错误是否可重试
9. **早期验证** - 立即返回验证错误
10. **服务器端记录错误** - 跟踪错误以进行监控

## 反模式

避免这些错误：

- **通用错误消息** - 没有细节的"发生了错误"
- **暴露堆栈跟踪** - 安全风险
- **不一致的错误格式** - 每个端点不同结构
- **缺少错误代码** - 仅有人类可读的消息
- **错误的状态码** - 响应体中有错误的 200
- **无请求 ID** - 使调试变得不可能
- **未记录的错误** - 客户端不知道预期什么
- **太多信息** - 暴露内部实现细节
