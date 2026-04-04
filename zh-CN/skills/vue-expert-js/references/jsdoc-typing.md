# Vue 的 JSDoc 类型标注

---

## Vue 基本用法的 JSDoc

### 标注 Refs

```vue
<script setup>
import { ref, computed } from 'vue'

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {boolean} [isActive] - 可选属性
 */

/** @type {import('vue').Ref<User | null>} */
const user = ref(null)

/** @type {import('vue').Ref<User[]>} */
const users = ref([])

/** @type {import('vue').Ref<string>} */
const searchQuery = ref('')

/** @type {import('vue').Ref<number>} */
const count = ref(0)
</script>
```

### 标注 Computed

```vue
<script setup>
import { ref, computed } from 'vue'

/** @type {import('vue').Ref<User | null>} */
const user = ref(null)

/** @type {import('vue').ComputedRef<string>} */
const userName = computed(() => user.value?.name ?? 'Anonymous')

/** @type {import('vue').ComputedRef<boolean>} */
const isLoggedIn = computed(() => user.value !== null)

/** @type {import('vue').ComputedRef<User[]>} */
const activeUsers = computed(() =>
  users.value.filter(u => u.isActive)
)
</script>
```

### 标注 Reactive

```vue
<script setup>
import { reactive } from 'vue'

/**
 * @typedef {Object} FormState
 * @property {string} email
 * @property {string} password
 * @property {boolean} rememberMe
 * @property {string[]} errors
 */

/** @type {FormState} */
const form = reactive({
  email: '',
  password: '',
  rememberMe: false,
  errors: []
})
</script>
```

---

## 带 JSDoc 的 Props

### 基本 Props

```vue
<script setup>
/**
 * @typedef {Object} Props
 * @property {string} title - 卡片标题
 * @property {string} [subtitle] - 可选副标题
 * @property {number} [count=0] - 带默认值的计数器
 * @property {boolean} [disabled=false] - 禁用状态
 */

/** @type {Props} */
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  count: {
    type: Number,
    default: 0
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
</script>
```

### 复杂 Props

```vue
<script setup>
/**
 * @typedef {Object} MenuItem
 * @property {string} id
 * @property {string} label
 * @property {string} [icon]
 * @property {MenuItem[]} [children]
 */

/**
 * @typedef {'primary' | 'secondary' | 'danger'} ButtonVariant
 */

/**
 * @typedef {Object} Props
 * @property {MenuItem[]} items - 菜单项
 * @property {ButtonVariant} [variant='primary'] - 按钮样式
 * @property {(item: MenuItem) => void} [onSelect] - 选择回调
 */

const props = defineProps({
  items: {
    type: Array,
    required: true,
    /** @param {MenuItem[]} value */
    validator: (value) => value.every(item => item.id && item.label)
  },
  variant: {
    type: String,
    default: 'primary',
    /** @param {string} value */
    validator: (value) => ['primary', 'secondary', 'danger'].includes(value)
  },
  onSelect: {
    type: Function,
    default: null
  }
})
</script>
```

---

## 带 JSDoc 的 Emits

### 基本 Emits

```vue
<script setup>
/**
 * @typedef {Object} Emits
 * @property {(value: string) => void} update - 值更改时触发
 * @property {(id: number) => void} delete - 删除时触发
 * @property {() => void} close - 关闭时触发
 */

const emit = defineEmits(['update', 'delete', 'close'])

/**
 * 处理输入更改
 * @param {string} value - 新值
 */
function handleChange(value) {
  emit('update', value)
}

/**
 * 处理删除操作
 * @param {number} id - 要删除的项目 ID
 */
function handleDelete(id) {
  emit('delete', id)
}

function handleClose() {
  emit('close')
}
</script>
```

### 带验证

```vue
<script setup>
const emit = defineEmits({
  /**
   * @param {string} value
   * @returns {boolean}
   */
  update: (value) => typeof value === 'string',

  /**
   * @param {{ id: number, reason: string }} payload
   * @returns {boolean}
   */
  delete: (payload) => typeof payload.id === 'number'
})
</script>
```

---

## 带 JSDoc 的 Composables

### 基本 Composable

```javascript
// composables/useCounter.js
import { ref, computed } from 'vue'

/**
 * @typedef {Object} UseCounterReturn
 * @property {import('vue').Ref<number>} count - 当前计数
 * @property {import('vue').ComputedRef<number>} doubled - 双倍值
 * @property {() => void} increment - 增加计数
 * @property {() => void} decrement - 减少计数
 * @property {(value: number) => void} set - 将计数设置为值
 */

/**
 * 带有增加/减少功能的计数器 composable
 * @param {number} [initialValue=0] - 起始值
 * @returns {UseCounterReturn}
 */
export function useCounter(initialValue = 0) {
  /** @type {import('vue').Ref<number>} */
  const count = ref(initialValue)

  const doubled = computed(() => count.value * 2)

  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  /**
   * @param {number} value
   */
  function set(value) {
    count.value = value
  }

  return { count, doubled, increment, decrement, set }
}
```

### 异步 Composable

```javascript
// composables/useFetch.js
import { ref, watchEffect, toValue } from 'vue'

/**
 * @template T
 * @typedef {Object} UseFetchReturn
 * @property {import('vue').Ref<T | null>} data - 获取的数据
 * @property {import('vue').Ref<Error | null>} error - 错误（如果有）
 * @property {import('vue').Ref<boolean>} loading - 加载状态
 * @property {() => Promise<void>} refresh - 重新获取数据
 */

/**
 * 用于获取数据的 composable
 * @template T
 * @param {string | import('vue').Ref<string>} url - 要获取的 URL
 * @param {RequestInit} [options] - 获取选项
 * @returns {UseFetchReturn<T>}
 */
export function useFetch(url, options = {}) {
  /** @type {import('vue').Ref<T | null>} */
  const data = ref(null)

  /** @type {import('vue').Ref<Error | null>} */
  const error = ref(null)

  /** @type {import('vue').Ref<boolean>} */
  const loading = ref(false)

  async function refresh() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(toValue(url), options)
      if (!response.ok) {
        throw new Error(`HTTP 错误: ${response.status}`)
      }
      data.value = await response.json()
    } catch (e) {
      error.value = /** @type {Error} */ (e)
    } finally {
      loading.value = false
    }
  }

  watchEffect(() => {
    refresh()
  })

  return { data, error, loading, refresh }
}
```

### 带选项的 Composable

```javascript
// composables/useLocalStorage.js
import { ref, watch } from 'vue'

/**
 * @template T
 * @typedef {Object} UseLocalStorageOptions
 * @property {(value: T) => string} [serialize] - 自定义序列化器
 * @property {(value: string) => T} [deserialize] - 自定义反序列化器
 */

/**
 * 响应式 localStorage composable
 * @template T
 * @param {string} key - 存储键
 * @param {T} defaultValue - 如果未找到键时的默认值
 * @param {UseLocalStorageOptions<T>} [options] - 选项
 * @returns {import('vue').Ref<T>}
 */
export function useLocalStorage(key, defaultValue, options = {}) {
  const serialize = options.serialize ?? JSON.stringify
  const deserialize = options.deserialize ?? JSON.parse

  /** @type {import('vue').Ref<T>} */
  const data = ref(defaultValue)

  // 从存储加载
  const stored = localStorage.getItem(key)
  if (stored) {
    try {
      data.value = deserialize(stored)
    } catch {
      data.value = defaultValue
    }
  }

  // 更改时持久化
  watch(data, (value) => {
    localStorage.setItem(key, serialize(value))
  }, { deep: true })

  return data
}
```

---

## 类型导入和共享类型

### 共享类型定义

```javascript
// types.js - 共享类型定义
/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {UserRole} role
 */

/**
 * @typedef {'admin' | 'user' | 'guest'} UserRole
 */

/**
 * @typedef {Object} Post
 * @property {number} id
 * @property {string} title
 * @property {string} content
 * @property {User} author
 * @property {string} createdAt
 */

/**
 * @typedef {Object} PaginatedResponse
 * @template T
 * @property {T[]} data
 * @property {number} total
 * @property {number} page
 * @property {number} pageSize
 */

// 导出空对象以支持 IDE 导入
export const Types = {}
```

### 导入类型

```vue
<script setup>
/** @typedef {import('./types.js').User} User */
/** @typedef {import('./types.js').Post} Post */

import { ref } from 'vue'

/** @type {import('vue').Ref<User | null>} */
const currentUser = ref(null)

/** @type {import('vue').Ref<Post[]>} */
const posts = ref([])
</script>
```

### 全局类型定义

```javascript
// types/global.d.js（用于 IDE 支持）
/**
 * @typedef {Object} ApiResponse
 * @template T
 * @property {boolean} success
 * @property {T} [data]
 * @property {string} [error]
 */

/**
 * @typedef {Object} ValidationError
 * @property {string} field
 * @property {string} message
 */
```

---

## 带 JSDoc 的 Pinia Stores

```javascript
// stores/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** @typedef {import('../types.js').User} User */

/**
 * @typedef {Object} UserStoreState
 * @property {User | null} currentUser
 * @property {boolean} isLoading
 */

export const useUserStore = defineStore('user', () => {
  /** @type {import('vue').Ref<User | null>} */
  const currentUser = ref(null)

  /** @type {import('vue').Ref<boolean>} */
  const isLoading = ref(false)

  const isLoggedIn = computed(() => currentUser.value !== null)
  const userName = computed(() => currentUser.value?.name ?? 'Guest')

  /**
   * 登录用户
   * @param {string} email
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async function login(email, password) {
    isLoading.value = true
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      })
      const data = await response.json()
      currentUser.value = data.user
      return true
    } catch {
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    currentUser.value = null
  }

  return {
    currentUser,
    isLoading,
    isLoggedIn,
    userName,
    login,
    logout
  }
})
```

---

## 快速参考

| 模式 | 语法 | 使用场景 |
|---------|--------|----------|
| `@typedef` | `@typedef {Object} Name` | 定义对象形状 |
| `@property` | `@property {type} name` | 对象属性 |
| `@type` | `@type {Type}` | 注解变量 |
| `@param` | `@param {type} name` | 函数参数 |
| `@returns` | `@returns {type}` | 函数返回类型 |
| `@template` | `@template T` | 泛型类型 |
| 可选 | `{type} [name]` | 可选属性 |
| 默认 | `{type} [name=value]` | 带默认值 |
| 联合类型 | `{type1 | type2}` | 多种类型 |
| 导入 | `import('./file').Type` | 从文件导入 |
| Vue Ref | `import('vue').Ref<T>` | 类型化 ref |
| Vue Computed | `import('vue').ComputedRef<T>` | 类型化 computed |
