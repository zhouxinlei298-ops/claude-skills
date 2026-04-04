# 快速修复

## TypeError: Cannot read property 'x' of undefined

```typescript
// Error
user.profile.name
// user or profile is undefined

// Fix: Optional chaining
user?.profile?.name

// Fix: Default value
user?.profile?.name ?? 'Unknown'

// Fix: Guard clause
if (!user?.profile) {
  return null;
}
return user.profile.name;
```

## 未处理的 Promise 拒绝

```typescript
// Error
fetchData().then(process);
// What if fetchData rejects?

// Fix: Add catch
fetchData()
  .then(process)
  .catch(error => {
    console.error('Fetch failed:', error);
  });

// Fix: try/catch with await
try {
  const data = await fetchData();
  await process(data);
} catch (error) {
  console.error('Operation failed:', error);
}
```

## React: 渲染次数过多

```typescript
// Error: Calling setState during render
function Component() {
  const [count, setCount] = useState(0);
  setCount(count + 1); // Infinite loop!
}

// Fix: Use useEffect for side effects
function Component() {
  const [count, setCount] = useState(0);
  useEffect(() => {
    setCount(c => c + 1);
  }, []); // Only on mount
}

// Error: Object/array in dependency array
useEffect(() => {}, [{ a: 1 }]); // New object every render!

// Fix: Memoize or use primitives
const config = useMemo(() => ({ a: 1 }), []);
useEffect(() => {}, [config]);
```

## CORS 错误

```typescript
// Browser blocks cross-origin request

// Fix 1: Server - Add CORS headers
app.use(cors({
  origin: 'http://localhost:3000',
  credentials: true,
}));

// Fix 2: Proxy in development (Vite)
// vite.config.ts
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
};
```

## 超出最大调用堆栈大小

```typescript
// Error: Infinite recursion
function factorial(n) {
  return n * factorial(n - 1); // No base case!
}

// Fix: Add base case
function factorial(n) {
  if (n <= 1) return 1;
  return n * factorial(n - 1);
}

// Error: Circular dependency in objects
const a = {};
const b = { ref: a };
a.ref = b;
JSON.stringify(a); // Fails!

// Fix: Break circular reference
JSON.stringify(a, (key, value) => {
  if (key === 'ref') return '[Circular]';
  return value;
});
```

## 模块未找到

```bash
# Error: Cannot find module 'x'

# Fix 1: Install the package
npm install x

# Fix 2: Check import path
import x from './x';     # Relative - needs ./
import x from 'x';       # Package - no ./

# Fix 3: Check file extension
import x from './x.js';  # ESM may need extension

# Fix 4: Clear cache
rm -rf node_modules package-lock.json
npm install
```

## Async/Await 问题

```typescript
// Error: await in non-async function
function getData() {
  const data = await fetch('/api'); // SyntaxError!
}

// Fix: Mark function as async
async function getData() {
  const data = await fetch('/api');
}

// Error: forEach doesn't await
items.forEach(async item => {
  await process(item); // Doesn't wait!
});

// Fix: Use for...of
for (const item of items) {
  await process(item);
}

// Fix: Use Promise.all for parallel
await Promise.all(items.map(item => process(item)));
```

## 快速参考

| 错误消息 | 可能的修复 |
|----------|------------|
| Cannot read property of undefined | 可选链 `?.` |
| Unhandled promise rejection | 添加 `.catch()` 或 try/catch |
| Too many re-renders | 从渲染中移除 setState |
| CORS error | 服务器上添加 CORS 头 |
| Maximum call stack | 添加递归基本情况 |
| Module not found | 检查路径，安装包 |
| await in non-async | 添加 `async` 关键字 |