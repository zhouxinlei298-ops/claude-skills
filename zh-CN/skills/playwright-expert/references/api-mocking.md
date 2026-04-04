# API Mock

## 基本路由 Mock

```typescript
test('displays mocked user data', async ({ page }) => {
  await page.route('**/api/users', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
      ]),
    })
  );

  await page.goto('/users');
  await expect(page.getByText('Alice')).toBeVisible();
  await expect(page.getByText('Bob')).toBeVisible();
});
```

## Mock 错误响应

```typescript
test('handles API error gracefully', async ({ page }) => {
  await page.route('**/api/users', route =>
    route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Server error' }),
    })
  );

  await page.goto('/users');
  await expect(page.getByText('Failed to load users')).toBeVisible();
});
```

## 条件 Mock

```typescript
test('mock specific requests', async ({ page }) => {
  await page.route('**/api/**', route => {
    const url = route.request().url();

    if (url.includes('/api/users')) {
      return route.fulfill({
        status: 200,
        json: [{ id: 1, name: 'Mocked User' }],
      });
    }

    // Let other requests through
    return route.continue();
  });
});
```

## 修改响应

```typescript
test('modify API response', async ({ page }) => {
  await page.route('**/api/products', async route => {
    // Get real response
    const response = await route.fetch();
    const json = await response.json();

    // Modify it
    json.products = json.products.map(p => ({
      ...p,
      price: p.price * 0.9, // 10% discount
    }));

    // Return modified response
    await route.fulfill({ json });
  });
});
```

## 等待响应

```typescript
test('waits for API response', async ({ page }) => {
  const responsePromise = page.waitForResponse('**/api/users');

  await page.getByRole('button', { name: 'Load Users' }).click();

  const response = await responsePromise;
  expect(response.status()).toBe(200);
});
```

## Mock 网络条件

```typescript
test('slow network', async ({ page }) => {
  await page.route('**/api/**', async route => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    await route.continue();
  });

  await page.goto('/dashboard');
  await expect(page.getByText('Loading...')).toBeVisible();
});
```

## HAR 文件 Mock

```typescript
// Record responses
await page.routeFromHAR('mocks/api.har', {
  url: '**/api/**',
  update: true, // Record new responses
});

// Playback recorded responses
await page.routeFromHAR('mocks/api.har', {
  url: '**/api/**',
  update: false,
});
```

## 快速参考

| 方法 | 目的 |
|------|------|
| `route.fulfill()` | 返回 Mock 响应 |
| `route.continue()` | 传递到真实服务器 |
| `route.fetch()` | 获取真实响应 |
| `route.abort()` | 阻止请求 |
| `waitForResponse()` | 等待 API 调用 |
| `routeFromHAR()` | 使用录制的响应 |

| 模式 | 使用场景 |
|------|----------|
| 全部 Mock | 隔离测试 |
| Mock 错误 | 错误处理 |
| 修改响应 | 测试边界情况 |
| 网络延迟 | 加载状态 |
