# 反馈示例

## 好坏反馈对比

### 具体，不笼统

```markdown
BAD: "This is confusing"

GOOD: "This function handles both validation and persistence. Consider
      splitting into `validateUser()` and `saveUser()` for single
      responsibility and easier testing."
```

### 有操作性，不只是批评

```markdown
BAD: "Fix the query"

GOOD: "This will cause N+1 queries - one per post. Use `include: [Author]`
      to eager load authors in a single query. See: [link to docs]"
```

### 有建设性，不是命令式

```markdown
BAD: "Add tests"

GOOD: "Missing test for the case when `email` is already taken. Add a test
      that verifies 409 is returned with appropriate error message."
```

### 提问，不假设

```markdown
BAD: "This is wrong"

GOOD: "I notice this returns null instead of throwing. Is that intentional?
      The other methods throw on not-found. Should this be consistent?"
```

## 表扬示例

用具体的表扬来强化好的模式：

```markdown
"Great use of early returns here - much more readable than nested ifs!"

"Nice extraction of this validation logic into a reusable function."

"Excellent error messages - they'll help debugging in production."

"Good choice using a discriminated union here instead of optional fields."

"Appreciate the comprehensive test coverage, especially the edge cases."
```

## 按类别分类的反馈

### 关键（必须修复）

```markdown
**[CRITICAL] Security: SQL Injection**
Location: `src/users/service.ts:45`

The query uses string interpolation:
`SELECT * FROM users WHERE id = ${id}`

This is vulnerable to SQL injection. Use parameterized query:
`db.query('SELECT * FROM users WHERE id = $1', [id])`
```

### 主要（应该修复）

```markdown
**[MAJOR] Performance: N+1 Query**
Location: `src/posts/service.ts:23`

Current code fetches users in a loop (N+1 problem):
```typescript
for (const post of posts) {
  post.author = await User.findById(post.authorId);
}
```

Suggestion: Use eager loading:
```typescript
const posts = await Post.findAll({ include: [User] });
```

Impact: ~100 extra DB queries per request with current approach.
```

### 次要（可有可无）

```markdown
**[MINOR] Naming: Unclear variable**
Location: `src/utils/date.ts:12`

`d` is unclear. Consider `createdDate` or `timestamp` for better readability.

**[MINOR] Style: Prefer const**
Location: `src/config/index.ts:8`

`let config` is never reassigned. Use `const` for immutability.
```

## 问题格式

```markdown
**[QUESTION]**
Location: `src/orders/service.ts:67`

What's the expected behavior when the user has an existing pending order?
Should this:
- Return the existing order?
- Create a new one anyway?
- Return an error?
```

## 总结格式

```markdown
## Summary

Overall this is a solid implementation of the user registration flow.
The validation logic is clean and the error handling is comprehensive.

**Blocking Issues**: 1 critical (SQL injection)
**Suggestions**: 2 major, 3 minor

Once the SQL injection is fixed, this is ready to merge. The major
suggestions are performance improvements worth considering.
```

## 快速参考

| 反馈类型 | 语气 | 必要行动 |
|---------------|------|-----------------|
| 关键 | 坚定、明确 | 合并前必须修复 |
| 主要 | 建议性 | 应该修复 |
| 次要 | 可选 | 有更好 |
| 表扬 | 积极 | 无 - 强化模式 |
| 问题 | 好奇 | 需要回应 |