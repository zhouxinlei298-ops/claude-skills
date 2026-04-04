# E2E 测试

## E2E 测试策略

```typescript
// Critical user paths to test
const criticalPaths = [
  'User registration and login',
  'Core product/service workflow',
  'Payment/checkout flow',
  'Settings and profile management',
];
```

## 用户流程测试

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Registration Flow', () => {
  test('complete registration', async ({ page }) => {
    await page.goto('/register');

    await page.getByLabel('Email').fill('new@example.com');
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm Password').fill('SecurePass123!');
    await page.getByRole('button', { name: 'Register' }).click();

    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByText('Welcome')).toBeVisible();
  });

  test('shows validation errors', async ({ page }) => {
    await page.goto('/register');

    await page.getByLabel('Email').fill('invalid');
    await page.getByRole('button', { name: 'Register' }).click();

    await expect(page.getByText('Invalid email')).toBeVisible();
  });
});
```

## 结账流程

```typescript
test.describe('Checkout Flow', () => {
  test('complete purchase', async ({ page }) => {
    // Add to cart
    await page.goto('/products/123');
    await page.getByRole('button', { name: 'Add to Cart' }).click();
    await expect(page.getByTestId('cart-count')).toHaveText('1');

    // Checkout
    await page.goto('/cart');
    await page.getByRole('button', { name: 'Checkout' }).click();

    // Payment
    await page.getByLabel('Card Number').fill('4242424242424242');
    await page.getByLabel('Expiry').fill('12/25');
    await page.getByLabel('CVC').fill('123');
    await page.getByRole('button', { name: 'Pay' }).click();

    // Confirmation
    await expect(page).toHaveURL(/order-confirmation/);
    await expect(page.getByText('Order Confirmed')).toBeVisible();
  });
});
```

## 测试数据管理

```typescript
// fixtures/testData.ts
export const testUsers = {
  standard: {
    email: 'standard@test.com',
    password: 'TestPass123!',
  },
  admin: {
    email: 'admin@test.com',
    password: 'AdminPass123!',
  },
};

// Test setup
test.beforeEach(async ({ page }) => {
  // Seed test data
  await page.request.post('/api/test/seed');
});

test.afterEach(async ({ page }) => {
  // Clean up
  await page.request.post('/api/test/cleanup');
});
```

## 跨浏览器测试

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
  ],
});
```

## 快速参考

| 模式 | 使用时机 |
|------|----------|
| 正常路径 | 关键用户旅程 |
| 错误处理 | 表单验证、API 错误 |
| 边界情况 | 空状态、最大限制 |
| 跨浏览器 | 重大发布前 |
| 移动端 | 响应式功能 |

| 优先级 | 测试覆盖 |
|--------|----------|
| **P0** | 注册、登录、核心功能 |
| **P1** | 支付、设置、常见流程 |
| **P2** | 边界情况、管理功能 |
| **P3** | 罕见场景 |
