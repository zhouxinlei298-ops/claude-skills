# 控制器与路由

## 带有 Swagger 的控制器

```typescript
import {
  Controller, Get, Post, Patch, Delete,
  Body, Param, Query, HttpCode, HttpStatus, UseGuards
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiParam, ApiQuery } from '@nestjs/swagger';
import { ParseUUIDPipe, ParseIntPipe } from '@nestjs/common';

@Controller('users')
@ApiTags('users')
@UseGuards(JwtAuthGuard)
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Post()
  @ApiOperation({ summary: 'Create user' })
  @ApiResponse({ status: 201, type: UserDto })
  @ApiResponse({ status: 400, description: 'Validation failed' })
  create(@Body() dto: CreateUserDto): Promise<UserDto> {
    return this.usersService.create(dto);
  }

  @Get()
  @ApiOperation({ summary: 'Get all users' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  findAll(
    @Query('page', new ParseIntPipe({ optional: true })) page = 1,
    @Query('limit', new ParseIntPipe({ optional: true })) limit = 20,
  ): Promise<UserDto[]> {
    return this.usersService.findAll({ page, limit });
  }

  @Get(':id')
  @ApiParam({ name: 'id', type: 'string', format: 'uuid' })
  @ApiResponse({ status: 200, type: UserDto })
  @ApiResponse({ status: 404, description: 'User not found' })
  findOne(@Param('id', ParseUUIDPipe) id: string): Promise<UserDto> {
    return this.usersService.findOne(id);
  }

  @Patch(':id')
  update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: UpdateUserDto,
  ): Promise<UserDto> {
    return this.usersService.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  remove(@Param('id', ParseUUIDPipe) id: string): Promise<void> {
    return this.usersService.remove(id);
  }
}
```

## 嵌套路由

```typescript
@Controller('posts/:postId/comments')
@ApiTags('comments')
export class CommentsController {
  @Get()
  findAll(@Param('postId', ParseUUIDPipe) postId: string) {
    return this.commentsService.findByPost(postId);
  }

  @Post()
  create(
    @Param('postId', ParseUUIDPipe) postId: string,
    @Body() dto: CreateCommentDto,
  ) {
    return this.commentsService.create(postId, dto);
  }
}
```

## 全局前缀与版本控制

```typescript
// main.ts
const app = await NestFactory.create(AppModule);
app.setGlobalPrefix('api');
app.enableVersioning({ type: VersioningType.URI });

// controller.ts
@Controller({ path: 'users', version: '1' })  // /api/v1/users
export class UsersV1Controller {}

@Controller({ path: 'users', version: '2' })  // /api/v2/users
export class UsersV2Controller {}
```

## 快速参考

| 装饰器 | 用途 |
|------|------|
| `@Controller('path')` | 定义路由前缀 |
| `@Get()`、`@Post()` | HTTP 方法 |
| `@Param('name')` | 路径参数 |
| `@Query('name')` | 查询参数 |
| `@Body()` | 请求体 |
| `@HttpCode(201)` | 覆盖状态码 |
| `@ApiTags()` | Swagger 分组 |
| `@ApiOperation()` | 端点描述 |
| `@ApiResponse()` | 文档响应 |
