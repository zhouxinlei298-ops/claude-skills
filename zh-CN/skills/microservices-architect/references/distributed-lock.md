# Phoenix 分布式锁框架

Phoenix 分布式锁框架是企业内部统一的分布式锁解决方案，提供声明式注解和编程式模板两种使用方式。

## 概述

**Maven 依赖**：
```xml
<dependency>
    <groupId>org.phoenix</groupId>
    <artifactId>phoenix-distributed-lock-core</artifactId>
    <version>${phoenix.version}</version>
</dependency>
```

**支持的锁实现**：
- **Redisson** - 推荐，支持看门狗自动续期
- **RedisTemplate** - 基于 Redis SET NX EX 实现
- **Zookeeper** - 基于临时顺序节点实现

## 配置

在 `application.yml` 中配置：

```yaml
distributed-lock:
  # 锁过期时间（毫秒），防止死锁，默认 30000ms
  expire: 60000
  # 获取锁超时时间（毫秒），默认 3000ms
  acquire-timeout: 5000
  # 获取锁失败重试间隔（毫秒），默认 100ms
  retry-interval: 200
  # 锁 Key 前缀，默认 "lock"
  lock-key-prefix: "phoenix_lock"
  # 主执行器（可选），默认取容器第一个
  primary-executor: org.phoenix.lock.executor.RedissonLockExecutor
```

## 使用方式

### 1. @DistributedLock 注解（声明式）

**注解属性**：

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | String | "" | 锁资源名称，为空则使用"包名+类名+方法名" |
| `keys` | String[] | {} | SpEL 表达式，锁的 key = name + keys |
| `expire` | long | -1 | 过期时间（毫秒），-1 使用默认 30000ms |
| `acquireTimeout` | long | -1 | 获取锁超时（毫秒），-1 使用默认 3000ms |
| `autoRelease` | boolean | true | 方法执行完自动释放锁 |
| `executor` | Class<? extends LockExecutor> | LockExecutor.class | 锁执行器类型 |
| `failureStrategy` | Class<? extends LockFailureStrategy> | DefaultLockFailureStrategy.class | 加锁失败策略 |

**单参数锁**：
```java
@Service
public class ProjectEnterpriseServiceImpl {

    @DistributedLock(keys = {"#p0.projectCode"})
    public Long submitPreBeaconProxyEnterprise(ProjectEnterpriseDTO dto) {
        // 锁 Key: ...ProjectEnterpriseServiceImpl.submitPreBeaconProxyEnterprise:PRJ001
        // 业务逻辑
        return save(dto);
    }
}
```

**多参数组合锁**：
```java
@DistributedLock(keys = {"#p0", "#p1"})
public Boolean processProject(String projectCode, String nodeType) {
    // 锁 Key 包含两个参数
    // ...processProject:PRJ001:PRE_BEACON
    return true;
}
```

**对象属性嵌套**：
```java
@DistributedLock(keys = {"#request.userId", "#request.orderId"})
public Order createOrder(OrderRequest request) {
    // 锁 Key: ...createOrder:USER123:ORD456
    return orderService.save(request);
}
```

**自定义过期时间**：
```java
@DistributedLock(
    keys = {"#p0.orderId"},
    expire = 60000,        // 过期时间 60 秒
    acquireTimeout = 3000  // 获取锁超时 3 秒
)
public Boolean processOrder(String orderId) {
    // 长时间业务逻辑...
    return true;
}
```

**指定锁执行器**：
```java
@DistributedLock(
    keys = {"#p0.id"},
    executor = RedisTemplateLockExecutor.class  // 使用 RedisTemplate 实现
)
public void processData(Long id) {
    // ...
}
```

**SpEL 表达式语法**：

| 表达式 | 说明 |
|--------|------|
| `#p0` | 第一个参数 |
| `#p0.fieldName` | 第一个参数的字段 |
| `#p1['key']` | 第二个参数的 Map 键值 |
| `#user.name` | 命名参数 `user` 的 name 字段 |

### 2. LockTemplate（编程式）

**注入 LockTemplate**：
```java
@Service
@RequiredArgsConstructor
public class TradingAnnouncementServiceImpl {

    private final LockTemplate lockTemplate;

    public Long insideSaveEnhance(TradingAnnouncementDTO dto) {
        LockInfo lockInfo = null;
        try {
            // 构造锁的 key
            String key = String.format("lock:trading_announcement:%s", dto.getObjectId());

            // 获取锁
            // 参数：key, 过期时间(ms), 获取超时(ms), 锁执行器类型
            lockInfo = lockTemplate.lock(key, 600000L, 3000L, RedisTemplateLockExecutor.class);

            if (lockInfo == null) {
                throw new LockedException("交易公告保存获取锁失败");
            }

            log.info("获取锁成功: key={}, value={}", lockInfo.getLockKey(), lockInfo.getLockValue());

            // 执行业务逻辑
            return processTradingAnnouncement(dto);

        } finally {
            // 释放锁
            releaseLock(lockInfo);
        }
    }

    private void releaseLock(LockInfo lockInfo) {
        if (null != lockInfo) {
            log.info("Thread[{}] -> releaseLock key [{}]", lockInfo.getThreadId(), lockInfo.getLockKey());
            boolean released = lockTemplate.releaseLock(lockInfo);
            if (!released) {
                log.error("releaseLock fail, lock Key={}, lock Value={}",
                    lockInfo.getLockKey(), lockInfo.getLockValue());
            }
        }
    }
}
```

**LockTemplate API**：

| 方法 | 说明 |
|------|------|
| `lock(key)` | 使用默认配置获取锁 |
| `lock(key, expire, acquireTimeout)` | 指定过期时间和获取超时 |
| `lock(key, expire, acquireTimeout, executorClass)` | 指定锁执行器 |
| `releaseLock(lockInfo)` | 释放锁 |

**LockInfo 属性**：

| 属性 | 类型 | 说明 |
|------|------|------|
| `threadId` | long | 获取锁的线程 ID |
| `lockKey` | String | 锁的 Key |
| `lockValue` | String | 锁的 Value（UUID） |
| `expire` | Long | 过期时间 |
| `acquireTimeout` | Long | 获取锁超时时间 |
| `acquireCount` | int | 获取锁尝试次数 |
| `lockInstance` | Object | 底层锁实例 |
| `lockExecutor` | LockExecutor | 锁执行器 |

## 锁执行器对比

| 执行器 | 实现方式 | 看门狗 | 性能 | 推荐场景 |
|--------|----------|--------|------|----------|
| **RedissonLockExecutor** | Redisson RLock | ✓ | 高 | 高并发、长任务 |
| **RedisTemplateLockExecutor** | SET NX EX | ✗ | 中 | 简单场景、已有 RedisTemplate |
| **ZookeeperLockExecutor** | 临时顺序节点 | ✓ | 中 | 需要 Zookeeper 的一致性保证 |

## 最佳实践

### 1. 锁粒度设计

**✅ 推荐**：细粒度锁
```java
// 每个项目独立锁
@DistributedLock(keys = {"#p0.projectCode"})
public void updateProject(ProjectDTO dto) { ... }
```

**❌ 不推荐**：粗粒度锁
```java
// 所有项目共用一把锁，并发度低
@DistributedLock
public void updateProject(ProjectDTO dto) { ... }
```

### 2. 过期时间设置

**原则**：过期时间 > 业务执行时间 + 安全余量

```java
// 预估业务 30 秒，设置 60 秒过期
@DistributedLock(keys = {"#p0.id"}, expire = 60000)
public void longRunningTask(Long id) { ... }
```

### 3. 获取锁超时设置

**原则**：高并发场景不宜设置过长，避免请求堆积

```java
// 高并发接口，快速失败
@DistributedLock(keys = {"#p0.id"}, acquireTimeout = 1000)
public void highConcurrencyMethod(Long id) { ... }
```

### 4. 异常处理

```java
public Long saveData(DataDTO dto) {
    LockInfo lockInfo = null;
    try {
        lockInfo = lockTemplate.lock("key", 30000L, 3000L);
        if (lockInfo == null) {
            // 获取锁失败，返回错误或重试
            throw new BusinessException("系统繁忙，请稍后重试");
        }
        // 业务逻辑
        return doSave(dto);
    } finally {
        // 确保锁释放
        if (lockInfo != null) {
            lockTemplate.releaseLock(lockInfo);
        }
    }
}
```

### 5. 避免死锁

```java
// ✅ 正确：锁在 try-finally 中获取和释放
LockInfo lockInfo = lockTemplate.lock(key);
try {
    // 业务逻辑
} finally {
    lockTemplate.releaseLock(lockInfo);
}

// ❌ 错误：异常时锁不会释放
LockInfo lockInfo = lockTemplate.lock(key);
doSomething();  // 如果抛异常，锁不会释放
lockTemplate.releaseLock(lockInfo);
```

### 6. 嵌套锁慎用

```java
// ❌ 可能死锁：线程 A 持有 lock1 等待 lock2，线程 B 持有 lock2 等待 lock1
@DistributedLock(keys = {"#p0.id1"})
public void method1(Long id1, Long id2) {
    method2(id1, id2);
}

@DistributedLock(keys = {"#p1.id2"})
public void method2(Long id1, Long id2) {
    // ...
}

// ✅ 解决：按相同顺序获取锁
@DistributedLock(keys = {"#p0 < #p1 ? #p0 : #p1"})
public void method(Long id1, Long id2) {
    // 始终按小 ID 先加锁
}
```

## 常见问题

### Q1: 为什么获取锁返回 null？

- 超过 `acquireTimeout` 时间仍未获取到锁
- 检查锁的持有时间是否过长
- 检查 `acquireTimeout` 设置是否合理

### Q2: Redisson 和 RedisTemplate 选择哪个？

- **Redisson**：推荐，支持看门狗自动续期，适合长任务
- **RedisTemplate**：简单场景，需要手动设置合适的过期时间

### Q3: 如何实现可重入锁？

当前框架不支持可重入锁。如需可重入，请：
1. 使用 Redisson 的 RLock（原生支持）
2. 或在业务层使用计数器手动实现

### Q4: 锁的 Key 是怎么生成的？

```
lockKey = lockKeyPrefix + ":" + name + ":" + SpEL(keys)
```

例如：
```java
@DistributedLock(name = "order", keys = {"#p0.id"})
// lockKey = "lock:order:123"

@DistributedLock(keys = {"#p0.projectCode"})  // name 为空
// lockKey = "lock:com.example.Service.method:PRJ001"
```
