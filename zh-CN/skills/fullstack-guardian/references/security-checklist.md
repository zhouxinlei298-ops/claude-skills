# 安全清单

## 每个功能的安全清单

| 类别 | 检查 | 行动 |
|------|------|------|
| **身份验证** | 端点需要身份验证？ | 添加身份验证中间件/守卫 |
| **授权** | 用户有执行此操作的权限？ | 检查所有权/角色 |
| **输入** | 所有输入已验证和清理？ | 使用模式，清理 |
| **输出** | 响应中排除敏感数据？ | 过滤响应字段 |
| **速率限制** | 端点速率受限？ | 添加速率限制器 |
| **日志** | 安全事件已记录？ | 记录身份验证失败、变更 |

## 身份验证模式

```typescript
// NestJS Guard
@UseGuards(JwtAuthGuard)
@Get('profile')
async getProfile(@CurrentUser() user: User) {
  return this.userService.findById(user.id);
}

// Express Middleware
app.get('/profile', authenticate, (req, res) => {
  res.json(req.user);
});
```

```python
# FastAPI Dependency
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
```

## 授权模式

```typescript
// Resource ownership check
async updatePost(postId: string, userId: string, data: UpdatePostDto) {
  const post = await this.postRepo.findById(postId);

  if (post.authorId !== userId) {
    throw new ForbiddenException('Not authorized to edit this post');
  }

  return this.postRepo.update(postId, data);
}

// Role-based check
@Roles('admin')
@UseGuards(RolesGuard)
@Delete(':id')
async deleteUser(@Param('id') id: string) {
  return this.userService.delete(id);
}
```

## 输入验证

```typescript
// Zod schema
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(12),
});

// Use in endpoint
const validated = CreateUserSchema.parse(req.body);
```

```python
# Pydantic model
class CreateUser(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12)
```

## 速率限制

```typescript
// Express rate-limit
import rateLimit from 'express-rate-limit';

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: 'Too many login attempts',
});

app.post('/login', authLimiter, loginHandler);
```

## 快速参考

| 风险 | 缓解措施 |
|------|----------|
| SQL 注入 | 参数化查询 |
| XSS | 输出编码，CSP |
| CSRF | CSRF 令牌，SameSite cookies |
| IDOR | 授权检查 |
| 暴力破解 | 速率限制 |
| 数据泄露 | 响应过滤 |