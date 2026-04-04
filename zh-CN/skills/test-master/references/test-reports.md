# 测试报告

## 测试报告模板

```markdown
# Test Report: {Feature Name}

**Date**: YYYY-MM-DD
**Tester**: {Name}
**Version**: {App Version}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | X |
| Passed | X |
| Failed | X |
| Skipped | X |
| Coverage | X% |

## Test Scope

- [x] Unit tests
- [x] Integration tests
- [x] E2E tests
- [ ] Performance tests
- [ ] Security tests

## Findings

### [CRITICAL] {Issue Title}
- **Location**: src/api/users.ts:45
- **Steps to Reproduce**:
  1. Send POST to /api/users without auth
  2. Request succeeds with 201
- **Expected**: 401 Unauthorized
- **Actual**: 201 Created
- **Impact**: Unauthorized user creation
- **Fix**: Add auth middleware

### [HIGH] {Issue Title}
- **Location**: src/services/orders.ts:123
- **Description**: N+1 query in order list
- **Impact**: 3s response time with 100 orders
- **Fix**: Add eager loading for order items

### [MEDIUM] {Issue Title}
- **Details**: ...

### [LOW] {Issue Title}
- **Details**: ...

## Coverage Analysis

| Module | Lines | Branches | Functions |
|--------|-------|----------|-----------|
| api/ | 85% | 78% | 90% |
| services/ | 92% | 85% | 95% |
| utils/ | 100% | 100% | 100% |

### Coverage Gaps
- `src/api/admin.ts` - 0% (no tests)
- `src/services/payment.ts:45-60` - Error handling untested

## Recommendations

1. **Immediate**: Add auth middleware to admin routes
2. **High Priority**: Optimize order queries
3. **Medium Priority**: Add tests for payment error handling
4. **Low Priority**: Increase branch coverage in api/

## Performance Results

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| GET /users | 45ms | 120ms | 250ms |
| POST /orders | 150ms | 400ms | 800ms |

## Sign-off

- [ ] All critical issues addressed
- [ ] Coverage meets threshold (80%)
- [ ] Performance meets SLA
```

## 严重程度定义

| 严重程度 | 判定标准 |
|----------|----------|
| **CRITICAL** | 安全漏洞、数据丢失、系统崩溃 |
| **HIGH** | 主要功能故障、严重性能问题 |
| **MEDIUM** | 功能部分失效、存在替代方案 |
| **LOW** | 次要问题、外观问题、边界情况 |

## 快速参考

| 部分 | 内容 |
|------|------|
| 摘要 | 高层级指标 |
| 发现 | 按严重程度排列的问题 |
| 覆盖率 | 代码覆盖率分析 |
| 建议 | 按优先级排列的行动项 |
| 签收 | 批准标准 |
