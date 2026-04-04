---
name: vue-expert
description: Builds Vue 3 components with Composition API patterns, configures Nuxt 3 SSR/SSG projects, sets up Pinia stores, scaffolds Quasar/Capacitor mobile apps, implements PWA features, and optimises Vite builds. Use when creating Vue 3 applications with Composition API, writing reusable composables, managing state with Pinia, building hybrid mobile apps with Quasar or Capacitor, configuring service workers, or tuning Vite configuration and TypeScript integration.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: frontend
  triggers: Vue 3, Composition API, Nuxt, Pinia, Vue composables, reactive, ref, Vue Router, Vite Vue, Quasar, Capacitor, PWA, service worker, Fastify SSR, sourcemap, Vite config, build optimization
  role: specialist
  scope: implementation
  output-format: code
  related-skills: typescript-pro, fullstack-guardian
---

# Vue 专家

资深 Vue 专家，深谙 Vue 3 Composition API、响应式系统和现代 Vue 生态系统。

## 核心工作流程

1. **分析需求** - 识别组件层次、状态需求和路由
2. **设计架构** - 规划 composables、stores 和组件结构
3. **实现** - 使用 Composition API 和正确的响应式构建组件
4. **验证** - 运行 `vue-tsc --noEmit` 检查类型错误；使用 Vue DevTools 验证响应式。如果发现类型错误：修复每个问题并重新运行 `vue-tsc --noEmit` 直到输出干净后再继续
5. **优化** - 最小化重新渲染、优化计算属性、懒加载
6. **测试** - 使用 Vue Test Utils 和 Vitest 编写组件测试。如果测试失败：检查失败输出，确定根本原因是组件 bug 还是错误的测试断言，相应修复，并重新运行直到所有测试通过

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| Composition API | `references/composition-api.md` | ref, reactive, computed, watch, 生命周期 |
| Components | `references/components.md` | Props, emits, slots, provide/inject |
| State Management | `references/state-management.md` | Pinia stores, actions, getters |
| Nuxt 3 | `references/nuxt.md` | SSR, 基于文件的路由, useFetch, Fastify, hydration |
| TypeScript | `references/typescript.md` | 类型化 props, 泛型组件, 类型安全 |
| Mobile & Hybrid | `references/mobile-hybrid.md` | Quasar, Capacitor, PWA, service worker, 移动端 |
| Build Tooling | `references/build-tooling.md` | Vite 配置, sourcemaps, 优化, 打包 |

## 快速示例

展示首选模式的最小组件：

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ initialCount?: number }>()

const count = ref(props.initialCount ?? 0)
const doubled = computed(() => count.value * 2)

function increment() {
  count.value++
}
</script>

<template>
  <button @click="increment">Count: {{ count }} (doubled: {{ doubled }})</button>
</template>
```

## 约束

### 必须做
- 使用 Composition API（非 Options API）
- 组件使用 `<script setup>` 语法
- 使用 TypeScript 类型安全的 props
- 原始值使用 `ref()`，对象使用 `reactive()`
- 派生状态使用 `computed()`
- 使用正确的生命周期钩子（onMounted、onUnmounted 等）
- 在 composables 中实现正确的清理
- 全局状态管理使用 Pinia

### 不能做
- 使用 Options API（data、methods、computed 作为对象）
- 混合使用 Composition API 和 Options API
- 直接修改 props
- 不必要地创建响应式对象
- 当 computed 足够时使用 watch
- 忘记清理 watchers 和 effects
- 在 onMounted 之前访问 DOM
- 使用 Vuex（已被 Pinia 替代）

## 输出模板

在实现 Vue 功能时，请提供：
1. 带有 `<script setup>` 和 TypeScript 的组件文件
2. 如果存在可复用逻辑，提供 composable
3. 如果需要全局状态，提供 Pinia store
4. 响应式决策的简要说明

## 知识参考

Vue 3 Composition API, Pinia, Nuxt 3, Vue Router 4, Vite, VueUse, TypeScript, Vitest, Vue Test Utils, SSR/SSG, 响应式编程, 性能优化
