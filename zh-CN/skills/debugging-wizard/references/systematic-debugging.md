# 系统化调试

---

## 核心原则

> **在没有进行根本原因调查之前，不要进行任何修复。**

跳过修复理解原因会产生更多错误。系统化调试可以避免"修复一个问题，损坏两个更多"的循环。

---

## 四个强制性阶段

```
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEMATIC DEBUGGING                      │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: ROOT CAUSE INVESTIGATION                          │
│  ├── Read error messages thoroughly                         │
│  ├── Reproduce reliably with documented steps               │
│  ├── Examine recent changes                                 │
│  └── Trace data flow backward                               │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: PATTERN ANALYSIS                                   │
│  ├── Find similar working implementations                   │
│  ├── Study reference implementations completely             │
│  └── Document all differences                               │
├─────────────────────────────────────────────────────────────┤
│  Phase 3: HYPOTHESIS TESTING                                 │
│  ├── Form specific, written hypothesis                      │
│  ├── Test with minimal, isolated changes                    │
│  └── One variable at a time                                 │
├─────────────────────────────────────────────────────────────┤
│  Phase 4: IMPLEMENTATION                                     │
│  ├── Create failing test case                               │
│  ├── Implement single fix addressing root cause             │
│  └── Verify no new breakage                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 阶段 1: 根本原因调查

**目标:** 在尝试任何修复之前，准确理解什么失败了以及为什么。

### 步骤 1.1: 彻底阅读错误信息

```bash
# Don't just read the first line
TypeError: Cannot read property 'map' of undefined
    at UserList.render (UserList.tsx:24)
    at renderWithHooks (react-dom.js:14985)
    at mountIndeterminateComponent (react-dom.js:17811)
```

**关键问题:**
- 什么确切操作失败了？
- 在代码中的哪个位置（文件、行）？
- 调用堆栈是什么？
- 是否有多个错误或只有一个？

### 步骤 1.2: 可靠地重现

```markdown
## Reproduction Steps
1. Navigate to /users
2. Click "Load More" button
3. Wait for loading spinner
4. **ERROR: "Cannot read property 'map' of undefined"**

## Environment
- Browser: Chrome 120
- User: Admin role
- Data state: 50+ users in database
```

**要求:** 记录可以 100% 重现错误的确切步骤。

### 步骤 1.3: 检查最近的更改

```bash
# What changed recently?
git log --oneline -10

# What specifically changed in the failing file?
git log -p UserList.tsx

# When did this start failing?
git bisect start
git bisect bad HEAD
git bisect good v1.2.0
```

### 步骤 1.4: 向后追踪数据流

```typescript
// Error happens here:
users.map(u => u.name)  // users is undefined

// Trace backward:
// Where does 'users' come from?
const users = props.users;

// Where do props come from?
<UserList users={data.users} />

// Where does data come from?
const { data } = useQuery(GET_USERS);

// ROOT CAUSE: Query returns { users: null } when loading
```

### 步骤 1.5: 添加诊断工具

```typescript
// Add temporary logging at boundaries
console.log('[UserList] props:', JSON.stringify(props));
console.log('[UserList] users type:', typeof props.users);
console.log('[UserList] users value:', props.users);

// Check at data source
console.log('[API] Response:', response);
console.log('[API] Response.data:', response.data);
```

---

## 阶段 2: 模式分析

**目标:** 找到工作示例以了解正确行为应该是什么样子。

### 步骤 2.1: 找到类似的工作实现

```bash
# Find similar components that work correctly
grep -r "useQuery" src/components/ --include="*.tsx"

# Find how other lists handle loading states
grep -r "loading" src/components/*List* --include="*.tsx"
```

### 步骤 2.2: 完全研究参考实现

```typescript
// WORKING: ProductList.tsx
function ProductList({ products, loading }) {
  if (loading) return <Spinner />;
  if (!products) return null;  // ← Handles undefined case

  return products.map(p => <ProductItem key={p.id} {...p} />);
}

// BROKEN: UserList.tsx
function UserList({ users, loading }) {
  if (loading) return <Spinner />;
  // Missing: !users check

  return users.map(u => <UserItem key={u.id} {...u} />);  // 💥 Crashes
}
```

### 步骤 2.3: 记录所有差异

| 方面 | 工作的 (ProductList) | 损坏的 (UserList) |
|------|----------------------|-------------------|
| null 检查 | `if (!products)` | 缺失 |
| 默认值 | `products ?? []` | 无 |
| 加载处理 | 渲染前 | 渲染前 |
| 错误处理 | 返回 ErrorState | 缺失 |

---

## 阶段 3: 假设测试

**目标:** 通过受控实验验证你的理解。

### 步骤 3.1: 形成具体、书面的假设

```markdown
## Hypothesis #1
**Statement:** The crash occurs because `users` is undefined when the
query is complete but returns no data.

**Prediction:** Adding a null check before `.map()` will prevent the crash.

**Test:** Add `if (!users) return null;` before the map call.
```

### 步骤 3.2: 使用最小更改进行测试

```typescript
// Change ONLY one thing
function UserList({ users, loading }) {
  if (loading) return <Spinner />;
  if (!users) return null;  // ← Single change

  return users.map(u => <UserItem key={u.id} {...u} />);
}
```

### 步骤 3.3: 一次测试一个变量

```markdown
## Test Results

| Hypothesis | Change | Result | Conclusion |
|------------|--------|--------|------------|
| #1: Null check | Add `if (!users)` | ✓ Pass | Confirmed |

Do NOT test multiple hypotheses simultaneously.
```

---

## 阶段 4: 实现

**目标:** 通过适当的保护措施永久修复错误。

### 步骤 4.1: 首先创建失败的测试用例

```typescript
describe('UserList', () => {
  it('should handle undefined users gracefully', () => {
    // This test should FAIL before the fix
    const { container } = render(<UserList users={undefined} loading={false} />);
    expect(container).not.toThrow();
    expect(screen.queryByRole('list')).not.toBeInTheDocument();
  });
});
```

### 步骤 4.2: 实现单一修复

```typescript
function UserList({ users, loading }: UserListProps) {
  if (loading) return <Spinner />;
  if (!users || users.length === 0) {
    return <EmptyState message="No users found" />;
  }

  return (
    <ul role="list">
      {users.map(u => <UserItem key={u.id} {...u} />)}
    </ul>
  );
}
```

### 步骤 4.3: 验证没有新的损坏

```bash
# Run full test suite
npm test

# Run specific component tests
npm test UserList

# Run integration tests
npm run test:integration

# Verify in browser
# 1. Normal case: 50 users
# 2. Empty case: 0 users
# 3. Loading case: spinner shows
# 4. Error case: error message shows
```

---

## 三次修复阈值

> **3 次修复尝试后 → 停止。**

不同位置的 3 次失败表明存在架构问题，而不是孤立错误。

### 三次失败意味着什么

```
Fix Attempt 1: Added null check → New error in child component
Fix Attempt 2: Fixed child component → New error in parent
Fix Attempt 3: Fixed parent → Original error returns
                              ↓
                    STOP. QUESTION ARCHITECTURE.
```

### 达到阈值时，这样做

1. **停止修复症状**
2. **记录失败模式**
3. **识别被违反的架构假设**
4. **提出结构更改而不是修补**
5. **继续前与团队讨论**

---

## 需要过程重置的危险信号

当你注意到这些时，停止并从阶段 1 重新开始：

| 危险信号 | 为什么是错的 |
|----------|-------------|
| 在追踪数据流之前提出解决方案 | 猜测，而不是调试 |
| 同时进行多个更改 | 无法识别哪个更改有效 |
| 跳过测试创建 | 错误会复发 |
|"让我们试试看是否有效" | 散弹式调试 |
| 在理解原因之前修复 | 临时修复，不是根治 |

---

## 决策流程图

```
                    ┌──────────────────┐
                    │   Bug Reported   │
                    └────────┬─────────┘
                             │
              ┌──────────────▼──────────────┐
              │   Can you reproduce it?      │
              └──────────────┬──────────────┘
                    No       │       Yes
            ┌────────────────┴────────────────┐
            ▼                                  ▼
    ┌───────────────┐               ┌─────────────────┐
    │ Get more info │               │ Trace data flow │
    └───────────────┘               └────────┬────────┘
                                             │
                              ┌──────────────▼──────────────┐
                              │ Do you understand the cause? │
                              └──────────────┬──────────────┘
                                    No       │       Yes
                    ┌────────────────────────┴─────────┐
                    ▼                                   ▼
            ┌───────────────┐               ┌─────────────────┐
            │ Study working │               │ Write hypothesis│
            │   examples    │               └────────┬────────┘
            └───────────────┘                        │
                                             ┌───────▼───────┐
                                             │  Write test   │
                                             └───────┬───────┘
                                                     │
                                             ┌───────▼───────┐
                                             │  Implement    │
                                             └───────┬───────┘
                                                     │
                                  ┌──────────────────▼──────────────────┐
                                  │          Does test pass?            │
                                  └──────────────────┬──────────────────┘
                                            No       │       Yes
                            ┌────────────────────────┴──────────┐
                            ▼                                    ▼
                    ┌───────────────┐                  ┌─────────────────┐
                    │ Attempt < 3?  │                  │      Done       │
                    └───────┬───────┘                  └─────────────────┘
                    No      │      Yes
            ┌───────────────┴─────────────────┐
            ▼                                  ▼
    ┌───────────────────┐          ┌─────────────────────┐
    │ Question          │          │ Return to Phase 1   │
    │ architecture      │          └─────────────────────┘
    └───────────────────┘
```

---

*内容改编自 [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent (@obra), MIT License.*