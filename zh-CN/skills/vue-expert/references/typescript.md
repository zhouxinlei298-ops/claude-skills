# Vue 3 中的 TypeScript

## 组件 Props 类型定义

```vue
<script setup lang="ts">
// 基本接口
interface Props {
  title: string
  count: number
  items: string[]
  optional?: boolean
}

const props = defineProps<Props>()

// 带有默认值的 Props
const propsWithDefaults = withDefaults(defineProps<Props>(), {
  count: 0,
  items: () => [],
  optional: false
})

// 联合类型
interface PropsWithUnion {
  status: 'success' | 'error' | 'warning'
  size: 'sm' | 'md' | 'lg'
}

// 复杂类型
interface User {
  id: number
  name: string
  email: string
}

interface ComplexProps {
  user: User
  users: User[]
  callback: (id: number) => void
  config: Record<string, unknown>
}

const complexProps = defineProps<ComplexProps>()
</script>
```

## Emits 类型定义

```vue
<script setup lang="ts">
// 类型安全的 emits
interface Emits {
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
  (e: 'submit', payload: { name: string; email: string }): void
}

const emit = defineEmits<Emits>()

// 使用
function handleUpdate(value: string) {
  emit('update', value) // 类型安全
  // emit('update', 123) // 错误: number 不能赋值给 string
}

// 替代语法
type EmitsType = {
  update: [value: string]
  delete: [id: number]
  submit: [payload: { name: string; email: string }]
}

const emit2 = defineEmits<EmitsType>()
</script>
```

## Ref 类型定义

```vue
<script setup lang="ts">
import { ref, Ref } from 'vue'

// 类型推断
const count = ref(0) // Ref<number>
const message = ref('hello') // Ref<string>

// 显式类型定义
const user = ref<User | null>(null)
const items = ref<string[]>([])

// 复杂类型
interface FormData {
  username: string
  email: string
  age: number
}

const form = ref<FormData>({
  username: '',
  email: '',
  age: 0
})

// Ref 作为函数参数
function updateCount(countRef: Ref<number>) {
  countRef.value++
}

updateCount(count)
</script>
```

## Reactive 类型定义

```vue
<script setup lang="ts">
import { reactive } from 'vue'

interface State {
  count: number
  user: {
    name: string
    email: string
  }
  items: string[]
}

// 显式类型定义
const state = reactive<State>({
  count: 0,
  user: {
    name: '',
    email: ''
  },
  items: []
})

// 类型推断
const inferredState = reactive({
  count: 0, // number
  message: 'hello', // string
  active: true // boolean
})
</script>
```

## Computed 类型定义

```vue
<script setup lang="ts">
import { ref, computed, ComputedRef } from 'vue'

const count = ref(0)

// 类型推断
const doubled = computed(() => count.value * 2) // ComputedRef<number>

// 显式类型定义
const tripled = computed<number>(() => count.value * 3)

// 复杂计算属性
interface User {
  firstName: string
  lastName: string
}

const user = ref<User>({ firstName: 'John', lastName: 'Doe' })

const fullName = computed<string>(() => {
  return `${user.value.firstName} ${user.value.lastName}`
})

// 可写计算属性带类型定义
const fullNameWritable = computed<string>({
  get() {
    return `${user.value.firstName} ${user.value.lastName}`
  },
  set(value: string) {
    const [first, last] = value.split(' ')
    user.value.firstName = first
    user.value.lastName = last
  }
})
</script>
```

## 模板 Ref 类型定义

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

// HTML 元素 refs
const inputRef = ref<HTMLInputElement | null>(null)
const divRef = ref<HTMLDivElement | null>(null)

onMounted(() => {
  inputRef.value?.focus()
  if (divRef.value) {
    divRef.value.scrollTop = 100
  }
})

// 组件 refs
import ChildComponent from './ChildComponent.vue'

const childRef = ref<InstanceType<typeof ChildComponent> | null>(null)

onMounted(() => {
  childRef.value?.someMethod()
})
</script>

<template>
  <input ref="inputRef" />
  <div ref="divRef">内容</div>
  <ChildComponent ref="childRef" />
</template>
```

## Composables 类型定义

```typescript
// composables/useCounter.ts
import { ref, computed, Ref, ComputedRef } from 'vue'

interface UseCounterReturn {
  count: Ref<number>
  doubled: ComputedRef<number>
  increment: () => void
  decrement: () => void
  reset: () => void
}

export function useCounter(initialValue = 0): UseCounterReturn {
  const count = ref(initialValue)
  const doubled = computed(() => count.value * 2)

  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  function reset() {
    count.value = initialValue
  }

  return {
    count,
    doubled,
    increment,
    decrement,
    reset
  }
}

// composables/useFetch.ts
interface UseFetchOptions<T> {
  immediate?: boolean
  transform?: (data: unknown) => T
}

interface UseFetchReturn<T> {
  data: Ref<T | null>
  error: Ref<Error | null>
  loading: Ref<boolean>
  execute: () => Promise<void>
}

export function useFetch<T = unknown>(
  url: string,
  options: UseFetchOptions<T> = {}
): UseFetchReturn<T> {
  const data = ref<T | null>(null)
  const error = ref<Error | null>(null)
  const loading = ref(false)

  async function execute() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(url)
      const json = await response.json()
      data.value = options.transform ? options.transform(json) : json
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  if (options.immediate !== false) {
    execute()
  }

  return { data, error, loading, execute }
}

// 使用
<script setup lang="ts">
interface User {
  id: number
  name: string
}

const { data, error, loading } = useFetch<User>('/api/user')
</script>
```

## 泛型组件

```vue
<!-- GenericList.vue -->
<script setup lang="ts" generic="T extends { id: number }">
interface Props {
  items: T[]
  selected?: T
}

interface Emits {
  (e: 'select', item: T): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

function handleSelect(item: T) {
  emit('select', item)
}
</script>

<template>
  <div>
    <div
      v-for="item in items"
      :key="item.id"
      @click="handleSelect(item)"
    >
      <slot :item="item"></slot>
    </div>
  </div>
</template>

<!-- 使用 -->
<script setup lang="ts">
interface User {
  id: number
  name: string
  email: string
}

const users: User[] = [
  { id: 1, name: 'John', email: 'john@example.com' }
]

function handleUserSelect(user: User) {
  console.log('选中的用户:', user.name)
}
</script>

<template>
  <GenericList :items="users" @select="handleUserSelect">
    <template #default="{ item }">
      <div>{{ item.name }} - {{ item.email }}</div>
    </template>
  </GenericList>
</template>
```

## 事件处理程序类型定义

```vue
<script setup lang="ts">
// DOM 事件
function handleClick(event: MouseEvent) {
  console.log(event.clientX, event.clientY)
}

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  console.log(target.value)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    console.log('按下 Enter 键')
  }
}

// 来自子组件的自定义事件
interface CustomPayload {
  id: number
  value: string
}

function handleCustomEvent(payload: CustomPayload) {
  console.log(payload.id, payload.value)
}
</script>

<template>
  <button @click="handleClick">点击我</button>
  <input @input="handleInput" @keydown="handleKeydown" />
  <ChildComponent @custom="handleCustomEvent" />
</template>
```

## Provide/Inject 类型定义

```vue
<!-- Parent.vue -->
<script setup lang="ts">
import { provide, InjectionKey, Ref, ref } from 'vue'

interface UserContext {
  user: Ref<User>
  updateUser: (user: User) => void
}

// 创建类型化的注入键
export const userContextKey = Symbol() as InjectionKey<UserContext>

const user = ref<User>({ id: 1, name: 'John', email: 'john@example.com' })

function updateUser(newUser: User) {
  user.value = newUser
}

// 类型安全的 provide
provide(userContextKey, {
  user,
  updateUser
})
</script>

<!-- Child.vue -->
<script setup lang="ts">
import { inject } from 'vue'
import { userContextKey } from './Parent.vue'

// 类型安全的 inject
const userContext = inject(userContextKey)

// 带有默认值
const defaultContext: UserContext = {
  user: ref({ id: 0, name: '', email: '' }),
  updateUser: () => {}
}

const contextWithDefault = inject(userContextKey, defaultContext)

// 或者如果未提供则抛出错误
const requiredContext = inject(userContextKey)
if (!requiredContext) {
  throw new Error('未提供用户上下文')
}
</script>
```

## Store 类型定义（Pinia）

```typescript
// stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: number
  name: string
  email: string
  role: 'admin' | 'user'
}

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref<User | null>(null)
  const users = ref<User[]>([])

  // Getters
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userCount = computed(() => users.value.length)

  // 操作
  async function fetchUser(id: number): Promise<User> {
    const response = await fetch(`/api/users/${id}`)
    const data = await response.json()
    user.value = data
    return data
  }

  function logout() {
    user.value = null
  }

  return {
    user,
    users,
    isAdmin,
    userCount,
    fetchUser,
    logout
  }
})

// 类型化的 store 实例
export type UserStore = ReturnType<typeof useUserStore>
```

## 全局属性类型定义

```typescript
// plugins/api.ts
export default defineNuxtPlugin(() => {
  const api = {
    async get<T>(url: string): Promise<T> {
      const response = await fetch(url)
      return response.json()
    },
    async post<T>(url: string, data: unknown): Promise<T> {
      const response = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(data)
      })
      return response.json()
    }
  }

  return {
    provide: {
      api
    }
  }
})

// types/nuxt.d.ts - 增强类型
declare module '#app' {
  interface NuxtApp {
    $api: {
      get<T>(url: string): Promise<T>
      post<T>(url: string, data: unknown): Promise<T>
    }
  }
}

declare module 'vue' {
  interface ComponentCustomProperties {
    $api: {
      get<T>(url: string): Promise<T>
      post<T>(url: string, data: unknown): Promise<T>
    }
  }
}

// 使用
<script setup lang="ts">
interface User {
  id: number
  name: string
}

const { $api } = useNuxtApp()
const user = await $api.get<User>('/api/user')
</script>
```

## 快速参考

| 模式 | 类型 |
|---------|------|
| `defineProps<T>()` | Props 接口 |
| `defineEmits<T>()` | Emits 接口 |
| `ref<T>()` | 类型化的 ref |
| `reactive<T>()` | 类型化的 reactive 对象 |
| `computed<T>()` | 类型化的 computed |
| `ref<HTMLElement \| null>` | 模板 refs |
| `generic="T"` | 泛型组件 |
| `InjectionKey<T>` | 类型化的 provide/inject |
| 类型守卫 | 运行时类型检查 |
| `as` 断言 | 类型断言 |
