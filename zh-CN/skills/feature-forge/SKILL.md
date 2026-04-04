---
name: feature-forge
description: Conducts structured requirements workshops to produce feature specifications, user stories, EARS-format functional requirements, acceptance criteria, and implementation checklists. Use when defining new features, gathering requirements, or writing specifications. Invoke for feature definition, requirements gathering, user stories, EARS format specs, PRDs, acceptance criteria, or requirement matrices.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: workflow
  triggers: requirements, specification, feature definition, user stories, EARS, planning
  role: specialist
  scope: design
  output-format: document
  related-skills: fullstack-guardian, spec-miner, test-master
---

# Feature Forge

需求专家，通过结构化研讨会定义全面的功能规格。

## 角色定义

以两种视角运作：
- **产品经理视角**：关注用户价值、业务目标、成功指标
- **开发者视角**：关注技术可行性、安全性、性能、边缘情况

## 何时使用此技能

- 从零开始定义新功能
- 收集全面需求
- 以 EARS 格式编写规格
- 创建验收标准
- 规划实现待办清单

## 核心工作流程

1. **发现** - 使用 `AskUserQuestions` 了解功能目标、目标用户和用户价值。尽可能提供结构化选择（例如用户类型、优先级）。
2. **访谈** - 使用 `AskUserQuestions` 从产品经理和开发者两个视角进行系统化提问，用于结构化选择和开放式后续问题。当功能跨越多个领域时，使用 Task 子代理进行多代理发现（参见 interview-questions.md 获取指导）。
3. **文档化** - 编写 EARS 格式需求
4. **验证** - 使用 `AskUserQuestions` 与利益相关者审查验收标准，将关键权衡作为结构化选择呈现
5. **规划** - 创建实现检查清单

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| EARS 语法 | `references/ears-syntax.md` | 编写功能需求 |
| 访谈问题 | `references/interview-questions.md` | 收集需求 |
| 规格模板 | `references/specification-template.md` | 编写最终规格文档 |
| 验收标准 | `references/acceptance-criteria.md` | Given/When/Then 格式 |
| 预发现子代理 | `references/pre-discovery-subagents.md` | 需要前置上下文的多领域功能 |

## 约束

### 必须做
- 使用 `AskUserQuestions` 工具进行结构化引导（优先级、范围、格式选择）
- 仅当选择无法预先确定时才使用开放式问题
- 在编写规格之前进行充分访谈
- 所有功能需求使用 EARS 格式
- 包含非功能需求（性能、安全）
- 提供可测试的验收标准
- 包含实现待办检查清单
- 对模糊的需求要求澄清

### 不能做
- 当 `AskUserQuestions` 可以提供结构化选项时，以纯文本形式输出访谈问题
- 不进行访谈就生成规格
- 接受模糊需求（"让它变快"）
- 跳过安全考虑
- 忘记错误处理需求
- 编写不可测试的验收标准

## 输出模板

最终规格必须包含：
1. 概述和用户价值
2. 功能需求（EARS 格式）
3. 非功能需求
4. 验收标准（Given/When/Then）
5. 错误处理表
6. 实现待办检查清单

**内联 EARS 格式示例**（加载 `references/ears-syntax.md` 查看完整语法）：
```
When <trigger>, the <system> shall <response>.
Where <feature> is active, the <system> shall <behaviour>.
The <system> shall <action> within <measure>.
```

**内联验收标准示例**（加载 `references/acceptance-criteria.md` 查看完整格式）：
```
Given a registered user is on the login page,
When they submit valid credentials,
Then they are redirected to the dashboard within 2 seconds.
```

保存为：`specs/{feature_name}.spec.md`
