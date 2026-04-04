# 数据获取与缓存

## 扩展的 fetch API

Next.js 扩展了原生 fetch，增加了缓存和 revalidation 选项：

```tsx
// app/page.tsx
async function getData() {
  const res = await fetch('https://api.example.com/posts', {
    cache: 'force-cache', // 默认：永久缓存 (SSG)
  })

  if (!res.ok) {
    throw new Error('Failed to fetch data')
  }

  return res.json()
}

export default async function Page() {
  const data = await getData()
  return <div>{/* render data */}</div>
}
```

## 缓存选项

```tsx
// 1. 强制缓存（静态站点生成）
fetch('https://api.example.com/data', {
  cache: 'force-cache' // 默认行为
})

// 2. 不缓存（服务端渲染）
fetch('https://api.example.com/data', {
  cache: 'no-store' // 总是获取最新数据
})

// 3. Revalidate（增量静态再生）
fetch('https://api.example.com/data', {
  next: { revalidate: 3600 } // 每小时重新验证
})

// 4. 基于标签的 revalidation
fetch('https://api.example.com/data', {
  next: { tags: ['posts'] }
})
```

## Revalidation 方法

### 基于时间的 Revalidation (ISR)

```tsx
// 每 60 秒重新验证
async function getPosts() {
  const res = await fetch('https://api.example.com/posts', {
    next: { revalidate: 60 }
  })
  return res.json()
}

// 路由段配置
export const revalidate = 60 // 秒

export default async function Page() {
  const posts = await getPosts()
  return <div>{/* render */}</div>
}
```

### 按需 Revalidation

```tsx
// app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache'
import { NextRequest } from 'next/server'

export async function POST(request: NextRequest) {
  const path = request.nextUrl.searchParams.get('path')

  if (path) {
    revalidatePath(path)
    return Response.json({ revalidated: true, now: Date.now() })
  }

  return Response.json({ revalidated: false })
}

// 在 Server Action 中使用
'use server'

import { revalidatePath } from 'next/cache'

export async function createPost(data: FormData) {
  await db.post.create({ data })

  // 重新验证特定路径
  revalidatePath('/posts')

  // 重新验证整个布局
  revalidatePath('/posts', 'layout')
}
```

### 基于标签的 Revalidation

```tsx
// 带标签的 fetch
async function getPosts() {
  const res = await fetch('https://api.example.com/posts', {
    next: { tags: ['posts'] }
  })
  return res.json()
}

async function getAuthors() {
  const res = await fetch('https://api.example.com/authors', {
    next: { tags: ['authors'] }
  })
  return res.json()
}

// 按标签重新验证
import { revalidateTag } from 'next/cache'

export async function createPost() {
  // 重新验证所有标记为 'posts' 的 fetch
  revalidateTag('posts')
}
```

## 路由段配置

```tsx
// app/posts/page.tsx

// 强制动态渲染
export const dynamic = 'force-dynamic' // 'auto' | 'force-dynamic' | 'error' | 'force-static'

// Revalidation 间隔
export const revalidate = 3600 // false | 0 | number (秒)

// Fetch 缓存
export const fetchCache = 'auto' // 'auto' | 'default-cache' | 'only-cache' | 'force-cache' | 'force-no-store' | 'default-no-store' | 'only-no-store'

// Runtime
export const runtime = 'nodejs' // 'nodejs' | 'edge'

// 首选区域
export const preferredRegion = 'auto' // 'auto' | 'home' | 'edge' | string | string[]

export default async function Page() {
  return <div>Posts</div>
}
```

## 并行数据获取

```tsx
async function getUser() {
  return fetch('https://api.example.com/user')
}

async function getPosts() {
  return fetch('https://api.example.com/posts')
}

async function getComments() {
  return fetch('https://api.example.com/comments')
}

export default async function Page() {
  // 使用 Promise.all 并行获取
  const [user, posts, comments] = await Promise.all([
    getUser(),
    getPosts(),
    getComments(),
  ])

  return (
    <div>
      <UserInfo user={user} />
      <Posts posts={posts} />
      <Comments comments={comments} />
    </div>
  )
}
```

## 顺序数据获取

```tsx
// 当一个 fetch 依赖另一个时
export default async function Page({ params }: { params: { id: string } }) {
  // 第一次获取
  const user = await fetch(`https://api.example.com/users/${params.id}`)
    .then(res => res.json())

  // 第二次获取依赖第一次
  const posts = await fetch(`https://api.example.com/users/${user.id}/posts`)
    .then(res => res.json())

  return (
    <div>
      <h1>{user.name}</h1>
      <Posts posts={posts} />
    </div>
  )
}
```

## 使用 Suspense 流式渲染

```tsx
// app/page.tsx
import { Suspense } from 'react'

async function Posts() {
  const posts = await fetch('https://api.example.com/posts', {
    cache: 'no-store'
  }).then(res => res.json())

  return (
    <ul>
      {posts.map((post: Post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}

export default function Page() {
  return (
    <div>
      <h1>Posts</h1>
      <Suspense fallback={<div>Loading posts...</div>}>
        <Posts />
      </Suspense>
    </div>
  )
}
```

## React cache 用于去重

```tsx
// lib/data.ts
import { cache } from 'react'

export const getUser = cache(async (id: string) => {
  const res = await fetch(`https://api.example.com/users/${id}`)
  return res.json()
})

// components/user-profile.tsx
export async function UserProfile({ userId }: { userId: string }) {
  const user = await getUser(userId) // 已缓存
  return <div>{user.name}</div>
}

// components/user-posts.tsx
export async function UserPosts({ userId }: { userId: string }) {
  const user = await getUser(userId) // 使用缓存结果
  return <div>{user.posts.length} posts</div>
}

// app/page.tsx
export default function Page() {
  return (
    <>
      <UserProfile userId="123" />
      <UserPosts userId="123" /> {/* 相同的 fetch，已去重 */}
    </>
  )
}
```

## 数据库查询

```tsx
// lib/db.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = global as unknown as { prisma: PrismaClient }

export const db = globalForPrisma.prisma || new PrismaClient()

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db

// app/posts/page.tsx
import { db } from '@/lib/db'

export const revalidate = 60 // 每 60 秒重新验证

export default async function PostsPage() {
  const posts = await db.post.findMany({
    include: { author: true },
    orderBy: { createdAt: 'desc' },
  })

  return (
    <div>
      {posts.map(post => (
        <article key={post.id}>
          <h2>{post.title}</h2>
          <p>By {post.author.name}</p>
        </article>
      ))}
    </div>
  )
}
```

## 错误处理

```tsx
async function getData() {
  const res = await fetch('https://api.example.com/data')

  if (!res.ok) {
    // 这将触发最近的 error.tsx
    throw new Error('Failed to fetch data')
  }

  return res.json()
}

export default async function Page() {
  const data = await getData()
  return <div>{data.title}</div>
}

// app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  )
}
```

## Loading 状态

```tsx
// app/posts/loading.tsx
export default function Loading() {
  return <div>Loading posts...</div>
}

// app/posts/page.tsx
export default async function PostsPage() {
  const posts = await fetch('https://api.example.com/posts')
    .then(res => res.json())

  return <div>{/* render posts */}</div>
}
```

## 客户端数据获取

```tsx
// 当需要客户端获取时
'use client'

import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then(res => res.json())

export function Posts() {
  const { data, error, isLoading } = useSWR('/api/posts', fetcher, {
    refreshInterval: 3000, // 每 3 秒刷新
  })

  if (error) return <div>Failed to load</div>
  if (isLoading) return <div>Loading...</div>

  return (
    <ul>
      {data.map((post: Post) => (
        <li key={post.id}>{post.title}</li>
      ))}
    </ul>
  )
}
```

## 预加载数据

```tsx
// lib/data.ts
import { cache } from 'react'

export const preload = (id: string) => {
  void getUser(id) // 触发 fetch 而不等待
}

export const getUser = cache(async (id: string) => {
  return fetch(`https://api.example.com/users/${id}`)
    .then(res => res.json())
})

// components/user.tsx
import { getUser, preload } from '@/lib/data'

export async function User({ id }: { id: string }) {
  const user = await getUser(id)
  return <div>{user.name}</div>
}

// app/page.tsx
import { User } from '@/components/user'
import { preload } from '@/lib/data'

export default async function Page() {
  preload('123') // 立即开始加载
  return <User id="123" />
}
```

## 动态路由的静态生成

```tsx
// app/posts/[slug]/page.tsx
type Post = {
  slug: string
  title: string
  content: string
}

export async function generateStaticParams() {
  const posts = await fetch('https://api.example.com/posts')
    .then(res => res.json())

  return posts.map((post: Post) => ({
    slug: post.slug,
  }))
}

export default async function Post({ params }: { params: { slug: string } }) {
  const post = await fetch(`https://api.example.com/posts/${params.slug}`)
    .then(res => res.json())

  return (
    <article>
      <h1>{post.title}</h1>
      <div>{post.content}</div>
    </article>
  )
}
```

## 快速参考

| 策略 | 配置 | 使用场景 |
|----------|--------|----------|
| **SSG** | `cache: 'force-cache'` | 静态内容 |
| **SSR** | `cache: 'no-store'` | 总是最新数据 |
| **ISR** | `next: { revalidate: 60 }` | 周期性更新 |
| **基于标签** | `next: { tags: ['posts'] }` | 按需 revalidation |
| **动态** | `export const dynamic = 'force-dynamic'` | 每次请求数据 |

## 最佳实践

1. **默认使用缓存** — 静态内容使用 force-cache
2. **使用 ISR** — 半动态内容定期 revalidate
3. **并行获取** — 独立请求使用 Promise.all
4. **去重** — 重复调用使用 React cache()
5. **Suspense 流式渲染** — 渐进式显示内容
6. **为 fetch 打标签** — 启用细粒度 revalidation
7. **错误处理** — 使用 error.tsx 优雅降级
