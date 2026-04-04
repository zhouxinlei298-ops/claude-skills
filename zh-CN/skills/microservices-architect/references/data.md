# 微服务中的数据管理

管理分布式服务数据的全面指南。

## 基本原则

### 每个服务一个数据库

**核心原则：** 每个微服务独占拥有其数据。

**规则：**
```
✓ 应该做：
- 每个服务有自己的数据库/模式
- 服务对其数据拥有所有 CRUD 操作
- 其他服务仅通过 API 访问数据
- 服务可以选择自己的数据库技术

✗ 不应该做：
- 在服务之间共享数据库
- 跨服务直接数据库查询
- 共享表或模式
- 跨服务的数据库级联接
```

**实现选项：**

**1. 独立数据库实例：**
```
UserService → PostgreSQL 实例 1
OrderService → PostgreSQL 实例 2
InventoryService → PostgreSQL 实例 3

优点：
- 完全隔离
- 独立扩展
- 无共享资源争用

缺点：
- 更高的基础设施成本
- 更多的运营开销
```

**2. 独立模式：**
```
同一个 PostgreSQL 实例：
- 模式：user_service
- 模式：order_service
- 模式：inventory_service

优点：
- 更低的成本
- 更容易本地开发

缺点：
- 共享资源（CPU、内存）
- 非真正的隔离
- 扩展限制

推荐：开发/测试使用独立模式，生产环境使用独立实例
```

**3. 多语言持久化：**
```
每个服务选择最佳的数据库：

UserService → PostgreSQL
  （关系型数据、ACID 事务）

ProductCatalog → Elasticsearch
  （全文搜索、分面导航）

SessionStore → Redis
  （快速键值、TTL 支持）

EventLog → Kafka
  （事件流、重放）

RecommendationEngine → MongoDB
  （灵活模式、非规范化数据）

好处：为工作选择合适的工具
挑战：需要管理多种技术
```

## 数据一致性模式

### 强一致性 vs 最终一致性

**强一致性：**
```
定义：写入后读取返回最新值

要求：
- 分布式事务（2PC、3PC）
- 跨服务协调
- 阻塞操作

成本：
- 更高的延迟
- 降低可用性（CAP 定理）
- 复杂性

何时使用：
- 金融事务
- 库存预留
- 关键业务操作
- 监管要求
```

**最终一致性：**
```
定义：系统随时间收敛到一致状态

特征：
- 暂时不一致性可接受
- 非阻塞操作
- 更高的可用性
- 更低的延迟

示例：
1. 下单（OrderService）
2. 立即向用户返回成功
3. 发布事件：order.created
4. InventoryService 最终处理事件
5. 库存计数更新（几毫秒后）

何时使用：
- 社交媒体源
- 分析仪表板
- 推荐系统
- 非关键更新
```

### 管理跨服务数据

**问题：** 订单服务需要用户服务拥有的客户数据。

**反模式解决方案：**
```
✗ 直接数据库访问
✗ 共享数据库
✗ 服务间数据库复制
```

**正确解决方案：**

**1. API 组合：**
```
客户端查询：获取带有客户详情的订单

API 网关：
1. 从 OrderService 获取 /orders/123
   响应：{ orderId: 123, customerId: 456, items: [...] }

2. 从 UserService 获取 /customers/456
   响应：{ customerId: 456, name: "John", email: "john@example.com" }

3. 合并响应并返回给客户端

优点：
- 维护服务边界
- 实时数据

缺点：
- 多次网络调用（延迟）
- 部分失败处理复杂
- N+1 查询问题
```

**2. 通过事件进行数据复制：**
```
OrderService 维护非规范化的客户数据：

CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    customer_id UUID,
    customer_name VARCHAR(255),  -- 非规范化
    customer_email VARCHAR(255), -- 非规范化
    order_total DECIMAL,
    created_at TIMESTAMP
);

UserService 发布事件：
- customer.created
- customer.updated
- customer.deleted

OrderService 订阅并更新本地副本：

async def on_customer_updated(event):
    await db.execute(
        "UPDATE orders SET customer_name = $1, customer_email = $2 WHERE customer_id = $3",
        event.name, event.email, event.customer_id
    )

优点：
- 快速查询（无跨服务联接）
- 对 UserService 停机时间有弹性

缺点：
- 最终一致性
- 存储重复
- 保持数据同步
```

**3. 使用共享读模型的 CQRS：**
```
写模型（命令侧）：
- UserService 写入 user_db
- OrderService 写入 order_db

读模型（查询侧）：
- 用于查询的专用数据库
- 订阅两个服务的事件
- 用于高效查询的非规范化视图

示例读模型：
CREATE TABLE order_details_view (
    order_id UUID,
    customer_id UUID,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    items JSONB,
    order_total DECIMAL,
    order_status VARCHAR(50)
);

优点：
- 为查询优化
- 无跨服务调用
- 可从事件重建

缺点：
- 最终一致性
- 额外基础设施
- 需要事件重放机制
```

## 分布式事务

### 两阶段提交（2PC）

**工作原理：**
```
阶段 1：准备
协调器询问所有参与者："你能提交吗？"
- 服务 A：是
- 服务 B：是
- 服务 C：是

阶段 2：提交
如果全都是：
  协调器告诉所有人："提交"
如果有任何否：
  协调器告诉所有人："回滚"

示例：
从账户 A 转账 $100 到账户 B

准备：
- AccountService A：可以扣除 $100 吗？是（余额充足）
- AccountService B：可以添加 $100 吗？是（账户活跃）

提交：
- AccountService A：扣除 $100（已提交）
- AccountService B：添加 $100（已提交）
```

**2PC 的问题：**
```
✗ 阻塞协议（参与者等待协调器）
✗ 单点故障（协调器宕机 = 全部阻塞）
✗ 降低可用性
✗ 性能差（同步协调）
✗ 扩展性不好

推荐：在微服务中避免 2PC，改用 Saga 模式
```

### Saga 模式（推荐）

**基于编排的 Saga：**
```
转账资金 Saga：

步骤：
1. 借记账户 A
2. 贷记账户 B

补偿：
1. 贷记账户 A（逆向借记）

Saga 编排器：
saga_state = {
    "saga_id": "saga-123",
    "status": "in_progress",
    "steps_completed": []
}

# 步骤 1
result1 = await account_service.debit(account_a, 100)
if not result1.success:
    return fail_saga("资金不足")

saga_state["steps_completed"].append("debit_a")

# 步骤 2
result2 = await account_service.credit(account_b, 100)
if not result2.success:
    # 补偿步骤 1
    await account_service.credit(account_a, 100)
    return fail_saga("账户 B 无效")

saga_state["status"] = "completed"
return success_saga()
```

**Saga 状态持久化：**
```
CREATE TABLE saga_state (
    saga_id UUID PRIMARY KEY,
    saga_type VARCHAR(50),
    current_step INTEGER,
    max_steps INTEGER,
    status VARCHAR(20),
    payload JSONB,
    steps_completed JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

每一步骤后：
UPDATE saga_state
SET
    current_step = current_step + 1,
    steps_completed = jsonb_array_append(steps_completed, 'step_name'),
    updated_at = NOW()
WHERE saga_id = $1;

失败时，加载 saga 状态并执行补偿
```

**Saga 步骤的幂等性：**
```
每个 saga 步骤必须具有幂等性：

借记操作：
async def debit_account(account_id, amount, saga_id):
    # 检查是否已处理
    existing = await db.fetchone(
        "SELECT * FROM transactions WHERE saga_id = $1 AND operation = 'debit'",
        saga_id
    )
    if existing:
        return {"success": True, "transaction_id": existing.id}

    # 处理借记
    result = await db.execute(
        "UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1",
        amount, account_id
    )

    if result.rowcount == 0:
        return {"success": False, "error": "资金不足"}

    # 记录事务
    await db.execute(
        "INSERT INTO transactions (saga_id, account_id, amount, operation) VALUES ($1, $2, $3, 'debit')",
        saga_id, account_id, amount
    )

    return {"success": True}

补偿操作：
async def compensate_debit(account_id, amount, saga_id):
    await credit_account(account_id, amount, saga_id)
```

## 事件溯源

### 核心概念

**事件存储：**
```
所有状态更改存储为不可变事件

示例：银行账户

事件：
1. AccountOpened { accountId: "acc-123", customerId: "cust-456", initialBalance: 0 }
2. MoneyDeposited { accountId: "acc-123", amount: 1000, timestamp: "2025-01-15T10:00:00Z" }
3. MoneyWithdrawn { accountId: "acc-123", amount: 200, timestamp: "2025-01-16T14:30:00Z" }
4. MoneyDeposited { accountId: "acc-123", amount: 500, timestamp: "2025-01-17T09:15:00Z" }

当前余额 = 0 + 1000 - 200 + 500 = 1300

重放所有事件以重建当前状态
```

**事件模式：**
```json
{
  "eventId": "evt-789",
  "aggregateId": "acc-123",
  "aggregateType": "BankAccount",
  "eventType": "MoneyDeposited",
  "eventVersion": "1.0",
  "timestamp": "2025-01-15T10:00:00Z",
  "correlationId": "corr-456",
  "causationId": "cmd-123",
  "payload": {
    "amount": 1000,
    "currency": "USD",
    "source": "wire_transfer"
  },
  "metadata": {
    "userId": "user-789",
    "ipAddress": "192.168.1.1"
  }
}
```

### 快照

**问题：** 重放数千个事件很慢。

**解决方案：** 定期快照。

```
事件流：
1. AccountOpened（版本 1）
2. MoneyDeposited（版本 2）
...
1000. MoneyDeposited（版本 1000）
[版本 1000 的快照：余额 = $50,000]
1001. MoneyWithdrawn（版本 1001）
...
1500. MoneyDeposited（版本 1500）

获取当前状态：
1. 加载版本 1000 的快照（余额 = $50,000）
2. 重放事件 1001-1500（仅 500 个事件）

比重放全部 1500 个事件快得多

快照策略：
- 每 100 个事件
- 或每 24 小时
- 异步后台进程
```

**快照表：**
```sql
CREATE TABLE snapshots (
    aggregate_id UUID,
    aggregate_type VARCHAR(50),
    version INTEGER,
    state JSONB,
    created_at TIMESTAMP,
    PRIMARY KEY (aggregate_id, version)
);

CREATE INDEX idx_latest_snapshot ON snapshots(aggregate_id, version DESC);
```

### 事件模式演进

**挑战：** 事件是不可变的，但需求会变化。

**策略：**

**1. 事件版本控制：**
```
版本 1：
{
  "eventType": "OrderPlaced",
  "eventVersion": "1.0",
  "payload": {
    "orderId": "123",
    "amount": 99.99
  }
}

版本 2（添加客户电子邮件）：
{
  "eventType": "OrderPlaced",
  "eventVersion": "2.0",
  "payload": {
    "orderId": "123",
    "amount": 99.99,
    "customerEmail": "customer@example.com"
  }
}

事件处理器：
def handle_order_placed(event):
    if event.eventVersion == "1.0":
        # 处理旧格式
        process_order_v1(event.payload)
    elif event.eventVersion == "2.0":
        # 处理新格式
        process_order_v2(event.payload)
```

**2. 事件转换：**
```
在重放期间将旧事件转换为新格式：

def upcast_event(event):
    if event.eventType == "OrderPlaced" and event.eventVersion == "1.0":
        # 转换为 v2.0
        return {
            "eventType": "OrderPlaced",
            "eventVersion": "2.0",
            "payload": {
                **event.payload,
                "customerEmail": "unknown@example.com"  # 默认值
            }
        }
    return event
```

**3. 事件转换：**
```
创建新事件类型，保留旧事件用于历史准确性：

旧：OrderPlaced
新：OrderPlacedV2

投影处理两者：
- 旧事件用于历史数据
- 新事件用于当前处理
```

## 数据同步

### 变更数据捕获（CDC）

**目的：** 捕获数据库更改并作为事件发布。

**工作原理：**
```
数据库事务日志 → CDC 工具 → 事件流

使用 Debezium 的示例：

PostgreSQL：
INSERT INTO orders (id, customer_id, total) VALUES (123, 456, 99.99);

Debezium 捕获：
{
  "before": null,
  "after": {
    "id": 123,
    "customer_id": 456,
    "total": 99.99,
    "created_at": "2025-01-15T10:00:00Z"
  },
  "op": "c",  // 创建
  "ts_ms": 1705314000000
}

发布到 Kafka 主题：postgres.public.orders

其他服务订阅并更新其读模型
```

**好处：**
```
✓ 无应用程序代码更改
✓ 保证传递（基于数据库事务日志）
✓ 捕获所有更改（即使来自直接数据库访问）
✓ 低延迟
✓ 保留顺序

用例：
- 保持搜索索引同步
- 自动更新缓存
- 复制到数据仓库
- 在数据库更改上触发工作流
```

### 物化视图

**目的：** 用于快速查询的预计算非规范化视图。

**模式：**
```
事件驱动物化视图：

1. 服务发布领域事件
2. 视图服务订阅事件
3. 实时更新物化视图

示例：订单摘要视图

事件：
- order.created
- order.payment_received
- order.shipped
- order.delivered

物化视图：
CREATE TABLE order_summary (
    order_id UUID PRIMARY KEY,
    customer_id UUID,
    customer_name VARCHAR(255),
    order_date TIMESTAMP,
    total_amount DECIMAL,
    status VARCHAR(50),
    items_count INTEGER,
    last_updated TIMESTAMP
);

视图服务：
async def on_order_created(event):
    await db.execute(
        "INSERT INTO order_summary (order_id, customer_id, status, ...) VALUES (...)",
        event.data
    )

async def on_order_shipped(event):
    await db.execute(
        "UPDATE order_summary SET status = 'shipped', last_updated = NOW() WHERE order_id = $1",
        event.order_id
    )
```

## 数据分区

### 水平分区（分片）

**何时使用：**
```
- 单个数据库无法处理负载
- 数据大小超过单个服务器容量
- 想要地理分布
```

**分片策略：**

**1. 基于哈希的分片：**
```
分片 = hash(customer_id) % num_shards

customer_id: cust-123 → hash → 7234 → mod 4 → 分片 2
customer_id: cust-456 → hash → 9812 → mod 4 → 分片 0

优点：
- 均匀分布
- 实现简单

缺点：
- 添加分片需要重新分片
- 范围查询困难
```

**2. 基于范围的分片：**
```
分片 0：customer_id 0-999
分片 1：customer_id 1000-1999
分片 2：customer_id 2000-2999

优点：
- 范围查询高效
- 容易添加分片

缺点：
- 分布不均（热点）
- 需要分片映射
```

**3. 基于地理位置的分片：**
```
分片 US：美国的客户
分片 EU：欧洲的客户
分片 APAC：亚太地区的客户

优点：
- 数据本地性（GDPR 合规）
- 更低的延迟

缺点：
- 分布不均
- 跨分片查询复杂
```

**分片管理：**
```
分片映射服务：

GET /shard-location?customer_id=cust-123
响应：{ "shard": "shard-2", "endpoint": "db2.example.com" }

应用程序逻辑：
customer_id = request.customer_id
shard_info = await shard_map.get_shard(customer_id)
db_connection = connection_pool.get(shard_info.endpoint)
result = await db_connection.query("SELECT * FROM customers WHERE id = $1", customer_id)
```

## 总结

微服务中的数据管理需要仔细设计：

**关键原则：**
- 每个服务一个数据库（不可协商）
- 尽可能接受最终一致性
- 使用 Saga 模式进行分布式事务
- 事件溯源用于审计踪迹和时间查询
- CQRS 用于读/写优化
- CDC 用于数据同步

**决策框架：**
- 强一致性 → 使用 Saga 仔细的补偿逻辑
- 审计踪迹 → 使用事件溯源
- 复杂查询 → 使用 CQRS 读模型
- 大规模 → 使用适当策略的分片

始终为故障设计：补偿事务、幂等操作和适当的监控是必不可少的。
