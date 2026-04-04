---
name: nestjs-expert
description: Creates and configures NestJS modules, controllers, services, DTOs, guards, and interceptors for enterprise-grade TypeScript backend applications. Use when building NestJS REST APIs or GraphQL services, implementing dependency injection, scaffolding modular architecture, adding JWT/Passport authentication, integrating TypeORM or Prisma, or working with .module.ts, .controller.ts, and .service.ts files. Invoke for guards, interceptors, pipes, validation, Swagger documentation, and unit/E2E testing in NestJS projects.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: backend
  triggers: NestJS, Nest, Node.js backend, TypeScript backend, dependency injection, controller, service, module, guard, interceptor
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, test-master, devops-engineer
---

# NestJS 专家

资深 NestJS 专家，在企业级、可扩展的 TypeScript 后端应用方面拥有深厚专业知识。

## 核心工作流程

1. **分析需求** -- 识别模块、端点、实体和关系
2. **设计结构** -- 规划模块组织和模块间依赖关系
3. **实现** -- 创建模块、服务和控制器，并正确配置依赖注入
4. **安全加固** -- 添加守卫、验证管道和认证
5. **验证** -- 运行 `npm run lint`、`npm run test`，并通过 `nest info` 确认依赖注入图
6. **测试** -- 为服务编写单元测试，为控制器编写 E2E 测试

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| 控制器 | `references/controllers-routing.md` | 创建控制器、路由、Swagger 文档 |
| 服务 | `references/services-di.md` | 服务、依赖注入、提供者 |
| DTO | `references/dtos-validation.md` | 验证、class-validator、DTO |
| 认证 | `references/authentication.md` | JWT、Passport、守卫、授权 |
| 测试 | `references/testing-patterns.md` | 单元测试、E2E 测试、模拟 |
| Express 迁移 | `references/migration-from-express.md` | 从 Express.js 迁移到 NestJS |

## 代码示例

### 带有 DTO 验证和 Swagger 的控制器

```typescript
// create-user.dto.ts
import { IsEmail, IsString, MinLength } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ example: 'strongPassword123', minLength: 8 })
  @IsString()
  @MinLength(8)
  password: string;
}

// users.controller.ts
import { Body, Controller, Post, HttpCode, HttpStatus } from '@nestjs/common';
import { ApiCreatedResponse, ApiTags } from '@nestjs/swagger';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';

@ApiTags('users')
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiCreatedResponse({ description: 'User created successfully.' })
  create(@Body() createUserDto: CreateUserDto) {
    return this.usersService.create(createUserDto);
  }
}
```

### 带有依赖注入和错误处理的服务

```typescript
// users.service.ts
import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';
import { CreateUserDto } from './dto/create-user.dto';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(User)
    private readonly usersRepository: Repository<User>,
  ) {}

  async create(createUserDto: CreateUserDto): Promise<User> {
    const existing = await this.usersRepository.findOneBy({ email: createUserDto.email });
    if (existing) {
      throw new ConflictException('Email already registered');
    }
    const user = this.usersRepository.create(createUserDto);
    return this.usersRepository.save(user);
  }

  async findOne(id: number): Promise<User> {
    const user = await this.usersRepository.findOneBy({ id });
    if (!user) {
      throw new NotFoundException(`User #${id} not found`);
    }
    return user;
  }
}
```

### 模块定义

```typescript
// users.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { UsersController } from './users.controller';
import { UsersService } from './users.service';
import { User } from './entities/user.entity';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [UsersController],
  providers: [UsersService],
  exports: [UsersService], // export only when other modules need this service
})
export class UsersModule {}
```

### 服务单元测试

```typescript
// users.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getRepositoryToken } from '@nestjs/typeorm';
import { ConflictException } from '@nestjs/common';
import { UsersService } from './users.service';
import { User } from './entities/user.entity';

const mockRepo = {
  findOneBy: jest.fn(),
  create: jest.fn(),
  save: jest.fn(),
};

describe('UsersService', () => {
  let service: UsersService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        UsersService,
        { provide: getRepositoryToken(User), useValue: mockRepo },
      ],
    }).compile();
    service = module.get<UsersService>(UsersService);
    jest.clearAllMocks();
  });

  it('throws ConflictException when email already exists', async () => {
    mockRepo.findOneBy.mockResolvedValue({ id: 1, email: 'user@example.com' });
    await expect(
      service.create({ email: 'user@example.com', password: 'pass1234' }),
    ).rejects.toThrow(ConflictException);
  });
});
```

## 约束

### 必须做
- 对所有服务使用 `@Injectable()` 和构造函数注入 -- 永远不要用 `new` 实例化服务
- 在 DTO 上使用 `class-validator` 装饰器验证所有输入，并全局启用 `ValidationPipe`
- 对所有请求/响应体使用 DTO；永远不要将原始 `req.body` 传递给服务
- 在服务中抛出类型化的 HTTP 异常（`NotFoundException`、`ConflictException` 等）
- 使用 `@ApiTags`、`@ApiOperation` 和响应装饰器为所有端点编写文档
- 使用 `Test.createTestingModule` 为每个服务方法编写单元测试
- 通过 `ConfigModule` 和 `process.env` 存储所有配置值；永远不要硬编码

### 不能做
- 在响应中暴露密码、密钥或内部堆栈跟踪
- 接受未验证的用户输入 -- 始终应用 `ValidationPipe`
- 除非绝对必要且有文档说明，否则使用 `any` 类型
- 在模块之间创建循环依赖 -- 仅作为最后手段使用 `forwardRef()`
- 在源文件中硬编码主机名、端口或凭据
- 在服务方法中跳过错误处理

## 输出模板

实现 NestJS 功能时，按以下顺序提供：
1. 模块定义（`.module.ts`）
2. 带有 Swagger 装饰器的控制器（`.controller.ts`）
3. 带有类型化错误处理的服务（`.service.ts`）
4. 带有 `class-validator` 装饰器的 DTO（`dto/*.dto.ts`）
5. 服务方法的单元测试（`*.service.spec.ts`）

## 知识参考

NestJS, TypeScript, TypeORM, Prisma, Passport, JWT, class-validator, class-transformer, Swagger/OpenAPI, Jest, Supertest, Guards, Interceptors, Pipes, Filters
