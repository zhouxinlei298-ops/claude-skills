# 多云架构参考

多云策略、抽象层、可移植性模式和供应商锁定缓解的全面指南。

## 多云策略

### 何时使用多云

**有效的用例**
- 需要在特定区域进行数据驻留的法规合规
- 选择最佳同类服务（BigQuery 用于分析、AWS 用于 ML）
- 并购集成（合并组织中的不同云）
- 云提供商作为故障域的灾难恢复
- 与云供应商谈判的筹码

**多云的糟糕理由**
- 在没有具体退出场景的情况下"避免供应商锁定"
- 假设可移植性是免费的（它有显著成本）
- 没有技术理由的政治决策
- 在提供商之间任意传播工作负载

### 多云模式

**主动-主动**
```
用户 -> 全局负载均衡器
              |
    +---------+---------+
    |                   |
  AWS 区域        GCP 区域
    |                   |
    +----> 数据同步 <--+
```
- 最高复杂性和成本
- 最适合全局延迟优化
- 需要强大的数据同步

**主动-被动（DR）**
```
用户 -> 主云（AWS）
              |
         [故障转移]
              |
         备用云（Azure）
```
- 复杂性低于主动-主动
- 云提供商成为故障域
- 备用云中是冷备或热备

**按工作负载分段**
```
分析 -> GCP（BigQuery）
核心应用 -> AWS（ECS、RDS）
办公    -> Azure（M365 集成）
```
- 每个工作负载在最合适的云上
- 无跨云数据同步
- 最简单的多云模式

## 抽象层

### 基础设施抽象

**Terraform（推荐）**
```hcl
# 与提供商无关的模块结构
module "compute" {
  source = "./modules/compute"

  provider_type = var.cloud_provider  # aws, azure, gcp
  instance_type = var.instance_size
  region        = var.region
}

# 提供商特定实现
# modules/compute/aws.tf
resource "aws_instance" "main" {
  count         = var.provider_type == "aws" ? 1 : 0
  ami           = data.aws_ami.latest.id
  instance_type = local.aws_instance_map[var.instance_size]
}

# modules/compute/azure.tf
resource "azurerm_virtual_machine" "main" {
  count    = var.provider_type == "azure" ? 1 : 0
  vm_size  = local.azure_vm_map[var.instance_size]
}
```

**Pulumi（代码优先）**
```typescript
// 使用 TypeScript 抽象云资源
interface ComputeConfig {
  size: "small" | "medium" | "large";
  region: string;
}

function createCompute(config: ComputeConfig, provider: "aws" | "gcp") {
  if (provider === "aws") {
    return new aws.ec2.Instance("web", {
      instanceType: sizeMap.aws[config.size],
      // ...
    });
  } else {
    return new gcp.compute.Instance("web", {
      machineType: sizeMap.gcp[config.size],
      // ...
    });
  }
}
```

### 容器编排（Kubernetes）

**可移植的 Kubernetes 部署**
```yaml
# 相同的清单在 EKS、AKS、GKE 上工作
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    spec:
      containers:
      - name: web
        image: myregistry/web:v1
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

**云特定注意事项**
| 功能 | EKS | AKS | GKE |
|---------|-----|-----|-----|
| 负载均衡器 | ALB/NLB 注解 | Azure LB | GCP LB |
| 存储类 | gp3、io2 | managed-premium | pd-ssd |
| IAM 集成 | IRSA | Workload Identity | Workload Identity |
| Ingress | AWS ALB 控制器 | AGIC | GKE Ingress |

### 应用程序抽象

**数据库抽象**
```python
# 使用标准协议（SQL、Redis、S3 API）
from sqlalchemy import create_engine

# 相同的代码适用于：
# - AWS RDS PostgreSQL
# - Azure Database for PostgreSQL
# - GCP Cloud SQL PostgreSQL
# - 自管理 PostgreSQL

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
```

**对象存储抽象**
```python
import boto3
from botocore.config import Config

# S3 兼容 API 适用于：
# - AWS S3
# - GCP Cloud Storage（互操作性模式）
# - MinIO
# - Cloudflare R2

s3_client = boto3.client(
    's3',
    endpoint_url=os.environ.get("S3_ENDPOINT"),  # 非AWS时覆盖
    aws_access_key_id=os.environ["ACCESS_KEY"],
    aws_secret_access_key=os.environ["SECRET_KEY"],
)
```

## 数据同步

### 数据库复制

**跨云 PostgreSQL**
```
AWS RDS 主
      |
      | 逻辑复制
      v
GCP Cloud SQL 副本（只读）
```

配置：
```sql
-- 在主库上（AWS RDS）
CREATE PUBLICATION my_publication FOR ALL TABLES;

-- 在副本上（GCP Cloud SQL）
CREATE SUBSCRIPTION my_subscription
  CONNECTION 'host=aws-rds-endpoint dbname=mydb user=repl'
  PUBLICATION my_publication;
```

**冲突解决策略**
- 最后写入获胜（基于时间戳）
- 应用程序级冲突解决
- 用于最终一致性数据的 CRDT 数据结构
- 事务数据避免多主

### 对象存储同步

**Rclone 用于跨云同步**
```bash
# 同步 S3 到 GCS
rclone sync s3:my-bucket gcs:my-bucket \
  --transfers 32 \
  --checkers 16 \
  --s3-upload-concurrency 8

# 带冲突处理的双向同步
rclone bisync s3:bucket gcs:bucket \
  --conflict-resolve newer
```

**事件驱动的复制**
```
S3 存储桶 -> S3 事件 -> Lambda -> GCS 上传
                              |
                              v
                       一致性检查
```

## 供应商锁定缓解

### 锁定风险评估

| 服务类型 | 锁定风险 | 缓解策略 |
|--------------|--------------|---------------------|
| 计算（VM） | 低 | 标准 OS 镜像、IaC |
| Kubernetes | 低 | 可移植清单、避免专有插件 |
| 对象存储 | 低 | S3 兼容 API、标准格式 |
| 托管数据库 | 中 | 标准 SQL、逻辑备份 |
| 无服务器函数 | 高 | 抽象层、容器 |
| 专有 AI/ML | 高 | 开源替代方案、ONNX 模型 |
| 托管服务 | 高 | 采用前评估可移植性 |

### 缓解策略

**1. 使用开放标准**
- SQL 数据库而非专有 NoSQL
- Kubernetes 而非 ECS/Cloud Run
- 用于对象存储的 S3 API
- 用于可观察性的 OpenTelemetry
- 用于身份验证的 OIDC

**2. 抽象专有服务**
```typescript
// 包装云特定服务
interface QueueService {
  send(message: string): Promise<void>;
  receive(): Promise<string>;
}

class SQSQueue implements QueueService {
  async send(message: string) {
    await this.sqsClient.sendMessage({ QueueUrl: this.url, MessageBody: message });
  }
}

class PubSubQueue implements QueueService {
  async send(message: string) {
    await this.pubsubClient.topic(this.topic).publish(Buffer.from(message));
  }
}

// 用于云选择的工厂模式
function createQueue(provider: string): QueueService {
  switch (provider) {
    case "aws": return new SQSQueue();
    case "gcp": return new PubSubQueue();
  }
}
```

**3. 维持退出能力**
- 定期数据导出测试
- 记录云特定依赖项
- 保持 IaC 在提供商间可移植
- 每年估算迁移工作量

**4. 容器化所有内容**
```dockerfile
# 可移植容器在任何地方运行
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

## 网络连接

### 跨云网络

**VPN 互连**
```
AWS VPC                          GCP VPC
   |                                |
   +---> AWS VPN 网关            |
              |                     |
              | IPsec 隧道        |
              |                     |
              +---> GCP Cloud VPN <-+
```

**专用互连（企业）**
```
本地数据中心
         |
    +----+----+
    |         |
AWS Direct  GCP Cloud
Connect     Interconnect
    |         |
    v         v
AWS VPC    GCP VPC
    |         |
    +----+----+
         |
    传输中心（如 Megaport、Equinix）
```

### 跨云服务网格

**Istio 多集群**
```yaml
# 主集群（AWS EKS）
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: multi-cloud-mesh
      multiCluster:
        clusterName: eks-primary
      network: aws-network

# 远程集群（GCP GKE）
spec:
  values:
    global:
      meshID: multi-cloud-mesh
      multiCluster:
        clusterName: gke-secondary
      network: gcp-network
```

## 成本管理

### 跨云成本可见性

**FinOps 工具**
- VMware CloudHealth
- Apptio Cloudability
- Spot.io（现为 NetApp 的一部分）
- Kubecost 用于 Kubernetes

**统一标记策略**
```
必需标记（所有云）：
- environment: prod/staging/dev
- cost-center: engineering/marketing/sales
- owner: team-name
- project: project-code
- managed-by: terraform/manual
```

### 成本比较框架

```
| 工作负载类型 | AWS | Azure | GCP | 决策 |
|---------------|-----|-------|-----|----------|
| 通用计算 | EC2 m5 | D-series | n2-standard | 比较 $/vCPU/小时 |
| GPU 训练 | p4d | NC-series | A2 | GCP 通常更便宜 |
| 对象存储 | S3 | Blob | GCS | 相似，检查出口 |
| 分析 | Redshift | Synapse | BigQuery | BigQuery 用于临时查询 |
| Kubernetes | EKS | AKS | GKE | GKE Autopilot 最简单 |
```

## 可观察性

### 统一监控技术栈

**OpenTelemetry Collector**
```yaml
# 从所有云收集，导出到单一后端
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:
  attributes:
    actions:
      - key: cloud.provider
        action: upsert
        value: ${CLOUD_PROVIDER}

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  jaeger:
    endpoint: jaeger:14250

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch, attributes]
      exporters: [prometheus]
```

**Grafana 用于统一仪表板**
- AWS CloudWatch 数据源
- Azure Monitor 数据源
- GCP Cloud Monitoring 数据源
- 跨所有云的单一视图

## 安全注意事项

### 身份联合

**跨云身份**
```
企业 IdP（Okta/Azure AD）
         |
    SAML/OIDC
         |
    +----+----+----+
    |    |    |    |
  AWS  Azure  GCP  K8s
  IAM   AD   IAM  RBAC
```

### 密钥管理

**HashiCorp Vault（云无关）**
```hcl
# 跨云单一密钥管理
resource "vault_aws_secret_backend_role" "aws_role" {
  backend = vault_aws_secret_backend.aws.path
  name    = "app-role"
  credential_type = "iam_user"
}

resource "vault_gcp_secret_roleset" "gcp_role" {
  backend     = vault_gcp_secret_backend.gcp.path
  roleset     = "app-role"
  project     = var.gcp_project
  token_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
}
```

### 网络安全

**跨云零信任**
- 所有服务之间的 mTLS（服务网格）
- 基于网络位置的无隐式信任
- 基于身份的访问控制
- 云之间加密传输（VPN/互连）
