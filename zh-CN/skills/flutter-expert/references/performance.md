# 性能优化

## 性能分析命令

```bash
# 在 profile 模式下运行
flutter run --profile

# 分析性能
flutter analyze

# DevTools
flutter pub global activate devtools
flutter pub global run devtools
```

## 常见优化

### Const Widgets
```dart
// ❌ 每次都重建
Widget build(BuildContext context) {
  return Container(
    padding: EdgeInsets.all(16),  // 创建新对象
    child: Text('Hello'),
  );
}

// ✅ const 防止重建
Widget build(BuildContext context) {
  return Container(
    padding: const EdgeInsets.all(16),
    child: const Text('Hello'),
  );
}
```

### 选择性 Provider 监听
```dart
// ❌ 任何用户更改都会重建
final user = ref.watch(userProvider);
return Text(user.name);

// ✅ 只在 name 更改时重建
final name = ref.watch(userProvider.select((u) => u.name));
return Text(name);
```

### RepaintBoundary
```dart
// 隔离昂贵的 widget
RepaintBoundary(
  child: ComplexAnimatedWidget(),
)
```

### 图片优化
```dart
// 使用 cached_network_image
CachedNetworkImage(
  imageUrl: url,
  placeholder: (_, __) => const CircularProgressIndicator(),
  errorWidget: (_, __, ___) => const Icon(Icons.error),
)

// 调整图片大小
Image.network(
  url,
  cacheWidth: 200,  // 在内存中调整大小
  cacheHeight: 200,
)
```

### Compute 用于繁重操作
```dart
// ❌ 阻塞 UI 线程
final result = heavyComputation(data);

// ✅ 在 isolate 中运行
final result = await compute(heavyComputation, data);
```

## 性能检查清单

| 检查项 | 解决方案 |
|-------|----------|
| 不必要的重建 | 添加 `const`，使用 `select()` |
| 大列表 | 使用 `ListView.builder` |
| 图片加载 | 使用 `cached_network_image` |
| 繁重计算 | 使用 `compute()` |
| 动画卡顿 | 使用 `RepaintBoundary` |
| 内存泄漏 | 释放控制器 |

## DevTools 指标

- **帧渲染时间**：60fps 需要 < 16ms
- **Widget 重建**：最小化不必要的重建
- **内存使用**：注意泄漏
- **CPU 分析器**：识别瓶颈
