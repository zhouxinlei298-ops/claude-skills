# Expo Router

## 项目结构

```
app/
├── _layout.tsx           # 根布局
├── index.tsx             # 首页 (/)
├── +not-found.tsx        # 404 页面
├── (tabs)/               # 标签页组
│   ├── _layout.tsx       # 标签栏配置
│   ├── index.tsx         # 第一个标签页
│   └── profile.tsx       # 个人资料标签页
├── (auth)/               # 认证组（无标签页）
│   ├── _layout.tsx
│   ├── login.tsx
│   └── register.tsx
├── settings/
│   ├── _layout.tsx       # 堆栈布局
│   ├── index.tsx         # 设置主页
│   └── notifications.tsx
└── details/[id].tsx      # 动态路由
```

## 根布局

```typescript
// app/_layout.tsx
import { Stack } from 'expo-router';
import { ThemeProvider } from '@react-navigation/native';

export default function RootLayout() {
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen
          name="details/[id]"
          options={{ presentation: 'modal' }}
        />
      </Stack>
    </ThemeProvider>
  );
}
```

## 标签页布局

```typescript
// app/(tabs)/_layout.tsx
import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#007AFF',
        headerShown: true,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home" color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person" color={color} size={size} />
          ),
        }}
      />
    </Tabs>
  );
}
```

## 导航

```typescript
import { router, useLocalSearchParams, Link } from 'expo-router';

// 程序化导航
router.push('/details/123');           // 推入堆栈
router.replace('/home');               // 替换当前页面
router.back();                          // 返回
router.canGoBack();                     // 检查是否可以返回

// 带参数
router.push({
  pathname: '/details/[id]',
  params: { id: '123', title: 'Item' },
});

// Link 组件
<Link href="/profile" asChild>
  <Pressable>
    <Text>Go to Profile</Text>
  </Pressable>
</Link>

// 读取参数
function DetailsScreen() {
  const { id, title } = useLocalSearchParams<{ id: string; title?: string }>();
  return <Text>Details for {id}</Text>;
}
```

## 受保护路由

```typescript
// app/(auth)/_layout.tsx
import { Redirect, Stack } from 'expo-router';
import { useAuth } from '@/hooks/useAuth';

export default function AuthLayout() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (user) {
    return <Redirect href="/(tabs)" />;
  }

  return <Stack screenOptions={{ headerShown: false }} />;
}

// app/(tabs)/_layout.tsx
export default function TabLayout() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Redirect href="/(auth)/login" />;
  }

  return <Tabs>...</Tabs>;
}
```

## 深度链接

```json
// app.json
{
  "expo": {
    "scheme": "myapp",
    "web": {
      "bundler": "metro"
    }
  }
}
```

```typescript
// 处理：myapp://details/123
// app/details/[id].tsx 自动处理
```

## 快速参考

| 组件 | 用途 |
|-----------|---------|
| `<Stack>` | 堆栈导航器 |
| `<Tabs>` | 标签页导航器 |
| `<Drawer>` | 抽屉导航器 |
| `<Link>` | 声明式导航 |

| router 方法 | 行为 |
|---------------|----------|
| `push()` | 添加到堆栈 |
| `replace()` | 替换当前页面 |
| `back()` | 返回 |
| `dismissAll()` | 关闭所有模态框 |
