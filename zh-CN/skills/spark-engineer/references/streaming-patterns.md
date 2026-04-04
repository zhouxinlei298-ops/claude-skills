# 流处理模式

---

## Structured Streaming 概览

### 何时使用 Structured Streaming

**使用时：**
- 处理连续数据流（Kafka、文件、套接字）
- 需要恰好一次处理保证
- 实时分析和仪表板
- 事件驱动架构
- 从流源进行增量 ETL

**考虑替代方案时：**
- 批处理足够（复杂度较低）
- 需要亚秒级延迟（考虑 Flink）
- 非常简单的事件处理（Kafka Streams 可能足够）

---

## 从流源读取

### Kafka 源

```python
# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker1:9092,broker2:9092") \
    .option("subscribe", "topic1,topic2") \
    .option("startingOffsets", "latest") \
    .option("maxOffsetsPerTrigger", 100000) \
    .option("kafka.security.protocol", "SASL_SSL") \
    .option("kafka.sasl.mechanism", "PLAIN") \
    .load()

# Kafka provides key, value as bytes
# Parse JSON value
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, DoubleType

schema = StructType([
    StructField("event_id", StringType()),
    StructField("user_id", StringType()),
    StructField("event_time", TimestampType()),
    StructField("amount", DoubleType())
])

parsed_df = df.select(
    F.col("key").cast("string").alias("kafka_key"),
    F.from_json(F.col("value").cast("string"), schema).alias("data"),
    F.col("timestamp").alias("kafka_timestamp"),
    F.col("partition"),
    F.col("offset")
).select("kafka_key", "data.*", "kafka_timestamp", "partition", "offset")
```

```scala
// Scala Kafka source
val df = spark.readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "broker1:9092,broker2:9092")
  .option("subscribe", "topic1")
  .option("startingOffsets", "latest")
  .load()

val parsed = df.select(
  col("key").cast("string"),
  from_json(col("value").cast("string"), schema).as("data")
).select("key", "data.*")
```

### 文件源（自动发现）

```python
# Read new files as they arrive
df = spark.readStream \
    .format("parquet") \
    .schema(my_schema) \
    .option("path", "s3://bucket/incoming/") \
    .option("maxFilesPerTrigger", 100) \
    .load()

# For JSON files
df = spark.readStream \
    .format("json") \
    .schema(my_schema) \
    .option("path", "s3://bucket/incoming/") \
    .load()

# CSV with header
df = spark.readStream \
    .format("csv") \
    .schema(my_schema) \
    .option("path", "s3://bucket/incoming/") \
    .option("header", "true") \
    .load()
```

### 速率源（测试）

```python
# Generate test data at specified rate
df = spark.readStream \
    .format("rate") \
    .option("rowsPerSecond", 1000) \
    .option("numPartitions", 10) \
    .load()

# Columns: timestamp, value (incrementing long)
```

---

## 输出模式

### Append 模式（默认）

```python
# Only new rows added since last trigger
# Use when: No aggregations, or windowed aggregations with watermark
query = df.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### Update 模式

```python
# Only rows that changed since last trigger
# Use when: Aggregations, want incremental updates
query = df.groupBy("user_id").count() \
    .writeStream \
    .outputMode("update") \
    .format("console") \
    .start()
```

### Complete 模式

```python
# Entire result table every trigger
# Use when: Need full aggregation result each time
# Warning: Can be expensive for large state
query = df.groupBy("user_id").count() \
    .writeStream \
    .outputMode("complete") \
    .format("console") \
    .start()
```

### 模式选择指南

| 使用场景 | 输出模式 | 说明 |
|----------|----------|------|
| ETL 到文件 | append | 默认值，高效 |
| 窗口聚合 | append | 带 watermark |
| 运行计数/求和 | update | 增量 |
| 需要完整状态的仪表板 | complete | 昂贵 |
| 去重 | append | 带 dropDuplicates |

---

## Watermark 和事件时间

### 了解 Watermark

Watermark 定义数据到达前可以延迟丢弃的程度。它们使 Spark 能够：
- 清理旧状态（有界内存）
- 在适当时间发出结果
- 处理乱序事件

### 设置 Watermark

```python
from pyspark.sql import functions as F

# Define watermark on event time column
df_with_watermark = df \
    .withWatermark("event_time", "10 minutes")

# Watermark threshold: max_event_time - 10 minutes
# Events older than watermark are dropped
# State older than watermark is cleaned up
```

### Watermark 指导原则

| 场景 | Watermark 时长 | 原因 |
|------|----------------|------|
| 实时分析 | 1-5 分钟 | 低延迟，容忍少量延迟数据 |
| 标准 ETL | 10-30 分钟 | 平衡延迟和延迟数据 |
| 延迟到达数据常见 | 1-24 小时 | 适应延迟事件 |
| 最佳努力实时 | 0 分钟 | 不容忍延迟数据 |

### 带窗口聚合的示例

```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# Streaming aggregation with watermark
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.window("event_time", "5 minutes", "1 minute"),  # 5-min tumbling window, 1-min slide
        "user_id"
    ) \
    .agg(
        F.count("*").alias("event_count"),
        F.sum("amount").alias("total_amount")
    )

# Output schema includes window struct: window.start, window.end
query = result \
    .select(
        F.col("window.start").alias("window_start"),
        F.col("window.end").alias("window_end"),
        "user_id",
        "event_count",
        "total_amount"
    ) \
    .writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3://bucket/windowed_output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

---

## 窗口操作

### 滚动窗口（无重叠）

```python
from pyspark.sql import functions as F

# 5-minute tumbling windows
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.window("event_time", "5 minutes"),
        "category"
    ) \
    .agg(F.sum("amount").alias("total"))

# Windows: [00:00-00:05), [00:05-00:10), [00:10-00:15), ...
```

### 滑动窗口（重叠）

```python
# 10-minute windows, sliding every 2 minutes
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.window("event_time", "10 minutes", "2 minutes"),
        "category"
    ) \
    .agg(F.sum("amount").alias("total"))

# Windows: [00:00-00:10), [00:02-00:12), [00:04-00:14), ...
```

### 会话窗口（基于间隔）

```python
# Session windows with 5-minute gap threshold
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        F.session_window("event_time", "5 minutes"),  # Spark 3.2+
        "user_id"
    ) \
    .agg(
        F.count("*").alias("events_in_session"),
        F.first("event_time").alias("session_start"),
        F.last("event_time").alias("session_end")
    )
```

---

## 有状态操作

### 聚合（内置状态）

```python
# Running count by key
running_counts = df \
    .withWatermark("event_time", "1 hour") \
    .groupBy("user_id") \
    .agg(F.count("*").alias("total_events"))

# State stored per user_id
# Cleaned up based on watermark
```

### 去重

```python
# Drop duplicates within watermark window
deduped = df \
    .withWatermark("event_time", "10 minutes") \
    .dropDuplicates(["event_id"])  # Keep first occurrence

# Can also dedupe by multiple columns
deduped = df \
    .withWatermark("event_time", "10 minutes") \
    .dropDuplicates(["user_id", "event_type", "event_time"])
```

### 自定义有状态处理（flatMapGroupsWithState）

```python
# PySpark - Custom state using applyInPandasWithState (Spark 3.4+)
from pyspark.sql.streaming.state import GroupState, GroupStateTimeout

def update_session_state(
    key: tuple,
    pdf_iter: Iterator[pd.DataFrame],
    state: GroupState
) -> Iterator[pd.DataFrame]:
    # Get or initialize state
    if state.exists:
        session_data = state.get
    else:
        session_data = {"count": 0, "total": 0.0}

    # Process input data
    for pdf in pdf_iter:
        session_data["count"] += len(pdf)
        session_data["total"] += pdf["amount"].sum()

    # Update state
    state.update(session_data)

    # Optionally set timeout
    state.setTimeoutDuration(10 * 60 * 1000)  # 10 minutes

    # Yield output
    yield pd.DataFrame([{
        "user_id": key[0],
        "event_count": session_data["count"],
        "total_amount": session_data["total"]
    }])

# Apply stateful function
result = df \
    .withWatermark("event_time", "10 minutes") \
    .groupBy("user_id") \
    .applyInPandasWithState(
        update_session_state,
        outputStructType=output_schema,
        stateStructType=state_schema,
        outputMode="update",
        timeoutConf=GroupStateTimeout.ProcessingTimeTimeout
    )
```

```scala
// Scala flatMapGroupsWithState
import org.apache.spark.sql.streaming.{GroupState, GroupStateTimeout}

case class UserState(count: Long, totalAmount: Double)
case class UserOutput(userId: String, count: Long, totalAmount: Double)

def updateState(
    userId: String,
    events: Iterator[Event],
    state: GroupState[UserState]
): Iterator[UserOutput] = {

  val currentState = state.getOption.getOrElse(UserState(0, 0.0))

  var newCount = currentState.count
  var newTotal = currentState.totalAmount

  events.foreach { event =>
    newCount += 1
    newTotal += event.amount
  }

  val newState = UserState(newCount, newTotal)
  state.update(newState)
  state.setTimeoutDuration("10 minutes")

  Iterator(UserOutput(userId, newCount, newTotal))
}

val result = df
  .withWatermark("event_time", "10 minutes")
  .as[Event]
  .groupByKey(_.userId)
  .flatMapGroupsWithState(
    OutputMode.Update,
    GroupStateTimeout.ProcessingTimeTimeout
  )(updateState)
```

---

## 流连接

### 流-静态连接

```python
# Join streaming data with static lookup table
static_df = spark.read.parquet("s3://bucket/lookup/")

# Streaming df joined with static - no watermark needed
result = streaming_df.join(static_df, "join_key", "left")

# Static table can be periodically refreshed
# Use broadcast for small static tables
from pyspark.sql.functions import broadcast
result = streaming_df.join(broadcast(static_df), "join_key")
```

### 流-流连接

```python
# Join two streams - requires watermarks on both
from pyspark.sql import functions as F

stream1 = spark.readStream.format("kafka")...
stream2 = spark.readStream.format("kafka")...

# Both streams need watermarks
stream1_wm = stream1.withWatermark("event_time", "10 minutes")
stream2_wm = stream2.withWatermark("event_time", "10 minutes")

# Inner join with time constraint
result = stream1_wm.join(
    stream2_wm,
    F.expr("""
        stream1.user_id = stream2.user_id AND
        stream1.event_time >= stream2.event_time AND
        stream1.event_time <= stream2.event_time + INTERVAL 5 MINUTES
    """),
    "inner"
)

# Left outer join (Spark 2.3+)
result = stream1_wm.join(
    stream2_wm,
    F.expr("""
        stream1.user_id = stream2.user_id AND
        stream1.event_time >= stream2.event_time - INTERVAL 5 MINUTES AND
        stream1.event_time <= stream2.event_time + INTERVAL 5 MINUTES
    """),
    "leftOuter"
)
```

### 连接类型支持

| 连接类型 | 流-静态 | 流-流 |
|----------|----------|------|
| 内部 | 是 | 是 |
| 左外 | 是 | 是（Spark 2.3+） |
| 右外 | 是 | 是（Spark 2.3+） |
| 全外 | 是 | 是（Spark 2.4+） |
| 左半 | 是 | 不支持 |
| 左反 | 是 | 不支持 |

---

## 接收器

### Kafka 接收器

```python
# Write to Kafka
query = df \
    .select(
        F.col("user_id").alias("key"),
        F.to_json(F.struct("*")).alias("value")
    ) \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker1:9092") \
    .option("topic", "output_topic") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### 文件接收器（Parquet、JSON、CSV）

```python
# Parquet sink with partitioning
query = df.writeStream \
    .format("parquet") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .partitionBy("date", "hour") \
    .trigger(processingTime="1 minute") \
    .start()

# JSON sink
query = df.writeStream \
    .format("json") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### Delta Lake 接收器

```python
# Delta Lake (ACID transactions, schema evolution)
query = df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("path", "s3://bucket/delta_table/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .option("mergeSchema", "true") \
    .start()

# Upsert with foreachBatch
def upsert_to_delta(batch_df, batch_id):
    delta_table = DeltaTable.forPath(spark, "s3://bucket/delta_table/")
    delta_table.alias("target").merge(
        batch_df.alias("source"),
        "target.id = source.id"
    ).whenMatchedUpdateAll() \
     .whenNotMatchedInsertAll() \
     .execute()

query = df.writeStream \
    .foreachBatch(upsert_to_delta) \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .start()
```

### 自定义接收器（foreachBatch）

```python
def write_to_database(batch_df, batch_id):
    """Write each micro-batch to external database."""
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://host:5432/db") \
        .option("dbtable", "output_table") \
        .option("user", "user") \
        .option("password", "password") \
        .mode("append") \
        .save()

query = df.writeStream \
    .foreachBatch(write_to_database) \
    .option("checkpointLocation", "s3://bucket/checkpoints/") \
    .trigger(processingTime="30 seconds") \
    .start()
```

### foreach（逐行）

```python
# For custom processing of each row
class ForeachWriter:
    def open(self, partition_id, epoch_id):
        # Initialize connection
        self.connection = create_connection()
        return True

    def process(self, row):
        # Process each row
        self.connection.insert(row.asDict())

    def close(self, error):
        # Clean up
        self.connection.close()

query = df.writeStream \
    .foreach(ForeachWriter()) \
    .start()
```

---

## 触发器

### 可用触发器类型

```python
# Process as fast as possible (default)
query = df.writeStream.trigger(processingTime="0 seconds").start()

# Fixed interval
query = df.writeStream.trigger(processingTime="1 minute").start()

# Once - process all available data, then stop
query = df.writeStream.trigger(once=True).start()

# Available now - process all available data (Spark 3.3+)
query = df.writeStream.trigger(availableNow=True).start()

# Continuous processing (experimental, low latency)
query = df.writeStream.trigger(continuous="1 second").start()
```

### 触发器选择指南

| 触发器 | 使用场景 |
|--------|----------|
| processingTime="0 秒" | 最大吞吐量 |
| processingTime="N 秒" | 受控资源使用 |
| once=True | 批处理样式 |
| availableNow=True | 追赶处理 |
| continuous="N 毫秒" | 超低延迟（实验性） |

---

## 监控和管理

### 查询管理

```python
# Start query and get handle
query = df.writeStream.format("console").start()

# Query properties
print(f"Query ID: {query.id}")
print(f"Run ID: {query.runId}")
print(f"Name: {query.name}")
print(f"Is Active: {query.isActive}")
print(f"Status: {query.status}")
print(f"Last Progress: {query.lastProgress}")
print(f"Recent Progress: {query.recentProgress}")

# Wait for termination
query.awaitTermination()
query.awaitTermination(timeout=60)  # With timeout

# Stop query
query.stop()

# Get exception if failed
exception = query.exception()
```

### 进度监控

```python
# Get latest progress
progress = query.lastProgress
if progress:
    print(f"Input rows/sec: {progress['inputRowsPerSecond']}")
    print(f"Processed rows/sec: {progress['processedRowsPerSecond']}")
    print(f"Batch ID: {progress['batchId']}")
    print(f"Duration: {progress['batchDuration']} ms")
    print(f"State rows: {progress['stateOperators']}")

# Custom progress listener
class ProgressListener:
    def onQueryProgress(self, event):
        print(f"Progress: {event.progress}")

    def onQueryTerminated(self, event):
        print(f"Terminated: {event.exception}")

spark.streams.addListener(ProgressListener())
```

### 检查点

```python
# Checkpoint location is required for fault tolerance
query = df.writeStream \
    .format("parquet") \
    .option("path", "s3://bucket/output/") \
    .option("checkpointLocation", "s3://bucket/checkpoints/query_name/") \
    .start()

# Checkpoint contains:
# - Offsets (what data has been processed)
# - State (for stateful operations)
# - Commits (what batches completed)

# Recovery: Query restarts from last checkpoint automatically
# Clean start: Delete checkpoint directory (loses state!)
```

---

## 性能模式

### 优化吞吐量

```python
# 1. Increase Kafka partitions for parallelism
# Consumer parallelism = Kafka partitions

# 2. Tune maxOffsetsPerTrigger
query = df.readStream \
    .format("kafka") \
    .option("maxOffsetsPerTrigger", 500000) \  # More data per batch
    .load()

# 3. Optimize shuffle partitions
spark.conf.set("spark.sql.shuffle.partitions", 100)

# 4. Use appropriate trigger interval
query = df.writeStream \
    .trigger(processingTime="30 seconds") \
    .start()

# 5. Enable AQE for dynamic optimization
spark.conf.set("spark.sql.adaptive.enabled", "true")
```

### 管理状态大小

```python
# 1. Always use watermarks for stateful operations
df.withWatermark("event_time", "1 hour")

# 2. Monitor state size in progress
progress = query.lastProgress
for operator in progress["stateOperators"]:
    print(f"State rows: {operator['numRowsTotal']}")
    print(f"Memory used: {operator['memoryUsedBytes']}")

# 3. Configure state store
spark.conf.set("spark.sql.streaming.stateStore.providerClass",
    "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider")
# RocksDB handles larger state better than in-memory default

# 4. Set state cleanup mode
spark.conf.set("spark.sql.streaming.stateStore.stateSchemaCheck", "false")
```

---

## 常见反模式

```python
# BAD: No watermark with aggregation
df.groupBy("user_id").count()  # Unbounded state growth!

# GOOD: Always use watermark
df.withWatermark("event_time", "1 hour").groupBy("user_id").count()

# BAD: Complete mode with large state
df.groupBy("user_id").count().writeStream.outputMode("complete")  # Outputs entire state

# GOOD: Update mode for incremental
df.groupBy("user_id").count().writeStream.outputMode("update")

# BAD: No checkpoint location
query = df.writeStream.format("console").start()  # No fault tolerance!

# GOOD: Always specify checkpoint
query = df.writeStream.format("console") \
    .option("checkpointLocation", "/checkpoints/query") \
    .start()

# BAD: foreach for high-throughput
df.writeStream.foreach(process_row).start()  # Row-by-row overhead

# GOOD: foreachBatch for batched processing
df.writeStream.foreachBatch(process_batch).start()  # Batch-level efficiency
```

---

## 最佳实践总结

1. **始终使用 watermark** - 防止无界状态增长
2. **选择适当的输出模式** - ETL 用 append，聚合用 update
3. **设置检查点位置** - 容错必需
4. **优先使用 foreachBatch 而非 foreach** - 自定义接收器性能更好
5. **监控状态大小** - 关注进度指标中的内存增长
6. **调整触发器间隔** - 平衡延迟与吞吐量
7. **匹配 Kafka 分区与并行性** - 消费者任务 = Kafka 分区数
8. **尽可能使用流-静态连接** - 比流-流连接更简单
9. **使用生产数据速率测试** - 性能随数据量变化
10. **启用结构化流 UI** - 在 Spark UI 中查看详细指标

```