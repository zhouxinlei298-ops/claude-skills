# 仪表板

## RED 方法（请求导向）

```
Rate     - Requests per second
Errors   - Failed requests per second
Duration - Response time distribution
```

```promql
# Rate
sum(rate(http_requests_total[5m]))

# Errors
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m]))

# Duration (p95)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## USE 方法（资源导向）

```
Utilization - % time resource is busy
Saturation  - Queue depth, backlog
Errors      - Error events
```

```promql
# CPU Utilization
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory Saturation
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes

# Disk Errors
rate(node_disk_io_time_weighted_seconds_total[5m])
```

## 仪表板结构

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE OVERVIEW                         │
│  Request Rate │ Error Rate │ p50 Latency │ p99 Latency     │
├─────────────────────────────────────────────────────────────┤
│                    REQUEST METRICS                          │
│  [Graph: Requests/s by endpoint]                           │
│  [Graph: Error rate over time]                             │
├─────────────────────────────────────────────────────────────┤
│                    LATENCY METRICS                          │
│  [Heatmap: Latency distribution]                           │
│  [Graph: p50, p95, p99 over time]                          │
├─────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE                           │
│  CPU │ Memory │ Disk │ Network                             │
└─────────────────────────────────────────────────────────────┘
```

## 关键面板

### 统计面板（单值）

```promql
# Current RPS
sum(rate(http_requests_total[5m]))

# Error percentage
sum(rate(http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(http_requests_total[5m])) * 100
```

### 时间序列

```promql
# Requests by status
sum by (status) (rate(http_requests_total[5m]))

# Latency percentiles
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### 表格

```promql
# Top endpoints by error rate
topk(10,
  sum by (path) (rate(http_requests_total{status=~"5.."}[5m]))
  /
  sum by (path) (rate(http_requests_total[5m]))
)
```

## 业务指标仪表板

```promql
# Orders per minute
sum(rate(orders_created_total[5m])) * 60

# Revenue (if tracked)
sum(increase(order_value_dollars_sum[1h]))

# Active users (gauge)
active_users_total
```

## 快速参考

| 方法 | 关注点 | 指标 |
|--------|-------|---------|
| RED | 服务 | 速率、错误、延迟 |
| USE | 资源 | 利用率、饱和度、错误 |

| 面板类型 | 使用场景 |
|------------|----------|
| 统计 | 单个 KPI |
| 时间序列 | 趋势 |
| 热力图 | 延迟分布 |
| 表格 | Top N、详细信息 |
| 仪表盘 | 当前值 vs 阈值 |