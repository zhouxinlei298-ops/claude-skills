# React Server Components

## Server Components（默认）

```tsx
// app/page.tsx - 默认为 Server Component
import { db } from '@/lib/db'

export default async function Page() {
  // 在 Server Component 中获取数据
  const users = await db.user.findMany()

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>{user.name}</li>
        ))}
      </ul>
    </div>
  )
}
```

## Server Components 的优势

- **零打包体积** - Server Components 不增加客户端包体积
- **直接后端访问** - 查询数据库、读取文件、使用密钥
- **自动代码分割** - 只有 Client Components 增加包体积
- **流式渲染** - 数据加载时渐进式发送 UI
- **无客户端瀑布** - 在服务器上并行获取所有数据

## Client Components

```tsx
// components/counter.tsx
'use client' // 必需的指令

import { useState } from 'react'

export function Counter() {
  const [count, setCount] = useState(0)

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  )
}
```

## 何时使用 Client Components

在以下情况使用 `'use client'`：
- **交互性** - onClick、onChange、事件处理器
- **状态** - useState、useReducer
- **副作用** - useEffect、useLayoutEffect
- **浏览器 API** - localStorage、window、document
- **自定义 hooks** - 使用仅限客户端功能的任何 hook
- **类组件** - 组件生命周期方法

## 组合模式

```tsx
// app/page.tsx - Server Component
import { ClientWrapper } from './client-wrapper'
import { db } from '@/lib/db'

export default async function Page() {
  const data = await db.query()

  return (
    <div>
      {/* Server Component 内容 */}
      <h1>Server Content</h1>

      {/* 将数据传递给 Client Component */}
      <ClientWrapper initialData={data}>
        {/* Server Component 作为 children */}
        <ServerSidebar />
      </ClientWrapper>
    </div>
  )
}

// components/client-wrapper.tsx
'use client'

export function ClientWrapper({
  children,
  initialData,
}: {
  children: React.ReactNode
  initialData: Data
}) {
  const [data, setData] = useState(initialData)

  return (
    <div>
      {/* Client Component UI */}
      <button onClick={() => refresh()}>Refresh</button>
      {/* Server Component children */}
      {children}
    </div>
  )
}
```

## 使用 Suspense 流式渲染

```tsx
// app/page.tsx
import { Suspense } from 'react'
import { SlowComponent } from './slow-component'
import { FastComponent } from './fast-component'

export default function Page() {
  return (
    <div>
      {/* 立即渲染 */}
      <FastComponent />

      {/* 加载时显示 fallback */}
      <Suspense fallback={<div>Loading...</div>}>
        <SlowComponent />
      </Suspense>
    </div>
  )
}

// components/slow-component.tsx
async function getData() {
  await new Promise(resolve => setTimeout(resolve, 3000))
  return { data: 'Loaded!' }
}

export async function SlowComponent() {
  const data = await getData()
  return <div>{data.data}</div>
}
```

## 并行数据获取

```tsx
// app/dashboard/page.tsx
async function getUser() {
  return fetch('https://api.example.com/user')
}

async function getPosts() {
  return fetch('https://api.example.com/posts')
}

export default async function Dashboard() {
  // 并行获取
  const [user, posts] = await Promise.all([
    getUser(),
    getPosts(),
  ])

  return (
    <div>
      <UserProfile user={user} />
      <PostsList posts={posts} />
    </div>
  )
}
```

## 顺序数据获取

```tsx
// app/artist/[id]/page.tsx
async function getArtist(id: string) {
  return fetch(`https://api.example.com/artists/${id}`)
}

async function getAlbums(artistId: string) {
  return fetch(`https://api.example.com/artists/${artistId}/albums`)
}

export default async function ArtistPage({ params }: { params: { id: string } }) {
  // 顺序：albums 依赖 artist
  const artist = await getArtist(params.id)
  const albums = await getAlbums(artist.id)

  return (
    <div>
      <h1>{artist.name}</h1>
      <Albums albums={albums} />
    </div>
  )
}
```

## 预加载数据

```tsx
// lib/data.ts
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  return db.user.findUnique({ where: { id } })
})

// components/user-profile.tsx
export async function UserProfile({ userId }: { userId: string }) {
  const user = await getUser(userId)
  return <div>{user.name}</div>
}

// app/page.tsx
import { getUser } from '@/lib/data'
import { UserProfile } from '@/components/user-profile'

export default async function Page() {
  // 预加载
  getUser('123')

  return (
    <div>
      {/* 这将使用缓存结果 */}
      <UserProfile userId="123" />
    </div>
  )
}
```

## Server Component 模式

### 模式：带数据获取的布局

```tsx
// app/dashboard/layout.tsx
import { auth } from '@/lib/auth'
import { db } from '@/lib/db'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()
  const user = await db.user.findUnique({ where: { id: session.userId } })

  return (
    <div>
      <Sidebar user={user} />
      <main>{children}</main>
    </div>
  )
}
```

### 模式：条件性 Client Components

```tsx
// app/page.tsx
import { ClientComponent } from './client-component'

export default async function Page() {
  const data = await fetchData()

  // 仅在需要时渲染 Client Component
  if (data.requiresInteractivity) {
    return <ClientComponent data={data} />
  }

  return <div>{data.content}</div>
}
```

### 模式：Server Component 带客户端岛屿

```tsx
// app/blog/[slug]/page.tsx
import { LikeButton } from './like-button'

export default async function BlogPost({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug)

  return (
    <article>
      {/* 服务器渲染的内容 */}
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.content }} />

      {/* 用于交互性的客户端岛屿 */}
      <LikeButton postId={post.id} initialLikes={post.likes} />
    </article>
  )
}
```

## Server/Client Components 中的 Context

```tsx
// app/providers.tsx
'use client'

import { ThemeProvider } from 'next-themes'

export function Providers({ children }: { children: React.ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>
}

// app/layout.tsx
import { Providers } from './providers'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

## 第三方组件

```tsx
// components/carousel-wrapper.tsx
'use client'

import { Carousel } from 'third-party-carousel'

export function CarouselWrapper({ items }: { items: Item[] }) {
  return <Carousel items={items} />
}

// app/page.tsx
import { CarouselWrapper } from '@/components/carousel-wrapper'

export default async function Page() {
  const items = await fetchItems()
  return <CarouselWrapper items={items} />
}
```

## Edge Runtime

```tsx
// app/api/route.ts
export const runtime = 'edge'

export async function GET() {
  return new Response('Hello from Edge!')
}

// app/page.tsx
export const runtime = 'edge'

export default async function Page() {
  return <div>Edge-rendered page</div>
}
```

## 快速参考

| 功能 | Server Component | Client Component |
|------------|------------------|------------------|
| 数据获取 | ✅ 可以 | ⚠️ 使用 SWR/React Query |
| 后端访问 | ✅ 可以（数据库、文件） | ❌ 不可以 |
| 事件处理器 | ❌ 不可以 | ✅ 可以 |
| 状态/副作用 | ❌ 不可以 | ✅ 可以 |
| 浏览器 API | ❌ 不可以 | ✅ 可以 |
| 包体积 | 0 KB | 增加到包中 |
| 流式渲染 | ✅ 可以 | ❌ 不可以 |

## 最佳实践

1. **默认使用 Server Components** - 仅在需要时使用 'use client'
2. **将 Client Components 下移** - 推到组件树的叶子节点
3. **向下传递数据** - 在 Server Components 中获取，传递给 Client Components
4. **使用组合** - 通过 children 在 Client Components 中嵌套 Server Components
5. **缓存昂贵操作** - 使用 React cache() 去重
