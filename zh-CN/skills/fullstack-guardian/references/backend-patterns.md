# 后端模式

## 微服务架构

### 熔断器模式
```typescript
class CircuitBreaker {
  private failures = 0;
  private threshold = 5;
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') throw new Error('Circuit breaker is OPEN');
    try {
      const result = await fn();
      this.failures = 0;
      this.state = 'CLOSED';
      return result;
    } catch (error) {
      this.failures++;
      if (this.failures >= this.threshold) {
        this.state = 'OPEN';
        setTimeout(() => this.state = 'HALF_OPEN', 60000);
      }
      throw error;
    }
  }
}
```

### Saga 模式（分布式事务）
```typescript
class OrderSaga {
  async execute(order: Order) {
    const compensations: (() => Promise<void>)[] = [];
    try {
      await inventoryService.reserve(order.items);
      compensations.push(() => inventoryService.release(order.items));

      await paymentService.charge(order.amount);
      compensations.push(() => paymentService.refund(order.amount));

      return { success: true };
    } catch (error) {
      for (const compensate of compensations.reverse()) await compensate();
      throw error;
    }
  }
}
```

## 消息队列集成

### 带 DLQ 的生产者/消费者
```typescript
// RabbitMQ Consumer with Dead Letter Queue
class MessageConsumer {
  async consume(queue: string, handler: (msg: any) => Promise<void>) {
    const channel = await this.connection.createChannel();

    // Setup DLQ
    await channel.assertExchange('dlx', 'direct', { durable: true });
    await channel.assertQueue(`${queue}.dlq`, { durable: true });
    await channel.bindQueue(`${queue}.dlq`, 'dlx', queue);

    // Main queue
    await channel.assertQueue(queue, {
      durable: true,
      deadLetterExchange: 'dlx',
      deadLetterRoutingKey: queue,
    });

    channel.consume(queue, async (msg) => {
      if (!msg) return;
      try {
        await handler(JSON.parse(msg.content.toString()));
        channel.ack(msg);
      } catch (error) {
        const retryCount = (msg.properties.headers['x-retry-count'] || 0) + 1;
        if (retryCount >= 3) {
          channel.nack(msg, false, false); // Send to DLQ
        } else {
          setTimeout(() => channel.nack(msg, false, true), retryCount * 1000);
        }
      }
    });
  }
}
```

### 幂等性
```typescript
class IdempotentHandler {
  async handle(messageId: string, fn: () => Promise<void>) {
    const exists = await db.processedMessages.findOne({ messageId });
    if (exists) return; // Already processed

    await fn();
    await db.processedMessages.insert({ messageId, processedAt: new Date() });
  }
}
```

## 数据库优化

### 连接池
```typescript
import { Pool } from 'pg';

const pool = new Pool({
  max: 20,
  min: 5,
  idleTimeoutMillis: 30000,
});

export async function query(sql: string, params: any[]) {
  const client = await pool.connect();
  try {
    return await client.query(sql, params);
  } finally {
    client.release();
  }
}
```

### 读取副本策略
```typescript
class DatabaseRouter {
  async query(sql: string, params: any[]) {
    const isWrite = /^(INSERT|UPDATE|DELETE)/i.test(sql);
    if (isWrite) return this.primary.query(sql, params);

    // Round-robin read replica
    const replica = this.replicas[Math.floor(Math.random() * this.replicas.length)];
    return replica.query(sql, params);
  }
}
```

## 监控与可观测性

### Prometheus 指标
```typescript
import { Counter, Histogram, Registry } from 'prom-client';

const register = new Registry();

const httpDuration = new Histogram({
  name: 'http_request_duration_seconds',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

// Middleware
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    httpDuration.observe({
      method: req.method,
      route: req.route?.path,
      status_code: res.statusCode
    }, (Date.now() - start) / 1000);
  });
  next();
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

### 分布式追踪
```typescript
import { trace } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function processOrder(orderId: string) {
  const span = tracer.startSpan('processOrder');
  span.setAttribute('orderId', orderId);

  try {
    await db.query('SELECT * FROM orders WHERE id = $1', [orderId]);
    span.addEvent('Order fetched');
    span.setStatus({ code: SpanStatusCode.OK });
  } catch (error) {
    span.recordException(error);
    throw error;
  } finally {
    span.end();
  }
}
```

## Docker 与部署

### 多阶段 Dockerfile
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm run build

FROM node:18-alpine
WORKDIR /app
RUN adduser -S nodejs -u 1001
COPY --from=builder --chown=nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs /app/node_modules ./node_modules
USER nodejs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD node healthcheck.js
CMD ["node", "dist/main.js"]
```

### 优雅关闭
```typescript
process.on('SIGTERM', async () => {
  console.log('Shutting down gracefully');
  server.close(() => console.log('HTTP server closed'));
  await db.end();
  await messageQueue.close();
  process.exit(0);
});
```

## 快速参考

| 模式 | 用例 | 关键收益 |
|------|------|----------|
| 熔断器 | 外部服务调用 | 防止级联故障 |
| Saga | 分布式事务 | 数据一致性 |
| 消息队列 | 异步处理 | 解耦与可扩展性 |
| 连接池 | 数据库访问 | 性能优化 |
| 读取副本 | 高读取负载 | 水平扩展 |
| 分布式追踪 | 微服务调试 | 端到端可见性 |
| 优雅关闭 | 容器编排 | 零停机部署 |