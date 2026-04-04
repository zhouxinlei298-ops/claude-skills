# 非功能性需求检查清单

## NFR 类别

### 可扩展性

| 问题 | 常见目标 |
|------|----------|
| 预期并发用户？ | 100 / 1K / 10K / 100K |
| 每秒请求数？ | 10 / 100 / 1000 / 10000 |
| 数据量？ | GB / TB / PB |
| 增长率？ | 每年 10% / 50% / 100% |
| 峰值与平均负载比？ | 2x / 5x / 10x |

### 性能

| 问题 | 常见目标 |
|------|----------|
| API 响应时间？ | < 100ms / 200ms / 500ms p95 |
| 页面加载时间？ | < 1s / 2s / 3s |
| 数据库查询时间？ | < 10ms / 50ms / 100ms |
| 批处理吞吐量？ | 每小时 1K / 10K / 100K 条记录 |

### 可用性

| 目标 | 年度停机时间 | 使用场景 |
|------|------------|----------|
| 99% | 3.65 天 | 内部工具 |
| 99.9% | 8.76 小时 | 业务应用 |
| 99.95% | 4.38 小时 | 电子商务 |
| 99.99% | 52.6 分钟 | 金融系统 |
| 99.999% | 5.26 分钟 | 关键业务 |

### 安全性

| 问题 | 考虑因素 |
|------|----------|
| 是否需要身份验证？ | JWT, OAuth, SAML, MFA |
| 授权模型？ | RBAC, ABAC, ACL |
| 数据敏感度？ | 公开，内部，机密，PII |
| 合规要求？ | GDPR, HIPAA, PCI DSS, SOC 2 |
| 加密需求？ | 静态，传输中，端到端 |

### 可靠性

| 问题 | 考虑因素 |
|------|----------|
| 可接受的数据丢失？ | RPO: 0 / 1小时 / 24小时 |
| 恢复时间目标？ | RTO: 1小时 / 4小时 / 24小时 |
| 备份频率？ | 实时 / 每小时 / 每天 |
| 灾难恢复？ | 单区域 / 多区域 |

### 可维护性

| 问题 | 考虑因素 |
|------|----------|
| 部署频率？ | 每天 / 每周 / 每月 |
| 部署策略？ | 蓝绿部署，金丝雀发布，滚动更新 |
| 监控要求？ | 日志，指标，追踪，警报 |
| 待命要求？ | 24/7，工作时间内 |

### 成本

| 问题 | 考虑因素 |
|------|----------|
| 基础设施预算？ | $/月，$/用户，$/请求 |
| 运营预算？ | 维护所需的 FTE |
| 成本优化？ | 预留实例， spot 实例 |
| 成本警报？ | 通知阈值 |

## 模板

```markdown
## Non-Functional Requirements

### Performance
- API response time: < 200ms p95
- Page load time: < 2s
- Database query time: < 50ms

### Scalability
- Concurrent users: 10,000
- Requests per second: 1,000
- Data volume: 1TB

### Availability
- Target: 99.9% (8.76 hours/year downtime)
- RPO: 1 hour
- RTO: 4 hours

### Security
- Authentication: JWT with refresh tokens
- Authorization: Role-based (admin, user, guest)
- Compliance: GDPR, SOC 2

### Observability
- Logging: Structured JSON to ELK
- Metrics: Prometheus + Grafana
- Tracing: OpenTelemetry
- Alerts: PagerDuty integration
```

## 快速参考

| 类别 | 关键指标 |
|------|----------|
| 性能 | 响应时间（p95） |
| 可扩展性 | 并发用户数，RPS |
| 可用性 | 正常运行时间百分比 |
| 可靠性 | RPO，RTO |
| 安全性 | 合规要求 |
| 成本 | 每月预算 |