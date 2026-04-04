# 架构决策指南

## 技术选择矩阵

### 后端框架选择

| 框架 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **NestJS** | 企业应用，微服务 | TypeScript 优先，依赖注入，优秀文档 | 意见性强，学习曲线陡峭 |
| **Express** | 简单 API，灵活性 | 极简，庞大的生态系统，知名 | 手动结构，不够意见化 |
| **Fastify** | 高性能 API | 快速，模式验证，插件 | 比 Express 生态系统小 |
| **FastAPI** | Python API，ML 集成 | 自动文档，类型提示，快速 | 仅 Python 生态系统 |
| **Go/Gin** | 高性能服务 | 编译型，并发，快速 | 冗长，开发速度较慢 |

**决策标准：**
- 团队专业知识：选择熟悉的栈
- 性能需求：高吞吐量选 Go/Fastify
- 类型安全：TypeScript/Python 选 NestJS/FastAPI
- 灵活性：自定义架构选 Express

### 前端框架选择

| 框架 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **React** | 大多数用例，大型应用 | 生态系统庞大，灵活，支持良好 | 不包含电池，决策疲劳 |
| **Vue** | 渐进增强 | 学习曲线平缓，文档好，响应式 | 比 React 生态系统小 |
| **Angular** | 企业应用 | 完整框架，原生 TypeScript | 重量级，意见性强，曲线陡峭 |
| **Svelte** | 性能关键应用 | 编译型，无虚拟 DOM，小包 | 生态系统小，资源少 |
| **Next.js** | SSR/SSG 应用，SEO | React + 路由 + SSR，出色体验 | 以 Vercel 为中心，简单应用过于复杂 |

**决策标准：**
- SEO 需求：SSR 选 Next.js/Nuxt
- 团队规模：大型团队选 Angular，小型团队选 Vue
- 生态系统：React 获得最大第三方支持
- 性能：最小包体积选 Svelte

### 数据库选择

| 数据库 | 适用场景 | 优点 | 缺点 |
|--------|----------|------|------|
| **PostgreSQL** | 关系型数据，ACID | 功能丰富，可靠，支持 JSON | 复杂查询可能慢 |
| **MySQL** | 读密集型工作负载 | 成熟，读快速，复制 | 功能比 Postgres 少 |
| **MongoDB** | 灵活模式，快速开发 | 无模式，水平扩展 | 旧版本无事务 |
| **Redis** | 缓存，会话，队列 | 极快，多用途 | 仅内存，数据结构有限 |
| **DynamoDB** | AWS 无服务器，高扩展 | 托管，可预测性能 | 供应商锁定，查询限制 |

**决策标准：**
- ACID 要求：PostgreSQL/MySQL
- 灵活模式：MongoDB
- 缓存层：Redis（总是）
- AWS 无服务器：DynamoDB
- 默认选择：PostgreSQL（最通用）

### 状态管理（前端）

| 方案 | 适用场景 | 复杂度 | 包大小 |
|------|----------|--------|--------|
| **React Context** | 简单状态，少量更新 | 低 | 无（内置） |
| **Zustand** | 中等应用，简洁 | 低 | 1KB |
| **Redux Toolkit** | 复杂状态，时间旅行调试 | 中 | 15KB |
| **Jotai/Recoil** | 原子状态，派生状态 | 中 | 3KB |
| **MobX** | 可观察状态，OOP 风格 | 中 | 16KB |
| **TanStack Query** | 仅服务器状态 | 低 | 12KB |

**决策标准：**
- 简单应用：Context 或 Zustand
- 复杂状态逻辑：Redux Toolkit
- 服务器状态：TanStack Query（不要用全局状态）
- 实时应用：Zustand + WebSocket

## 单体 vs 微服务

### 决策矩阵

| 因素 | 单体 | 微服务 |
|------|------|--------|
| **团队规模** | < 10 个开发者 | > 10 个开发者 |
| **系统复杂性** | 简单领域 | 复杂，有界上下文 |
| **部署** | 简单，一次性全部 | 复杂，独立服务 |
| **扩展性** | 垂直扩展 | 按服务水平扩展 |
| **开发速度** | 最初快 | 设置慢，迭代快 |
| **基础设施** | 简单（1 应用，1 数据库） | 复杂（K8s，服务网格，多数据库） |
| **数据一致性** | ACID 事务 | 最终一致性，saga |
| **测试** | 更简单的集成测试 | 更复杂的测试 |
| **监控** | 单个应用监控 | 需要分布式跟踪 |

### 何时使用单体
```
✓ Starting new product (validate idea first)
✓ Small team (< 10 developers)
✓ Simple domain with few bounded contexts
✓ Need rapid development
✓ Limited infrastructure budget
✓ Straightforward deployment requirements
```

### 何时使用微服务
```
✓ Large team (> 10 developers)
✓ Clear bounded contexts in domain
✓ Different services have different scaling needs
✓ Need independent deployment cycles
✓ Multiple teams working independently
✓ Polyglot requirements (different languages)
✓ Have DevOps expertise and infrastructure
```

### 模块化单体（推荐的中间方案）
```typescript
// Structure monolith with clear boundaries
project/
├── src/
│   ├── modules/
│   │   ├── users/
│   │   │   ├── users.module.ts
│   │   │   ├── users.service.ts
│   │   │   ├── users.controller.ts
│   │   │   └── users.repository.ts
│   │   ├── orders/
│   │   │   ├── orders.module.ts
│   │   │   └── ...
│   │   └── payments/
│   │       └── ...
│   └── shared/
│       ├── database/
│       └── auth/

// Clear module boundaries, can split later if needed
```

## API 架构模式

### REST vs GraphQL

| 方面 | REST | GraphQL |
|------|------|---------|
| **适用** | CRUD 操作，公共 API | 复杂查询，移动应用 |
| **学习曲线** | 低 | 中-高 |
| **过度获取** | 常见问题 | 设计上解决 |
| **获取不足** | 需要多个请求 | 单个请求 |
| **缓存** | HTTP 缓存效果好 | 更复杂的缓存 |
| **版本控制** | URL 版本控制（/v1，/v2） | 模式演化 |
| **工具** | Swagger，Postman | GraphiQL，Apollo Studio |

**选择 REST 时：**
- 构建简单 CRUD API
- 需要 HTTP 缓存
- 公共 API，有很多消费者
- 团队不熟悉 GraphQL

**选择 GraphQL 时：**
- 移动应用需要灵活查询
- 复杂数据需求
- 快速前端迭代
- 需要实时订阅

### BFF 模式（面向前端的后端）

```typescript
// Use when frontend needs differ from backend APIs
// Mobile BFF: Returns minimal data, optimized responses
@Controller('mobile-bff')
export class MobileBFFController {
  @Get('dashboard')
  async getMobileDashboard(@CurrentUser() user: User) {
    const [profile, notifications] = await Promise.all([
      this.userService.getProfile(user.id),
      this.notificationService.getUnread(user.id, 5), // Only 5 for mobile
    ]);
    return { profile, notifications }; // Minimal payload
  }
}

// Web BFF: Returns richer data
@Controller('web-bff')
export class WebBFFController {
  @Get('dashboard')
  async getWebDashboard(@CurrentUser() user: User) {
    const [profile, notifications, analytics, recentActivity] = await Promise.all([
      this.userService.getProfile(user.id),
      this.notificationService.getUnread(user.id, 20), // More for web
      this.analyticsService.getUserStats(user.id),
      this.activityService.getRecent(user.id),
    ]);
    return { profile, notifications, analytics, recentActivity };
  }
}
```

## 身份验证策略

### JWT vs 基于 Session

| 方面 | JWT | Session |
|------|-----|---------|
| **可扩展性** | 无状态，水平扩展 | 需要 session 存储 |
| **性能** | 每个请求无需数据库查找 | 需要 Redis/数据库查找 |
| **撤销** | 复杂（需要黑名单） | 简单（删除 session） |
| **安全性** | Token 无法失效 | 容易失效 |
| **移动/SPA** | 适合 token 存储 | 需要 cookies |
| **微服务** | 容易跨服务共享 | 难以共享 |

**混合方法（推荐）：**
```typescript
// Short-lived access token (15min) + refresh token (7 days)
interface AuthTokens {
  accessToken: string;   // JWT, 15 minutes, stored in memory
  refreshToken: string;  // Opaque token, 7 days, httpOnly cookie
}

// Access token: Stateless, fast validation
// Refresh token: Stored in DB, can be revoked
```

### SSO 集成选项

| 提供商 | 用例 | 复杂度 |
|--------|------|--------|
| **OAuth2/OIDC** | 标准协议，大多数 IdP | 中 |
| **SAML** | 企业客户，遗留系统 | 高 |
| **社交登录** | B2C 应用（Google，GitHub） | 低 |
| **Auth0/Okta** | 托管解决方案，快速设置 | 低 |

## 缓存策略

### 分层缓存方法

```typescript
// Layer 1: CDN caching (static assets)
// CloudFront, Cloudflare

// Layer 2: API response caching (Redis)
const cacheKey = `user:${userId}:profile`;
let profile = await redis.get(cacheKey);

if (!profile) {
  profile = await db.users.findById(userId);
  await redis.setex(cacheKey, 300, JSON.stringify(profile)); // 5 min TTL
}

// Layer 3: Database query caching
// PostgreSQL prepared statements, query plan caching

// Layer 4: Application-level caching
const userCache = new LRU({ max: 1000 });
```

### 缓存失效模式

```typescript
// Write-through: Update cache on write
async updateUser(id: string, data: UpdateUserDto) {
  const user = await db.users.update(id, data);
  await redis.set(`user:${id}`, JSON.stringify(user), 'EX', 300);
  return user;
}

// Write-behind: Invalidate cache, lazy load
async updateUser(id: string, data: UpdateUserDto) {
  const user = await db.users.update(id, data);
  await redis.del(`user:${id}`); // Delete, will reload on next read
  return user;
}

// Event-based: Invalidate related caches
eventBus.on('user.updated', async ({ userId }) => {
  await Promise.all([
    redis.del(`user:${userId}`),
    redis.del(`user:${userId}:posts`),
    redis.del(`user:${userId}:followers`),
  ]);
});
```

## 部署策略

### 环境演进

```
Development → Staging → Production

Development:
- Local dev servers
- Docker Compose for dependencies
- Hot reload enabled
- Debug logging
- Relaxed security

Staging:
- Production-like environment
- Real integrations (test mode)
- E2E tests run here
- Performance testing
- Security scanning

Production:
- High availability setup
- Blue-green deployment
- Monitoring & alerting
- Automated rollback
- Strict security
```

### 部署模式

| 模式 | 停机时间 | 回滚 | 复杂度 | 何时使用 |
|------|----------|------|--------|----------|
| **Recreate** | 是 | 手动 | 低 | 仅开发/测试环境 |
| **Rolling** | 否 | 渐进式 | 中 | 标准部署 |
| **Blue-Green** | 否 | 即时 | 中 | 需要零停机 |
| **Canary** | 否 | 渐进式 | 高 | 高风险更改 |
| **A/B Testing** | 否 | 渐进式 | 高 | 功能验证 |

## 快速决策树

### "我该使用哪个数据库？"
```
Need ACID transactions? → PostgreSQL
NoSQL with flexible schema? → MongoDB
Caching/sessions/queues? → Redis
AWS serverless? → DynamoDB
High read throughput? → PostgreSQL + read replicas
```

### "单体还是微服务？"
```
New product? → Modular monolith
Team < 10 people? → Modular monolith
Clear bounded contexts? → Consider microservices
Different scaling needs? → Microservices
Limited DevOps resources? → Monolith
```

### "REST 还是 GraphQL？"
```
Simple CRUD? → REST
Mobile app with flexible queries? → GraphQL
Public API? → REST
Complex data requirements? → GraphQL
Team knows GraphQL? → GraphQL, otherwise REST
```

### "使用哪个状态管理？"
```
Simple app, few global state? → React Context
Server state (API data)? → TanStack Query
Medium complexity? → Zustand
Complex state logic? → Redux Toolkit
Real-time updates? → Zustand + WebSocket
```
