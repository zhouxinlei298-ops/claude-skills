# 消息队列最佳实践指南

> 消息队列是分布式系统核心组件，用于解耦服务、异步处理、削峰填谷。

## 📋 目录

- [消息队列对比](#消息队列对比)
- [核心设计原则](#核心设计原则)
- [Kafka 最佳实践](#kafka-最佳实践)
- [RabbitMQ 最佳实践](#rabbitmq-最佳实践)
- [RocketMQ 最佳实践](#rocketmq-最佳实践)
- [可靠性保障](#可靠性保障)
- [顺序保证](#顺序保证)
- [性能优化](#性能优化)

---

## 消息队列对比

### 核心特性对比

| 特性 | Kafka | RabbitMQ | RocketMQ |
|------|-------|----------|----------|
| **吞吐量** | 极高（百万级/秒） | 中等（万级/秒） | 高（十万级/秒） |
| **延迟** | 毫秒级 | 微秒级 | 毫秒级 |
| **可靠性** | 高（多副本） | 高（持久化 + ACK） | 高（同步/异步刷盘） |
| **消息顺序** | 分区内有序 | 队列内有序 | 队列内有序 |
| **事务消息** | 不支持 | 不支持 | **支持** |
| **定时消息** | 不支持 | 延迟队列插件 | **支持** |
| **回溯消费** | 支持 | 不支持 | 支持 |
| **运维复杂度** | 中等 | 简单 | 较高 |
| **适用场景** | 日志收集、流式处理 | 传统业务消息 | 金融、电商业务 |

### 选型建议

```
┌─────────────────────────────────────────────────────────────┐
│  场景                          推荐方案                       │
├─────────────────────────────────────────────────────────────┤
│  大数据、日志收集               Kafka                         │
│  传统业务解耦（TPS < 10万）     RabbitMQ                      │
│  金融事务、订单业务             RocketMQ                      │
│  低延迟要求                     RabbitMQ                      │
│  大吞吐 + 高可靠                Kafka + RocketMQ              │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心设计原则

### 1. 幂等性设计

**原则**：消费者必须实现幂等性，消费同一消息多次结果相同

```java
// ✅ 使用数据库唯一约束保证幂等
@Service
@RequiredArgsConstructor
public class OrderConsumer {

    private final OrderRepository orderRepository;

    public void consumeOrderCreated(OrderCreatedEvent event) {
        // orderId 设置唯一索引
        Order order = Order.builder()
            .orderId(event.getOrderId())        // 唯一键
            .userId(event.getUserId())
            .amount(event.getAmount())
            .messageId(event.getMessageId())    // 消息 ID 用于去重
            .build();

        try {
            orderRepository.save(order);
        } catch (DuplicateKeyException e) {
            // 重复消费，直接返回
            log.info("Duplicate order: {}", event.getOrderId());
        }
    }
}

// ✅ 使用 Redis 去重表
public void consumeWithDedup(Event event) {
    String key = "dedup:" + event.getMessageId();

    // SET NX：只消费第一次
    Boolean acquired = redis.setnx(key, "1", 24 * 60 * 60);
    if (!acquired) {
        log.info("Duplicate message: {}", event.getMessageId());
        return;
    }

    // 处理业务逻辑...
    processEvent(event);
}
```

### 2. 消息不可变

**原则**：消息发送后禁止修改，避免版本不一致

```java
// ✅ 消息对象设计为不可变
public final class OrderCreatedEvent {
    private final String orderId;
    private final String userId;
    private final BigDecimal amount;
    private final Instant createdAt;

    // 全参构造器
    @JsonCreator
    public OrderCreatedEvent(
        @JsonProperty("orderId") String orderId,
        @JsonProperty("userId") String userId,
        @JsonProperty("amount") BigDecimal amount,
        @JsonProperty("createdAt") Instant createdAt
    ) {
        this.orderId = orderId;
        this.userId = userId;
        this.amount = amount;
        this.createdAt = createdAt;
    }

    // 只提供 Getter，无 Setter
    public String getOrderId() { return orderId; }
    // ...
}
```

### 3. 死信队列（DLQ）

**原则**：处理失败的消息转入死信队列，避免阻塞主队列

```java
// ✅ RabbitMQ 死信队列配置
@Configuration
public class RabbitMQConfig {

    @Bean
    public Queue orderQueue() {
        return QueueBuilder.durable("order.queue")
            .withArgument("x-dead-letter-exchange", "order.dlx")      // 死信交换机
            .withArgument("x-dead-letter-routing-key", "order.dlq")   // 死信路由键
            .withArgument("x-max-retries", 3)                         // 最大重试次数
            .build();
    }

    @Bean
    public Queue deadLetterQueue() {
        return QueueBuilder.durable("order.dlq").build();
    }

    @Bean
    public DirectExchange deadLetterExchange() {
        return new DirectExchange("order.dlx");
    }

    @Bean
    public Binding dlqBinding() {
        return BindingBuilder.bind(deadLetterQueue())
            .to(deadLetterExchange())
            .with("order.dlq");
    }
}
```

---

## Kafka 最佳实践

### 生产者配置

```java
@Configuration
public class KafkaProducerConfig {

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> config = new HashMap<>();

        // 基础配置
        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);

        // ✅ 可靠性配置
        config.put(ProducerConfig.ACKS_CONFIG, "all");              // 等待所有副本确认
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);  // 幂等性（去重）
        config.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);

        // ✅ 重试配置
        config.put(ProducerConfig.RETRIES_CONFIG, 3);                 // 重试次数
        config.put(ProducerConfig.RETRY_BACKOFF_MS_CONFIG, 100);     // 重试退避

        // ✅ 缓冲配置
        config.put(ProducerConfig.BUFFER_MEMORY_CONFIG, 32 * 1024 * 1024);  // 32MB
        config.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384);                 // 16KB
        config.put(ProducerConfig.LINGER_MS_CONFIG, 10);                     // 10ms 批量发送

        // ✅ 压缩配置
        config.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "lz4");    // 压缩算法

        return new DefaultKafkaProducerFactory<>(config);
    }

    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }
}
```

### 消费者配置

```java
@Configuration
public class KafkaConsumerConfig {

    @Bean
    public ConsumerFactory<String, Object> consumerFactory() {
        Map<String, Object> config = new HashMap<>();

        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
        config.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        config.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);

        // ✅ 消费者组
        config.put(ConsumerConfig.GROUP_ID_CONFIG, "order-service-group");

        // ✅ 自动提交关闭（手动控制）
        config.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

        // ✅ 初始位置
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");  // earliest/latest

        // ✅ 会话与心跳
        config.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, 30000);     // 30 秒
        config.put(ConsumerConfig.HEARTBEAT_INTERVAL_MS_CONFIG, 10000);  // 10 秒

        // ✅ 批量消费
        config.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 500);

        return new DefaultKafkaConsumerFactory<>(
            config,
            new StringDeserializer(),
            new JsonDeserializer<>(Object.class)
        );
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, Object> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, Object> factory =
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());

        // ✅ 并发配置
        factory.setConcurrency(3);                    // 3 个消费者线程

        // ✅ 手动提交
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);

        // ✅ 错误处理
        factory.setErrorHandler(new ConsumerErrorHandler());

        return factory;
    }
}
```

### 消费者实现

```java
@Service
@Slf4j
public class OrderConsumer {

    @KafkaListener(
        topics = "order-created",
        groupId = "order-service-group",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumeOrderCreated(
        OrderCreatedEvent event,
        Acknowledgment ack,
        ConsumerRecord<String, Object> record
    ) {
        try {
            log.info("Consumed order: {}", event.getOrderId());

            // 处理业务逻辑
            processOrder(event);

            // ✅ 手动提交偏移量
            ack.acknowledge();

        } catch (Exception e) {
            log.error("Failed to consume order: {}", event.getOrderId(), e);

            // 方案1：不提交 ack，等待重试（需配合 retry 配置）
            // 方案2：发送到死信队列
            sendToDeadLetterQueue(record, e);
        }
    }

    private void processOrder(OrderCreatedEvent event) {
        // 幂等性检查
        if (isDuplicate(event.getMessageId())) {
            return;
        }

        // 业务处理...
        orderService.createOrder(event);
    }
}
```

---

## RabbitMQ 最佳实践

### 生产者配置

```java
@Configuration
public class RabbitMQConfig {

    @Bean
    public ConnectionFactory connectionFactory() {
        CachingConnectionFactory factory = new CachingConnectionFactory("localhost");
        factory.setUsername("guest");
        factory.setPassword("guest");

        // ✅ 发布确认（保障消息可靠到达）
        factory.setPublisherConfirmType(CachingConnectionFactory.ConfirmType.CORRELATED);

        // ✅ 发布返回（保障消息路由到队列）
        factory.setPublisherReturns(true);

        return factory;
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);

        // ✅ 开启强制返回（消息无法路由时返回）
        template.setMandatory(true);

        // ✅ 确认回调
        template.setConfirmCallback((correlationData, ack, cause) -> {
            if (!ack) {
                log.error("Message send failed: {}", cause);
                // 重试或记录...
            }
        });

        // ✅ 返回回调
        template.setReturnsCallback(returnedMessage -> {
            log.error("Message returned: {}", returnedMessage.getMessage());
            // 处理无法路由的消息...
        });

        return template;
    }
}
```

### 消费者配置

```java
@Configuration
public class RabbitMQConsumerConfig {

    @Bean
    public SimpleRabbitListenerContainerFactory rabbitListenerContainerFactory(
        ConnectionFactory connectionFactory
    ) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        factory.setConnectionFactory(connectionFactory);

        // ✅ 手动确认模式
        factory.setAcknowledgeMode(AcknowledgeMode.MANUAL);

        // ✅ 并发消费者
        factory.setConcurrentConsumers(3);
        factory.setMaxConcurrentConsumers(10);

        // ✅ 预取数量
        factory.setPrefetch(10);

        // ✅ 重试配置
        factory.setAdviceChain(
            RetryInterceptorBuilder
                .stateless()
                .maxAttempts(3)
                .backOff(1000, 2.0)  // 初始 1s，2 倍递增
                .retryableException(Exception.class)
                .build()
        );

        return factory;
    }
}
```

### 消费者实现

```java
@Component
@Slf4j
public class OrderConsumer {

    @RabbitListener(
        queues = "order.queue",
        containerFactory = "rabbitListenerContainerFactory"
    )
    public void consumeOrderCreated(
        OrderCreatedEvent event,
        Channel channel,
        @Header(AmqpHeaders.DELIVERY_TAG) long deliveryTag
    ) throws IOException {
        try {
            log.info("Consumed order: {}", event.getOrderId());

            // 处理业务逻辑
            processOrder(event);

            // ✅ 手动确认
            channel.basicAck(deliveryTag, false);  // false = 不批量确认

        } catch (Exception e) {
            log.error("Failed to consume order: {}", event.getOrderId(), e);

            // ✅ 拒绝消息，重新入队
            channel.basicNack(deliveryTag, false, true);  // true = 重新入队

            // 或者拒绝不入队（发送到死信队列）
            // channel.basicReject(deliveryTag, false);
        }
    }
}
```

---

## RocketMQ 最佳实践

### 生产者配置

```java
@Configuration
public class RocketMQProducerConfig {

    @Bean
    public DefaultMQProducer defaultMQProducer() throws MQClientException {
        DefaultMQProducer producer = new DefaultMQProducer("order-producer-group");

        producer.setNamesrvAddr("localhost:9876");

        // ✅ 发送失败重试次数
        producer.setRetryTimesWhenSendFailed(2);
        producer.setRetryTimesWhenSendAsyncFailed(2);

        // ✅ 超时时间
        producer.setSendMsgTimeout(3000);

        producer.start();

        return producer;
    }
}
```

### 消费者配置

```java
@Component
public class OrderConsumer implements MessageListenerConcurrently {

    @Override
    public ConsumeConcurrentlyStatus consumeMessage(
        List<MessageExt> messages,
        ConsumeConcurrentlyContext context
    ) {
        for (MessageExt message : messages) {
            try {
                String body = new String(message.getBody(), StandardCharsets.UTF_8);
                OrderCreatedEvent event = JSON.parseObject(body, OrderCreatedEvent.class);

                log.info("Consumed order: {}", event.getOrderId());

                // 处理业务逻辑（带幂等）
                processOrder(event);

            } catch (Exception e) {
                log.error("Failed to consume message: {}", message.getMsgId(), e);

                // ✅ 稍后重试
                return ConsumeConcurrentlyStatus.RECONSUME_LATER;
            }
        }

        // ✅ 消费成功
        return ConsumeConcurrentlyStatus.CONSUME_SUCCESS;
    }
}
```

### 事务消息

```java
@Service
public class OrderTransactionProducer {

    @Autowired
    private TransactionMQProducer transactionProducer;

    public void sendTransactionalMessage(Order order) {
        Message message = new Message(
            "order-topic",
            "order-create",
            JSON.toJSONString(order).getBytes(StandardCharsets.UTF_8)
        );

        transactionProducer.sendMessageInTransaction(
            message,
            null,  // 自定义参数
            order  // 本地事务参数
        );
    }

    // ✅ 本地事务监听器
    public static class OrderTransactionListener implements TransactionListener {

        @Autowired
        private OrderService orderService;

        @Override
        public LocalTransactionState executeLocalTransaction(Message msg, Object arg) {
            Order order = (Order) arg;

            try {
                // 执行本地事务（创建订单）
                orderService.createOrder(order);

                // ✅ 本地事务成功，提交消息
                return LocalTransactionState.COMMIT_MESSAGE;

            } catch (Exception e) {
                log.error("Local transaction failed", e);
                // ✅ 本地事务失败，回滚消息
                return LocalTransactionState.ROLLBACK_MESSAGE;
            }
        }

        @Override
        public LocalTransactionState checkLocalTransaction(MessageExt msg) {
            // ✅ 回查本地事务状态
            String orderId = msg.getKeys();

            Order order = orderService.getOrderByOrderId(orderId);
            if (order != null) {
                return LocalTransactionState.COMMIT_MESSAGE;
            }

            // 未知状态，继续回查
            return LocalTransactionState.UNKNOW;
        }
    }
}
```

---

## 可靠性保障

### 消息发送可靠性

```
┌────────────────────────────────────────────────────────────────┐
│  发送可靠性保障层次                                              │
├────────────────────────────────────────────────────────────────┤
│  1. 生产者确认（Publisher Confirm）                               │
│     - Kafka: acks=all                                          │
│     - RabbitMQ: publisher-confirms                              │
│     - RocketMQ: SYNC 模式                                        │
│                                                                │
│  2. 消息持久化                                                   │
│     - Kafka: log.flush.interval.messages                       │
│     - RabbitMQ: delivery-mode=2 (持久化)                        │
│     - RocketMQ: flushDiskType=SYNC_FLUSH                       │
│                                                                │
│  3. 多副本/集群高可用                                            │
│     - Kafka: replication.factor=3                              │
│     - RabbitMQ: 镜像队列 + HAMP                                 │
│     - RocketMQ: 多 Master + 多 Slave                            │
└────────────────────────────────────────────────────────────────┘
```

### 消息消费可靠性

```java
// ✅ 消费者幂等 + 事务
@Service
public class OrderConsumer {

    @Transactional
    public void consumeWithTransaction(OrderCreatedEvent event) {
        // 1. 幂等检查（使用唯一索引）
        if (orderRepository.existsByOrderId(event.getOrderId())) {
            return;
        }

        // 2. 处理业务逻辑
        Order order = Order.builder()
            .orderId(event.getOrderId())
            .userId(event.getUserId())
            .amount(event.getAmount())
            .build();

        orderRepository.save(order);

        // 3. 确认消息（在事务成功后）
        // ack.acknowledge();
    }
}
```

---

## 顺序保证

### Kafka 分区内有序

```java
// ✅ 生产者：相同 Key 发送到同一分区
kafkaTemplate.send(
    "order-topic",
    event.getUserId(),     // Key（决定分区）
    event                  // Value
);

// ✅ 消费者：单线程消费或确保分区有序
@KafkaListener(
    topics = "order-topic",
    concurrency = "1"      // 单线程保证顺序
)
public void consume(OrderCreatedEvent event) {
    processOrder(event);
}
```

### RocketMQ 顺序消息

```java
// ✅ 生产者：相同 orderId 发送到同一队列
SendResult result = producer.send(
    new Message(
        "order-topic",
        "order-create",
        orderId.toString(),  // Hash Key（决定队列）
        JSON.toJSONString(order).getBytes()
    )
);

// ✅ 消费者：使用 MessageListenerOrderly
public class OrderConsumer implements MessageListenerOrderly {

    @Override
    public ConsumeOrderlyStatus consumeMessage(
        List<MessageExt> messages,
        ConsumeOrderlyContext context
    ) {
        // 同一队列内的消息顺序消费
        for (MessageExt message : messages) {
            processOrder(message);
        }

        return ConsumeOrderlyStatus.CONSUME_SUCCESS;
    }
}
```

---

## 性能优化

### 批量发送

```java
// ✅ Kafka 批量发送
List<OrderCreatedEvent> events = getOrders();

for (OrderCreatedEvent event : events) {
    kafkaTemplate.send("order-topic", event);
}

kafkaTemplate.flush();  // 批量发送
```

### 批量消费

```java
// ✅ Kafka 批量消费
@KafkaListener(
    topics = "order-topic",
    containerFactory = "batchFactory"
)
public void consumeBatch(List<OrderCreatedEvent> events) {
    // 批量插入数据库
    orderRepository.batchInsert(events);
}
```

### 并发调优

| 参数 | Kafka | RabbitMQ | RocketMQ |
|------|-------|----------|----------|
| **消费者并发** | `concurrency` | `concurrentConsumers` | `consumeThreadMin/Max` |
| **预取数量** | `max.poll.records` | `prefetch` | `pullBatchSize` |
| **网络线程** | `num.network.threads` | - | `clientWorkerThreads` |

---

## 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| **消息堆积** | Consumer Lag | > 10000 |
| **消费 TPS** | 消费速率 | - |
| **消费延迟** | 端到端延迟 | > 1s |
| **错误率** | 消费失败率 | > 1% |
| **生产失败率** | 发送失败率 | > 0.1% |
