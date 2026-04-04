# 面试问题

## 产品经理视角问题

关注用户价值和业务目标。

| 领域 | 问题 |
|------|------|
| **问题** | 这解决了什么问题？谁会遇到这个问题？多久一次？ |
| **用户** | 目标用户是谁？他们的目标是什么？技术水平如何？ |
| **价值** | 用户如何受益？业务价值是什么？ROI？ |
| **范围** | 什么在范围内？明确什么在范围外？MVP vs 完整版本？ |
| **成功** | 如何衡量成功？关键指标？ |
| **优先级** | 这是必须具备、应该具备还是可有可无的功能？ |

### 示例 PM 问题

```markdown
For a "User Export" feature:
- Who needs to export data and why?
- What format do they need (CSV, JSON, Excel)?
- How much data? 100 rows or 1 million?
- Is this for compliance (GDPR) or convenience?
- How often will this be used?
- What's the deadline?
```

## 开发视角问题

关注技术可行性和边缘情况。

| 领域 | 问题 |
|------|------|
| **集成** | 这与哪些系统集成？API、数据库、服务？ |
| **安全** | 需要身份验证吗？数据敏感性（PII、PCI）？ |
| **性能** | 预期负载？响应时间要求？异步可以吗？ |
| **边缘情况** | 当 X 失败时会发生什么？空状态？限制？ |
| **数据** | 存储什么？保留期？备份需求？ |
| **依赖** | 外部服务？速率限制？成本？ |

### 示例 Dev 问题

```markdown
For a "User Export" feature:
- What fields to include? Are any sensitive (passwords, tokens)?
- Max export size? Need streaming or background job?
- Should include soft-deleted records?
- What happens if export fails midway?
- File retention - how long to keep generated files?
- Need progress indicator for large exports?
```

## 工具使用：AskUserQuestions

当问题的可能答案数量有限时使用 `AskUserQuestions`。当答案无边界时使用开放式追问。

### 何时使用结构化选项

| 问题模式 | 示例 | 选项样式 |
|---------|------|---------|
| 优先级/排名 | "这是必须具备还是可有可无？" | 单选：必须具备、应该具备、可有可无 |
| 格式选择 | "什么导出格式？" | 多选：CSV、JSON、Excel、PDF |
| 范围决策 | "MVP 还是完整版本？" | 单选：MVP、完整、分阶段 |
| 是/带细节的否定 | "需要身份验证？" | 单选：公开、认证、基于角色 |

### 何时使用开放式

- "用自己的话描述用户旅程"
- "这解决了什么问题？"
- "带我了解整个工作流程"

### 示例：结构化获取需求

对于"用户导出"功能，将相关的选择分组：

**问题 1**（标题："导出范围"）：
"用户应该能够导出哪些数据？"
选项："仅自己的数据"、"团队数据"、"组织范围"、"启用多选"

**问题 2**（标题："格式"）：
"应该支持哪些导出格式？"
选项："CSV"、"JSON"、"Excel (.xlsx)"、"PDF"、"启用多选"

**问题 3**（标题："优先级"）：
"这个功能有多关键？"
选项："必须具备（阻塞）"、"应该具备（重要）"、"可有可无（未来）"

---

## 面试流程

### 阶段 1：发现
使用开放式问题了解问题空间：
1. "用自己的话描述一下这个功能"
2. "我们在解决什么问题？"

然后使用 `AskUserQuestions` 来缩小范围：
- 目标用户（从识别的用户画像中单选）
- 使用频率（每日、每周、每月、很少）
- 优先级（必须具备、应该具备、可有可无）

### 阶段 2：细节
使用 `AskUserQuestions` 进行范围和约束决策：
- 范围：MVP vs 完整 vs 分阶段（单选）
- 关键能力（多选自发现的条目）

然后开放式："带我了解用户旅程"

### 阶段 3：边缘情况
使用 `AskUserQuestions` 进行技术权衡：
- 错误处理方法（重试、快速失败、队列、通知）
- 数据限制（多选阈值）

然后开放式："当 [X] 失败时会发生什么？"

### 阶段 4：验证
呈现需求摘要，然后使用 `AskUserQuestions`：
- "这捕捉了您的需求吗？"（是 / 需要更改 / 主要差距）
- 如需要按需确认优先级

## 多代理预发现

对于跨多个领域的功能，在开始面试之前启动 Task 子代理并使用相关技能。这提前加载技术上下文，使面试专注于决策而不是探索。

### 模式：并行技能触发的发现

```
User request: "I need a feature that does X"

Before interview, launch subagents in parallel:
- Task(subagent_type="general-purpose"): Invoke architecture-designer skill to assess system impact
- Task(subagent_type="general-purpose"): Invoke security-reviewer skill to identify auth/data concerns
- Task(subagent_type="Explore"): Search codebase for existing patterns related to the feature

Collect subagent findings → Use them to inform interview questions
```

这确保 Feature Forge 面试从具体的技术上下文开始，而不是假设。

---

## 快速参考

| 阶段 | 焦点 | 工具 |
|------|------|------|
| 预发现 | 技术上下文 | Task 子代理使用技能 |
| 发现 | 问题、用户、价值 | 开放式 → AskUserQuestions |
| 细节 | 旅程、范围、约束 | AskUserQuestions → 开放式 |
| 边缘情况 | 失败、限制、安全 | AskUserQuestions → 开放式 |
| 验证 | 摘要、差距 | AskUserQuestions |