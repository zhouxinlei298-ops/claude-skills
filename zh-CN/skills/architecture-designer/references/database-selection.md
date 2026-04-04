# 数据库选择

## 数据库类型

| 类型 | 示例 | 最佳用途 |
|------|------|----------|
| **关系型** | PostgreSQL, MySQL | 事务，复杂查询，关系 |
| **文档型** | MongoDB, Firestore | 灵活的模式，快速迭代 |
| **键值型** | Redis, DynamoDB | 缓存，会话，高吞吐量 |
| **时序型** | TimescaleDB, InfluxDB | 指标，物联网，分析 |
| **图型** | Neo4j, Neptune | 关系，社交网络 |
| **搜索型** | Elasticsearch, Meilisearch | 全文搜索，日志 |

## 关系型（PostgreSQL, MySQL）

```
Best For:
- Financial transactions (ACID compliance)
- Complex queries with joins
- Data integrity requirements
- Structured, predictable schemas

When to Avoid:
- Highly variable schemas
- Massive horizontal scaling needs
- Simple key-value access patterns
```

| 功能 | PostgreSQL | MySQL |
|------|------------|-------|
| JSON 支持 | 优秀（JSONB） | 良好（JSON） |
| 全文搜索 | 内置支持 | 基础支持 |
| 扩展 | 丰富的生态系统 | 有限 |
| 复制 | 流复制、逻辑复制 | 语句复制、基于行的复制 |

## 文档型（MongoDB, Firestore）

```
Best For:
- Flexible, evolving schemas
- Hierarchical data (nested documents)
- Rapid prototyping
- Content management

When to Avoid:
- Complex transactions across documents
- Heavy relational queries
- Strict schema requirements
```

## 键值型（Redis, DynamoDB）

```
Best For:
- Session storage
- Caching layer
- Real-time leaderboards
- Rate limiting counters

When to Avoid:
- Complex queries
- Relational data
- Large value sizes (>1MB)
```

## 时序型（TimescaleDB, InfluxDB）

```
Best For:
- Metrics and monitoring
- IoT sensor data
- Financial tick data
- Event logging with timestamps

When to Avoid:
- Frequent updates to existing records
- Complex relational queries
- Non-time-based access patterns
```

## 决策矩阵

| 需求 | 推荐选择 |
|------|----------|
| ACID 事务 | PostgreSQL, MySQL |
| 灵活模式 | MongoDB, Firestore |
| 高速缓存 | Redis |
| 时序数据 | TimescaleDB, InfluxDB |
| 社交关系 | Neo4j |
| 全文搜索 | Elasticsearch |
| 无服务器扩展 | DynamoDB, Firestore |

## 快速参考

| 问题 | 如果是 → |
|------|----------|
| 需要 ACID 事务？ | 关系型（PostgreSQL） |
| 模式经常变化？ | 文档型（MongoDB） |
| 亚毫秒级读取？ | 键值型（Redis） |
| 基于时间的查询？ | 时序型 |
| 遍历关系？ | 图型（Neo4j） |
| 全文搜索是主要功能？ | Elasticsearch |