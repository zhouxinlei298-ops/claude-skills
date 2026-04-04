# 错误处理模式

## 前端错误处理

```typescript
// React with async/await
async function handleSubmit(data: FormData) {
  setLoading(true);
  setError(null);

  try {
    const result = await api.updateProfile(data);
    showSuccess('Profile updated');
    return result;
  } catch (error) {
    if (error.status === 401) {
      redirect('/login');
    } else if (error.status === 403) {
      showError('Not authorized');
    } else if (error.status === 422) {
      setValidationErrors(error.errors);
    } else {
      showError('Something went wrong');
      reportError(error); // Send to error tracking
    }
  } finally {
    setLoading(false);
  }
}
```

```typescript
// Custom hook for API calls
function useApi<T>(fn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (e) {
      setError(e as Error);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [fn]);

  return { data, error, loading, execute };
}
```

## 后端错误处理

```python
# FastAPI
from fastapi import HTTPException

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        return await user_service.update(user_id, data)
    except UserNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except EmailTaken:
        raise HTTPException(status_code=422, detail="Email already in use")
```

```typescript
// NestJS
@Put(':id')
async updateUser(
  @Param('id') id: string,
  @Body() dto: UpdateUserDto,
  @CurrentUser() user: User,
) {
  if (user.id !== id && !user.isAdmin) {
    throw new ForbiddenException('Not authorized');
  }

  try {
    return await this.userService.update(id, dto);
  } catch (error) {
    if (error instanceof UserNotFoundError) {
      throw new NotFoundException('User not found');
    }
    if (error instanceof EmailTakenError) {
      throw new UnprocessableEntityException('Email already in use');
    }
    throw error;
  }
}
```

## 错误响应格式

```typescript
// Consistent error shape
interface ApiError {
  error: string;
  message: string;
  details?: Record<string, string[]>;
  requestId?: string;
}

// Example responses
{ "error": "VALIDATION_ERROR", "message": "Invalid input", "details": { "email": ["Invalid format"] } }
{ "error": "NOT_FOUND", "message": "User not found" }
{ "error": "FORBIDDEN", "message": "Not authorized to perform this action" }
```

## 快速参考

| HTTP 代码 | 何时使用 | 示例 |
|-----------|----------|------|
| 400 | 请求格式错误 | 格式错误的 JSON |
| 401 | 未身份验证 | 缺少/无效的令牌 |
| 403 | 未授权 | 错误的权限 |
| 404 | 资源不存在 | 用户不存在 |
| 409 | 冲突 | 重复的邮箱 |
| 422 | 验证失败 | 无效的邮箱格式 |
| 429 | 请求频率受限 | 请求过多 |
| 500 | 服务器错误 | 未处理的异常 |