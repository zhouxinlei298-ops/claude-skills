# 报告模板

## 代码审查报告模板

```markdown
# Code Review: [PR Title]

## Summary
[1-2 sentence overview of the changes and overall assessment]

**Verdict**: [ ] Approve | [x] Request Changes | [ ] Comment

## Critical Issues (Must Fix)

### 1. [File:Line] Security: SQL Injection Risk
- **Current**: String interpolation in query
- **Suggested**: Use parameterized query
- **Impact**: Potential data breach

```typescript
// Current (vulnerable)
const query = `SELECT * FROM users WHERE id = ${id}`;

// Suggested (secure)
const query = 'SELECT * FROM users WHERE id = $1';
db.query(query, [id]);
```

## Major Issues (Should Fix)

### 1. [File:Line] Performance: N+1 Query
- **Current**: Fetching users in loop
- **Suggested**: Use eager loading with include
- **Impact**: ~100 extra DB queries per request

### 2. [File:Line] Logic: Missing edge case
- **Current**: No handling for empty array
- **Suggested**: Add guard clause
- **Impact**: Potential runtime error

## Minor Issues (Nice to Have)

### 1. [File:Line] Naming: Unclear variable name
- **Current**: `d`
- **Suggested**: `createdDate`

### 2. [File:Line] Style: Inconsistent formatting
- **Current**: Mixed quotes
- **Suggested**: Use single quotes consistently

## Positive Feedback
- Clean separation of concerns in service layer
- Comprehensive input validation on DTOs
- Good test coverage for edge cases
- Excellent error messages

## Questions for Author
- What's the expected behavior when X happens?
- Should this support pagination for large datasets?
- Is the retry logic intentional or accidental?

## Test Coverage Assessment
- [ ] Happy path tested
- [x] Error cases tested
- [ ] Edge cases tested (missing empty array test)
- [x] Integration tests present

## Checklist
- [x] No security vulnerabilities
- [ ] Performance is acceptable (N+1 issue)
- [x] Code is readable
- [x] Tests are adequate
- [x] Documentation is present
```

## 结论指南

| 结论 | 使用时机 |
|------|----------|
| **批准** | 无阻塞问题，仅有次要建议 |
| **请求修改** | 关键或主要问题必须修复 |
| **评论** | 问题需要回答，无阻塞问题 |

## 严重程度定义

| 严重程度 | 定义 | 示例 |
|----------|------|------|
| **关键** | 安全风险、数据丢失、崩溃 | SQL 注入、认证绕过 |
| **主要** | 重大性能、可维护性问题 | N+1 查询、上帝函数 |
| **次要** | 风格、命名、小改进 | 变量命名、格式化 |

## 时间分配

| 部分 | 建议时间 |
|------|----------|
| 上下文和理解 | 5 分钟 |
| 关键/安全审查 | 10 分钟 |
| 逻辑和性能 | 15 分钟 |
| 测试审查 | 10 分钟 |
| 编写报告 | 10 分钟 |
| **总计** | ~50 分钟 |

## 提交前快速检查

- [ ] 所有关键问题有明确的修复方案
- [ ] 主要问题解释了影响
- [ ] 包含至少一条正面评价
- [ ] 问题具体且可回答
- [ ] 结论与发现的问题匹配
