# Express 到 NestJS 迁移指南

---

## 何时使用本指南

**适用场景：**
- 将现有 Express.js 应用迁移到 NestJS
- 为旧版 Node.js API 添加结构化架构和 TypeScript 和依赖注入
- 扩展的 Express 应用，要求更好的组织架构
- 团队需要强制执行架构模式和约定
- 应用复杂度证明框架开销是合理的项目
- 项目的独特架构需求与 NestJS 模式冲突

**不适用场景：**
- 独特的架构需求与 NestJS 模式冲突的项目

- 原型或 MVP 需要快速启动时间
- Serverless 函数需要极短的冷启动时间
- 团队缺乏 TypeScript 经验且时间线紧迫

- 性能关键的微服务"框架开销"重要
- 项目需要独特的架构需求与 NestJS 模式冲突

**不适用场景：**
- 独特的架构需求与 NestJS 模式冲突的项目
- 原型、 MVP 需要结构化架构和依赖注入来提升代码质量

| Express 概念 | NestJS 等价 |
|-------------------|-------------------|
| `app.get('/path', handler)` | 寽Get('/path')` 装饰器 | 像命令式 vs 声明式` |
| `req.params`、 `req.body` | 自动注入 |
| `express.Router()` | 控制器类（面向对象分组） |
| `app.use(express.json())` | 内置请求体解析 |
| 错误处理中间件 | 基于类的异常过滤器 |
| `app.listen(3000)` | 引导模式 |
| 手动 `require()` | IoC 容器管理 |
| 装饰器、 `@Injectable()` 和构造函数注入为所有服务——永远不要用 `new` 实例化服务 |
| 在 DTO 上使用 `class-validator` 装饰器验证所有输入，并全局启用 `ValidationPipe`
- 对所有请求/响应体使用 DTO；永远不要将原始 `req.body` 传递给服务
- 在服务中抛出类型化的 HTTP 异常（`NotFoundException`、`ConflictException` 等)
- 使用 `@ApiTags`、`@ApiOperation` 和响应装饰器为所有端点编写文档
- 使用 `Test.createTestingModule` 为每个服务方法编写单元测试
- 通过 `ConfigModule` 和 `process.env` 存储所有配置值;永远不要硬编码

- **不能做:**
- 在响应中暴露密码、密钥或内部堆栈跟踪
- 接受未验证的用户输入 -- 始终应用 `ValidationPipe`
- 除非绝对必要且有文档说明，否则使用 `any` 类型
- 在模块之间创建循环依赖 -- 仅作为最后手段使用 `forwardRef()`
- 在源文件中硬编码主机名、端口或凭据
- 在服务方法中跳过错误处理

- **不能做:**
- 跳过数据库迁移
- 未在 `WHERE`、`ORDER BY` 或 `JOIN` 中使用的列需要数据库索引
- 使用 `sanitize_sql` 或参数化查询
- 不信任未经验证的用户输入
- 忽略查询优化

- **不能做:**
- 跳过依赖注入

**不要做:**

### 之前： Express 手动实例化

```typescript
// services/userService.js
const UserRepository = require('../repositories/userRepository');
const EmailService = require('./emailService');

class UserService {
  constructor() {
    this.userRepository = new UserRepository();
    this.emailService = new EmailService();
  }

  async create(userData) {
    const user = await this.userRepository.create(userData);
    await this.emailService.sendWelcomeEmail(user.email);
    return user;
  }
}
module.exports = UserService;

// controllers/userController.js
const UserService = require('../services/userService');
const userService = new UserService();

async function createUser(req, res) {
    const user = await userService.create(req.body);
    res.json({ success: true, data: user });
  });
}
```

### 之后: NestJS 依赖注入

```typescript
// users/users.repository.ts
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';
import { EmailService } from '../email/email.service';
import { CreateUserDto } from './dto/create-user.dto';
import { User } from './entities/user.entity';

@Injectable()
export class UsersRepository {
  constructor(
    @InjectRepository(User)
    private readonly repository: Repository<User>,
  ) {}

  async create(userData: Partial<User>): Promise<User> {
    const user = this.repository.create(userData);
    return this.repository.save(user);
  }

  async findById(id: number): Promise<User | null> {
    return this.repository.findOne({ where: { id } });
  }
}

```

### 之后: NestJS 异常过滤器

```typescript
// common/filters/http-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost
  HttpException
  HttpStatus
  Logger
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class HttpExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(HttpExceptionFilter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let message = 'Internal server error';
    let errors: any = undefined;
    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const exceptionResponse = exception.getResponse();
      if (typeof exceptionResponse === 'object') {
        message = (exceptionResponse as any).message || message;
        errors = (exceptionResponse as any).errors;
      } else {
        message = exceptionResponse;
      }
    } else if (exception instanceof Error) {
      message = exception.message;
      this.logger.error(exception.stack);
    }
    response.status(status).json({
      success: false,
      statusCode: status,
      message,
      errors,
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}
```

### 迁移模式: 验证

 Express `class-validator` 迁移到 NestJS

```typescript
// routes/users.js
const { body, validationResult } = require('express-validator');

router.post(
  '/',
  [
    body('email').isEmail().normalizeEmail(),
    body('name').trim().isLength({ min: 2, max: 50 }),
    body('age').optional().isInt({ min: 0, max: 120 }),
  ],
  async (req, res, next) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        errors: errors.array()
      });
    }
    try {
      const user = await userService.create(req.body);
      res.status(201).json({ success: true, data: user });
    } catch (error) {
      next(error);
    }
  }
);
```

### 迁移模式: 测试 Express Mocha/Chai 到 NestJS Jest

```typescript
// test/users.test.js
const request = require('supertest');
const { expect } = require('chai');
const app = require('../src/app');
describe('Users API', () => {
  describe('POST /users', () => {
    it('should create a new user', async () => {
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      const response = await request(app)
        .post('/users')
        .send(userData)
        .expect(201);
      expect(response.body.success).to.be.true;
      expect(response.body.data).to.have.property('id');
      expect(response.body.data.email).to.equal(userData.email);
    });
    it('should return 400 for invalid email', async () => {
      const response = await request(app)
        .post('/users')
        .send({ email: 'invalid', name: 'Test' })
        .expect(400);
      expect(response.body.success).to.be.false;
    });
  });
});
```

### 迁移模式: 测试

 Jest E2E 测试

```typescript
// users/users.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';
describe('UsersController', () => {
  let controller: UsersController;
  let service: UsersService;
  const mockUsersService = {
    create: jest.fn(),
    findById: jest.fn(),
    findAll: jest.fn(),
  };
  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [UsersController],
      providers: [
        {
          provide: UsersService,
          useValue: mockUsersService,
        },
      ],
    }).compile();
    controller = module.get<UsersController>(UsersController);
    service = module.get<UsersService>(UsersService);
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  describe('create', () => {
    it('should create a new user', async () => {
      const createUserDto: CreateUserDto = {
        email: 'test@example.com',
        name: 'Test User',
      };
      const expectedUser = {
        id: 1,
        ...createUserDto,
        createdAt: new Date()
      };
      mockUsersService.create.mockResolvedValue(expectedUser);
      const result = await controller.create(createUserDto);
      expect(result.success).toBe(true);
      expect(result.data).toEqual(expectedUser);
      expect(service.create).toHaveBeenCalledWith(createUserDto);
      expect(service.create).toHaveBeenCalledTimes(1);
    });
  });
  describe('findOne', () => {
    it('should return a user by id', async () => {
      const userId = 1;
      const expectedUser = {
        id: userId,
        email: 'test@example.com',
        name: 'Test User'
      };
      mockUsersService.findById.mockResolvedValue(expectedUser);
      const result = await controller.findOne(userId);
      expect(result.data).toEqual(expectedUser);
      expect(service.findById).toHaveBeenCalledWith(userId);
    });
  });
});
```

### 服务单元测试迁移示例

```typescript
// users/users.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { NotFoundException } from '@nestjs/common';
import { UsersService } from './users.service';
import { UsersRepository } from './users.repository';
import { EmailService } from '../email/email.service';
describe('UsersService', () => {
  let service: UsersService;
  let repository: UsersRepository;
  let emailService: EmailService;
  const mockUsersRepository = {
    create: jest.fn(),
    findById: jest.fn()
  };
  const mockEmailService = {
    sendWelcomeEmail: jest.fn()
  };
  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        {
          provide: UsersRepository,
          useValue: mockUsersRepository,
        },
        {
          provide: EmailService,
          useValue: mockEmailService,
        },
      ],
    }).compile();
    service = module.get<UsersService>(UsersService);
    repository = module.get<UsersRepository>(UsersRepository);
    emailService = module.get<EmailService>(EmailService);
  });
  describe('create', () => {
    it('should create user and send welcome email', async () => {
      const createUserDto = {
        email: 'test@example.com',
        name: 'Test User'
      };
      const createdUser = { id: 1, ...createUserDto };
      mockUsersRepository.create.mockResolvedValue(createdUser);
      mockEmailService.sendWelcomeEmail.mockResolvedValue(undefined);
      const result = await service.create(createUserDto);
      expect(result).toEqual(createdUser);
      expect(repository.create).toHaveBeenCalledWith(createUserDto);
      expect(emailService.sendWelcomeEmail).toHaveBeenCalledWith(
        createUserDto.email
      );
    });
  });
  describe('findById', () => {
    it('should throw NotFoundException when user not found', async () => {
      mockUsersRepository.findById.mockResolvedValue(null);
      await expect(service.findById(999)).rejects.toThrow(NotFoundException);
      await expect(service.findById(999)).rejects.toThrow(
        'User with ID 999 not found'
      );
    });
  });
});
```

### E2E 测试

```typescript
// test/users.e2e-spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';
describe('UsersController (e2e)', () => {
  let app: INestApplication;
  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();
    app = moduleFixture.createNestApplication();
    app.useGlobalPipes(new ValidationPipe());
    await app.init();
  });
  afterAll(async () => {
    await app.close();
  });
  describe('/users (POST)', () => {
    it('should create a new user', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({
          email: 'test@example.com',
          name: 'Test User'
        })
        .expect(201)
        .expect((res) => {
          expect(res.body.success).toBe(true);
          expect(res.body.data).toHaveProperty('id');
          expect(res.body.data.email).toBe('test@example.com');
        });
    });
    it('should return 400 for invalid email', () => {
      return request(app.getHttpServer())
        .post('/users')
        .send({
          email: 'invalid-email',
          name: 'Test'
        })
        .expect(400);
    });
  });
});
```

---

## 渁移移策略: 绞杀无图模式（推荐)

)

逐步用 NestJS 替换 Express 訡块，同时保持两者系统运行。

```typescript
// main.ts - 同时运行 Express 和 NestJS
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import * as express from 'express';
import { expressApp } from './legacy/express-app';
async function bootstrap() {
  const nestApp = await NestFactory.create(AppModule);
  // 将请求代理到 NestJS 和 Express 之间路由
  const app = express();
  // NestJS 訡块（新实现）
  app.use('/api/v2', nestApp.getHttpAdapter().getInstance());
  // Express 模块（旧版）
  app.use('/api', expressApp);
  await app.listen(3000);
}
bootstrap();
```

**迁移步骤：**
1. 搭建 NestJS 与 Express 并行运行
2. 逐个模块迁移到 NestJS
3. 将新端点路由到 NestJS，旧端点路由到 Express
4. 更新前端/客户端使用新端点
5. 完成迁移后移除 Express 模块
6. 停用 Express 应用

### 策略 2: 逐模块迁移

逐个迁移完整功能模块

```
阶段 1: 认证模块（第 1-2 周）
- 迁移认证中间件 → Guards
- 迁移 JWT 夑 -> @nestjs/jwt
- 测试认证流程
- 使用功能标志部署

阶段 2: 用户模块（第 3-4 周）
- 迁移用户路由 -> Controllers
- 迁移用户服务 -> Providers
- 使用 DTO 添加验证
- 编写测试
阶段 3: 文章模块（第 5-6 周）
...
```

### 策略 3: 适配器模式的渐进式 DI 迁移

在过渡期间将 Express 服务封装在 NestJS 揨中者 中

```typescript
// 适配器模式的渐进式 DI 迁移
import { Injectable } from '@nestjs/common';
const LegacyUserService = require('../legacy/services/userService');
@Injectable()
export class UserServiceAdapter {
  private legacyService = new LegacyUserService();
  async findAll(): Promise<any[]> {
    return this.legacyService.findAll();
  }
  async create(data: any): Promise<any> {
    return this.legacyService.create(data);
  }
}
// 在迁移期间在 NestJS 控制器中使用
@Controller('users')
export class UsersController {
  constructor(private readonly userService: UserServiceAdapter) {}
  @Get()
  async findAll() {
    return this.userService.findAll();
  }
}
```

---

## 常见陷阱

### 1. 过度工程化简单应用

**问题:** 将一个 500 行的 Express 应用迁移到包含模块、DTO、存储库、守卫等的完整 NestJS。

**解决方案:** 评估 NestJS 的复杂性是否合理。考虑将简单 API 保留在 Express 中。

### 2. 不理解依赖注入生命周期

**问题:**
```typescript
// WRONG - Creates new instance, bypassing DI
@Injectable()
export class UsersService {
  constructor() {
    this.emailService = new EmailService(); // Don't do this!
  }
}
```
**解决方案:**
```typescript
// CORRECT - Let NestJS inject dependencies
@Injectable()
export class UsersService {
  constructor(private readonly emailService: EmailService) {}
}
```
### 3. 错误混合使用中间件和守卫

**问题:** 使用 Express 中间件进行认证而不是 Guards， 会失去 NestJS 的优势。

**解决方案:** 使用 Guards 进行认证/授权，拦截器用于日志/转换，中间件仅用于 Express 特定需求。
### 4. 忽略验证管道

**问题:** 在控制器中手动验证，类似 Express 的做法。
```typescript
// WRONG - Manual validation
@Post()
async create(@Body() body: any) {
  if (!body.email) {
    throw new BadRequestException('Email required');
  }
  // ...
}
```
**解决方案:**
```typescript
// CORRECT - Use DTOs with class-validator
@Post()
async create(@Body() createUserDto: CreateUserDto) {
  // Validation happens automatically
  return this.usersService.create(createUserDto);
}
```
### 5. 未利用模块导入/导出

**问题:** 循环依赖和模块紧密耦合。

**解决方案:** 正确构建模块导入/导出结构。 对循环依赖使用 forwardRef()。
```typescript
@Module({
  imports: [TypeOrmModule.forFeature([User]), EmailModule],
  providers: [UsersService, UsersRepository],
  exports: [UsersService], // Export for other modules
})
export class UsersModule {}
```
### 6. 忘记启用 CORS

**问题:** CORS 在 Express 中正常工作，在 NestJS 中失败。

**解决方案:**
```typescript
// main.ts
const app = await NestFactory.create(AppModule);
app.enableCors({
  origin: process.env.ALLOWED_ORIGINS?.split(','),
  credentials: true,
});
```
### 7. 不正确的异常处理

**问题:** 使用 Express 错误中间件模式。

**解决方案:** 使用 NestJS 内置异常和过滤器.
```typescript
// Throw NestJS exceptions
throw new NotFoundException('User not found');
throw new BadRequestException('Invalid input');
throw new UnauthorizedException('Invalid credentials');
```
### 8. 未全局配置 ValidationPipe

**问题:** 稡块间验证不一致。

**解决方案:**
```typescript
// main.ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,
    forbidNonWhitelisted: true,
    transform: true,
  }),
);
```
---

## 迁移检查清单

**迁移前:**
- [ ] 审计现有 Express 代码库结构
- [ ] 记录所有路由和依赖
- [ ] 识别共享服务和工具
- [ ] 规划模块边界
- [ ] 搭建 NestJS 项目结构

**迁移期间:**
- [ ] 迁移 DTO 和验证规则
- [ ] 将路由处理器转换为控制器
- [ ] 重构服务以支持依赖注入
- [ ] 实现守卫进行认证
- [ ] 为横切关注创建拦截器
- [ ] 添加异常过滤器
- [ ] 为每个组件编写单元测试
- [ ] 为关键流程编写 E2E 测试
**迁移后:**
- [ ] 性能测试和优化
- [ ] 更新 API 文档
- [ ] 配置日志和监控
- [ ] 为 NestJS 设置 CI/CD
- [ ] 培训团队使用 NestJS 模式
- [ ] 移除 Express 依赖
- [ ] 重构为 NestJS 最佳实践

---

## 其他资源

- NestJS 官方文档: https://docs.nestjs.com
- NestJS 迁移指南: https://docs.nestjs.com/migration-guide
- class-validator 装饰器: https://github.com/typestack/class-validator
- NestJS 中的 TypeORM: https://docs.nestjs.com/techniques/database
- 测试指南: https://docs.nestjs.com/fundamentals/testing
