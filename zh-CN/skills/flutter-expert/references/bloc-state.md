# Bloc 状态管理

## 何时使用 Bloc

使用 **Bloc/Cubit** 当你需要：

* 明确的事件 → 状态转换
* 复杂的业务逻辑
* 可预测、可测试的流程
* UI 和逻辑的清晰分离

| 使用场景               | 推荐 |
| ---------------------- | ----------- |
| 简单可变状态   | Riverpod    |
| 事件驱动的工作流 | Bloc        |
| 表单、认证、向导   | Bloc        |
| 功能模块        | Bloc        |

---

## 核心概念

| 概念 | 描述            |
| ------- | ---------------------- |
| Event   | 用户/系统输入      |
| State   | 不可变 UI 状态     |
| Bloc    | Event → State 映射器   |
| Cubit   | 仅 State（无 events） |

---

## 基本 Bloc 设置

### Event

```dart
sealed class CounterEvent {}

final class CounterIncremented extends CounterEvent {}

final class CounterDecremented extends CounterEvent {}
```

### State

```dart
class CounterState {
  final int value;

  const CounterState({required this.value});

  CounterState copyWith({int? value}) {
    return CounterState(value: value ?? this.value);
  }
}
```

### Bloc

```dart
import 'package:flutter_bloc/flutter_bloc.dart';

class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(const CounterState(value: 0)) {
    on<CounterIncremented>((event, emit) {
      emit(state.copyWith(value: state.value + 1));
    });

    on<CounterDecremented>((event, emit) {
      emit(state.copyWith(value: state.value - 1));
    });
  }
}
```

---

## Cubit（推荐用于更简单的逻辑）

```dart
class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
}
```

---

## 将 Bloc 提供给 Widget 树

```dart
BlocProvider(
  create: (_) => CounterBloc(),
  child: const CounterScreen(),
);
```

多个 blocs：

```dart
MultiBlocProvider(
  providers: [
    BlocProvider(create: (_) => AuthBloc()),
    BlocProvider(create: (_) => ProfileBloc()),
  ],
  child: const AppRoot(),
);
```

---

## 在 Widget 中使用 Bloc

### BlocBuilder（UI 重建）

```dart
class CounterScreen extends StatelessWidget {
  const CounterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<CounterBloc, CounterState>(
      buildWhen: (prev, curr) => prev.value != curr.value,
      builder: (context, state) {
        return Text(
          state.value.toString(),
          style: Theme.of(context).textTheme.displayLarge,
        );
      },
    );
  }
}
```

---

### BlocListener（副作用）

```dart
BlocListener<AuthBloc, AuthState>(
  listenWhen: (prev, curr) => curr is AuthFailure,
  listener: (context, state) {
    if (state is AuthFailure) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(state.message)));
    }
  },
  child: const LoginForm(),
);
```

---

### BlocConsumer（Builder + Listener）

```dart
BlocConsumer<FormBloc, FormState>(
  listener: (context, state) {
    if (state.status == FormStatus.success) {
      context.pop();
    }
  },
  builder: (context, state) {
    return ElevatedButton(
      onPressed: state.isValid
          ? () => context.read<FormBloc>().add(FormSubmitted())
          : null,
      child: const Text('Submit'),
    );
  },
);
```

---

## 在不重建的情况下访问 Bloc

```dart
context.read<CounterBloc>().add(CounterIncremented());
```

⚠️ **永远不要在回调中使用 `watch`**

---

## 异步 Bloc 模式（API 调用）

```dart
on<UserRequested>((event, emit) async {
  emit(const UserState.loading());

  try {
    final user = await repository.fetchUser();
    emit(UserState.success(user));
  } catch (e) {
    emit(UserState.failure(e.toString()));
  }
});
```

---

## Bloc + GoRouter（认证守卫示例）

```dart
redirect: (context, state) {
  final authState = context.read<AuthBloc>().state;

  if (authState is Unauthenticated) {
    return '/login';
  }
  return null;
}
```

---

## 测试 Bloc

```dart
blocTest<CounterBloc, CounterState>(
  'emits incremented value',
  build: () => CounterBloc(),
  act: (bloc) => bloc.add(CounterIncremented()),
  expect: () => [
    const CounterState(value: 1),
  ],
);
```

---

## 最佳实践（必须遵循）

✅ 不可变状态
✅ 小而专注的 blocs
✅ 一个功能 = 一个 bloc
✅ 尽可能使用 Cubit
✅ 测试所有 blocs

❌ 在 bloc 中有 UI 逻辑
❌ 在 bloc 中使用 context
❌ 可变状态
❌ 巨大的"上帝 blocs"

---

## 快速参考

| Widget            | 用途              |
| ----------------- | -------------------- |
| BlocBuilder       | UI 重建           |
| BlocListener      | 副作用         |
| BlocConsumer      | 两者都包含                 |
| BlocProvider      | 依赖注入 |
| MultiBlocProvider | 多个 blocs       |
