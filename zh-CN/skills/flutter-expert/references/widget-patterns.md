# Widget 模式

## 优化的 Widget 模式

```dart
// 使用 const 构造函数
class OptimizedCard extends StatelessWidget {
  final String title;
  final VoidCallback onTap;

  const OptimizedCard({
    super.key,
    required this.title,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text(title, style: Theme.of(context).textTheme.titleMedium),
        ),
      ),
    );
  }
}
```

## 响应式布局

```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget? tablet;
  final Widget desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    this.tablet,
    required this.desktop,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1100) return desktop;
        if (constraints.maxWidth >= 650) return tablet ?? mobile;
        return mobile;
      },
    );
  }
}
```

## 自定义 Hooks (flutter_hooks)

```dart
import 'package:flutter_hooks/flutter_hooks.dart';

class CounterWidget extends HookWidget {
  @override
  Widget build(BuildContext context) {
    final counter = useState(0);
    final controller = useTextEditingController();

    useEffect(() {
      // 设置
      return () {
        // 清理
      };
    }, []);

    return Column(
      children: [
        Text('Count: ${counter.value}'),
        ElevatedButton(
          onPressed: () => counter.value++,
          child: const Text('Increment'),
        ),
      ],
    );
  }
}
```

## Sliver 模式

```dart
CustomScrollView(
  slivers: [
    SliverAppBar(
      expandedHeight: 200,
      pinned: true,
      flexibleSpace: FlexibleSpaceBar(
        title: const Text('Title'),
        background: Image.network(imageUrl, fit: BoxFit.cover),
      ),
    ),
    SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) => ListTile(title: Text('Item $index')),
        childCount: 100,
      ),
    ),
  ],
)
```

## 关键优化模式

| 模式 | 实现 |
|---------|----------------|
| **const widgets** | 为静态 widget 添加 `const` |
| **keys** | 为列表项使用 `Key` |
| **select** | `ref.watch(provider.select(...))` |
| **RepaintBoundary** | 隔离昂贵的重绘 |
| **ListView.builder** | 列表的懒加载 |
| **const constructors** | 尽可能始终使用 |
