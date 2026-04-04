# GoRouter 导航

## 基本设置

```dart
import 'package:go_router/go_router.dart';

final goRouter = GoRouter(
  initialLocation: '/',
  redirect: (context, state) {
    final isLoggedIn = /* 检查认证 */;
    if (!isLoggedIn && !state.matchedLocation.startsWith('/auth')) {
      return '/auth/login';
    }
    return null;
  },
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'details/:id',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return DetailsScreen(id: id);
          },
        ),
      ],
    ),
    GoRoute(
      path: '/auth/login',
      builder: (context, state) => const LoginScreen(),
    ),
  ],
);

// 在 app.dart 中
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      routerConfig: goRouter,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
    );
  }
}
```

## 导航方法

```dart
// 导航并替换历史记录
context.go('/details/123');

// 导航并添加到堆栈
context.push('/details/123');

// 返回
context.pop();

// 替换当前路由
context.pushReplacement('/home');

// 带额外数据的导航
context.push('/details/123', extra: {'title': 'Item'});

// 在目标访问额外数据
final extra = GoRouterState.of(context).extra as Map<String, dynamic>?;
```

## Shell 路由（持久化 UI）

```dart
final goRouter = GoRouter(
  routes: [
    ShellRoute(
      builder: (context, state, child) {
        return ScaffoldWithNavBar(child: child);
      },
      routes: [
        GoRoute(path: '/home', builder: (_, __) => const HomeScreen()),
        GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
        GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
      ],
    ),
  ],
);
```

## 查询参数

```dart
GoRoute(
  path: '/search',
  builder: (context, state) {
    final query = state.uri.queryParameters['q'] ?? '';
    final page = int.tryParse(state.uri.queryParameters['page'] ?? '1') ?? 1;
    return SearchScreen(query: query, page: page);
  },
),

// 带查询参数导航
context.go('/search?q=flutter&page=2');
```

## 快速参考

| 方法 | 行为 |
|--------|----------|
| `context.go()` | 导航，替换堆栈 |
| `context.push()` | 导航，添加到堆栈 |
| `context.pop()` | 返回 |
| `context.pushReplacement()` | 替换当前 |
| `:param` | 路径参数 |
| `?key=value` | 查询参数 |
