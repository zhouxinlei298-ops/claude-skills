# 云成本优化参考

包括预留实例、Spot/可抢占实例、合理调整大小和 FinOps 实践的云成本优化全面指南。

## FinOps 框架

### FinOps 原则

1. **团队需要协作** - 财务、工程和业务团队协同工作
2. **每个人承担责任** - 去中心化的成本责任
3. **集中化团队驱动 FinOps** - 最佳实践卓越中心
4. **报告应可访问且及时** - 实时可见性
5. **决策由业务价值驱动** - 每业务成果的成本
6. **利用可变成本模型** - 根据需要扩展和缩减

### FinOps 生命周期

```
      告知
         |
    +---------+
    |         |
    v         v
  优化 --> 运营
    ^         |
    |         |
    +---------+
```

**告知阶段**
- 可见性到云支出
- 分配和退单
- 基准测试和预测

**优化阶段**
- 费率优化（RI、节省计划）
- 使用优化（合理调整大小）
- 架构优化

**运营阶段**
- 持续改进
- 自动化和治理
- 异常检测

## 计算成本优化

### 预留实例 / 节省计划

**AWS 节省计划**

| 类型 | 灵活性 | 节省 |
|------|-------------|---------|
| Compute Savings Plans | 任何 EC2、Fargate、Lambda | 高达 66% |
| EC2 实例节省计划 | 特定实例系列、区域 | 高达 72% |
| 预留实例 | 特定实例类型、可用区 | 高达 72% |

**承诺策略**
```
基线（始终在线）：1 年或 3 年节省计划
可变（可预测）：定时预留实例
波动（不可预测）：按需 + Spot
```

**Azure 预留**
```
# Azure CLI - 购买预留
az reservations reservation-order purchase \
  --sku Standard_D2s_v3 \
  --term P1Y \
  --billing-scope /subscriptions/{subscription-id} \
  --quantity 10 \
  --applied-scope-type Shared
```

**GCP 承诺使用折扣**
- 基于资源：特定的 vCPU 和内存
- 基于支出：实现灵活性的美元承诺
- 1 年（37% 折扣）或 3 年（55% 折扣）

### Spot/可抢占实例

**何时使用 Spot**
- 批处理和分析
- CI/CD 构建代理
- 无状态 Web 服务器（带自动扩展）
- 机器学习训练
- 开发和测试环境

**AWS Spot 最佳实践**
```yaml
# EC2 Auto Scaling with Spot
混合实例策略：
  实例分配：
    按需基准容量：2
    按需基准以上百分比：20
    Spot 分配策略：容量优化
  启动模板：
    覆盖：
      - 实例类型：m5.large
      - 实例类型：m5a.large
      - 实例类型：m4.large
      - 实例类型：r5.large
```

**Spot 中断处理**
```python
# 检查 Spot 终止通知（AWS）
import requests

def check_spot_termination():
    try:
        response = requests.get(
            "http://169.254.169.254/latest/meta-data/spot/termination-time",
            timeout=2
        )
        if response.status_code == 200:
            # 2 分钟警告 - 优雅关闭
            graceful_shutdown()
    except requests.exceptions.RequestException:
        pass  # 未被终止
```

**GCP 可抢占/Spot VM**
```hcl
# Terraform - GCP Spot VM
resource "google_compute_instance" "spot" {
  name         = "spot-instance"
  machine_type = "n2-standard-4"

  调度 {
    可抢占                = true
    自动重启           = false
    配置模型          = "SPOT"
    instance_termination_action = "STOP"
  }
}
```

### 合理调整大小

**分析流程**
1. 收集指标（CPU、内存、网络、磁盘 I/O）
2. 识别空闲或利用率不足的资源
3. 推荐适当的实例大小
4. 在维护窗口期间实施更改
5. 监控和迭代

**AWS Compute Optimizer**
```bash
# 启用 Compute Optimizer
aws compute-optimizer update-enrollment-status \
  --status Active \
  --include-member-accounts

# 获取推荐
aws compute-optimizer get-ec2-instance-recommendations \
  --filters name=Finding,values=OVER_PROVISIONED
```

**合理调整大小阈值**
| 指标 | 利用率不足 | 最佳 | 利用率过高 |
|--------|---------------|-------|---------------|
| CPU | <20% 平均 | 40-60% 平均 | >80% 平均 |
| 内存 | <30% 平均 | 50-70% 平均 | >85% 平均 |
| 网络 | <10% 容量 | 可变 | >80% 容量 |

**Azure Advisor 推荐**
```bash
# 获取成本推荐
az advisor recommendation list \
  --category Cost \
  --query "[?impact=='High']"
```

## 存储成本优化

### 对象存储分层

**AWS S3 存储类别**
```
S3 标准
    |
    |（30 天）
    v
S3 标准-IA
    |
    |（90 天）
    v
S3 Glacier 即时检索
    |
    |（180 天）
    v
S3 Glacier 深度归档
```

**生命周期策略示例**
```json
{
  "规则": [
    {
      "ID": "优化成本",
      "状态": "启用",
      "筛选器": { "前缀": "logs/" },
      "转换": [
        { "天": 30, "存储类别": "STANDARD_IA" },
        { "天": 90, "存储类别": "GLACIER" },
        { "天": 365, "存储类别": "DEEP_ARCHIVE" }
      ],
      "过期": { "天": 730 }
    }
  ]
}
```

**S3 智能分层**
- 基于访问模式自动分层
- 无检索费用
- 小的监控费用（每个对象）
- 最适合不可预测的访问模式

### 块存储优化

**EBS 卷选择**
| 类型 | 用例 | $/GB/月 |
|------|----------|------------|
| gp3 | 通用目的 | $0.08 |
| gp2 | 遗留（迁移到 gp3） | $0.10 |
| io2 | 高 IOPS 数据库 | $0.125+ |
| st1 | 吞吐量（大数据） | $0.045 |
| sc1 | 冷归档 | $0.025 |

**gp3 迁移（20% 节省）**
```bash
# 将 EBS 卷从 gp2 修改为 gp3
aws ec2 modify-volume \
  --volume-id vol-12345678 \
  --volume-type gp3 \
  --iops 3000 \
  --throughput 125
```

### 数据库存储

**Aurora 存储优化**
- 仅为使用的存储付费（自动扩展）
- 无需预配置
- 10GB 增量至 128TB

**DynamoDB 容量模式**
| 模式 | 最适合 | 定价 |
|------|----------|--------|
| 按需 | 不可预测的流量 | 按请求付费 |
| 已预置 | 稳定的流量 | 按容量单位付费 |
| 已预置 + 自动扩展 | 可变但可预测 | 比按需便宜 |

## 网络成本优化

### 数据传输成本

**AWS 数据传输定价**
```
入站：免费
同一 AZ：免费
跨 AZ：$0.01/GB 每个方向
同一区域（通过公共 IP）：$0.01/GB
跨区域（通过公共 IP）：$0.02/GB
互联网出站（前 10TB）：$0.09/GB
```

**优化策略**
1. 尽可能将流量保持在同一 AZ 内
2. 为 AWS 服务使用 VPC 端点
3. 为可缓存内容使用 CloudFront
4. 传输前压缩数据
5. 使用区域性而非全球服务

**VPC 端点（避免 NAT 网关）**
```hcl
# 网关端点（S3、DynamoDB 免费）
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.us-east-1.s3"
}

# 接口端点（比用于特定服务的 NAT 更便宜）
resource "aws_vpc_endpoint" "ecr" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.us-east-1.ecr.api"
  vpc_endpoint_type = "接口"
}
```

### CDN 优化

**CloudFront 成本节省**
- 比直接从源传输更低的费率
- 缓存命中率优化（目标 >90%）
- 使用 Origin Shield 减少源负载
- 压缩对象（Gzip/Brotli）

```yaml
# CloudFront 缓存优化
缓存行为：
  - 路径模式："/static/*"
    缓存策略 ID：658327ea-f89d-4fab-a63d-7e88639e58f6  # CachingOptimized
    压缩：true
    TTL：
      默认 TTL：86400
      最大 TTL：31536000
```

## 无服务器成本优化

### Lambda 优化

**内存/CPU 调优**
```python
# 使用 AWS Lambda Power Tuning
# 找到成本与性能的最佳内存平衡

# 结果示例：
# 128MB：$0.0000021 每次调用，3200ms 持续时间
# 256MB：$0.0000025 每次调用，1600ms 持续时间
# 512MB：$0.0000031 每次调用，800ms 持续时间
# 1024MB：$0.0000042 每次调用，450ms 持续时间
# 2048MB：$0.0000001 每次调用，450ms 持续时间
# 最佳：1024MB（最佳成本-性能平衡）
```

**成本降低策略**
1. 合理调整内存分配
2. 最小化冷启动（为关键路径预置并发）
3. 使用 ARM64（Graviton2）- 低 20% 成本
4. 优化包大小以加快冷启动
5. 使用 Lambda Layers 共享依赖

**Graviton2 迁移**
```yaml
# 带 ARM64 的 SAM 模板
资源：
  MyFunction：
    类型：AWS::Serverless::Function
    属性：
      运行时：python3.11
      架构：
        - arm64  # 20% 成本节省
```

### 容器优化

**Fargate 定价优化**
```
# Fargate Spot：高达 70% 折扣
# 用于容错工作负载

ECS 服务：
  容量提供者策略：
    - 容量提供者：FARGATE_SPOT
      权重：4
    - 容量提供者：FARGATE
      权重：1
    基线：2  # 最少按需任务
```

**合理调整容器资源**
```yaml
# 使用 Container Insights 分析实际使用情况
资源：
  请求：
    内存："256Mi"  # 基于 p95 使用 + 20% 缓冲
    cpu："100m"      # 基于 p95 使用 + 20% 缓冲
  限制：
    内存："512Mi"  # 2 倍请求以应对突发
    cpu："500m"
```

## 成本分配和标记

### 标记策略

**必需标记**
```yaml
# Terraform - 强制标记
variable "required_tags" {
  default = {
    environment  = "prod"
    cost-center  = "engineering"
    owner        = "platform-team"
    project      = "api-gateway"
    managed-by   = "terraform"
  }
}

resource "aws_instance" "example" {
  ami           = data.aws_ami.latest.id
  instance_type = "t3.medium"
  标签          = var.required_tags
}
```

**标记强制执行**
```json
// AWS SCP - 拒绝未标记的资源
{
  "版本": "2012-10-17",
  "声明": [
    {
      "Sid": "拒绝未标记的 EC2",
      "效果": "拒绝",
      "操作": "ec2:RunInstances",
      "资源": "arn:aws:ec2:*:*:instance/*",
      "条件": {
        "Null": {
          "aws:RequestTag/cost-center": "true"
        }
      }
    }
  ]
}
```

### 成本分配报告

**AWS 成本和使用报告**
```bash
# 启用详细账单报告
aws cur put-report-definition \
  --report-definition '{
    "报告名称": "详细成本报告",
    "时间单位": "HOURLY",
    "格式": "Parquet",
    "压缩": "Parquet",
    "S3存储桶": "my-billing-bucket",
    "区域": "us-east-1",
    "其他资源": ["ATHENA"]
  }'
```

**Athena 分析查询**
```sql
-- 按服务和标记分析成本
SELECT
  line_item_product_code as 服务,
  resource_tags_user_cost_center as cost_center,
  SUM(line_item_unblended_cost) as 成本
FROM cost_report
WHERE month = '2024-01'
GROUP BY 1, 2
ORDER BY 3 DESC;

-- 未使用的预留实例
SELECT
  reservation_reservation_a_r_n,
  reservation_unused_quantity,
  reservation_unused_normalized_unit_quantity
FROM cost_report
WHERE reservation_unused_quantity > 0;
```

## 自动化和治理

### 自动成本控制

**带有操作的 AWS 预算**
```yaml
# CloudFormation - 带自动停止的预算
资源：
  月度成本预算：
    类型：AWS::Budgets::预算
    属性：
      预算：
        预算名称：monthly-cost-limit
        预算限制：
          金额：10000
          单位：美元
        时间单位：月度
        预算类型：成本
      使用订阅者的通知：
        - 通知：
            通知类型：实际
            比较运算符：大于
            阈值：80
          订阅者：
            - 订阅类型：电子邮件
              地址：finance@company.com
```

**定时扩展（开发/测试）**
```yaml
# 非生产时间停止非生产资源
资源：
  缩减计划：
    类型：AWS::AutoScaling::ScheduledAction
    属性：
      AutoScalingGroupName：!Ref DevASG
      预期容量：0
      循环：在星期一 020 * * MON-FRI  # 上午 8 点工作日

  扩展计划：
    类型：AWS::AutoScaling::ScheduledAction
    属性：
      AutoScalingGroupName：!Ref DevASG
      预期容量：3
      循环：在 0 8 * * MON-FRI   # 上午 8 点工作日
```

### 成本异常检测

**AWS 成本异常检测**
```bash
# 创建异常监控
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "监控名称": "ServiceMonitor",
    "监控类型": "维度",
    "监控维度": "服务"
  }'

# 创建异常订阅
aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "订阅名称": "成本警报",
    "监控 ARN 列表": ["arn:aws:ce:123456789:anomaly-monitor/abc123"],
    "订阅者": [{"类型": "电子邮件", "地址": "alerts@company.com"}],
    "阈值": 100
  }'
```

## 成本指标和 KPI

### 关键指标

| 指标 | 公式 | 目标 |
|--------|------|------|
| 单位成本 | 总成本 / 业务指标 | 降低 |
| 覆盖率 | 预留小时数 / 总小时数 | >70% |
| 利用率 | 已使用的预留小时数 / 已购买的预留 | >80% |
| 浪费 | 空闲资源成本 / 总成本 | <10% |
| 预测准确性 | 实际 / 预测 | 90-110% |

### 仪表板示例
```sql
-- 成本效率仪表板指标
WITH metrics AS (
  SELECT
    date_trunc('month', usage_date) as 月份,
    SUM(cost) as 总成本,
    SUM(CASE WHEN reservation_arn IS NOT NULL THEN cost END) as 预留成本,
    COUNT(DISTINCT user_id) as 活跃用户
  FROM cloud_costs
  GROUP BY 1
)
SELECT
  月份,
  总成本,
  预留成本 / 总成本 as 预留覆盖,
  总成本 / 活跃用户 as 每用户成本
FROM metrics;
```

## 快速获胜清单

**即时节省（本周）**
- [ ] 删除未使用的 EBS 卷和快照
- [ ] 终止不需要的已停止 EC2 实例
- [ ] 移除未使用的弹性 IP
- [ ] 删除未使用的负载均衡器
- [ ] 审查并删除旧的 AMI

**短期（本月）**
- [ ] 合理调整利用率不足的实例
- [ ] 将 gp2 卷迁移到 gp3
- [ ] 实施 S3 生命周期策略
- [ ] 启用 S3 智能分层
- [ ] 安排开发/测试环境

**中期（本季度）**
- [ ] 为基线购买节省计划
- [ ] 为容错工作负载实施 Spot
- [ ] 设置成本分配标记
- [ ] 启用成本异常检测
- [ ] 建立 FinOps 实践
