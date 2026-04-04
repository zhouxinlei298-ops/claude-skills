# 分页模式

## 为什么要分页？

由于以下原因，大型集合不能一次性返回：
- 性能（慢查询、大负载）
- 内存限制（服务器和客户端）
- 网络超时
- 用户体验差

始终对集合端点进行分页。

## 分页策略

### 1. 基于偏移量的分页

最常见和直观。使用 `offset`（跳过）和 `limit`（页面大小）。

**请求：**
```http
GET /users?offset=20&limit=10
```

**响应：**
```json
{
  "data": [
    {"id": 21, "name": "User 21"},
    {"id": 22, "name": "User 22"}
  ],
  "pagination": {
    "offset": 20,
    "limit": 10,
    "total": 150,
    "has_more": true
  },
  "links": {
    "first": "/users?offset=0&limit=10",
    "prev": "/users?offset=10&limit=10",
    "next": "/users?offset=30&limit=10",
    "last": "/users?offset=140&limit=10"
  }
}
```

**优点：**
- 实现简单
- 易于理解
- 随机访问（跳转到任何页面）
- 显示总计数

**缺点：**
- 大偏移量时性能下降（数据库扫描多行）
- 分页期间数据更改导致结果不一致
- 实时数据效率低
- 数据库必须计数总行数（昂贵）

**用于：**
- 中小型数据集
- 数据不经常更改
- 需要随机页面访问
- 需要总计数

### 2. 基于页码的分页

使用页码简化偏移量分页。

**请求：**
```http
GET /users?page=3&per_page=10
```

**响应：**
```json
{
  "data": [...],
  "pagination": {
    "page": 3,
    "per_page": 10,
    "total_pages": 15,
    "total_count": 150
  },
  "links": {
    "first": "/users?page=1&per_page=10",
    "prev": "/users?page=2&per_page=10",
    "next": "/users?page=4&per_page=10",
    "last": "/users?page=15&per_page=10"
  }
}
```

**计算：**
- `offset = (page - 1) * per_page`
- `total_pages = ceil(total_count / per_page)`

**与基于偏移量相同的优缺点，但：**
- 对用户更直观（第 1 页、第 2 页）
- 在 Web 应用中常见

### 3. 基于游标的分页

使用不透明游标（指针）来获取下一组结果。

**请求：**
```http
GET /users?limit=10
GET /users?cursor=eyJpZCI6MTIzfQ&limit=10
```

**响应：**
```json
{
  "data": [
    {"id": 21, "name": "User 21"},
    {"id": 22, "name": "User 22"}
  ],
  "pagination": {
    "next_cursor": "eyJpZCI6MzB9",
    "prev_cursor": "eyJpZCI6MjB9",
    "has_more": true
  },
  "links": {
    "next": "/users?cursor=eyJpZCI6MzB9&limit=10",
    "prev": "/users?cursor=eyJpZCI6MjB9&limit=10"
  }
}
```

**游标结构（base64 编码）：**
```json
{"id": 30, "sort": "created_at"}
```

**实现：**
```sql
-- 第一页
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;

-- 下一页（游标指向最后一项）
SELECT * FROM users
WHERE created_at < '2024-01-15T10:30:00Z'
ORDER BY created_at DESC
LIMIT 10;
```

**优点：**
- 一致的结果（无跳过/重复项）
- 大型数据集效率高
- 与实时数据配合良好
- 无昂贵的 COUNT 查询
- 更好的数据库性能

**缺点：**
- 无随机访问（无法跳转到第 10 页）
- 无总计数
- 实现更复杂
- 游标是不透明的（用户无法修改）

**用于：**
- 大型数据集
- 数据频繁更改
- 无限滚动 UI
- 实时信息流
- 性能至关重要

### 4. 键集分页

类似于游标但使用实际字段值而不是不透明游标。

**请求：**
```http
GET /users?after_id=20&limit=10
GET /users?after_created_at=2024-01-15T10:30:00Z&limit=10
```

**响应：**
```json
{
  "data": [
    {"id": 21, "name": "User 21", "created_at": "2024-01-15T11:00:00Z"},
    {"id": 22, "name": "User 22", "created_at": "2024-01-15T11:30:00Z"}
  ],
  "pagination": {
    "after_id": 30,
    "limit": 10,
    "has_more": true
  },
  "links": {
    "next": "/users?after_id=30&limit=10"
  }
}
```

**实现：**
```sql
SELECT * FROM users
WHERE id > 20
ORDER BY id ASC
LIMIT 10;
```

**优点：**
- 非常高效（使用索引）
- 透明的游标（人类可读）
- 一致的结果
- 简单实现

**缺点：**
- 需要索引列
- 无随机访问
- 排序限制为游标字段
- 多字段排序复杂

**用于：**
- 简单排序（按 ID、时间戳）
- 需要高效分页
- 希望透明的游标
- 有适当的索引

### 5. 查找分页（基于时间）

时间序列数据的专门化键集分页。

**请求：**
```http
GET /events?since=2024-01-15T10:00:00Z&until=2024-01-15T11:00:00Z&limit=100
```

**响应：**
```json
{
  "data": [...],
  "pagination": {
    "since": "2024-01-15T10:00:00Z",
    "until": "2024-01-15T11:00:00Z",
    "limit": 100,
    "has_more": true
  },
  "links": {
    "next": "/events?since=2024-01-15T11:00:00Z&until=2024-01-15T12:00:00Z&limit=100"
  }
}
```

**用于：**
- 时间序列数据
- 日志和事件
- 活动流
- 分析数据

## 默认限制

始终设置合理的默认值和最大限制：

```json
{
  "default_limit": 20,
  "max_limit": 100,
  "min_limit": 1
}
```

**验证：**
```http
GET /users?limit=1000

响应：400 Bad Request
{
  "error": {
    "code": "INVALID_LIMIT",
    "message": "限制必须在 1 到 100 之间。默认为 20。"
  }
}
```

## 响应格式

### 标准分页对象

```json
{
  "data": [...],
  "pagination": {
    "limit": 10,
    "offset": 20,
    "total": 150,
    "has_more": true,
    "has_previous": true
  }
}
```

### 链接头（RFC 5988）

```http
Link: </users?offset=0&limit=10>; rel="first",
      </users?offset=10&limit=10>; rel="prev",
      </users?offset=30&limit=10>; rel="next",
      </users?offset=140&limit=10>; rel="last"
```

**由以下使用：** GitHub API

### 嵌入链接

```json
{
  "data": [...],
  "_links": {
    "self": { "href": "/users?offset=20&limit=10" },
    "first": { "href": "/users?offset=0&limit=10" },
    "prev": { "href": "/users?offset=10&limit=10" },
    "next": { "href": "/users?offset=30&limit=10" },
    "last": { "href": "/users?offset=140&limit=10" }
  }
}
```

## 带排序的分页

分页时始终支持排序：

```http
GET /users?sort=created_at&order=desc&limit=10
GET /users?sort=-created_at&limit=10                    # 降序
GET /users?sort=last_name,first_name&limit=10           # 多字段
```

**对于游标分页，游标必须包含排序字段：**
```json
{
  "cursor": {
    "id": 123,
    "created_at": "2024-01-15T10:30:00Z",
    "sort_fields": ["created_at", "id"]
  }
}
```

## 带过滤的分页

将过滤与分页结合：

```http
GET /users?status=active&role=admin&offset=0&limit=10
```

**重要：** 分页前应用过滤器：
1. 过滤记录
2. 计数过滤后的结果
3. 应用分页
4. 返回分页子集

## 总计数

### 包含总计数

```json
{
  "data": [...],
  "pagination": {
    "total": 1523,
    "limit": 10,
    "offset": 20
  }
}
```

**优点：**
- 客户端知道总结果
- 可以计算总页数
- 更好的 UX（显示"共 153 页，第 3 页"）

**缺点：**
- COUNT 查询昂贵
- 减慢响应
- 大型/更改数据集不准确

### 省略总计数

```json
{
  "data": [...],
  "pagination": {
    "has_more": true,
    "limit": 10
  }
}
```

**用于：**
- 大型数据集（COUNT 太慢）
- 实时数据（计数不断变化）
- 游标分页
- 无限滚动 UI

### 可选总计数

让客户端请求总计数：

```http
GET /users?limit=10&include_total=true
```

## 边缘情况

### 空结果

```json
{
  "data": [],
  "pagination": {
    "offset": 0,
    "limit": 10,
    "total": 0,
    "has_more": false
  }
}
```

### 最后一页

```json
{
  "data": [{"id": 150, "name": "Last User"}],
  "pagination": {
    "offset": 140,
    "limit": 10,
    "total": 150,
    "has_more": false
  },
  "links": {
    "first": "/users?offset=0&limit=10",
    "prev": "/users?offset=130&limit=10",
    "next": null
  }
}
```

### 超出范围

```http
GET /users?offset=10000&limit=10

响应：200 OK（空结果）
{
  "data": [],
  "pagination": {
    "offset": 10000,
    "limit": 10,
    "total": 150,
    "has_more": false
  }
}
```

或为不存在的页面返回 404：
```http
GET /users?page=1000&per_page=10

响应：404 Not Found
{
  "error": {
    "code": "PAGE_NOT_FOUND",
    "message": "第 1000 页不存在。总页数：15"
  }
}
```

## 最佳实践

1. **始终对集合进行分页** - 绝不返回无界列表
2. **设置合理的默认值** - 默认限制 20-50 项
3. **强制最大限制** - 防止过度加载（最大 100-1000）
4. **包含 has_more 标志** - 告诉客户端是否存在更多结果
5. **提供导航链接** - 使获取下一页/上一页容易
6. **记录分页** - 解释游标格式、限制、默认值
7. **保持一致** - 在所有端点使用相同的分页模式
8. **考虑性能** - 根据数据大小/类型选择策略
9. **支持排序** - 让客户端控制结果顺序
10. **处理边缘情况** - 空结果、最后一页、无效游标

## 对比矩阵

| 功能 | 偏移量 | 页码 | 游标 | 键集 |
|---------|--------|------|--------|--------|
| 性能 | 大偏移量差 | 差 | 优秀 | 优秀 |
| 随机访问 | 是 | 是 | 否 | 否 |
| 总计数 | 是 | 是 | 否 | 可选 |
| 一致性 | 差 | 差 | 优秀 | 优秀 |
| 复杂性 | 简单 | 简单 | 中等 | 中等 |
| 实时数据 | 差 | 差 | 优秀 | 优秀 |
| 数据库负载 | 高 | 高 | 低 | 低 |
| 用例 | 小型数据集 | Web UI | 信息流/流 | 大型数据集 |
