# 调试与不稳定测试

## 调试工具

```typescript
// Pause execution and open inspector
await page.pause();

// Enable step-by-step mode
PWDEBUG=1 npx playwright test

// Slow motion
test.use({ launchOptions: { slowMo: 500 } });

// Headed mode
npx playwright test --headed
```

## 追踪查看器

```bash
# View trace from failed test
npx playwright show-trace trace.zip

# Generate trace always
test.use({ trace: 'on' });

# View in UI mode
npx playwright test --ui
```

## 常见不稳定测试原因

### 1. 竞态条件

```typescript
// ❌ Bad: Element may not exist yet
await page.click('.submit-btn');

// ✅ Good: Auto-waiting built in
await page.getByRole('button', { name: 'Submit' }).click();
```

### 2. 动画/过渡

```typescript
// ❌ Bad: Click during animation
await page.click('.menu-item');

// ✅ Good: Wait for stable state
await page.getByRole('menuitem').click();
await expect(page.getByRole('menu')).toBeVisible();
```

### 3. 网络时序

```typescript
// ❌ Bad: Assumes data loaded
await page.goto('/dashboard');
expect(await page.textContent('.user-name')).toBe('John');

// ✅ Good: Wait for network
await page.goto('/dashboard');
await page.waitForResponse('**/api/user');
await expect(page.getByTestId('user-name')).toHaveText('John');
```

### 4. 测试隔离

```typescript
// ❌ Bad: Tests share state
test('test 1', async () => { /* creates user */ });
test('test 2', async () => { /* assumes user exists */ });

// ✅ Good: Each test is independent
test.beforeEach(async ({ page }) => {
  await page.request.post('/api/test/reset');
});
```

## 正确的等待方式

```typescript
// Wait for element state
await expect(page.getByText('Success')).toBeVisible();
await expect(page.getByRole('button')).toBeEnabled();
await expect(page.getByRole('dialog')).toBeHidden();

// Wait for navigation
await page.waitForURL(/dashboard/);

// Wait for response
await page.waitForResponse(r => r.url().includes('/api/data'));

// Wait for load state
await page.waitForLoadState('networkidle');

// AVOID arbitrary waits
await page.waitForTimeout(3000); // ❌ BAD
```

## 重试策略

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,

  // Retry only specific tests
  expect: {
    timeout: 10000, // Increase assertion timeout
  },
});

// Per-test retry
test('flaky test', async ({ page }) => {
  test.info().annotations.push({ type: 'issue', description: 'Known flaky' });
  // ...
});
```

## 调试输出

```typescript
// Console output
test('debug test', async ({ page }) => {
  page.on('console', msg => console.log(msg.text()));
  page.on('pageerror', err => console.log(err.message));
});

// Screenshot on step
await page.screenshot({ path: 'debug.png' });
```

## 快速参考

| 命令 | 目的 |
|------|------|
| `PWDEBUG=1` | 启用检查器 |
| `--headed` | 显示浏览器 |
| `--ui` | UI 模式 |
| `page.pause()` | 暂停执行 |
| `show-trace` | 查看追踪文件 |

| 修复方式 | 不稳定原因 |
|----------|-----------|
| 自动等待定位器 | 竞态条件 |
| `waitForResponse` | 网络时序 |
| 测试隔离 | 共享状态 |
| 增加超时 | 慢操作 |
