# 选择器与定位器

## 选择器优先级（从最佳到最差）

```typescript
// 1. Role-based (BEST - accessible)
await page.getByRole('button', { name: 'Submit' });
await page.getByRole('textbox', { name: 'Email' });
await page.getByRole('link', { name: 'Home' });
await page.getByRole('heading', { level: 1 });

// 2. Label/placeholder (good for forms)
await page.getByLabel('Email address');
await page.getByPlaceholder('Enter your email');

// 3. Test ID (good for non-semantic elements)
await page.getByTestId('user-avatar');
await page.getByTestId('submit-button');

// 4. Text content
await page.getByText('Welcome back');
await page.getByText(/welcome/i);  // Case insensitive

// 5. CSS/XPath (AVOID - brittle)
await page.locator('.submit-btn');  // Last resort
await page.locator('#email-input');
```

## 基于角色的选择器

```typescript
// Buttons
page.getByRole('button', { name: 'Submit' });
page.getByRole('button', { name: /save/i });

// Links
page.getByRole('link', { name: 'Documentation' });

// Inputs
page.getByRole('textbox', { name: 'Username' });
page.getByRole('checkbox', { name: 'Remember me' });
page.getByRole('combobox', { name: 'Country' });

// Navigation
page.getByRole('navigation');
page.getByRole('main');
page.getByRole('banner');

// Tables
page.getByRole('row', { name: 'John Doe' });
page.getByRole('cell', { name: 'Active' });
```

## 过滤定位器

```typescript
// Filter by text
page.getByRole('listitem').filter({ hasText: 'Product A' });

// Filter by child locator
page.getByRole('listitem').filter({
  has: page.getByRole('button', { name: 'Delete' })
});

// Filter by NOT having
page.getByRole('listitem').filter({
  hasNot: page.getByText('Sold out')
});

// Chain locators
page.getByTestId('product-card').getByRole('button', { name: 'Buy' });
```

## 处理多个元素

```typescript
// Get nth element (0-indexed)
page.getByRole('listitem').nth(0);
page.getByRole('listitem').first();
page.getByRole('listitem').last();

// Count elements
const count = await page.getByRole('listitem').count();

// Iterate
for (const item of await page.getByRole('listitem').all()) {
  console.log(await item.textContent());
}
```

## 测试 ID

```html
<!-- Add in HTML -->
<button data-testid="submit-button">Submit</button>
```

```typescript
// Configure custom attribute
// playwright.config.ts
use: {
  testIdAttribute: 'data-test-id'
}

// Use in tests
page.getByTestId('submit-button');
```

## 快速参考

| 定位器 | 最适合 |
|--------|--------|
| `getByRole()` | 按钮、链接、输入框 |
| `getByLabel()` | 表单字段 |
| `getByPlaceholder()` | 没有标签的输入框 |
| `getByTestId()` | 非语义元素 |
| `getByText()` | 静态文本 |
| `filter()` | 缩小结果范围 |
| `nth()` / `first()` | 多个匹配项 |
