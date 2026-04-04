# 性能调优

---

## 集群大小配置

### Executor 配置

```python
# Key executor configurations
spark.conf.set("spark.executor.instances", 10)      # Number of executors
spark.conf.set("spark.executor.cores", 4)           # Cores per executor
spark.conf.set("spark.executor.memory", "16g")      # Memory per executor

# Dynamic allocation (recommended for varying workloads)
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", 2)
spark.conf.set("spark.dynamicAllocation.maxExecutors", 100)
spark.conf.set("spark.dynamicAllocation.executorIdleTimeout", "60s")
```

### 大小指导原则

| 集群大小 | Executor 内存 | Executor 核心 | 实例数 |
|----------|---------------|---------------|--------|
| 小型（开发） | 4-8GB | 2-4 | 2-5 |
| 中型 | 8-16GB | 4-5 | 10-50 |
| 大型 | 16-32GB | 5-8 | 50-200 |
| 超大型 | 32-64GB | 8-16 | 200+ |

**经验法则：**
- 每个 executor 5 个核心最优（避免 HDFS I/O 瓶颈）
- 每个节点留 1 个核心给 OS/YARN
- 每个节点留 1GB 给开销
- executor.memoryOverhead = max(384MB, executor.memory 的 10%)

### 内存配置

```python
# Executor memory breakdown
spark.conf.set("spark.executor.memory", "16g")
spark.conf.set("spark.executor.memoryOverhead", "2g")  # For off-heap, network buffers

# Memory fractions (default values usually good)
spark.conf.set("spark.memory.fraction", 0.6)           # Unified memory pool
spark.conf.set("spark.memory.storageFraction", 0.5)    # Cache vs execution split

# Off-heap memory (for large data)
spark.conf.set("spark.memory.offHeap.enabled", "true")
spark.conf.set("spark.memory.offHeap.size", "8g")
```

---

## Shuffle 优化

### Shuffle 配置

```python
# Number of shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", 200)  # Adjust based on data size

# Shuffle behavior
spark.conf.set("spark.shuffle.compress", "true")              # Compress shuffle data
spark.conf.set("spark.shuffle.spill.compress", "true")        # Compress spill data
spark.conf.set("spark.io.compression.codec", "lz4")           # Fast compression

# Shuffle file management
spark.conf.set("spark.shuffle.file.buffer", "64k")            # Buffer for shuffle writes
spark.conf.set("spark.shuffle.io.maxRetries", 3)              # Retry failed fetches
spark.conf.set("spark.shuffle.io.retryWait", "5s")            # Wait between retries

# Sort-based shuffle (default in Spark 2.0+)
spark.conf.set("spark.shuffle.sort.bypassMergeThreshold", 200)
```

### 减少 Shuffle 大小

```python
from pyspark.sql import functions as F

# 1. Filter before join/aggregation
df_filtered = df.filter(F.col("date") >= "2024-01-01")
result = df_filtered.groupBy("category").count()

# 2. Use broadcast for small tables
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")  # No shuffle for small_df

# 3. Select only needed columns before shuffle
df_slim = df.select("key", "value")  # Not all 50 columns
result = df_slim.groupBy("key").sum("value")

# 4. Use reduceByKey over groupByKey (RDD)
# BAD: groupByKey shuffles all values
counts = rdd.groupByKey().mapValues(len)
# GOOD: reduceByKey combines locally first
counts = rdd.map(lambda x: (x, 1)).reduceByKey(lambda a, b: a + b)

# 5. Coalesce after filter reduces data
df_filtered = df.filter(condition).coalesce(50)  # Reduce partitions without shuffle
```

### Spark UI Shuffle 指标

在阶段标签中检查：
- **Shuffle 写大小**: 为 shuffle 写入的总数据量
- **Shuffle 读大小**: 从 shuffle 读取的总数据量
- **Shuffle 读阻塞时间**: 等待 shuffle 数据的时间
- **Shuffle 溢出（内存）**: 溢出到内存的数据
- **Shuffle 溢出（磁盘）**: 溢出到磁盘的数据（坏，增加内存）

---

## 数据倾斜处理

### 识别倾斜

```python
from pyspark.sql import functions as F

# Check key distribution
key_counts = df.groupBy("join_key").count()
key_counts.orderBy(F.desc("count")).show(20)

# Summary statistics
stats = key_counts.agg(
    F.min("count").alias("min"),
    F.max("count").alias("max"),
    F.avg("count").alias("avg"),
    F.percentile_approx("count", 0.99).alias("p99")
)
stats.show()

# Skew ratio: max/avg > 10 indicates severe skew
```

**Spark UI 指标：**
- 少数任务比其他任务花费时间长得多
- 任务持续时间直方图显示长尾
- 某些分区比其他分区大得多

### 倾斜解决方案

#### 1. 自适应查询执行（Spark 3.x）

```python
# Enable AQE skew handling
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", 5)
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")

# AQE will automatically split skewed partitions
result = large_df.join(another_df, "key")
```

#### 2. 加盐技术

```python
from pyspark.sql import functions as F

# Identify skewed keys
skewed_keys = ["NULL", "UNKNOWN", "DEFAULT"]
salt_buckets = 20

# Salt the skewed keys in large table
large_salted = large_df.withColumn(
    "salted_key",
    F.when(
        F.col("join_key").isin(skewed_keys),
        F.concat(F.col("join_key"), F.lit("_"), (F.rand() * salt_buckets).cast("int").cast("string"))
    ).otherwise(F.col("join_key"))
)

# Explode small table for skewed keys only
from pyspark.sql.functions import explode, array, lit, when

small_exploded = small_df.withColumn(
    "salted_key",
    F.when(
        F.col("join_key").isin(skewed_keys),
        F.explode(F.array([F.concat(F.col("join_key"), F.lit("_"), F.lit(i)) for i in range(salt_buckets)]))
    ).otherwise(F.col("join_key"))
)

# Join on salted key
result = large_salted.join(small_exploded, "salted_key")
```

#### 3. 倾斜键的广播连接

```python
from pyspark.sql.functions import broadcast

# Separate skewed and non-skewed data
skewed_keys = ["NULL", "UNKNOWN"]

large_skewed = large_df.filter(F.col("join_key").isin(skewed_keys))
large_normal = large_df.filter(~F.col("join_key").isin(skewed_keys))

small_skewed = small_df.filter(F.col("join_key").isin(skewed_keys))
small_normal = small_df.filter(~F.col("join_key").isin(skewed_keys))

# Broadcast join for skewed (small result expected)
result_skewed = large_skewed.join(broadcast(small_skewed), "join_key")

# Regular join for non-skewed
result_normal = large_normal.join(small_normal, "join_key")

# Union results
final_result = result_skewed.union(result_normal)
```

#### 4. 大倾斜键的迭代广播

```python
# For extremely skewed single keys
skewed_key_value = "NULL"

# Process skewed key separately with broadcast
skewed_large = large_df.filter(F.col("join_key") == skewed_key_value)
skewed_small = small_df.filter(F.col("join_key") == skewed_key_value)
result_skewed = skewed_large.crossJoin(broadcast(skewed_small))

# Process rest normally
normal_large = large_df.filter(F.col("join_key") != skewed_key_value)
normal_small = small_df.filter(F.col("join_key") != skewed_key_value)
result_normal = normal_large.join(normal_small, "join_key")

# Combine
final = result_skewed.union(result_normal)
```

---

## 内存调优

### 内存压力症状

| 症状 | 原因 | 解决方案 |
|------|------|----------|
| 长时间 GC 暂停 | 缓存数据太多 | 减少缓存，使用序列化存储 |
| 溢出到磁盘 | 分区太大 | 增加分区，添加内存 |
| 驱动程序 OOM | 大 collect/广播 | 减少到驱动程序的数据 |
| Executor OOM | 大分区 | 重新分区，增加内存 |

### 垃圾回收调优

```python
# GC options (set via spark-submit --conf)
# For executor JVM
spark.conf.set("spark.executor.extraJavaOptions",
    "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35 -XX:ConcGCThreads=4")

# For driver JVM
spark.conf.set("spark.driver.extraJavaOptions",
    "-XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=35")

# Monitor GC in Spark UI
# Executors tab shows GC Time for each executor
# Target: GC Time < 10% of total task time
```

### 减少内存压力

```python
# 1. Use serialized caching
from pyspark import StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK_SER)

# 2. Kryo serialization (faster, more compact)
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

# 3. Avoid UDFs that create objects
# BAD: Creates Python objects
@udf("string")
def process(x):
    return x.upper()  # String allocation

# GOOD: Use built-in
df.withColumn("upper", F.upper("column"))

# 4. Use mapPartitions with generators
def efficient_process(iterator):
    for row in iterator:
        yield transform(row)  # No list allocation

result = df.rdd.mapPartitions(efficient_process)

# 5. Release cached data promptly
df.unpersist()
```

### Driver 内存问题

```python
# Increase driver memory
spark.conf.set("spark.driver.memory", "8g")
spark.conf.set("spark.driver.maxResultSize", "4g")

# Avoid large collects
# BAD
all_data = df.collect()  # Pulls everything to driver

# GOOD
sample = df.take(1000)  # Small sample
df.write.parquet("s3://output/")  # Write distributed
```

---

## 连接优化

### 连接策略选择

```python
# Broadcast Hash Join - small table (< 200MB)
from pyspark.sql.functions import broadcast
result = large.join(broadcast(small), "key")

# Sort Merge Join - large tables, equi-join
# Default for non-broadcast joins
result = large1.join(large2, "key")

# Shuffle Hash Join - medium tables, memory-constrained
spark.conf.set("spark.sql.join.preferSortMergeJoin", "false")

# Cartesian Product - cross join (avoid if possible)
result = df1.crossJoin(df2)

# Bucket Join - pre-bucketed tables (no shuffle)
# Requires saveAsTable with bucketBy
```

### 连接提示（Spark 3.0+）

```python
# Broadcast hint
result = df1.join(df2.hint("broadcast"), "key")

# Shuffle merge hint
result = df1.hint("merge").join(df2, "key")

# Shuffle hash hint
result = df1.hint("shuffle_hash").join(df2, "key")

# Shuffle replicate NL hint (for small-large joins)
result = df1.hint("shuffle_replicate_nl").join(df2, "key")
```

### 检查连接计划

```python
# View physical plan
df1.join(df2, "key").explain(True)

# Look for:
# - BroadcastHashJoin (best for small tables)
# - SortMergeJoin (good for large-large joins)
# - BroadcastNestedLoopJoin (avoid, expensive)
# - CartesianProduct (avoid unless intentional)
```

---

## I/O 优化

### 读取数据

```python
# Parquet (best for Spark)
df = spark.read.parquet("s3://bucket/data/")

# Optimize Parquet reading
spark.conf.set("spark.sql.parquet.filterPushdown", "true")
spark.conf.set("spark.sql.parquet.mergeSchema", "false")  # Faster if schema consistent

# Partition pruning - filter on partition columns
df = spark.read.parquet("s3://bucket/data/") \
    .filter(F.col("date") >= "2024-01-01")  # Only reads matching partitions

# Column pruning - select only needed columns
df = spark.read.parquet("s3://bucket/data/").select("id", "name", "amount")

# Explicit schema (avoid inference)
df = spark.read.schema(my_schema).json("s3://bucket/data/")
```

### 写入数据

```python
# Optimal file sizes (128MB-256MB)
spark.conf.set("spark.sql.files.maxRecordsPerFile", 1000000)

# Compaction for small files
df.coalesce(100).write.parquet("s3://bucket/output/")

# Partitioned writes
df.write.partitionBy("date").parquet("s3://bucket/output/")

# Bucketed writes (requires Hive metastore)
df.write.bucketBy(100, "user_id").sortBy("timestamp").saveAsTable("table")

# Compression
df.write.option("compression", "snappy").parquet("s3://bucket/output/")
```

### 小文件问题

```python
# Detect small files
file_list = spark.sparkContext._jvm.org.apache.hadoop.fs.FileSystem \
    .get(spark.sparkContext._jsc.hadoopConfiguration()) \
    .listStatus(spark.sparkContext._jvm.org.apache.hadoop.fs.Path("s3://bucket/data/"))

# Compact small files
df = spark.read.parquet("s3://bucket/small_files/")
df.coalesce(optimal_partition_count).write.parquet("s3://bucket/compacted/")

# Or use repartition for even distribution
df.repartition(100).write.parquet("s3://bucket/compacted/")
```

---

## Spark UI 深入分析

### 作业标签

- **作业持续时间**: 识别慢作业
- **阶段**: 阶段数量（更多阶段 = 更多 shuffle）
- **DAG 可视化**: 理解数据流

### 阶段标签

| 指标 | 健康值 | 异常时的操作 |
|------|--------|--------------|
| 持续时间 | 每个阶段 < 5 分钟 | 拆分大阶段 |
| 任务 | 均匀分布 | 处理倾斜 |
| Shuffle 写 | 最小化 | 更早过滤，选择更少的列 |
| Shuffle 读阻塞时间 | 接近 0 | 检查网络，增加并行性 |
| 溢出（磁盘） | 0 | 增加内存或分区 |
| GC 时间 | < 任务时间的 10% | 调优 GC，减少缓存数据 |

### Executor 标签

- **存储内存**: 缓存使用情况
- **Shuffle 读/写**: I/O 模式
- **GC 时间**: 垃圾回收开销
- **失败任务**: Executor 失败

### SQL 标签

- **持续时间**: 查询执行时间
- **详情**: 物理计划详情
- **指标**: 每个阶段的输入/输出行数

### 存储标签

- **缓存的 RDD/DataFrame**: 大小和分区分布
- **缓存比例**: 应该是 100%

---

## 常见配置模板

```python
# Production configuration template
spark_configs = {
    # Executor configuration
    "spark.executor.instances": 50,
    "spark.executor.cores": 5,
    "spark.executor.memory": "16g",
    "spark.executor.memoryOverhead": "2g",

    # Driver configuration
    "spark.driver.memory": "8g",
    "spark.driver.maxResultSize": "4g",

    # Shuffle configuration
    "spark.sql.shuffle.partitions": 500,
    "spark.shuffle.compress": "true",
    "spark.io.compression.codec": "lz4",

    # SQL optimization
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.sql.autoBroadcastJoinThreshold": str(200 * 1024 * 1024),  # 200MB

    # Serialization
    "spark.serializer": "org.apache.spark.serializer.KryoSerializer",

    # Dynamic allocation
    "spark.dynamicAllocation.enabled": "true",
    "spark.dynamicAllocation.minExecutors": 5,
    "spark.dynamicAllocation.maxExecutors": 100,
}

for key, value in spark_configs.items():
    spark.conf.set(key, value)
```

---

## 故障排除决策树

```
Slow Spark Job
├── Long GC Time (> 10%)?
│   ├── Yes → Increase executor memory or reduce cache
│   └── No → Continue
├── Shuffle Spill to Disk?
│   ├── Yes → Increase partitions or memory
│   └── No → Continue
├── Uneven Task Duration?
│   ├── Yes → Data skew, use salting or AQE
│   └── No → Continue
├── Long Shuffle Read Time?
│   ├── Yes → Network bottleneck, increase locality
│   └── No → Continue
├── Large Shuffle Size?
│   ├── Yes → Filter earlier, broadcast small tables
│   └── No → Continue
└── Too Many Small Tasks?
    ├── Yes → Reduce partitions with coalesce
    └── No → Check for code-level optimizations
```

---

## 最佳实践总结

1. **正确配置 executor** - 5 个核心，16GB 内存为典型
2. **启用 AQE（Spark 3.x）** - 分区和倾斜的自动优化
3. **调优 shuffle 分区** - 根据数据大小，而非默认 200
4. **处理数据倾斜** - 加密 key 或使用 AQE 自动处理
5. **监控 Spark UI** - 检查 shuffle、溢出、GC 指标
6. **使用广播连接** - 对于 200MB 以下的表
7. **早期过滤和选择** - 在 shuffle 前减少数据
8. **避免 UDF** - 使用内置函数（快 10-100 倍）
9. **战略性缓存** - 只缓存被重用的数据，完成后 unpersist
10. **按规模测试** - 性能随数据量显著变化

```