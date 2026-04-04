# 三层设计

## 设计模板

对于每个功能，都要处理所有三个层次：

```markdown
## Feature: [Feature Name]

### [Frontend]
- UI components needed
- Client-side validation
- Loading/error states
- Optimistic UI updates
- Accessibility considerations

### [Backend]
- API endpoints (method, path)
- Request/response schemas
- Database operations
- Business logic
- External service calls

### [Security]
- Authentication requirements
- Authorization rules
- Input sanitization
- Rate limiting
- Audit logging
```

## 示例：用户资料更新

```markdown
## Feature: User Profile Update

### [Frontend]
- Form with name, email, bio, avatar fields
- Client-side validation with real-time feedback
- Loading states during submission
- Error/success message display
- Optimistic UI updates

### [Backend]
- PUT /api/users/:id endpoint
- Pydantic/Zod schema validation
- Database transaction with rollback on error
- Audit logging for profile changes
- Email verification if email changes

### [Security]
- Authorization: users can only update own profile
- Input sanitization against XSS
- Rate limiting (10 req/min per user)
- File upload validation for avatar (type, size)
- CSRF protection on form submission
```

## 技术设计文档

创建 `specs/{feature_name}_design.md`，内容如下：

```markdown
# Feature: {Name}

## Requirements (EARS Format)
While <precondition>, when <trigger>, the system shall <response>.

Example: While a user is logged in, when they click Save, the system shall
persist the form data and display a success message.

## Architecture
- Frontend: [Components, state management]
- Backend: [Endpoints, data models]
- Security: [Auth, validation, protection]

## Implementation Plan
- [ ] Step 1: Create Pydantic/Zod schemas
- [ ] Step 2: Implement API endpoint
- [ ] Step 3: Build UI component
- [ ] Step 4: Add error handling
- [ ] Step 5: Write tests
```

## 快速参考

| 层次 | 关键关注点 |
|------|------------|
| 前端 | UX、验证、状态、可访问性 |
| 后端 | API、数据、逻辑、性能 |
| 安全 | 身份验证、授权、清理、日志 |