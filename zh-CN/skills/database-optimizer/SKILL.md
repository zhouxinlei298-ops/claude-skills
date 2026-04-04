---
name: database-optimizer
description: Optimizes database queries and improves performance across PostgreSQL and MySQL systems. Use when investigating slow queries, analyzing execution plans, or optimizing database performance. Invoke for index design, query rewrites, configuration tuning, partitioning strategies, lock contention resolution.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.1"
  domain: infrastructure
  triggers: database optimization, slow query, query performance, database tuning, index optimization, execution plan, EXPLAIN ANALYZE, database performance, PostgreSQL optimization, MySQL optimization
  role: specialist
  scope: optimization
  output-format: analysis-and-code
  related-skills: devops-engineer, postgres-pro, graphql-architect
---

# 数据库优化器

资深数据库优化专家，精通多种数据库系统的性能调优、查询优化和可扩展性。

## 何时使用此技能

- 分析慢查询和执行计划
- 设计最优索引策略
- 调优数据库配置参数
- 优化模式设计和分区
- 减少锁竞争和死锁
- 提高缓存命中率和内存使用

## 核心工作流程

1. **分析性能** -- 在任何变更之前捕获基线指标并运行 `EXPLAIN ANALYZE`
2. **识别瓶颈** -- 查找低效查询、缺失索引、配置问题
3. **设计解决方案** -- 创建索引策略、查询重写、模式改进
4. **实施变更** -- 增量应用优化并监控；验证每个变更后再进行下一个
5. **验证结果** -- 重新运行 `EXPLAIN ANALYZE`，比较成本，测量实际时间改进，记录变更

> ⚠️ 始终先在非生产环境测试变更。如果写入性能下降或复制延迟增加，立即回滚。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| 查询优化 | `references/query-optimization.md` | 分析慢查询、执行计划 |
| 索引策略 | `references/index-strategies.md` | 设计索引、覆盖索引 |
| PostgreSQL 调优 | `references/postgresql-tuning.md` | PostgreSQL 特定优化 |
| MySQL 调优 | `references/mysql-tuning.md` | MySQL 特定优化 |
| 监控与分析 | `references/monitoring-analysis.md` | 性能指标、诊断 |

## 常见操作与示例

### 识别 Top 慢查询（PostgreSQL）
```sql
-- Requires pg_stat_statements extension
SELECT query,
       calls,
       round(total_exec_time::numeric, 2)  AS total_ms,
       round(mean_exec_time::numeric, 2)   AS mean_ms,
       round(stddev_exec_time::numeric, 2) AS stddev_ms,
       rows
FROM   pg_stat_statements
ORDER  BY mean_exec_time DESC
LIMIT  20;
```

### 捕获执行计划
```sql
-- Use BUFFERS to expose cache hit vs. disk read ratio
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.id, c.name
FROM   orders o
JOIN   customers c ON c.id = o.customer_id
WHERE  o.status = 'pending'
  AND  o.created_at > now() - interval '7 days';
```

### 解读 EXPLAIN 输出 -- 需要关注的关键模式

| 模式 | 症状 | 典型解决方案 |
|---------|---------|----------------|
| 大表上的 `Seq Scan` | 高行估算，无过滤选择性 | 在过滤列添加 B-tree 索引 |
| 大外部集合的 `Nested Loop` | 内循环中行数指数增长 | 考虑 Hash Join；为内部连接键添加索引 |
| `cost=... rows=1` 但实际 rows=50000 | 统计信息过期 | 运行 `ANALYZE <table>;` |
| `Buffers: hit=10 read=90000` | 低缓冲区缓存命中率 | 增加 `shared_buffers`；添加覆盖索引 |
| `Sort Method: external merge` | 排序溢出到磁盘 | 为会话增加 `work_mem` |

### 创建覆盖索引
```sql
-- Covers the filter AND the projected columns, eliminating a heap fetch
CREATE INDEX CONCURRENTLY idx_orders_status_created_covering
    ON orders (status, created_at)
    INCLUDE (customer_id, total_amount);
```

### 验证改进
```sql
-- Before optimization: save plan & timing
EXPLAIN (ANALYZE, BUFFERS) <query>;   -- note "Execution Time: X ms"

-- After optimization: compare
EXPLAIN (ANALYZE, BUFFERS) <query>;   -- target meaningful reduction in cost & time

-- Confirm index is actually used
SELECT indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM   pg_stat_user_indexes
WHERE  relname = 'orders';
```

### MySQL：查找慢查询
```sql
-- Inspect slow query log candidates
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER  BY SUM_TIMER_WAIT DESC
LIMIT  20;

-- Execution plan
EXPLAIN FORMAT=JSON
SELECT * FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL 7 DAY;
```

## 约束

### 必须做
- 在优化**之前**捕获 `EXPLAIN (ANALYZE, BUFFERS)` 输出 -- 这是基线
- 每次变更前后都测量性能
- 使用 `CONCURRENTLY`（PostgreSQL）创建索引以避免表锁
- 在非生产环境测试；如果写入性能或复制延迟恶化则回滚
- 使用前后指标记录所有优化决策
- 批量数据变更后运行 `ANALYZE` 刷新统计信息

### 不能做
- 在没有测量基线的情况下应用优化
- 创建冗余或未使用的索引
- 同时进行多个变更（无法归因影响）
- 忽视新索引导致的写放大
- 忽略 `VACUUM` / 统计信息维护

## 输出模板

在优化数据库性能时，提供：
1. 带有基线指标的性能分析（查询时间、成本、缓冲区命中率）
2. 识别的瓶颈和根本原因（附带 EXPLAIN 证据）
3. 带有具体变更的优化策略
4. 实施的 SQL / 配置变更
5. 用于测量改进的验证查询
6. 监控建议
