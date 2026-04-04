# 性能优化

## EXPLAIN ANALYZE 基础

```sql
-- 基本 EXPLAIN ANALYZE
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT u.id, u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name;

-- 需要观察的关键指标：
-- Planning Time：创建查询计划所花费的时间
-- Execution Time：实际查询执行时间
-- Shared Hit Blocks：在缓存中找到的数据（好）
-- Shared Read Blocks：从磁盘读取的数据（慢）
-- Rows：估计的 vs 实际的行数
```

## 阅读 EXPLAIN 输出

```
Seq Scan on users  (cost=0.00..1234.56 rows=10000 width=32)
                    ^^^^^^^^^^^^^^^^^^^^  ^^^^^^     ^^^^^^^^
                    启动..总成本        估计       行宽度

Actual time: 0.123..45.678 rows=9876 loops=1
             ^^^^^^^^^^^^^^^  ^^^^^^^^  ^^^^^^^
             首行..末行时间     实际      迭代次数
```

**节点类型（从快到慢）：**
- Index Only Scan - 最佳，仅从索引获取数据
- Index Scan - 好，使用索引 + 堆查找
- Bitmap Index Scan - 好，适用于多个条件
- Seq Scan - 表扫描，对于小表可以
- 大表上的 Seq Scan - 问题，需要索引

## 索引策略

### B-tree 索引（默认）

```sql
-- 单列索引
CREATE INDEX idx_users_email ON users(email);

-- 多列索引（顺序很重要！）
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);
-- 适用于：WHERE user_id = X ORDER BY created_at DESC
-- 适用于：WHERE user_id = X AND created_at > Y
-- 不适用于：WHERE created_at > Y（不使用索引）

-- 部分索引（更小、更快）
CREATE INDEX idx_active_users ON users(email) WHERE active = true;

-- 表达式索引
CREATE INDEX idx_users_lower_email ON users(LOWER(email));
-- 启用：WHERE LOWER(email) = 'user@example.com'

-- 覆盖索引（包含额外列）
CREATE INDEX idx_orders_covering ON orders(user_id) INCLUDE (total, created_at);
-- 启用 Index Only Scan
```

### GIN 索引（JSONB、数组、全文）

```sql
-- JSONB 包含
CREATE INDEX idx_data_gin ON documents USING GIN(data);
-- 启用：WHERE data @> '{"status": "active"}'

-- JSONB 特定路径
CREATE INDEX idx_data_status ON documents USING GIN((data -> 'status'));

-- 数组操作
CREATE INDEX idx_tags_gin ON posts USING GIN(tags);
-- 启用：WHERE tags @> ARRAY['postgresql', 'performance']

-- 全文搜索
CREATE INDEX idx_content_fts ON articles USING GIN(to_tsvector('english', content));
-- 启用：WHERE to_tsvector('english', content) @@ to_tsquery('postgresql & performance')
```

### GiST 索引（空间、范围、最近邻）

```sql
-- PostGIS 空间索引
CREATE INDEX idx_locations_geom ON locations USING GIST(geom);
-- 启用：WHERE ST_DWithin(geom, point, 1000)

-- 范围类型
CREATE INDEX idx_bookings_range ON bookings USING GIST(during);
-- 启用：WHERE during && '[2024-01-01, 2024-01-31]'::daterange

-- 最近邻（KNN）
CREATE INDEX idx_locations_gist ON locations USING GIST(coordinates);
-- 启用：ORDER BY coordinates <-> point('0,0') LIMIT 10
```

### BRIN 索引（大型、自然有序的表）

```sql
-- 时序数据（仅插入、按时间排序）
CREATE INDEX idx_metrics_time_brin ON metrics USING BRIN(timestamp);
-- 非常小的索引，适用于 WHERE timestamp > NOW() - INTERVAL '1 day'

-- 适用于：
-- - 日志表
-- - 时序指标
-- - 具有自然顺序的仅追加表
```

## 统计信息和计划器

```sql
-- 更新统计信息（批量更改后执行）
ANALYZE users;
ANALYZE;  -- 所有表

-- 检查统计信息新鲜度
SELECT schemaname, tablename, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- 为高基数列增加统计目标
ALTER TABLE users ALTER COLUMN email SET STATISTICS 1000;
-- 默认为 100，增加以获得更好的选择性估计

-- 查看列统计信息
SELECT * FROM pg_stats WHERE tablename = 'users' AND attname = 'email';
```

## 查询优化模式

### 问题：大表上的顺序扫描

```sql
-- 不好：全表扫描
SELECT * FROM orders WHERE user_id = 123;
-- 解决方案：添加索引
CREATE INDEX idx_orders_user ON orders(user_id);
```

### 问题：索引未使用

```sql
-- 不好：函数阻止索引使用
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';
-- 解决方案：表达式索引
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

-- 不好：隐式类型转换
SELECT * FROM users WHERE id = '123';  -- id 是整数
-- 解决方案：使用正确类型
SELECT * FROM users WHERE id = 123;
```

### 问题：大型 JOIN 低效

```sql
-- 不好：大表上的嵌套循环
EXPLAIN ANALYZE
SELECT * FROM orders o JOIN users u ON o.user_id = u.id;

-- 解决方案：
-- 1. 确保 JOIN 列上有索引
CREATE INDEX idx_orders_user ON orders(user_id);
-- 2. 更新统计信息
ANALYZE orders, users;
-- 3. 如果哈希连接更好，增加 work_mem
SET work_mem = '256MB';
```

### 问题：COUNT(*) 慢

```sql
-- 不好：全表扫描
SELECT COUNT(*) FROM orders WHERE status = 'pending';

-- 解决方案：
-- 1. 部分索引
CREATE INDEX idx_orders_pending ON orders(id) WHERE status = 'pending';

-- 2. 大表的近似计数
SELECT reltuples::bigint FROM pg_class WHERE relname = 'orders';

-- 3. 报告的物化计数
CREATE MATERIALIZED VIEW order_counts AS
SELECT status, COUNT(*) FROM orders GROUP BY status;
CREATE UNIQUE INDEX ON order_counts(status);
REFRESH MATERIALIZED VIEW CONCURRENTLY order_counts;
```

## 连接池

```sql
-- 检查活跃连接
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- 达到连接限制？使用 pgBouncer
-- pgbouncer.ini:
-- [databases]
-- mydb = host=localhost port=5432 dbname=mydb
-- [pgbouncer]
-- pool_mode = transaction
-- max_client_conn = 1000
-- default_pool_size = 25
```

## 配置调优

```sql
-- 内存设置（对于 16GB RAM 服务器）
shared_buffers = 4GB           -- RAM 的 25%
effective_cache_size = 12GB    -- RAM 的 75%
work_mem = 64MB                -- 每个操作
maintenance_work_mem = 1GB     -- 用于 VACUUM、CREATE INDEX

-- 检查点调优
checkpoint_completion_target = 0.9
wal_buffers = 16MB
checkpoint_timeout = 10min

-- 查询计划器
random_page_cost = 1.1         -- SSD 更低（默认 4.0 适用于 HDD）
effective_io_concurrency = 200 -- SSD 更高

-- 并行性（Postgres 10+）
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

## 性能监控

```sql
-- 慢查询（需要 pg_stat_statements）
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time,
  stddev_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 缓存命中率（应 > 99%）
SELECT
  sum(blks_hit) * 100.0 / sum(blks_hit + blks_read) as cache_hit_ratio
FROM pg_stat_database;

-- 索引使用
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%pkey';  -- 未使用的索引
```
