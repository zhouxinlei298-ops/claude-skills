# 常见问题

## N+1 查询问题

```typescript
// N+1 queries - BAD
const posts = await Post.findAll();
for (const post of posts) {
  post.author = await User.findById(post.authorId); // N queries!
}

// Single query with join - GOOD
const posts = await Post.findAll({ include: [User] });

// Or batch load
const posts = await Post.findAll();
const authorIds = posts.map(p => p.authorId);
const authors = await User.findByIds(authorIds);
```

## 缺少错误处理

```typescript
// Unhandled rejection - BAD
const data = await fetch('/api/data').then(r => r.json());

// Proper error handling - GOOD
try {
  const response = await fetch('/api/data');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const data = await response.json();
} catch (error) {
  logger.error('Failed to fetch data', { error });
  throw new DataFetchError('Could not load data');
}
```

## 魔法数字/字符串

```typescript
// Magic number - BAD
if (user.age >= 18) { ... }
setTimeout(fn, 86400000);

// Named constant - GOOD
const MINIMUM_AGE = 18;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

if (user.age >= MINIMUM_AGE) { ... }
setTimeout(fn, ONE_DAY_MS);
```

## 深层嵌套

```typescript
// Deep nesting - BAD
if (user) {
  if (user.isActive) {
    if (user.hasPermission) {
      doSomething();
    }
  }
}

// Early returns - GOOD
if (!user || !user.isActive || !user.hasPermission) {
  return;
}
doSomething();
```

## 上帝函数

```typescript
// Does too much - BAD
async function processOrder(order) {
  // validate
  // check inventory
  // process payment
  // send email
  // update database
  // log analytics
}

// Single responsibility - GOOD
async function processOrder(order) {
  await validateOrder(order);
  await reserveInventory(order);
  await chargePayment(order);
  await sendConfirmation(order);
}
```

## 可变共享状态

```typescript
// Shared mutable - BAD
const config = { debug: false };
function enableDebug() {
  config.debug = true;
}

// Immutable pattern - GOOD
function createConfig(overrides = {}) {
  return Object.freeze({ debug: false, ...overrides });
}
```

## 缺少 Null 检查

```typescript
// Unsafe access - BAD
const name = user.profile.name;

// Safe access - GOOD
const name = user?.profile?.name ?? 'Unknown';
```

## 同步文件操作

```typescript
// Blocks event loop - BAD
const data = fs.readFileSync('file.txt');

// Non-blocking - GOOD
const data = await fs.promises.readFile('file.txt');
```

## 快速参考

| 问题 | 影响 | 修复 |
|------|------|------|
| N+1 查询 | 性能 | 预加载或批量加载 |
| 缺少错误处理 | 可靠性 | Try/catch + 日志 |
| 魔法数字 | 可维护性 | 命名常量 |
| 深层嵌套 | 可读性 | 提前返回 |
| 上帝函数 | 可测试性 | 单一职责 |
| 可变共享状态 | Bug | 不可变模式 |
| 缺少 Null 检查 | 崩溃 | 可选链 |
| 同步文件操作 | 性能 | 异步操作 |
