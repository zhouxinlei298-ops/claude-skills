# 事前分析

结合二阶思维的事前分析方法，在计划失败前识别如何失败。

## 核心原则

事前分析将问题反转。不要问"这会成功吗？"，而是问：**"现在是6个月后，这个计划已经失败了。为什么？"** 这种心理转变通过让失败成为起点，而不是需要反对的东西，来绕过乐观偏见。

## 流程

1. **设定场景** — "想象现在是[时间范围]之后。这个计划已经失败了。不是小挫折—而是明确的失败。"
2. **生成失败叙事** — 写具体的关于如何失败的故事
3. **按可能性和影响排序** — 并非所有失败都平等
4. **追踪后果链** → 第一阶 → 第二阶 → 第三阶效应
5. **识别早期警告信号** — 失败前你会看到什么？
6. **设计缓解措施** — 具体行动，而不是模糊的"小心"

## 失败叙事构建

失败叙事必须具体。"它无法扩展"不是叙事。"在5万并发用户时，数据库连接池耗尽，导致所有服务出现级联超时，这触发了断路器在高峰时段拒绝所有请求4分钟"才是叙事。

### 具体性检查清单

- [ ] 指定具体的触发器（不是"出问题了"）
- [ ] 包含数字或阈值
- [ ] 描述事件链，而不仅仅是最终状态
- [ ] 识别受影响的人或物
- [ ] 确实可能发生（不是幻想场景）

### 失败叙事模板

```markdown
**Failure: [Title]**

It's [timeframe] from now. [Specific trigger event]. This caused [first-order effect],
which led to [second-order effect]. The team discovered the problem when [detection point],
but by then [consequence]. The root cause was [underlying assumption that proved wrong].
```

### 示例

```markdown
**Failure: Migration Data Loss**

It's 3 months from now. During the database migration from PostgreSQL to the new schema,
a batch job silently drops records where the `legacy_id` field contains special characters
(~2% of records). The team discovers the problem 2 weeks post-migration when a customer
reports missing order history. By then, the legacy database has been decommissioned and
backups have rotated past the migration date. The root cause was that the migration script
was tested against a sanitized staging dataset that didn't include special characters.
```

## 二阶后果链

每个失败都有超出直接影响的后果。至少追踪两阶深度。

### 链条模板

```
Trigger: [event]
  → 1st order: [immediate effect]
    → 2nd order: [consequence of the 1st order effect]
      → 3rd order: [consequence of the 2nd order effect]
```

### 示例链条

```
Trigger: Key engineer leaves during migration
  → 1st order: Migration timeline slips 4 weeks
    → 2nd order: Overlap period with legacy system extends, doubling operational cost
      → 3rd order: Budget overrun triggers executive review, project gets descoped
```

### 常见二阶模式

| 第一阶 | 第二阶 | 第三阶 |
|------------|-------------|-------------|
| 功能发布延迟 | 销售错过季度目标 | 工程团队失去信任，受到更多监督 |
| 性能下降 | 用户采用变通方法 | 变通方法成为"需求"，限制未来设计 |
| 团队成员倦怠 | 知识集中在少数人 | 公交因子下降，风险增加 |
| 依赖项失效 | 紧急修复跳过测试 | 引入新bug，发布信心下降 |
| 数据质量问题 | 下游报告错误 | 基于错误数据做业务决策 |

## 反转技巧

问：**"什么会保证这必定失败？"** 然后检查是否存在这些条件。

### 保证失败的条件

| 类别 | 什么保证失败 |
|----------|----------------------|
| **人员** | 单点知识，利益相关者不认可，团队不相信方法 |
| **流程** | 没有回滚计划，没有增量验证，全有或全无的部署 |
| **技术** | 在目标规模未经测试，未记录的依赖项，版本锁定 |
| **时间线** | 没有未知缓冲，依赖没有SLA的外部团队，并行的关键路径 |
| **数据** | 无验证的迁移，没有数据质量检查，没有向后兼容的模式变更 |

## 领域特定的失败模式

### 技术失败

| 模式 | 触发器 | 典型后果 |
|---------|---------|-------------------|
| 集成悬崖 | 新服务连接到3个以上现有系统 | 一个集成阻塞所有其他 |
| 规模意外 | 负载超过测试10倍 | 依赖服务出现级联失败 |
| 迁移陷阱 | "只需移动数据" | 数据丢失，长时间停机，无法回滚 |
| 依赖腐化 | 锁定在废弃的库上 | 安全漏洞且无升级路径 |
| 配置漂移 | 手动环境设置 | "在我的机器上工作"变成"在任何环境都无法工作" |

### 业务失败

| 模式 | 触发器 | 典型后果 |
|---------|---------|-------------------|
| 采用悬崖 | 建好但没人来 | 沉没成本无收入影响 |
| 竞争对手抢占 | 竞争对手先推出类似功能 | 市场定位丢失，差异化被侵蚀 |
| 时间不匹配 | 开发期间市场转移 | 产品解决了昨天的问题 |
| 利益相关者反转 | 高管赞助者变更 | 项目失去优先级，资源重新分配 |
| 隐藏成本 | 运营负担低估 | 功能运行成本超过产生的价值 |

### 流程失败

| 模式 | 触发器 | 典型后果 |
|---------|---------|-------------------|
| 时间幻想 | 基于最佳情况估计 | 糟糕时期出现压缩、质量削减或范围削减 |
| 依赖链 | 团队A等团队B等团队C | 任何延迟在所有团队中级联 |
| 知识孤岛 | 专家离开或不可用 | 进度停止；新人员需要数周才能接手 |
| 范围蔓延 | "趁我们做这个..." | 原始目标被新增内容埋没 |
| 反馈真空 | 发布前无用户测试 | 做对了错误的产品 |

## 早期警告信号

| 警告信号 | 它表明什么 |
|-------------|-------------------|
| "我们稍后会处理这个"重复3次以上 | 关键决策被推迟，未解决 |
| 没人能解释回滚计划 | 回滚方案尚未设计 |
| 估计持续增长 | 隐藏的复杂性在逐步被发现 |
| 关键会议不断改期 | 利益相关者一致性比假设的弱 |
| "在我的机器上能工作" | 环境一致性比假设的差 |
| 测试阶段被压缩 | 质量将被牺牲 |
| 没有为成功定义指标 | 没人会知道这是否成功 |

## 输出模板

```markdown
## Pre-Mortem: [Plan/Decision Name]

**Timeframe:** [When would failure be evident]

### Failure Narratives

#### 1. [Failure Title] — Likelihood: High/Medium/Low | Impact: High/Medium/Low

[Specific failure narrative using the template above]

**Consequence chain:**
- 1st order: [immediate]
- 2nd order: [downstream]
- 3rd order: [systemic]

#### 2. [Failure Title] — Likelihood: High/Medium/Low | Impact: High/Medium/Low

[Narrative]

#### 3. [Failure Title] — Likelihood: High/Medium/Low | Impact: High/Medium/Low

[Narrative]

### Early Warning Signs

| Signal | Failure It Predicts | Check Frequency |
|--------|-------------------|-----------------|
| [Observable signal] | Failure #X | Weekly / Sprint / Monthly |

### Mitigations

| Failure | Mitigation | Effort | Reduces Risk By |
|---------|-----------|--------|-----------------|
| #1 | [Specific action] | Low/Med/High | [How much] |
| #2 | [Specific action] | Low/Med/High | [How much] |
| #3 | [Specific action] | Low/Med/High | [How much] |

### Inversion Check

**What would guarantee failure:** [List top 3 conditions]
**Do any exist now?** [Yes/No with specifics]
```