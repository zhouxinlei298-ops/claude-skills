---
name: react-native-expert
description: Builds, optimizes, and debugs cross-platform mobile applications with React Native and Expo. Implements navigation hierarchies (tabs, stacks, drawers), configures native modules, optimizes FlatList rendering with memo and useCallback, and handles platform-specific code for iOS and Android. Use when building a React Native or Expo mobile app, setting up navigation, integrating native modules, improving scroll performance, handling SafeArea or keyboard input, or configuring Expo SDK projects.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: frontend
  triggers: React Native, Expo, mobile app, iOS, Android, cross-platform, native module
  role: specialist
  scope: implementation
  output-format: code
  related-skills: react-expert, flutter-expert, test-master
---

# React Native 专家

资深移动工程师，使用 React Native 和 Expo 构建生产就绪的跨平台应用。

## 核心工作流程

1. **设置** — Expo Router 或 React Navigation, TypeScript 配置 → _运行 `npx expo doctor` 验证环境和 SDK 兼容性；修复任何报告的问题后再继续_
2. **结构** — 基于功能的组织
3. **实现** — 带平台处理的组件 → _在 iOS 模拟器和 Android 模拟器上验证；检查 Metro bundler 输出的错误后再继续_
4. **优化** — FlatList, 图片, 内存 → _使用 Flipper 或 React DevTools 进行性能分析_
5. **测试** — 两个平台，真机测试

### 错误恢复
- **Metro bundler 错误** → 使用 `npx expo start --clear` 清除缓存，然后重启
- **iOS 构建失败** → 检查 Xcode 日志 → 解决原生依赖或签名问题 → 使用 `npx expo run:ios` 重新构建
- **Android 构建失败** → 检查 `adb logcat` 或 Gradle 输出 → 解决 SDK/NDK 版本不匹配 → 使用 `npx expo run:android` 重新构建
- **原生模块未找到** → 运行 `npx expo install <module>` 确保兼容版本，然后重新构建原生层

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| Navigation | `references/expo-router.md` | Expo Router, tabs, stacks, deep linking |
| 平台 | `references/platform-handling.md` | iOS/Android 代码, SafeArea, 键盘 |
| Lists | `references/list-optimization.md` | FlatList, 性能, memo |
| Storage | `references/storage-hooks.md` | AsyncStorage, MMKV, 持久化 |
| Structure | `references/project-structure.md` | 项目设置, 架构 |

## 约束

### 必须做
- 列表使用 FlatList/SectionList（而非 ScrollView）
- 列表项实现 memo + useCallback
- 处理 SafeAreaView 适配刘海屏
- 在 iOS 和 Android 真机上测试
- 表单使用 KeyboardAvoidingView
- 导航中处理 Android 返回按钮

### 不能做
- 大列表使用 ScrollView
- 大量使用内联样式（创建新对象）
- 硬编码尺寸（使用 Dimensions API 或 flex）
- 忽略订阅导致的内存泄漏
- 跳过平台特定测试
- 动画使用 waitFor/setTimeout（使用 Reanimated）

## 代码示例

### 使用 memo + useCallback 优化的 FlatList

```tsx
import React, { memo, useCallback } from 'react';
import { FlatList, View, Text, StyleSheet } from 'react-native';

type Item = { id: string; title: string };

const ListItem = memo(({ title, onPress }: { title: string; onPress: () => void }) => (
  <View style={styles.item}>
    <Text onPress={onPress}>{title}</Text>
  </View>
));

export function ItemList({ data }: { data: Item[] }) {
  const handlePress = useCallback((id: string) => {
    console.log('pressed', id);
  }, []);

  const renderItem = useCallback(
    ({ item }: { item: Item }) => (
      <ListItem title={item.title} onPress={() => handlePress(item.id)} />
    ),
    [handlePress]
  );

  return (
    <FlatList
      data={data}
      keyExtractor={(item) => item.id}
      renderItem={renderItem}
      removeClippedSubviews
      maxToRenderPerBatch={10}
      windowSize={5}
    />
  );
}

const styles = StyleSheet.create({
  item: { padding: 16, borderBottomWidth: StyleSheet.hairlineWidth },
});
```

### KeyboardAvoidingView 表单

```tsx
import React from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TextInput,
  StyleSheet,
  SafeAreaView,
} from 'react-native';

export function LoginForm() {
  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <TextInput style={styles.input} placeholder="Email" autoCapitalize="none" />
          <TextInput style={styles.input} placeholder="Password" secureTextEntry />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  flex: { flex: 1 },
  content: { padding: 16, gap: 12 },
  input: { borderWidth: 1, borderRadius: 8, padding: 12, fontSize: 16 },
});
```

### 平台特定组件

```tsx
import { Platform, StyleSheet, View, Text } from 'react-native';

export function StatusChip({ label }: { label: string }) {
  return (
    <View style={styles.chip}>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: '#0a7ea4',
    // 平台特定的阴影
    ...Platform.select({
      ios: { shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.2, shadowRadius: 4 },
      android: { elevation: 3 },
    }),
  },
  label: { color: '#fff', fontSize: 13, fontWeight: '600' },
});
```

## 输出格式

在实现 React Native 功能时，交付：
1. **组件代码** — TypeScript，定义了 prop 类型
2. **平台处理** — 根据需要使用 `Platform.select` 或 `.ios.tsx` / `.android.tsx` 分割
3. **导航集成** — 路由参数类型化，包含返回按钮处理
4. **性能说明** — memo 边界，key extractor 策略，图片缓存

## 知识参考

React Native 0.73+, Expo SDK 50+, Expo Router, React Navigation 7, Reanimated 3, Gesture Handler, AsyncStorage, MMKV, React Query, Zustand
