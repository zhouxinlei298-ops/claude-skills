# 结构化日志

## Pino (Node.js)

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  redact: ['password', 'token', 'authorization'],
});

// Structured logging
logger.info({
  event: 'user.login',
  userId: user.id,
  ip: req.ip,
  userAgent: req.headers['user-agent'],
  duration: Date.now() - start,
});

// Error logging with context
logger.error({
  event: 'payment.failed',
  error: err.message,
  stack: err.stack,
  orderId: order.id,
  amount: order.total,
  userId: user.id,
});
```

## 请求日志中间件

```typescript
import { randomUUID } from 'crypto';

app.use((req, res, next) => {
  const requestId = req.headers['x-request-id'] || randomUUID();
  const start = Date.now();

  res.setHeader('x-request-id', requestId);

  res.on('finish', () => {
    logger.info({
      event: 'http.request',
      requestId,
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration: Date.now() - start,
      userAgent: req.headers['user-agent'],
      ip: req.ip,
    });
  });

  next();
});
```

## Python (structlog)

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
)

logger = structlog.get_logger()

# Structured logging
logger.info(
    "user.login",
    user_id=user.id,
    ip=request.client.host,
    duration=elapsed_time,
)

# Error logging
logger.error(
    "payment.failed",
    error=str(exc),
    order_id=order.id,
    amount=order.total,
)
```

## 日志级别

| 级别 | 使用场景 |
|-------|----------|
| `error` | 需要关注的失败 |
| `warn` | 潜在问题 |
| `info` | 业务事件、请求 |
| `debug` | 开发细节 |
| `trace` | 详细调试 |

## 最佳实践

```typescript
// Good: Structured fields
logger.info({ event: 'order.created', orderId: '123', total: 99.99 });

// Bad: String interpolation
logger.info(`Order 123 created with total 99.99`);

// Good: Consistent event names
logger.info({ event: 'user.registered' });
logger.info({ event: 'user.login' });
logger.info({ event: 'user.logout' });

// Good: Include correlation ID
logger.info({ event: 'request.processed', requestId, userId });
```

## 快速参考

| 字段 | 用途 |
|-------|---------|
| `event` | 事件名称 |
| `requestId` | 关联 ID |
| `userId` | 用户上下文 |
| `duration` | 时间信息 |
| `error` / `stack` | 错误详情 |
| `timestamp` | 时间（自动添加） |

| 库 | 语言 |
|---------|----------|
| pino | Node.js |
| structlog | Python |
| slog | Go |
| logrus | Go |