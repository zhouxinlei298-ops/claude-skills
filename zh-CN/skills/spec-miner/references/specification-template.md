# 规范模板

## 完整模板

```markdown
# Reverse-Engineered Specification: [System/Feature Name]

## Overview
[High-level description based on analysis]

## Architecture Summary

### Technology Stack
- **Language**: TypeScript 5.x
- **Framework**: NestJS 10.x
- **Database**: PostgreSQL 15
- **ORM**: Prisma 5.x

### Module Structure
```
src/
├── auth/         # 认证（JWT、守卫）
├── users/        # 用户 CRUD 操作
├── orders/       # 订单处理
└── common/       # 共享工具
```

### Data Flow
```
请求 → 守卫 → 控制器 → 服务 → 仓库 → 数据库
                             ↓
                      外部 API
```

## Observed Functional Requirements

### [Module Name]

**OBS-XXX-001**: [Feature Name]
[EARS format requirement]

**OBS-XXX-002**: [Feature Name]
[EARS format requirement]

## Observed Non-Functional Requirements

### Security
- JWT tokens signed with RS256
- Passwords hashed with bcrypt (12 rounds)
- Rate limiting: 100 req/min per IP

### Performance
- Database connection pool: 10 connections
- Response timeout: 30 seconds
- Pagination: default 20, max 100

### Error Handling
| Code | Condition | Response |
|------|-----------|----------|
| 400 | Validation failure | `{ error: string, details: object }` |
| 401 | Invalid/missing token | `{ error: "Unauthorized" }` |
| 404 | Resource not found | `{ error: "Not found" }` |
| 500 | Unhandled error | `{ error: "Internal server error" }` |

## Inferred Acceptance Criteria

### AC-001: [Feature]
Given [precondition]
When [action]
Then [expected result]

## Uncertainties and Questions

- [ ] What triggers order status transitions?
- [ ] Is soft delete implemented for users?
- [ ] What external APIs are called?
- [ ] Are there background jobs?

## Recommendations

1. Add OpenAPI documentation to controllers
2. Missing input validation on PATCH endpoints
3. Consider adding request tracing
```

## 输出位置

将规范保存为：`specs/{project_name}_reverse_spec.md`

## 必需章节

| 章节 | 用途 |
|------|------|
| 概述 | 高级摘要 |
| 架构 | 技术栈、结构、数据流 |
| 功能性需求 | EARS 格式观察 |
| 非功能性需求 | 安全性、性能、错误 |
| 验收标准 | Given/When/Then 格式 |
| 不确定性 | 需要澄清的问题 |
| 建议 | 识别的改进 |