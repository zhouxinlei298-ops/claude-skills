# GCP 架构参考

Google Cloud Platform 服务、模式和架构框架的全面指南。

## Google Cloud 架构框架

### 五大支柱

1. **卓越运营**
   - 基础设施即代码（Deployment Manager、Terraform）
   - 使用 Cloud Build 的 CI/CD
   - 使用 Cloud Monitoring（Stackdriver）进行监控
   - SRE 原则和 SLO
   - 事故管理

2. **安全性、隐私和合规**
   - 身份和访问管理（Cloud IAM）
   - 用于数据边界的 VPC Service Controls
   - 容器的二进制授权
   - 数据加密（默认静态和传输中加密）
   - Security Command Center

3. **可靠性**
   - 多可用区和多区域部署
   - 负载均衡和自动扩展
   - 灾难恢复规划
   - 混沌工程实践
   - SLI、SLO 和错误预算

4. **成本优化**
   - 承诺使用折扣
   - 持续使用折扣（自动）
   - 可抢占 VM 和 Spot VM
   - 用于合理调整大小的 Recommender
   - 用于优化的 Active Assist

5. **性能优化**
   - Cloud CDN 和 Media CDN
   - 缓存策略（Memorystore）
   - 数据库性能调优
   - 网络优化（高级版 vs 标准版）
   - 区域和可用区资源放置

## 核心服务架构

### 计算

**Compute Engine**
- 机器类型：E2（成本优化）、N2（均衡）、C2（计算优化）、M2（内存优化）
- 特定需求的自定义机器类型
- 可抢占 VM（高达 80% 折扣，最长 24 小时）
- Spot VM（类似于可抢占，可用性更好）
- 实例组：托管（带自动扩展）、非托管
- 最佳实践：使用最新一代、承诺使用折扣、批处理作业使用 Spot

**Cloud Run**
- 完全托管的无服务器容器平台
- 自动扩展到零
- 按请求付费
- 仅在处理请求期间分配 CPU
- 最佳实践：无状态容器、优化冷启动、批处理使用 Cloud Run 作业

**Cloud Functions**
- 事件驱动的无服务器函数
- 第一代：HTTP 和后台函数
- 第二代：基于 Cloud Run，性能更好
- 事件源：Pub/Sub、Cloud Storage、Firestore、HTTP
- 最佳实践：使用第二代、最小化冷启动、实现重试逻辑

**Google Kubernetes Engine（GKE）**
- 与 GCP 集成的托管 Kubernetes
- Autopilot 模式：完全托管，按 Pod 定价
- 标准模式：更多控制，节点管理
- 用于安全服务访问的 Workload Identity
- 用于部署策略的二进制授权
- 最佳实践：简单使用 Autopilot、启用 Workload Identity、实施网络策略

**App Engine**
- 完全托管平台（PaaS）
- 标准环境（沙箱、自动扩展）
- 灵活环境（Docker 容器、自定义运行时）
- 用于金丝雀部署的流量拆分
- 最佳实践：Web 应用使用标准环境，自定义依赖使用灵活环境

### 存储

**Cloud Storage**
- 存储类别：Standard（标准）、Nearline（近线，30 天）、Coldline（冷线，90 天）、Archive（归档，365 天）
- 对象生命周期管理
- 对象版本控制和保留策略
- 自动类别转换的 Autoclass
- 用于数据传输的请求者付费
- 最佳实践：使用 Autoclass、启用版本控制、实施生命周期策略

**Persistent Disk**
- 类型：Standard（HDD）、Balanced SSD、SSD、Extreme
- 可用区和区域持久磁盘
- 用于备份的快照（增量）
- 无停机时间的磁盘调整大小
- 最佳实践：大多数工作负载使用 Balanced SSD、启用快照

**Filestore**
- 托管 NFS 文件存储
- 层级：Basic（1-63.9 TB）、Enterprise（1-10 TB，性能更好）
- 备份到 Cloud Storage
- 最佳实践：生产环境使用 Enterprise、实施备份

**Cloud Storage for Firebase**
- 用于移动端和 Web 应用的对象存储
- 用于直接上传/下载的客户端 SDK
- 用于访问控制的安全规则

### 数据库

**Cloud SQL**
- 托管的 MySQL、PostgreSQL、SQL Server
- 高可用性配置（区域）
- 用于扩展的只读副本
- 自动备份和时间点恢复
- 最佳实践：启用 HA、使用只读副本、使用 Cloud SQL Proxy 实施连接池

**Cloud Spanner**
- 全球分布式关系数据库
- 具有强一致性的水平扩展
- 99.999% 可用性的多区域
- 用于全局一致性的 TrueTime
- 最佳实践：设计适当的模式拆分、使用提交时间戳、优化热点

**Firestore（Native 模式）**
- NoSQL 文档数据库
- 实时同步
- 移动端离线支持
- ACID 事务
- 最佳实践：仔细设计文档结构、明智使用集合组查询

**Bigtable**
- NoSQL 宽列数据库
- 拍字节级单毫秒延迟
- HBase API 兼容
- 通过添加节点线性扩展
- 最佳实践：设计行键以避免热点、使用复制实现 HA

**Memorystore**
- 托管的 Redis 和 Memcached
- 标准层级（带副本的 HA）和基本层级
- 最佳实践：生产环境使用标准层级、实施连接池

**BigQuery**
- 无服务器数据仓库
- 拍字节级数据的 SQL 分析
- 面向列的存储
- 自动缓存和优化
- 最佳实践：对表进行分区和集群、使用近似函数、使用配额控制成本

### 网络

**VPC（虚拟私有云）**
- 全局资源（子网是区域性的）
- 自定义或自动模式网络
- 防火墙规则（有状态）
- VPC 对等互连和共享 VPC
- GCP 服务的专用 Google 访问
- 最佳实践：使用自定义模式 VPC、规划 IP 范围、实施防火墙规则

**Cloud Load Balancing**
- 全局负载均衡（HTTP(S)、TCP/SSL 代理、外部 TCP/UDP）
- 区域负载均衡（内部 HTTP(S)、内部 TCP/UDP）
- 用于全局分布的任播 IP
- 带有健康检查的后端服务
- 最佳实践：多区域使用全局、启用 CDN、配置健康检查

**Cloud CDN**
- 全球内容交付网络
- 缓存失效和签名 URL
- 与 Cloud Storage 和计算集成
- 最佳实践：启用压缩、使用 cache-control 头

**Cloud Interconnect 和 VPN**
- 专用 Interconnect（10 Gbps 或 100 Gbps）
- 合作伙伴 Interconnect（50 Mbps 到 50 Gbps）
- Cloud VPN（HA VPN，99.99% SLA）
- 最佳实践：冗余使用 HA VPN、高带宽使用专用 Interconnect

**Cloud Armor**
- DDoS 保护和 WAF
- 预配置和自定义规则
- 自适应保护（基于 ML）
- 最佳实践：为面向互联网的服务启用、使用预配置规则

**Private Service Connect**
- 与 Google API 和服务的专用连接
- 用于服务发现的 Service Directory
- 最佳实践：生产环境中所有托管服务都使用

### 无服务器和事件驱动

**Pub/Sub**
- 全局消息队列
- 至少一次传递
- 推送和拉取订阅
- 消息排序和过滤
- 死信主题
- 最佳实践：使用消息属性进行过滤、实现幂等处理

**Eventarc**
- 事件驱动架构
- Cloud Run、Workflows、GKE 的触发器
- 源：审计日志、Pub/Sub、自定义事件
- 最佳实践：用于解耦架构、实施事件过滤

**Cloud Scheduler**
- 完全托管的 cron 服务
- HTTP、Pub/Sub 和 App Engine 目标
- 最佳实践：用于定期任务、实施重试逻辑

**Workflows**
- 编排和自动化 GCP 和 HTTP 服务
- 基于 YAML 的工作流定义
- 内置错误处理和重试
- 最佳实践：用于复杂的多步骤流程、实施补偿事务

### 安全和身份

**Cloud IAM**
- 资源层次结构：组织 → 文件夹 → 项目 → 资源
- 角色：原始角色（所有者、编辑者、查看者）、预定义角色、自定义角色
- 应用程序的服务账户
- GKE 的 Workload Identity
- 最佳实践：使用预定义角色、最小权限、应用使用服务账户

**Cloud Key Management（KMS）**
- 加密密钥管理
- 客户管理的加密密钥（CMEK）
- 由硬件安全模块（HSM）支持
- 自动密钥轮换
- 最佳实践：启用自动轮换、每个环境使用单独的密钥

**Secret Manager**
- 存储 API 密钥、密码、证书
- 版本控制和访问控制
- 自动轮换集成
- 最佳实践：定期轮换密钥、使用 IAM 进行访问控制

**Security Command Center**
- 集中式安全和风险管理
- 资产发现和漏洞扫描
- 威胁检测和合规监控
- 最佳实践：启用所有检测器、定期审查发现结果

**VPC Service Controls**
- 围绕 GCP 资源创建安全边界
- 防止数据外泄
- 最佳实践：用于敏感数据、实施访问级别

### AI 和机器学习

**Vertex AI**
- 统一的 ML 平台
- 用于自定义模型的 AutoML
- 预训练模型（Vision、Natural Language 等）
- 使用管道的 MLOps
- 最佳实践：快速开始使用 AutoML、实施特征存储

**BigQuery ML**
- 使用 SQL 创建和执行 ML 模型
- 模型类型：线性回归、逻辑回归、聚类等
- 与 Vertex AI 集成
- 最佳实践：用于简单模型、利用 BigQuery 的规模

## 架构模式

### 高可用性

**多可用区模式**
```
全局 HTTP(S) 负载均衡器
    |
    v
托管实例组（多可用区）
    |
    v
Cloud SQL（区域，HA 配置）
    |
    v
Cloud Storage（多区域）
```

**多区域模式**
```
全局 HTTP(S) 负载均衡器
    |
    ├── 后端服务区域 1（Cloud Run）
    └── 后端服务区域 2（Cloud Run）
         |
         v
    Cloud Spanner（多区域）
```

### 无服务器架构

**事件驱动模式**
```
Cloud Storage 上传事件
    |
    v
Pub/Sub 主题
    |
    v
Cloud Functions（图像处理）
    |
    v
Firestore（元数据存储）
```

**API 优先模式**
```
Cloud Endpoints 或 API Gateway
    |
    v
Cloud Run（多个服务）
    |
    ├── Cloud SQL（事务数据）
    └── Firestore（用户数据）
```

### GKE 上的微服务

**带服务网格的 GKE**
```
全局负载均衡器
    |
    v
GKE Ingress
    |
    v
Anthos Service Mesh（Istio）
    |
    v
微服务（Cloud Spanner、Firestore、Memorystore）
```

### 数据分析平台

```
数据源
    |
    v
Pub/Sub（流式）
    |
    v
Dataflow（Apache Beam）
    |
    v
BigQuery（数据仓库）
    |
    v
Looker 或 Data Studio（可视化）
```

**批处理**
```
Cloud Storage（原始数据）
    |
    v
Dataproc（Apache Spark）
    |
    v
BigQuery（分析）
```

## 落地区设计

### 资源层次结构

```
组织
├── 文件夹（按环境或团队）
│   ├── 生产文件夹
│   │   ├── 项目 A
│   │   └── 项目 B
│   ├── 暂存文件夹
│   └── 开发文件夹
└── 共享服务文件夹
    ├── 网络项目（共享 VPC 主机）
    ├── 安全项目（KMS、Secret Manager）
    └── 日志项目（集中式日志）
```

### 网络设计

**共享 VPC 模式**
```
主机项目（网络团队）
├── 共享 VPC
│   ├── 子网生产（区域 A）
│   ├── 子网暂存（区域 A）
│   └── 子网开发（区域 B）

服务项目（应用团队）
├── 生产项目（使用生产子网）
├── 暂存项目（使用暂存子网）
└── 开发项目（使用开发子网）
```

**带 VPN 的中心辐射拓扑**
```
本地网络
    |
    v
Cloud VPN / Interconnect
    |
    v
中心 VPC（共享服务）
    |
    ├── 辐射 VPC 1（生产工作负载）
    ├── 辐射 VPC 2（开发工作负载）
    └── 辐射 VPC 3（分析工作负载）
```

### 治理

**组织策略**
- 限制公共 IP 分配
- 强制实施统一存储桶级访问
- 限制 VM 外部 IP
- 定义允许的资源位置

**IAM 策略**
- 使用 Google Groups 进行角色分配
- 职责分离（网络管理员、安全管理员等）
- 每个应用程序的服务账户
- GKE 工作负载的 Workload Identity

**日志和监控**
```
所有项目
    |
    v
日志路由器
    |
    ├── Cloud Logging（默认接收器）
    ├── BigQuery（长期分析）
    ├── Cloud Storage（归档）
    └── Pub/Sub（实时处理）
```

## 迁移策略

### 迁移到虚拟机

**工具**
- 迁移到虚拟机（原为 Migrate for Compute Engine）
- 支持 VMware、AWS、Azure、物理服务器
- 无代理或基于代理的迁移
- 迁移批次和测试克隆

**流程**
1. 评估：适配评估和 TCO 分析
2. 规划：对 VM 分组，定义迁移批次
3. 部署：设置基础设施（VPC、防火墙规则）
4. 迁移：测试迁移、切换、验证
5. 优化：合理调整大小、承诺使用折扣

### 数据库迁移

**Database Migration Service**
- 最小停机时间的迁移
- 支持 MySQL、PostgreSQL、SQL Server、Oracle
- 连续复制以实现切换灵活性

**Transfer Appliance**
- 用于大数据传输的物理设备
- 高达 1 PB 容量
- 离线数据传输

## 成本优化

### 计算节省

**承诺使用折扣**
- 1 年或 3 年承诺
- VM 高达 57% 的节省
- 基于资源或基于支出

**持续使用折扣**
- 运行超过月度 25% 的 VM 的自动折扣
- 高达 30% 的节省
- 无需承诺

**可抢占和 Spot VM**
- 高达 80% 的折扣
- 可能被 GCP 终止
- 最适合批处理、容错工作负载

**Recommender**
- VM 合理调整大小建议
- 空闲资源识别
- 承诺使用折扣建议

### 存储节省

**Cloud Storage**
- 用于自动类别转换的 Autoclass
- 生命周期策略（删除或转换）
- Nearline（30+ 天）、Coldline（90+ 天）、Archive（365+ 天）
- 数据传输的请求者付费

**Persistent Disk**
- 删除孤立磁盘
- 尽可能使用 Balanced SSD 而不是 SSD
- 调整磁盘大小以匹配实际使用情况

### BigQuery 节省

**按需定价**
- 每处理 TB $5
- 使用分区和聚类
- 查询缓存免费重复查询

**统一费率定价**
- 重型用户的可预测成本
- 可用的自动扩展槽位
- 短期承诺的弹性槽位

**最佳实践**
- 使用近似聚合函数（APPROX_COUNT_DISTINCT）
- 避免 SELECT *，指定列
- 为常见查询使用物化视图
- 使用自定义配额设置成本控制

### 监控成本

**Cloud Billing**
- 预算和警报
- 按项目、服务、SKU 的成本明细
- 导出到 BigQuery 进行分析
- 来自 Active Assist 的建议

## 灾难恢复

### 备份策略

**VM 备份**
- 持久磁盘快照（增量）
- 机器镜像（包括元数据和配置）
- 跨区域快照复制
- 用于自动化的快照计划

**数据库备份**
- Cloud SQL：自动备份（7-365 天保留）
- Cloud Spanner：按需或计划备份
- Firestore：自动每日导出
- Bigtable：备份到 Cloud Storage

### 高可用性

**RTO/RPO 矩阵**

| 模式 | RPO | RTO | 成本 |
|---------|-----|-----|------|
| 多区域主动-主动 | 秒 | 秒 | 高 |
| 带复制的主动-被动 | 分钟 | 分钟 | 中 |
| 热备 | 分钟 | 10-30 分钟 | 中 |
| 备份和恢复 | 小时 | 小时 | 低 |

**Cloud SQL HA**
- 带同步复制的区域配置
- 自动故障转移
- 99.95% SLA（单可用区为 99.5%）

**Cloud Spanner**
- 多区域配置
- 99.999% 可用性 SLA
- 跨区域同步复制

### 灾难恢复测试

- 定期 DR 演练（建议每季度）
- 记录运维手册
- 测试恢复过程
- 衡量实际 RTO/RPO 与目标的差距

## 监控和可观察性

### Cloud Monitoring（原 Stackdriver）

**指标**
- 系统指标（CPU、内存、磁盘、网络）
- 通过 Cloud Monitoring API 的自定义指标
- 用于多项目监控的指标范围
- 用于可用性的正常运行时间检查

**仪表板和图表**
- GCP 服务的预定义仪表板
- 带有过滤和分组的自定义仪表板
- 带有错误预算的 SLO 监控

### Cloud Logging

**日志类型**
- 管理活动日志（始终启用，不收费）
- 数据访问日志（必须启用）
- 系统事件日志
- 访问透明度日志（用于 Google 访问）

**日志接收器**
- 将日志路由到 BigQuery、Cloud Storage、Pub/Sub
- 组织/文件夹级别的聚合接收器
- 排除过滤器以降低成本

### Cloud Trace

**分布式跟踪**
- App Engine、Cloud Run、GKE 的自动检测
- 使用客户端库的手动检测
- 延迟分析和性能洞察
- 与 Zipkin 集成

### Cloud Profiler

**持续分析**
- CPU 和内存分析
- 低开销（< 0.5% CPU）
- 用于可视化的火焰图
- 支持的语言：Java、Go、Python、Node.js

### Error Reporting

**聚合错误跟踪**
- 自动错误分组
- 堆栈跟踪分析
- 与 Cloud Logging 集成
- 新错误的通知
