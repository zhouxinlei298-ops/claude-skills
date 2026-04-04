# 性能优化

## React.memo

```tsx
import { memo } from 'react';

// Memoize component - only re-renders when props change
const ExpensiveList = memo(function ExpensiveList({ items }: { items: Item[] }) {
  return (
    <ul>
      {items.map(item => <li key={item.id}>{item.name}</li>)}
    </ul>
  );
});

// Custom comparison function
const UserCard = memo(
  function UserCard({ user }: { user: User }) {
    return <div>{user.name}</div>;
  },
  (prevProps, nextProps) => prevProps.user.id === nextProps.user.id
);
```

## 防止重新渲染

```tsx
// Problem: New object/function on each render
function Parent() {
  // ❌ Creates new object every render
  return <Child style={{ color: 'red' }} onClick={() => doSomething()} />;
}

// Solution: Memoize or lift out
const style = { color: 'red' }; // Lifted out

function Parent() {
  const handleClick = useCallback(() => doSomething(), []);
  return <Child style={style} onClick={handleClick} />;
}
```

## 使用 lazy() 进行代码分割

```tsx
import { lazy, Suspense } from 'react';

// Split heavy components
const HeavyChart = lazy(() => import('./HeavyChart'));
const AdminPanel = lazy(() => import('./AdminPanel'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      {showChart && <HeavyChart data={data} />}
    </Suspense>
  );
}

// Route-based splitting (React Router)
const routes = [
  {
    path: '/admin',
    element: (
      <Suspense fallback={<Loading />}>
        <AdminPanel />
      </Suspense>
    ),
  },
];
```

## 虚拟化

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: virtualItem.start,
              height: virtualItem.size,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## useMemo 用于昂贵的计算

```tsx
function Analytics({ data }: { data: DataPoint[] }) {
  // Only recalculate when data changes
  const stats = useMemo(() => ({
    total: data.reduce((sum, d) => sum + d.value, 0),
    average: data.reduce((sum, d) => sum + d.value, 0) / data.length,
    max: Math.max(...data.map(d => d.value)),
  }), [data]);

  return <StatsDisplay stats={stats} />;
}
```

## useTransition 用于非紧急更新

```tsx
import { useTransition } from 'react';

function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Item[]>([]);
  const [isPending, startTransition] = useTransition();

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setQuery(e.target.value); // Urgent: update input immediately

    startTransition(() => {
      // Non-urgent: can be interrupted
      setResults(filterItems(e.target.value));
    });
  }

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <Results items={results} />}
    </>
  );
}
```

## 快速参考

| 技术 | 何时使用 |
|-----------|-------------|
| `memo()` | 防止 props 未变时的重新渲染 |
| `useMemo()` | 缓存昂贵的计算 |
| `useCallback()` | 稳定的函数引用 |
| `lazy()` | 代码分割重型组件 |
| `useTransition()` | 在更新期间保持 UI 响应 |
| Virtualization | 大列表（1000+ 项） |

| 反模式 | 修复方案 |
|--------------|----------|
| 内联对象 | 提取出来或使用 useMemo |
| 内联函数 | useCallback |
| 大包体积 | lazy() + Suspense |
| 长列表 | Virtualization |
