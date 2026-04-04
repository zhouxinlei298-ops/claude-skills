# 组件架构

---

## Props

```vue
<script setup>
/**
 * @typedef {Object} Props
 * @property {string} title - 必需
 * @property {string} [subtitle] - 可选
 * @property {number} [count=0] - 带默认值
 */

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  count: { type: Number, default: 0 },
  // 复杂类型
  items: { type: Array, default: () => [] },
  user: { type: Object, required: true },
  // 验证器
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium', 'large'].includes(v)
  }
})
</script>
```

---

## Emits

```vue
<script setup>
const emit = defineEmits(['update', 'delete', 'close'])

// 带验证
const emit = defineEmits({
  /** @param {string} value */
  update: (value) => typeof value === 'string',
  /** @param {{ id: number }} payload */
  delete: (payload) => typeof payload?.id === 'number',
  close: null
})

// 使用
emit('update', 'new value')
emit('delete', { id: 1 })
</script>
```

---

## v-model

```vue
<!-- 单个 v-model -->
<script setup>
const props = defineProps({ modelValue: { type: String, required: true } })
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <input :value="modelValue" @input="emit('update:modelValue', $event.target.value)" />
</template>
```

```vue
<!-- 多个 v-model: v-model:firstName, v-model:lastName -->
<script setup>
defineProps({ firstName: String, lastName: String })
defineEmits(['update:firstName', 'update:lastName'])
</script>
```

---

## Slots

```vue
<!-- Card.vue -->
<template>
  <div class="card">
    <header v-if="$slots.header"><slot name="header" /></header>
    <div class="card-body"><slot /></div>
    <footer v-if="$slots.footer"><slot name="footer" /></footer>
  </div>
</template>
```

```vue
<!-- 作用域 slot -->
<template>
  <ul>
    <li v-for="(item, index) in items" :key="item.id">
      <slot name="item" :item="item" :index="index">
        {{ item.name }}
      </slot>
    </li>
  </ul>
</template>

<!-- 使用 -->
<DataList :items="users">
  <template #item="{ item, index }">
    {{ index + 1 }}. {{ item.name }}
  </template>
</DataList>
```

---

## Provide / Inject

```vue
<!-- Provider.vue -->
<script setup>
import { provide, ref, readonly } from 'vue'

const theme = ref('light')
provide('theme', readonly(theme))
provide('setTheme', (t) => { theme.value = t })
</script>
```

```vue
<!-- Consumer.vue -->
<script setup>
import { inject, ref } from 'vue'

const theme = inject('theme', ref('light'))
const setTheme = inject('setTheme', () => {})
</script>
```

```javascript
// Composable 模式
// composables/useTheme.js
import { ref, provide, inject, readonly, computed } from 'vue'

const ThemeSymbol = Symbol('theme')

export function provideTheme(initial = 'light') {
  const theme = ref(initial)
  const isDark = computed(() => theme.value === 'dark')
  const toggle = () => { theme.value = theme.value === 'light' ? 'dark' : 'light' }

  provide(ThemeSymbol, { theme: readonly(theme), isDark, toggle })
  return { theme, isDark, toggle }
}

export function useTheme() {
  const ctx = inject(ThemeSymbol)
  if (!ctx) throw new Error('useTheme 需要 ThemeProvider')
  return ctx
}
```

---

## 动态组件

```vue
<script setup>
import { shallowRef, markRaw } from 'vue'
import TabHome from './TabHome.vue'
import TabProfile from './TabProfile.vue'

const tabs = [
  { name: 'Home', component: markRaw(TabHome) },
  { name: 'Profile', component: markRaw(TabProfile) }
]

const currentTab = shallowRef(tabs[0].component)
</script>

<template>
  <button v-for="tab in tabs" :key="tab.name" @click="currentTab = tab.component">
    {{ tab.name }}
  </button>
  <KeepAlive>
    <component :is="currentTab" />
  </KeepAlive>
</template>
```

```javascript
// 异步组件
import { defineAsyncComponent } from 'vue'

const AsyncModal = defineAsyncComponent({
  loader: () => import('./Modal.vue'),
  delay: 200,
  timeout: 10000
})
```

---

## 快速参考

| 功能 | 语法 |
|---------|--------|
| 必需 prop | `{ type: String, required: true }` |
| 默认 prop | `{ type: Number, default: 0 }` |
| 数组/对象默认 | `{ type: Array, default: () => [] }` |
| 触发事件 | `emit('eventName', payload)` |
| v-model | `modelValue` prop + `update:modelValue` emit |
| 命名 v-model | `v-model:name` → `name` prop + `update:name` emit |
| 默认 slot | `<slot />` |
| 命名 slot | `<slot name="header" />` → `#header` |
| 作用域 slot | `<slot :item="item" />` → `#default="{ item }"` |
| 提供 | `provide('key', value)` |
| 注入 | `inject('key', defaultValue)` |
| 动态组件 | `<component :is="comp" />` |
