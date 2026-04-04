# Spark SQL 和 DataFrame API

---

## 何时使用 DataFrame vs RDD

**使用 DataFrame 时：**
- 处理结构化或半结构化数据（JSON、Parquet、CSV、Avro）
- 执行类 SQL 操作（连接、聚合、过滤）
- 需要 Catalyst 优化器优势（谓词下推、列修剪）
- 使用列式格式以获得更好的压缩

**使用 RDD 时：**
- 需要精细控制物理数据分布
- 处理非结构化数据（文本处理、自定义二进制格式）
- 实现自定义分区逻辑
- 遗留代码迁移（尽可能使用 DataFrame 迁移）

---

## 模式定义

### 显式模式（生产必需）

```python
# PySpark - Explicit schema definition
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, TimestampType, ArrayType, MapType
)

# Define schema explicitly - ALWAYS do this in production
user_schema = StructType([
    StructField("user_id", StringType(), nullable=False),
    StructField("name", StringType(), nullable=True),
    StructField("age", IntegerType(), nullable=True),
    StructField("email", StringType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("tags", ArrayType(StringType()), nullable=True),
    StructField("metadata", MapType(StringType(), StringType()), nullable=True)
])

# Read with explicit schema - no inference overhead
df = spark.read.schema(user_schema).json("s3://bucket/users/")
```

```scala
// Scala - Explicit schema definition
import org.apache.spark.sql.types._

val userSchema = StructType(Seq(
  StructField("user_id", StringType, nullable = false),
  StructField("name", StringType, nullable = true),
  StructField("age", IntegerType, nullable = true),
  StructField("email", StringType, nullable = true),
  StructField("created_at", TimestampType, nullable = false),
  StructField("tags", ArrayType(StringType), nullable = true),
  StructField("metadata", MapType(StringType, StringType), nullable = true)
))

val df = spark.read.schema(userSchema).json("s3://bucket/users/")
```

### 模式推断陷阱

```python
# AVOID in production - causes full data scan
df = spark.read.json("s3://bucket/users/")  # Infers schema - slow!

# If you must infer, sample a small portion
df = spark.read.option("samplingRatio", 0.01).json("s3://bucket/users/")
```

---

## 列操作和表达式

### 内置函数（始终优先于 UDF）

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Column transformations - use built-in functions
df = df.withColumn("name_upper", F.upper(F.col("name")))
df = df.withColumn("email_domain", F.split(F.col("email"), "@")[1])
df = df.withColumn("age_group",
    F.when(F.col("age") < 18, "minor")
     .when(F.col("age") < 65, "adult")
     .otherwise("senior")
)

# Date/time operations
df = df.withColumn("year", F.year("created_at"))
df = df.withColumn("date_str", F.date_format("created_at", "yyyy-MM-dd"))
df = df.withColumn("days_since", F.datediff(F.current_date(), "created_at"))

# Array operations
df = df.withColumn("first_tag", F.col("tags")[0])
df = df.withColumn("tag_count", F.size("tags"))
df = df.withColumn("has_premium", F.array_contains("tags", "premium"))

# Null handling
df = df.withColumn("name_clean", F.coalesce("name", F.lit("Unknown")))
df = df.filter(F.col("email").isNotNull())
```

### 窗口函数

```python
from pyspark.sql.window import Window
from pyspark.sql import functions as F

# Define window specifications
user_window = Window.partitionBy("user_id").orderBy("created_at")
category_window = Window.partitionBy("category")

# Ranking functions
df = df.withColumn("row_num", F.row_number().over(user_window))
df = df.withColumn("rank", F.rank().over(user_window))
df = df.withColumn("dense_rank", F.dense_rank().over(user_window))

# Analytic functions
df = df.withColumn("prev_value", F.lag("amount", 1).over(user_window))
df = df.withColumn("next_value", F.lead("amount", 1).over(user_window))
df = df.withColumn("running_total", F.sum("amount").over(user_window))

# Aggregations over windows
df = df.withColumn("category_avg", F.avg("amount").over(category_window))
df = df.withColumn("category_max", F.max("amount").over(category_window))

# Rolling windows
rolling_7day = Window.partitionBy("user_id") \
    .orderBy(F.col("created_at").cast("long")) \
    .rangeBetween(-7*86400, 0)  # 7 days in seconds

df = df.withColumn("rolling_7d_sum", F.sum("amount").over(rolling_7day))
```

```scala
// Scala window functions
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._

val userWindow = Window.partitionBy("user_id").orderBy("created_at")
val categoryWindow = Window.partitionBy("category")

val result = df
  .withColumn("row_num", row_number().over(userWindow))
  .withColumn("running_total", sum("amount").over(userWindow))
  .withColumn("category_avg", avg("amount").over(categoryWindow))
```

---

## Spark SQL 查询

### 将 DataFrame 注册为视图

```python
# Temporary view - session scoped
df.createOrReplaceTempView("users")

# Global temporary view - application scoped
df.createOrReplaceGlobalTempView("users")
# Access via: global_temp.users

# Execute SQL
result = spark.sql("""
    SELECT
        user_id,
        name,
        COUNT(*) as order_count,
        SUM(amount) as total_spent
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    WHERE u.created_at >= '2024-01-01'
    GROUP BY user_id, name
    HAVING total_spent > 1000
    ORDER BY total_spent DESC
""")
```

### CTE 和子查询

```python
result = spark.sql("""
    WITH user_stats AS (
        SELECT
            user_id,
            COUNT(*) as order_count,
            SUM(amount) as total_spent,
            AVG(amount) as avg_order
        FROM orders
        WHERE order_date >= '2024-01-01'
        GROUP BY user_id
    ),
    ranked_users AS (
        SELECT
            *,
            PERCENT_RANK() OVER (ORDER BY total_spent) as spend_percentile
        FROM user_stats
    )
    SELECT *
    FROM ranked_users
    WHERE spend_percentile >= 0.9
""")
```

---

## 连接策略

### 连接类型和何时使用

```python
# Inner join - matching records only
result = orders.join(users, orders.user_id == users.user_id, "inner")

# Left outer - all from left, matching from right
result = orders.join(users, "user_id", "left")

# Right outer - all from right, matching from left
result = orders.join(users, "user_id", "right")

# Full outer - all records from both
result = orders.join(users, "user_id", "full")

# Left anti - records in left NOT in right
new_users = all_users.join(existing_users, "user_id", "left_anti")

# Left semi - records in left that have match in right (no columns from right)
active_users = users.join(orders, "user_id", "left_semi")

# Cross join - cartesian product (use carefully!)
result = df1.crossJoin(df2)
```

### 广播连接（小表优化）

```python
from pyspark.sql.functions import broadcast

# Explicit broadcast hint - join small table to large table
# Broadcasts entire small_df to all executors (must fit in memory)
result = large_df.join(broadcast(small_df), "join_key")

# Auto broadcast threshold (default 10MB)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 200 * 1024 * 1024)  # 200MB

# Disable auto broadcast for specific query
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

**Spark UI 检查:** 在 SQL 标签中，查找 "BroadcastHashJoin" vs "SortMergeJoin"。广播应显示快速交换，而排序合并显示 shuffle。

### 处理倾斜连接（Spark 3.x AQE）

```python
# Enable Adaptive Query Execution (Spark 3.0+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# Manual skew handling with salting
from pyspark.sql.functions import monotonically_increasing_id, explode, array, lit

# Add salt to skewed key in large table
salt_count = 10
large_df_salted = large_df.withColumn(
    "join_key_salted",
    F.concat(F.col("join_key"), F.lit("_"), (F.monotonically_increasing_id() % salt_count).cast("string"))
)

# Explode small table to match salted keys
small_df_exploded = small_df.withColumn(
    "salt", F.explode(F.array([F.lit(i) for i in range(salt_count)]))
).withColumn(
    "join_key_salted",
    F.concat(F.col("join_key"), F.lit("_"), F.col("salt").cast("string"))
)

# Join on salted key
result = large_df_salted.join(small_df_exploded, "join_key_salted")
```

---

## 聚合

### GroupBy 操作

```python
from pyspark.sql import functions as F

# Basic aggregations
stats = df.groupBy("category").agg(
    F.count("*").alias("count"),
    F.sum("amount").alias("total"),
    F.avg("amount").alias("average"),
    F.min("amount").alias("minimum"),
    F.max("amount").alias("maximum"),
    F.stddev("amount").alias("std_dev"),
    F.countDistinct("user_id").alias("unique_users"),
    F.collect_list("product_id").alias("products"),  # Caution: can OOM
    F.collect_set("product_id").alias("unique_products")
)

# Multiple grouping sets (Spark SQL)
result = spark.sql("""
    SELECT
        category,
        region,
        SUM(amount) as total
    FROM sales
    GROUP BY GROUPING SETS (
        (category, region),
        (category),
        (region),
        ()
    )
""")

# Equivalent with rollup/cube
rollup_df = df.rollup("category", "region").agg(F.sum("amount"))
cube_df = df.cube("category", "region").agg(F.sum("amount"))
```

### 透视表

```python
# Pivot - turn row values into columns
pivot_df = df.groupBy("user_id").pivot("category", ["electronics", "clothing", "food"]) \
    .agg(F.sum("amount"))

# Result columns: user_id, electronics, clothing, food

# Unpivot (melt) - turn columns into rows
from pyspark.sql.functions import expr

unpivot_df = pivot_df.select(
    "user_id",
    expr("stack(3, 'electronics', electronics, 'clothing', clothing, 'food', food) as (category, amount)")
).filter("amount is not null")
```

---

## Catalyst 优化器技巧

### 谓词下推

```python
# Good - filter pushed down to data source
df = spark.read.parquet("s3://bucket/data/").filter(F.col("date") == "2024-01-01")

# Check physical plan for PushedFilters
df.explain(True)
```

### 列修剪

```python
# Good - only read required columns
df = spark.read.parquet("s3://bucket/data/").select("id", "name", "amount")

# Bad - reads all columns then filters
df = spark.read.parquet("s3://bucket/data/")
result = df.select("id", "name", "amount")
```

### 分区修剪

```python
# Data partitioned by date
# Good - only reads matching partitions
df = spark.read.parquet("s3://bucket/data/") \
    .filter(F.col("date").between("2024-01-01", "2024-01-31"))

# Verify partition pruning in Spark UI - Files Read should be reduced
```

---

## 常见反模式

### 避免这些模式

```python
# BAD: Using Python UDF when built-in exists
from pyspark.sql.functions import udf
@udf("string")
def upper_udf(s):
    return s.upper() if s else None
df.withColumn("name", upper_udf("name"))  # 10-100x slower!

# GOOD: Use built-in function
df.withColumn("name", F.upper("name"))

# BAD: Collect large data to driver
all_data = df.collect()  # OOM risk!
for row in all_data:
    process(row)

# GOOD: Process distributed or use take/limit
sample = df.take(100)  # Small sample
df.foreach(process_partition)  # Distributed processing

# BAD: Multiple actions triggering recomputation
count = df.count()
total = df.agg(F.sum("amount")).collect()
# Two full scans of data!

# GOOD: Cache if multiple actions needed
df.cache()
count = df.count()
total = df.agg(F.sum("amount")).collect()
df.unpersist()

# BAD: String column used in filter (case sensitivity issues)
df.filter(df.status == "ACTIVE")  # May miss "active", "Active"

# GOOD: Normalize or use case-insensitive comparison
df.filter(F.upper("status") == "ACTIVE")
```

---

## DataFrame 的 Spark UI 分析

### SQL 标签指标监控

1. **持续时间** - 长阶段表示优化机会
2. **输入大小** - 验证分区修剪减少了数据读取
3. **Shuffle 读/写** - 大 shuffle 表示连接/聚合问题
4. **溢出（内存/磁盘）** - 表示内存压力，增加 executor 内存

### 物理计划分析

```python
# View physical plan
df.explain(True)

# Look for:
# - FileScan with PushedFilters (predicate pushdown working)
# - BroadcastHashJoin vs SortMergeJoin (broadcast optimization)
# - Exchange (shuffle operations)
# - WholeStageCodegen (Tungsten optimization active)
```

### 阶段标签中的关键指标

| 指标 | 健康范围 | 高时的操作 |
|------|----------|-----------|
| Shuffle 读大小 | 每个 task < 1GB | 增加分区，添加过滤 |
| 溢出（磁盘） | 0 | 增加 executor 内存 |
| GC 时间 | < 任务时间的 10% | 调优内存比例 |
| 任务持续时间方差 | < 中位数的 2 倍 | 处理数据倾斜 |

---

## 最佳实践总结

1. **始终定义显式模式** - 生产中不使用推断
2. **使用内置函数** - 可能时避免 UDF
3. **广播小表** - 200MB 以下的表
4. **早期过滤** - 在连接和聚合前推送过滤
5. **只选择需要的列** - 启用列修剪
6. **按常用过滤列分区** - 启用分区修剪
7. **战略性缓存** - 只缓存被重用的 DataFrame
8. **监控 Spark UI** - 检查 shuffle、溢出和 GC 指标
9. **在 Spark 3.x 中启用 AQE** - 倾斜和分区的自动优化
10. **使用生产数据量测试** - 性能随规模变化

```