# 构建工具 & Vite

---

## Vue 的 Vite 配置

### 基本配置

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@components': fileURLToPath(new URL('./src/components', import.meta.url)),
      '@composables': fileURLToPath(new URL('./src/composables', import.meta.url)),
      '@stores': fileURLToPath(new URL('./src/stores', import.meta.url))
    }
  }
})
```

### 核心插件

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import VueDevTools from 'vite-plugin-vue-devtools'
import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { QuasarResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),

    // Vue DevTools 集成
    VueDevTools(),

    // 自动导入组件
    Components({
      dirs: ['src/components'],
      resolvers: [QuasarResolver()],
      dts: 'src/components.d.ts'
    }),

    // 自动导入 Vue API
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts',
      dirs: ['src/composables'],
      vueTemplate: true
    })
  ]
})
```

### 环境变量

```typescript
// .env
VITE_API_URL=https://api.example.com
VITE_APP_TITLE=My App

// .env.development
VITE_API_URL=http://localhost:3000

// .env.production
VITE_API_URL=https://api.production.com
```

```typescript
// 在代码中使用
const apiUrl = import.meta.env.VITE_API_URL
const isDev = import.meta.env.DEV
const isProd = import.meta.env.PROD
const mode = import.meta.env.MODE

// 类型声明（env.d.ts）
/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}
```

```typescript
// vite.config.ts - 定义全局常量
export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString())
  }
})
```

### 开发服务器代理

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://localhost:3000',
        ws: true
      }
    }
  }
})
```

---

## Source Maps 配置

### 开发 Source Maps

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // 开发环境的完整 source maps
    sourcemap: true
  }
})
```

### 生产 Source Maps

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // 选项：true | 'inline' | 'hidden' | false
    sourcemap: process.env.NODE_ENV === 'production' ? 'hidden' : true
  }
})
```

| 模式 | 值 | 使用场景 |
|------|-------|----------|
| 完整 | `true` | 开发、staging |
| 隐藏 | `'hidden'` | 带错误追踪的生产环境 |
| 内联 | `'inline'` | 单文件调试 |
| 无 | `false` | 无调试的生产环境 |

### VS Code 调试

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "调试 Vue 应用",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/src",
      "sourceMapPathOverrides": {
        "webpack:///./src/*": "${webRoot}/*"
      }
    }
  ]
}
```

### Sentry 错误追踪

```typescript
// vite.config.ts
import { sentryVitePlugin } from '@sentry/vite-plugin'

export default defineConfig({
  build: {
    sourcemap: true
  },
  plugins: [
    sentryVitePlugin({
      org: 'your-org',
      project: 'your-project',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        assets: './dist/**',
        filesToDeleteAfterUpload: './dist/**/*.map'
      }
    })
  ]
})
```

---

## 构建优化

### Tree Shaking 最佳实践

```typescript
// 好的做法：命名导入启用 tree shaking
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { format, parseISO } from 'date-fns'

// 坏的做法：命名空间导入包含所有内容
import * as Vue from 'vue'
import * as dateFns from 'date-fns'
```

```typescript
// 确保 package.json 有正确的 sideEffects 以实现适当的 tree shaking
{
  "sideEffects": [
    "*.css",
    "*.scss",
    "*.vue"
  ]
}
```

### 代码分割 & 懒加载

```typescript
// 基于路由的代码分割
const routes = [
  {
    path: '/dashboard',
    component: () => import('./views/Dashboard.vue')
  },
  {
    path: '/settings',
    component: () => import('./views/Settings.vue')
  }
]

// 组件级别的懒加载
const HeavyChart = defineAsyncComponent(() =>
  import('./components/HeavyChart.vue')
)

// 带加载/错误状态
const AsyncModal = defineAsyncComponent({
  loader: () => import('./components/Modal.vue'),
  loadingComponent: LoadingSpinner,
  errorComponent: ErrorDisplay,
  delay: 200,
  timeout: 10000
})
```

### 手动 Chunks 配置

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // 核心依赖的 vendor chunk
          'vendor': ['vue', 'vue-router', 'pinia'],

          // UI 框架 chunk
          'ui': ['quasar', '@quasar/extras'],

          // 工具库
          'utils': ['lodash-es', 'date-fns', 'axios']
        }
      }
    }
  }
})
```

```typescript
// 按包进行动态 chunking
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // 将每个包拆分为自己的 chunk
            const packageName = id.split('node_modules/')[1].split('/')[0]
            return `vendor-${packageName}`
          }
        }
      }
    }
  }
})
```

### Chunk 大小优化

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // 如果 chunk 超过 500KB 则警告
    chunkSizeWarningLimit: 500,

    rollupOptions: {
      output: {
        // 确保 CSS 被提取
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js'
      }
    }
  }
})
```

### 压缩插件

```typescript
// vite.config.ts
import viteCompression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    // Gzip 压缩
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 1024
    }),

    // Brotli 压缩（更好的压缩率）
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 1024
    })
  ]
})
```

### 图片优化

```typescript
// vite.config.ts
import viteImagemin from 'vite-plugin-imagemin'

export default defineConfig({
  plugins: [
    viteImagemin({
      gifsicle: { optimizationLevel: 3 },
      optipng: { optimizationLevel: 7 },
      mozjpeg: { quality: 80 },
      svgo: {
        plugins: [
          { name: 'removeViewBox', active: false },
          { name: 'removeEmptyAttrs', active: true }
        ]
      },
      webp: { quality: 80 }
    })
  ]
})
```

---

## 性能分析

### Bundle 分析器

```typescript
// vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    visualizer({
      filename: 'stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap' // 或 'sunburst', 'network'
    })
  ]
})
```

```bash
# 生成分析报告
npm run build
# 自动打开 stats.html
```

### 构建性能

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // 使用 esbuild 压缩实现更快的构建
    minify: 'esbuild',

    // 仅针对现代浏览器
    target: 'esnext',

    // 禁用 CSS 代码分割以获得更快的构建
    cssCodeSplit: false
  },

  // 优化依赖预打包
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios'],
    exclude: ['your-local-package']
  }
})
```

### Web Vitals 监控

```typescript
// src/utils/vitals.ts
import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals'

type VitalMetric = {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
}

function sendToAnalytics(metric: VitalMetric) {
  // 发送到你的分析端点
  console.log(metric)
}

export function initVitals() {
  onCLS(sendToAnalytics)
  onFID(sendToAnalytics)
  onLCP(sendToAnalytics)
  onFCP(sendToAnalytics)
  onTTFB(sendToAnalytics)
}
```

```typescript
// main.ts
import { initVitals } from './utils/vitals'

if (import.meta.env.PROD) {
  initVitals()
}
```

---

## 快速参考

| 模式 | 使用场景 |
|---------|----------|
| `@vitejs/plugin-vue` | Vue 3 SFC 支持 |
| `unplugin-vue-components` | 自动导入组件 |
| `unplugin-auto-import` | 自动导入 Vue API |
| `manualChunks` | Vendor 代码分割 |
| `sourcemap: 'hidden'` | 生产环境错误追踪 |
| `vite-plugin-compression` | Gzip/Brotli 压缩 |
| `rollup-plugin-visualizer` | Bundle 大小分析 |
| `import.meta.env.VITE_*` | 环境变量 |
| `defineAsyncComponent` | 组件懒加载 |
| `web-vitals` | 核心 Web Vitals 监控 |
