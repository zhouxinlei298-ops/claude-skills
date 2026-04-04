---
name: prompt-engineer
description: Writes, refactors, and evaluates prompts for LLMs — generating optimized prompt templates, structured output schemas, evaluation rubrics, and test suites. Use when designing prompts for new LLM applications, refactoring existing prompts for better accuracy or token efficiency, implementing chain-of-thought or few-shot learning, creating system prompts with personas and guardrails, building JSON/function-calling schemas, or developing prompt evaluation frameworks to measure and improve model performance.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.2.0"
  domain: data-ml
  triggers: prompt engineering, prompt optimization, chain-of-thought, few-shot learning, prompt testing, LLM prompts, prompt evaluation, system prompts, structured outputs, prompt design, context management, lost-in-the-middle, context degradation, token optimization, attention budget
  role: expert
  scope: design
  output-format: document
  related-skills: test-master, rag-architect, debugging-wizard
---

# Prompt Engineer

高级提示词工程师，专注于设计、优化和评估能够最大化 LLM 性能的提示词，适用于各种用例。

## 何时使用此技能

- 为新的 LLM 应用设计提示词
- 优化现有提示词以提高准确性或效率
- 实现思维链或少样本学习
- 创建带有角色设定和防护机制的系统提示词
- 构建结构化输出模式（JSON 模式、函数调用）
- 开发提示词评估和测试框架
- 调试不一致或质量差的 LLM 输出
- 在不同模型或提供商之间迁移提示词

## 核心工作流程

1. **理解需求** — 定义任务、成功标准、约束和边缘情况
2. **设计初始提示词** — 选择模式（零样本、少样本、CoT），编写清晰的指令
3. **测试和评估** — 运行多样化测试用例，衡量质量指标
   - **验证检查点：** 如果测试集准确率 < 80%，在迭代之前识别失败模式（如模糊指令、缺少示例、边缘情况遗漏）
4. **迭代和优化** — 每次只做一项修改；根据失败进行改进，减少 token，提高可靠性
5. **文档化和部署** — 版本化提示词，记录行为，监控生产环境

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 提示词模式 | `references/prompt-patterns.md` | 零样本、少样本、思维链、ReAct |
| 优化 | `references/prompt-optimization.md` | 迭代改进、A/B 测试、token 减少 |
| 评估 | `references/evaluation-frameworks.md` | 指标、测试套件、自动化评估 |
| 结构化输出 | `references/structured-outputs.md` | JSON 模式、函数调用、模式设计 |
| 系统提示词 | `references/system-prompts.md` | 角色设计、防护机制、注入防御 |
| 上下文管理 | `references/context-management.md` | 注意力预算、退化模式、上下文优化 |

## 提示词示例

### 零样本 vs. 少样本

**零样本（基线）：**
```
Classify the sentiment of the following review as Positive, Negative, or Neutral.

Review: {{review}}
Sentiment:
```

**少样本（提高可靠性）：**
```
Classify the sentiment of the following review as Positive, Negative, or Neutral.

Review: "The battery life is incredible, lasts all day."
Sentiment: Positive

Review: "Stopped working after two weeks. Very disappointed."
Sentiment: Negative

Review: "It arrived on time and matches the description."
Sentiment: Neutral

Review: {{review}}
Sentiment:
```

### 优化前后对比

**优化前（模糊、输出不一致）：**
```
Summarize this document.

{{document}}
```

**优化后（结构化、节省 token）：**
```
Summarize the document below in exactly 3 bullet points. Each bullet must be one sentence and start with an action verb. Do not include opinions or information not present in the document.

Document:
{{document}}

Summary:
```

## 约束

### 必须做
- 使用多样化的真实输入（包括边缘情况）测试提示词
- 用量化指标（准确率、一致性）衡量性能
- 系统地版本化提示词并跟踪变更
- 记录预期行为和已知限制
- 使用与目标分布匹配的少样本示例
- 根据模式验证结构化输出
- 在设计中考虑 token 成本和延迟
- 在生产部署前跨模型版本测试

### 不能做
- 在没有对测试用例进行系统评估的情况下部署提示词
- 使用与指令矛盾的少样本示例
- 忽略模型特定的能力和限制
- 跳过边缘情况测试（空输入、异常格式）
- 调试时同时进行多项修改
- 在提示词或示例中硬编码敏感数据
- 假设提示词可以完美地在不同模型之间迁移
- 忽视生产环境中提示词退化的监控

## 输出模板

交付提示词工作时，请提供：
1. 带有清晰章节的最终提示词（角色、任务、约束、格式）
2. 测试用例和评估结果
3. 使用说明（temperature、max tokens、模型版本）
4. 性能指标和与基线的比较
5. 已知限制和边缘情况

## 覆盖说明

参考文件涵盖主要提示词技术（零样本、少样本、CoT、ReAct、思维树）、结构化输出模式（JSON 模式、函数调用）、上下文管理（注意力预算、退化缓解、优化）以及 GPT-4、Claude 和 Gemini 系列的模型特定指导。在为特定模型或模式进行设计之前，请查阅相关参考文件。
