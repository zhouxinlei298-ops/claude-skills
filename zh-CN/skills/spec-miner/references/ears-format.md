# EARS 格式

## EARS 语法

Easy Approach to Requirements Syntax（简单需求方法语法），用于清晰、明确的需求描述。

### 基本模式

**无处不在（始终）**
```
The system shall [action].
```

**事件驱动**
```
When [trigger], the system shall [action].
```

**状态驱动**
```
While [state], the system shall [action].
```

**条件性**
```
While [state], when [trigger], the system shall [action].
```

**可选性**
```
Where [feature enabled], the system shall [action].
```

## 示例观察

### 认证

**OBS-AUTH-001: 登录流程**
```
While credentials are valid, when POST /auth/login is called,
the system shall return JWT access token (15m) and refresh token (7d).
```

**OBS-AUTH-002: 令牌刷新**
```
While refresh token is valid, when POST /auth/refresh is called,
the system shall issue new access token.
```

**OBS-AUTH-003: 无效令牌**
```
When expired or invalid token is provided,
the system shall return 401 Unauthorized.
```

### 用户管理

**OBS-USER-001: 用户创建**
```
While email is unique, when POST /users is called with valid data,
the system shall create user with bcrypt-hashed password (rounds=12).
```

**OBS-USER-002: 邮箱验证**
```
When email format is invalid,
the system shall return 400 with error message "Invalid email format".
```

### 输入验证

**OBS-INPUT-001: 必填字段**
```
When required fields are missing,
the system shall return 400 with field-specific error messages.
```

## 快速参考

| 类型 | 模式 | 示例触发条件 |
|------|------|------------|
| 无处不在 | shall [action] | 始终为真 |
| 事件 | When [X], shall | 点击按钮时 |
| 状态 | While [X], shall | 登录状态下 |
| 条件 | While [X], when [Y], shall | 管理员状态下，删除时 |
| 可选 | Where [X], shall | 如果功能启用 |