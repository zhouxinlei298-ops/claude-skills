# ESLint 与代码规范

## Airbnb JavaScript Style Guide 关键约束

本项目遵循 Airbnb JavaScript Style Guide，以下是必须注意的约束：

### 禁止使用 Dangling Underscores

**错误示例**：
```javascript
// ❌ 禁止：变量名以单个或多个下划线开头
const _privateVar = 'something'
const __privateVar = 'something'
const _internalMethod = () => {}

// ❌ 禁止：属性名以单个或多个下划线开头
obj.__proto__
obj.__isWrapped
component.__name
```

**正确示例**：
```javascript
// ✅ 使用普通命名
const privateVar = 'something'
const isWrapped = true
const componentName = 'EditForm'

// ✅ 使用 Symbol 表示真正的私有属性
const PRIVATE_KEY = Symbol('private')
obj[PRIVATE_KEY] = 'value'
```

**例外情况**：以下划线开头和结尾的标识符是允许的（用于表示特殊约定）：
```javascript
// ✅ 允许：双下划线包裹（表示特殊约定）
const __dirname__ = path
const __filename__ = file
```

### 禁止使用 `++` 和 `--` 运算符

**错误示例**：
```javascript
// ❌ 禁止
i++
count--
++index
```

**正确示例**：
```javascript
// ✅ 使用 += 和 -=
i += 1
count -= 1
index += 1
```

### 禁止使用 `console`（生产环境）

```javascript
// ❌ 生产环境禁止
console.log('debug')
console.warn('warning')
console.error('error')

// ✅ 开发环境允许，生产环境禁止
// ESLint 配置：'no-console': process.env.NODE_ENV === 'production' ? ['error', { allow: ['warn', 'error'] }] : 'off'
```

## 项目特定 ESLint 规则

```javascript
// .eslintrc.js
{
  rules: {
    // 允许 @ts-ignore 注释
    '@typescript-eslint/ban-ts-comment': 0,

    // 未使用变量允许以 _ 开头
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' }],

    // 禁止 dangling underscores
    'no-underscore-dangle': ['error', { allowAfterThis: false }],

    // 禁止 ++ 和 --
    'no-plusplus': ['error', { allowForLoopAfterthoughts: false }],

    // 环境相关的 console 规则
    'no-console': process.env.NODE_ENV === 'production' ? ['error', { allow: ['warn', 'error'] }] : 'off',
  }
}
```

## 代码风格最佳实践

### 变量命名

```javascript
// ✅ 使用 camelCase
const userName = 'John'
const isActive = true
const getMaxValue = (a, b) => Math.max(a, b)

// ✅ 常量使用 UPPER_SNAKE_CASE
const MAX_RETRY_COUNT = 3
const API_BASE_URL = 'https://api.example.com'

// ✅ 组件名使用 PascalCase
const UserProfile = () => {}
class UserService {}

// ✅ 私有属性使用 #（ES2022）
class MyClass {
  #privateField = 'private'
  #privateMethod() {}
}
```

### 条件判断

```javascript
// ✅ 使用三元运算符代替简单 if-else
const value = condition ? 'yes' : 'no'

// ✅ 使用逻辑或提供默认值
const value = input ?? 'default'

// ❌ 避免嵌套三元运算符
const value = condition1 ? (condition2 ? 'a' : 'b') : 'c'

// ✅ 复杂逻辑使用 if-else
let value
if (condition1) {
  if (condition2) {
    value = 'a'
  } else {
    value = 'b'
  }
} else {
  value = 'c'
}
```

### 函数定义

```javascript
// ✅ 使用函数声明（命名函数）
function fetchData() {
  return fetch('/api/data')
}

// ✅ 使用箭头函数（回调、简单逻辑）
const fetchData = () => fetch('/api/data')

// ✅ 复杂参数使用对象解构
function createUser({ name, email, role = 'user' }) {
  return { name, email, role }
}

// ❌ 避免多个布尔参数
function createUser(name, email, isAdmin, isActive, isVerified) {}
```

## Vue 3 特定规范

### 组件定义

```vue
<script setup lang="ts">
// ✅ Props 使用 interface 定义
interface Props {
  title: string
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0
})

// ✅ Emits 使用 interface 定义
interface Emits {
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
}

const emit = defineEmits<Emits>()
</script>
```

### 响应式数据

```vue
<script setup lang="ts">
import { ref, reactive } from 'vue'

// ✅ 基本类型使用 ref
const count = ref(0)
const message = ref('hello')

// ✅ 对象类型使用 reactive
const state = reactive({
  count: 0,
  message: 'hello'
})

// ✅ 需要重新赋值时使用 ref
const user = ref<User | null>(null)

function fetchUser() {
  user.value = await api.getUser() // ✅ 可以重新赋值
}

// ❌ 避免 reactive 重新赋值
const state = reactive({ count: 0 })
state = { count: 1 } // ❌ 错误：不能直接替换 reactive 对象
```

### 组件命名

```vue
<!-- ✅ 组件文件名使用 PascalCase 或 kebab-case -->
<!-- UserProfile.vue 或 user-profile.vue -->

<!-- ✅ 组件名使用多单词 -->
<template>
  <UserProfile /> <!-- ✅ -->
  <UserList /> <!-- ✅ -->
</template>

<!-- ❌ 避免单单词组件名（HTML 标签冲突） -->
<template>
  <List /> <!-- ❌ 与 <ul> 混淆 -->
  <Form /> <!-- ❌ 与 <form> 混淆 -->
</template>
```

## TypeScript 特定规范

### 类型定义

```typescript
// ✅ 优先使用 interface
interface User {
  id: number
  name: string
  email: string
}

// ✅ 联合类型使用 type
type Status = 'success' | 'error' | 'pending'
type ID = string | number

// ✅ 工具类型
type PartialUser = Partial<User>
type UserKeys = keyof User
type UserValues = User[keyof User]
```

### 类型注解

```typescript
// ✅ 函数返回类型显式声明
function getUser(id: number): User {
  return api.getUser(id)
}

// ✅ 异步函数返回 Promise
async function getUser(id: number): Promise<User> {
  return await api.getUser(id)
}

// ❌ 避免使用 any
const data: any = fetchData()

// ✅ 使用 unknown 代替 any
const data: unknown = fetchData()
if (isUser(data)) {
  console.log(data.name) // 类型守卫后安全访问
}
```

## 快速参考

| 规则 | 说明 |
|------|------|
| `no-underscore-dangle` | 禁止变量/属性名以 `_` 开头 |
| `no-plusplus` | 禁止 `++` 和 `--` 运算符 |
| `no-console` | 生产环境禁止 console |
| `@typescript-eslint/ban-ts-comment` | 项目允许 `@ts-ignore` |
| `@typescript-eslint/no-unused-vars` | 未使用变量允许 `_` 前缀 |
