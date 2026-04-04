# MySQL 调优

## InnoDB 内存配置

### 缓冲池

```sql
-- 推荐：专用 MySQL 服务器使用系统 RAM 的 70-80%
-- 对于 16GB RAM 服务器：
SET GLOBAL innodb_buffer_pool_size = 12884901888;  -- 12GB

-- 检查缓冲池使用情况
SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_%';

-- 缓冲池命中率（目标：>99%）
SELECT
    (1 - (Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests)) * 100 as hit_ratio
FROM (
    SELECT
        VARIABLE_VALUE as Innodb_buffer_pool_reads
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads'
) reads,
(
    SELECT
        VARIABLE_VALUE as Innodb_buffer_pool_read_requests
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests'
) requests;

-- 缓冲池实例（用于多核系统）
-- 推荐：每 1GB 一个实例，最多 64 个
SET GLOBAL innodb_buffer_pool_instances = 8;
```

### 排序和连接缓冲区

```sql
-- 每个连接的排序缓冲区
SET GLOBAL sort_buffer_size = 2097152;  -- 2MB

-- 用于全连接的连接缓冲区
SET GLOBAL join_buffer_size = 2097152;  -- 2MB

-- 临时表大小
SET GLOBAL tmp_table_size = 67108864;  -- 64MB
SET GLOBAL max_heap_table_size = 67108864;  -- 64MB

-- 监控临时表使用情况
SHOW GLOBAL STATUS LIKE 'Created_tmp%';
```

## 查询缓存（在 8.0 中已弃用）

```sql
-- MySQL 5.7 及更早版本
-- 注意：在 MySQL 8.0 中已移除
SET GLOBAL query_cache_type = 1;
SET GLOBAL query_cache_size = 67108864;  -- 64MB

-- 检查查询缓存有效性
SHOW STATUS LIKE 'Qcache%';

-- 查询缓存命中率
SELECT
    Qcache_hits / (Qcache_hits + Com_select) * 100 as cache_hit_ratio
FROM (
    SELECT VARIABLE_VALUE as Qcache_hits
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Qcache_hits'
) hits,
(
    SELECT VARIABLE_VALUE as Com_select
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Com_select'
) selects;
```

## InnoDB 性能设置

### 日志文件和刷新

```sql
-- InnoDB 日志文件大小（越大 = 更好的写入性能）
-- 推荐：写入密集型工作负载使用 1-2GB
SET GLOBAL innodb_log_file_size = 1073741824;  -- 1GB

-- 日志缓冲区大小
SET GLOBAL innodb_log_buffer_size = 16777216;  -- 16MB

-- 刷新方法（专用服务器使用 O_DIRECT，避免双重缓冲）
-- 在 my.cnf 中设置
innodb_flush_method = O_DIRECT

-- 事务提交时刷新日志
-- 1 = 完整 ACID（默认，最安全）
-- 2 = 写入操作系统缓存，每秒刷新
-- 0 = 每秒写入和刷新（最快，有数据丢失风险）
SET GLOBAL innodb_flush_log_at_trx_commit = 1;

-- 用于复制从库或分析（牺牲安全性换取速度）
SET GLOBAL innodb_flush_log_at_trx_commit = 2;
```

### I/O 配置

```sql
-- 读取 I/O 线程
SET GLOBAL innodb_read_io_threads = 8;

-- 写入 I/O 线程
SET GLOBAL innodb_write_io_threads = 8;

-- I/O 容量（存储可以处理的 IOPS）
-- 对于 SSD：5000-20000
SET GLOBAL innodb_io_capacity = 10000;
SET GLOBAL innodb_io_capacity_max = 20000;

-- 最佳 I/O 刷新方法
-- my.cnf:
innodb_flush_method = O_DIRECT
innodb_flush_neighbors = 0  -- 对于 SSD 禁用
```

### 线程配置

```sql
-- 最大连接数
SET GLOBAL max_connections = 200;

-- 线程缓存（重用线程）
SET GLOBAL thread_cache_size = 100;

-- 检查线程缓存有效性
SHOW STATUS LIKE 'Threads_%';
SHOW STATUS LIKE 'Connections';

-- 线程缓存命中率（目标：>90%）
SELECT
    (1 - (Threads_created / Connections)) * 100 as thread_cache_hit_ratio
FROM (
    SELECT VARIABLE_VALUE as Threads_created
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Threads_created'
) created,
(
    SELECT VARIABLE_VALUE as Connections
    FROM performance_schema.global_status
    WHERE VARIABLE_NAME = 'Connections'
) conns;
```

## 查询优化

### 慢查询日志

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1.0;  -- 记录超过 1 秒的查询
SET GLOBAL log_queries_not_using_indexes = 'ON';

-- 慢查询日志文件位置
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow-query.log';

-- 使用 pt-query-digest 分析慢查询日志
-- $ pt-query-digest /var/log/mysql/slow-query.log

-- 检查慢查询状态
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

### Performance Schema

```sql
-- 启用 performance schema（my.cnf）
performance_schema = ON

-- 按总执行时间排序的顶级查询
SELECT
    DIGEST_TEXT,
    COUNT_STAR as exec_count,
    ROUND(AVG_TIMER_WAIT / 1000000000000, 3) as avg_time_sec,
    ROUND(SUM_TIMER_WAIT / 1000000000000, 3) as total_time_sec,
    ROUND((SUM_TIMER_WAIT / SUM(SUM_TIMER_WAIT) OVER ()) * 100, 2) as pct
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;

-- 全表扫描
SELECT * FROM sys.statements_with_full_table_scans
ORDER BY exec_count DESC
LIMIT 10;

-- 高 I/O 表
SELECT
    object_schema,
    object_name,
    count_read,
    count_write,
    count_fetch,
    SUM_TIMER_WAIT / 1000000000000 as total_latency_sec
FROM performance_schema.table_io_waits_summary_by_table
WHERE object_schema NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

## 索引优化

### 索引统计信息

```sql
-- 更新索引统计信息
ANALYZE TABLE users;

-- 检查索引基数
SHOW INDEX FROM users;

-- 查找重复/冗余索引
SELECT
    a.table_schema,
    a.table_name,
    a.index_name as index1,
    a.column_name,
    b.index_name as index2
FROM information_schema.statistics a
JOIN information_schema.statistics b
    ON a.table_schema = b.table_schema
    AND a.table_name = b.table_name
    AND a.seq_in_index = b.seq_in_index
    AND a.column_name = b.column_name
    AND a.index_name != b.index_name
WHERE a.table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
ORDER BY a.table_schema, a.table_name, a.index_name;

-- 查找未使用的索引
SELECT
    object_schema,
    object_name,
    index_name
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE index_name IS NOT NULL
  AND count_star = 0
  AND object_schema NOT IN ('mysql', 'performance_schema', 'sys')
ORDER BY object_schema, object_name;
```

### 覆盖索引

```sql
-- 创建覆盖索引
CREATE INDEX idx_users_email_name_created
ON users(email, name, created_at);

-- 查询可以使用覆盖索引
EXPLAIN
SELECT name, created_at FROM users WHERE email = 'user@example.com';
-- 在 Extra 列中查找 "Using index"

-- 强制使用索引进行测试
SELECT name FROM users FORCE INDEX (idx_users_email_name_created)
WHERE email = 'user@example.com';
```

## 分区

### 范围分区

```sql
-- 创建分区表
CREATE TABLE events (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_type VARCHAR(50),
    created_at DATETIME NOT NULL,
    data JSON,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);

-- 带分区修剪的查询
EXPLAIN PARTITIONS
SELECT * FROM events
WHERE created_at >= '2024-01-01' AND created_at < '2024-02-01';
-- 应显示 "partitions: p2024"

-- 添加新分区
ALTER TABLE events
ADD PARTITION (PARTITION p2026 VALUES LESS THAN (2027));

-- 删除旧分区（快速删除）
ALTER TABLE events DROP PARTITION p2023;
```

### 列表分区

```sql
-- 按离散值分区
CREATE TABLE orders (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT,
    status VARCHAR(20),
    PRIMARY KEY (id, status)
) PARTITION BY LIST COLUMNS(status) (
    PARTITION p_pending VALUES IN ('pending', 'processing'),
    PARTITION p_completed VALUES IN ('completed', 'shipped'),
    PARTITION p_cancelled VALUES IN ('cancelled', 'refunded')
);
```

## 复制优化

### 二进制日志设置

```sql
-- 二进制日志格式
SET GLOBAL binlog_format = 'ROW';  -- ROW、STATEMENT 或 MIXED

-- 二进制日志缓存大小
SET GLOBAL binlog_cache_size = 1048576;  -- 每个事务 1MB

-- 同步二进制日志（持久性与性能）
SET GLOBAL sync_binlog = 1;  -- 最安全，每次提交后同步
-- sync_binlog = 0  -- 最快，让操作系统处理刷新

-- N 天后过期二进制日志
SET GLOBAL binlog_expire_logs_seconds = 604800;  -- 7 天
```

### 复制延迟监控

```sql
-- 在副本上：检查复制延迟
SHOW SLAVE STATUS\G

-- 解析落后于主服务器的秒数
SELECT
    IF(Slave_IO_Running = 'Yes' AND Slave_SQL_Running = 'Yes',
       Seconds_Behind_Master,
       NULL) as replication_lag_seconds
FROM (SHOW SLAVE STATUS) s;

-- 并行复制（MySQL 8.0+）
SET GLOBAL slave_parallel_workers = 4;
SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK';
```

## 表优化

### 表维护

```sql
-- 优化表（重建，回收空间）
OPTIMIZE TABLE users;

-- 检查表错误
CHECK TABLE users;

-- 修复损坏的表
REPAIR TABLE users;

-- 分析表统计信息
ANALYZE TABLE users;

-- 检查碎片
SELECT
    table_schema,
    table_name,
    ROUND(data_length / 1024 / 1024, 2) as data_mb,
    ROUND(data_free / 1024 / 1024, 2) as free_mb,
    ROUND(data_free / data_length * 100, 2) as fragmentation_pct
FROM information_schema.tables
WHERE table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
  AND data_free > 0
ORDER BY fragmentation_pct DESC;
```

### 表压缩

```sql
-- InnoDB 压缩（需要 ROW_FORMAT=COMPRESSED）
CREATE TABLE compressed_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message TEXT,
    created_at DATETIME
) ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8;

-- 检查压缩比
SELECT
    table_schema,
    table_name,
    ROUND(data_length / 1024 / 1024, 2) as data_mb,
    ROUND(index_length / 1024 / 1024, 2) as index_mb,
    create_options
FROM information_schema.tables
WHERE row_format = 'Compressed';
```

## 配置文件示例

```ini
# my.cnf - 为 16GB RAM 服务器优化的生产配置

[mysqld]
# InnoDB 设置
innodb_buffer_pool_size = 12G
innodb_buffer_pool_instances = 8
innodb_log_file_size = 1G
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 1
innodb_flush_method = O_DIRECT
innodb_flush_neighbors = 0

# I/O 设置
innodb_read_io_threads = 8
innodb_write_io_threads = 8
innodb_io_capacity = 10000
innodb_io_capacity_max = 20000

# 连接设置
max_connections = 200
thread_cache_size = 100

# 查询缓存（MySQL 5.7）
# query_cache_type = 1
# query_cache_size = 64M

# 临时表
tmp_table_size = 64M
max_heap_table_size = 64M

# 慢查询日志
slow_query_log = ON
long_query_time = 1
log_queries_not_using_indexes = ON

# 二进制日志
binlog_format = ROW
sync_binlog = 1
binlog_expire_logs_seconds = 604800

# Performance Schema
performance_schema = ON

# 字符集
character_set_server = utf8mb4
collation_server = utf8mb4_unicode_ci
```
