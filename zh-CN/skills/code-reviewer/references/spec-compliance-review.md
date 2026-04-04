# 规范合规性审查

---

## 两阶段审查架构

```
                    ┌─────────────────────┐
                    │   Implementation    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  STAGE 1: Spec      │
                    │  Compliance Review  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                  │
      ┌───────▼───────┐                ┌────────▼────────┐
      │   ✗ Issues    │                │   ✓ Compliant   │
      │     Found     │                │                 │
      └───────┬───────┘                └────────┬────────┘
              │                                  │
              │                        ┌────────▼────────┐
              │                        │  STAGE 2: Code  │
              │                        │  Quality Review │
              │                        └────────┬────────┘
              │                                  │
              │                    ┌─────────────┴─────────────┐
              │                    │                           │
              │            ┌───────▼───────┐         ┌────────▼────────┐
              │            │   ✗ Issues    │         │   ✓ Approved    │
              │            │     Found     │         │                 │
              │            └───────┬───────┘         └─────────────────┘
              │                    │
              └────────────────────┴────────────────────┐
                                                        │
                                              ┌─────────▼─────────┐
                                              │ Return to Author  │
                                              └───────────────────┘
```

**关键：** 在阶段 2（代码质量）之前完成阶段 1（规范合规性）。永远不要对不符合规范的功能进行代码质量审查。

---

## 阶段 1：规范合规性审查

### 核心指导原则

> "实现者完成得太快了。他们的报告可能是不完整的、不准确的或过于乐观的。"

以专业的怀疑态度对待每次审查。独立验证声明。

### 三个验证类别

#### 类别 1：缺失的需求

**检查被请求但未实现的功能。**

| 问题 | 如何验证 |
|------|----------|
| 是否跳过了请求的功能？ | 将 PR 与原始需求逐行比较 |
| 边界情况是否处理？ | 检查错误路径、空状态、边界 |
| 错误场景是否处理？ | 查找 try/catch、错误边界、验证 |
| 正常路径是否完整？ | 手动追踪主要用例 |

```markdown
## Example Review Finding

**Missing Requirement:** Issue #42 requested "password must be at least 8 characters"

**Found in code:**
```typescript
// No length validation present
function validatePassword(password: string) {
  return password.length > 0;  // Only checks non-empty
}
```

**Status:** ❌ Incomplete - minimum length validation missing
```

#### 类别 2：不必要的添加

**检查范围蔓延和过度工程。**

| 问题 | 如何验证 |
|------|----------|
| 超出规范的功能？ | 与原始需求比较 |
| 过度工程？ | 复杂性是否被需求所证明？ |
| 过早优化？ | 是否在没有测量数据的情况下引用性能？ |
| 未请求的抽象？ | 是否有只用一次的辅助函数/工具？ |

```markdown
## Example Review Finding

**Unnecessary Addition:** Added caching layer not in requirements

**Found in code:**
```typescript
// Original requirement: "Fetch user by ID"
// Actual implementation:
class CachedUserRepository {  // Not requested
  private cache = new Map();
  private ttl = 60000;

  async getUser(id: string) {
    if (this.cache.has(id)) { ... }
    // 50 lines of cache logic
  }
}
```

**Status:** ⚠️ Scope creep - discuss before merging
```

#### 类别 3：理解偏差

**检查对需求的误解。**

| 问题 | 如何验证 |
|------|----------|
| 对需求有不同的理解？ | 要求作者解释其理解 |
| 未澄清的假设？ | 查找"假设..."等注释 |
| 模糊规范是否被错误解决？ | 与类似的现有功能比较 |

```markdown
## Example Review Finding

**Interpretation Gap:** "Sort by date" implemented as ascending

**Requirement stated:** "Sort by date" (ambiguous)

**Author implemented:** Oldest first (ascending)

**Expected:** Most recent first is typical UX pattern

**Status:** ❓ Clarify - which sort order was intended?
```

---

## 为什么顺序很重要

### 阶段 1 必须先进行

| 场景 | 错误顺序造成的浪费 |
|------|---------------------|
| 跳过阶段 1 | 审查 500 行代码质量，然后发现构建了错误的功能 |
| 先做阶段 2 | 建议重构，然后意识到代码不应该存在 |
| 混合进行 | 混淆关注点，遗漏系统性问题 |

### 关注点分离

- **阶段 1（规范）：** 它做了正确的事吗？
- **阶段 2（质量）：** 它做对了吗？

如果代码没有实现正确的功能，代码质量审查就没有意义。

---

## 规范合规性检查清单

### 开始之前

- [ ] 完整阅读原始 Issue/工单
- [ ] 识别所有明确需求
- [ ] 从上下文中识别隐含需求
- [ ] 记录任何列出的验收标准

### 审查期间

**缺失需求：**
- [ ] 所有需求的功能都存在
- [ ] 边界情况已覆盖（空、null、最大值）
- [ ] 错误处理符合规范
- [ ] 正常路径完全可用
- [ ] UI 符合原型/规范（如果提供）

**不必要的添加：**
- [ ] 没有未请求的功能
- [ ] 没有推测性抽象
- [ ] 没有过早优化
- [ ] 范围完全匹配需求

**理解偏差：**
- [ ] 作者的理解与规范匹配
- [ ] 歧义已正确解决
- [ ] 假设已文档化且有效
- [ ] 行为与类似的现有功能匹配

### 审查之后

- [ ] 用文件:行号引用记录所有发现
- [ ] 分类为缺失/不必要/理解偏差
- [ ] 优先级排列：阻塞 vs 非阻塞问题

---

## 输出格式

### 合规结果

```markdown
## Spec Compliance Review: ✅ PASS

All requirements verified:
- ✅ User can upload profile image (req #1)
- ✅ Image resized to 200x200 (req #2)
- ✅ Invalid formats rejected with error message (req #3)
- ✅ Progress indicator during upload (req #4)

**Proceed to:** Code Quality Review
```

### 发现问题

```markdown
## Spec Compliance Review: ❌ ISSUES FOUND

### Missing Requirements

1. **Progress indicator not implemented** (req #4)
   - File: `ProfileUpload.tsx`
   - Expected: Progress bar during upload
   - Found: No progress indication

2. **Error messages not user-friendly** (req #3)
   - File: `ProfileUpload.tsx:45`
   - Expected: "Please upload a JPG or PNG file"
   - Found: "Error: INVALID_FORMAT"

### Unnecessary Additions

1. **Image cropping feature not requested**
   - File: `ImageCropper.tsx` (new file, 150 lines)
   - Impact: Adds complexity, delays delivery
   - Recommendation: Remove or create separate PR

**Action Required:** Address missing requirements before code quality review
```

---

## 常见错误

| 错误 | 为什么是错的 |
|------|-------------|
| 在规范合规性之前审查代码风格 | 如果构建了错误的东西，努力就白费了 |
| 假设遵循了规范 | 独立验证 |
| 跳过边界情况 | Bug 藏在边界中 |
| 接受"以后再加" | 技术债务会累积 |
| 遗漏范围蔓延 | 未审查的代码进入代码库 |

---

*内容改编自 [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent (@obra)，MIT License。*
