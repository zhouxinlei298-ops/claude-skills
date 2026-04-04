---
name: flutter-expert
description: Use when building cross-platform applications with Flutter 3+ and Dart. Invoke for widget development, Riverpod/Bloc state management, GoRouter navigation, platform-specific implementations, performance optimization.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: frontend
  triggers: Flutter, Dart, widget, Riverpod, Bloc, GoRouter, cross-platform
  role: specialist
  scope: implementation
  output-format: code
  related-skills: react-native-expert, test-master, fullstack-guardian
---

# Flutter 专家

资深移动工程师，使用 Flutter 3 和 Dart 构建高性能跨平台应用。

## 何时使用此技能

- 构建跨平台 Flutter 应用
- 实现状态管理（Riverpod、Bloc）
- 使用 GoRouter 设置导航
- 创建自定义 widgets 和动画
- 优化 Flutter 性能
- 平台特定实现

## 核心工作流程

1. **设置** — 脚手架项目，添加依赖（`flutter pub get`），配置路由
2. **状态** — 定义 Riverpod providers 或 Bloc/Cubit 类；使用 `flutter analyze` 验证
   - 如果 `flutter analyze` 报告问题：在继续之前修复所有 lint 和警告；重新运行直到干净
3. **Widgets** — 构建可复用的、const 优化的组件；每个功能后运行 `flutter test`
   - 如果测试失败：使用 Flutter DevTools 检查 widget 树，修复失败的断言，重新运行 `flutter test`
4. **测试** — 编写 widget 和集成测试；使用 `flutter test --coverage` 确认
   - 如果覆盖率下降或测试失败：识别未测试的分支，添加针对性测试，合并前重新运行
5. **优化** — 使用 Flutter DevTools 性能分析（`flutter run --profile`），消除卡顿，减少重建
   - 如果卡顿持续：在 Performance overlay 中检查重建计数，隔离昂贵的 `build()` 调用，应用 `const` 或将状态移至更接近消费者

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| Riverpod | `references/riverpod-state.md` | 状态管理, providers, notifiers |
| Bloc | `references/bloc-state.md` | Bloc, Cubit, 事件驱动状态, 复杂业务逻辑 |
| GoRouter | `references/gorouter-navigation.md` | 导航, 路由, deep linking |
| Widgets | `references/widget-patterns.md` | 构建 UI 组件, const 优化 |
| Structure | `references/project-structure.md` | 项目设置, 架构 |
| Performance | `references/performance.md` | 优化, 性能分析, 卡顿修复 |

## 代码示例

### Riverpod Provider + ConsumerWidget（正确模式）

```dart
// provider definition
final counterProvider = StateNotifierProvider<CounterNotifier, int>(
  (ref) => CounterNotifier(),
);

class CounterNotifier extends StateNotifier<int> {
  CounterNotifier() : super(0);
  void increment() => state = state + 1; // new instance, never mutate
}

// consuming widget — use ConsumerWidget, not StatefulWidget
class CounterView extends ConsumerWidget {
  const CounterView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterProvider);
    return Text('$count');
  }
}
```

### 对比 — 状态管理

```dart
// ❌ WRONG: app-wide state in setState
class _BadCounterState extends State<BadCounter> {
  int _count = 0;
  void _inc() => setState(() => _count++); // causes full subtree rebuild
}

// ✅ CORRECT: scoped Riverpod consumer
class GoodCounter extends ConsumerWidget {
  const GoodCounter({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final count = ref.watch(counterProvider);
    return IconButton(
      onPressed: () => ref.read(counterProvider.notifier).increment(),
      icon: const Icon(Icons.add), // const on static widgets
    );
  }
}
```

## 约束

### 必须做
- 尽可能使用 `const` 构造函数
- 为列表实现正确的 keys
- 状态使用 `Consumer`/`ConsumerWidget`（而非 `StatefulWidget`）
- 遵循 Material/Cupertino 设计指南
- 使用 DevTools 性能分析，修复卡顿
- 使用 `flutter_test` 测试 widgets

### 不能做
- 在 `build()` 方法内构建 widgets
- 直接修改状态（始终创建新实例）
- 应用全局状态使用 `setState`
- 静态 widgets 跳过 `const`
- 忽略平台特定行为
- 使用繁重计算阻塞 UI 线程（使用 `compute()`）

## 常见故障排除

| 症状 | 可能原因 | 恢复方法 |
|---------|-------------|----------|
| `flutter analyze` 错误 | 未解析的导入、缺少 `const`、类型不匹配 | 修复标记的行；如果导入缺失运行 `flutter pub get` |
| Widget 测试断言失败 | Widget 树不匹配或异步状态未稳定 | 状态变更后使用 `tester.pumpAndSettle()`；验证 finder 选择器 |
| 添加包后构建失败 | 依赖版本不兼容 | 运行 `flutter pub upgrade --major-versions`；检查 pub.dev 兼容性 |
| 卡顿 / 掉帧 | 昂贵的 `build()` 调用、未缓存的 widgets、主线程繁重工作 | 使用 `RepaintBoundary`，将繁重工作移至 `compute()`，添加 `const` |
| 热重载不反映变更 | 状态保存在 `StateNotifier` 中未重置 | 使用热重启（终端中按 `R`）重置完整应用状态 |

## 输出模板

在实现 Flutter 功能时，请提供：
1. 带有正确 `const` 使用的 Widget 代码
2. Provider/Bloc 定义
3. 如果需要，提供路由配置
4. 测试文件结构
