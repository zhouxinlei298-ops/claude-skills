# 集成模式

## 跨栈类型安全

### 共享类型定义
```typescript
// packages/shared/types.ts
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
}

export interface CreateUserDto {
  email: string;
  name: string;
  password: string;
}

export interface UpdateUserDto {
  email?: string;
  name?: string;
}

// API response wrapper
export interface ApiResponse<T> {
  data: T;
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
  };
}
```

### 共享验证（Zod）
```typescript
// packages/shared/schemas.ts
import { z } from 'zod';

export const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(12),
});

export type CreateUserDto = z.infer<typeof createUserSchema>;

// Backend: const validated = createUserSchema.parse(req.body);
// Frontend: useForm({ resolver: zodResolver(createUserSchema) });
```

### API 客户端生成
```typescript
// Generated from OpenAPI spec
import { UserApi } from '@/generated/api';

const user = await userApi.getUser({ id: '123' }); // Type-safe
```

## 架构决策

### Monorepo 结构
```
workspace/
├── packages/
│   ├── shared/           # Shared types, utils, schemas
│   ├── backend/          # Node.js/Python backend
│   ├── frontend/         # React/Vue frontend
│   ├── mobile/           # React Native (optional)
│   └── e2e-tests/        # End-to-end tests
├── package.json
└── turbo.json           # Turborepo config
```

```json
// package.json (workspace root)
{
  "private": true,
  "workspaces": ["packages/*"],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test"
  }
}

// turbo.json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "dev": {
      "cache": false
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    }
  }
}
```

### BFF（面向前端的后端）
```typescript
// Aggregates multiple services for frontend
@Controller('bff')
export class BFFController {
  @Get('dashboard')
  async getDashboard(@CurrentUser() user: User) {
    const [profile, orders, analytics] = await Promise.all([
      this.userService.getProfile(user.id),
      this.orderService.getRecentOrders(user.id, 5),
      this.analyticsService.getUserStats(user.id),
    ]);

    return { profile, orders, analytics };
  }
}
```

### 微服务 vs 单体决策矩阵

| 因素 | 单体 | 微服务 |
|------|------|--------|
| 团队规模 | < 10 个开发者 | > 10 个开发者 |
| 部署 | 简单，一次性全部 | 复杂，独立部署 |
| 扩展性 | 垂直扩展 | 按服务水平水平扩展 |
| 开发速度 | 最初快 | 设置慢，迭代快 |
| 基础设施 | 简单 | 更复杂（K8s，服务网格） |
| 数据一致性 | ACID 事务 | 最终一致性 |

## 部署管道

### CI/CD 配置（GitHub Actions）
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run unit tests
        run: npm run test

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Build
        run: npm run build

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploy to staging environment"
          # Deploy commands here

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          echo "Deploy to production environment"
          # Blue-green deployment commands
```

### 数据库迁移
```typescript
// TypeORM migration
export class AddUserRoles implements MigrationInterface {
  async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
      CREATE INDEX idx_users_role ON users(role);
    `);
  }

  async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.query(`
      DROP INDEX idx_users_role;
      ALTER TABLE users DROP COLUMN role;
    `);
  }
}

// Run: npm run migration:run
// Revert: npm run migration:revert
```

### 功能标志
```typescript
class FeatureFlags {
  private flags = new Map<string, boolean>();

  constructor() {
    this.flags.set('new_dashboard', process.env.FEATURE_NEW_DASHBOARD === 'true');
  }

  isEnabled(flag: string): boolean {
    return this.flags.get(flag) ?? false;
  }
}

// Backend: if (flags.isEnabled('new_dashboard')) return getNewDashboard();
// Frontend: {flags.isEnabled('new_dashboard') ? <New /> : <Old />}
```

### 蓝绿部署
```bash
#!/bin/bash
docker build -t myapp:new .
kubectl apply -f k8s/green-deployment.yml
kubectl wait --for=condition=ready pod -l app=myapp,env=green --timeout=300s
kubectl patch service myapp -p '{"spec":{"selector":{"env":"green"}}}'
# Keep blue for rollback, then: kubectl delete deployment myapp-blue
```

## 端到端测试

### Playwright E2E 测试
```typescript
import { test, expect } from '@playwright/test';

test('should login successfully', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  await page.waitForResponse(res =>
    res.url().includes('/api/auth/login') && res.status() === 200
  );

  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('[data-testid="user-name"]')).toHaveText('Test User');
});
```

### 使用 k6 进行负载测试
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
  },
};

export default function () {
  const res = http.get('https://api.example.com/users');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

## 环境管理

### 多环境配置
```typescript
interface Environment {
  api: { baseUrl: string; timeout: number };
  database: { host: string; port: number; name: string };
  features: { analytics: boolean; betaFeatures: boolean };
}

const environments: Record<string, Environment> = {
  development: {
    api: { baseUrl: 'http://localhost:3000', timeout: 30000 },
    database: { host: 'localhost', port: 5432, name: 'myapp_dev' },
    features: { analytics: false, betaFeatures: true },
  },
  production: {
    api: { baseUrl: 'https://api.example.com', timeout: 10000 },
    database: { host: process.env.DB_HOST!, port: 5432, name: 'myapp_prod' },
    features: { analytics: true, betaFeatures: false },
  },
};

export const config = environments[process.env.NODE_ENV || 'development'];
```

## 快速参考

| 模式 | 用例 | 关键收益 |
|------|------|----------|
| 共享类型 | 类型安全 | 防止 API 合同偏移 |
| Zod 模式 | 验证 | DRY 验证逻辑 |
| Monorepo | 多包项目 | 代码共享和一致性 |
| BFF 模式 | 复杂前端 | 为 UI 需要优化的 API |
| 功能标志 | 渐进式发布 | 安全部署 |
| 蓝绿部署 | 零停机 | 即时回滚 |
| E2E 测试 | 用户流程 | 捕获集成错误 |
| 负载测试 | 性能验证 | 确保可扩展性 |