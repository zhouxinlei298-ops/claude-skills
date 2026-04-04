---
name: typescript-pro
description: Implements advanced TypeScript type systems, creates custom type guards, utility types, and branded types, and configures tRPC for end-to-end type safety. Use when building TypeScript applications requiring advanced generics, conditional or mapped types, discriminated unions, monorepo setup, or full-stack type safety with tRPC.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: TypeScript, generics, type safety, conditional types, mapped types, tRPC, tsconfig, type guards, discriminated unions
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, api-designer
---

# TypeScript Pro

## 核心工作流程

1. **分析类型架构** - 审查 tsconfig、类型覆盖率、构建性能
2. **设计类型优先的 API** - 创建品牌类型、泛型、工具类型
3. **以类型安全实现** - 编写类型守卫、可辨识联合、条件类型；运行 `tsc --noEmit` 在继续之前捕获类型错误
4. **优化构建** - 配置项目引用、增量编译、tree shaking；重新运行 `tsc --noEmit` 以确认更改后零错误
5. **测试类型** - 使用 `type-coverage` 等工具确认类型覆盖率；验证所有公共 API 都具有显式返回类型；迭代步骤 3-4 直到所有检查通过

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|------|----------|----------|
| 高级类型 | `references/advanced-types.md` | 泛型、条件类型、映射类型、模板字面量 |
| 类型守卫 | `references/type-guards.md` | 类型收窄、可辨识联合、断言函数 |
| 工具类型 | `references/utility-types.md` | Partial、Pick、Omit、Record、自定义工具类型 |
| 配置 | `references/configuration.md` | tsconfig 选项、严格模式、项目引用 |
| 模式 | `references/patterns.md` | 建造者模式、工厂模式、类型安全的 API |

## 代码示例

### 品牌类型
```typescript
// Branded type for domain modeling
type Brand<T, B extends string> = T & { readonly __brand: B };
type UserId  = Brand<string, "UserId">;
type OrderId = Brand<number, "OrderId">;

const toUserId  = (id: string): UserId  => id as UserId;
const toOrderId = (id: number): OrderId => id as OrderId;

// Usage — prevents accidental id mix-ups at compile time
function getOrder(userId: UserId, orderId: OrderId) { /* ... */ }
```

### 可辨识联合与类型守卫
```typescript
type LoadingState = { status: "loading" };
type SuccessState = { status: "success"; data: string[] };
type ErrorState   = { status: "error";   error: Error };
type RequestState = LoadingState | SuccessState | ErrorState;

// Type predicate guard
function isSuccess(state: RequestState): state is SuccessState {
  return state.status === "success";
}

// Exhaustive switch with discriminated union
function renderState(state: RequestState): string {
  switch (state.status) {
    case "loading": return "Loading…";
    case "success": return state.data.join(", ");
    case "error":   return state.error.message;
    default: {
      const _exhaustive: never = state;
      throw new Error(`Unhandled state: ${_exhaustive}`);
    }
  }
}
```

### 自定义工具类型
```typescript
// Deep readonly — immutable nested objects
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};

// Require exactly one of a set of keys
type RequireExactlyOne<T, Keys extends keyof T = keyof T> =
  Pick<T, Exclude<keyof T, Keys>> &
  { [K in Keys]-?: Required<Pick<T, K>> & Partial<Record<Exclude<Keys, K>, never>> }[Keys];
```

### 推荐的 tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "isolatedModules": true,
    "declaration": true,
    "declarationMap": true,
    "incremental": true,
    "skipLibCheck": false
  }
}
```

## 约束

### 必须做
- 启用严格模式及所有编译器标志
- 使用类型优先的 API 设计
- 为领域建模实现品牌类型
- 使用 `satisfies` 运算符进行类型验证
- 为状态机创建可辨识联合
- 使用带类型谓词的 `Annotated` 模式
- 为库生成声明文件
- 优化类型推断

### 不能做
- 在没有正当理由的情况下使用显式 `any`
- 跳过公共 API 的类型覆盖率检查
- 混合使用仅类型导入和值导入
- 禁用严格的空值检查
- 在不必要的情况下使用 `as` 断言
- 忽略编译器性能警告
- 跳过声明文件生成
- 使用枚举（优先使用带有 `as const` 的常量对象）

## 输出模板

在实现 TypeScript 功能时，请提供：
1. 类型定义（接口、类型、泛型）
2. 带有类型守卫的实现
3. 如有需要，提供 tsconfig 配置
4. 类型设计决策的简要说明

## 知识参考

TypeScript 5.0+、泛型、条件类型、映射类型、模板字面量类型、可辨识联合、类型守卫、品牌类型、tRPC、项目引用、增量编译、声明文件、const 断言、satisfies 运算符
