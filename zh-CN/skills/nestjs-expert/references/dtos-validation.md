# DTO 与验证

## DTO 模式

```typescript
import {
  IsEmail, IsString, IsOptional, IsBoolean, IsInt,
  MinLength, MaxLength, Min, Max, IsUUID, IsEnum,
  IsArray, ArrayMinSize, ValidateNested, Matches
} from 'class-validator';
import { Type, Transform } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional, PartialType, OmitType, PickType } from '@nestjs/swagger';

export class CreateUserDto {
  @ApiProperty({ example: 'user@example.com' })
  @IsEmail()
  email: string;

  @ApiProperty({ minLength: 8 })
  @IsString()
  @MinLength(8)
  @Matches(/^(?=.*[A-Z])(?=.*\d)/, { message: 'Password must contain uppercase and digit' })
  password: string;

  @ApiProperty()
  @IsString()
  @MinLength(2)
  @MaxLength(50)
  name: string;

  @ApiPropertyOptional({ enum: UserRole, default: UserRole.USER })
  @IsOptional()
  @IsEnum(UserRole)
  role?: UserRole = UserRole.USER;
}

```

## 嵌套验证

```typescript
export class CreateOrderDto {
  @ApiProperty({ type: [OrderItemDto] })
  @IsArray()
  @ArrayMinSize(1)
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];

  @ApiProperty({ type: AddressDto })
  @ValidateNested()
  @Type(() => AddressDto)
  shippingAddress: AddressDto;
}
```

## 自定义验证

```typescript
import { registerDecorator, ValidationOptions, ValidationArguments } from 'class-validator';

// Custom decorator
export function IsStrongPassword(options?: ValidationOptions) {
  return function (object: object, propertyName: string) {
    registerDecorator({
      name: 'isStrongPassword',
      target: object.constructor,
      propertyName,
      options,
      validator: {
        validate(value: string) {
          return /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$/.test(value);
        },
        defaultMessage(): string {
          return 'Password must contain uppercase, lowercase, digit, and special character';
        },
      },
    });
  };
}

// Usage
@IsStrongPassword()
password: string;
```

## 转换与清理

```typescript
export class QueryDto {
  @Transform(({ value }) => parseInt(value, 10))
  @IsInt()
  @Min(1)
  page: number = 1;

  @Transform(({ value }) => value?.trim().toLowerCase())
  @IsString()
  @IsOptional()
  search?: string;

  @Transform(({ value }) => value === 'true')
  @IsBoolean()
  isActive: boolean = true;
}
```

## 全局启用验证

```typescript
// main.ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,           // 剥离未知属性
  forbidNonWhitelisted: true, // 对未知属性抛出异常
  transform: true,            // 自动转换类型
  transformOptions: {
    enableImplicitConversion: true,
  },
}));
```

## 快速参考

| 装饰器 | 用途 |
|------|------|
| `@IsString()` | 字符串类型 |
| `@IsEmail()` | 有效邮箱 |
| `@MinLength(n)` | 最小字符串长度 |
| `@IsInt()`, `@Min(n)` | 整数验证 |
| `@IsEnum(Enum)` | 枙4 值 |
| `@IsOptional()` | 可选字段 |
| `@ValidateNested()` | 验证嵌套对象 |
| `@Type(() => Class)` | 转换为类 |
| `@Transform()` | 自定义转换 |
| `PartialType()` | 所有字段可选 |
| `OmitType()` | 排除字段 |
| `PickType()` | 仅包含字段 |
