# 弹性和可靠性模式

构建容错分布式系统的基本模式。

## 弹性模式

### 断路器

**目的：** 当依赖项不健康时，通过快速失败来防止级联故障。

**工作原理：**
```
状态：
1. 关闭（正常操作）
   - 请求通过
   - 跟踪失败率
   - 如果故障超过阈值 → 打开

2. 打开（快速失败）
   - 立即拒绝请求
   - 返回降级响应
   - 超时后 → 半开

3. 半开（测试恢复）
   - 允许有限的测试请求
   - 如果成功 → 关闭
   - 如果失败 → 打开

配置：
- 失败阈值：10 次请求中有 50% 故障
- 超时时间：在打开状态下 30 秒
- 成功阈值：半开状态下连续 2 次成功
```

**实现示例：**
```python
# 使用 resilience4j 类似的模式
@CircuitBreaker(
    name="payment-service",
    fallbackMethod="paymentFallback",
    failureThreshold=50,
    waitDurationInOpenState=30000,  # 30s
    permittedNumberOfCallsInHalfOpenState=3
)
async def process_payment(order_id: str, amount: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENT_SERVICE_URL}/payments",
            json={"orderId": order_id, "amount": amount},
            timeout=5.0
        )
        return response.json()

async def paymentFallback(order_id: str, amount: float, exception):
    # 记录失败
    logger.error(f"支付服务不可用：{exception}")
    # 返回优雅降级
    return {
        "status": "pending",
        "message": "付款处理延迟，将重试"
    }
```

**何时使用：**
```
对断路器应用：
✓ 外部服务调用
✓ 数据库查询
✓ 第三方 API
✓ 微服务到微服务调用
✓ 同步调用的数据库

配置指南：
- 快速服务（p99 < 100ms）：5s 超时，10 次电路打开
- 中等服务（p99 < 1s）：10s 超时，30s 电路打开
- 慢服务（p99 > 1s）：30s 超时，60s 电路打开
```

### 重试模式

**目的：** 通过重试操作来处理瞬态故障。

**策略：**

**1. 指数退避：**
```
重试延迟：100ms、200ms、400ms、800ms、1600ms

优点：
- 事件发生期间减少负载
- 给服务时间恢复
- 防止惊群效应

实现：
attempts = 0
max_attempts = 5
base_delay = 0.1  # 100ms

while attempts < max_attempts:
    try:
        return await make_request()
    except TransientError as e:
        attempts += 1
        if attempts == max_attempts:
            raise
        delay = base_delay * (2 ** attempts) + random.uniform(0, 0.1)
        await asyncio.sleep(delay)
```

**2. 带抖动的重试：**
```
为什么：防止同步重试（惊群效应）

完全抖动：
delay = random.uniform(0, base_delay * (2 ** attempt))

装饰抖动：
delay = min(cap, random.uniform(base, previous_delay * 3))

推荐：生产系统使用装饰抖动
```

**3. 幂等性密钥：**
```
问题：重试可能导致重复操作

解决方案：幂等性密钥

POST /api/v1/payments
Headers:
  Idempotency-Key: uuid-12345

服务器逻辑：
1. 检查具有此密钥的操作是否已处理
2. 如果是，返回缓存响应
3. 如果否，处理并缓存结果
4. 缓存 24 小时

确保即使非幂等操作也能安全重试
```

**重试最佳实践：**
```
应该做：
✓ 仅重试瞬态错误（超时、503、429）
✓ 使用带有抖动的指数退避
✓ 设置最大重试次数（3-5 次）
✓ 实施整体超时
✓ 为写入使用幂等性密钥
✓ 记录每次重试尝试

不应该做：
✗ 重试客户端错误（400、401、404）
✗ 无退避的重试（导致负载高峰）
✗ 无限次重试
✗ 没有保护的幂等操作重试
```

### 隔离模式

**目的：** 隔离资源以防止系统完全故障。

**线程池隔离：**
```
概念：不同操作使用独立的线程池

示例：
- 支付服务线程池：20 个线程
- 库存服务线程池：20 个线程
- 通知服务线程池：10 个线程

如果支付服务变慢：
- 仅支付线程池耗尽
- 库存和通知服务仍然工作
- 系统部分降级，非完全故障
```

**连接池隔离：**
```
数据库连接池：
- 只读查询：50 个连接
- 写入查询：20 个连接
- 报告查询：10 个连接

繁重的报表查询不会消耗事务性操作
```

**每租户限流：**
```
多租户 SaaS 应用：

tenant-a: 1000 请求/分钟
tenant-b: 10000 请求/分钟
tenant-c: 1000 请求/分钟

如果 tenant-a 泛滥系统：
- 仅限流 tenant-a
- tenant-b 和 tenant-c 不受影响
```

**实现：**
```python
# 使用信号量实现并发限制
class BulkheadExecutor:
    def __init__(self):
        self.payment_semaphore = asyncio.Semaphore(20)
        self.inventory_semaphore = asyncio.Semaphore(20)
        self.notification_semaphore = asyncio.Semaphore(10)

    async def call_payment_service(self, data):
        async with self.payment_semaphore:
            return await payment_service.call(data)

    async def call_inventory_service(self, data):
        async with self.inventory_semaphore:
            return await inventory_service.call(data)
```

### 超时模式

**目的：** 防止响应无限等待。

**超时类型：**

**1. 连接超时：**
```
建立连接所允许的时间

推荐：2-5 秒
如果耗时更长，网络可能存在问题

httpx.AsyncClient(timeout=httpx.Timeout(connect=3.0))
```

**2. 读取超时：**
```
在建立连接后接收响应所允许的时间

因服务而异：
- 快速 API：5 秒
- 数据库查询：10 秒
- 复杂处理：30 秒

httpx.AsyncClient(timeout=httpx.Timeout(read=10.0))
```

**3. 整体超时：**
```
整个操作的时间预算

示例：用户结账流程
- 总预算：30 秒
- 支付服务：10 秒
- 库存检查：5 秒
- 订单创建：5 秒
- 缓冲：10 秒

async with asyncio.timeout(30):
    result = await complete_checkout()
```

**超时最佳实践：**
```
超时层次：
父超时 > 子超时总和

请求 → API 网关（30s 超时）
  → 服务 A（10s 超时）
    → 服务 B（5s 超时）
      → 数据库（2s 超时）

随处设置超时：
✓ HTTP 客户端
✓ 数据库连接
✓ 消息消费者
✓ gRPC 调用
✓ 缓存操作
```

## 分布式事务模式

### Saga 模式

**目的：** 管理跨服务的事务。

**事件编排的 Saga：**
```
示例：订单创建 Saga

事件：
1. OrderService: order.created
2. PaymentService: payment.completed 或 payment.failed
3. InventoryService: inventory.reserved 或 inventory.reservation.failed
4. ShippingService: shipment.created

补偿事务：
如果 inventory.reservation.failed：
  → PaymentService 监听 → refund.initiated
  → OrderService 监听 → order.cancelled

优点：
- 去中心化
- 无单点故障
- 服务自主

缺点：
- 难以跟踪 saga 状态
- 复杂的调试
- 无集中监控
- 最终一致性挑战
```

**编排的 Saga：**
```
示例：订单 Saga 编排器

Saga 步骤：
1. 创建订单（OrderService）
2. 充值支付（PaymentService）
3. 预留库存（InventoryService）
4. 创建发货（ShippingService）

编排器逻辑：
step1_result = await order_service.create_order()
if not step1_result.success:
    return failure("订单创建失败")

step2_result = await payment_service.charge(amount)
if not step2_result.success:
    await order_service.cancel_order(step1_result.order_id)
    return failure("支付失败")

step3_result = await inventory_service.reserve(items)
if not step3_result.success:
    await payment_service.refund(step2_result.payment_id)
    await order_service.cancel_order(step1_result.order_id)
    return failure("库存不足")

# 继续 saga...
```

**Saga 状态管理：**
```
将 saga 状态持久化以处理失败：

CREATE TABLE saga_instances (
    saga_id UUID PRIMARY KEY,
    saga_type VARCHAR(50),
    current_step VARCHAR(50),
    status VARCHAR(20),
    payload JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

编排器重启时：
- 加载未完成的 saga
- 从最后完成的步骤恢复
- 执行剩余步骤或补偿
```

### 事件溯源

**目的：** 将所有状态更改作为事件存储，通过重放推导当前状态。

**实现：**
```
传统方法：
UPDATE orders SET status = 'shipped' WHERE id = 123;
(已发货时，由谁，从哪里)

事件溯源方法：
事件：
1. OrderPlaced { orderId, customerId, items, timestamp }
2. PaymentReceived { orderId, amount, paymentId, timestamp }
3. OrderShipped { orderId, trackingNumber, carrier, timestamp }

当前状态 = 重放所有事件
```

**事件存储：**
```
CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    aggregate_id UUID,
    aggregate_type VARCHAR(50),
    event_type VARCHAR(100),
    event_data JSONB,
    version INTEGER,
    timestamp TIMESTAMP,
    correlation_id UUID
);

CREATE INDEX idx_aggregate ON events(aggregate_id, version);
```

**好处：**
```
✓ 完整审计踪
✓ 时间旅行（重放到任意点）
✓ 从同一事件创建多个读取模型
✓ 临时查询（"昨天的订单是什么状态"）

挑战：
✗ 最终一致性
✗ 事件模式演进
✗ 快照策略
✗ 增加的存储
```

### CQRS（命令查询责任分离）

**目的：** 为不同的优化策略分离读和写模型。

**架构：**
```
写端（命令）：
- 接收命令（CreateOrder、UpdateInventory）
- 验证业务规则
- 将事件存储到事件存储
- 为一致性优化写入

读端（查询）：
- 监听事件
- 更新非规范化的读模型
- 为查询进行优化

示例：命令
命令：CreateOrder
  → Order aggregate 验证
  → 发布 OrderCreated 事件

读端：多个专用视图
  1. 订单详情视图（面向客户）
  2. 订单列表视图（面向管理员）
  3. 订单分析视图（聚合指标）

每个视图为特定查询模式优化
```

**读模型：**
```
针对不同用途的多个专用视图：

1. 订单详情视图：
   { orderId, customerName, orderDate, total, items, status }

2. 订单列表视图：
   { orderId, customerName, orderDate, status, total }

3. 分析视图：
   { date, totalOrders, totalRevenue, averageOrderValue }

每个视图针对特定查询模式优化
```

## 容错模式

### 健康检查

**类型：**

**1. 存活探测：**
```
目的：服务是否存活？

端点：GET /health/live

返回 200 如果：
- 应用进程正在运行
- 未死锁

Kubernetes 操作：
- 如果失败：重启容器
```

**2. 就绪探测：**
```
目的：服务是否准备好接收流量？

端点：GET /health/ready

返回 200 如果：
- 数据库连接池健康
- 缓存可访问
- 下游服务响应

Kubernetes 操作：
- 如果失败：从负载均衡器移除
```

**3. 启动探测：**
```
目的：服务是否已完成初始化？

端点：GET /health/startup

用于启动缓慢的应用：
- 防止过早的存活探测失败
- 允许更长的启动时间
```

**实现：**
```python
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness():
    checks = {
        "database": await check_database(),
        "cache": await check_cache(),
        "payment_service": await check_payment_service()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_healthy else "not ready", "checks": checks}
    )
```

### 优雅降级

**目的：** 当依赖失败时提供降级的功能。

**策略：**

**1. 缓存响应：**
```
async def get_product_recommendations(user_id):
    try:
        async with circuit_breaker:
            return await ml_service.get_recommendations(user_id)
    except ServiceUnavailable:
        # 降级到热门产品缓存
        return await cache.get_popular_products()
```

**2. 默认值：**
```
async def get_user_preferences(user_id):
    try:
        return await preferences_service.get(user_id)
    except ServiceUnavailable:
        # 返回合理的默认值
        return {
            "language": "en",
            "currency": "USD",
            "theme": "light"
        }
```

**3. 功能开关：**
```
if feature_flags.is_enabled("personalized_recommendations"):
    recommendations = await ml_service.get_recommendations()
else:
    # 降级到简单算法
    recommendations = await get_popular_products()
```

## 总结

弹性模式对于分布式系统是强制性的。分层应用多种模式进行深度防御：

**基本栈：**
1. 超时（防止挂起）
2. 重试（处理瞬态错误）
3. 断路器（防止级联故障）
4. 隔离（隔离故障）
5. 健康检查（启用自动修复）
6. 优雅降级（维持部分功能）

**选择 Saga 模式当：**
- 需要分布式事务
- 强一致性不是必需的
- 可以进行补偿事务

**选择事件溯源当：**
- 需要完整审计踪迹
- 需要时间旅行（重放历史）
- 可以从同一事件创建多个读模型

**始终测试故障场景。** 使用混沌工程验证弹性模式。
