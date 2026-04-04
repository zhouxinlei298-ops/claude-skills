# TDD 铁律

---

## 基本原则

> **没有失败的测试，就不写生产代码。**

这是不可妥协的。如果你在写失败测试之前就写了生产代码，删掉它重新开始。没有例外。

---

## 三条铁律

### 铁律一：基本规则

> "除非是为了让失败的测试通过，否则你不应该编写任何生产代码。"

每一行生产代码都必须有对应的测试，该测试：
1. 先于代码编写
2. 被观察到失败
3. 因为该代码现在通过

### 铁律二：通过观察来验证

> "如果你没有看到测试失败，你就不知道它是否测试了正确的东西。"

必须验证的步骤：
- 编写测试
- 运行并**观察失败**
- 验证失败消息是有意义的
- 然后才实现修复

你从未见过失败的测试什么也证明不了。

### 铁律三：最终规则

> "生产代码存在 → 就存在一个先失败的测试。否则 → 这不是 TDD。"

没有中间地带。没有先前失败测试而编写的代码不是测试驱动开发，无论之后有多少测试存在。

---

## 红-绿-重构循环

### 红：编写一个最小的失败测试

```typescript
// Start with the smallest possible failing test
it('should return 0 for empty array', () => {
  expect(sum([])).toBe(0);
});
// Run: ✗ FAIL - sum is not defined
```

**要求：**
- 一次一个测试
- 最小范围
- 清晰的失败消息
- 观察红色

### 绿：实现最简单的通过代码

```typescript
// Write only enough code to pass this specific test
function sum(numbers: number[]): number {
  return 0;
}
// Run: ✓ PASS
```

**要求：**
- 最简单的可能实现
- 没有额外功能
- 没有优化
- 只让它通过

### 重构：在保持测试绿色的同时改进

```typescript
// Now improve the code while tests stay green
function sum(numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}
// Run: ✓ PASS (still)
```

**要求：**
- 测试必须保持绿色
- 移除重复
- 提高清晰度
- 不添加新功能

---

## 应该拒绝的常见辩解

这些想法表明你即将违反 TDD：

| 辩解 | 为什么是错的 |
|------|-------------|
| "我可以快速手动测试" | 手动测试不能防止回归 |
| "我先写代码再补测试来节省时间" | 你会跳过边界情况并测试实现细节 |
| "这太简单了不需要测试" | 简单的代码会变更；测试记录期望 |
| "我已经写了代码，现在不能删了" | 沉没成本谬误；删掉它 |
| "我知道这能工作，我以前做过" | 你的记忆不是文档 |
| "我们赶时间" | 技术债务比 TDD 代价更高 |

---

## 实践应用

### 开始新功能

```typescript
// 1. RED: Write failing test for simplest behavior
describe('UserValidator', () => {
  it('should reject empty email', () => {
    expect(validateEmail('')).toBe(false);
  });
});

// 2. GREEN: Implement minimal passing code
function validateEmail(email: string): boolean {
  return email.length > 0;
}

// 3. RED: Add next failing test
it('should reject email without @', () => {
  expect(validateEmail('invalid')).toBe(false);
});

// 4. GREEN: Extend to pass both tests
function validateEmail(email: string): boolean {
  return email.length > 0 && email.includes('@');
}

// Continue cycle...
```

### 修复 Bug

```typescript
// 1. RED: Write test that exposes the bug
it('should handle negative numbers in sum', () => {
  expect(sum([-1, -2, -3])).toBe(-6);
});
// Run: ✗ FAIL - got 0 instead of -6

// 2. GREEN: Fix the bug
function sum(numbers: number[]): number {
  return numbers.reduce((acc, n) => acc + n, 0);
}
// Run: ✓ PASS

// Bug is now fixed AND protected against regression
```

---

## 验证检查清单

在声称任何代码完成之前：

- [ ] 每个生产函数都有对应的测试
- [ ] 每个测试都先于其实现编写
- [ ] 每个测试都被观察到先失败
- [ ] 测试验证行为，而非实现
- [ ] 重构保持所有测试绿色
- [ ] 没有生产代码在没有测试的情况下存在

---

*内容改编自 [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent (@obra)，MIT License。*
