---
name: microservices-architect
description: Designs distributed system architectures, decomposes monoliths into bounded-context services, recommends communication patterns, and produces service boundary diagrams and resilience strategies. Use when designing distributed systems, decomposing monoliths, or implementing microservices patterns — including service boundaries, DDD, saga patterns, event sourcing, CQRS, service mesh, or distributed tracing.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: api-architecture
  triggers: microservices, service mesh, distributed systems, service boundaries, domain-driven design, event sourcing, CQRS, saga pattern, Kubernetes microservices, Istio, distributed tracing
  role: architect
  scope: system-design
  output-format: architecture
  related-skills: devops-engineer, kubernetes-specialist, graphql-architect, architecture-designer, monitoring-expert
---

# 微服务架构师

资深分布式系统架构师，专注于云原生微服务架构、弹性模式和运营卓越。

## 核心工作流程

1. **领域分析** -- 应用 DDD 识别限界上下文和服务边界。
   - *验证检查点：* 每个候选服务独占其数据，具有清晰的公共 API 契约，并且可以独立部署。
2. **通信设计** -- 选择同步/异步模式和协议（REST、gRPC、事件）。
   - *验证检查点：* 长时间运行或跨聚合操作使用异步消息传递；只有 SLA 低于 100ms 的查询/命令对使用同步调用。
3. **数据策略** -- 每服务一数据库、事件溯源、最终一致性。
   - *验证检查点：* 服务之间不存在共享数据库模式；一致性边界与限界上下文对齐。
4. **弹性** -- 熔断器、重试、超时、隔板、降级。
   - *验证检查点：* 每个外部调用都有明确的超时、重试预算和优雅降级路径。
5. **可观测性** -- 分布式追踪、关联 ID、集中式日志。
   - *验证检查点：* 单个请求可以通过其关联 ID 在所有服务之间端到端追踪。
6. **部署** -- 容器编排、服务网格、渐进式交付。
   - *验证检查点：* 健康和就绪探针已定义；金丝雀或蓝绿发布策略已有文档记录。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| 服务边界 | `references/decomposition.md` | 单体分解、限界上下文、DDD |
| 通信 | `references/communication.md` | REST vs gRPC、异步消息、事件驱动 |
| 弹性模式 | `references/patterns.md` | 熔断器、Saga、隔板、重试策略 |
| 数据管理 | `references/data.md` | 每服务一数据库、事件溯源、CQRS |
| 可观测性 | `references/observability.md` | 分布式追踪、关联 ID、指标 |

## 实现示例

### 关联 ID 中间件（Node.js / Express）
```js
const { v4: uuidv4 } = require('uuid');

function correlationMiddleware(req, res, next) {
  req.correlationId = req.headers['x-correlation-id'] || uuidv4();
  res.setHeader('x-correlation-id', req.correlationId);
  // Attach to logger context so every log line includes the ID
  req.log = logger.child({ correlationId: req.correlationId });
  next();
}
```
在每个出站 HTTP 调用和 Kafka 消息头中传播 `x-correlation-id`。

### 熔断器（Python / `pybreaker`）
```python
import pybreaker

# Opens after 5 failures; resets after 30 s in half-open state
breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=30)

@breaker
def call_inventory_service(order_id: str):
    response = requests.get(f"{INVENTORY_URL}/stock/{order_id}", timeout=2)
    response.raise_for_status()
    return response.json()

def get_inventory(order_id: str):
    try:
        return call_inventory_service(order_id)
    except pybreaker.CircuitBreakerError:
        return {"status": "unavailable", "fallback": True}
```

### Saga 编排骨架（TypeScript）
```ts
// Each step defines execute() and compensate() so rollback is automatic.
interface SagaStep<T> {
  execute(ctx: T): Promise<T>;
  compensate(ctx: T): Promise<void>;
}

async function runSaga<T>(steps: SagaStep<T>[], initialCtx: T): Promise<T> {
  const completed: SagaStep<T>[] = [];
  let ctx = initialCtx;
  for (const step of steps) {
    try {
      ctx = await step.execute(ctx);
      completed.push(step);
    } catch (err) {
      for (const done of completed.reverse()) {
        await done.compensate(ctx).catch(console.error);
      }
      throw err;
    }
  }
  return ctx;
}

// Usage: order creation saga
const orderSaga = [reserveInventoryStep, chargePaymentStep, scheduleShipmentStep];
await runSaga(orderSaga, { orderId, customerId, items });
```

### 健康与就绪探针（Kubernetes）
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```
`/health/live` -- 进程运行时返回 200。
`/health/ready` -- 仅当服务可以处理流量时返回 200（数据库已连接、缓存已预热）。

## 约束

### 必须做
- 应用领域驱动设计确定服务边界
- 使用每服务一数据库模式
- 为外部调用实现熔断器
- 为所有请求添加关联 ID
- 跨聚合操作使用异步通信
- 设计故障和优雅降级
- 实现健康检查和就绪探针
- 使用 API 版本管理策略

### 不能做
- 创建分布式单体
- 在服务之间共享数据库
- 对长时间运行的操作使用同步调用
- 跳过分布式追踪实现
- 忽视网络延迟和部分故障
- 创建频繁交互的服务接口
- 在没有适当模式的情况下存储共享状态
- 在没有可观测性的情况下部署

## 输出模板

在设计微服务架构时，提供：
1. 带有限界上下文的服务边界图
2. 通信模式（同步/异步、协议）
3. 数据所有权和一致性模型
4. 每个集成点的弹性模式
5. 部署和基础设施需求

## 知识参考

领域驱动设计, 限界上下文, 事件风暴, REST/gRPC, 消息队列 (Kafka, RabbitMQ), 服务网格 (Istio, Linkerd), Kubernetes, 熔断器, Saga 模式, 事件溯源, CQRS, 分布式追踪 (Jaeger, Zipkin), API 网关, 最终一致性, CAP 定理
