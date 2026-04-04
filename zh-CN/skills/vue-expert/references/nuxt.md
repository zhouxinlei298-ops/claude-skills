# Nuxt 3

## 项目结构

```
my-nuxt-app/
├── app.vue              # 根组件（可选）
├── nuxt.config.ts       # Nuxt 配置
├── package.json
├── tsconfig.json
├── .output/             # 构建输出
├── assets/              # 编译资源（CSS、图片）
├── public/              # 静态文件（在根目录提供服务）
├── components/          # 自动导入的组件
│   ├── AppHeader.vue
│   └── base/
│       └── Button.vue   # 用作 <BaseButton>
├── composables/         # 自动导入的 composables
│   └── useAuth.ts
├── layouts/             # 布局组件
│   ├── default.vue
│   └── admin.vue
├── middleware/          # 路由中间件
│   └── auth.ts
├── pages/               # 基于文件的路由
│   ├── index.vue        # /
│   ├── about.vue        # /about
│   ├── users/
│   │   ├── index.vue    # /users
│   │   └── [id].vue     # /users/:id
│   └── [...slug].vue    # 捕获所有路由
├── plugins/             # 插件
│   └── api.ts
├── server/              # 服务器 API 路由
│   ├── api/
│   │   └── users.ts     # /api/users
│   └── middleware/
│       └── log.ts
└── stores/              # Pinia stores
    └── user.ts
```

## 基于文件的路由

```vue
<!-- pages/index.vue -->
<script setup lang="ts">
definePageMeta({
  title: '首页',
  layout: 'default'
})
</script>

<template>
  <div>
    <h1>首页</h1>
  </div>
</template>

<!-- pages/about.vue -->
<template>
  <div>关于页面</div>
</template>

<!-- pages/users/[id].vue - 动态路由 -->
<script setup lang="ts">
const route = useRoute()
const userId = computed(() => route.params.id)

const { data: user } = await useFetch(`/api/users/${userId.value}`)
</script>

<template>
  <div>用户：{{ user?.name }}</div>
</template>

<!-- pages/blog/[...slug].vue - 捕获所有路由 -->
<script setup lang="ts">
const route = useRoute()
const slug = route.params.slug // ['2024', '12', 'my-post']
</script>

<template>
  <div>博客文章：{{ slug }}</div>
</template>
```

## 布局

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <header>
      <nav>导航</nav>
    </header>
    <main>
      <slot /> <!-- 页面内容在这里 -->
    </main>
    <footer>页脚</footer>
  </div>
</template>

<!-- layouts/admin.vue -->
<script setup lang="ts">
definePageMeta({
  middleware: 'auth' // 用中间件保护
})
</script>

<template>
  <div class="admin-layout">
    <aside>管理侧边栏</aside>
    <main>
      <slot />
    </main>
  </div>
</template>

<!-- pages/admin/dashboard.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'admin'
})
</script>

<template>
  <div>管理仪表板</div>
</template>
```

## 数据获取

```vue
<script setup lang="ts">
interface User {
  id: number
  name: string
  email: string
}

// useFetch - SSR 安全，自动导入
const { data: users, pending, error, refresh } = await useFetch<User[]>('/api/users')

// 带选项
const { data } = await useFetch('/api/users', {
  method: 'POST',
  body: { name: 'John' },
  headers: {
    'Authorization': 'Bearer token'
  },
  query: { page: 1, limit: 10 },
  // 转换响应
  transform: (data) => data.map(u => ({ ...u, fullName: u.firstName + ' ' + u.lastName })),
  // 选择特定键
  pick: ['id', 'name'],
  // 监听变化
  watch: [page, limit]
})

// useAsyncData - 更多控制
const { data: user } = await useAsyncData(
  'user-123', // 缓存的唯一键
  async () => {
    const response = await fetch('/api/users/123')
    return response.json()
  },
  {
    server: true, // 在服务器上获取
    lazy: false, // 不阻塞导航
    default: () => null // 加载时的默认值
  }
)

// useLazyFetch - 非阻塞
const { data: posts } = await useLazyFetch('/api/posts')

// useLazyAsyncData - 非阻塞自定义 fetcher
const { data: comments } = await useLazyAsyncData('comments', () =>
  $fetch('/api/comments')
)

// 手动刷新
function handleRefresh() {
  refresh() // 重新获取数据
}
</script>

<template>
  <div v-if="pending">加载中...</div>
  <div v-else-if="error">错误：{{ error.message }}</div>
  <div v-else>
    <div v-for="user in users" :key="user.id">
      {{ user.name }}
    </div>
    <button @click="handleRefresh">刷新</button>
  </div>
</template>
```

## 服务器 API 路由

```typescript
// server/api/users.get.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const page = Number(query.page) || 1
  const limit = Number(query.limit) || 10

  // 从数据库获取
  const users = await prisma.user.findMany({
    skip: (page - 1) * limit,
    take: limit
  })

  return users
})

// server/api/users/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')

  const user = await prisma.user.findUnique({
    where: { id: Number(id) }
  })

  if (!user) {
    throw createError({
      statusCode: 404,
      message: '用户未找到'
    })
  }

  return user
})

// server/api/users.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  // 验证
  if (!body.email || !body.name) {
    throw createError({
      statusCode: 400,
      message: '电子邮件和名称是必需的'
    })
  }

  const user = await prisma.user.create({
    data: {
      email: body.email,
      name: body.name
    }
  })

  return user
})

// server/api/auth/login.post.ts
export default defineEventHandler(async (event) => {
  const { email, password } = await readBody(event)

  // 验证凭据
  const user = await verifyCredentials(email, password)

  if (!user) {
    throw createError({
      statusCode: 401,
      message: '凭据无效'
    })
  }

  // 设置会话 cookie
  setCookie(event, 'session', user.sessionToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 60 * 60 * 24 * 7 // 7 天
  })

  return { success: true, user }
})
```

## 中间件

```typescript
// middleware/auth.ts - 路由中间件
export default defineNuxtRouteMiddleware((to, from) => {
  const { isLoggedIn } = useAuthStore()

  if (!isLoggedIn) {
    return navigateTo('/login')
  }
})

// middleware/logger.global.ts - 全局中间件
export default defineNuxtRouteMiddleware((to, from) => {
  console.log(`从 ${from.path} 导航到 ${to.path}`)
})

// server/middleware/log.ts - 服务器中间件
export default defineEventHandler((event) => {
  console.log(`[${event.method}] ${event.path}`)
})
```

## Composables

```typescript
// composables/useAuth.ts - 自动导入
export const useAuth = () => {
  const user = useState<User | null>('user', () => null)
  const isLoggedIn = computed(() => user.value !== null)

  async function login(email: string, password: string) {
    const { data, error } = await useFetch('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    })

    if (data.value) {
      user.value = data.value.user
    }
  }

  async function logout() {
    await useFetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    navigateTo('/login')
  }

  async function fetchUser() {
    const { data } = await useFetch('/api/auth/me')
    user.value = data.value
  }

  return {
    user,
    isLoggedIn,
    login,
    logout,
    fetchUser
  }
}

// 组件中使用（自动导入）
<script setup lang="ts">
const { user, isLoggedIn, login, logout } = useAuth()
</script>
```

## 插件

```typescript
// plugins/api.ts
export default defineNuxtPlugin((nuxtApp) => {
  const api = $fetch.create({
    baseURL: '/api',
    onRequest({ options }) => {
      // 添加认证令牌
      const token = useCookie('token')
      if (token.value) {
        options.headers = options.headers || {}
        options.headers.Authorization = `Bearer ${token.value}`
      }
    },
    onResponseError({ response }) => {
      if (response.status === 401) {
        navigateTo('/login')
      }
    }
  })

  return {
    provide: {
      api
    }
  }
})

// 组件中使用
<script setup lang="ts">
const { $api } = useNuxtApp()
const users = await $api('/users')
</script>
```

## 配置

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt'
  ],

  runtimeConfig: {
    // 服务器专用（从不暴露给客户端）
    apiSecret: process.env.API_SECRET,

    // 暴露给客户端
    public: {
      apiBase: process.env.API_BASE || '/api'
    }
  },

  app: {
    head: {
      title: '我的应用',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: '我的神奇网站' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  },

  css: ['~/assets/css/main.css'],

  typescript: {
    strict: true,
    typeCheck: true
  },

  // Vite 是 Nuxt 3 中的默认打包器
  // 注意：webpack 已被弃用 - 所有新项目都应使用 Vite
  vite: {
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia']
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'pinia']
          }
        }
      }
    }
  },

  nitro: {
    preset: 'vercel' // 或 'node-server', 'cloudflare', 'bun'
  }
})
```

## SEO 和 Meta 标签

```vue
<script setup lang="ts">
const route = useRoute()
const title = computed(() => `用户 ${route.params.id}`)

useHead({
  title,
  meta: [
    { name: 'description', content: '用户资料页面' },
    { property: 'og:title', content: title },
    { property: 'og:description', content: '用户资料页面' }
  ]
})

// 或使用 useSeoMeta
useSeoMeta({
  title: '我的页面',
  ogTitle: '我的页面',
  description: '页面描述',
  ogDescription: '页面描述',
  ogImage: 'https://example.com/image.png'
})
</script>
```

## 使用 Fastify 的自定义 SSR

对于不使用 Nuxt 的自定义 Vue 3 SSR，使用 Fastify 作为服务器：

```typescript
// server.ts
import Fastify from 'fastify'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import App from './App.vue'

const fastify = Fastify({ logger: true })

const app = createSSRApp(App)

fastify.get('*', async (request, reply) => {
  // 服务器端数据获取
  const initialState = await fetchInitialData(request.url)

  const html = await renderToString(app)

  reply.type('text/html').send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Vue SSR</title>
        <script>window.__INITIAL_STATE__ = ${JSON.stringify(initialState)}</script>
      </head>
      <body>
        <div id="app">${html}</div>
        <script type="module" src="/src/entry-client.ts"></script>
      </body>
    </html>
  `)
})

fastify.listen({ port: 3000 })
```

```typescript
// entry-client.ts
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)

// 与服务器状态水合
if (window.__INITIAL_STATE__) {
  app.provide('initialState', window.__INITIAL_STATE__)
}

app.mount('#app')
```

```typescript
// vite.config.ts 用于 SSR
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    ssr: true,
    rollupOptions: {
      input: {
        server: './server.ts',
        client: './src/entry-client.ts'
      }
    }
  }
})
```

## 水合模式

### 使用 ClientOnly 懒加载

```vue
<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

// 仅在客户端加载的繁重组件
const HeavyChart = defineAsyncComponent(() =>
  import('./components/HeavyChart.vue')
)
</script>

<template>
  <ClientOnly>
    <HeavyChart />
    <template #fallback>
      <div class="chart-skeleton">加载图表中...</div>
    </template>
  </ClientOnly>
</template>
```

### 防止水合不匹配

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 避免对仅客户端值的水合不匹配
const currentTime = ref<string | null>(null)
const windowWidth = ref<number | null>(null)

onMounted(() => {
  // 这些值在服务器和客户端之间不同
  currentTime.value = new Date().toLocaleTimeString()
  windowWidth.value = window.innerWidth
})
</script>

<template>
  <div>
    <!-- 使用 v-if 防止不匹配 -->
    <span v-if="currentTime">{{ currentTime }}</span>
    <span v-else>--:--</span>
  </div>
</template>
```

### 渐进式水合

```vue
<script setup lang="ts">
import { defineNuxtLink, useLazyAsyncData } from '#app'

// 使用 nuxt-delay-hydration 延迟非关键内容的加载
definePageMeta({
  // 延迟水合直到可见或空闲
  hydration: 'when-visible' // 或 'on-idle'
})
</script>

<template>
  <div>
    <!-- 关键内容立即水合 -->
    <header>导航</header>

    <!-- 非关键内容可以等待 -->
    <LazyBelowFoldContent />
  </div>
</template>
```

```typescript
// nuxt.config.ts - 配置延迟水合
export default defineNuxtConfig({
  modules: ['@nuxtjs/delay-hydration'],

  delayHydration: {
    mode: 'init', // 或 'mount'
    debug: process.env.NODE_ENV === 'development'
  }
})
```

---

## 快速参考

| 模式 | 使用场景 |
|---------|----------|
| `useFetch()` | 获取数据（SSR 安全） |
| `useAsyncData()` | 自定义异步操作 |
| `useLazyFetch()` | 非阻塞获取 |
| `useLazyAsyncData()` | 非阻塞自定义 fetcher |
| `useState()` | 跨组件共享状态 |
| `useRoute()` | 访问路由参数/查询 |
| `useRouter()` | 编程式导航 |
| `navigateTo()` | 导航到路由 |
| `definePageMeta()` | 页面级元数据 |
| `useHead()` | 动态元标签 |
| 服务器路由 | `/server/api/*.ts` |
| 自动导入 | 组件、composables、utils |
| `<ClientOnly>` | 仅客户端渲染，防止水合不匹配 |
| `renderToString()` | 使用 Fastify/Express 的自定义 SSR |
| `vite: {}` | nuxt.config.ts 中的 Vite 配置 |
| `nuxt-delay-hydration` | 渐进式水合以优化性能 |
