# 红队对抗

通过对抗性思维和红队方法，在敌人之前发现弱点。

## 核心原则

红队方法问：**"如果有人想要破坏、利用或操纵这个，他们会怎么做？"** The Fool 采用对手的心态——不是为了造成伤害，而是在真正的对手之前发现漏洞。这适用于安全之外：竞争对手、不满的用户、反向激励和监管挑战都是对抗性力量。

## 流程

1. **识别资产** — 你在保护什么？（系统、决策、策略、产品）
2. **构建对手画像** — 谁会攻击这个以及为什么？
3. **映射攻击向量** — 每个画像如何利用弱点？
4. **评估影响** — 按可能性×影响排序
5. **设计防御** — 为排名最高的向量制定具体对策

## 对手画像构建

通用的"攻击者"产生通用的发现。具体的画像产生可行的洞察。

### 画像模板

| 字段 | 描述 |
|-------|-------------|
| **角色** | 这个对手是谁？ |
| **动机** | 为什么他们会攻击？ |
| **能力** | 他们有什么资源和技能？ |
| **访问权限** | 他们已经拥有什么访问权限？ |
| **限制** | 什么限制了他们？ |

### 常见对手画像

| 画像 | 动机 | 典型向量 |
|---------|-----------|----------------|
| **外部攻击者** | 财务收益，数据盗窃 | API利用，凭证填充，注入攻击 |
| **竞争对手** | 市场优势 | 功能复制，人才挖角，FUD营销 |
| **不满的内部人员** | 报复，财务收益 | 权限提升，数据泄露，破坏 |
| **粗心用户** | 无（意外） | 错误配置，弱密码，共享凭证 |
| **监管者** | 合规执行 | 审计结果，数据处理违规，可访问性差距 |
| **机会主义玩家** | 个人利益 | 利用业务逻辑中的漏洞，推荐欺诈 |
| **活动家** | 意识形态目标 | 公开羞辱，数据泄露，服务中断 |

### 领域特定画像

| 领域 | 关键对手 | 关注点 |
|--------|--------------|-------|
| 电商 | 欺诈者 | 支付绕过，优惠券滥用，虚假退货 |
| SaaS | 免费套餐滥用者 | 速率限制绕过，多账号，资源囤积 |
| 市场平台 | 不良意图卖家 | 虚假列表，评论操纵，托管博弈 |
| API平台 | 抓取者 | 速率限制绕过，数据收集，反向工程 |
| 社交平台 | 喷子/机器人农场 | 垃圾邮件，操纵，虚假参与度 |

## 攻击向量识别

### 按类别

| 类别 | 向量 | 示例 |
|----------|---------|---------|
| **技术** | 注入，认证绕过，竞争条件，SSRF | 搜索参数中的SQL注入 |
| **业务逻辑** | 工作流绕过，状态操纵，价格篡改 | 通过API重放使用过期优惠券 |
| **社会工程** | 钓鱼，欺骗，权威利用 | "我是CEO，我现在需要访问权限" |
| **运营** | 供应链，依赖投毒，内部威胁 | 构建管道中被破坏的npm包 |
| **信息** | 数据泄露，元数据暴露，时序攻击 | 通过登录错误消息枚举用户 |
| **经济** | 资源耗尽，拒绝钱包，非对称成本 | Lambda调用洪流导致5万美元账单 |

### 攻击树构建

对于复杂系统，构建攻击树来映射通往目标的路径。

```
Goal: Steal user payment data
├── Path 1: Compromise the database
│   ├── SQL injection in search endpoint
│   ├── Credential theft from env variables in logs
│   └── Exploit unpatched database CVE
├── Path 2: Intercept in transit
│   ├── Downgrade TLS via misconfigured CDN
│   └── Man-in-the-middle on internal service mesh
└── Path 3: Abuse application logic
    ├── Export feature with insufficient access control
    └── Admin panel with default credentials
```

## 反向激励检测

系统创造激励。有时这些激励奖励错误的行为。

### 揭示反向激励的问题

| 问题 | 揭示的内容 |
|----------|----------------|
| "人们会如何钻这个空子？" | 业务逻辑中的漏洞 |
| "这奖励了我们不想要的行为？" | 激励不一致 |
| "以最少努力获得奖励的最便宜方式是什么？" | 短路利用 |
| "如果我们测量X，什么Y会被牺牲？" | 古德哈特定律在起作用 |
| "谁从这次失败中受益？" | 有动机的对手 |

### 常见反向激励模式

| 模式 | 示例 | 后果 |
|---------|---------|-------------|
| 指标游戏 | "代码行数"作为生产力指标 | 冗长、不可维护的代码 |
| 奖励黑客 | 无验证的推荐奖励 | 用于自推荐的虚假账号 |
| 恶性竞争 | "最快响应时间"作为SLA | 团队避免处理复杂工单 |
| 眼镜蛇效应 | 报告bug的赏金 | 团队引入bug来申领赏金 |
| 信息不对称 | 用户比系统知道更多 | 市场定价中的逆向选择 |

## 竞争响应分析

当"对手"是竞争对手时。

| 场景 | 分析框架 |
|----------|-------------------|
| 功能持平 | 他们能复制什么？多快？我们可防御的护城河是什么？ |
| 价格战 | 他们能维持更低的价格？他们的成本结构是什么？ |
| 人才挖角 | 哪些角色是关键？多可替代？我们的保留优势是什么？ |
| 平台风险 | 我们依赖他们的平台吗？切换成本是多少？ |
| FUD营销 | 他们能提出什么说法？哪些最难反驳？ |

## 输出模板

```markdown
## Red Team Analysis: [Target]

### Asset Under Assessment

[What we're protecting and why it matters]

### Adversary Profiles

#### Adversary 1: [Name/Role]
- **Motivation:** [Why they attack]
- **Capability:** [What they can do]
- **Access:** [What they start with]

#### Adversary 2: [Name/Role]
- **Motivation:** [Why they attack]
- **Capability:** [What they can do]
- **Access:** [What they start with]

### Attack Vectors (Ranked)

| # | Vector | Adversary | Likelihood | Impact | Risk Score |
|---|--------|-----------|-----------|--------|------------|
| 1 | [Specific attack] | [Who] | High/Med/Low | High/Med/Low | [L x I] |
| 2 | [Specific attack] | [Who] | High/Med/Low | High/Med/Low | [L x I] |
| 3 | [Specific attack] | [Who] | High/Med/Low | High/Med/Low | [L x I] |

### Perverse Incentives

| Incentive Created | Unintended Behavior | Severity |
|-------------------|-------------------|----------|
| [What the system rewards] | [How it gets gamed] | High/Med/Low |

### Recommended Defenses

| Attack Vector | Defense | Effort | Priority |
|--------------|---------|--------|----------|
| #1 | [Specific countermeasure] | Low/Med/High | Immediate/Next sprint/Backlog |
| #2 | [Specific countermeasure] | Low/Med/High | Immediate/Next sprint/Backlog |
| #3 | [Specific countermeasure] | Low/Med/High | Immediate/Next sprint/Backlog |
```