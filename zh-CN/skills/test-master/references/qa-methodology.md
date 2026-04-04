# QA 方法论

## 手动测试类型

### 探索性测试
```markdown
**Charter**: Explore {feature} with focus on {aspect}
**Duration**: 60-90 min
**Mission**: Find defects in {specific functionality}

Test Ideas:
- Boundary conditions & edge cases
- Error handling & recovery
- User workflow variations
- Integration points

Findings:
1. [HIGH] {Issue + impact}
2. [MED] {Issue + impact}

Coverage: {Areas explored} | Risks: {Identified risks}
```

### 可用性测试
```markdown
**Task**: Can users complete {action} intuitively?
**Metrics**: Time to complete, errors made, satisfaction (1-5)
**Success**: 80% complete without help in <5 min

Observations:
- Navigation confusing at {step}
- Users expect {A} but get {B}
- Positive: {feature feedback}
```

### 可访问性测试（WCAG 2.1 AA）
```typescript
test('accessibility compliance', async ({ page }) => {
  // Keyboard navigation
  await page.keyboard.press('Tab');
  expect(['A', 'BUTTON', 'INPUT']).toContain(
    await page.evaluate(() => document.activeElement.tagName)
  );
  
  // ARIA labels
  expect(await page.getByRole('button').first().getAttribute('aria-label')).toBeTruthy();
  
  // Color contrast (axe-core)
  const violations = await page.evaluate(async () => {
    const axe = await import('axe-core');
    return (await axe.run()).violations;
  });
  expect(violations).toHaveLength(0);
});
```

### 本地化测试
```markdown
**Test**: {Feature} in {language/locale}
- [ ] Text displays without truncation
- [ ] Date/time/currency formats correct
- [ ] Right-to-left layout (Arabic, Hebrew)
- [ ] Character encoding UTF-8
- [ ] Sort order respects locale
```

### 兼容性矩阵
```markdown
| Browser | Version | OS | Status |
|---------|---------|----|----- --|
| Chrome | Latest | Win/Mac | ✓ |
| Firefox | Latest | Win/Mac | ✓ |
| Safari | Latest | macOS/iOS | ✓ |
| Edge | Latest | Windows | ✓ |
```

## 测试设计技术

### 配对测试
```typescript
// Test all parameter pairs efficiently
const pairwiseTests = [
  { browser: 'chrome', os: 'windows', lang: 'en' },
  { browser: 'firefox', os: 'mac', lang: 'es' },
  { browser: 'safari', os: 'windows', lang: 'fr' },
  // Covers all pairs with minimal tests
];
```

### 基于风险的测试
```markdown
| Risk | Probability | Impact | Priority | Test Effort |
|------|-------------|--------|----------|-------------|
| Critical | High | High | P0 | Exhaustive |
| High | Med-High | High | P1 | Comprehensive |
| Medium | Low-Med | Med | P2 | Standard |
| Low | Low | Low | P3 | Smoke only |
```

## 缺陷管理

### 根因分析（5 Whys）
```markdown
1. Why did defect occur? {User input not validated}
2. Why wasn't it validated? {Validation logic missing}
3. Why was it missing? {Requirement unclear}
4. Why was requirement unclear? {Acceptance criteria incomplete}
5. Why incomplete? {No QA review in planning}

**Root Cause**: QA not involved in requirements phase
**Prevention**: Add QA to all planning meetings
```

### 缺陷报告模板
```markdown
## [CRITICAL] {Defect Title}

**Steps to Reproduce**:
1. {Step 1}
2. {Step 2}

**Expected**: {Should happen}
**Actual**: {Actually happens}
**Impact**: {Business/user impact}
**Root Cause**: {Why it happened}
**Fix**: {Recommended solution}
```

## 质量指标

### 关键计算
```typescript
// Defect Removal Efficiency (target: >95%)
const dre = (defectsInTesting / (defectsInTesting + defectsInProd)) * 100;

// Defect Leakage (target: <5%)
const leakage = (defectsInProd / totalDefects) * 100;

// Test Effectiveness (target: >90%)
const effectiveness = (defectsFoundByTests / totalDefects) * 100;

// Automation ROI
const roi = (timeSaved - maintenanceCost - developmentCost) / developmentCost;
```

### 质量仪表板
```markdown
| Metric | Target | Actual | Trend | Status |
|--------|--------|--------|-------|--------|
| Coverage | >80% | 87% | ↑ | ✓ |
| Defect Leakage | <5% | 3% | ↓ | ✓ |
| Automation | >70% | 68% | ↑ | ⚠ |
| Critical Defects | 0 | 0 | → | ✓ |
| MTTR | <48h | 36h | ↓ | ✓ |
```

## 持续测试与左移

### 左移活动
```markdown
**Early Testing**:
- Review requirements for testability
- Create test cases during design
- TDD: unit tests with code
- Automated tests in CI pipeline
- Static analysis on commit
- Security scanning pre-merge

**Benefits**: 10x cheaper defect fixes, faster feedback
```

### 反馈周期目标
```typescript
const feedbackCycle = {
  unitTests: '< 5 min',       // On save
  integration: '< 15 min',    // On commit
  e2e: '< 30 min',            // On PR
  regression: '< 2 hours',    // Nightly
};
```

## 质量倡导

### 质量门
```markdown
## Production Release Gate

**Must Pass (Blockers)**:
- [ ] Zero critical defects
- [ ] Coverage >80%
- [ ] All P0/P1 tests passing
- [ ] Performance SLA met
- [ ] Security scan clean
- [ ] Accessibility WCAG AA

**Decision**: GO | NO-GO | GO with exceptions
```

### 团队培训计划
```markdown
**Week 1-2**: Test fundamentals
**Week 3-4**: Automation basics
**Week 5-6**: Advanced topics (perf, security, API)
**Ongoing**: Best practices, tool updates
```

## 测试规划

### 测试计划模板
```markdown
## Test Plan: {Feature}

**Scope**: {What to test}
**Types**: Unit, Integration, E2E, Perf, Security
**Resources**: {Team allocation}
**Dependencies**: {Prerequisites}
**Schedule**: {Timeline}
**Entry Criteria**: {Start conditions}
**Exit Criteria**: {Completion conditions}
**Risks**: {Identified risks + mitigation}
```

### 环境策略
```markdown
| Env | Purpose | Data | Refresh | Access |
|-----|---------|------|---------|--------|
| Dev | Development | Synthetic | On-demand | All |
| Test | QA testing | Test data | Daily | QA |
| Stage | Pre-prod | Prod-like | Weekly | Limited |
| Prod | Live | Real | N/A | Ops |
```

## 快速参考

| 测试类型 | 时机 | 持续时间 |
|----------|------|----------|
| 探索性测试 | 新功能 | 60-120 分钟 |
| 可用性测试 | UI 变更 | 2-4 小时 |
| 可访问性测试 | 每次发布 | 1-2 小时 |
| 本地化测试 | 多区域 | 1 天/语言 |

| 指标 | 优秀 | 良好 | 需改进 |
|------|------|------|--------|
| 覆盖率 | >90% | 70-90% | <70% |
| 泄漏率 | <2% | 2-5% | >5% |
| 自动化率 | >80% | 60-80% | <60% |
| MTTR | <24h | 24-48h | >48h |
