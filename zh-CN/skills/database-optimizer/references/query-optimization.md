# 查询优化

## 执行计划分析

### PostgreSQL EXPLAIN ANALYZE

```sql
-- 获取实际执行统计信息
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING)
SELECT u.id, u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > NOW() - INTERVAL '30 days'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5;

-- 需要检查的关键指标：
-- 1. 实际时间 vs 计划时间
-- 2. 行估计 vs 实际行（基数）
-- 3. 缓冲区（共享命中 vs 读取）
-- 4. 顺序扫描 vs 索引扫描
-- 5. 连接方法（嵌套循环、哈希连接、合并连接）
```

### MySQL EXPLAIN

```sql
-- 基本执行计划
EXPLAIN SELECT * FROM orders
WHERE user_id = 123 AND status = 'pending';

-- JSON 格式用于详细分析
EXPLAIN FORMAT=JSON
SELECT u.name, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.created_at > '2024-01-01';

-- 分析实际执行（MySQL 8.0+）
EXPLAIN ANALYZE
SELECT * FROM products
WHERE category_id = 5
ORDER BY price DESC
LIMIT 10;
```

## 查询重写模式

### 消除子查询

```sql
-- 之前（慢 - 为每行执行子查询）
SELECT *
FROM orders o
WHERE total > (
    SELECT AVG(total)
    FROM orders
    WHERE user_id = o.user_id
);

-- 之后（快 - 单次连接加窗口函数）
WITH user_averages AS (
    SELECT user_id, AVG(total) as avg_total
    FROM orders
    GROUP BY user_id
)
SELECT o.*
FROM orders o
INNER JOIN user_averages ua ON o.user_id = ua.user_id
WHERE o.total > ua.avg_total;
```

### 优化连接顺序

```sql
-- 之前（笛卡尔积然后过滤）
SELECT p.name, c.name, s.stock
FROM products p, categories c, stock s
WHERE p.category_id = c.id
  AND p.id = s.product_id
  AND c.active = true;

-- 之后（先过滤，然后连接）
SELECT p.name, c.name, s.stock
FROM categories c
INNER JOIN products p ON p.category_id = c.id
INNER JOIN stock s ON s.product_id = p.id
WHERE c.active = true;
```

### 使用 EXISTS 代替 IN

```sql
-- 之前（慢 - 物化整个子查询）
SELECT * FROM users
WHERE id IN (
    SELECT DISTINCT user_id
    FROM orders
    WHERE total > 1000
);

-- 之后（快 - 首次匹配时短路）
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.id
    AND o.total > 1000
);
```

### 优化 DISTINCT

```sql
-- 之前（排序整个结果集）
SELECT DISTINCT u.email
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';

-- 之后（使用索引实现唯一性）
SELECT u.email
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.id
    AND o.status = 'completed'
);
```

## CTE 优化

### 物化 vs 内联 CTE

```sql
-- PostgreSQL：强制物化以重用
WITH expensive_calculation AS MATERIALIZED (
    SELECT user_id,
           SUM(total) as lifetime_value,
           COUNT(*) as order_count
    FROM orders
    WHERE created_at > NOW() - INTERVAL '1 year'
    GROUP BY user_id
)
SELECT *
FROM expensive_calculation
WHERE lifetime_value > 10000
   OR order_count > 50;

-- 强制内联用于单次使用 CTE
WITH recent_users AS NOT MATERIALIZED (
    SELECT id FROM users
    WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_users;
```

## 窗口函数优化

```sql
-- 之前（多个子查询）
SELECT
    o.id,
    o.total,
    (SELECT MAX(total) FROM orders WHERE user_id = o.user_id) as max_total,
    (SELECT AVG(total) FROM orders WHERE user_id = o.user_id) as avg_total
FROM orders o;

-- 之后（单次窗口函数扫描）
SELECT
    id,
    total,
    MAX(total) OVER (PARTITION BY user_id) as max_total,
    AVG(total) OVER (PARTITION BY user_id) as avg_total
FROM orders;
```

## 聚合策略

### 部分聚合

```sql
-- 对于高基数组，预先聚合
WITH daily_stats AS (
    SELECT
        DATE(created_at) as day,
        user_id,
        COUNT(*) as daily_orders,
        SUM(total) as daily_total
    FROM orders
    WHERE created_at > NOW() - INTERVAL '90 days'
    GROUP BY DATE(created_at), user_id
)
SELECT
    user_id,
    SUM(daily_orders) as total_orders,
    AVG(daily_total) as avg_daily_total
FROM daily_stats
GROUP BY user_id;
```

## 分页优化

```sql
-- 之前（在大偏移量时慢）
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 20 OFFSET 10000;

-- 之后（键集分页 - 基于游标）
SELECT * FROM products
WHERE created_at < '2024-01-01 12:00:00'
   OR (created_at = '2024-01-01 12:00:00' AND id < 12345)
ORDER BY created_at DESC, id DESC
LIMIT 20;

-- 为键集分页创建索引
CREATE INDEX idx_products_pagination
ON products (created_at DESC, id DESC);
```

## 查询模式红旗

| 模式 | 问题 | 解决方案 |
|---------|-------|----------|
| `SELECT *` | 获取不必要的列 | 仅选择所需的列 |
| `OR` 条件 | 阻止索引使用 | 使用 UNION 或单独查询 |
| `LIKE '%term%'` | 全表扫描 | 使用全文搜索或三元组索引 |
| `WHERE DATE(column) = ...` | 函数阻止索引使用 | 使用范围：`column >= '2024-01-01' AND column < '2024-01-02'` |
| 大的 `IN` 列表 | 对于 >100 个项目效率低 | 使用临时表或 JOIN |
| 隐式类型转换 | 阻止索引使用 | 完全匹配列数据类型 |

## 性能验证

```sql
-- PostgreSQL：比较查询性能
EXPLAIN (ANALYZE, BUFFERS)
-- 您的查询在这里

-- 检查缓冲区缓存命中
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;

-- MySQL：检查处理程序统计信息
SHOW STATUS LIKE 'Handler%';
FLUSH STATUS;
-- 运行您的查询
SHOW STATUS LIKE 'Handler%';
```
