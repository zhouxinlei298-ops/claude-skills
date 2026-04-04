# Redis 最佳实践指南

> Redis 是高性能的键值存储系统，广泛用于缓存、分布式锁、排行榜等场景。

## 📋 目录

- [数据类型与使用场景](#数据类型与使用场景)
- [缓存模式](#缓存模式)
- [分布式锁](#分布式锁)
- [常见问题与解决方案](#常见问题与解决方案)
- [性能优化](#性能优化)
- [生产环境配置](#生产环境配置)

---

## 数据类型与使用场景

### String（字符串）

**适用场景**：简单 KV、计数器、分布式锁、Session 存储

```bash
# 设置键值（带过期时间）
SET user:session:123 "token_data" EX 3600

# 计数器
INCR article:views:456
DECR user:credits:789

# 原子操作（GETSET）
GETSET lock:order:123 "locked"
```

### Hash（哈希）

**适用场景**：对象存储（如用户信息、商品详情）

```bash
# 存储用户信息
HSET user:1001 name "张三" email "zhang@example.com" age 28

# 获取单个字段
HGET user:1001 name

# 获取所有字段
HGETALL user:1001

# 批量设置
HMSET user:1001 name "李四" email "li@example.com" age 30
```

**优势**：
- 内存占用比多个 String 键更小
- 支持 HGETALL 一次性获取整个对象

### List（列表）

**适用场景**：消息队列（轻量）、最新列表、关注列表

```bash
# 左侧推入（LPUSH）
LPUSH queue:tasks "task1" "task2" "task3"

# 右侧弹出（RPOP）- FIFO 队列
RPOP queue:tasks

# 阻塞弹出（生产环境推荐）
BRPOP queue:tasks 0  # 永久阻塞

# 获取列表范围（分页）
LRANGE recent:users 0 9
```

**注意**：List 不支持消息确认机制，生产环境建议使用 Kafka/RabbitMQ。

### Set（集合）

**适用场景**：去重、标签、交集/并集运算

```bash
# 添加元素
SADD user:1001:tags "java" "redis" "microservices"

# 判断是否存在
SISMEMBER user:1001:tags "redis"  # 返回 1

# 交集运算（共同关注）
SINTER user:1001:following user:1002:following

# 并集运算（推荐好友）
SUNION user:1001:friends user:1002:friends
```

### ZSet（有序集合）

**适用场景**：排行榜、延时队列、优先级队列

```bash
# 添加成员（分数 + 成员）
ZADD leaderboard:game 1000 "player1" 850 "player2" 920 "player3"

# 获取排名（升序）
ZRANGE leaderboard:game 0 9 WITHSCORES

# 获取排名（降序，从高到低）
ZREVRANGE leaderboard:game 0 9 WITHSCORES

# 获取成员排名
ZREVRANK leaderboard:game "player1"  # 返回排名（从 0 开始）

# 延时队列（时间戳作为分数）
ZADD delay:queue 1709420400 "order:123" 1709420400 "order:456"
```

---

## 缓存模式

### 1. Cache-Aside（旁路缓存）

**最常用的缓存模式**

```go
// ✅ 读取流程
func GetUser(ctx context.Context, userID int64) (*User, error) {
    // 1. 先查缓存
    cacheKey := fmt.Sprintf("user:%d", userID)
    cached, err := redis.Get(ctx, cacheKey).Result()
    if err == nil {
        var user User
        json.Unmarshal([]byte(cached), &user)
        return &user, nil
    }

    // 2. 缓存未命中，查数据库
    user, err := db.QueryUser(ctx, userID)
    if err != nil {
        return nil, err
    }

    // 3. 写入缓存（设置过期时间）
    data, _ := json.Marshal(user)
    redis.Set(ctx, cacheKey, data, 30*time.Minute)

    return user, nil
}

// ✅ 更新流程
func UpdateUser(ctx context.Context, user *User) error {
    // 1. 先更新数据库
    if err := db.UpdateUser(ctx, user); err != nil {
        return err
    }

    // 2. 删除缓存（而非更新）
    cacheKey := fmt.Sprintf("user:%d", user.ID)
    redis.Del(ctx, cacheKey)

    return nil
}
```

**为什么更新时删除缓存而非更新缓存？**
- 避免并发写导致数据不一致
- 删除成本低于更新成本（序列化开销）

### 2. Read-Through / Write-Through

由缓存层统一管理数据读写，应用层只需与缓存交互。

```go
// Read-Through 示例（伪代码）
func GetUser(ctx context.Context, userID int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", userID)

    // 缓存层负责：先查缓存，未命中则查数据库并回填
    return cacheManager.GetOrLoad(ctx, cacheKey, func() (*User, error) {
        return db.QueryUser(ctx, userID)
    })
}
```

### 3. Write-Behind（异步写）

写入操作先更新缓存，由后台任务异步批量写入数据库。

**优点**：极致性能
**缺点**：可能丢数据，适合对一致性要求不高的场景

---

## 分布式锁

### Redis 分布式锁实现

```go
package lock

import (
    "context"
    "errors"
    "time"

    "github.com/go-redis/redis/v8"
)

var (
    ErrLockFailed = errors.New("lock: failed to acquire lock")
)

// RedisLock 分布式锁
type RedisLock struct {
    client *redis.Client
}

// Acquire 获取锁（SET NX EX 原子操作）
func (l *RedisLock) Acquire(ctx context.Context, key string, expiration time.Duration) (bool, error) {
    // ✅ 使用 SET NX EX 原子操作（避免竞态条件）
    result, err := l.client.SetNX(ctx, key, "1", expiration).Result()
    if err != nil {
        return false, err
    }
    return result, nil
}

// Release 释放锁（Lua 脚本保证原子性）
func (l *RedisLock) Release(ctx context.Context, key string) error {
    // ✅ Lua 脚本：检查锁是否属于当前客户端，是则删除
    script := `
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    `
    return l.client.Eval(ctx, script, []string{key}, "1").Err()
}

// 使用示例
func ProcessOrder(ctx context.Context, orderID int64) error {
    lock := &RedisLock{client: redisClient}
    key := fmt.Sprintf("lock:order:%d", orderID)

    // 获取锁（过期时间 10 秒）
    acquired, err := lock.Acquire(ctx, key, 10*time.Second)
    if err != nil {
        return err
    }
    if !acquired {
        return errors.New("order is being processed")
    }
    defer lock.Release(ctx, key)

    // 处理订单...
    return nil
}
```

### Redlock 算法（多节点锁）

对于高可用要求场景，使用 Redlock 算法在多个 Redis 实例上加锁：

```go
// 使用 redigo/redlock 库
func AcquireRedlock(key string, expiration time.Duration) error {
    lock, err := redlock.NewRedlock(
        &redis.Client{Addr: "redis1:6379"},
        &redis.Client{Addr: "redis2:6379"},
        &redis.Client{Addr: "redis3:6379"},
    )
    if err != nil {
        return err
    }

    return lock.Acquire(key, expiration)
}
```

---

## 常见问题与解决方案

### 1. 缓存穿透（查询不存在的数据）

**场景**：恶意查询不存在的 Key，导致请求直接打到数据库

**解决方案**：

```go
// 方案1：缓存空值
func GetUser(ctx context.Context, userID int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", userID)

    // 查缓存（包括空值）
    cached, err := redis.Get(ctx, cacheKey).Result()
    if err == nil {
        if cached == "NULL" {  // 空值标记
            return nil, ErrUserNotFound
        }
        return parseUser(cached), nil
    }

    // 查数据库
    user, err := db.QueryUser(ctx, userID)
    if errors.Is(err, sql.ErrNoRows) {
        // 缓存空值（较短过期时间）
        redis.Set(ctx, cacheKey, "NULL", 5*time.Minute)
        return nil, ErrUserNotFound
    }

    // 缓存正常数据
    redis.Set(ctx, cacheKey, user, 30*time.Minute)
    return user, nil
}

// 方案2：布隆过滤器
func initBloomFilter() {
    bf := bloom.NewWithEstimates(1000000, 0.001)  // 100万元素，0.1% 误判率

    // 预加载所有有效 Key
    users := db.GetAllUserIDs()
    for _, id := range users {
        bf.AddString(fmt.Sprintf("user:%d", id))
    }

    globalBloomFilter = bf
}

func GetUser(ctx context.Context, userID int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", userID)

    // 布隆过滤器预判
    if !globalBloomFilter.TestString(cacheKey) {
        return nil, ErrUserNotFound  // 直接返回，不查数据库
    }

    // 正常查询流程...
}
```

### 2. 缓存击穿（热点 Key 过期）

**场景**：热点 Key 过期瞬间，大量请求同时打到数据库

**解决方案**：

```go
// 方案1：互斥锁
func GetUser(ctx context.Context, userID int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", userID)

    // 查缓存
    cached, err := redis.Get(ctx, cacheKey).Result()
    if err == nil {
        return parseUser(cached), nil
    }

    // 获取互斥锁
    lockKey := fmt.Sprintf("lock:%s", cacheKey)
    acquired, _ := redis.SetNX(ctx, lockKey, "1", 10*time.Second).Result()
    if acquired {
        defer redis.Del(ctx, lockKey)

        // 双重检查（其他 goroutine 可能已加载）
        cached, err = redis.Get(ctx, cacheKey).Result()
        if err == nil {
            return parseUser(cached), nil
        }

        // 查数据库
        user, err := db.QueryUser(ctx, userID)
        if err != nil {
            return nil, err
        }

        // 写缓存
        redis.Set(ctx, cacheKey, user, 30*time.Minute)
        return user, nil
    }

    // 未获取锁，等待后重试
    time.Sleep(50 * time.Millisecond)
    return GetUser(ctx, userID)  // 递归重试
}

// 方案2：热点数据永不过期（后台异步更新）
func StartHotDataRefresh() {
    go func() {
        ticker := time.NewTicker(5 * time.Minute)
        for range ticker.C {
            hotKeys := getHotKeys()  // 获取热点 Key
            for _, key := range hotKeys {
                data := db.QueryByKey(key)
                redis.Set(context.Background(), key, data, 30*time.Minute)
            }
        }
    }()
}
```

### 3. 缓存雪崩（大量 Key 同时过期）

**场景**：大量 Key 设置了相同的过期时间，同时失效导致数据库压力激增

**解决方案**：

```go
// ✅ 过期时间加随机值（避免同时过期）
func SetCacheWithRandomExpire(ctx context.Context, key string, value interface{}) {
    baseExpire := 30 * time.Minute
    randomJitter := time.Duration(rand.Intn(300)) * time.Second  // 0-5分钟随机

    redis.Set(ctx, key, value, baseExpire+randomJitter)
}

// ✅ 多级缓存（本地缓存 + Redis）
var localCache = lru.New(1000)  // 本地 LRU 缓存

func GetUser(ctx context.Context, userID int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", userID)

    // 1. 本地缓存
    if val, ok := localCache.Get(cacheKey); ok {
        return val.(*User), nil
    }

    // 2. Redis 缓存
    cached, err := redis.Get(ctx, cacheKey).Result()
    if err == nil {
        user := parseUser(cached)
        localCache.Add(cacheKey, user)  // 回填本地缓存
        return user, nil
    }

    // 3. 数据库
    user, err := db.QueryUser(ctx, userID)
    if err != nil {
        return nil, err
    }

    // 回填缓存
    redis.Set(ctx, cacheKey, user, 30*time.Minute)
    localCache.Add(cacheKey, user)

    return user, nil
}
```

---

## 性能优化

### 1. Pipeline（管道）

批量执行命令，减少网络往返

```go
// ❌ 逐条执行（N 次网络往返）
for _, id := range userIDs {
    redis.Get(ctx, fmt.Sprintf("user:%d", id))
}

// ✅ Pipeline 批量执行（1 次网络往返）
pipe := redis.Pipeline()
cmds := make([]*redis.StringCmd, len(userIDs))

for i, id := range userIDs {
    cmds[i] = pipe.Get(ctx, fmt.Sprintf("user:%d", id))
}

pipe.Exec(ctx)  // 批量发送

for _, cmd := range cmds {
    user, _ := cmd.Result()
    // 处理结果...
}
```

### 2. 优化 Key 命名

**规范**：`业务:模块:唯一标识`

```bash
# ✅ 好的命名
user:profile:123
user:session:456
order:detail:789
lock:payment:order:999

# ❌ 避免的命名
user123profile                    # 无分隔符，难以管理
u:p:123                          # 过于简略
user:profile:2024-03-25:123      # 避免在 Key 中包含时间
```

### 3. 避免大 Key

```bash
# ❌ 大 Key（单个 Hash 存储百万字段）
HGETALL huge:object

# ✅ 拆分为多个小 Key
HGETALL user:1001:profile
HGETALL user:1001:settings
HGETALL user:1001:permissions
```

### 4. 禁用危险命令

**生产环境禁用**：`KEYS`、`FLUSHDB`、`FLUSHALL`

```conf
# redis.conf
rename-command KEYS ""
rename-command FLUSHDB ""
rename-command FLUSHALL ""
```

使用 `SCAN` 替代 `KEYS`：

```go
// ✅ 使用 SCAN 遍历
var cursor uint64
for {
    var keys []string
    var err error

    keys, cursor, err = redis.Scan(ctx, cursor, "user:*", 100).Result()
    if err != nil {
        break
    }

    // 处理 keys...

    if cursor == 0 {
        break
    }
}
```

---

## 生产环境配置

### 内存优化

```conf
# redis.conf
maxmemory 2gb                    # 最大内存限制
maxmemory-policy allkeys-lru     # 内存淘汰策略：LRU

# 淘汰策略选择：
# - volatile-lru：淘汰设置了 TTL 的 Key 中最少使用的
# - allkeys-lru：淘汰所有 Key 中最少使用的（推荐）
# - volatile-ttl：淘汰即将过期的 Key
# - noeviction：不淘汰，内存满时返回错误
```

### 持久化配置

```conf
# RDB（快照）- 适合备份
save 900 1      # 900 秒内至少 1 个写操作
save 300 10     # 300 秒内至少 10 个写操作
save 60 10000   # 60 秒内至少 10000 个写操作

rdbcompression yes               # 压缩 RDB 文件
dbfilename dump.rdb
dir /var/lib/redis

# AOF（追加日志）- 适合恢复
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec             # 每秒同步（推荐）
```

**选型建议**：
- **缓存场景**：可关闭持久化，或仅使用 RDB
- **存储场景**：使用 AOF + RDB 混合持久化

### 连接池配置

```go
// Go-Redis 客户端配置
client := redis.NewClient(&redis.Options{
    Addr:         "localhost:6379",
    Password:     "",
    DB:           0,
    PoolSize:     100,              // 连接池大小
    MinIdleConns: 10,               // 最小空闲连接
    MaxRetries:   3,                // 最大重试次数
    DialTimeout:  5 * time.Second,
    ReadTimeout:  3 * time.Second,
    WriteTimeout: 3 * time.Second,
    PoolTimeout:  4 * time.Second,
})
```

---

## 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| **内存使用率** | `used_memory / maxmemory` | > 80% |
| **命中率** | `(keyspace_hits / (keyspace_hits + keyspace_misses))` | < 80% |
| **响应时间** | 单次命令平均耗时 | > 10ms |
| **连接数** | `connected_clients` | > 80% 最大连接数 |
| **阻塞操作** | `blocked_clients` | > 0 |
| **过期 Key** | `expired_keys` | 监控趋势 |

---

## 常见问题排查

### 1. 慢查询

```bash
# 启用慢查询日志（阈值 10ms）
CONFIG SET slowlog-log-slower-than 10000
CONFIG SET slowlog-max-len 128

# 查看慢查询
SLOWLOG GET 10
```

### 2. 内存碎片

```bash
# 查看内存碎片率
INFO memory
# mem_fragmentation_ratio > 1.5 表示碎片严重

# 重启 Redis 或执行碎片整理（Redis 4.0+）
MEMORY PURGE
```

### 3. 连接数泄漏

```bash
# 查看客户端连接
CLIENT LIST

# 杀死指定连接
KILL IP:PORT
```
