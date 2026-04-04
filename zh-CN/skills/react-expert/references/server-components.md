# Server Components

## Server 与 Client Components

```tsx
// Server Component (default in App Router)
// Can: fetch data, access backend, use async/await
// Cannot: use hooks, browser APIs, event handlers
async function ProductList() {
  const products = await db.products.findMany();
  return (
    <ul>
      {products.map(p => <ProductCard key={p.id} product={p} />)}
    </ul>
  );
}

// Client Component (explicit)
'use client';
import { useState } from 'react';

function AddToCartButton({ productId }: { productId: string }) {
  const [loading, setLoading] = useState(false);
  return (
    <button onClick={() => addToCart(productId)} disabled={loading}>
      Add to Cart
    </button>
  );
}
```

## 数据获取模式

```tsx
// app/products/page.tsx
export default async function ProductsPage() {
  // Runs on server only - no client bundle impact
  const products = await fetch('https://api.example.com/products', {
    next: { revalidate: 3600 } // Cache for 1 hour
  }).then(res => res.json());

  return <ProductGrid products={products} />;
}

// Parallel data fetching
async function Dashboard() {
  const [user, orders, recommendations] = await Promise.all([
    getUser(),
    getOrders(),
    getRecommendations(),
  ]);

  return (
    <>
      <UserHeader user={user} />
      <OrderList orders={orders} />
      <Recommendations items={recommendations} />
    </>
  );
}
```

## 使用 Suspense 进行流式渲染

```tsx
import { Suspense } from 'react';

async function SlowComponent() {
  const data = await slowFetch(); // 3 second API call
  return <div>{data}</div>;
}

export default function Page() {
  return (
    <main>
      <h1>Dashboard</h1>
      <FastComponent />

      <Suspense fallback={<Skeleton />}>
        <SlowComponent />
      </Suspense>
    </main>
  );
}
```

## 从 Server 传递数据到 Client

```tsx
// Server Component
async function ProductPage({ id }: { id: string }) {
  const product = await getProduct(id);

  // Pass serializable data to client
  return (
    <div>
      <h1>{product.name}</h1>
      {/* Client component receives serialized props */}
      <AddToCartButton productId={product.id} price={product.price} />
    </div>
  );
}
```

## Server Actions

```tsx
// actions.ts
'use server';

export async function createPost(formData: FormData) {
  const title = formData.get('title') as string;
  await db.posts.create({ data: { title } });
  revalidatePath('/posts');
}

// page.tsx (Server Component)
import { createPost } from './actions';

export default function NewPost() {
  return (
    <form action={createPost}>
      <input name="title" required />
      <button type="submit">Create</button>
    </form>
  );
}
```

## 快速参考

| 类型 | 可以使用 | 不能使用 |
|------|---------|------------|
| Server | async/await, db, fs | useState, onClick |
| Client | hooks, events, browser APIs | async component |

| 模式 | 用例 |
|---------|----------|
| Server Component | 数据获取、大型依赖 |
| Client Component | 交互性、状态 |
| `'use client'` | 标记 client 边界 |
| `'use server'` | Server Action |
| Suspense | 流式渲染、加载状态 |
