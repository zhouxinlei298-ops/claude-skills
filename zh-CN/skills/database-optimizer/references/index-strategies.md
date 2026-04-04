# 索引策略

## 索引选择方法

### 识别索引候选

```sql
-- PostgreSQL：查找缺少索引的查询
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
ORDER BY total_exec_time DESC
LIMIT 20;

-- PostgreSQL：查找在大表上的顺序扫描
SELECT schemaname, tablename, seq_scan, seq_tup_read,
       idx_scan, seq_tup_read / seq_scan as avg_seq_tup_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
  AND seq_tup_read / seq_scan > 10000
ORDER BY seq_tup_read DESC;

-- MySQL：检查表扫描
SELECT * FROM sys.statements_with_full_table_scans
WHERE db = 'your_database'
ORDER BY exec_count DESC;
```

## B-Tree 索引（默认）

### 单列索引

```sql
-- 为 WHERE 子句创建索引
CREATE INDEX idx_users_email ON users(email);

-- 为 JOIN 条件创建索引
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 为 ORDER BY 创建索引
CREATE INDEX idx_products_price ON products(price);

-- 唯一约束即索引
CREATE UNIQUE INDEX idx_users_username ON users(username);
```

### 多列索引

```sql
-- 顺序很重要：选择性最高的列在前
CREATE INDEX idx_orders_status_created
ON orders(status, created_at);

-- 适用于以下查询：
-- WHERE status = 'pending'
-- WHERE status = 'pending' AND created_at > '2024-01-01'
-- WHERE status = 'pending' ORDER BY created_at

-- 不适用于：
-- WHERE created_at > '2024-01-01'（未指定 status）

-- 包含常用查询列
CREATE INDEX idx_users_active_email_name
ON users(active, email) INCLUDE (name);
```

### 列顺序指南

```sql
-- 规则 1：等值条件在前，范围条件在后
CREATE INDEX idx_events_type_timestamp
ON events(type, timestamp);  -- type = 'click' AND timestamp > ...

-- 规则 2：高选择性列在前
CREATE INDEX idx_orders_user_status
ON orders(user_id, status);  -- user_id 比 status 选择性更高

-- 规则 3：匹配查询模式
-- 查询：WHERE country = 'US' AND city = 'NYC' AND zip = '10001'
CREATE INDEX idx_locations_country_city_zip
ON locations(country, city, zip);
```

## 覆盖索引

### PostgreSQL INCLUDE 子句

```sql
-- 包含非键列以实现索引只扫描
CREATE INDEX idx_users_email_covering
ON users(email) INCLUDE (name, created_at);

-- 查询可完全从索引满足
EXPLAIN (ANALYZE, BUFFERS)
SELECT name, created_at
FROM users
WHERE email = 'user@example.com';
-- 应显示 "Index Only Scan"
```

### MySQL 覆盖索引

```sql
-- MySQL：在索引末尾添加列
CREATE INDEX idx_orders_user_covering
ON orders(user_id, status, created_at, total);

-- 查询使用覆盖索引
EXPLAIN
SELECT status, created_at, total
FROM orders
WHERE user_id = 123;
-- 应在 Extra 列显示 "Using index"
```

## 部分索引

### PostgreSQL 部分索引

```sql
-- 仅索引活跃用户
CREATE INDEX idx_users_active_email
ON users(email)
WHERE active = true;

-- 仅索引最近的订单
CREATE INDEX idx_orders_recent
ON orders(user_id, created_at)
WHERE created_at > NOW() - INTERVAL '30 days';

-- 仅索引待处理/处理中的订单（忽略已完成）
CREATE INDEX idx_orders_active
ON orders(status, user_id)
WHERE status IN ('pending', 'processing');

-- 更小的索引 = 更好的性能 + 更少的存储
```

### MySQL 过滤索引（8.0+）

```sql
-- MySQL 8.0+ 支持函数索引以实现类似效果
CREATE INDEX idx_users_active
ON users((CASE WHEN active = 1 THEN email END));
```

## 表达式索引

### PostgreSQL 函数索引

```sql
-- 不区分大小写的搜索索引
CREATE INDEX idx_users_email_lower
ON users(LOWER(email));

-- 查询必须匹配表达式
SELECT * FROM users
WHERE LOWER(email) = LOWER('User@Example.com');

-- JSONB 查询索引
CREATE INDEX idx_users_settings_theme
ON users((settings->>'theme'));

SELECT * FROM users
WHERE settings->>'theme' = 'dark';

-- 日期截断索引
CREATE INDEX idx_orders_date
ON orders(DATE(created_at));
```

### MySQL 生成列索引

```sql
-- 创建生成列，然后索引
ALTER TABLE users
ADD COLUMN email_lower VARCHAR(255)
GENERATED ALWAYS AS (LOWER(email)) STORED;

CREATE INDEX idx_users_email_lower
ON users(email_lower);

-- 在查询中使用
SELECT * FROM users
WHERE email_lower = LOWER('User@Example.com');
```

## 专用索引类型

### PostgreSQL GIN 索引（全文搜索、数组、JSONB）

```sql
-- 全文搜索
CREATE INDEX idx_posts_search
ON posts USING GIN(to_tsvector('english', title || ' ' || content));

SELECT * FROM posts
WHERE to_tsvector('english', title || ' ' || content)
      @@ to_tsquery('english', 'database & optimization');

-- 数组搜索
CREATE INDEX idx_products_tags
ON products USING GIN(tags);

SELECT * FROM products
WHERE tags @> ARRAY['electronics', 'sale'];

-- JSONB 搜索
CREATE INDEX idx_users_metadata
ON users USING GIN(metadata);

SELECT * FROM users
WHERE metadata @> '{"plan": "premium"}';
```

### PostgreSQL GiST 索引（几何、范围）

```sql
-- 范围类型
CREATE INDEX idx_events_time_range
ON events USING GIST(time_range);

SELECT * FROM events
WHERE time_range && '[2024-01-01, 2024-01-31]'::tstzrange;

-- PostGIS 几何查询
CREATE INDEX idx_locations_coords
ON locations USING GIST(coordinates);
```

### MySQL 全文索引

```sql
-- 全文搜索
CREATE FULLTEXT INDEX idx_posts_content
ON posts(title, content);

SELECT * FROM posts
WHERE MATCH(title, content)
      AGAINST('database optimization' IN NATURAL LANGUAGE MODE);

-- 布尔模式用于复杂搜索
SELECT * FROM posts
WHERE MATCH(title, content)
      AGAINST('+database -mysql' IN BOOLEAN MODE);
```

## 索引维护

### PostgreSQL 维护

```sql
-- 更新查询计划器统计信息
ANALYZE users;

-- 重建膨胀的索引
REINDEX INDEX CONCURRENTLY idx_users_email;

-- 检查索引膨胀
SELECT
    schemaname, tablename, indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- 查找未使用的索引
SELECT
    schemaname, tablename, indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE 'pg_toast%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### MySQL 维护

```sql
-- 更新统计信息
ANALYZE TABLE users;

-- 重建索引
ALTER TABLE users DROP INDEX idx_users_email, ADD INDEX idx_users_email(email);

-- 检查索引使用情况
SELECT
    object_schema,
    object_name,
    index_name,
    count_star,
    count_read,
    count_fetch
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE object_schema = 'your_database'
ORDER BY count_star DESC;

-- 查找未使用的索引
SELECT
    object_schema,
    object_name,
    index_name
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE index_name IS NOT NULL
  AND count_star = 0
  AND object_schema = 'your_database';
```

## 索引反模式

| 反模式 | 问题 | 解决方案 |
|-------------|-------|----------|
| 索引每列 | 写入开销，存储浪费 | 基于查询模式创建索引 |
| 冗余索引 | `(a)` + `(a,b)` | 只保留 `(a,b)` |
| 列顺序错误 | `(created_at, user_id)` 用于 `WHERE user_id = ?` | 将过滤列放在前面 |
| 过度覆盖 | 包含很少使用的列 | 只包含经常访问的列 |
| 忽略 WHERE 子句 | 为 5% 的数据创建完整索引 | 使用部分索引 |
| 表达式不匹配 | 索引 `email`，查询 `LOWER(email)` | 创建表达式索引 |

## 索引设计检查清单

1. **分析查询**：使用 pg_stat_statements 或慢查询日志
2. **检查执行计划**：查找大表上的 Seq Scan
3. **设计索引**：等值 → 范围 → 包含
4. **并发创建**：避免锁定（PostgreSQL）
5. **验证改进**：比较 EXPLAIN 前后结果
6. **监控使用情况**：30 天后删除未使用的索引
7. **定期维护**：根据需要执行 VACUUM、ANALYZE、REINDEX
