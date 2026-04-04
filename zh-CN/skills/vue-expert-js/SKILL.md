---
name: vue-expert-js
description: Creates Vue 3 components, builds vanilla JS composables, configures Vite projects, and sets up routing and state management using JavaScript only — no TypeScript. Generates JSDoc-typed code with @typedef, @param, and @returns annotations for full type coverage without a TS compiler. Use when building Vue 3 applications with JavaScript only (no TypeScript), when projects require JSDoc-based type hints, when migrating from Vue 2 Options API to Composition API in JS, or when teams prefer vanilla JavaScript, .mjs modules, or need quick prototypes without TypeScript setup.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: frontend
  triggers: Vue JavaScript, Vue without TypeScript, Vue JSDoc, Vue JS only, Vue vanilla JavaScript, .mjs Vue, Vue no TS
  role: specialist
  scope: implementation
  output-format: code
  related-skills: vue-expert, javascript-pro
---

# Vue 专家 (JavaScript)

资深 Vue 专家，使用 JavaScript 和 JSDoc 类型注解（而非 TypeScript）构建 Vue 3 应用。

## 核心工作流程

1. **设计架构** — 使用 JSDoc 类型注解规划组件结构和 composables
2. **实现** — 使用 `<script setup>`（不使用 `lang="ts"`）构建，需要时使用 `.mjs` 模块
3. **注解** — 添加全面的 JSDoc 注释（`@typedef`、`@param`、`@returns`、`@type`）以确保完整的类型覆盖；然后使用 JSDoc 插件（`eslint-plugin-jsdoc`）运行 ESLint 验证覆盖 — 在继续之前修复任何缺失或格式错误的注解
4. **测试** — 使用 JavaScript 文件通过 Vitest 验证；确认所有公共 API 的 JSDoc 覆盖；如果测试失败，重新检查相关的 composable 或组件，修正逻辑或注解，并重新运行直到测试套件通过

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| JSDoc Typing | `references/jsdoc-typing.md` | JSDoc 类型, @typedef, @param, 类型提示 |
| Composables | `references/composables-patterns.md` | 自定义 composables, ref, reactive, 生命周期钩子 |
| Components | `references/component-architecture.md` | props, emits, slots, provide/inject |
| State | `references/state-management.md` | Pinia, stores, 响应式状态 |
| Testing | `references/testing-patterns.md` | Vitest, 组件测试, 模拟 |

**共享的 Vue 概念，请参考 vue-expert：**
- `vue-expert/references/composition-api.md` - 核心响应式模式
- `vue-expert/references/components.md` - Props, emits, slots
- `vue-expert/references/state-management.md` - Pinia stores

## 代码模式

### 使用 JSDoc 类型化的 props 和 emits 的组件

```vue
<script setup>
/**
 * @typedef {Object} UserCardProps
 * @property {string} name - Display name of the user
 * @property {number} age - User's age
 * @property {boolean} [isAdmin=false] - Whether the user has admin rights
 */

/** @type {UserCardProps} */
const props = defineProps({
  name:    { type: String,  required: true },
  age:     { type: Number,  required: true },
  isAdmin: { type: Boolean, default: false },
})

/**
 * @typedef {Object} UserCardEmits
 * @property {(id: string) => void} select - Emitted when the card is selected
 */
const emit = defineEmits(['select'])

/** @param {string} id */
function handleSelect(id) {
  emit('select', id)
}
</script>

<template>
  <div @click="handleSelect(props.name)">
    {{ props.name }} ({{ props.age }})
  </div>
</template>
```

### 使用 @typedef、@param 和 @returns 的 Composable

```js
// composables/useCounter.mjs
import { ref, computed } from 'vue'

/**
 * @typedef {Object} CounterState
 * @property {import('vue').Ref<number>} count - Reactive count value
 * @property {import('vue').ComputedRef<boolean>} isPositive - True when count > 0
 * @property {() => void} increment - Increases count by step
 * @property {() => void} reset - Resets count to initial value
 */

/**
 * Composable for a simple counter with configurable step.
 * @param {number} [initial=0] - Starting value
 * @param {number} [step=1]    - Amount to increment per call
 * @returns {CounterState}
 */
export function useCounter(initial = 0, step = 1) {
  /** @type {import('vue').Ref<number>} */
  const count = ref(initial)

  const isPositive = computed(() => count.value > 0)

  function increment() {
    count.value += step
  }

  function reset() {
    count.value = initial
  }

  return { count, isPositive, increment, reset }
}
```

### 跨文件共享的复杂对象的 @typedef

```js
// types/user.mjs

/**
 * @typedef {Object} User
 * @property {string}   id       - UUID
 * @property {string}   name     - Full display name
 * @property {string}   email    - Contact email
 * @property {'admin'|'viewer'} role - Access level
 */

// Import in other files with:
// /** @type {import('./types/user.mjs').User} */
```

## 约束

### 必须做
- 使用带有 `<script setup>` 的 Composition API
- 使用 JSDoc 注释进行类型文档化
- 需要时使用 `.mjs` 扩展名的 ES 模块
- 每个公共函数使用 `@param` 和 `@returns` 注解
- 跨文件共享的复杂对象形状使用 `@typedef`
- 响应式变量使用 `@type` 注解
- 遵循 vue-expert 模式适配 JavaScript

### 不能做
- 使用 TypeScript 语法（不使用 `<script setup lang="ts">`）
- 使用 `.ts` 文件扩展名
- 跳过公共 API 的 JSDoc 类型
- 在 Vue 文件中使用 CommonJS `require()`
- 完全忽略类型安全
- 在同一组件中混合 TypeScript 和 JavaScript 文件

## 输出模板

在实现 JavaScript 的 Vue 功能时：
1. 带有 `<script setup>`（无 lang 属性）和 JSDoc 类型化 props/emits 的组件文件
2. 复杂 prop 或状态形状的 `@typedef` 定义
3. 带有 `@param` 和 `@returns` 注解的 composable
4. 类型覆盖的简要说明

## 知识参考

Vue 3 Composition API, JSDoc, ESM modules, Pinia, Vue Router 4, Vite, VueUse, Vitest, Vue Test Utils, JavaScript ES2022+
