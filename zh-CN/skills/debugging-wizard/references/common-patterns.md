# 常见错误模式

## 模式识别

| 模式 | 症状 | 可能原因 |
|------|------|----------|
| 竞态条件 | 间歇性失败 | 缺少 await、异步时序问题 |
| 差一错误 | 缺少第一个/最后一个元素 | `<` vs `<=`、数组边界 |
| 空引用 | "undefined is not..." | 缺少 null 检查 |
| 内存泄漏 | 内存持续增长 | 未清理的监听器/定时器 |
| N+1 查询 | 数据越多越慢 | 循环中获取数据 |
| 类型强制 | 意外行为 | `==` 而不是 `===` |
| 闭包问题 | 变量值错误 | 循环变量捕获 |
| 状态过期 | 使用旧值 | React 状态闭包 |

## 竞态条件

```typescript
// BUG: Race condition
let data;
fetchData().then(result => { data = result; });
console.log(data); // undefined!

// FIX: Await the result
const data = await fetchData();
console.log(data);
```

## 差一错误

```typescript
// BUG: Skips last element
for (let i = 0; i < array.length - 1; i++) { }

// FIX: Include last element
for (let i = 0; i < array.length; i++) { }

// BUG: Array index out of bounds
const last = array[array.length]; // undefined

// FIX: Correct index
const last = array[array.length - 1];
```

## 空引用

```typescript
// BUG: Crashes if user is null
const name = user.profile.name;

// FIX: Optional chaining
const name = user?.profile?.name ?? 'Unknown';

// FIX: Guard clause
if (!user?.profile) {
  return 'Unknown';
}
return user.profile.name;
```

## 内存泄漏

```typescript
// BUG: Listener never removed
useEffect(() => {
  window.addEventListener('resize', handleResize);
}, []);

// FIX: Cleanup function
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);

// BUG: Interval never cleared
setInterval(pollData, 1000);

// FIX: Store and clear
const intervalId = setInterval(pollData, 1000);
return () => clearInterval(intervalId);
```

## 循环中的闭包

```typescript
// BUG: All callbacks use i = 5
for (var i = 0; i < 5; i++) {
  setTimeout(() => console.log(i), 100);
}

// FIX: Use let (block scoped)
for (let i = 0; i < 5; i++) {
  setTimeout(() => console.log(i), 100);
}

// FIX: Capture in closure
for (var i = 0; i < 5; i++) {
  ((j) => setTimeout(() => console.log(j), 100))(i);
}
```

## React 状态过期

```typescript
// BUG: count is stale in closure
const [count, setCount] = useState(0);
useEffect(() => {
  setInterval(() => {
    setCount(count + 1); // Always uses initial count
  }, 1000);
}, []);

// FIX: Use functional update
setCount(prev => prev + 1);

// FIX: Include in dependency array with cleanup
useEffect(() => {
  const id = setInterval(() => setCount(c => c + 1), 1000);
  return () => clearInterval(id);
}, []);
```

## 快速参考

| 症状 | 首先检查 |
|------|----------|
| "undefined is not..." | 缺少 null 检查 |
| 有时工作 | 竞态条件 |
| 回调中值错误 | 闭包/状态过期 |
| 随时间变慢 | 内存泄漏、N+1 |
| 差一个项目 | 循环边界、数组索引 |
| 类型不匹配 | `==` vs `===`、强制类型转换 |