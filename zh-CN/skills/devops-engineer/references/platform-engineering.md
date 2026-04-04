# 平台工程

## 平台原则

- **自助服务优先**：减少手动工作到 <10%
- **黄金路径**：预先批准的、有明确观点的模板
- **开发者体验**：度量和优化生产力
- **平台即产品**：用产品思维对待平台

## 使用 Crossplane 的自助服务

```yaml
# Composition for self-service database
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: postgres-database
spec:
  compositeTypeRef:
    apiVersion: platform.example.com/v1alpha1
    kind: Database
  resources:
    - name: rds-instance
      base:
        apiVersion: rds.aws.crossplane.io/v1alpha1
        kind: DBInstance
        spec:
          forProvider:
            dbInstanceClass: db.t3.micro
            engine: postgres
            engineVersion: "15"
            masterUsername: admin
            allocatedStorage: 20
```

## Terraform 自助服务模块

```hcl
# modules/service/main.tf
variable "service_name" {}
variable "environment" {}

module "k8s_service" {
  source   = "./k8s-deployment"
  name     = var.service_name
  env      = var.environment
}

module "database" {
  source = "./postgres"
  name   = "${var.service_name}-db"
}

module "monitoring" {
  source  = "./monitoring-stack"
  service = var.service_name
}

output "service_url" {
  value = module.k8s_service.url
}
```

## Backstage 服务模板

```yaml
# templates/microservice/template.yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: microservice-template
  title: Microservice Golden Path
spec:
  owner: platform-team
  type: service
  parameters:
    - title: Service Info
      properties:
        name:
          type: string
        owner:
          type: string
          ui:field: OwnerPicker
        language:
          type: string
          enum: [go, python, nodejs, java]
  steps:
    - id: fetch
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
    - id: publish
      action: publish:github
      input:
        repoUrl: github.com?owner=org&repo=${{ parameters.name }}
    - id: register
      action: catalog:register
```

## 服务目录信息

```yaml
# catalog-info.yaml
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-service
  annotations:
    github.com/project-slug: org/payment-service
    pagerduty.com/integration-key: abc123
    grafana/dashboard-selector: service=payment
spec:
  type: service
  lifecycle: production
  owner: payments-team
  system: checkout
  dependsOn:
    - resource:default/payment-db
    - component:default/auth-service
  providesApis:
    - payment-api
```

## 黄金路径脚手架

```bash
#!/bin/bash
# create-service.sh - Golden path for new services

SERVICE=$1
LANG=$2

# Create from template
gh repo create "org/$SERVICE" --template "org/template-$LANG"
git clone "git@github.com:org/$SERVICE.git"
cd "$SERVICE"

# Setup CI/CD
cat > .github/workflows/ci.yml <<EOF
name: CI/CD
on: [push]
jobs:
  pipeline:
    uses: org/workflows/.github/workflows/standard.yml@v1
    with:
      service_name: $SERVICE
EOF

# Create infrastructure
cat > terraform/main.tf <<EOF
module "service" {
  source = "git::https://github.com/org/terraform//service"
  name   = "$SERVICE"
}
EOF

git add . && git commit -m "Golden path init" && git push

echo "✓ Service created! Merge to main to deploy."
```

## GitOps 仓库结构

```
gitops/
├── apps/
│   ├── production/
│   │   ├── payment-service/
│   │   └── auth-service/
│   └── staging/
│       └── payment-service/
├── infrastructure/
│   ├── clusters/
│   │   ├── prod-us-east/
│   │   └── prod-eu-west/
│   └── base/
│       ├── ingress/
│       └── monitoring/
└── platform/
    ├── backstage/
    ├── argocd/
    └── vault/
```

## ArgoCD 应用

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service
spec:
  project: default
  source:
    repoURL: https://github.com/org/gitops
    path: apps/production/payment-service
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    retry:
      limit: 5
      backoff:
        duration: 5s
        maxDuration: 3m
```

## 平台指标

```yaml
# prometheus/platform-metrics.yaml
groups:
  - name: platform
    rules:
      # Self-service adoption rate
      - record: platform:self_service:rate
        expr: |
          sum(rate(platform_provision_automated[1h]))
          /
          sum(rate(platform_provision_total[1h]))

      # Provisioning time P95
      - record: platform:provision:p95
        expr: |
          histogram_quantile(0.95,
            rate(platform_provision_duration_bucket[5m]))

      # Golden path adoption
      - record: platform:golden_path:adoption
        expr: |
          count(service{template="golden-path"})
          / count(service)
```

## 自定义 Backstage 插件

```typescript
// plugins/platform-stats/PlatformMetrics.tsx
import React from 'react';
import { InfoCard, Progress } from '@backstage/core-components';

export const PlatformMetrics = () => {
  const metrics = {
    selfServiceRate: 92,
    avgProvisionTime: '3.5min',
    uptime: '99.95%',
    satisfaction: 4.6
  };

  return (
    <InfoCard title="Platform Health">
      <Progress value={metrics.selfServiceRate} label="Self-Service" />
      <p>Provision Time: {metrics.avgProvisionTime}</p>
      <p>Uptime: {metrics.uptime}</p>
      <p>Satisfaction: {metrics.satisfaction}/5</p>
    </InfoCard>
  );
};
```

## 成本分配

```yaml
# kubecost/allocation.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-allocation
data:
  allocation.json: |
    {
      "defaultLabels": {
        "team": "team",
        "service": "app",
        "environment": "env"
      },
      "shareNamespaces": ["kube-system"],
      "shareCost": "weighted"
    }
```

## 平台 API

```python
# Platform API for self-service provisioning
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

class ServiceRequest(BaseModel):
    name: str
    environment: str
    language: str
    database: bool = False

@app.post("/api/v1/services")
async def create_service(request: ServiceRequest):
    # Validate and enqueue
    task = platform.provision_service(
        name=request.name,
        env=request.environment,
        template=f"golden-path-{request.language}"
    )
    return {"task_id": task.id, "status": "provisioning"}

@app.get("/api/v1/services/{name}/status")
async def service_status(name: str):
    return {
        "status": "running",
        "url": f"https://{name}.example.com",
        "health": "healthy",
        "cost_mtd": "$142.50"
    }
```

## 多租户架构

```yaml
# Policy: Resource quotas per tenant
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-quota
  namespace: team-payments
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
---
# RBAC: Namespace admin
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-admin
  namespace: team-payments
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: namespace-admin
subjects:
  - kind: Group
    name: team-payments
```

## 采用策略

```yaml
# Platform metrics tracking
apiVersion: v1
kind: ConfigMap
metadata:
  name: platform-goals
data:
  goals.yaml: |
    q1_2024:
      self_service_rate: 90%
      avg_provision_time: 5min
      developer_satisfaction: 4.5/5
      golden_path_adoption: 80%

    tracking:
      weekly_provisioning: true
      team_feedback: true
      support_tickets: true
      training_completion: true
```

## CLI 工具示例

```bash
#!/bin/bash
# platform-cli - Self-service CLI

platform() {
  case $1 in
    create)
      curl -X POST $PLATFORM_API/services \
        -d "{\"name\":\"$2\",\"env\":\"$3\",\"language\":\"$4\"}"
      ;;
    status)
      curl $PLATFORM_API/services/$2/status | jq
      ;;
    logs)
      kubectl logs -l app=$2 -n ${3:-staging} --tail=100
      ;;
    cost)
      curl $PLATFORM_API/services/$2/cost?period=mtd
      ;;
  esac
}
```

## 最佳实践

- 从第一天就设计自助服务
- 让黄金路径成为最容易的选择
- 持续度量开发者满意度
- 自动化平台操作
- 提供优秀的文档
- 构建 API，而不仅仅是工具
- 支持安全的实验
- 保持向后兼容
- 将平台视为产品
- 收集并回应反馈
- 每周跟踪采用指标
- 作为产品团队运行平台
- 投资开发者传道
- 维护平台的 SLO
- 提供快速、有帮助的支持
