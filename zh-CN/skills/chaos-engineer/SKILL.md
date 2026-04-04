---
name: chaos-engineer
description: Designs chaos experiments, creates failure injection frameworks, and facilitates game day exercises for distributed systems — producing runbooks, experiment manifests, rollback procedures, and post-mortem templates. Use when designing chaos experiments, implementing failure injection frameworks, or conducting game day exercises. Invoke for chaos experiments, resilience testing, blast radius control, game days, antifragile systems, fault injection, Chaos Monkey, Litmus Chaos.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: devops
  triggers: chaos engineering, resilience testing, failure injection, game day, blast radius, chaos experiment, fault injection, Chaos Monkey, Litmus Chaos, antifragile
  role: specialist
  scope: implementation
  output-format: code
  related-skills: sre-engineer, devops-engineer, kubernetes-specialist
---

# Chaos Engineer

## 何时使用此技能

- 设计和执行混沌实验
- 实现故障注入框架（Chaos Monkey、Litmus 等）
- 规划和进行 Game Day 演练
- 构建爆炸半径控制和安全机制
- 在 CI/CD 中设置持续混沌测试
- 基于实验发现改进系统韧性

## 核心工作流程

1. **系统分析** - 映射架构、依赖关系、关键路径和故障模式
2. **实验设计** - 定义假设、稳态、爆炸半径和安全控制
3. **执行混沌** - 在监控和快速回滚下运行受控实验
4. **学习与改进** - 记录发现、实施修复、增强监控
5. **自动化** - 将混沌测试集成到 CI/CD 中实现持续韧性

## 参考指南

根据上下文加载详细指南：

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| 实验 | `references/experiment-design.md` | 设计假设、爆炸半径、回滚 |
| 基础设施 | `references/infrastructure-chaos.md` | 服务器、网络、区域、地域故障 |
| Kubernetes | `references/kubernetes-chaos.md` | Pod、节点、Litmus、Chaos Mesh 实验 |
| 工具与自动化 | `references/chaos-tools.md` | Chaos Monkey、Gremlin、Pumba、CI/CD 集成 |
| Game Day | `references/game-days.md` | 规划、执行、从 Game Day 中学习 |

## 安全检查清单

每次实验都必须执行的非显而易见的约束：

- **稳态优先** — 在注入任何故障之前定义并验证基线指标
- **爆炸半径上限** — 从最小可能的影响范围开始；仅在验证后扩大
- **自动回滚 ≤ 30 秒** — 中止路径必须在实验开始前编写脚本并测试
- **单一变量** — 每次只改变一个故障条件，直到行为被充分理解
- **没有安全网不在生产环境测试** — 面向客户的环境需要断路器、功能开关或金丝雀隔离
- **闭环** — 每个实验必须产生书面学习总结和至少一个已跟踪的改进

## 输出模板

实现混沌工程时，请提供：
1. 实验设计文档（假设、指标、爆炸半径）
2. 实现代码（故障注入脚本/清单）
3. 监控设置和告警配置
4. 回滚流程和安全控制
5. 学习总结和改进建议

## 具体示例：Pod 故障实验（Litmus Chaos）

以下展示了使用 Litmus Chaos 在 Kubernetes 上从假设到回滚的完整实验。

### 步骤 1 — 定义稳态并应用实验

```bash
# Verify baseline: p99 latency < 200ms, error rate < 0.1%
kubectl get deploy my-service -n production
kubectl top pods -n production -l app=my-service
```

### 步骤 2 — 创建并应用 Litmus ChaosEngine 清单

```yaml
# chaos-pod-delete.yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: my-service-pod-delete
  namespace: production
spec:
  appinfo:
    appns: production
    applabel: "app=my-service"
    appkind: deployment
  # Limit blast radius: only 1 replica at a time
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "60"          # seconds
            - name: CHAOS_INTERVAL
              value: "20"          # delete one pod every 20s
            - name: FORCE
              value: "false"
            - name: PODS_AFFECTED_PERC
              value: "33"          # max 33% of replicas affected
```

```bash
# Apply the experiment
kubectl apply -f chaos-pod-delete.yaml

# Watch experiment status
kubectl describe chaosengine my-service-pod-delete -n production
kubectl get chaosresult my-service-pod-delete-pod-delete -n production -w
```

### 步骤 3 — 实验期间监控

```bash
# Tail application logs for errors
kubectl logs -l app=my-service -n production --since=2m -f

# Check ChaosResult verdict when complete
kubectl get chaosresult my-service-pod-delete-pod-delete \
  -n production -o jsonpath='{.status.experimentStatus.verdict}'
```

### 步骤 4 — 回滚/中止（如果违反稳态）

```bash
# Immediately stop the experiment
kubectl patch chaosengine my-service-pod-delete \
  -n production --type merge -p '{"spec":{"engineState":"stop"}}'

# Confirm all pods are healthy
kubectl rollout status deployment/my-service -n production
```

## 具体示例：使用 toxiproxy 进行网络延迟

```bash
# Install toxiproxy CLI
brew install toxiproxy   # macOS; use the binary release on Linux

# Start toxiproxy server (runs alongside your service)
toxiproxy-server &

# Create a proxy for your downstream dependency
toxiproxy-cli create -l 0.0.0.0:22222 -u downstream-db:5432 db-proxy

# Inject 300ms latency with 10% jitter — blast radius: this proxy only
toxiproxy-cli toxic add db-proxy -t latency -a latency=300 -a jitter=30

# Run your load test / observe metrics here ...

# Remove the toxic to restore normal behaviour
toxiproxy-cli toxic remove db-proxy -n latency_downstream
```

## 具体示例：Chaos Monkey（Spinnaker / 独立模式）

```bash
# chaos-monkey-config.yml — restrict to a single ASG
deployment:
  enabled: true
  regionIndependence: false
chaos:
  enabled: true
  meanTimeBetweenKillsInWorkDays: 2
  minTimeBetweenKillsInWorkDays: 1
  grouping: APP           # kill one instance per app, not per cluster
  exceptions:
    - account: production
      region: us-east-1
      detail: "*-canary"  # never kill canary instances

# Apply and trigger a manual kill for testing
chaos-monkey --app my-service --account staging --dry-run false
```
