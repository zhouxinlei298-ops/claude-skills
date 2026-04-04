# 服务间通信模式

设计微服务之间通信的全面指南。

## 通信风格

### 同步通信

**REST API：**
```
何时使用：
- 需要请求/响应模式
- 客户端需要立即结果
- 简单的 CRUD 操作
- 面向公众的 API

设计原则：
- 面向资源的 URL
- HTTP 动词（GET、POST、PUT、DELETE、PATCH）
- 无状态操作
- 尽可能的幂等操作
- 适当的状态码（200、201、400、404、500）

示例：
GET    /api/v1/orders/{orderId}
POST   /api/v1/orders
PUT    /api/v1/orders/{orderId}
DELETE /api/v1/orders/{orderId}
PATCH  /api/v1/orders/{orderId}/status
```

**gRPC：**
```
何时使用：
- 低延迟要求
- 需要强类型
- 流式数据
- 内部服务到服务调用
- 多语言环境

优势：
- 二进制协议（比 JSON 更快）
- 内置代码生成
- 双向流
- HTTP/2 多路复用
- 通过 Protobuf 强制执行模式

示例 Proto：
service OrderService {
  rpc GetOrder(OrderRequest) returns (OrderResponse);
  rpc CreateOrder(CreateOrderRequest) returns (OrderResponse);
  rpc StreamOrders(StreamRequest) returns (stream OrderResponse);
}

message OrderRequest {
  string order_id = 1;
}

message OrderResponse {
  string order_id = 1;
  string status = 2;
  repeated OrderItem items = 3;
}
```

**GraphQL：**
```
何时使用：
- 前端驱动的数据需求
- 从多个服务聚合数据
- 灵活的查询要求
- 减少过度获取/不足获取

联邦模式：
- 每个服务拥有自己的子域模式
- 网关将模式拼接在一起
- 客户端查询统一 API
- 服务解析自己的字段

示例：
# 用户服务模式
type User @key(fields: "id") {
  id: ID!
  name: String!
  email: String!
}

# 订单服务模式
extend type User @key(fields: "id") {
  id: ID! @external
  orders: [Order!]!
}
```

### 异步通信

**消息队列（点对点）：**
```
何时使用：
- 任务分发
- 负载均衡
- 需要保证传递
- 每条消息单个消费者

示例：
- 带工作队列的 RabbitMQ
- AWS SQS
- Azure Service Bus Queues

模式：
生产者 → 队列 → 消费者
- 消费者确认消息
- 未确认的消息重新传递
- 失败的死信队列

用例：
- 后台作业处理
- 邮件/SMS 发送
- 图像处理
- 报告生成
```

**事件流（发布/订阅）：**
```
何时使用：
- 多个消费者需要同一事件
- 事件溯源
- 实时数据管道
- 审计日志
- CQRS 读模型更新

Kafka 示例：
主题：
- order.created
- order.updated
- order.cancelled

生产者：
- OrderService 发布事件

消费者：
- NotificationService（发送确认邮件）
- InventoryService（预留库存）
- AnalyticsService（跟踪指标）
- WarehouseService（准备发货）

每个消费者独立处理
```

**事件驱动架构：**
```
事件类型：

1. 领域事件：
   - order.placed
   - payment.completed
   - shipment.dispatched

   特征：
   - 表示已发生的事情
   - 不可变
   - 过去时态命名
   - 包含必要的最小数据

2. 集成事件：
   - 跨限界上下文发布
   - 设计用于外部消费
   - 模式版本控制
   - 向后兼容

3. 命令事件：
   - 命令式（执行某事）
   - 示例：process.order、send.notification
   - 谨慎使用（优先使用领域事件）

事件模式示例：
{
  "eventId": "uuid",
  "eventType": "order.placed",
  "eventVersion": "1.0",
  "timestamp": "2025-12-14T10:00:00Z",
  "aggregateId": "order-12345",
  "correlationId": "request-uuid",
  "payload": {
    "orderId": "12345",
    "customerId": "67890",
    "totalAmount": 99.99,
    "currency": "USD"
  }
}
```

## 通信模式

### 请求/响应

**同步请求/响应：**
```
模式：
客户端 → 服务 A → 服务 B → 响应

优点：
- 实现简单
- 立即反馈
- 易于调试

缺点：
- 紧密的时间耦合
- 级联故障
- 更高的延迟
- 阻塞操作

何时使用：
- 实时用户交互
- 少量跳转（最多 2-3 个）
- 低延迟要求
- 依赖失败应该使请求失败
```

**异步请求/响应：**
```
模式：
1. 客户端向服务 A 发送请求
2. 服务 A 立即返回请求 ID
3. 服务 A 异步处理
4. 客户端轮询或完成后接收 Webhook

实现：
POST /api/v1/orders
响应：202 Accepted
{
  "requestId": "req-12345",
  "statusUrl": "/api/v1/requests/req-12345"
}

GET /api/v1/requests/req-12345
响应：200 OK
{
  "status": "completed",
  "result": { ... }
}

替代：准备就绪时通过 WebSocket 通知
```

### 即发即忘

**模式：**
```
客户端 → 消息队列 → 消费者

特征：
- 客户端不等待响应
- 最终一致性
- 高吞吐量
- 松散耦合

示例：
用户上传图片：
1. API 立即返回 202 Accepted
2. 消息排队：image.uploaded
3. 工作进程异步处理：
   - 生成缩略图
   - 优化图片
   - 更新数据库
4. 准备就绪时通过 WebSocket/SSE 通知用户

优点：
- 非阻塞
- 有弹性（失败时重试）
- 可扩展（多个工作进程）

缺点：
- 无即时反馈
- 需要状态跟踪
- 复杂的错误处理
```

### 事件编排

**模式：**
```
通过事件进行分布式工作流（无中央编排器）

示例：订单放置
1. OrderService 发布：order.created
2. PaymentService 监听，处理付款，发布：payment.completed
3. InventoryService 监听，预留库存，发布：inventory.reserved
4. ShippingService 监听，创建发货，发布：shipment.created
5. NotificationService 监听所有事件，发送适当的通知

优点：
- 无单点故障
- 服务高度解耦
- 独立扩展

缺点：
- 难以理解完整工作流
- 难以调试
- 无中央监控
- 最终一致性挑战
```

### Saga 编排

**模式：**
```
中央编排器管理分布式事务

示例：订单 Saga
编排器：OrderSagaService

步骤：
1. 创建订单（OrderService）
2. 处理付款（PaymentService）
3. 预留库存（InventoryService）
4. 创建发货（ShippingService）

如果步骤 3 失败：
- 补偿步骤 2：退款
- 补偿步骤 1：取消订单

实现：
- 状态机跟踪进度
- 持久化存储 saga 状态
- 处理重试和补偿
- 向服务发送命令

优点：
- 清晰的工作流可见性
- 更容易调试
- 集中式监控

缺点：
- 编排器可能成为瓶颈
- 单点故障（通过 HA 缓解）
- 更复杂的实现
```

## 协议选择指南

### 决策矩阵

**REST vs gRPC：**
```
使用 REST 当：
- 公共 API（外部客户端）
- 基于浏览器的客户端
- 需要人类可读的调试
- 需要广泛的工具支持
- HTTP 层缓存

使用 gRPC 当：
- 内部服务到服务
- 低延迟至关重要
- 需要强类型
- 双向流
- 多语言团队（代码生成）
```

**同步 vs 异步：**
```
使用同步当：
- 用户等待响应
- 需要强一致性
- 简单的请求/响应
- 低延迟可能（<100ms）
- 少量服务跳转（1-2 个）

使用异步当：
- 长时间运行的操作（>5s）
- 多个消费者需要相同数据
- 解耦服务
- 需要高吞吐量
- 可接受的最终一致性
```

**消息队列 vs 事件流：**
```
使用消息队列（RabbitMQ、SQS）当：
- 每条消息单个消费者
- 任务分发
- 保证处理
- 简单模型足够

使用事件流（Kafka）当：
- 每个事件多个消费者
- 需要事件重放
- 高吞吐量（百万/秒）
- 事件溯源
- 需要长期保留
```

## API 设计最佳实践

### RESTful API 设计

**URL 结构：**
```
好的：
GET    /api/v1/customers/{customerId}/orders
POST   /api/v1/orders
GET    /api/v1/orders/{orderId}/items

避免：
GET    /api/v1/getCustomerOrders?customerId=123
POST   /api/v1/createOrder
```

**版本控制策略：**
```
1. URL 版本控制：
   /api/v1/orders
   /api/v2/orders
   优点：清晰、易于路由
   缺点：URL 污染

2. 头版本控制：
   Accept: application/vnd.company.v1+json
   优点：干净的 URL
   缺点：难以调试

3. 查询参数：
   /api/orders?version=1
   优点：灵活
   缺点：容易遗漏

推荐：使用 URL 版本控制以简化
```

**分页：**
```
基于游标（推荐）：
GET /api/v1/orders?cursor=abc123&limit=20
响应：
{
  "data": [...],
  "nextCursor": "xyz789",
  "hasMore": true
}

基于偏移（简单但有问题）：
GET /api/v1/orders?page=2&pageSize=20
问题：如果插入数据，结果会改变
```

### gRPC 最佳实践

**错误处理：**
```
使用标准 gRPC 状态码：
- OK (0)
- INVALID_ARGUMENT (3)
- NOT_FOUND (5)
- ALREADY_EXISTS (6)
- PERMISSION_DENIED (7)
- RESOURCE_EXHAUSTED (8)
- FAILED_PRECONDITION (9)
- UNAVAILABLE (14)

包含错误详细信息：
rpc CreateOrder(CreateOrderRequest) returns (OrderResponse) {
  // 错误时返回带详细信息的 status
}

错误详细信息在元数据中以提供丰富的上下文
```

**流模式：**
```
1. 服务器流：
   rpc ListOrders(ListRequest) returns (stream Order);
   使用：大型结果集

2. 客户端流：
   rpc UploadImages(stream Image) returns (UploadResponse);
   使用：批量上传

3. 双向流：
   rpc Chat(stream Message) returns (stream Message);
   使用：实时通信
```

## 总结

根据以下因素选择通信模式：
- 一致性要求（强 vs 最终）
- 延迟容忍度
- 耦合容忍度
- 复杂性预算
- 团队专业知识

**经验法则**
- 同步用于读取和简单写入
- 异步用于复杂工作流
- 事件用于跨聚合更新
- Saga 用于分布式事务

无论选择哪种模式，都要实施超时、重试和断路器。
