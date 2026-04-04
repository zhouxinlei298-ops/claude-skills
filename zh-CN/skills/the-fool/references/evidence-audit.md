# 证据审计

通过证伪主义和证据质量评估，审计主张是否真正得到了证据支持。

## 核心原则

卡尔·波普的关键见解：只有能指出什么可以证伪一个主张时，该主张才有意义。证据审计模式从提案中提取主张、设计证伪标准、评估证据质量，并展示竞争性解释。目标不是为了证伪——而是为了确定证据是否真正支持结论。

## 流程

1. **提取主张** — 识别正在做出的具体主张
2. **设计证伪标准** — 对每个主张，指出什么可以证伪它
3. **评估证据质量** — 评估支持每个主张的证据
4. **识别认知偏见** — 检查推理中的系统性错误
5. **展示竞争性解释** — 寻找相同证据的替代解释

## 主张提取

提案包含主张——通常是隐含的。在评估之前先提取它们。

### 主张类型

| 类型 | 示例 | 隐藏在 |
|------|---------|-----------|
| **因果性** | "X导致Y" | "我们的重构提升了性能" |
| **预测性** | "X会发生" | "用户会采用这个功能" |
| **比较性** | "X优于Y" | "React是我们更好的选择" |
| **存在性** | "X存在/不存在" | "没有能满足我们需求的替代方案" |
| **普遍性** | "X总是为真" | "微服务总是提升团队速度" |
| **量化性** | "X是N" | "这每季度将节省200小时" |

### 提取方法

对提案中的每句话：
1. 这是主张还是定义？
2. 如果是主张，是什么类型？
3. 引用了什么证据（或暗示了什么）？
4. 什么会让这个主张变为错误？

### 提取示例

```
Statement: "Based on our pilot, migrating to Kubernetes will reduce deployment time by 60%."

Claims extracted:
1. The pilot results are representative of production (Predictive)
2. Kubernetes is the cause of the deployment time reduction (Causal)
3. The 60% reduction will persist at scale (Quantitative)
```

## 证伪标准

对每个主张，设计一个可以证伪它的测试。

| 主张 | 证伪标准 | 测试方法 |
|-------|------------------------|------|
| "用户需要功能X" | 30天内少于10%的用户使用X | 功能标记，衡量采用率 |
| "这能扩展到10万用户" | 在5万用户时响应时间超过500ms | 在目标规模下进行负载测试 |
| "迁移需要3个月" | 第1个月发现超过2个未知未知数 | 在初始阶段跟踪意外数量 |
| "框架X更快" | 基准测试显示差异小于5% | 在代表性的工作负载上进行受控基准测试 |
| "这将降低成本" | 12个月内总拥有成本超过当前成本 | 包括迁移、培训、运营的TCO分析 |

### 不可证伪的主张（警告信号）

有些主张无法被证伪。这些是警告信号。

| 模式 | 示例 | 问题 |
|---------|---------|---------|
| 模糊的结果 | "这将改善事情" | 没有可衡量的标准 |
| 移动目标 | "最终会起作用" | 没有时间边界 |
| 循环推理 | "这是最好的，因为专家都推荐" | 证据只是主张的重述 |
| 不可证伪的推诿 | "在某些情况下可能会有帮助" | 根据定义就是真的 |

当遇到不可证伪的主张时，问："什么是具体的、可衡量的结果，能告诉我们这行不通？"

## 证据质量评估

并非所有证据都平等。从以下维度评估每条证据。

### 证据质量矩阵

| 维度 | 强 | 弱 |
|-----------|--------|------|
| **样本量** | 大、有代表性的样本 | 单个案例、轶事 |
| **时效性** | 当前数据（12个月内） | 过时（2年以上） |
| **相关性** | 同一领域、同一规模 | 不同领域或规模 |
| **独立性** | 多个独立来源 | 单一来源或供应商提供 |
| **方法论** | 受控的、可重复的 | 临时的、不可重复的 |
| **具体性** | 精确的指标和条件 | 模糊或定性的 |

### 证据评级标准

| 等级 | 描述 | 可靠性 |
|-------|-------------|------------|
| **A** | 受控实验、大样本、可重复 | 高置信度 |
| **B** | 观测数据、合理样本、与其他证据一致 | 中等置信度 |
| **C** | 案例研究、小样本或单一来源 | 低置信度——需要佐证 |
| **D** | 轶事、意见或供应商营销材料 | 不足——不能单独基于此做决策 |
| **F** | 没有引用证据 | 主张未得到支持 |

### 常见弱证据模式

| 模式 | 示例 | 为什么弱 |
|---------|---------|---------------|
| 幸存者偏见 | "使用X的公司都成功了" | 忽视了使用X但失败的公司 |
| 樱桃挑选指标 | "响应时间提升了40%" | 其他指标（错误率、吞吐量）可能恶化了 |
| 供应商基准测试 | "我们的工具快3倍" | 基准测试针对供应商的优势进行了优化 |
| 权威诉求 | "Google就是这么做的" | Google的约束不是你的约束 |
| 锚定效应 | "行业平均是X，我们是Y" | 平均值可能不是正确的基准 |

## 认知偏见意识

检查推理链中的这些偏见。

| 偏见 | 描述 | 检测信号 |
|------|-------------|-----------------|
| **确认偏见** | 寻找证实现有信念的证据 | 只引用积极证据；不考虑反证 |
| **幸存者偏见** | 关注成功，忽视失败 | "所有成功的公司都做X" |
| **锚定效应** | 过度依赖第一条信息 | 最初估计不变，尽管有新数据 |
| **沉没成本谬误** | 由于过去投资而继续 | "我们已经在这上花了6个月"作为理由 |
| **可得性启发** | 过度重视近期或生动的例子 | 基于一个难忘的事件做决定 |
| **从众效应** | "大家都在这么做" | 不评估适用性就跟随趋势 |
| **邓宁-克鲁格效应** | 在不熟悉的领域过度自信 | 对专业领域外的自信主张 |
| **现状偏见** | 尽管有变革证据仍偏爱现状 | "一直如此" |

## 竞争性解释（溯因推理）

对每个结论，问："还有什么可以解释这些证据？"

### 方法

1. 陈述证据
2. 陈述提出的解释
3. 生成2-3个替代解释
4. 比较解释能力

### 示例

```
Evidence: "Deployment failures dropped 50% after adopting tool X."

Proposed explanation: Tool X is better than the old tool.

Alternative explanations:
1. The team also started doing more code review in the same period
2. A particularly error-prone service was retired last month
3. The team gained experience that would have improved results with any tool
```

## 输出模板

```markdown
## Evidence Audit: [Proposal/Decision]

### Claims Extracted

| # | Claim | Type | Evidence Cited |
|---|-------|------|---------------|
| 1 | [Specific claim] | Causal/Predictive/etc. | [What evidence supports it] |
| 2 | [Specific claim] | Causal/Predictive/etc. | [What evidence supports it] |
| 3 | [Specific claim] | Causal/Predictive/etc. | [What evidence supports it] |

### Falsification Criteria

| Claim | What Would Disprove It | How to Test |
|-------|----------------------|-------------|
| #1 | [Specific criterion] | [Concrete test] |
| #2 | [Specific criterion] | [Concrete test] |

### Evidence Quality

| Claim | Evidence Grade | Key Weakness |
|-------|--------------|--------------|
| #1 | A/B/C/D/F | [Primary concern] |
| #2 | A/B/C/D/F | [Primary concern] |

### Bias Check

| Bias Detected | Where | Impact |
|--------------|-------|--------|
| [Bias name] | Claim #X | [How it affects the conclusion] |

### Competing Explanations

| Evidence | Proposed Explanation | Alternative Explanations |
|----------|---------------------|------------------------|
| [Data point] | [Original claim] | 1. [Alternative] 2. [Alternative] |

### Verdict

**Overall evidence strength:** Strong / Moderate / Weak / Insufficient

**Recommendations:**
1. [Specific action to strengthen the weakest claim]
2. [Specific action to test the riskiest assumption]
```