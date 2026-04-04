# 集成测试

## API 测试（Supertest）

```typescript
import request from 'supertest';
import { app } from '../app';

describe('POST /api/users', () => {
  it('creates user with valid data', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'test@test.com', name: 'Test' })
      .expect(201);

    expect(response.body).toMatchObject({
      email: 'test@test.com',
      name: 'Test',
    });
    expect(response.body.id).toBeDefined();
  });

  it('returns 400 for invalid email', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'invalid', name: 'Test' })
      .expect(400);

    expect(response.body.error).toContain('email');
  });

  it('returns 401 without auth token', async () => {
    await request(app)
      .get('/api/users/me')
      .expect(401);
  });
});
```

## 认证请求

```typescript
describe('Protected endpoints', () => {
  let authToken: string;

  beforeAll(async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@test.com', password: 'password' });
    authToken = response.body.token;
  });

  it('accesses protected route', async () => {
    await request(app)
      .get('/api/users/me')
      .set('Authorization', `Bearer ${authToken}`)
      .expect(200);
  });
});
```

## 数据库测试

```typescript
import { db } from '../database';

describe('UserRepository', () => {
  beforeEach(async () => {
    await db.query('DELETE FROM users');
  });

  afterAll(async () => {
    await db.end();
  });

  it('creates and retrieves user', async () => {
    const user = await userRepo.create({
      email: 'test@test.com',
      name: 'Test',
    });

    const found = await userRepo.findById(user.id);
    expect(found).toEqual(user);
  });
});
```

## pytest API 测试

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/api/users/", json={
        "email": "test@example.com",
        "name": "Test"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_invalid_email(client: AsyncClient):
    response = await client.post("/api/users/", json={
        "email": "invalid",
        "name": "Test"
    })
    assert response.status_code == 422
```

## 快速参考

| 方法 | 用途 |
|------|------|
| `.send(body)` | 发送请求体 |
| `.set(header, value)` | 设置请求头 |
| `.expect(status)` | 断言状态码 |
| `.expect('Content-Type', /json/)` | 断言请求头 |
| `response.body` | 解析后的 JSON 请求体 |
