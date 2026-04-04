# API 设计标准

## RESTful API 规范

### URL 结构
```
# Collection vs Resource
GET    /api/users          # List all users
POST   /api/users          # Create user
GET    /api/users/:id      # Get single user
PUT    /api/users/:id      # Full update
PATCH  /api/users/:id      # Partial update
DELETE /api/users/:id      # Delete user

# Nested resources
GET    /api/users/:id/posts        # User's posts
POST   /api/users/:id/posts        # Create post for user
GET    /api/posts/:id/comments     # Comments on post
```

### HTTP 状态码
```typescript
// Success codes
200 OK              // GET, PUT, PATCH successful
201 Created         // POST successful, resource created
204 No Content      // DELETE successful, no body
202 Accepted        // Async operation queued

// Client error codes
400 Bad Request     // Malformed request
401 Unauthorized    // Authentication required
403 Forbidden       // Authenticated but not authorized
404 Not Found       // Resource doesn't exist
409 Conflict        // Resource conflict (e.g., duplicate)
422 Unprocessable   // Validation failed
429 Too Many Requests // Rate limit exceeded

// Server error codes
500 Internal Server Error  // Unhandled exception
502 Bad Gateway           // Upstream service failed
503 Service Unavailable   // Temporary downtime
```

### 标准化错误响应
```typescript
interface ApiError {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable message
    details?: {             // Field-level validation errors
      [field: string]: string[];
    };
    requestId: string;      // For support/debugging
    timestamp: string;      // ISO 8601 timestamp
  };
}

// Examples
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "email": ["Must be a valid email address"],
      "password": ["Must be at least 12 characters"]
    },
    "requestId": "req_abc123",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}

{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "User not found",
    "requestId": "req_def456",
    "timestamp": "2025-01-15T10:31:00Z"
  }
}
```

### 分页
```typescript
// Query parameters
GET /api/users?page=1&limit=20&sort=-createdAt&filter[role]=admin

// Response format
interface PaginatedResponse<T> {
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  links?: {
    first: string;
    prev?: string;
    next?: string;
    last: string;
  };
}

// Implementation
@Get()
async findAll(
  @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
  @Query('limit', new DefaultValuePipe(20), ParseIntPipe) limit: number,
) {
  const [data, total] = await this.service.findAndCount({ page, limit });
  return {
    data,
    meta: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
    links: {
      first: `/api/users?page=1&limit=${limit}`,
      next: page < totalPages ? `/api/users?page=${page + 1}&limit=${limit}` : undefined,
      last: `/api/users?page=${totalPages}&limit=${limit}`,
    },
  };
}
```

## API 版本控制

### URL 路径版本控制（推荐）
```typescript
// Version in URL path
GET /api/v1/users
GET /api/v2/users

// Express routing
app.use('/api/v1', v1Router);
app.use('/api/v2', v2Router);

// NestJS versioning
@Controller({ version: '1', path: 'users' })
export class UsersV1Controller {}

@Controller({ version: '2', path: 'users' })
export class UsersV2Controller {}
```

### Header 版本控制（备选方案）
```typescript
// Request header
GET /api/users
Accept-Version: v2

// Middleware
app.use((req, res, next) => {
  const version = req.headers['accept-version'] || 'v1';
  req.apiVersion = version;
  next();
});
```

## 速率限制

### 每端点配置
```typescript
// Express with express-rate-limit
import rateLimit from 'express-rate-limit';

const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,                 // 100 requests per window
  message: 'Too many requests from this IP',
});

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,                   // Stricter for auth endpoints
  skipSuccessfulRequests: true,
});

app.use('/api/', generalLimiter);
app.use('/api/auth/', authLimiter);
```

### Redis 支持的速率限制
```typescript
import { RateLimiterRedis } from 'rate-limiter-flexible';

const rateLimiter = new RateLimiterRedis({
  storeClient: redisClient,
  keyPrefix: 'rate-limit',
  points: 100,              // Number of requests
  duration: 60,             // Per 60 seconds
});

app.use(async (req, res, next) => {
  try {
    await rateLimiter.consume(req.ip);
    next();
  } catch (error) {
    res.status(429).json({ error: 'Too Many Requests' });
  }
});
```

## CORS 配置

### 生产就绪的 CORS
```typescript
import cors from 'cors';

const corsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = [
      'https://app.example.com',
      'https://admin.example.com',
    ];

    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,                    // Allow cookies
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  exposedHeaders: ['X-Total-Count'],
  maxAge: 86400,                        // 24 hours preflight cache
};

app.use(cors(corsOptions));
```

## 请求/响应验证

### 使用 Zod 进行输入验证
```typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(18).max(120).optional(),
  role: z.enum(['user', 'admin']).default('user'),
});

// Middleware
const validate = (schema: z.ZodSchema) => (req, res, next) => {
  try {
    req.validatedBody = schema.parse(req.body);
    next();
  } catch (error) {
    res.status(422).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request data',
        details: error.errors,
      },
    });
  }
};

app.post('/api/users', validate(createUserSchema), createUserHandler);
```

## API 文档

### OpenAPI/Swagger 设置
```typescript
// NestJS with Swagger
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

const config = new DocumentBuilder()
  .setTitle('API Documentation')
  .setDescription('The API description')
  .setVersion('1.0')
  .addBearerAuth()
  .build();

const document = SwaggerModule.createDocument(app, config);
SwaggerModule.setup('api/docs', app, document);

// Decorate endpoints
@ApiOperation({ summary: 'Create a new user' })
@ApiResponse({ status: 201, description: 'User created successfully' })
@ApiResponse({ status: 422, description: 'Validation failed' })
@Post()
async create(@Body() dto: CreateUserDto) {
  return this.service.create(dto);
}
```

## 快速参考

| 方面 | 标准 | 示例 |
|------|------|------|
| URL 命名 | 复数名词 | `/api/users` 而不是 `/api/user` |
| HTTP 方法 | RESTful 语义 | GET（读取）、POST（创建）、PUT/PATCH（更新）、DELETE |
| 状态码 | 语义化使用 | 200（成功）、201（已创建）、422（验证失败） |
| 错误 | 一致格式 | `{ error: { code, message, details } }` |
| 分页 | Meta + links | `{ data, meta: { page, total }, links }` |
| 版本控制 | URL 路径 | `/api/v1/users` |
| 速率限制 | 每端点 | Auth: 5/分钟，General: 100/15分钟 |
| CORS | 白名单来源 | 仅生产域名 |
| 验证 | 基于模式 | Zod/Pydantic 带详细错误 |
| 文档 | OpenAPI | 从装饰器自动生成 |