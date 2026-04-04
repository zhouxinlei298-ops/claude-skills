# 移动 & 混合应用

---

## Quasar 框架

### 项目设置

```bash
# 创建新的 Quasar 项目
npm init quasar

# 将 Quasar 添加到现有的 Vue 项目
npm install quasar @quasar/extras
npm install -D @quasar/vite-plugin
```

```typescript
// vite.config.ts - Quasar 插件设置
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'

export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    quasar({
      sassVariables: 'src/quasar-variables.scss'
    })
  ]
})
```

### Quasar 配置

```javascript
// quasar.config.js
export default configure((ctx) => ({
  // 构建模式：spa, pwa, ssr, capacitor, electron, bex
  boot: ['axios', 'i18n'],

  css: ['app.scss'],

  extras: [
    'roboto-font',
    'material-icons'
  ],

  framework: {
    plugins: ['Notify', 'Dialog', 'Loading', 'LocalStorage'],
    config: {
      notify: { position: 'top-right' },
      loading: { spinnerColor: 'primary' }
    }
  },

  build: {
    target: { browser: ['es2022', 'firefox115', 'chrome115', 'safari14'] },
    vueRouterMode: 'history'
  }
}))
```

### 带 Composition API 的 Quasar 组件

```vue
<script setup lang="ts">
import { useQuasar } from 'quasar'

const $q = useQuasar()

function showNotification() {
  $q.notify({
    message: '操作成功完成',
    type: 'positive',
    position: 'top',
    timeout: 3000
  })
}

function showConfirmDialog() {
  $q.dialog({
    title: '确认',
    message: '您确定要继续吗？',
    cancel: true,
    persistent: true
  }).onOk(() => {
    // 用户已确认
  })
}

async function showLoading() {
  $q.loading.show({ message: '处理中...' })
  await doAsyncWork()
  $q.loading.hide()
}
</script>
```

### 布局系统

```vue
<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>我的应用</q-toolbar-title>
        <q-btn flat round icon="person" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item clickable v-ripple to="/dashboard">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>仪表板</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const leftDrawerOpen = ref(false)

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value
}
</script>
```

### 平台检测

```vue
<script setup lang="ts">
import { useQuasar } from 'quasar'

const $q = useQuasar()

// 平台检测
const isMobile = $q.platform.is.mobile
const isIOS = $q.platform.is.ios
const isAndroid = $q.platform.is.android
const isDesktop = $q.platform.is.desktop
const isCapacitor = $q.platform.is.capacitor

// 屏幕工具
const isSmallScreen = $q.screen.lt.md
const screenWidth = $q.screen.width
</script>

<template>
  <div>
    <MobileNav v-if="isMobile" />
    <DesktopNav v-else />
  </div>
</template>
```

---

## Capacitor 集成

### 设置

```bash
# 将 Capacitor 添加到 Quasar
quasar mode add capacitor

# 初始化 Capacitor
cd src-capacitor
npx cap init "应用名称" "com.example.app"

# 添加平台
npx cap add android
npx cap add ios

# 同步并运行
npx cap sync
npx cap open android
```

### Capacitor 配置

```typescript
// capacitor.config.ts
import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: '我的应用',
  webDir: 'dist/spa',
  server: {
    androidScheme: 'https',
    // 用于开发
    url: 'http://192.168.1.100:9000',
    cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: false,
      showSpinner: true
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert']
    }
  }
}

export default config
```

### 带 TypeScript 的原生插件

```typescript
// composables/useCamera.ts
import { ref } from 'vue'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'

export function useCamera() {
  const photo = ref<string | null>(null)
  const error = ref<string | null>(null)

  async function takePhoto() {
    try {
      const image = await Camera.getPhoto({
        resultType: CameraResultType.Uri,
        source: CameraSource.Camera,
        quality: 90
      })
      photo.value = image.webPath ?? null
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  async function pickFromGallery() {
    try {
      const image = await Camera.getPhoto({
        resultType: CameraResultType.Uri,
        source: CameraSource.Photos,
        quality: 90
      })
      photo.value = image.webPath ?? null
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  return { photo, error, takePhoto, pickFromGallery }
}
```

```typescript
// composables/useGeolocation.ts
import { ref, onMounted, onUnmounted } from 'vue'
import { Geolocation, Position } from '@capacitor/geolocation'

export function useGeolocation() {
  const position = ref<Position | null>(null)
  const error = ref<string | null>(null)
  let watchId: string | null = null

  async function getCurrentPosition() {
    try {
      position.value = await Geolocation.getCurrentPosition({
        enableHighAccuracy: true
      })
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  async function watchPosition() {
    watchId = await Geolocation.watchPosition(
      { enableHighAccuracy: true },
      (pos, err) => {
        if (err) {
          error.value = err.message
        } else if (pos) {
          position.value = pos
        }
      }
    )
  }

  function stopWatching() {
    if (watchId) {
      Geolocation.clearWatch({ id: watchId })
      watchId = null
    }
  }

  onUnmounted(stopWatching)

  return { position, error, getCurrentPosition, watchPosition, stopWatching }
}
```

### 推送通知

```typescript
// composables/usePushNotifications.ts
import { ref, onMounted } from 'vue'
import { PushNotifications, Token, PushNotificationSchema } from '@capacitor/push-notifications'
import { Capacitor } from '@capacitor/core'

export function usePushNotifications() {
  const token = ref<string | null>(null)
  const notifications = ref<PushNotificationSchema[]>([])

  async function register() {
    if (!Capacitor.isNativePlatform()) return

    const permission = await PushNotifications.requestPermissions()
    if (permission.receive !== 'granted') return

    await PushNotifications.register()
  }

  onMounted(() => {
    if (!Capacitor.isNativePlatform()) return

    PushNotifications.addListener('registration', (t: Token) => {
      token.value = t.value
    })

    PushNotifications.addListener('pushNotificationReceived', (notification) => {
      notifications.value.push(notification)
    })

    PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
      // 处理通知点击
      console.log('Action:', action.actionId)
    })
  })

  return { token, notifications, register }
}
```

### 应用生命周期

```typescript
// composables/useAppLifecycle.ts
import { onMounted, onUnmounted } from 'vue'
import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'

export function useAppLifecycle() {
  onMounted(() => {
    if (!Capacitor.isNativePlatform()) return

    App.addListener('appStateChange', ({ isActive }) => {
      if (isActive) {
        // 应用来到前台
        refreshData()
      } else {
        // 应用来到后台
        saveState()
      }
    })

    App.addListener('backButton', ({ canGoBack }) => {
      if (!canGoBack) {
        App.exitApp()
      } else {
        window.history.back()
      }
    })
  })

  onUnmounted(() => {
    App.removeAllListeners()
  })
}
```

---

## PWA & Service Workers

### Workbox 配置

```javascript
// quasar.config.js
export default configure((ctx) => ({
  pwa: {
    workboxMode: 'GenerateSW', // 或 'InjectManifest'

    workboxOptions: {
      skipWaiting: true,
      clientsClaim: true,
      cleanupOutdatedCaches: true,

      // 缓存策略
      runtimeCaching: [
        {
          // 缓存 API 响应
          urlPattern: /^https:\/\/api\./,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            networkTimeoutSeconds: 10,
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 // 24 小时
            }
          }
        },
        {
          // 缓存图片
          urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'image-cache',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 60 * 60 * 24 * 30 // 30 天
            }
          }
        },
        {
          // 缓存字体
          urlPattern: /\.(?:woff|woff2|ttf|eot)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'font-cache',
            expiration: {
              maxAgeSeconds: 60 * 60 * 24 * 365 // 1 年
            }
          }
        }
      ]
    }
  }
}))
```

### Web App Manifest

```javascript
// quasar.config.js
export default configure((ctx) => ({
  pwa: {
    manifest: {
      name: '我的渐进式应用',
      short_name: '我的应用',
      description: '一个渐进式 Web 应用',
      display: 'standalone',
      orientation: 'portrait',
      background_color: '#ffffff',
      theme_color: '#1976D2',
      start_url: '/',
      icons: [
        {
          src: 'icons/icon-128x128.png',
          sizes: '128x128',
          type: 'image/png'
        },
        {
          src: 'icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    }
  }
}))
```

### 安装提示处理

```typescript
// composables/usePWAInstall.ts
import { ref, onMounted } from 'vue'

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function usePWAInstall() {
  const canInstall = ref(false)
  const isInstalled = ref(false)
  let deferredPrompt: BeforeInstallPromptEvent | null = null

  onMounted(() => {
    // 检查是否已安装
    isInstalled.value = window.matchMedia('(display-mode: standalone)').matches

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      deferredPrompt = e as BeforeInstallPromptEvent
      canInstall.value = true
    })

    window.addEventListener('appinstalled', () => {
      isInstalled.value = true
      canInstall.value = false
      deferredPrompt = null
    })
  })

  async function install() {
    if (!deferredPrompt) return false

    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    deferredPrompt = null
    canInstall.value = false

    return outcome === 'accepted'
  }

  return { canInstall, isInstalled, install }
}
```

### PWA 更新流程

```typescript
// composables/usePWAUpdate.ts
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'

export function usePWAUpdate() {
  const $q = useQuasar()
  const needsUpdate = ref(false)
  let registration: ServiceWorkerRegistration | null = null

  onMounted(() => {
    if (!('serviceWorker' in navigator)) return

    navigator.serviceWorker.ready.then((reg) => {
      registration = reg

      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing
        if (!newWorker) return

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            needsUpdate.value = true
            promptUpdate()
          }
        })
      })
    })
  })

  function promptUpdate() {
    $q.notify({
      message: '有新版本可用',
      timeout: 0,
      actions: [
        {
          label: '更新',
          color: 'white',
          handler: updateApp
        },
        {
          label: '稍后',
          color: 'white'
        }
      ]
    })
  }

  function updateApp() {
    if (registration?.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
    window.location.reload()
  }

  return { needsUpdate, updateApp }
}
```

### 离线检测

```typescript
// composables/useOnlineStatus.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useOnlineStatus() {
  const isOnline = ref(navigator.onLine)

  function updateOnlineStatus() {
    isOnline.value = navigator.onLine
  }

  onMounted(() => {
    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)
  })

  onUnmounted(() => {
    window.removeEventListener('online', updateOnlineStatus)
    window.removeEventListener('offline', updateOnlineStatus)
  })

  return { isOnline }
}
```

---

## 快速参考

| 模式 | 使用场景 |
|---------|----------|
| `useQuasar()` | 访问 Quasar 插件 ($q) |
| `$q.platform.is.*` | 平台检测 |
| `$q.notify()` | Toast 通知 |
| `$q.dialog()` | 模态对话框 |
| `@capacitor/camera` | 原生相机访问 |
| `@capacitor/geolocation` | GPS 定位 |
| `@capacitor/push-notifications` | 推送通知 |
| `workboxMode: 'GenerateSW'` | 自动生成 service worker |
| `runtimeCaching` | Workbox 缓存策略 |
| `beforeinstallprompt` | PWA 安装提示 |
| `navigator.serviceWorker.ready` | Service worker 生命周期 |
