# 安全测试

## 认证测试

```typescript
describe('Authentication Security', () => {
  it('rejects invalid credentials', async () => {
    await request(app)
      .post('/api/login')
      .send({ email: 'user@test.com', password: 'wrong' })
      .expect(401);
  });

  it('rejects expired tokens', async () => {
    const expiredToken = createExpiredToken();
    await request(app)
      .get('/api/protected')
      .set('Authorization', `Bearer ${expiredToken}`)
      .expect(401);
  });

  it('rejects tampered tokens', async () => {
    const tamperedToken = validToken.slice(0, -5) + 'xxxxx';
    await request(app)
      .get('/api/protected')
      .set('Authorization', `Bearer ${tamperedToken}`)
      .expect(401);
  });

  it('enforces rate limiting on login', async () => {
    for (let i = 0; i < 6; i++) {
      await request(app)
        .post('/api/login')
        .send({ email: 'user@test.com', password: 'wrong' });
    }

    await request(app)
      .post('/api/login')
      .send({ email: 'user@test.com', password: 'correct' })
      .expect(429);
  });
});
```

## 授权测试

```typescript
describe('Authorization', () => {
  it('denies access to other users resources', async () => {
    await request(app)
      .get('/api/users/other-user-id/data')
      .set('Authorization', `Bearer ${userAToken}`)
      .expect(403);
  });

  it('denies admin routes to regular users', async () => {
    await request(app)
      .delete('/api/admin/users/123')
      .set('Authorization', `Bearer ${regularUserToken}`)
      .expect(403);
  });
});
```

## 输入验证测试

```typescript
describe('Input Validation', () => {
  it('rejects SQL injection attempts', async () => {
    await request(app)
      .get('/api/users')
      .query({ search: "'; DROP TABLE users; --" })
      .expect(400);
  });

  it('rejects XSS in input fields', async () => {
    const response = await request(app)
      .post('/api/posts')
      .send({ title: '<script>alert("xss")</script>' })
      .expect(201);

    expect(response.body.title).not.toContain('<script>');
  });

  it('validates file upload types', async () => {
    await request(app)
      .post('/api/upload')
      .attach('file', 'malicious.exe')
      .expect(400);
  });
});
```

## 安全头测试

```typescript
describe('Security Headers', () => {
  it('sets security headers', async () => {
    const response = await request(app).get('/');

    expect(response.headers['x-content-type-options']).toBe('nosniff');
    expect(response.headers['x-frame-options']).toBe('DENY');
    expect(response.headers['strict-transport-security']).toBeDefined();
  });
});
```

## 安全测试检查清单

| 类别 | 测试项 |
|------|--------|
| **认证** | 无效凭据、令牌过期、篡改 |
| **输入** | SQL 注入、XSS、命令注入 |
| **访问** | IDOR、权限提升 |
| **速率限制** | 暴力破解、API 滥用 |
| **安全头** | CSP、HSTS、X-Frame-Options |
| **数据** | PII 泄露、错误消息 |

## 快速参考

| 漏洞 | 测试方法 |
|------|----------|
| SQL 注入 | 在输入中使用 `'; DROP TABLE--` |
| XSS | `<script>alert(1)</script>` |
| IDOR | 访问其他用户的资源 |
| CSRF | 缺失/无效的令牌 |
| 认证绕过 | 缺失认证、过期令牌 |
