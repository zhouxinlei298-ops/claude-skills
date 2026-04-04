# Pinia 状态管理

## 基本 Store 设置

```typescript
// stores/counter.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Setup Stores（组合式 API 风格）- 推荐
export const useCounterStore = defineStore('counter', () => {
  // 状态
  const count = ref(0)
  const name = ref('Counter')

  // Getters（计算属性）
  const doubleCount = computed(() => count.value * 2)
  const isEven = computed(() => count.value % 2 === 0)

  // 操作
  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  function reset() {
    count.value = 0
  }

  async function incrementAsync() {
    await new Promise(resolve => setTimeout(resolve, 1000))
    count.value++
  }

  return {
    // 状态
    count,
    name,
    // Getters
    doubleCount,
    isEven,
    // 操作
    increment,
    decrement,
    reset,
    incrementAsync
  }
})

// 在组件中使用
<script setup lang="ts">
import { useCounterStore } from '@/stores/counter'
import { storeToRefs } from 'pinia'

const counter = useCounterStore()

// 使用 storeToRefs 在解构时保持响应式
const { count, doubleCount, isEven } = storeToRefs(counter)

// 操作可以直接解构（不需要 refs）
const { increment, decrement } = counter
</script>

<template>
  <div>
    <p>计数: {{ count }}</p>
    <p>双倍: {{ doubleCount }}</p>
    <p>是偶数: {{ isEven }}</p>
    <button @click="increment">+</button>
    <button @click="decrement">-</button>
  </div>
</template>
```

## Options Store（替代风格）

```typescript
// stores/user.ts
import { defineStore } from 'pinia'

interface User {
  id: number
  name: string
  email: string
}

interface UserState {
  user: User | null
  users: User[]
  loading: boolean
}

export const useUserStore = defineStore('user', {
  // 状态
  state: (): UserState => ({
    user: null,
    users: [],
    loading: false
  }),

  // Getters
  getters: {
    isLoggedIn: (state) => state.user !== null,
    userCount: (state) => state.users.length,

    // 带参数的 getter
    getUserById: (state) => {
      return (userId: number) => state.users.find(u => u.id === userId)
    },

    // 访问其他 getters 的 getter
    activeUserCount(): number {
      return this.users.filter(u => u.isActive).length
    }
  },

  // 操作
  actions: {
    async fetchUsers() {
      this.loading = true
      try {
        const response = await fetch('/api/users')
        this.users = await response.json()
      } catch (error) {
        console.error('获取用户失败:', error)
      } finally {
        this.loading = false
      }
    },

    async login(email: string, password: string) {
      this.loading = true
      try {
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
        this.user = await response.json()
      } catch (error) {
        console.error('登录失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.user = null
    },

    // 调用另一个操作
    async refreshUserData() {
      if (this.user) {
        await this.fetchUsers()
      }
    }
  }
})
```

## 带有 TypeScript 的 Store

```typescript
// stores/todos.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Todo {
  id: number
  title: string
  completed: boolean
  createdAt: Date
}

type TodoFilter = 'all' | 'active' | 'completed'

export const useTodoStore = defineStore('todos', () => {
  // 状态
  const todos = ref<Todo[]>([])
  const filter = ref<TodoFilter>('all')
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const filteredTodos = computed(() => {
    switch (filter.value) {
      case 'active':
        return todos.value.filter(t => !t.completed)
      case 'completed':
        return todos.value.filter(t => t.completed)
      default:
        return todos.value
    }
  })

  const completedCount = computed(() =>
    todos.value.filter(t => t.completed).length
  )

  const activeCount = computed(() =>
    todos.value.filter(t => !t.completed).length
  )

  // 操作
  async function fetchTodos() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/todos')
      if (!response.ok) throw new Error('获取待办事项失败')
      todos.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '未知错误'
    } finally {
      loading.value = false
    }
  }

  function addTodo(title: string) {
    const newTodo: Todo = {
      id: Date.now(),
      title,
      completed: false,
      createdAt: new Date()
    }
    todos.value.push(newTodo)
  }

  function toggleTodo(id: number) {
    const todo = todos.value.find(t => t.id === id)
    if (todo) {
      todo.completed = !todo.completed
    }
  }

  function deleteTodo(id: number) {
    const index = todos.value.findIndex(t => t.id === id)
    if (index > -1) {
      todos.value.splice(index, 1)
    }
  }

  function setFilter(newFilter: TodoFilter) {
    filter.value = newFilter
  }

  function clearCompleted() {
    todos.value = todos.value.filter(t => !t.completed)
  }

  return {
    // 状态
    todos,
    filter,
    loading,
    error,
    // Getters
    filteredTodos,
    completedCount,
    activeCount,
    // 操作
    fetchTodos,
    addTodo,
    toggleTodo,
    deleteTodo,
    setFilter,
    clearCompleted
  }
})
```

## 访问其他 Stores

```typescript
// stores/cart.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUserStore } from './user'
import { useProductStore } from './product'

interface CartItem {
  productId: number
  quantity: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])

  const userStore = useUserStore()
  const productStore = useProductStore()

  const total = computed(() => {
    return items.value.reduce((sum, item) => {
      const product = productStore.getProductById(item.productId)
      return sum + (product?.price || 0) * item.quantity
    }, 0)
  })

  function addItem(productId: number, quantity = 1) {
    const existingItem = items.value.find(i => i.productId === productId)
    if (existingItem) {
      existingItem.quantity += quantity
    } else {
      items.value.push({ productId, quantity })
    }
  }

  async function checkout() {
    if (!userStore.isLoggedIn) {
      throw new Error('用户必须登录才能结账')
    }

    // 结账逻辑
    const order = {
      userId: userStore.user?.id,
      items: items.value,
      total: total.value
    }

    // 发起 API 调用
    await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order)
    })

    items.value = []
  }

  return { items, total, addItem, checkout }
})
```

## Store 插件

```typescript
// plugins/pinia-logger.ts
import { PiniaPluginContext } from 'pinia'

export function piniaLogger({ store }: PiniaPluginContext) {
  store.$subscribe((mutation, state) => {
    console.log(`[${store.$id}]:`, mutation.type, mutation.payload)
    console.log('新状态:', state)
  })
}

// main.ts
import { createPinia } from 'pinia'
import { piniaLogger } from './plugins/pinia-logger'

const pinia = createPinia()
pinia.use(piniaLogger)

app.use(pinia)
```

## 持久化插件

```typescript
// 安装: npm install pinia-plugin-persistedstate

// main.ts
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// stores/settings.ts
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark'>('light')
  const language = ref('en')

  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
  }

  return { theme, language, setTheme }
}, {
  persist: true // 自动持久化到 localStorage
})

// 高级持久化
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)

  return { token, user }
}, {
  persist: {
    key: 'auth-storage',
    storage: sessionStorage,
    paths: ['token'] // 仅持久化 token，不持久化 user
  }
})
```

## Store 测试

```typescript
// stores/__tests__/counter.spec.ts
import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useCounterStore } from '../counter'

describe('Counter Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('增加计数', () => {
    const counter = useCounterStore()
    expect(counter.count).toBe(0)
    counter.increment()
    expect(counter.count).toBe(1)
  })

  it('双倍计数', () => {
    const counter = useCounterStore()
    counter.count = 5
    expect(counter.doubleCount).toBe(10)
  })

  it('重置计数', () => {
    const counter = useCounterStore()
    counter.count = 10
    counter.reset()
    expect(counter.count).toBe(0)
  })
})
```

## 快速参考

| 模式 | 使用场景 |
|---------|----------|
| Setup stores | 组合式 API 风格（推荐） |
| Options stores | 传统的 Vuex 风格语法 |
| `storeToRefs()` | 在解构时保持响应式 |
| `store.$subscribe()` | 监听状态变化 |
| `store.$patch()` | 批量更新状态 |
| `store.$reset()` | 重置状态到初始值 |
| 插件 | 添加全局功能（日志、持久化） |
| 访问 stores | 在操作中使用其他 stores |
| 测试 | 使用 `setActivePinia()` 进行隔离测试 |
