# 告警规则

## Prometheus 告警规则

```yaml
# alerts.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: Error rate is {{ $value | humanizePercentage }}

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High latency detected
          description: 95th percentile latency is {{ $value }}s

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: Service {{ $labels.instance }} is down

  - name: infrastructure
    rules:
      - alert: HighMemoryUsage
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
          / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: High memory usage on {{ $labels.instance }}

      - alert: HighCPUUsage
        expr: |
          100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: High CPU usage on {{ $labels.instance }}

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: Disk space low on {{ $labels.instance }}
```

## 告警设计原则

```yaml
# Good alert: Actionable, specific
- alert: DatabaseConnectionPoolExhausted
  expr: db_pool_available_connections == 0
  for: 2m
  annotations:
    runbook_url: https://wiki.example.com/runbooks/db-pool

# Bad alert: Too noisy, not actionable
- alert: AnyError
  expr: errors_total > 0  # Will always fire
```

## 严重级别

| 严重级别 | 响应方式 | 示例 |
|----------|----------|---------|
| `critical` | 立即响应 | 服务中断、数据丢失 |
| `warning` | 尽快调查 | 高延迟、磁盘空间不足 |
| `info` | 早上检查 | 异常流量模式 |

## Alertmanager 配置

```yaml
# alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/...'

route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-key'
```

## 快速参考

| 字段 | 用途 |
|-------|---------|
| `expr` | PromQL 查询 |
| `for` | 触发前的持续时间 |
| `labels` | 分类（严重级别） |
| `annotations` | 人可读的信息 |

| 阈值 | 使用场景 |
|-----------|-----|
| 错误率 > 5% | 关键 |
| p95 延迟 > 1s | 警告 |
| 磁盘 < 10% | 关键 |
| 内存 > 90% | 警告 |