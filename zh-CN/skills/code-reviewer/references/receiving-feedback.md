# 接收反馈

---

## 核心心态

> "实施前先验证。不确定就询问。技术正确性优于社交舒适度。"

代码审查反馈是技术讨论，而非社交互动。关注代码，而非感受。

---

## 六步流程

### 步骤 1：完整阅读

**不要立即反应。** 在形成任何回应之前，完整阅读整条评论。

```markdown
❌ BAD: Read first sentence → start typing defense
✅ GOOD: Read entire comment → understand full context → then respond
```

### 步骤 2：重述要求

用你自己的话重新表述审查者的反馈，以确认理解。

```markdown
Reviewer: "This function is doing too much. It handles validation,
transformation, and persistence all in one place."

Your restatement: "You're suggesting I split this into three separate
functions: validate(), transform(), and persist()?"
```

### 步骤 3：对照代码库检查

在回应之前，根据实际代码条件验证反馈。

```typescript
// Reviewer says: "This will throw if user is null"

// Check the code:
function getUsername(user: User): string {
  return user.name;  // No null check - reviewer is correct
}

// Or discover context:
function getUsername(user: User): string {
  return user.name;  // TypeScript enforces User, null not possible
}
```

### 步骤 4：评估技术合理性

考虑反馈是否适用于你的特定技术和上下文。

```markdown
Reviewer: "You should use useMemo here for performance"

Evaluate:
- Is this component re-rendering frequently? → Check React DevTools
- Is the computation expensive? → Profile it
- Does React 19's compiler auto-optimize this? → Check version
```

### 步骤 5：有实质内容的回应

提供技术认可或合理的反对意见。

```markdown
✅ GOOD: "Fixed. Split into validate(), transform(), persist()
         at lines 24, 45, 67."

✅ GOOD: "Respectfully disagree. This list has max 5 items
         (see schema.ts:12), so filter performance is O(5)."

❌ BAD: "You're absolutely right! Great catch!"
❌ BAD: "I don't think that's necessary."
```

### 步骤 6：一次只处理一项

逐项验证每个反馈点。

```markdown
Feedback item 1: Add null check
→ Implement → Test → Commit → Verify → Move to next

Feedback item 2: Extract helper function
→ Implement → Test → Commit → Verify → Move to next

NOT: Try to address all feedback in one massive commit
```

---

## 避免表演性同意

### 问题所在

表演性同意浪费时间且不提供任何信息。当你写"很好的观点！"时，你添加的是噪音，而非信号。

### 禁用短语

| 短语 | 为什么错误 |
|------|------------|
| "你说得太对了！" | 拍马屁，不提供信息 |
| "很好的观点！" | 空洞的赞扬，不是回应 |
| "极好的反馈！" | 恭维，不参与讨论 |
| "感谢发现这个问题！" | 不必要，直接修复即可 |
| "我真的很感谢..." | 社交废话，非技术性 |

### 行动证明理解

```markdown
❌ "You're absolutely right! Great catch on that null check!
    Thanks so much for pointing this out!"

✅ "Fixed. Added null check at line 42."
```

代码变更表明你理解了。话语是多余的。

### 何时表达认可

学习新知识时，简洁的技术性认可：

```markdown
✅ "I wasn't aware of that edge case. Added handling at line 42."
✅ "Good point about thread safety. Added mutex at line 67."
```

---

## 何时反驳

### 合理反驳的情况

当反馈出现以下情况时，用技术性理由反驳：

| 情况 | 如何回应 |
|------|----------|
| 破坏现有功能 | "这个改动会破坏 X 功能（见 tests/feature-x.spec.ts:34 的测试）" |
| 缺乏完整的代码库上下文 | "这种模式的存在是因为 Y（见 architecture.md#constraints）" |
| 违反 YAGNI 原则 | "这种灵活性还不需要 - 只有一个调用者" |
| 技术上不正确 | "这实际上是可行的，因为 Z（链接到文档）" |
| 与既定架构冲突 | "这违背了我们的 JWT 方法（见 auth/README.md）" |

### 良好的反驳格式

```markdown
## Template
This conflicts with [X]. [Evidence]. Was that the intent, or should we [alternative]?

## Example
This conflicts with our JWT authentication architecture (see auth/token.js:45).
Switching to sessions would require restructuring the API middleware.
Was that the intent, or should we keep JWT?
```

### 不良反驳

```markdown
❌ "I don't think that's right."
❌ "That won't work."
❌ "We've always done it this way."
❌ "That's too much work."
```

---

## 声称已修复前的验证

### 检查清单

在写"已修复"或"完成"之前：

- [ ] 变更已实施
- [ ] 测试通过（完整套件，不只是修改的文件）
- [ ] 反馈中提到的特定行为已验证
- [ ] 边界情况已测试
- [ ] 没有引入意外的副作用

### 可接受的回应

```markdown
✅ "Fixed. Added null check. Tests pass."
✅ "Fixed at line 42. Verified with test case X."
✅ "Implemented. All 47 tests pass."
```

### 不可接受的回应

```markdown
❌ "I think this addresses your concern."
❌ "Should be fixed now."
❌ "Done, I believe."
❌ "Fixed (probably)."
```

### 无法验证时

如果你无法验证修复：

```markdown
✅ "Implemented the change, but I'm unable to verify because
    [specific reason]. Can you confirm on your end?"
```

---

## 快速参考

| 情况 | 回应 |
|------|------|
| 审查者正确 | "已修复。[你做了什么修改]。 |
| 需要澄清 | "确认一下：您是说 [重述]？" |
| 审查者不正确 | "这是可行的，因为 [证据]。[链接到证明]。 |
| 方法上有分歧 | "这与 [X] 冲突。我们应该 [替代方案]？" |
| 学到了新知识 | "我不知道 [X]。在第 [N] 行已修复。 |
| 无法验证 | "已实施。无法验证，因为 [原因]。 |

---

## 反模式

| 模式 | 问题 | 修复 |
|------|------|------|
| 辩解式回应 | 制造冲突，浪费时间 | 假设善意，技术性回应 |
| 道歉式回应 | 不专业，增加噪音 | 直接修复即可 |
| 延迟回应 | 阻碍审查循环 | 几小时内响应，不要几天 |
| 模糊回应 | 让审查者不确定 | 具体说明做了什么修改 |
| 忽略反馈 | 不尊重，制造摩擦 | 处理每个要点 |

---

*内容改编自 [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent (@obra), MIT License.*