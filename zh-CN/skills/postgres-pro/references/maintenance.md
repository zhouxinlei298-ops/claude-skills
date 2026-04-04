# 数据库维护

## VACUUM 基础

### 为什么 VACUUM 至关重要

PostgreSQL 使用 MVCC（多版本并发控制）：
- 更新/删除不会立即移除旧行
- 旧行标记为"死元组"
- VACUUM 从死元组中回收空间
- 没有 VACUUM：表膨胀、性能下降、事务 ID 环绕

### VACUUM 变体

```sql
-- 标准 VACUUM（非阻塞，回收空间以重用）
VACUUM users;
VACUUM;  -- 所有表

-- VACUUM FULL（锁定表，重写整个表，回收磁盘空间）
VACUUM FULL users;
-- 使用 pg_repack 作为替代（生产环境非阻塞）

-- VACUUM VERBOSE（显示详细信息）
VACUUM VERBOSE users;

-- VACUUM ANALYZE（vacuum + 更新统计信息）
VACUUM ANALYZE users;
```

### VACUUM 监控

```sql
-- 检查表上次 vacuum 的时间
SELECT
  schemaname,
  relname,
  last_vacuum,
  last_autovacuum,
  n_dead_tup,
  n_live_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- 检查 vacuum 进度（PG 9.6+）
SELECT
  pid,
  datname,
  relid::regclass,
  phase,
  heap_blks_total,
  heap_blks_scanned,
  heap_blks_vacuumed,
  round(100.0 * heap_blks_scanned / NULLIF(heap_blks_total, 0), 2) as pct_complete
FROM pg_stat_progress_vacuum;
```

## Autovacuum 配置

```sql
-- 全局设置（postgresql.conf）
autovacuum = on
autovacuum_max_workers = 3
autovacuum_naptime = 60s  -- 检查间隔

-- Vacuum 阈值
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.2
-- 触发条件：dead_tuples > threshold + (scale_factor * total_tuples)
-- 默认：50 + (0.2 * 1000000) = 200,050 行死元组（对于 100 万行表）

-- 分析阈值
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.1

-- 性能设置
autovacuum_vacuum_cost_delay = 2ms  -- 更低 = 更快，更多 I/O 影响
autovacuum_vacuum_cost_limit = 200
```

### 每表 Autovacuum 调优

```sql
-- 高变更表：更积极地 vacuum
ALTER TABLE orders SET (
  autovacuum_vacuum_scale_factor = 0.05,  -- 5% 而非 20%
  autovacuum_vacuum_threshold = 1000,
  autovacuum_analyze_scale_factor = 0.02
);

-- 大型、稳定表：较少 vacuum
ALTER TABLE archive_logs SET (
  autovacuum_vacuum_scale_factor = 0.5,
  autovacuum_vacuum_threshold = 5000
);

-- 极高变更表：禁用成本延迟
ALTER TABLE sessions SET (
  autovacuum_vacuum_cost_delay = 0
);

-- 查看表设置
SELECT
  relname,
  reloptions
FROM pg_class
WHERE relname = 'orders';
```

## ANALYZE（统计信息）

```sql
-- 更新查询计划器的统计信息
ANALYZE users;
ANALYZE;  -- 所有表

-- 检查统计信息新鲜度
SELECT
  schemaname,
  relname,
  last_analyze,
  last_autoanalyze,
  n_mod_since_analyze
FROM pg_stat_user_tables
ORDER BY n_mod_since_analyze DESC;

-- 为高基数列增加统计目标
ALTER TABLE users ALTER COLUMN email SET STATISTICS 1000;
-- 默认为 100，范围为 0-10000
-- 更高 = 更好的估计，ANALYZE 更慢

-- 查看列统计信息
SELECT
  tablename,
  attname,
  n_distinct,      -- 估计的唯一值数量
  correlation,     -- 物理与逻辑顺序的对比（-1 到 1）
  null_frac        -- null 的百分比
FROM pg_stats
WHERE tablename = 'users';
```

## 膨胀检测和移除

### 检测表膨胀

```sql
-- 近似膨胀计算
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  round(100 * pg_relation_size(schemaname||'.'||tablename)::numeric /
        NULLIF(pg_total_relation_size(schemaname||'.'||tablename), 0), 2) as table_pct,
  n_dead_tup,
  round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
WHERE pg_total_relation_size(schemaname||'.'||tablename) > 10485760  -- > 10MB
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 检测索引膨胀

```sql
-- 未使用的索引
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%pkey'  -- 未使用的索引
ORDER BY pg_relation_size(indexrelid) DESC;

-- 索引大小与表大小对比
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                 pg_relation_size(schemaname||'.'||tablename)) as indexes_size,
  round(100.0 * (pg_total_relation_size(schemaname||'.'||tablename) -
                 pg_relation_size(schemaname||'.'||tablename))::numeric /
        NULLIF(pg_relation_size(schemaname||'.'||tablename), 0), 2) as index_ratio_pct
FROM pg_stat_user_tables
WHERE pg_total_relation_size(schemaname||'.'||tablename) > 10485760
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 移除膨胀

```sql
-- 选项 1：VACUUM FULL（锁定表）
VACUUM FULL users;

-- 选项 2：pg_repack（在线，无锁）
-- 命令行：pg_repack -d mydb -t users

-- 选项 3：REINDEX（用于索引膨胀）
REINDEX TABLE users;
REINDEX INDEX CONCURRENTLY idx_users_email;  -- 非阻塞（PG 12+）

-- 选项 4：CLUSTER（按索引顺序重写表，锁定表）
CLUSTER users USING users_pkey;
```

## pg_stat 监控视图

### pg_stat_activity（当前查询）

```sql
-- 活跃查询
SELECT
  pid,
  usename,
  application_name,
  client_addr,
  state,
  query_start,
  state_change,
  query
FROM pg_stat_activity
WHERE state = 'active'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY query_start;

-- 长时间运行的查询
SELECT
  pid,
  now() - query_start as duration,
  state,
  query
FROM pg_stat_activity
WHERE state = 'active'
  AND (now() - query_start) > interval '5 minutes'
ORDER BY duration DESC;

-- 终止长时间运行的查询
SELECT pg_cancel_backend(pid);  -- 优雅
SELECT pg_terminate_backend(pid);  -- 强制

-- 空闲事务（不好，持有锁）
SELECT
  pid,
  usename,
  state,
  now() - state_change as idle_duration,
  query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND (now() - state_change) > interval '1 minute';
```

### pg_stat_database（数据库范围统计）

```sql
SELECT
  datname,
  numbackends,  -- 活跃连接
  xact_commit,
  xact_rollback,
  round(100.0 * xact_rollback / NULLIF(xact_commit + xact_rollback, 0), 2) as rollback_pct,
  blks_read,
  blks_hit,
  round(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_ratio,
  tup_returned,
  tup_fetched,
  tup_inserted,
  tup_updated,
  tup_deleted
FROM pg_stat_database
WHERE datname = current_database();
```

### pg_stat_user_tables（表统计）

```sql
SELECT
  schemaname,
  relname,
  seq_scan,        -- 顺序扫描（高 = 可能需要索引）
  seq_tup_read,
  idx_scan,        -- 索引扫描
  idx_tup_fetch,
  n_tup_ins,
  n_tup_upd,
  n_tup_del,
  n_tup_hot_upd,   -- HOT 更新（好，页内更新）
  n_live_tup,
  n_dead_tup,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;  -- 顺序扫描最多的表
```

### pg_stat_user_indexes（索引使用）

```sql
-- 索引使用效率
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan;  -- 低 idx_scan = 可能未使用的索引

-- 索引命中率
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  CASE WHEN idx_tup_read > 0
    THEN round(100.0 * idx_tup_fetch / idx_tup_read, 2)
    ELSE 0
    END as hit_ratio
FROM pg_stat_user_indexes
WHERE idx_scan > 0
ORDER BY hit_ratio;
```

### pg_statio_user_tables（I/O 统计）

```sql
SELECT
  schemaname,
  relname,
  heap_blks_read,   -- 磁盘读取
  heap_blks_hit,    -- 缓存命中
  round(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 2) as cache_hit_ratio,
  idx_blks_read,
  idx_blks_hit,
  toast_blks_read,
  toast_blks_hit
FROM pg_statio_user_tables
WHERE heap_blks_read + heap_blks_hit > 0
ORDER BY heap_blks_read DESC;
```

## 锁监控

```sql
-- 当前锁
SELECT
  l.pid,
  a.usename,
  a.query,
  l.mode,
  l.locktype,
  l.granted,
  l.relation::regclass
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT l.granted
ORDER BY l.pid;

-- 阻塞查询
SELECT
  blocked_locks.pid AS blocked_pid,
  blocked_activity.usename AS blocked_user,
  blocking_locks.pid AS blocking_pid,
  blocking_activity.usename AS blocking_user,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
  AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
  AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
  AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
  AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
  AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
  AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
  AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
  AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
  AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
  AND blocking_locks.pid != blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

## 事务 ID 环绕

```sql
-- 检查到环绕的距离（应 < 10 亿）
SELECT
  datname,
  age(datfrozenxid) as xid_age,
  2147483647 - age(datfrozenxid) as xids_remaining
FROM pg_database
ORDER BY age(datfrozenxid) DESC;

-- 每表环绕状态
SELECT
  schemaname,
  relname,
  age(relfrozenxid) as xid_age,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as size
FROM pg_stat_user_tables
ORDER BY age(relfrozenxid) DESC
LIMIT 20;

-- 防止环绕：VACUUM FREEZE
VACUUM FREEZE;  -- 所有数据库
VACUUM FREEZE users;  -- 特定表
```

## 维护检查清单

**每日：**
- 监控 autovacuum 活动
- 检查长时间运行的查询
- 验证复制延迟（如果适用）
- 检查缓存命中率

**每周：**
- 从 pg_stat_statements 审查慢查询
- 检查表/索引膨胀
- 审查未使用的索引
- 监控磁盘空间使用

**每月：**
- 审查 autovacuum 设置
- 重建频繁更新的索引
- 更新大表的统计信息
- 审查数据库增长趋势

**每季度：**
- 测试备份恢复
- 审查和优化慢查询
- 容量规划
- PostgreSQL 版本更新

## 有用的维护查询

```sql
-- 数据库大小
SELECT
  pg_database.datname,
  pg_size_pretty(pg_database_size(pg_database.datname)) as size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;

-- 最大的表
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
  pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                 pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

-- 按状态的连接数
SELECT
  state,
  count(*) as count
FROM pg_stat_activity
GROUP BY state
ORDER BY count DESC;

-- 重置统计信息（性能测试后）
SELECT pg_stat_reset();
SELECT pg_stat_statements_reset();
```
