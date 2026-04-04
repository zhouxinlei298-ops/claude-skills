---
name: sql-pro
description: Optimizes SQL queries, designs database schemas, and troubleshoots performance issues. Use when a user asks why their query is slow, needs help writing complex joins or aggregations, mentions database performance issues, or wants to design or migrate a schema. Invoke for complex queries, window functions, CTEs, indexing strategies, query plan analysis, covering index creation, recursive queries, EXPLAIN/ANALYZE interpretation, before/after query benchmarking, or migrating queries between database dialects (PostgreSQL, MySQL, SQL Server, Oracle).
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: SQL optimization, query performance, database design, PostgreSQL, MySQL, SQL Server, window functions, CTEs, query tuning, EXPLAIN plan, database indexing
  role: specialist
  scope: implementation
  output-format: code
  related-skills: devops-engineer
---

# SQL Pro

## 核心工作流程

1. **模式分析** - 审查数据库结构、索引、查询模式、性能瓶颈
2. **设计** - 使用 CTE、窗口函数、适当的连接创建基于集合的操作
3. **优化** - 分析执行计划，实现覆盖索引，消除全表扫描
4. **验证** - 运行 `EXPLAIN ANALYZE` 并确认大表上没有顺序扫描；如果查询未达到 100ms 以内的目标，则在继续之前迭代索引选择或查询重写
5. **文档化** - 提供查询说明、索引理由、性能指标

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| 查询模式 | `references/query-patterns.md` | JOIN、CTE、子查询、递归查询 |
| 窗口函数 | `references/window-functions.md` | ROW_NUMBER、RANK、LAG/LEAD、分析 |
| 优化 | `references/optimization.md` | EXPLAIN 计划、索引、统计信息、调优 |
| 数据库设计 | `references/database-design.md` | 规范化、键、约束、模式 |
| 方言差异 | `references/dialect-differences.md` | PostgreSQL 与 MySQL 与 SQL Server 的具体差异 |

## 快速参考示例

### CTE 模式
```sql
-- Isolate expensive subquery logic for reuse and readability
WITH ranked_orders AS (
    SELECT
        customer_id,
        order_id,
        total_amount,
        ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS rn
    FROM orders
    WHERE status = 'completed'          -- filter early, before the join
)
SELECT customer_id, order_id, total_amount
FROM ranked_orders
WHERE rn = 1;                           -- latest completed order per customer
```

### 窗口函数模式
```sql
-- Running total and rank within partition — no self-join required
SELECT
    department_id,
    employee_id,
    salary,
    SUM(salary)  OVER (PARTITION BY department_id ORDER BY hire_date) AS running_payroll,
    RANK()       OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank
FROM employees;
```

### EXPLAIN ANALYZE 解读
```sql
-- PostgreSQL: always use ANALYZE to see actual row counts vs. estimates
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT *
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.created_at > NOW() - INTERVAL '30 days';
```
输出中需要检查的关键点：
- **大表上的 Seq Scan** → 添加或修复索引
- **实际行数远大于估计行数** → 运行 `ANALYZE <table>` 刷新统计信息
- **Buffers: shared hit** 与 **read** → 高 `read` 计数表示缺少缓存/索引

### 优化前后示例
```sql
-- BEFORE: correlated subquery, one execution per row (slow)
SELECT order_id,
       (SELECT SUM(quantity) FROM order_items oi WHERE oi.order_id = o.id) AS item_count
FROM orders o;

-- AFTER: single aggregation join (fast)
SELECT o.order_id, COALESCE(agg.item_count, 0) AS item_count
FROM orders o
LEFT JOIN (
    SELECT order_id, SUM(quantity) AS item_count
    FROM order_items
    GROUP BY order_id
) agg ON agg.order_id = o.id;

-- Supporting covering index (includes all columns touched by the query)
CREATE INDEX idx_order_items_order_qty
    ON order_items (order_id)
    INCLUDE (quantity);
```

## 约束

### 必须做
- 在推荐优化方案之前分析执行计划
- 使用基于集合的操作而非逐行处理
- 在查询执行中尽早应用过滤（尽可能在连接之前）
- 存在性检查使用 EXISTS 而非 COUNT
- 在比较和聚合中显式处理 NULL
- 为频繁查询创建覆盖索引
- 使用生产级数据量进行测试

### 不能做
- 在生产查询中使用 SELECT *
- 当基于集合的操作可行时使用游标
- 在针对特定方言时忽略平台特定的优化
- 在不考虑数据量和基数的情况下实现解决方案

## 输出模板

在实现 SQL 解决方案时，请提供：
1. 带有内联注释的优化查询
2. 所需索引及其理由
3. 执行计划分析
4. 性能指标（优化前后）
5. 适用时的平台特定说明
