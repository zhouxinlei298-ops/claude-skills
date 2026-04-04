# 分区和缓存

---

## 分区基础

### 为什么分区很重要

- **并行性**：每个分区在单独的任务上运行
- **数据局部性**：最小化跨网络的数据移动
- **内存效率**：合适大小的分区防止 OOM
- **连接性能**：协同分区的数据避免 shuffle

### 分区数量指南

```python
# Rule of thumb: 2-4 partitions per CPU core
# For 100 executor cores: 200-400 partitions

# Check current partitions
print(f"Number of partitions: {df.rdd.getNumPartitions()}")

# Recommended formula
total_cores = num_executors * cores_per_executor
recommended_partitions = total_cores * 2 to 4

# Target partition size: 128MB - 256MB per partition
# For 100GB data with 128MB target: ~800 partitions
```

### 最优分区大小

| 数据量 | 目标分区大小 | 分区数量 |
|-------------|----------------------|-----------------|
| < 1GB | 64MB | 8-16 |
| 1-10GB | 128MB | 8-80 |
| 10-100GB | 128-256MB | 40-800 |
| 100GB-1TB | 256MB | 400-4000 |
| > 1TB | 256MB | 4000+ |

---

## DataFrame 分区

### 重新分区（完全 Shuffle）

```python
from pyspark.sql import functions as F

# Repartition to specific number
df_repart = df.repartition(200)

# Repartition by column(s) - same keys go to same partition
df_repart = df.repartition("user_id")
df_repart = df.repartition("user_id", "date")

# Repartition with count and columns
df_repart = df.repartition(100, "user_id")

# Range partitioning (for sorted access patterns)
df_range = df.repartitionByRange(100, "date")
```

```scala
// Scala repartition
val dfRepart = df.repartition(200)
val dfByCol = df.repartition($"user_id")
val dfRange = df.repartitionByRange(100, $"date")
```

### 合并分区（无 Shuffle）

```python
# Reduce partitions without shuffle - efficient!
# Use after filtering reduces data significantly
df_coalesced = df.coalesce(50)

# Common pattern: filter then coalesce
df_filtered = df.filter(F.col("active") == True)
# If filter reduced data by 80%, reduce partitions too
df_optimized = df_filtered.coalesce(40)  # From 200 to 40
```

**何时使用：**
- `repartition(n)`：增加分区，需要均匀分布，按列分区
- `coalesce(n)`：仅减少分区（无 Shuffle 优势）
- `repartitionByRange()`：需要排序的分区用于范围查询

### 检查分区分布

```python
from pyspark.sql import functions as F

# Check partition count
print(f"Partitions: {df.rdd.getNumPartitions()}")

# Check partition sizes (row counts)
partition_counts = df.withColumn("partition_id", F.spark_partition_id()) \
    .groupBy("partition_id") \
    .count() \
    .orderBy("partition_id")

partition_counts.show()

# Get partition statistics
stats = partition_counts.agg(
    F.min("count").alias("min_rows"),
    F.max("count").alias("max_rows"),
    F.avg("count").alias("avg_rows"),
    F.stddev("count").alias("stddev")
)
stats.show()

# Identify skew: max/avg ratio > 3 indicates skew
```

---

## Shuffle 分区

### 配置

```python
# Default shuffle partitions (200) - often suboptimal
spark.conf.set("spark.sql.shuffle.partitions", 200)

# For small data (<10GB), reduce
spark.conf.set("spark.sql.shuffle.partitions", 50)

# For large data (>100GB), increase
spark.conf.set("spark.sql.shuffle.partitions", 2000)

# Adaptive Query Execution (Spark 3.0+) - dynamic partition sizing
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "64MB")
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128MB")
```

### AQE 自动优化（Spark 3.x）

```python
# Enable full AQE suite
spark.conf.set("spark.sql.adaptive.enabled", "true")

# Auto-coalesce shuffle partitions
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.parallelismFirst", "false")

# Handle skewed partitions automatically
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# Local shuffle reader (avoid remote reads when possible)
spark.conf.set("spark.sql.adaptive.localShuffleReader.enabled", "true")
```

**Spark UI 检查：** 使用 AQE 时，检查 SQL 标签中的"自适应"徽章。在阶段详情中查看合并的分区数。

---

## 缓存和持久化

### 何时缓存

**缓存时：**
- DataFrame 在同一作业中被多次重用
- DataFrame 计算成本高（复杂连接/聚合）
- 迭代算法（ML 训练循环）
- 笔记本中的交互式探索

**不要缓存时：**
- DataFrame 只使用一次
- 数据不适合集群内存
- 源数据已经很快（本地 SSD、列式格式）
- 存储级别导致过多的 GC

### 持久化级别

```python
from pyspark import StorageLevel

# Memory only (default for cache())
df.cache()  # Equivalent to persist(MEMORY_AND_DISK)
df.persist()  # Same as cache()

# Specific storage levels
df.persist(StorageLevel.MEMORY_ONLY)         # Fast, may lose partitions
df.persist(StorageLevel.MEMORY_AND_DISK)     # Spill to disk if needed
df.persist(StorageLevel.MEMORY_ONLY_SER)     # Serialized, less memory, slower
df.persist(StorageLevel.MEMORY_AND_DISK_SER) # Serialized with disk spill
df.persist(StorageLevel.DISK_ONLY)           # Only disk, slowest
df.persist(StorageLevel.OFF_HEAP)            # Off-heap memory

# With replication (for fault tolerance)
df.persist(StorageLevel.MEMORY_AND_DISK_2)   # 2x replication

# Unpersist when done
df.unpersist()
df.unpersist(blocking=True)  # Wait for completion
```

```scala
// Scala persistence
import org.apache.spark.storage.StorageLevel

df.cache()
df.persist(StorageLevel.MEMORY_AND_DISK_SER)
df.unpersist()
```

### 存储级别选择指南

| 存储级别 | 使用场景 |
|---------------|----------|
| MEMORY_ONLY | 内存充足，需要最快访问 |
| MEMORY_AND_DISK | 默认，大多数情况安全 |
| MEMORY_ONLY_SER | 内存受限，CPU 可用 |
| MEMORY_AND_DISK_SER | 大数据，内存受限 |
| DISK_ONLY | 非常大的数据，内存稀缺 |
| OFF_HEAP | 使用 Tungsten 堆外内存 |

### 缓存最佳实践

```python
# Pattern 1: Cache after expensive transformation
expensive_df = source_df \
    .join(lookup_df, "key") \
    .groupBy("category").agg(F.sum("amount"))

expensive_df.cache()

# Trigger caching with action
expensive_df.count()

# Reuse cached data
result1 = expensive_df.filter(F.col("category") == "A")
result2 = expensive_df.filter(F.col("category") == "B")

# Clean up
expensive_df.unpersist()

# Pattern 2: Cache at checkpoint in iterative algorithm
for iteration in range(100):
    df = df.transform(update_function)
    if iteration % 10 == 0:
        df.cache()
        df.count()  # Materialize
        df.unpersist()  # Clean previous

# Pattern 3: Checkpoint to break lineage (long pipelines)
spark.sparkContext.setCheckpointDir("hdfs://path/checkpoints/")
df.checkpoint()  # Truncates lineage, saves to reliable storage
```

### 监控缓存使用情况

```python
# Check if DataFrame is cached
print(df.storageLevel)  # StorageLevel(False, False, False, False, 1) = not cached

# Check storage tab in Spark UI for:
# - Size in Memory
# - Size on Disk
# - Fraction Cached (should be 100%)
```

**Spark UI 检查：** 存储选项卡显示缓存的 RDD/DataFrame。监控"缓存比例"- 如果 < 100%，内存不足。

---

## 广播变量

### 何时使用广播

- 小型查找表（< 200MB）
- 连接到大事实表的维表
- 跨所有任务使用的配置数据
- 避免映射端连接中的 shuffle

### DataFrame 广播连接

```python
from pyspark.sql.functions import broadcast

# Explicit broadcast hint
large_df = spark.read.parquet("s3://bucket/transactions/")  # 100GB
small_df = spark.read.parquet("s3://bucket/categories/")    # 50MB

# Broadcast small table for efficient join
result = large_df.join(broadcast(small_df), "category_id")

# Auto-broadcast threshold configuration
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 100 * 1024 * 1024)  # 100MB

# Disable auto-broadcast (force sort-merge join)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

### RDD 广播变量

```python
# Create broadcast variable
lookup_dict = {"A": 1, "B": 2, "C": 3}
broadcast_lookup = spark.sparkContext.broadcast(lookup_dict)

# Use in transformation
def enrich_with_lookup(row):
    lookup = broadcast_lookup.value
    return Row(
        id=row.id,
        code=row.code,
        value=lookup.get(row.code, 0)
    )

enriched_rdd = df.rdd.map(enrich_with_lookup)

# Clean up
broadcast_lookup.unpersist()
broadcast_lookup.destroy()
```

### 广播大小限制

```python
# Maximum broadcast size (default 8GB, adjustable)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", 200 * 1024 * 1024)  # 200MB

# For larger broadcasts
spark.conf.set("spark.driver.maxResultSize", "4g")

# Monitor broadcast time in Spark UI
# Long broadcast time indicates table too large
```

**警告：** 广播 > 200MB 的表可能导致驱动 OOM 和缓慢广播。改用排序合并连接。

---

## 常见模式的分区策略

### 时间序列数据

```python
# Partition by date for time-range queries
df_partitioned = df.repartition("date")

# Range partition for ordered access
df_range = df.repartitionByRange(365, "date")  # One year

# Write partitioned by date
df.write.partitionBy("year", "month", "day").parquet("s3://bucket/data/")

# Read with partition pruning
df = spark.read.parquet("s3://bucket/data/") \
    .filter(F.col("year") == 2024)  # Only reads 2024 partitions
```

### 用户/实体数据

```python
# Partition by user_id for user-specific queries
df_user_partitioned = df.repartition(1000, "user_id")

# Co-partition for efficient joins
users_partitioned = users.repartition(1000, "user_id")
orders_partitioned = orders.repartition(1000, "user_id")

# Join without shuffle (if partitioners match)
joined = users_partitioned.join(orders_partitioned, "user_id")
```

### 倾斜数据

```python
# Salt skewed keys
salt_buckets = 10

# Add salt to skewed table
salted_df = large_df.withColumn(
    "salted_key",
    F.concat(
        F.col("join_key"),
        F.lit("_"),
        (F.monotonically_increasing_id() % salt_buckets).cast("string")
    )
)

# Explode small table to match
from pyspark.sql.functions import explode, array, lit

small_exploded = small_df.withColumn(
    "salt",
    explode(array([lit(i) for i in range(salt_buckets)]))
).withColumn(
    "salted_key",
    F.concat(F.col("join_key"), F.lit("_"), F.col("salt").cast("string"))
)

# Join on salted key
result = salted_df.join(small_exploded, "salted_key")
```

---

## 文件分区（写入优化）

### Hive 风格分区

```python
# Write with partitioning
df.write \
    .mode("overwrite") \
    .partitionBy("year", "month") \
    .parquet("s3://bucket/data/")

# Result directory structure:
# s3://bucket/data/year=2024/month=01/part-*.parquet
# s3://bucket/data/year=2024/month=02/part-*.parquet

# Read with partition discovery
df = spark.read.parquet("s3://bucket/data/")
# Columns year, month automatically added from path
```

### 分桶（基于哈希的文件分区）

```python
# Write bucketed table for optimized joins
df.write \
    .mode("overwrite") \
    .bucketBy(100, "user_id") \
    .sortBy("timestamp") \
    .saveAsTable("bucketed_orders")

# Read bucketed table
orders = spark.table("bucketed_orders")
users = spark.table("bucketed_users")  # Same bucket count

# Bucket join - no shuffle if buckets match
result = orders.join(users, "user_id")
```

**注意：** 分桶需要 Hive metastore 和 saveAsTable。不适用于直接文件写入。

### 控制输出文件

```python
# Control number of output files
# One file per partition
df.coalesce(1).write.parquet("s3://bucket/output/")

# Multiple files per partition (for large partitions)
df.repartition(100).write.parquet("s3://bucket/output/")

# Max records per file
df.write \
    .option("maxRecordsPerFile", 1000000) \
    .parquet("s3://bucket/output/")
```

---

## Spark UI 分区/缓存分析

### 作业选项卡

- 检查 DAG 中是否显示缓存的数据"(cached)"
- 寻找跳过的阶段（使用缓存数据）

### 阶段选项卡

- **Shuffle 写入大小**：大值表示有重新分区机会
- **Shuffle 读取大小**：应在任务间相似（无倾斜）
- **任务持续时间分布**：方差大表示分区不平衡

### 存储选项卡

- **内存中的大小**：实际缓存大小
- **磁盘上的大小**：溢出大小
- **缓存比例**：如果内存充足，应为 100%

### SQL 选项卡

- 寻找"BroadcastExchange" - 表示广播连接
- 寻找"ShuffleExchange" - 表示数据移动
- 检查每个阶段的"输出行数"以了解数据流

---

## 常见反模式

```python
# BAD: Caching without measuring benefit
for table in all_tables:
    spark.read.parquet(table).cache()  # Wastes memory

# GOOD: Cache only if reused
expensive_df.cache()
result1 = expensive_df.groupBy("a").count()
result2 = expensive_df.groupBy("b").count()
expensive_df.unpersist()

# BAD: Too many small partitions
df.repartition(10000)  # Creates scheduling overhead

# GOOD: Right-size partitions (128MB-256MB each)
df.repartition(100)

# BAD: Too few partitions for large data
df.coalesce(1)  # Single partition can't parallelize

# GOOD: Maintain parallelism
df.coalesce(max(1, target_size))

# BAD: Repartition before filter
df.repartition(1000).filter(F.col("active") == True)  # Shuffles then filters

# GOOD: Filter then coalesce
df.filter(F.col("active") == True).coalesce(100)  # Filter first, then resize

# BAD: Broadcasting large table
result = large.join(broadcast(also_large), "key")  # OOM risk

# GOOD: Let Spark decide or use sort-merge
result = large.join(also_large, "key")  # Sort-merge join
```

---

## 最佳实践总结

1. **目标 128-256MB 分区** - 不要太小（开销）或太大（OOM）
2. **每个核心使用 2-4 个分区** - 最大化并行性
3. **在 Spark 3.x 中启用 AQE** - 自动分区优化
4. **只缓存重用的 DataFrame** - 缓存前衡量
5. **使用 MEMORY_AND_DISK** - 安全的默认存储级别
6. **广播 < 200MB 的表** - 避免小型维表的 shuffle
7. **过滤后合并** - 数据减少时减少分区
8. **连接前重新分区** - 协同分区相关表
9. **按过滤列写入分区** - 启用分区修剪
10. **监控存储选项卡** - 确保缓存适合内存