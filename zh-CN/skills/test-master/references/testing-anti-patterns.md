# 测试反模式

---

## 核心原则

> **"测试代码做什么，而不是测试 Mock 做什么。"**

当测试验证 Mock 行为而不是实际功能时，它们提供虚假的信心，同时捕获零个真正的 Bug。

---

## 五大反模式

### 反模式一：测试 Mock 行为

**问题：** 验证 Mock 存在并被调用，而不是测试实际的组件输出。

```typescript
// ❌ BAD: Testing the mock, not the behavior
it('should call the API', () => {
  const mockApi = jest.fn().mockResolvedValue({ data: 'test' });
  const service = new UserService(mockApi);

  service.getUser(1);

  expect(mockApi).toHaveBeenCalledWith(1); // Testing mock, not result
});
```

```typescript
// ✅ GOOD: Testing actual behavior
it('should return user data from API', async () => {
  const mockApi = jest.fn().mockResolvedValue({ id: 1, name: 'Alice' });
  const service = new UserService(mockApi);

  const user = await service.getUser(1);

  expect(user.name).toBe('Alice'); // Testing actual output
});
```

**解决方案：** 测试真正的组件输出。如果你只能验证 Mock 调用，重新考虑该测试是否增加了价值。

---

### 反模式二：生产代码中的测试专用方法

**问题：** 向生产类添加仅用于测试设置或清理的方法。

```typescript
// ❌ BAD: Production code polluted with test concerns
class UserCache {
  private cache: Map<number, User> = new Map();

  getUser(id: number): User | undefined {
    return this.cache.get(id);
  }

  // This method exists ONLY for tests
  _resetForTesting(): void {
    this.cache.clear();
  }
}
```

```typescript
// ✅ GOOD: Test utilities separate from production
// production/UserCache.ts
class UserCache {
  private cache: Map<number, User> = new Map();

  getUser(id: number): User | undefined {
    return this.cache.get(id);
  }
}

// test/helpers.ts
function createFreshCache(): UserCache {
  return new UserCache(); // Fresh instance per test
}
```

**解决方案：** 将清理逻辑移到测试工具函数中。每个测试使用新实例而不是重置方法。

---

### 反模式三：不理解就 Mock

**问题：** 不理解副作用就过度 Mock，导致测试通过但隐藏了真正的问题。

```typescript
// ❌ BAD: Mocking everything without understanding
it('should process order', async () => {
  jest.mock('./inventory');
  jest.mock('./payment');
  jest.mock('./shipping');
  jest.mock('./notifications');

  const result = await processOrder(order);

  expect(result.success).toBe(true); // What did we actually test?
});
```

```typescript
// ✅ GOOD: Strategic mocking with real components where possible
it('should process order with real inventory check', async () => {
  // Real inventory service against test database
  const inventory = new InventoryService(testDb);

  // Mock only external services
  const payment = mockPaymentGateway();

  const processor = new OrderProcessor(inventory, payment);
  const result = await processor.process(order);

  expect(result.success).toBe(true);
  expect(await inventory.getStock(order.itemId)).toBe(originalStock - 1);
});
```

**解决方案：** 先用真实实现运行测试来理解行为。然后在适当的层级 Mock — 外部服务，而非内部逻辑。

---

### 反模式四：不完整的 Mock

**问题：** 部分 Mock 响应缺少生产代码期望的下游字段。

```typescript
// ❌ BAD: Incomplete mock response
const mockUserApi = jest.fn().mockResolvedValue({
  id: 1,
  name: 'Test User'
  // Missing: email, createdAt, permissions, settings...
});

// Test passes, but production crashes when accessing user.email
```

```typescript
// ✅ GOOD: Complete mock matching real API response
const mockUserApi = jest.fn().mockResolvedValue({
  id: 1,
  name: 'Test User',
  email: 'test@example.com',
  createdAt: '2024-01-01T00:00:00Z',
  permissions: ['read', 'write'],
  settings: {
    theme: 'light',
    notifications: true
  }
});

// Or use a factory
const mockUserApi = jest.fn().mockResolvedValue(
  createMockUser({ name: 'Test User' }) // Factory fills defaults
);
```

**解决方案：** 镜像完整的真实 API 响应结构。使用工厂生成具有合理默认值的完整 Mock 对象。

---

### 反模式五：集成测试作为事后补充

**问题：** 将测试视为可选的后续工作，而非开发的组成部分。

```typescript
// ❌ BAD: "We'll add tests later"
// Day 1: Write 500 lines of code
// Day 2: Write 500 more lines
// Day 3: "We need to ship, tests can wait"
// Day 30: Catastrophic bug in production
// Day 31: "Why didn't we have tests?"
```

```typescript
// ✅ GOOD: Tests are part of implementation
// Write failing test
it('should reject duplicate usernames', async () => {
  await createUser({ username: 'alice' });

  await expect(createUser({ username: 'alice' }))
    .rejects.toThrow('Username already exists');
});

// Make it pass
async function createUser(data: UserInput): Promise<User> {
  const existing = await db.users.findByUsername(data.username);
  if (existing) {
    throw new Error('Username already exists');
  }
  return db.users.create(data);
}

// Feature AND test ship together
```

**解决方案：** 遵循 TDD — 测试就是实现，不是文档。没有测试的功能不算"完成"。

---

## 检测检查清单

检查你的测试是否有以下警告信号：

| 警告信号 | 反模式 |
|----------|--------|
| `expect(mock).toHaveBeenCalled()` 而不测试输出 | 测试 Mock 行为 |
| 生产代码中以 `_` 或 `ForTesting` 开头的方法 | 测试专用方法 |
| 每个依赖都被 Mock | 不理解就 Mock |
| Mock 只返回 `{ success: true }` | 不完整的 Mock |
| 测试文件在功能发布数周后才添加 | 测试作为事后补充 |

---

## 快速参考

| 反模式 | 症状 | 修复 |
|--------|------|------|
| 测试 Mock | 只有 Mock 断言，没有行为测试 | 断言实际输出 |
| 测试专用方法 | 生产代码中的 `_reset()`、`_setForTest()` | 使用新实例 |
| 过度 Mock | 每个测试 10+ 个 Mock | 先用真实依赖测试 |
| 不完整的 Mock | 最小化的桩响应 | 使用工厂，匹配真实情况 |
| 测试作为事后补充 | 功能未经测试就发布 | 从一开始就 TDD |

---

*内容改编自 [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent (@obra)，MIT License。*
