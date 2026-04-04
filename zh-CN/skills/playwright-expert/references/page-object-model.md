# Page Object Model

## 基本 Page Object

```typescript
// pages/LoginPage.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Log in' });
    this.errorMessage = page.getByRole('alert');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async getErrorMessage() {
    return this.errorMessage.textContent();
  }
}
```

## 在测试中使用 Page Object

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test('successful login redirects to dashboard', async ({ page }) => {
  const loginPage = new LoginPage(page);

  await loginPage.goto();
  await loginPage.login('user@test.com', 'password123');

  await expect(page).toHaveURL(/dashboard/);
});

test('invalid credentials show error', async ({ page }) => {
  const loginPage = new LoginPage(page);

  await loginPage.goto();
  await loginPage.login('user@test.com', 'wrongpassword');

  await expect(loginPage.errorMessage).toBeVisible();
});
```

## 自定义 Fixtures

```typescript
// fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';

type Fixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: Page;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  authenticatedPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('user@test.com', 'password123');
    await page.waitForURL(/dashboard/);
    await use(page);
  },
});

export { expect } from '@playwright/test';
```

## 使用 Fixtures

```typescript
// tests/dashboard.spec.ts
import { test, expect } from '../fixtures';

test('shows user profile', async ({ authenticatedPage, dashboardPage }) => {
  await expect(dashboardPage.userProfile).toBeVisible();
});
```

## 组件 Page Object

```typescript
// components/NavBar.ts
export class NavBar {
  constructor(private page: Page) {}

  readonly homeLink = () => this.page.getByRole('link', { name: 'Home' });
  readonly profileLink = () => this.page.getByRole('link', { name: 'Profile' });
  readonly logoutButton = () => this.page.getByRole('button', { name: 'Logout' });

  async logout() {
    await this.logoutButton().click();
  }
}

// pages/DashboardPage.ts
export class DashboardPage {
  readonly navBar: NavBar;

  constructor(private page: Page) {
    this.navBar = new NavBar(page);
  }
}
```

## 快速参考

| 模式 | 目的 |
|------|------|
| Page Object | 封装页面交互 |
| Fixture | 跨测试共享设置 |
| 组件 PO | 可复用 UI 组件 |
| 定位器方法 | 延迟求值 |

| 最佳实践 | 原因 |
|----------|------|
| 方法用于操作 | 可读的测试 |
| 定位器作为 getter | 延迟求值 |
| PO 中不做断言 | 灵活性 |
| Fixture 用于设置 | DRY，可维护 |
