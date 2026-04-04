# JSONB 操作

## JSONB vs JSON

```sql
-- 使用 JSONB（二进制、可索引、更快）
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  data JSONB NOT NULL
);

-- 不使用 json（文本存储，无索引）
-- 仅在需要保留精确格式/空格时使用 json
```

## JSONB 操作符

### 检索操作符

```sql
-- -> 返回 JSONB
SELECT data -> 'user' FROM documents;                    -- {"id": 123, "name": "Alice"}
SELECT data -> 'user' -> 'name' FROM documents;          -- "Alice" (仍然是 JSONB)

-- ->> 返回文本
SELECT data ->> 'status' FROM documents;                 -- active (文本)
SELECT data -> 'user' ->> 'name' FROM documents;         -- Alice (文本)

-- #> 用于嵌套路径（JSONB）
SELECT data #> '{user,address,city}' FROM documents;    -- "NYC" (JSONB)

-- #>> 用于嵌套路径（文本）
SELECT data #>> '{user,address,city}' FROM documents;   -- NYC (文本)

-- 数组访问
SELECT data -> 'tags' -> 0 FROM documents;               -- 第一个标签
SELECT jsonb_array_elements(data -> 'tags') FROM documents;  -- 展开数组
```

### 包含操作符

```sql
-- @> 包含（最常用于索引）
SELECT * FROM documents WHERE data @> '{"status": "active"}';
SELECT * FROM documents WHERE data @> '{"tags": ["postgresql"]}';
SELECT * FROM documents WHERE data -> 'user' @> '{"role": "admin"}';

-- <@ 被包含于
SELECT * FROM documents WHERE '{"status": "active"}' <@ data;

-- ? 键存在
SELECT * FROM documents WHERE data ? 'email';
SELECT * FROM documents WHERE data -> 'user' ? 'email';

-- ?| 任意键存在
SELECT * FROM documents WHERE data ?| ARRAY['email', 'phone'];

-- ?& 所有键存在
SELECT * FROM documents WHERE data ?& ARRAY['email', 'phone'];
```

### 修改操作符

```sql
-- || 连接/合并（浅层）
UPDATE documents SET data = data || '{"updated_at": "2024-01-01"}'::jsonb;

-- - 删除键
UPDATE documents SET data = data - 'temp_field';

-- #- 删除嵌套路径
UPDATE documents SET data = data #- '{user,temp_field}';

-- jsonb_set 用于深层更新
UPDATE documents
SET data = jsonb_set(data, '{user,email}', '"new@example.com"'::jsonb)
WHERE id = 123;

-- jsonb_insert
UPDATE documents
SET data = jsonb_insert(data, '{tags,0}', '"new-tag"'::jsonb)
WHERE id = 123;
```

## JSONB 索引

### GIN 索引（包含的默认选择）

```sql
-- 标准 GIN 索引（用于 @>, ?, ?&, ?| 操作符）
CREATE INDEX idx_documents_data ON documents USING GIN(data);

-- 受益的查询：
SELECT * FROM documents WHERE data @> '{"status": "active"}';
SELECT * FROM documents WHERE data ? 'email';
SELECT * FROM documents WHERE data ?& ARRAY['email', 'phone'];
```

### 特定路径的 GIN 索引

```sql
-- 索引特定路径以获得更好的性能
CREATE INDEX idx_documents_status ON documents USING GIN((data -> 'status'));
CREATE INDEX idx_documents_user ON documents USING GIN((data -> 'user'));

-- 更小的索引，特定路径上更快的查询
SELECT * FROM documents WHERE data -> 'status' @> '"active"';
```

### 带有 jsonb_path_ops 的 GIN 索引

```sql
-- 更小、更快的索引，仅用于 @> 查询
CREATE INDEX idx_documents_path_ops ON documents USING GIN(data jsonb_path_ops);

-- 适用于：WHERE data @> '{"key": "value"}'
-- 不适用于：WHERE data ? 'key'（不支持）
-- 比默认 GIN 小约 20%，@> 查询更快
```

### 提取值的 B-tree 索引

```sql
-- 索引提取值（选择性最高）
CREATE INDEX idx_documents_status_btree ON documents((data ->> 'status'));
CREATE INDEX idx_documents_user_id ON documents((CAST(data -> 'user' ->> 'id' AS INTEGER)));

-- 启用高效的等值和范围查询
SELECT * FROM documents WHERE data ->> 'status' = 'active';
SELECT * FROM documents WHERE CAST(data -> 'user' ->> 'id' AS INTEGER) > 1000;
```

### 嵌套值的表达式索引

```sql
-- 索引深层嵌套值
CREATE INDEX idx_documents_user_email ON documents((data #>> '{user,email}'));

-- 启用：
SELECT * FROM documents WHERE data #>> '{user,email}' = 'user@example.com';
```

## 查询模式

### 过滤

```sql
-- 精确匹配
SELECT * FROM documents WHERE data @> '{"status": "active"}';

-- 多个条件
SELECT * FROM documents
WHERE data @> '{"status": "active", "verified": true}';

-- 嵌套条件
SELECT * FROM documents
WHERE data -> 'user' @> '{"role": "admin"}';

-- 数组包含
SELECT * FROM documents
WHERE data -> 'tags' @> '["postgresql"]';

-- JSONB 值中的文本搜索
SELECT * FROM documents
WHERE data ->> 'title' ILIKE '%postgres%';
```

### 聚合

```sql
-- 提取并聚合
SELECT
  data ->> 'status' as status,
  COUNT(*) as count,
  AVG(CAST(data ->> 'score' AS FLOAT)) as avg_score
FROM documents
GROUP BY data ->> 'status';

-- 数组聚合
SELECT
  jsonb_agg(data -> 'user') as users
FROM documents
WHERE data @> '{"status": "active"}';

-- 对象聚合
SELECT
  jsonb_object_agg(id, data -> 'user') as user_map
FROM documents
WHERE data ? 'user';
```

### 数组操作

```sql
-- 展开数组为行
SELECT
  id,
  jsonb_array_elements(data -> 'tags') as tag
FROM documents;

-- 展开数组为文本
SELECT
  id,
  jsonb_array_elements_text(data -> 'tags') as tag
FROM documents;

-- 数组长度
SELECT * FROM documents
WHERE jsonb_array_length(data -> 'tags') > 5;

-- 过滤数组元素
SELECT
  id,
  jsonb_path_query_array(data, '$.tags[*] ? (@ like_regex "^post.*" flag "i")') as postgres_tags
FROM documents;
```

## JSONB 函数

```sql
-- 构建 JSONB
SELECT jsonb_build_object('id', 123, 'name', 'Alice', 'active', true);
SELECT jsonb_build_array(1, 2, 'three', true);

-- 对象键
SELECT jsonb_object_keys(data) FROM documents;

-- 漂亮打印
SELECT jsonb_pretty(data) FROM documents;

-- 类型检查
SELECT jsonb_typeof(data -> 'score');  -- number, string, array, object, boolean, null

-- 移除 null
SELECT jsonb_strip_nulls(data) FROM documents;
```

## JSONB 路径查询（Postgres 12+）

```sql
-- jsonb_path_query 用于灵活查询
SELECT jsonb_path_query(data, '$.user.address.city') FROM documents;

-- 带过滤器
SELECT jsonb_path_query(data, '$.items[*] ? (@.price > 100)') FROM documents;

-- 存在检查
SELECT * FROM documents
WHERE jsonb_path_exists(data, '$.tags[*] ? (@ == "postgresql")');

-- 数组结果
SELECT jsonb_path_query_array(data, '$.items[*].name') FROM documents;
```

## 性能最佳实践

### 应该这样做

```sql
-- 为热路径使用特定路径索引
CREATE INDEX idx_docs_status ON documents((data ->> 'status'));

-- 使用带路径操作符的 GIN 索引进行仅包含查询
CREATE INDEX idx_docs_pathops ON documents USING GIN(data jsonb_path_ops);

-- 将频繁查询的值提取到列
ALTER TABLE documents ADD COLUMN status TEXT GENERATED ALWAYS AS (data ->> 'status') STORED;
CREATE INDEX idx_docs_status_col ON documents(status);

-- 使用 @> 进行索引查询
WHERE data @> '{"status": "active"}'  -- 使用 GIN 索引更快
```

### 不应该这样做

```sql
-- 不要使用 ->> 配合 @>（混合类型）
WHERE data @> '{"score": "100"}'  -- 错误，比较字符串
WHERE CAST(data ->> 'score' AS INTEGER) = 100  -- 更好

-- 不要在没有索引的情况下查询
SELECT * FROM documents WHERE data -> 'nested' -> 'deep' ->> 'value' = 'x';
-- 添加索引：CREATE INDEX ON documents((data #>> '{nested,deep,value}'));

-- 不要在 JSONB 中存储大数组
-- 如果有 10k+ 元素，使用单独的表

-- 不要对高更新列使用 JSONB
-- 如果频繁更新，提取为常规列
```

## Schema 验证（Postgres 15+）

```sql
-- 使用 CHECK 约束
ALTER TABLE documents
ADD CONSTRAINT check_data_schema
CHECK (
  jsonb_typeof(data) = 'object' AND
  data ? 'id' AND
  data ? 'status' AND
  data ->> 'status' IN ('active', 'pending', 'archived')
);
```

## 迁移模式

```sql
-- 添加 JSONB 列
ALTER TABLE users ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;

-- 将现有列迁移到 JSONB
UPDATE users SET metadata = jsonb_build_object(
  'preferences', preferences,
  'settings', settings,
  'flags', flags
);

-- 验证后删除旧列
ALTER TABLE users DROP COLUMN preferences, DROP COLUMN settings, DROP COLUMN flags;
```
