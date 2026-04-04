# 事件响应

## 响应指标

- **MTTD**（平均检测时间）：目标 < 5 分钟
- **MTTA**（平均确认时间）：目标 < 5 分钟
- **MTTR**（平均解决时间）：目标 < 30 分钟
- **MTBF**（平均故障间隔时间）：最大化

### 严重级别

| 级别 | 影响 | 响应 | 示例 |
|------|------|------|------|
| SEV1 | 完全中断 | 立即 | 数据库宕机，支付失败 |
| SEV2 | 严重降级 | 15 分钟 | API 延迟 >5s，50% 错误 |
| SEV3 | 轻微降级 | 1 小时 | 非关键功能损坏 |
| SEV4 | 低影响 | 工作时间 | UI 故障，日志问题 |

## 运行手册模板

```markdown
# Runbook: High API Error Rate

## Symptoms
- Alert: `api_error_rate > 0.05`
- Dashboard: https://grafana.example.com/d/api-errors

## Impact
Users cannot complete purchases (~$X per minute)

## Triage
1. Check dashboard for affected endpoints
2. Check recent deployments: `kubectl rollout history deployment/api`
3. Check dependencies: database, redis, external APIs

## Resolution

### Option 1: Rollback
kubectl rollout undo deployment/api -n production

### Option 2: Scale Up
kubectl scale deployment/api --replicas=10 -n production

### Option 3: Fix Config
kubectl set env deployment/api DB_POOL_SIZE=50 -n production

## Verification
- [ ] Error rate <1%
- [ ] P95 latency <500ms
- [ ] Health checks passing

## Communication
- Update status page
- Notify #incidents
- Post if user-facing
```

## 自动修复脚本

```python
#!/usr/bin/env python3
import kubernetes, prometheus_api_client

class IncidentRemediator:
    def check_high_error_rate(self):
        query = 'rate(http_requests_total{status=~"5.."}[5m]) > 0.05'
        result = self.prometheus.custom_query(query)
        return len(result) > 0

    def rollback_deployment(self, namespace, deployment):
        body = {'spec': {'rollbackTo': {'revision': 0}}}
        self.k8s.patch_namespaced_deployment(deployment, namespace, body)

    def remediate(self):
        if self.check_high_error_rate():
            if self.rollback_deployment('production', 'api'):
                time.sleep(120)
                if not self.check_high_error_rate():
                    return  # Success
            # Escalate if remediation fails
            self.create_incident("Auto-remediation failed")
```

## 事后回顾模板

```markdown
# Postmortem: API Outage - 2024-01-15

**Date**: January 15, 2024
**Duration**: 45 minutes (14:23 - 15:08 UTC)
**Severity**: SEV1
**Impact**: Complete API outage, ~$25K revenue loss

## Summary
API became unresponsive due to database connection pool exhaustion
from slow query in v2.3.1.

## Timeline (UTC)
- 14:23 - Alert fired
- 14:27 - Incident declared SEV1
- 14:30 - Rollback initiated
- 14:45 - Identified slow query
- 14:50 - Killed queries
- 15:08 - Resolved

## Root Cause
New query missing index on `user_id`, causing full table scans that
exhausted connection pool under load.

## Impact
- 100% API failure for 45 minutes
- 15,000 users affected
- $25K revenue loss
- 200+ support tickets

## Action Items
| Action | Owner | Deadline |
|--------|-------|----------|
| Add index on user_id | DB team | 2024-01-16 |
| Add query perf testing | Platform | 2024-01-22 |
| Increase staging DB size | Infra | 2024-01-30 |

## Lessons Learned
- Performance testing must use production-scale data
- Connection pool exhaustion needs active intervention
- Consider circuit breakers for DB operations
```

## PagerDuty 配置

```yaml
schedules:
  - name: Primary On-Call
    time_zone: America/New_York
    layers:
      - rotation_turn_length_seconds: 604800  # 1 week
        users: [PXXXXXX, PXXXXXX, PXXXXXX]

escalation_policies:
  - name: Production
    rules:
      - escalation_delay_in_minutes: 0
        targets: [{type: schedule, id: primary}]
      - escalation_delay_in_minutes: 15
        targets: [{type: schedule, id: secondary}]
      - escalation_delay_in_minutes: 30
        targets: [{type: user, id: manager}]
```

## 混沌工程

```yaml
# chaos-mesh: Pod failure test
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure-test
spec:
  action: pod-failure
  mode: one
  duration: "30s"
  selector:
    namespaces: [production]
    labelSelectors:
      app: api
  scheduler:
    cron: "@every 2h"
```

```bash
#!/bin/bash
# Game Day: Database failover drill

echo "🎮 Game Day: Database failover"
slack-cli -d incidents "Starting failover drill"

# Simulate failure
kubectl delete pod postgres-0 -n production

# Monitor recovery
start=$(date +%s)
while ! kubectl get pod postgres-1 | grep Running; do
  sleep 5
done
duration=$(($(date +%s) - start))

echo "Failover: ${duration}s" >> results.md
curl -f https://api.example.com/health || echo "FAIL"
```

## 证据收集与取证

```bash
#!/bin/bash
# collect-evidence.sh - Preserve incident evidence

INCIDENT_ID=$1
EVIDENCE_DIR="incidents/${INCIDENT_ID}/evidence"
mkdir -p $EVIDENCE_DIR

# Preserve logs
kubectl logs -l app=api --all-containers --timestamps \
  --since=2h > $EVIDENCE_DIR/pod-logs.txt

# Capture current state
kubectl get all -n production -o yaml > $EVIDENCE_DIR/k8s-state.yaml
kubectl describe pods -n production > $EVIDENCE_DIR/pod-details.txt

# Network traces
kubectl exec -n production deploy/api -- \
  tcpdump -i any -w /tmp/capture.pcap -G 60 -W 5 &

# Memory/CPU snapshot
kubectl top pods -n production > $EVIDENCE_DIR/resource-usage.txt

# Git commit at time of incident
git log --since="2 hours ago" --oneline > $EVIDENCE_DIR/recent-commits.txt

# Database queries
psql -c "SELECT * FROM pg_stat_activity" > $EVIDENCE_DIR/db-activity.txt

# Create timeline
echo "$(date): Evidence collection completed" >> $EVIDENCE_DIR/timeline.txt
```

## 通信模板

```markdown
## SEV1 Initial Notification

**INCIDENT ALERT - SEV1**

**Status**: Investigating
**Impact**: Payment API unavailable (100% error rate)
**Started**: 2024-01-15 14:23 UTC
**Affected**: All users (~15K active sessions)
**Lead**: @oncall-engineer
**War Room**: https://zoom.us/incident-123

Updates every 15 minutes or on major change.

---

## SEV1 Resolution Notification

**INCIDENT RESOLVED**

**Summary**: Payment API restored after database connection pool exhaustion
**Duration**: 45 minutes (14:23 - 15:08 UTC)
**Resolution**: Rollback to v2.3.0 + query optimization
**Impact**: 15K users, ~$25K revenue loss
**Next Steps**: Postmortem scheduled for Jan 16 10am

Thanks to @oncall-team for rapid response.
```

## 事件分类

| 类型 | 示例 | 响应团队 | 升级 |
|------|------|----------|------|
| **安全** | 泄露、数据泄露、未授权访问 | 安全 + DevOps | CISO、法务 |
| **服务** | 中断、降级、错误 | DevOps + SRE | 工程副总裁 |
| **数据** | 损坏、丢失、同步问题 | DBA + DevOps | CTO |
| **合规** | GDPR、SOC2、审计违规 | 合规 + 法务 | CEO |
| **第三方** | 供应商中断、API 故障 | DevOps + 产品 | 客户经理 |

## 安全事件具体处理

```bash
# Compromise investigation checklist
□ Isolate affected systems
□ Preserve logs and memory dumps
□ Identify attack vector
□ Check for lateral movement
□ Scan for malware/backdoors
□ Review access logs for 30 days
□ Identify data accessed
□ Assess exfiltration risk
□ Check for persistence mechanisms
□ Coordinate with security team
□ Notify legal if PII involved
□ Document chain of custody
```

## 合规要求

```yaml
# Incident notification requirements
gdpr:
  notification_deadline: 72h
  authority: Data Protection Officer
  required_info:
    - Nature of breach
    - Data categories affected
    - Number of individuals
    - Consequences
    - Remediation measures

sox:
  notification_deadline: immediate
  authority: Audit Committee
  documentation:
    - Financial impact
    - Control failures
    - Remediation plan

pci_dss:
  notification_deadline: 24h
  authority: Card brands + acquirer
  required_info:
    - Cardholder data affected
    - Incident timeline
    - Forensic investigation
```

## 最佳实践

- 为关键服务维护运行手册
- 每月进行游戏日演练
- 自动化常见修复
- 保持事后回顾无责备
- 跟踪事件指标
- 测试恢复流程
- 记录所有事件
- 持续改进检测
- 正确保存证据链
- 明确协调通信
- 立即升级安全事件
- 理解合规义务
- 培训团队响应流程
- 每季度审查和更新手册
