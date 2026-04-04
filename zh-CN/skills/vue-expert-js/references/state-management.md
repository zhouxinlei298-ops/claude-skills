# 状态管理

---

## 设置

```javascript
// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

createApp(App).use(createPinia()).mount('#app')
```

---

## Options Store 语法

```javascript
// stores/counter.js
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
    name: 'Counter'
  }),

  getters: {
    doubleCount: (state) => state.count * 2,
    // 带参数的 getter
    countPlusN: (state) => (n) => state.count + n
  },

  actions: {
    increment() {
      this.count++
    },
    /** @param {number} amount */
    incrementBy(amount) {
      this.count += amount
    }
  }
})
```

---

## Setup Store 语法（组合式 API）

```javascript
// stores/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

export const useUserStore = defineStore('user', () => {
  // State
  /** @type {import('vue').Ref<User | null>} */
  const currentUser = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const isLoggedIn = computed(() => currentUser.value !== null)
  const userName = computed(() => currentUser.value?.name ?? 'Guest')

  // Actions
  async function login(email, password) {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      currentUser.value = (await res.json()).user
      return true
    } catch (e) {
      error.value = e.message
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    currentUser.value = null
  }

  return { currentUser, isLoading, error, isLoggedIn, userName, login, logout }
})
```

---

## 使用 Stores

```vue
<script setup>
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const userStore = useUserStore()

// 使用 storeToRefs 获取响应式状态/getters
const { currentUser, isLoggedIn, isLoading } = storeToRefs(userStore)

// Actions 可以直接解构
const { login, logout } = userStore
</script>

<template>
  <div v-if="isLoading">加载中...</div>
  <div v-else-if="isLoggedIn">
    欢迎，{{ currentUser?.name }}
    <button @click="logout">登出</button>
  </div>
</template>
```

---

## Store 组合

```javascript
// stores/cart.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useProductsStore } from './products'
import { useUserStore } from './user'

export const useCartStore = defineStore('cart', () => {
  const items = ref([]) // [{ productId, quantity }]

  // 访问其他 stores
  const productsStore = useProductsStore()
  const userStore = useUserStore()

  const total = computed(() =>
    items.value.reduce((sum, item) => {
      const product = productsStore.items.find(p => p.id === item.productId)
      return sum + (product?.price ?? 0) * item.quantity
    }, 0)
  )

  function addItem(productId, quantity = 1) {
    const existing = items.value.find(i => i.productId === productId)
    if (existing) existing.quantity += quantity
    else items.value.push({ productId, quantity })
  }

  async function checkout() {
    if (!userStore.isLoggedIn) throw new Error('必须先登录')
    await fetch('/api/checkout', {
      method: 'POST',
      body: JSON.stringify({ userId: userStore.currentUser.id, items: items.value })
    })
    items.value = []
  }

  return { items, total, addItem, checkout }
})
```

---

## 持久化

```javascript
// stores/settings.js
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'app-settings'

function loadFromStorage() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? {}
  } catch {
    return {}
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadFromStorage()

  const theme = ref(saved.theme ?? 'light')
  const language = ref(saved.language ?? 'en')

  watch([theme, language], () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      theme: theme.value,
      language: language.value
    }))
  })

  return { theme, language }
})
```

---

## 测试 Stores

```javascript
// stores/__tests__/counter.test.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCounterStore } from '../counter'

describe('Counter Store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('increments count', () => {
    const store = useCounterStore()
    store.increment()
    expect(store.count).toBe(1)
  })

  it('computes double count', () => {
    const store = useCounterStore()
    store.count = 5
    expect(store.doubleCount).toBe(10)
  })
})
```

---

## 快速参考

| 功能 | Options 语法 | Setup 语法 |
|---------|---------------|--------------|
| State | `state: () => ({})` | `const x = ref()` |
| Getter | `getters: { x: (state) => }` | `const x = computed()` |
| Action | `actions: { fn() {} }` | `function fn() {}` |
| 在组件中使用 | `storeToRefs()` 用于状态 | 相同 |
| 重置状态 | `store.$reset()` | 手动重置函数 |
| 订阅 | `store.$subscribe((mutation, state) => {})` | 相同 |
| 其他 stores | 在 actions 中使用 | 在 setup 顶层调用 |
