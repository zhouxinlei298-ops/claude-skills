# AWS 架构参考

AWS 服务、模式和 Well-Architected 框架实施的全面指南。

## Well-Architected 框架

### 六大支柱

1. **卓越运营**
   - 基础设施即代码（CloudFormation、CDK、Terraform）
   - 持续集成/部署
   - 可观察性（CloudWatch、X-Ray）
   - 运行手册和操作手册
   - 故障演练和故障注入

2. **安全性**
   - 身份和访问管理（IAM）
   - 检测控制（GuardDuty、Security Hub）
   - 基础设施保护（VPC、安全组、NACL）
   - 数据保护（KMS、静态/传输中加密）
   - 事件响应自动化

3. **可靠性**
   - 多可用区部署
   - 自动扩展组
   - Route 53 健康检查和故障转移
   - 备份和恢复（AWS Backup）
   - 混沌工程（AWS FIS）

4. **性能效率**
   - 使用 Compute Optimizer 进行合理调整大小
   - 缓存策略（CloudFront、ElastiCache）
   - 数据库优化（RDS Performance Insights）
   - 无服务器架构
   - 全球内容交付

5. **成本优化**
   - 预留实例和节省计划
   - 容错工作负载的 Spot 实例
   - S3 智能分层和生命周期策略
   - 合理调整大小建议
   - 成本分配标签和预算

6. **可持续性**
   - 选择使用可再生能源的区域
   - 无服务器以最小化空闲资源
   - 高效的数据存储模式
   - 资源利用率优化

## 核心服务架构

### 计算

**EC2（弹性计算云）**
- 实例类型：通用（t3、m5）、计算优化（c5）、内存优化（r5）、GPU（p3、g4）
- 自动扩展：目标跟踪、分步扩展、定时扩展
- 放置组：集群、分区、分散
- 最佳实践：使用最新代、合理调整大小、启用详细监控

**Lambda**
- 调用模型：同步、异步、事件源映射
- 并发：预留、已预置、突发限制
- 用于共享依赖的层
- 最佳实践：保持函数小型化、使用环境变量、设置超时

**ECS/EKS（容器服务）**
- ECS：Fargate 用于无服务器，EC2 用于控制
- EKS：具有 AWS 集成的托管 Kubernetes
- 服务网格：App Mesh 用于可观察性
- 最佳实践：使用 Fargate 简化操作，使用 EKS 获得可移植性

**Elastic Beanstalk**
- Web 应用的托管平台
- 包含自动扩展和负载均衡
- 支持多种语言和 Docker

### 存储

**S3（简单存储服务）**
- 存储类别：标准、IA、One Zone-IA、Glacier、深度归档
- 自动分层的生命周期策略
- 版本控制和 MFA 删除保护
- 跨区域复制用于 DR
- 最佳实践：启用版本控制、使用生命周期策略、阻止公共访问

**EBS（弹性块存储）**
- 卷类型：gp3（通用）、io2（IOPS）、st1（吞吐量）、sc1（冷）
- 快照到 S3 用于备份
- 默认加密
- 最佳实践：对大多数工作负载使用 gp3、启用加密

**EFS（弹性文件系统）**
- 用于共享访问的 NFSv4 文件系统
- 性能模式：通用、最大 I/O
- 吞吐量模式：突发、已预置
- 最佳实践：使用生命周期管理、启用加密

**FSx**
- FSx for Windows File Server（SMB）
- FSx for Lustre（HPC 工作负载）
- FSx for NetApp ONTAP
- FSx for OpenZFS

### 数据库

**RDS（关系型数据库服务）**
- 引擎：MySQL、PostgreSQL、MariaDB、Oracle、SQL Server、Aurora
- 多可用区实现高可用性
- 只读副本用于可扩展性
- 自动备份和时间点恢复
- 最佳实践：使用 Aurora 获得性能、启用多可用区、使用只读副本

**Aurora**
- MySQL 和 PostgreSQL 兼容
- 5x MySQL 性能、3x PostgreSQL 性能
- 全球数据库用于跨区域 DR
- Serverless v2 用于可变工作负载
- 最佳实践：对不可预测的工作负载使用 Aurora Serverless

**DynamoDB**
- NoSQL 键值和文档数据库
- 按需或已预置容量
- 用于多区域复制的全局表
- 用于变更数据捕获的 DynamoDB Streams
- 最佳实践：对不可预测的流量使用按需模式、谨慎实现 GSI

**ElastiCache**
- Redis 或 Memcached 内存缓存
- 用于 Redis 可扩展性的集群模式
- 最佳实践：用于会话存储、API 缓存

### 网络

**VPC（虚拟私有云）**
- CIDR 规划：避免重叠、为增长做计划
- 子网：公有（IGW）、私有（NAT）、隔离（无互联网）
- 路由表和路由决策
- 安全组（有状态）和 NACL（无状态）
- 最佳实践：VPC 使用 /16、子网使用 /24、规划 IP 空间

**Route 53**
- 带有健康检查的 DNS 服务
- 路由策略：简单、加权、延迟、故障转移、地理位置
- 最佳实践：使用别名记录、启用 DNSSEC

**CloudFront**
- 具有边缘位置的全球 CDN
- 源类型：S3、ALB、自定义源
- Lambda@Edge 用于请求/响应操作
- 最佳实践：启用压缩、使用字段级加密

**VPN 和 Direct Connect**
- 用于加密隧道的站点到站点 VPN
- 用于专用带宽的 Direct Connect
- 用于中心辐射拓扑的 Transit Gateway
- 最佳实践：对高带宽使用 Direct Connect、对复杂路由使用 Transit Gateway

**API Gateway**
- REST API、HTTP API、WebSocket API
- 节流和配额
- 与 Lambda、HTTP 端点、AWS 服务的集成
- 最佳实践：使用 HTTP API 降低成本、实现缓存

### 安全性

**IAM（身份和访问管理）**
- 最小权限原则
- 应用程序使用角色，不使用访问密钥
- 特权用户的 MFA
- 用于组织范围控制的 Service Control Policies（SCP）
- 最佳实践：使用角色、启用 MFA、轮换凭证

**KMS（密钥管理服务）**
- 客户托管密钥（CMK）
- 自动密钥轮换
- 信封加密模式
- 最佳实践：启用自动轮换、使用授权进行临时访问

**Secrets Manager**
- RDS 凭证的自动轮换
- 版本控制和回滚
- 最佳实践：定期轮换密钥、使用 VPC 端点

**Security Hub**
- 集中式安全发现
- CIS AWS 基础基准
- 与 GuardDuty、Inspector、Macie 集成

**GuardDuty**
- 使用 ML 进行威胁检测
- 监控 CloudTrail、VPC Flow Logs、DNS 日志

## 架构模式

### 高可用性

**多可用区模式**
```
- 跨 3 个可用区的应用负载均衡器
- 每个可用区中实例的自动扩展组
- 数据库的多可用区 RDS
- S3 用于静态资产（11 个 9 的持久性）
```

**多区域模式**
```
- 带有健康检查和故障转移的 Route 53
- CloudFront 用于全球分发
- Aurora 全球数据库实现 <1s RPO
- S3 跨区域复制
```

### 无服务器架构

**API 驱动模式**
```
API Gateway -> Lambda -> DynamoDB
              |
              v
          EventBridge -> Lambda（异步处理）
```

**事件驱动模式**
```
S3 Event -> Lambda -> Process -> SNS
                            |
                            v
                        多个订阅者
```

### AWS 上的微服务

**基于容器**
```
ALB -> ECS Fargate（多个服务）
    |
    v
Service Discovery（Cloud Map）
    |
    v
RDS/DynamoDB 每个服务
```

**服务网格**
```
App Mesh 用于流量管理
X-Ray 用于分布式追踪
CloudWatch Container Insights
```

### 数据湖架构

```
数据源 -> Kinesis Data Streams
                      |
                      v
              Kinesis Firehose
                      |
                      v
                S3（原始存储桶）
                      |
                      v
        Glue ETL 或 Lambda 处理
                      |
                      v
            S3（处理后存储桶）
                      |
                      v
          Athena/Redshift Spectrum
                      |
                      v
              QuickSight 仪表板
```

## 迁移策略（6R）

1. **重新托管（直接迁移）**
   - AWS 应用迁移服务（MGN）
   - 最小更改、快速迁移
   - 用于具有合规约束的遗留应用

2. **重新平台（平台迁移）**
   - 迁移到 RDS 而不是自托管数据库
   - 使用 Elastic Beanstalk 代替自定义应用服务器
   - 迁移期间的少量优化

3. **重新购买（放弃并购买）**
   - 迁移到 SaaS（如 Salesforce、Workday）
   - 减少维护负担

4. **重构/重新架构**
   - 现代化到无服务器或容器
   - 最高工作量、最高收益
   - 用于竞争优势应用

5. **停用**
   - 停用未使用的应用程序
   - 减少攻击面和成本

6. **保留**
   - 暂时保留在本地
   - 稍后迁移或出于监管原因保留

## 落地区设计

**AWS Control Tower**
- 多账户策略（AWS Organizations）
- 用于标准化的账户工厂
- 治理护栏（SCP）
- 集中式日志记录（CloudTrail、Config）

**账户结构**
```
Root
├── Security OU
│   ├── Log Archive Account
│   └── Security Tooling Account
├── Infrastructure OU
│   ├── Network Account（Transit Gateway、VPN）
│   └── Shared Services Account
└── Workloads OU
    ├── Production Account
    ├── Staging Account
    └── Development Account
```

**网络设计**
```
Transit Gateway（中心）
    |
    ├── Production VPC
    ├── Staging VPC
    ├── Development VPC
    └── On-premises（Direct Connect/VPN）
```

## 成本优化策略

**计算节省**
- Compute Savings Plans（高达 66% 节省）
- EC2 预留实例（1 年或 3 年）
- 用于批处理/容错工作负载的 Spot 实例
- Lambda：尽可能减少内存、使用预留并发

**存储节省**
- S3 智能分层用于不可预测的访问
- 到 Glacier/深度归档的生命周期策略
- 使用 EBS gp3 代替 gp2（便宜 20%、更好的性能）
- 删除未使用的快照和卷

**数据库节省**
- Aurora Serverless v2 用于可变工作负载
- RDS 预留实例
- 用于不可预测工作负载的 DynamoDB 按需模式
- 在同一区域使用只读副本以减少跨可用区数据传输

**监控和警报**
- AWS Cost Explorer 进行分析
- AWS Budgets 用于警报
- 成本异常检测
- 用于建议的 Trusted Advisor

## 灾难恢复

**RPO 和 RTO 目标**
- 备份和恢复：小时级 RPO/RTO（最低成本）
- 导航灯：分钟级 RPO、小时级 RTO
- 热待机：秒级 RPO、分钟级 RTO
- 多站点主动/主动：近零 RPO/RTO（最高成本）

**实施**
- 用于集中化备份管理的 AWS Backup
- 用于跨区域复制的 Aurora 全球数据库
- S3 跨区域复制
- Route 53 健康检查和故障转移路由
- 使用 CloudFormation/Terraform 定期进行 DR 测试

## 监控和可观察性

**CloudWatch**
- 指标：标准（5 分钟）和详细（1 分钟）
- 带有 SNS 通知的警报
- 用于日志分析的日志洞察
- 用于可视化的仪表板

**X-Ray**
- 用于微服务的分布式追踪
- 服务图可视化
- 追踪注释和元数据

**AWS Config**
- 资源清单和更改跟踪
- 合规规则评估
- 资源之间的关系跟踪
