# 调试策略

## 二分查找

分治法来找到错误位置。

```markdown
1. Comment out/disable half the code
2. Test if bug still occurs
3. If yes: bug is in remaining half
4. If no: bug is in disabled half
5. Repeat until isolated
```

```typescript
// Example: Bug in data processing pipeline
async function process(data) {
  const step1 = await transform(data);
  // Bug somewhere below?

  const step2 = await validate(step1);
  console.log('After step2:', step2); // Check here

  const step3 = await enrich(step2);
  const step4 = await save(step3);
  return step4;
}
```

## 最小复现

剥离所有内容，直到只剩下错误。

```markdown
1. Create new minimal project
2. Add only code needed to reproduce
3. Remove dependencies one by one
4. Simplify inputs to smallest failing case
5. Document exact reproduction steps
```

```typescript
// Instead of debugging full app
// Create minimal test case:
const input = { id: null }; // Minimal failing input
const result = processUser(input);
console.log(result); // Isolate the exact failure
```

## Git Bisect

找到引入错误的提交。

```bash
# Start bisect
git bisect start

# Mark current commit as bad
git bisect bad

# Mark known good commit
git bisect good v1.0.0

# Git checks out middle commit
# Test and mark:
git bisect good  # or
git bisect bad

# Repeat until found
# Git will say: "abc123 is the first bad commit"

# End bisect
git bisect reset
```

```bash
# Automated bisect with test script
git bisect start HEAD v1.0.0
git bisect run npm test
```

## 时间旅行调试

从失败点向后工作。

```markdown
1. Start at the error/failure point
2. What value caused it? Where did that come from?
3. Trace backwards through the code
4. Find where the value diverged from expected
```

```typescript
// Error: Cannot read 'name' of undefined at line 45

// Line 45: const name = user.name;
// Q: Why is user undefined?

// Line 40: const user = users.find(u => u.id === id);
// Q: Why didn't find() return a user?

// Check: Is the id correct? Are users populated?
console.log({ id, users, user });
```

## 橡皮鸭调试

一步一步解释问题。

```markdown
1. State what the code should do
2. Explain what it actually does
3. Walk through the code line by line
4. Describe what each line does
5. The discrepancy often becomes obvious
```

## Delta 调试

当最近出现问题的时候。

```bash
# Check what changed
git diff HEAD~5..HEAD

# Check specific file history
git log -p --follow -- src/problematic-file.ts

# Find when file last worked
git log --oneline -- src/problematic-file.ts
```

## 快速参考

| 策略 | 最适用于 |
|------|----------|
| Binary Search | 未知错误位置 |
| Minimal Repro | 复杂错误、报告 |
| Git Bisect | 回归错误 |
| Time Travel | 已知错误位置 |
| Rubber Duck | 逻辑错误 |
| Delta Debug | 最近损坏 |