# Composition API

## Script Setup 语法

```vue
<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'

// 自动组件注册 - 无需在 components 选项中注册
import UserCard from './UserCard.vue'

// TypeScript Props
interface Props {
  userId: number
  optional?: string
}
const props = withDefaults(defineProps<Props>(), {
  optional: 'default value'
})

// TypeScript Emits
interface Emits {
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
}
const emit = defineEmits<Emits>()

// 响应式状态
const count = ref(0)
const user = reactive({
  name: 'John',
  age: 30
})

// 计算属性
const doubled = computed(() => count.value * 2)

// 方法
function increment() {
  count.value++
  emit('update', count.value.toString())
}

// 生命周期
onMounted(() => {
  console.log('Component mounted')
})
</script>
```

## Ref 与 Reactive

```typescript
import { ref, reactive, toRefs } from 'vue'

// 原始值使用 ref()
const count = ref(0)
const message = ref('hello')
const isActive = ref(true)

// 使用 .value 访问/修改
count.value++
console.log(message.value)

// 对象使用 reactive()
const state = reactive({
  count: 0,
  user: {
    name: 'John',
    email: 'john@example.com'
  }
})

// reactive 不需要 .value
state.count++
state.user.name = 'Jane'

// 将 reactive 转换为 refs 以便解构
const { count: refCount, user } = toRefs(state)
// 现在 refCount.value 可以使用
```

## 计算属性

```typescript
import { ref, computed } from 'vue'

const firstName = ref('John')
const lastName = ref('Doe')

// 只读计算属性
const fullName = computed(() => {
  return `${firstName.value} ${lastName.value}`
})

// 可写计算属性
const fullNameWritable = computed({
  get() {
    return `${firstName.value} ${lastName.value}`
  },
  set(value: string) {
    const [first, last] = value.split(' ')
    firstName.value = first
    lastName.value = last
  }
})

// 带复杂逻辑的计算属性（缓存直到依赖变化）
const filteredItems = computed(() => {
  return items.value.filter(item =>
    item.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})
```

## 侦听器

```typescript
import { ref, watch, watchEffect } from 'vue'

const count = ref(0)
const user = ref({ name: 'John', age: 30 })

// 侦听单个源
watch(count, (newValue, oldValue) => {
  console.log(`Count changed from ${oldValue} to ${newValue}`)
})

// 侦听多个源
watch([count, user], ([newCount, newUser], [oldCount, oldUser]) => {
  console.log('Count or user changed')
})

// 带选项的侦听
watch(
  () => user.value.name, // Getter 函数
  (newName) => {
    console.log(`Name changed to ${newName}`)
  },
  {
    immediate: true, // 立即运行
    deep: true // 深度侦听对象
  }
)

// watchEffect - 自动追踪依赖
watchEffect(() => {
  console.log(`Count is ${count.value}`)
  // 当 count 变化时自动重新运行
})

// 清理和停止侦听
const stop = watchEffect((onCleanup) => {
  const timer = setInterval(() => console.log('tick'), 1000)

  onCleanup(() => {
    clearInterval(timer)
  })
})

// 需要时停止侦听
stop()
```

## 生命周期钩子

```typescript
import {
  onBeforeMount,
  onMounted,
  onBeforeUpdate,
  onUpdated,
  onBeforeUnmount,
  onUnmounted,
  onErrorCaptured
} from 'vue'

// 组件挂载前
onBeforeMount(() => {
  console.log('Before mount')
})

// 组件挂载后（DOM 已就绪）
onMounted(() => {
  console.log('Mounted - DOM is ready')
  // 获取数据、设置事件监听器等
})

// 组件更新前
onBeforeUpdate(() => {
  console.log('Before update')
})

// 组件更新后
onUpdated(() => {
  console.log('Updated')
})

// 组件卸载前
onBeforeUnmount(() => {
  console.log('Before unmount - cleanup here')
})

// 组件卸载后
onUnmounted(() => {
  console.log('Unmounted')
  // 清理：移除事件监听器、取消定时器等
})

// 错误处理
onErrorCaptured((err, instance, info) => {
  console.error('Error captured:', err, info)
  return false // 阻止错误传播
})
```

## Composables 模式

```typescript
// composables/useCounter.ts
import { ref, computed } from 'vue'

export function useCounter(initialValue = 0) {
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

// 在组件中使用
<script setup lang="ts">
import { useCounter } from './composables/useCounter'

const { count, doubled, increment, decrement } = useCounter(10)
</script>
```

## 带清理的高级 Composable

```typescript
// composables/useEventListener.ts
import { onMounted, onUnmounted } from 'vue'

export function useEventListener(
  target: EventTarget,
  event: string,
  handler: EventListener
) {
  onMounted(() => {
    target.addEventListener(event, handler)
  })

  onUnmounted(() => {
    target.removeEventListener(event, handler)
  })
}

// 使用
<script setup lang="ts">
import { useEventListener } from './composables/useEventListener'

function handleClick(e: MouseEvent) {
  console.log('Clicked at:', e.clientX, e.clientY)
}

useEventListener(window, 'click', handleClick)
</script>
```

## 快速参考

| 模式 | 使用场景 |
|---------|----------|
| `ref()` | 原始值（string、number、boolean） |
| `reactive()` | 对象和数组 |
| `computed()` | 派生状态（缓存） |
| `watch()` | 特定变化的副作用 |
| `watchEffect()` | 自动追踪的副作用 |
| `onMounted()` | 依赖 DOM 的操作 |
| `onUnmounted()` | 清理（定时器、监听器） |
| Composables | 可复用的有状态逻辑 |
