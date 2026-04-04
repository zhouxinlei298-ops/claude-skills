# 部署与生产环境

## Vercel 部署（推荐）

### 快速部署

```bash
# Install Vercel CLI
npm i -g vercel

# 部署
vercel

# 生产部署
vercel --prod
```

### vercel.json 配置

```json
{
  "buildCommand": "next build",
  "devCommand": "next dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"],
  "env": {
    "DATABASE_URL": "@database-url",
    "NEXT_PUBLIC_API_URL": "https://api.example.com"
  },
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" },
        { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE" }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/old-blog/:slug",
      "destination": "/blog/:slug",
      "permanent": true
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.example.com/:path*"
    }
  ]
}
```

### 环境变量

```bash
# .env.local（不提交到版本控制）
DATABASE_URL="postgresql://user:pass@localhost:5432/db"
NEXTAUTH_SECRET="your-secret"

# .env.production（提交到版本控制，仅公开变量）
NEXT_PUBLIC_API_URL="https://api.example.com"
```

```tsx
// 在 Server Components 中访问
const dbUrl = process.env.DATABASE_URL

// 在 Client Components 中访问（必须以 NEXT_PUBLIC_ 前缀）
const apiUrl = process.env.NEXT_PUBLIC_API_URL
```

## 自托管

### Standalone 输出

```js
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
}

module.exports = nextConfig
```

```bash
# 构建
npm run build

# standalone 文件夹包含所需的一切
# 将以下内容复制到服务器：
# - .next/standalone/
# - .next/static/
# - public/

# 在服务器上运行
node .next/standalone/server.js
```

### Node.js 服务器

```bash
# 构建
npm run build

# 启动生产服务器
npm start

# 使用 PM2 进行进程管理
pm2 start npm --name "nextjs" -- start
pm2 startup
pm2 save
```

## Docker 部署

### Dockerfile（多阶段）

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  nextjs:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/myapp
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=your-secret
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

```bash
# 构建并运行
docker-compose up -d

# 查看日志
docker-compose logs -f nextjs

# 重新构建
docker-compose up -d --build
```

## 生产优化

### next.config.js

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // 自托管的 standalone 模式
  output: 'standalone',

  // 图片优化
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'cdn.example.com',
        pathname: '/images/**',
      },
    ],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // 压缩
  compress: true,

  // 安全头
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
        ],
      },
    ]
  },

  // 实验性功能
  experimental: {
    optimizePackageImports: ['@mui/material', 'lodash'],
  },

  // 包分析器
  webpack: (config, { isServer }) => {
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer')
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: isServer
            ? '../analyze/server.html'
            : './analyze/client.html',
        })
      )
    }
    return config
  },
}

module.exports = nextConfig
```

### 包分析

```bash
# 安装分析器
npm install -D @next/bundle-analyzer

# 分析
ANALYZE=true npm run build

# 或使用内置
npm run build -- --experimental-build-mode=compile
```

### 性能监控

```tsx
// app/layout.tsx
import { SpeedInsights } from '@vercel/speed-insights/next'
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <body>
        {children}
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  )
}
```

## CDN 与 Edge

### 静态资源 CDN

```js
// next.config.js
const nextConfig = {
  assetPrefix: process.env.NODE_ENV === 'production'
    ? 'https://cdn.example.com'
    : '',
}
```

### Edge Runtime

```tsx
// app/api/edge/route.ts
export const runtime = 'edge'

export async function GET(request: Request) {
  return new Response('Hello from Edge!', {
    status: 200,
    headers: {
      'content-type': 'text/plain',
    },
  })
}

// app/page.tsx
export const runtime = 'edge'

export default async function Page() {
  return <div>Edge-rendered page</div>
}
```

## 缓存策略

### ISR（增量静态再生成）

```tsx
// app/blog/[slug]/page.tsx
export const revalidate = 3600 // 每小时重新验证

export default async function BlogPost({ params }: { params: { slug: string } }) {
  const post = await fetchPost(params.slug)
  return <article>{post.content}</article>
}
```

### 按需 Revalidation

```tsx
// app/api/revalidate/route.ts
import { revalidatePath } from 'next/cache'
import { NextRequest } from 'next/server'

export async function POST(request: NextRequest) {
  const secret = request.nextUrl.searchParams.get('secret')

  if (secret !== process.env.REVALIDATE_SECRET) {
    return Response.json({ message: 'Invalid secret' }, { status: 401 })
  }

  const path = request.nextUrl.searchParams.get('path') || '/'

  revalidatePath(path)

  return Response.json({ revalidated: true, now: Date.now() })
}
```

## 数据库连接池

```ts
// lib/db.ts
import { PrismaClient } from '@prisma/client'

const globalForPrisma = global as unknown as {
  prisma: PrismaClient | undefined
}

export const db =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  })

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db
```

## 健康检查端点

```tsx
// app/api/health/route.ts
import { db } from '@/lib/db'

export async function GET() {
  try {
    // 检查数据库连接
    await db.$queryRaw`SELECT 1`

    return Response.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
    })
  } catch (error) {
    return Response.json(
      {
        status: 'error',
        message: 'Database connection failed',
      },
      { status: 503 }
    )
  }
}
```

## 使用 GitHub Actions 的 CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          NEXTAUTH_SECRET: ${{ secrets.NEXTAUTH_SECRET }}

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

## 监控与日志

```tsx
// app/error.tsx
'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'

export default function Error({
  error,
}: {
  error: Error & { digest?: string }
}) {
  useEffect(() => {
    Sentry.captureException(error)
  }, [error])

  return <div>Something went wrong!</div>
}
```

## 快速参考

| 平台 | 最适用场景 | 难度 |
|----------|----------|--------|
| **Vercel** | 零配置、最佳性能 | 低 |
| **Netlify** | Vercel 的替代方案 | 低 |
| **Railway** | 简单托管加数据库 | 中 |
| **AWS/GCP** | 企业级、自定义需求 | 高 |
| **Docker** | 自托管、完全控制 | 高 |

## 生产检查清单

- [ ] 启用 TypeScript strict 模式
- [ ] 配置 CSP 头
- [ ] 设置错误监控（Sentry）
- [ ] 配置分析（Vercel/GA）
- [ ] 优化图片（next/image）
- [ ] 启用压缩
- [ ] 为静态资源设置 CDN
- [ ] 配置数据库连接池
- [ ] 添加健康检查端点
- [ ] 设置 CI/CD 管道
- [ ] 配置环境变量
- [ ] 尽可能启用 ISR/SSG
- [ ] 测试 Core Web Vitals
- [ ] 设置日志（Datadog/LogRocket）
- [ ] 配置备份策略
