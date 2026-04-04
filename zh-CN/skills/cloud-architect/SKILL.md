---
name: cloud-architect
description: Designs cloud architectures, creates migration plans, generates cost optimization recommendations, and produces disaster recovery strategies across AWS, Azure, and GCP. Use when designing cloud architectures, planning migrations, or optimizing multi-cloud deployments. Invoke for Well-Architected Framework, cost optimization, disaster recovery, landing zones, security architecture, serverless design.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: infrastructure
  triggers: AWS, Azure, GCP, Google Cloud, cloud migration, cloud architecture, multi-cloud, cloud cost, Well-Architected, landing zone, cloud security, disaster recovery, cloud native, serverless architecture
  role: architect
  scope: infrastructure
  output-format: architecture
  related-skills: devops-engineer, kubernetes-specialist, terraform-engineer, security-reviewer, microservices-architect, monitoring-expert
---

# 云架构师

## 核心工作流程

1. **发现** -- 评估当前状态、需求、约束、合规要求
2. **设计** -- 选择服务、设计拓扑、规划数据架构
3. **安全** -- 实施零信任、身份联合、加密
4. **成本模型** -- 合理调整资源规格、预留容量、自动扩展
5. **迁移** -- 应用 6Rs 框架、定义批次、在切换前验证连接
6. **运营** -- 设置监控、自动化、持续优化

### 工作流验证检查点

**设计完成后：** 确认每个组件都有冗余策略，拓扑中不存在单点故障。

**迁移切换前：** 验证 VPC 对等连接或网络连接已完全建立：
```bash
# AWS: confirm peering connection is Active before proceeding
aws ec2 describe-vpc-peering-connections \
  --filters "Name=status-code,Values=active"

# Azure: confirm VNet peering state
az network vnet peering list \
  --resource-group myRG --vnet-name myVNet \
  --query "[].{Name:name,State:peeringState}"
```

**迁移完成后：** 验证应用健康状态和路由：
```bash
# AWS: check target group health in ALB
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
```

**DR 测试后：** 确认达到了 RTO/RPO 目标；记录实际恢复时间。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| AWS 服务 | `references/aws.md` | EC2、S3、Lambda、RDS、Well-Architected Framework |
| Azure 服务 | `references/azure.md` | VM、Storage、Functions、SQL、Cloud Adoption Framework |
| GCP 服务 | `references/gcp.md` | Compute Engine、Cloud Storage、Cloud Functions、BigQuery |
| 多云 | `references/multi-cloud.md` | 抽象层、可移植性、供应商锁定缓解 |
| 成本优化 | `references/cost.md` | 预留实例、Spot、合理调整、FinOps 实践 |

## 约束

### 必须做
- 设计高可用性（99.9%+）
- 实施安全设计（零信任）
- 使用基础设施即代码（Terraform、CloudFormation）
- 启用成本分配标签和监控
- 规划具有明确 RTO/RPO 的灾难恢复
- 关键工作负载实施多区域部署
- 尽可能使用托管服务
- 记录架构决策

### 不能做
- 在代码或公共仓库中存储凭证
- 跳过加密（静态和传输中）
- 创建单点故障
- 忽视成本优化机会
- 在没有适当监控的情况下部署
- 使用过于复杂的架构
- 忽视合规要求
- 跳过灾难恢复测试

## 常见模式与示例

### 最小权限 IAM（零信任）

与其使用宽泛的策略，不如将权限限定到特定资源和操作：

```bash
# AWS: create a scoped role for an application
aws iam create-role \
  --role-name AppRole \
  --assume-role-policy-document file://trust-policy.json

aws iam put-role-policy \
  --role-name AppRole \
  --policy-name AppInlinePolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-app-bucket/*"
    }]
  }'
```

```hcl
# Terraform equivalent
resource "aws_iam_role" "app_role" {
  name               = "AppRole"
  assume_role_policy = data.aws_iam_policy_document.trust.json
}

resource "aws_iam_role_policy" "app_policy" {
  role = aws_iam_role.app_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject"]
      Resource = "${aws_s3_bucket.app.arn}/*"
    }]
  })
}
```

### VPC 公共/私有子网（Terraform）

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = { Name = "main", CostCenter = var.cost_center }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet("10.0.0.0/16", 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet("10.0.0.0/16", 8, count.index + 10)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
}
```

### 自动扩展组（Terraform）

```hcl
resource "aws_autoscaling_group" "app" {
  desired_capacity    = 2
  min_size            = 1
  max_size            = 10
  vpc_zone_identifier = aws_subnet.private[*].id

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "CostCenter"
    value               = var.cost_center
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_policy" "cpu_target" {
  autoscaling_group_name = aws_autoscaling_group.app.name
  policy_type            = "TargetTrackingScaling"
  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 60.0
  }
}
```

### 成本分析 CLI

```bash
# AWS: identify top cost drivers for the last 30 days
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[*].{Service:Keys[0],Cost:Metrics.UnblendedCost.Amount}' \
  --output table

# Azure: review spend by resource group
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[].{ResourceGroup:resourceGroup,Cost:pretaxCost,Currency:currency}" \
  --output table
```

## 输出模板

在设计云架构时，提供：
1. 包含服务和数据流的架构图
2. 服务选择理由（计算、存储、数据库、网络）
3. 安全架构（IAM、网络分段、加密）
4. 成本估算和优化策略
5. 部署方法和回滚计划
