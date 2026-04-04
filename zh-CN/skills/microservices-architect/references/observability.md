# 微服务中的可观察性

监控、跟踪和调试分布式系统的全面指南。

## 三大支柱

### 1. 指标

**目的：** 系统行为的定量测量。

**类别：**

**业务指标：**
```
示例：
- 每分钟订单数
- 每小时收入
- 活跃用户
- 转化率
- 购物车放弃率

重要性：
- 与业务目标对齐
- 检测业务异常
- 指导扩展决策

实现：
from prometheus_client import Counter, Histogram

orders_total = Counter(
    'orders_total',
    '订单总数',
    ['status', 'payment_method']
)

order_value = Histogram(
    'order_value_dollars',
    '订单价值（美元）',
    buckets=[10, 50, 100, 500, 1000, 5000]
)

# 在代码中
orders_total.labels(status='completed', payment_method='credit_card').inc()
order_value.observe(order.total_amount)
```

**系统指标：**
```
基础设施：
- CPU 使用率
- 内存使用率
- 磁盘 I/O
- 网络吞吐量

应用程序：
- 请求速率
- 错误率
- 请求持续时间（延迟）
- 活跃连接数
- 线程池利用率

数据库：
- 查询持续时间
- 连接池使用率
- 慢查询
- 死锁

消息队列：
- 队列深度
- 消息处理速率
- 消费者延迟
- 死信队列大小
```

**四大黄金信号（Google SRE）：**
```
1. 延迟：
   - 服务请求的时间
   - 跟踪 p50、p95、p99、p99.9
   - 分开成功 vs 错误延迟

   request_duration = Histogram(
       'http_request_duration_seconds',
       'HTTP 请求持续时间',
       ['method', 'endpoint', 'status']
   )

2. 流量：
   - 每秒请求数
   - 每秒事务数
   - 并发用户数

   requests_total = Counter(
       'http_requests_total',
       'HTTP 请求总数',
       ['method', 'endpoint', 'status']
   )

3. 错误：
   - 失败请求率
   - 4xx vs 5xx 错误
   - 异常类型

   errors_total = Counter(
       'errors_total',
       '错误总数',
       ['service', 'error_type']
   )

4. 饱和度：
   - 资源利用率
   - 队列深度
   - 线程池使用率

   connection_pool_usage = Gauge(
       'db_connection_pool_active',
       '活跃数据库连接'
   )
```

**RED 方法（用于服务）：**
```
- Rate：每秒请求数
- Errors：每秒失败请求数
- Duration：请求延迟分布

非常适合微服务仪表板
```

**USE 方法（用于资源）：**
```
- Utilization：资源繁忙时间百分比
- Saturation：队列深度或等待线程
- Errors：错误计数

非常适合基础设施监控
```

### 2. 日志

**目的：** 带上下文的离散事件记录。

**结构化日志：**
```json
{
  "timestamp": "2025-12-14T15:30:45.123Z",
  "level": "INFO",
  "service": "order-service",
  "version": "1.2.3",
  "traceId": "abc123def456",
  "spanId": "span789",
  "userId": "user-123",
  "message": "订单创建成功",
  "orderId": "order-456",
  "totalAmount": 99.99,
  "currency": "USD",
  "duration_ms": 45,
  "endpoint": "/api/v1/orders",
  "method": "POST",
  "statusCode": 201
}
```

**日志级别：**
```
ERROR：
- 应用程序错误
- 失败操作
- 异常
使用：警报、立即关注

WARN：
- 功能降级
- 重试尝试
- 已弃用的 API 使用
使用：调查、潜在问题

INFO：
- 业务事件（订单创建、用户登录）
- 系统事件（服务启动、配置加载）
使用：审计踪迹、业务分析

DEBUG：
- 详细的执行流程
- 变量值
- 函数入口/出口
使用：开发、故障排除

TRACE：
- 非常详细的调试
使用：深度故障排除（通常在生产中禁用）
```

**关联 ID：**
```
跨服务的请求流：

客户端请求 → API 网关
                ↓ (correlationId: corr-123)
                订单服务
                ↓ (correlationId: corr-123)
                支付服务
                ↓ (correlationId: corr-123)
                通知服务

所有日志包含 correlationId: corr-123
容易跟踪整个请求流

实现：
import logging
from contextvars import ContextVar

correlation_id_var = ContextVar('correlation_id', default=None)

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = correlation_id_var.get()
        return True

# 中间件
async def correlation_middleware(request, call_next):
    correlation_id = request.headers.get('X-Correlation-ID', str(uuid4()))
    correlation_id_var.set(correlation_id)
    response = await call_next(request)
    response.headers['X-Correlation-ID'] = correlation_id
    return response
```

**日志聚合：**
```
服务 → 日志传输 → 集中式日志存储 → 可视化

工具：
- ELK Stack（Elasticsearch、Logstash、Kibana）
- EFK Stack（Elasticsearch、Fluentd、Kibana）
- Loki（来自 Grafana）
- CloudWatch Logs（AWS）
- Stackdriver（GCP）

查询示例：
# 查找特定用户的所有错误
service:"order-service" AND level:"ERROR" AND userId:"user-123"

# 查找慢请求
service:"payment-service" AND duration_ms:>5000

# 查找具有特定关联 ID 的请求
correlationId:"corr-123"
```

### 3. 分布式跟踪

**目的：** 可视化跨服务的请求流，识别瓶颈。

**概念：**

**跟踪（Trace）：**
```
跨越所有服务的整个请求旅程

示例：用户下订单
跟踪 ID：trace-abc123

跟踪中的 Span：
1. api-gateway: /checkout (200ms)
2. order-service: createOrder (150ms)
3. payment-service: processPayment (80ms)
4. inventory-service: reserveItems (40ms)
5. notification-service: sendEmail (30ms)

总计：200ms（部分并行执行）
```

**跨度（Span）：**
```
跟踪中的单个操作

Span 属性：
{
  "traceId": "trace-abc123",
  "spanId": "span-456",
  "parentSpanId": "span-123",
  "name": "POST /api/v1/orders",
  "startTime": "2025-12-14T15:30:45.000Z",
  "endTime": "2025-12-14T15:30:45.150Z",
  "duration": 150,
  "status": "OK",
  "attributes": {
    "http.method": "POST",
    "http.url": "/api/v1/orders",
    "http.status_code": 201,
    "user.id": "user-123",
    "order.id": "order-456",
    "order.total": 99.99
  },
  "events": [
    {
      "timestamp": "2025-12-14T15:30:45.050Z",
      "name": "验证订单项目"
    },
    {
      "timestamp": "2025-12-14T15:30:45.100Z",
      "name": "调用支付服务"
    }
  ]
}
```

**实现（OpenTelemetry）：**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# 设置跟踪
provider = TracerProvider()
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)

# 为 FastAPI 添加检测
app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# 手动创建 span
tracer = trace.get_tracer(__name__)

async def create_order(order_data):
    with tracer.start_as_current_span("create_order") as span:
        span.set_attribute("order.items_count", len(order_data.items))
        span.set_attribute("order.total", order_data.total)

        # 数据库操作
        with tracer.start_as_current_span("db.insert_order"):
            order_id = await db.insert_order(order_data)

        # 调用支付服务
        with tracer.start_as_current_span("http.payment_service") as payment_span:
            payment_span.set_attribute("http.url", f"{PAYMENT_URL}/payments")
            result = await payment_service.charge(order_id, order_data.total)

        return order_id
```

**跟踪可视化：**
```
Jaeger UI 显示：

时间线视图：
|-- api-gateway (200ms) ----------------------------------|
    |-- order-service (150ms) ------------------------|
        |-- db.insert_order (30ms) --|
        |-- payment-service (80ms) -----------------|
            |-- db.create_transaction (20ms) ----|
        |-- notification-service (30ms) ----------|

关键路径高亮显示
识别瓶颈（payment-service 耗时 80ms）
可见并行操作
```

**采样策略：**
```
问题：跟踪每个请求很昂贵

解决方案：

1. 概率采样：
   - 跟踪 1% 的请求
   - 适用于高流量服务

2. 速率限制采样：
   - 每秒最多 100 个跟踪
   - 防止跟踪后端过载

3. 基于尾部的采样：
   - 跟踪所有错误
   - 跟踪慢请求（>5s）
   - 采样 1% 的快速成功请求

4. 优先级采样：
   - 始终跟踪高级用户
   - 始终跟踪关键端点
   - 采样其他

实现：
from opentelemetry.sdk.trace.sampling import (
    ParentBasedTraceIdRatioBased,
    ALWAYS_ON,
    ALWAYS_OFF
)

# 采样 1% 的跟踪
sampler = ParentBasedTraceIdRatioBased(0.01)

# 或自定义采样器
class CustomSampler:
    def should_sample(self, context, trace_id, name, attributes):
        # 始终采样错误
        if attributes.get("http.status_code", 0) >= 500:
            return ALWAYS_ON

        # 始终采样慢请求
        if attributes.get("duration_ms", 0) > 5000:
            return ALWAYS_ON

        # 采样 1% 的其他请求
        return ParentBasedTraceIdRatioBased(0.01).should_sample(...)
```

## 服务级别目标（SLOs）

### 定义 SLO

**SLI（服务级别指标）：**
```
服务级别的定量测量

示例：
- 请求延迟：p99 < 200ms
- 可用性：99.9% 的请求成功
- 吞吐量：处理 10,000 请求/秒
```

**SLO（服务级别目标）：**
```
SLI 的目标值

示例：
- 99.9% 的请求在 < 200ms 内完成
- 30 天内 99.95% 的可用性
- 零数据丢失

SLO 组件：
- 指标：测量内容（延迟、可用性）
- 目标：阈值（99.9%、200ms）
- 时间窗口：评估周期（30 天、每周）
```

**SLA（服务级别协议）：**
```
如果未满足 SLO 则有后果的合同

示例：
- SLO：99.9% 可用性
- SLA：如果可用性 < 99.9%，客户获得 10% 退款

SLA ≤ SLO（为事故留出缓冲）
```

**错误预算：**
```
满足 SLO 的允许失败 = (100% - SLO 目标)

示例：
SLO：99.9% 可用性
错误预算：0.1% = 每月 43.8 分钟停机时间

错误预算消耗：
- 停机
- 慢响应
- 失败请求

当错误预算耗尽时：
- 冻结功能部署
- 专注于可靠性
- 仅部署关键修复

好处：
- 平衡创新与稳定性
- 数据驱动的部署决策
- 对齐工程优先级
```

### 实现 SLO 监控

**Prometheus + Grafana：**
```
# SLI：可用性
availability_sli = (
    sum(rate(http_requests_total{status!~"5.."}[30d]))
    /
    sum(rate(http_requests_total[30d]))
) * 100

# SLI：延迟
latency_sli = histogram_quantile(
    0.99,
    rate(http_request_duration_seconds_bucket[30d])
)

# 错误预算
error_budget_remaining = (
    1 - (target_slo / 100)
) - (
    1 - (availability_sli / 100)
)

当错误预算 < 10% 时警报：
alert: ErrorBudgetCritical
expr: error_budget_remaining < 0.1
annotations:
  summary: "错误预算严重不足"
  description: "仅剩 10% 错误预算。冻结部署。"
```

## 警报策略

### 警报级别

**严重（立即传呼）：**
```
条件：
- 服务完全宕机
- 错误率 > 50%
- 发生数据丢失
- SLO 消耗率严重

操作：
- 传呼值班工程师
- 自动创建事故
- 5 分钟内未确认则升级

示例：
alert: ServiceDown
expr: up{service="payment-service"} == 0
for: 1m
severity: critical
```

**警告（尽快调查）：**
```
条件：
- 错误率升高（5-10%）
- 延迟降级（p99 > 500ms）
- 队列深度增加
- 错误预算 < 25%

操作：
- Slack 通知
- 创建工单
- 工作时间内调查

示例：
alert: HighErrorRate
expr: rate(http_requests_total{status="500"}[5m]) > 0.05
for: 10m
severity: warning
```

**信息（感知）：**
```
条件：
- 部署完成
- 扩展事件
- 配置更改
- 达到容量阈值

操作：
- 记录到监控系统
- 仪表板注释
- 可选 Slack 通知
```

### 警报最佳实践

**可操作的警报：**
```
糟糕的警报：
"CPU 使用率高"

好的警报：
"order-service-pod-abc 上的 CPU 使用率 > 80% 持续 10 分钟
运维手册：https://wiki.company.com/runbooks/high-cpu
可能原因：内存泄漏或无限循环
操作：1) 检查最近部署 2) 查看日志中的异常 3) 考虑回滚"

包括：
✓ 有什么问题
✓ 为什么重要
✓ 如何调查
✓ 运维手册链接
✓ 建议的操作
```

**避免警报疲劳：**
```
问题：
- 警报太多
- 误报
- 不可操作的警报
- 重复警报

解决方案：
- 对症状而非原因发出警报
- 适当的阈值和持续时间
- 警报聚合（不要按 Pod 警报，按服务警报）
- 定期警报审查和调整
- 自动解决警报
- 维护期间静默

好的做法：
for: 5m  # 不要对瞬态峰值发出警报
group_by: [service]  # 按服务聚合
group_wait: 30s  # 发送前等待
group_interval: 5m  # 批量通知
```

## 可观察性技术栈

### 推荐工具

**指标：**
```
收集：Prometheus
- 基于拉取的指标
- 时间序列数据库
- 强大的查询语言（PromQL）
- 服务发现

可视化：Grafana
- 美观的仪表板
- 警报集成
- 多数据源
- 模板变量

替代方案：Datadog、New Relic、CloudWatch
```

**日志：**
```
聚合：ELK Stack
- Elasticsearch（存储和搜索）
- Logstash / Fluentd（收集）
- Kibana（可视化）

或：Loki（轻量级替代方案）
- 与 Grafana 集成
- 使用标签而非全文索引
- 更低的资源使用

替代方案：Splunk、Datadog、CloudWatch Logs
```

**跟踪：**
```
后端：Jaeger 或 Zipkin
- 跟踪存储
- 跟踪可视化
- 依赖关系图
- 性能分析

检测：OpenTelemetry
- 与供应商无关的标准
- 常见框架的自动检测
- 手动检测 API
- 导出到任何后端

替代方案：Datadog APM、New Relic、Lightstep
```

**一体化：**
```
可观察性平台：
- Datadog（指标、日志、跟踪、RUM）
- New Relic（APM、日志、基础设施）
- Dynatrace（自动检测、AI）

优点：
- 统一体验
- 相关数据
- 更容易设置

缺点：
- 供应商锁定
- 更高的成本
- 灵活性较差
```

### 实施检查清单

**对于每个服务：**
```
✓ 带有关联 ID 的结构化日志
✓ 指标已导出（Prometheus 格式）
✓ 分布式跟踪已设置
✓ 健康检查端点（/health/live、/health/ready）
✓ 优雅关闭处理
✓ 资源限制已设置（CPU、内存）
✓ 关键路径的警报已配置
✓ 仪表板已创建
✓ 运维手册已记录
✓ 值班轮换已建立
```

**对于系统范围：**
```
✓ 集中式日志聚合
✓ 分布式跟踪后端
✓ 指标聚合和存储
✓ 统一仪表板（服务概览）
✓ 警报路由已配置
✓ 事故管理流程
✓ 事后复盘模板
✓ SLO 定义和跟踪
✓ 依赖关系映射
✓ 混沌工程实验
```

## 故障排除工作流

**事故响应：**
```
1. 检测（警报触发）
   - 检查仪表板
   - 验证警报是否有效
   - 评估影响

2. 分类（确定严重性）
   - 严重：传呼值班人员
   - 警告：创建工单
   - 多少用户受到影响？
   - 哪些功能损坏？

3. 调查（找到根本原因）
   - 检查最近部署
   - 查看日志（按关联 ID 搜索）
   - 分析跟踪（慢操作）
   - 检查指标（资源饱和）
   - 检查依赖项

4. 缓解（停止损失）
   - 回滚部署
   - 扩展资源
   - 故障转移到备份
   - 启用断路器
   - 流量限流

5. 解决（修复根本原因）
   - 部署修复
   - 验证解决
   - 监控是否复发

6. 事后复盘（学习和改进）
   - 事件时间线
   - 根本原因分析
   - 行动项
   - 更新运维手册
```

**使用跟踪进行调试：**
```
场景：API 返回 500 错误

1. 查找失败的跟踪：
   - 过滤：status = error，service = api-gateway
   - 按时间戳排序（最新的）

2. 分析 span 瀑布图：
   - 识别哪个服务失败（order-service 返回 500）
   - 检查 span 中的错误消息
   - 查看 span 属性

3. 与日志关联：
   - 从失败的跟踪中提取跟踪 ID
   - 搜索日志：traceId:"trace-abc123"
   - 查找异常堆栈跟踪

4. 检查相关指标：
   - order-service 错误率在 10 分钟前飙升
   - 与部署对应
   - 可能原因：部署错误

5. 修复：
   - 回滚 order-service
   - 验证错误已停止
   - 为错误修复创建工单
```

## 总结

微服务中的可观察性是不可协商的：

**必备：**
- 带有关联 ID 的结构化日志
- 指标（RED/USE 方法论）
- 分布式跟踪（OpenTelemetry）
- 集中式日志聚合
- 带有错误预算的 SLO 跟踪
- 带有运维手册的可操作警报

**最佳实践：**
- 关联指标、日志和跟踪
- 根据用户体验定义 SLO
- 对症状而非原因发出警报
- 为常见问题维护运维手册
- 定期事后复盘和学习
- 通过游戏日练习事故响应

没有可观察性，你在生产环境中是盲目的。
