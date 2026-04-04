# PostgreSQL 扩展

## 扩展管理

```sql
-- 列出可用扩展
SELECT * FROM pg_available_extensions ORDER BY name;

-- 列出已安装扩展
SELECT * FROM pg_extension;

-- 安装扩展
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 删除扩展
DROP EXTENSION pg_stat_statements;

-- 更新扩展
ALTER EXTENSION pg_stat_statements UPDATE TO '1.10';
```

## pg_stat_statements（查询性能）

```sql
-- 安装和配置
CREATE EXTENSION pg_stat_statements;

-- postgresql.conf:
-- shared_preload_libraries = 'pg_stat_statements'
-- pg_stat_statements.max = 10000
-- pg_stat_statements.track = all

-- 按平均时间排序的前 10 个最慢查询
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time,
  max_exec_time,
  stddev_exec_time,
  rows
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 调用最频繁的查询
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;

-- 最耗时的查询（总时间）
SELECT
  query,
  calls,
  total_exec_time / 1000 as total_seconds,
  mean_exec_time,
  (total_exec_time / sum(total_exec_time) OVER ()) * 100 as percentage
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- 重置统计信息
SELECT pg_stat_statements_reset();
```

## uuid-ossp（UUID 生成）

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 生成 UUID
SELECT uuid_generate_v1();    -- 基于时间 + MAC 地址
SELECT uuid_generate_v4();    -- 随机（最常用）

-- 在表中使用
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入
INSERT INTO users (email) VALUES ('user@example.com')
RETURNING id;
```

## pg_trgm（模糊字符串匹配）

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 相似性搜索
SELECT
  email,
  similarity(email, 'john@example.com') as sim
FROM users
WHERE similarity(email, 'john@example.com') > 0.3
ORDER BY sim DESC;

-- 使用三元组索引优化 LIKE
CREATE INDEX idx_users_email_trgm ON users USING GIN(email gin_trgm_ops);

-- 现在这些查询使用索引：
SELECT * FROM users WHERE email ILIKE '%john%';
SELECT * FROM users WHERE email % 'jon@example.com';  -- 相似于

-- 三元组操作符
SELECT 'hello' % 'helo';              -- True（相似）
SELECT similarity('hello', 'helo');   -- 0.5
SELECT word_similarity('hello', 'hello world');  -- 1.0

-- 设置相似性阈值
SET pg_trgm.similarity_threshold = 0.5;
SELECT * FROM users WHERE email % 'searchtext';
```

## PostGIS（空间和地理）

```sql
CREATE EXTENSION IF NOT EXISTS postgis;

-- 创建空间表
CREATE TABLE locations (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  geom GEOMETRY(Point, 4326)  -- WGS84 经/纬
);

-- 添加空间索引
CREATE INDEX idx_locations_geom ON locations USING GIST(geom);

-- 插入点（经度，纬度）
INSERT INTO locations (name, geom)
VALUES ('NYC', ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326));

-- 距离查询（以米为单位）
SELECT
  name,
  ST_Distance(
    geom::geography,
    ST_SetSRID(ST_MakePoint(-73.9857, 40.7484), 4326)::geography
  ) as distance_meters
FROM locations
ORDER BY distance_meters
LIMIT 10;

-- 半径内查询（1km = 1000m）
SELECT * FROM locations
WHERE ST_DWithin(
  geom::geography,
  ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326)::geography,
  1000
);

-- 边界框查询（使用 GIST 索引非常快）
SELECT * FROM locations
WHERE geom && ST_MakeEnvelope(-74.1, 40.6, -73.9, 40.8, 4326);

-- 包含查询
SELECT * FROM zones
WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(-74.0060, 40.7128), 4326));

-- 面积计算
SELECT
  name,
  ST_Area(geom::geography) / 1000000 as area_km2
FROM zones;

-- GeoJSON 导出
SELECT
  name,
  ST_AsGeoJSON(geom) as geojson
FROM locations;
```

## pgvector（向量相似性搜索）

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建带有向量列的表
CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  content TEXT,
  embedding vector(1536)  -- OpenAI 嵌入是 1536 维
);

-- 添加向量索引（HNSW 以获得更好的性能）
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops);
-- 或 IVFFlat 以获得内存效率：
-- CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);

-- 插入向量
INSERT INTO embeddings (content, embedding)
VALUES ('Hello world', '[0.1, 0.2, 0.3, ...]');

-- 相似性搜索（余弦距离）
SELECT
  content,
  1 - (embedding <=> '[0.1, 0.2, ...]') as similarity
FROM embeddings
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 10;

-- 距离操作符
-- <-> L2 距离（欧几里得）
-- <#> 负内积
-- <=> 余弦距离（嵌入最常用）

-- 设置索引参数以获得更好的召回率
SET hnsw.ef_search = 100;  -- 更高 = 更好的召回率，查询更慢

-- 批量插入优化
SET maintenance_work_mem = '2GB';
```

## pgcrypto（加密和哈希）

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 哈希密码（使用 bcrypt）
INSERT INTO users (email, password_hash)
VALUES ('user@example.com', crypt('password123', gen_salt('bf', 10)));

-- 验证密码
SELECT * FROM users
WHERE email = 'user@example.com'
  AND password_hash = crypt('password123', password_hash);

-- 生成随机值
SELECT gen_random_uuid();
SELECT gen_random_bytes(32);

-- 加密/解密数据
SELECT
  pgp_sym_encrypt('sensitive data', 'encryption-key'),
  pgp_sym_decrypt(encrypted_column, 'encryption-key')
FROM table_name;

-- 摘要函数
SELECT digest('data', 'sha256');
SELECT encode(digest('data', 'sha256'), 'hex');
```

## postgres_fdw（外部数据包装器）

```sql
CREATE EXTENSION IF NOT EXISTS postgres_fdw;

-- 创建外部服务器
CREATE SERVER remote_db
FOREIGN DATA WRAPPER postgres_fdw
OPTIONS (host 'remote-host', port '5432', dbname 'remote_db');

-- 用户映射
CREATE USER MAPPING FOR current_user
SERVER remote_db
OPTIONS (user 'remote_user', password 'remote_password');

-- 导入外部架构
IMPORT FOREIGN SCHEMA public
FROM SERVER remote_db
INTO remote_schema;

-- 或创建特定的外部表
CREATE FOREIGN TABLE remote_users (
  id INTEGER,
  email TEXT,
  created_at TIMESTAMPTZ
)
SERVER remote_db
OPTIONS (schema_name 'public', table_name 'users');

-- 查询外部表（透明）
SELECT * FROM remote_users WHERE created_at > NOW() - INTERVAL '1 day';

-- 连接本地和外部表
SELECT
  l.id,
  l.name,
  r.email
FROM local_table l
JOIN remote_users r ON l.user_id = r.id;
```

## pg_repack（在线表重组）

```sql
CREATE EXTENSION IF NOT EXISTS pg_repack;

-- 重组表（移除膨胀，重建索引）
-- 通过命令行运行，而非 SQL：
-- pg_repack -d mydb -t users

-- 在 repack 之前检查膨胀
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                 pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 重组整个数据库
-- pg_repack -d mydb

-- 使用自定义顺序重组
-- pg_repack -d mydb -t users -o "created_at DESC"
```

## timescaledb（时序数据）

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 创建超表（必须有时间列）
CREATE TABLE metrics (
  time TIMESTAMPTZ NOT NULL,
  device_id INTEGER,
  temperature DOUBLE PRECISION,
  humidity DOUBLE PRECISION
);

-- 转换为超表
SELECT create_hypertable('metrics', 'time');

-- 设置块间隔（默认 7 天）
SELECT set_chunk_time_interval('metrics', INTERVAL '1 day');

-- 添加压缩
ALTER TABLE metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'device_id',
  timescaledb.compress_orderby = 'time DESC'
);

-- 自动压缩策略（压缩 7 天前的块）
SELECT add_compression_policy('metrics', INTERVAL '7 days');

-- 保留策略（丢弃 30 天前的块）
SELECT add_retention_policy('metrics', INTERVAL '30 days');

-- 连续聚合（时序的物化视图）
CREATE MATERIALIZED VIEW metrics_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', time) AS bucket,
  device_id,
  AVG(temperature) as avg_temp,
  MAX(temperature) as max_temp,
  MIN(temperature) as min_temp
FROM metrics
GROUP BY bucket, device_id;

-- 刷新策略
SELECT add_continuous_aggregate_policy('metrics_hourly',
  start_offset => INTERVAL '3 hours',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour'
);
```

## 按用例分类的扩展推荐

**查询性能监控：**
- `pg_stat_statements`（必需）
- `pg_stat_kcache`（缓存命中统计）

**文本搜索：**
- `pg_trgm`（模糊匹配，LIKE 优化）
- 内置全文搜索（无需扩展）

**空间数据：**
- `postgis`（全面的空间功能）

**向量嵌入 / AI：**
- `pgvector`（用于语义搜索、RAG 应用）

**时序：**
- `timescaledb`（自动分区、压缩）

**数据安全：**
- `pgcrypto`（哈希、加密）
- `pg_audit`（审计日志）

**UUID 支持：**
- `uuid-ossp`（UUID 生成）

**跨数据库查询：**
- `postgres_fdw`（查询远程 PostgreSQL）
- `file_fdw`（查询 CSV 文件）

**表维护：**
- `pg_repack`（在线膨胀移除）
