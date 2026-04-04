# Azure 架构参考

Azure 服务、模式和云采用框架实施的全面指南。

## 云采用框架

### 框架阶段

1. **战略**
   - 定义业务理由
   - 预期业务成果
   - 业务案例开发
   - 首个项目优先级排序

2. **计划**
   - 数字资产评估
   - 初始组织对齐
   - 技能就绪计划
   - 云采用计划

3. **就绪**
   - Azure 落地区设置
   - Azure 设置指南
   - 迁移就绪
   - 最佳实践验证

4. **采用（迁移 + 创新）**
   - 迁移：评估、迁移、优化
   - 创新：构建云原生解决方案
   - 最佳实践和模式

5. **治理**
   - 治理方法论
   - 治理基准
   - 初始治理基础
   - 成熟治理演进

6. **管理**
   - 业务承诺
   - 运营基线
   - 平台和工作负载专业化

## Azure Well-Architected 框架

### 五大支柱

1. **成本优化**
   - Azure 成本管理和计费
   - 预留实例和节省计划
   - Azure 混合权益
   - 自动扩展和合理调整大小

2. **卓越运营**
   - 基础设施即代码（ARM、Bicep、Terraform）
   - Azure DevOps 和 GitHub Actions
   - Azure Monitor 和 Application Insights
   - 部署槽和蓝绿部署

3. **性能效率**
   - Azure CDN 和 Front Door
   - 自动扩展（VMSS、App Service）
   - 缓存（Redis、CDN）
   - 性能诊断

4. **可靠性**
   - 可用性集和区域
   - Azure Site Recovery
   - 负载均衡器和流量管理器
   - 备份和灾难恢复

5. **安全性**
   - Azure AD（Entra ID）
   - 网络安全组和防火墙
   - Azure Key Vault
   - Microsoft Defender for Cloud

## 核心服务架构

### 计算

**虚拟机**
- VM 大小：通用（D 系列）、计算（F 系列）、内存（E 系列）、GPU（N 系列）
- 可用性集（99.95% SLA）
- 可用性区域（99.99% SLA）
- VM 规模集用于自动扩展
- 最佳实践：使用托管磁盘、启用加速网络、使用邻近放置组

**App Service**
- Web 应用、API 应用、移动应用
- 用于暂存的部署槽
- 基于指标或计划的自动扩展
- 支持 .NET、Java、Node.js、Python、PHP、Ruby
- 最佳实践：使用部署槽、启用自动扩展、高效使用 App Service Plan

**Azure Functions**
- 消费计划（无服务器）
- 高级计划（VNet 集成、无冷启动）
- 专用计划（App Service Plan）
- Durable Functions 用于编排
- 最佳实践：保持函数小型化、生产环境使用高级计划、实现重试策略

**Azure Kubernetes Service（AKS）**
- 托管 Kubernetes 控制平面
- Azure CNI 或 kubenet 联网
- Azure AD 集成
- 虚拟节点（Azure Container Instances）
- 最佳实践：使用系统节点池、启用自动扩展、实施网络策略

**Container Instances**
- 无服务器容器
- 快速启动且无需基础设施管理
- 最适合批处理作业和突发工作负载

**Azure Batch**
- 大规模并行和 HPC 工作负载
- 计算节点自动扩展
- 任务调度和依赖关系

### 存储

**Blob 存储**
- 存储层：热、冷、归档
- 访问层：高级、标准
- 生命周期管理策略
- 用于合规的不可变存储
- 最佳实践：使用生命周期策略、启用软删除、实施版本控制

**Azure Files**
- SMB 和 NFS 文件共享
- 与 Azure File Sync 集成
- 高性能的高级层
- 最佳实践：数据库使用高级层、实施快照

**磁盘存储**
- 托管磁盘：高级 SSD、标准 SSD、标准 HDD、超级磁盘
- 使用 Azure 磁盘加密进行磁盘加密
- 快照和增量备份
- 最佳实践：生产环境使用高级 SSD、启用加密

**Data Lake Storage Gen2**
- 用于大数据的分层命名空间
- 建立在 Blob 存储上
- 与 Azure Synapse 和 Databricks 集成
- 最佳实践：启用分层命名空间、使用生命周期策略

**Azure NetApp Files**
- 企业级 NFS 和 SMB 共享
- 高性能和低延迟
- 快照和数据保护

### 数据库

**Azure SQL Database**
- 无服务器和已预置计算
- 超大规模扩展至 100TB
- 用于多个数据库的弹性池
- 自动调整和智能洞察
- 最佳实践：开发/测试使用无服务器、启用异地复制

**Azure SQL 托管实例**
- 与 SQL Server 近 100% 兼容
- 用于隔离的 VNet 集成
- 原生虚拟网络实现
- 最佳实践：用于直接迁移

**Cosmos DB**
- 多模型 NoSQL 数据库
- 具有多主的全球分发
- 一致性级别：强、有限过期、会话、一致前缀、最终
- API：SQL、MongoDB、Cassandra、Gremlin、Table
- 最佳实践：选择适当的一致性、分区键设计至关重要

**Azure Database for PostgreSQL/MySQL/MariaDB**
- 灵活服务器（较新）vs 单一服务器（旧版）
- 具有区域冗余的高可用性
- 用于扩展的只读副本
- 最佳实践：使用灵活服务器、启用 HA、实施连接池

**Cache for Redis**
- 内存缓存
- 用于可扩展性的集群
- 用于灾难恢复的异地复制
- 最佳实践：生产环境使用高级层、启用持久化

### 网络

**虚拟网络（VNet）**
- CIDR 规划（避免重叠）
- 带有网络安全组的子网
- 服务端点和专用链接
- 用于连接的 VNet 对等互连
- 最佳实践：规划 IP 地址空间、使用 NSG、实施专用链接

**Azure 负载均衡器**
- 第 4 层负载均衡
- 标准 SKU（区域冗余、SLA）
- 健康探测和分发算法
- 最佳实践：使用标准 SKU、配置健康探测

**Application Gateway**
- 第 7 层负载均衡
- WAF（Web 应用防火墙）
- 基于 URL 的路由和 SSL 终止
- 最佳实践：启用 WAF、使用自动扩展

**Azure Front Door**
- 全局负载均衡和 CDN
- 边缘的 WAF
- 用于低延迟的任播
- 最佳实践：用于全球应用、启用缓存

**VPN 网关和 ExpressRoute**
- 用于加密连接的站点到站点 VPN
- 用于专用、私密连接的 ExpressRoute
- 用于全球传输网络的虚拟 WAN
- 最佳实践：生产环境使用 ExpressRoute、实施冗余

**Azure 防火墙**
- 托管防火墙服务
- 应用程序和网络规则
- 威胁智能
- 最佳实践：在中心辐射拓扑中使用、启用 DNS 代理

**Azure 专用链接**
- 与 Azure 服务的专用连接
- 无公共互联网暴露
- 适用于 PaaS 服务
- 最佳实践：生产环境中的所有 PaaS 服务使用

### 安全和身份

**Azure Active Directory（Microsoft Entra ID）**
- 身份和访问管理
- 条件访问策略
- 多因素身份验证
- B2B 和 B2C 场景
- 最佳实践：启用 MFA、使用条件访问、实施 PIM

**Azure Key Vault**
- 密钥、密钥和证书管理
- 由硬件安全模块（HSM）支持
- 软删除和清除保护
- 最佳实践：启用软删除、使用 RBAC、实施专用链接

**Microsoft Defender for Cloud**
- 安全态势管理
- 混合工作负载的威胁保护
- 监管合规仪表板
- 即时 VM 访问
- 最佳实践：启用增强安全、实施建议

**Azure Policy**
- 大规模治理和合规
- 内置和自定义策略
- 拒绝、审计、追加效果
- 最佳实践：在管理组级别分配、强制之前测试

**Azure Sentinel**
- 云原生 SIEM 和 SOAR
- AI 驱动的威胁检测
- 与 Microsoft 365、第三方工具集成
- 最佳实践：启用数据连接器、创建自定义分析规则

## 架构模式

### 高可用性

**区域冗余模式**
```
Azure Front Door（全球）
    |
    v
Application Gateway（区域冗余）
    |
    v
VM 规模集（跨可用性区域）
    |
    v
Azure SQL Database（区域冗余）
```

**多区域模式**
```
Azure 流量管理器（基于 DNS 的路由）
    |
    ├── 区域 1：App Service + SQL Database（主）
    └── 区域 2：App Service + SQL Database（异地副本）
```

### 中心辐射拓扑

```
中心 VNet
├── Azure 防火墙
├── VPN 网关
└── 共享服务
    |
    ├── 辐射 VNet 1（生产）
    ├── 辐射 VNet 2（开发）
    └── 辐射 VNet 3（DMZ）
```

### 无服务器架构

**事件驱动模式**
```
Event Grid -> Azure Functions -> Cosmos DB
                    |
                    v
          Service Bus -> Functions（处理）
```

**API 优先模式**
```
API Management
    |
    ├── Function App 1（认证）
    ├── Function App 2（业务逻辑）
    └── Function App 3（数据访问）
```

### Azure 上的微服务

**基于 AKS**
```
Azure Front Door
    |
    v
Application Gateway + WAF
    |
    v
AKS（多个微服务）
    |
    ├── Cosmos DB（微服务 A）
    ├── SQL Database（微服务 B）
    └── Service Bus（异步通信）
```

**容器应用模式**
```
Azure Container Apps
├── Dapr 用于状态管理
├── KEDA 用于事件驱动扩展
└── Azure Monitor 用于可观察性
```

### 数据平台

```
数据源
    |
    v
Event Hubs / IoT Hub
    |
    v
Stream Analytics（实时处理）
    |
    v
Data Lake Storage Gen2
    |
    v
Azure Synapse Analytics
    |
    v
Power BI（可视化）
```

## 落地区设计

### 企业级落地区

**管理组层次结构**
```
租户根组
├── 平台
│   ├── 管理（监控、自动化）
│   ├── 连接性（中心网络、VPN）
│   └── 身份（域控制器）
└── 落地区
    ├── Corp（内部工作负载）
    └── Online（面向互联网的工作负载）
```

**网络拓扑**
```
中心 VNet（连接性订阅）
├── Azure 防火墙
├── VPN 网关
├── ExpressRoute 网关
└── Bastion

辐射 VNet（工作负载订阅）
├── Production VNet
├── Staging VNet
└── Development VNet
```

**治理**
- 用于合规的 Azure Policy
- 用于层次结构的管理组
- 在适当范围的 RBAC 分配
- 用于成本分配的资源标记
- 用于可重复部署的 Azure 蓝图

## 迁移策略

### Azure Migrate

1. **评估**
   - 使用 Azure Migrate 设备进行发现
   - 依赖关系分析
   - 基于性能的调整大小
   - 成本估算

2. **迁移**
   - Azure Migrate：服务器迁移（无代理）
   - 数据库迁移服务
   - App Service 迁移助手
   - Data Box 用于大数据传输

3. **优化**
   - 合理调整大小建议
   - 预留实例
   - Azure 混合权益

### 迁移模式

**重新托管**：Azure Migrate 用于 VM
**重新平台**：App Service、Azure SQL Database
**重构**：Container Apps、AKS、Functions
**重建**：Azure 原生服务（Cosmos DB、Cognitive Services）

## 成本优化

### 计算节省
- Azure 预留实例（1 年或 3 年，高达 72% 节省）
- 计算节省计划（高达 65% 节省）
- 用于容错工作负载的 Spot VM（高达 90% 节省）
- Azure 混合权益（使用现有 Windows Server/SQL 许可证）
- 开发/测试 VM 的自动关闭

### 存储节省
- Blob 存储生命周期策略（热 -> 冷 -> 归档）
- Azure Files：一般用途使用标准层
- 托管磁盘：如果可能，使用标准 SSD 而不是高级 SSD
- 删除未使用的快照和磁盘

### 数据库节省
- Azure SQL Database 的无服务器层
- Cosmos DB 的预留容量
- DTU 模型 vs vCore（基于工作负载选择）
- 不使用时暂停 Azure Synapse

### 监控
- Azure 成本管理 + 计费
- 成本警报和预算
- Azure Advisor 建议
- 用于成本分配的资源标记

## 灾难恢复

### Azure Site Recovery

**VM 复制**
- Azure 到 Azure 复制
- 本地到 Azure（VMware、Hyper-V、物理）
- RPO：30 秒到几分钟
- 自动故障转移和故障回复

**恢复计划**
- 多层应用恢复
- 可自定义脚本和手动操作
- 与 Azure Automation 集成

### 备份策略

**Azure Backup**
- VM 备份（应用一致性）
- Azure VM 中的 SQL Server 和 SAP HANA
- Azure Files 备份
- 跨区域恢复

**数据库备份**
- SQL Database：自动备份（7-35 天）
- Cosmos DB：连续备份（30 天）
- 长期保留策略

### 高可用性

**RTO/RPO 目标**
- 主动-主动：使用流量管理器的多区域（近零）
- 主动-被动：使用故障转移的异地复制（分钟）
- 备份和恢复：Azure Backup（小时）

## 监控和可观察性

### Azure Monitor

**组件**
- 指标：时间序列数据（1 分钟分辨率）
- 日志：用于查询（KQL）的日志分析工作区
- 警报：指标、日志和活动日志警报
- 仪表板：自定义可视化

**Application Insights**
- Web 应用的 APM
- 分布式追踪
- 实时指标流
- 智能检测和异常检测
- 最佳实践：检测所有应用、设置可用性测试

### 日志分析

**KQL 查询**
```kusto
// 性能分析
Perf
| where CounterName == "% Processor Time"
| summarize avg(CounterValue) by bin(TimeGenerated, 5m), Computer
| render timechart

// 失败请求
requests
| where success == false
| summarize count() by resultCode, bin(timestamp, 1h)
```

**工作簿**
- 交互式报告
- 参数化查询
- 组合指标和日志

## 身份和访问

### Azure AD 最佳实践

- 为所有用户启用 MFA
- 使用条件访问策略
- 实施特权身份管理（PIM）
- 定期访问审查
- 突破玻璃账户

### RBAC 设计

**内置角色**
- 所有者：包括 RBAC 的完全访问权限
- 参与者：除 RBAC 外的完全访问权限
- 读者：只读访问权限
- 用于特定需求的自定义角色

**范围层次结构**
```
管理组（最高）
    |
订阅
    |
资源组
    |
资源（最低）
```

最佳实践：在适当的最高范围分配、使用组而不是单个用户、应用最小权限
