# 部署策略

## 策略对比

| 策略 | 使用场景 | 回滚 | 风险 |
|------|----------|------|------|
| **滚动部署** | 标准更新，可接受混合版本 | 通过健康检查自动回滚 | 低 |
| **蓝绿部署** | 零停机，需要即时回滚 | 切换流量到旧环境 | 中 |
| **金丝雀发布** | 风险缓解，渐进式发布 | 缩减金丝雀实例 | 低 |
| **重建部署** | 有状态应用，破坏性变更 | 重新部署上一个版本 | 高 |

## 滚动部署（Kubernetes）

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%        # Max pods above desired
      maxUnavailable: 25%  # Max pods unavailable
```

## 使用 Ingress 的蓝绿部署

```yaml
# Blue deployment (current)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  labels:
    version: blue
---
# Green deployment (new)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  labels:
    version: green
---
# Service pointing to active version
apiVersion: v1
kind: Service
metadata:
  name: app
spec:
  selector:
    version: blue  # Switch to 'green' for cutover
```

## 使用 Istio 的金丝雀发布

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: app
spec:
  hosts:
    - app
  http:
    - match:
        - headers:
            canary:
              exact: "true"
      route:
        - destination:
            host: app-canary
    - route:
        - destination:
            host: app-stable
          weight: 90
        - destination:
            host: app-canary
          weight: 10
```

## 回滚流程

### Kubernetes 回滚
```bash
# View rollout history
kubectl rollout history deployment/app

# Rollback to previous
kubectl rollout undo deployment/app

# Rollback to specific revision
kubectl rollout undo deployment/app --to-revision=2

# Check status
kubectl rollout status deployment/app
```

### ArgoCD 回滚
```bash
argocd app rollback app-prod --revision=123
```

### Terraform 回滚
```bash
# Identify previous state
terraform state list

# Import previous configuration
git checkout HEAD~1 -- main.tf
terraform apply
```

## 部署前检查清单

- [ ] 数据库迁移向后兼容
- [ ] 新功能的功能标志
- [ ] 监控仪表板已更新
- [ ] 告警阈值已审核
- [ ] 回滚流程已文档化
- [ ] 预发布环境已测试并批准
- [ ] 团队已获知部署窗口

## 部署后验证

```bash
# Check pod status
kubectl get pods -l app=app

# Check logs for errors
kubectl logs -l app=app --tail=100 | grep -i error

# Verify endpoints
curl -f https://app.example.com/health

# Check metrics
# - Error rate < 1%
# - Latency p99 < 500ms
# - No memory/CPU spikes
```

## 部署指标（DORA）

跟踪四个关键指标：
- **部署频率**：目标每天 10+ 次
- **变更前置时间**：目标 <1 小时
- **变更失败率**：目标 <5%
- **平均恢复时间**：目标 <30 分钟

```yaml
# Prometheus metrics for DORA tracking
- record: deployment:frequency:1d
  expr: count_over_time(deployment_completed[1d])

- record: deployment:lead_time:p95
  expr: histogram_quantile(0.95,
    rate(commit_to_deploy_seconds_bucket[1h]))

- record: deployment:failure_rate
  expr: |
    sum(rate(deployment_failed[1h]))
    / sum(rate(deployment_total[1h]))
```

## 自动化分析的高级金丝雀发布

```yaml
# Flagger: Automated canary with rollback
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: api
spec:
  provider: istio
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  progressDeadlineSeconds: 60
  service:
    port: 8080
    trafficPolicy:
      tls:
        mode: ISTIO_MUTUAL
  analysis:
    interval: 30s
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: error-rate
        templateRef:
          name: error-rate
        thresholdRange:
          max: 1
      - name: latency
        templateRef:
          name: latency
        thresholdRange:
          max: 500
    webhooks:
      - name: acceptance-test
        type: pre-rollout
        url: http://test-runner/
      - name: load-test
        url: http://loadtester/
        timeout: 5s
        metadata:
          type: bash
          cmd: "hey -z 1m -q 10 http://api-canary:8080/"
```

## 影子部署

```yaml
# Mirror traffic to shadow deployment
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api
spec:
  hosts:
    - api
  http:
    - match:
        - headers:
            x-test-version:
              exact: "v2"
      route:
        - destination:
            host: api
            subset: v2
      mirror:
        host: api
        subset: v2-shadow
      mirrorPercentage:
        value: 100
    - route:
        - destination:
            host: api
            subset: v1
```
