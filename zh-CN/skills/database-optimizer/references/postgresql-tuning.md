# PostgreSQL 调优

## 内存配置

### 共享缓冲区

```sql
-- 推荐：系统 RAM 的 25%（专用数据库服务器可达 40%）
-- 对于 16GB RAM 服务器：
ALTER SYSTEM SET shared_buffers = '4GB';

-- 检查当前设置
SHOW shared_buffers;

-- 监控缓冲区命中率（目标：>99%）
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    round(sum(heap_blks_hit) / nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0) * 100, 2) as cache_hit_ratio
FROM pg_statio_user_tables;
```

### 工作内存

```sql
-- 用于排序/哈希的每个操作内存
-- 推荐：(总 RAM * 0.25) / max_connections
-- 对于 16GB RAM，100 个连接：约 40MB
ALTER SYSTEM SET work_mem = '40MB';

-- 监控排序
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    min_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%ORDER BY%' OR query LIKE '%GROUP BY%'
ORDER BY total_exec_time DESC
LIMIT 10;

-- 为大型操作设置每个会话的值
SET work_mem = '256MB';
SELECT ... ORDER BY ... LIMIT 1000;
RESET work_mem;
```

### 维护工作内存

```sql
-- 用于 VACUUM、CREATE INDEX、ALTER TABLE
-- 推荐：生产系统使用 1-2GB
ALTER SYSTEM SET maintenance_work_mem = '2GB';

-- Autovacuum 工作进程使用成比例的量
ALTER SYSTEM SET autovacuum_work_mem = '512MB';
```

### 有效缓存大小

```sql
-- 可用操作系统缓存的查询计划器提示
-- 推荐：总 RAM 的 50-75%
-- 对于 16GB RAM：
ALTER SYSTEM SET effective_cache_size = '12GB';
```

## 查询计划器设置

### 统计信息目标

```sql
-- 默认为 100，为复杂查询增加以获得更好的估计
ALTER SYSTEM SET default_statistics_target = 200;

-- 特定列的每列统计信息
ALTER TABLE users ALTER COLUMN email SET STATISTICS 500;

-- 强制更新统计信息
ANALYZE users;

-- 检查统计信息质量
SELECT
    schemaname, tablename, attname,
    n_distinct, correlation
FROM pg_stats
WHERE tablename = 'users';
```

### 并行查询配置

```sql
-- 启用并行查询
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers = 8;
ALTER SYSTEM SET parallel_setup_cost = 100;
ALTER SYSTEM SET parallel_tuple_cost = 0.01;

-- 考虑并行执行的最小行数
ALTER SYSTEM SET min_parallel_table_scan_size = '8MB';
ALTER SYSTEM SET min_parallel_index_scan_size = '512kB';

-- 检查查询是否使用并行执行
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM large_table WHERE condition = 'value';
-- 查找 "Parallel Seq Scan" 或 "Gather" 节点
```

### 连接和扫描方法

```sql
-- 启用所有连接方法（默认通常全部启用）
ALTER SYSTEM SET enable_hashjoin = on;
ALTER SYSTEM SET enable_mergejoin = on;
ALTER SYSTEM SET enable_nestloop = on;

-- 成本参数（根据硬件调整）
ALTER SYSTEM SET random_page_cost = 1.1;  -- 对于 SSD（默认 4.0 适用于 HDD）
ALTER SYSTEM SET seq_page_cost = 1.0;

-- 禁用方法进行测试（不要在生产环境中执行）
SET enable_seqscan = off;  -- 强制使用索引进行测试
```

## 写入性能优化

### WAL 配置

```sql
-- WAL 写入策略
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET wal_writer_delay = '200ms';

-- 检查点配置
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET max_wal_size = '2GB';
ALTER SYSTEM SET min_wal_size = '1GB';

-- 监控检查点
SELECT
    checkpoints_timed,
    checkpoints_req,
    checkpoint_write_time,
    checkpoint_sync_time,
    buffers_checkpoint,
    buffers_clean,
    buffers_backend
FROM pg_stat_bgwriter;

-- 请求的检查点太多 = 增加 max_wal_size
```

### 提交延迟

```sql
-- 分组提交（以延迟换取吞吐量）
ALTER SYSTEM SET commit_delay = 10000;  -- 10ms
ALTER SYSTEM SET commit_siblings = 5;

-- 异步提交（以持久性换取速度）
-- 谨慎使用 - 有崩溃时丢失最近提交的风险
ALTER SYSTEM SET synchronous_commit = 'off';

-- 或每个事务
BEGIN;
SET LOCAL synchronous_commit = 'off';
INSERT INTO logs (...) VALUES (...);
COMMIT;
```

## VACUUM 和 Autovacuum

### Autovacuum 配置

```sql
-- 启用 autovacuum（应始终开启）
ALTER SYSTEM SET autovacuum = on;

-- Autovacuum 工作进程设置
ALTER SYSTEM SET autovacuum_max_workers = 4;
ALTER SYSTEM SET autovacuum_naptime = '30s';

-- 触发 autovacuum 的阈值
ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1;  -- 10% 死元组
ALTER SYSTEM SET autovacuum_vacuum_threshold = 50;

-- 分析阈值
ALTER SYSTEM SET autovacuum_analyze_scale_factor = 0.05;  -- 5% 更改
ALTER SYSTEM SET autovacuum_analyze_threshold = 50;

-- 高变更表的每个表 autovacuum 设置
ALTER TABLE busy_table SET (
    autovacuum_vacuum_scale_factor = 0.01,  -- 更积极
    autovacuum_vacuum_cost_delay = 2,       -- 更快的 vacuum
    autovacuum_vacuum_cost_limit = 1000
);
```

### 手动 Vacuum 操作

```sql
-- 完整 vacuum（锁定表，回收空间）
VACUUM FULL users;  -- 谨慎使用，需要排他锁

-- 常规 vacuum（非锁定）
VACUUM (ANALYZE, VERBOSE) users;

-- 检查表膨胀
SELECT
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY n_dead_tup DESC;

-- 监控 autovacuum 活动
SELECT
    schemaname, relname,
    last_vacuum, last_autovacuum,
    last_analyze, last_autoanalyze,
    vacuum_count, autovacuum_count,
    analyze_count, autoanalyze_count
FROM pg_stat_user_tables
ORDER BY last_autovacuum DESC NULLS LAST;
```

## 连接池

### 配置

```sql
-- 最大连接数（保持合理以管理内存）
ALTER SYSTEM SET max_connections = 200;

-- 为超级用户保留的连接
ALTER SYSTEM SET superuser_reserved_connections = 3;

-- 连接生命周期
ALTER SYSTEM SET idle_in_transaction_session_timeout = '5min';
ALTER SYSTEM SET statement_timeout = '30s';  -- 每个查询超时

-- 监控连接
SELECT
    state,
    count(*),
    max(now() - state_change) as max_idle_time
FROM pg_stat_activity
WHERE state IS NOT NULL
GROUP BY state;

-- 查找长时间运行的查询
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
  AND state != 'idle';
```

## 锁管理

### 锁监控

```sql
-- 检查当前锁
SELECT
    locktype,
    relation::regclass,
    mode,
    granted,
    pid,
    pg_blocking_pids(pid) as blocked_by
FROM pg_locks
WHERE NOT granted
ORDER BY relation;

-- 查找阻塞查询
SELECT
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation = blocked_locks.relation
    AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- 死锁配置
ALTER SYSTEM SET deadlock_timeout = '1s';
ALTER SYSTEM SET log_lock_waits = on;
```

## 分区

### 范围分区

```sql
-- 创建分区表
CREATE TABLE events (
    id BIGSERIAL,
    event_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL,
    data JSONB
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE events_2024_02 PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 在分区上创建索引
CREATE INDEX idx_events_2024_01_type ON events_2024_01(event_type);
CREATE INDEX idx_events_2024_02_type ON events_2024_02(event_type);

-- 查询使用分区修剪
EXPLAIN (ANALYZE)
SELECT * FROM events
WHERE created_at >= '2024-01-15' AND created_at < '2024-01-20';
-- 应显示 "Partitions pruned: X"
```

## 性能监控

### 关键指标查询

```sql
-- pg_stat_statements（首先安装扩展）
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 顶级慢查询
SELECT
    round(total_exec_time::numeric, 2) as total_time,
    calls,
    round(mean_exec_time::numeric, 2) as mean_time,
    round((100 * total_exec_time / sum(total_exec_time) OVER ())::numeric, 2) as pct,
    query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- 按表的缓存命中率
SELECT
    schemaname,
    tablename,
    heap_blks_hit,
    heap_blks_read,
    round(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) as cache_hit_pct
FROM pg_statio_user_tables
WHERE heap_blks_hit + heap_blks_read > 0
ORDER BY heap_blks_read DESC;

-- 索引使用统计信息
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 配置文件示例

```ini
# postgresql.conf - 为 16GB RAM 服务器优化的生产配置

# 内存
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 40MB
maintenance_work_mem = 2GB

# WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB

# 查询计划器
default_statistics_target = 200
random_page_cost = 1.1  # SSD
effective_io_concurrency = 200  # SSD

# 并行查询
max_parallel_workers_per_gather = 4
max_parallel_workers = 8

# 连接
max_connections = 200

# 日志
log_min_duration_statement = 1000  # 记录超过 1s 的查询
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_checkpoints = on
log_lock_waits = on
```
