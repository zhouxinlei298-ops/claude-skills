# 使用子代理进行预发现

对于跨越多个领域（身份验证、数据库、UI 等）的功能，在 Feature Forge 面试前需要预加载技术上下文。

## 概述

对于跨多个领域的功能，您可以在开始 Feature Forge 面试之前启动具有相关技能的 Task 子代理来加速发现。这预加载技术上下文，使面试专注于决策而不是探索。

## 何时使用

- 功能涉及 3+ 个不同的系统层（例如，身份验证、数据库、UI）
- 代码库不熟悉或文档不足
- 在提出需求问题之前需要具体的技术事实
- 利益相关者时间有限，希望减少来回沟通

## 何时不使用

- 功能很好地限制在单个领域内
- 您已经对代码库有深入了解
- 需求纯粹是业务/UX 方面的（不需要技术探索）

## 模式

```
1. Identify domains the feature touches
2. Launch parallel Task subagents with relevant skills:
   - Architecture Designer → existing patterns and constraints
   - Framework Expert → current implementation details
   - Security Reviewer → security requirements and risks
3. Collect findings from all subagents
4. Begin Feature Forge interview with technical context loaded
5. Focus interview on decisions, trade-offs, and requirements
```

## 示例

对于"带有头像上传的用户资料"功能：

```
Task subagent 1 (Architecture Designer):
  "Analyze the current user model, storage patterns, and image handling in this codebase"

Task subagent 2 (Security Reviewer):
  "What security concerns exist for file upload in this stack?"

Task subagent 3 (Framework Expert):
  "How does this project handle API endpoints and file storage?"
```

结果输入到 Feature Forge 面试中，因此像"我们应该在哪里存储头像？"这样的问题会带有现有模式的上下文。

## 与面试问题的集成

有关完整的多代理发现模式以及子代理发现如何映射到面试类别的信息，请参见 `interview-questions.md`。