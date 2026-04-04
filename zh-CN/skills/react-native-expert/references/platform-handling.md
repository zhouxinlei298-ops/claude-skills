# 平台处理

## Platform.select

```typescript
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#fff',
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  text: {
    fontFamily: Platform.select({
      ios: 'Helvetica Neue',
      android: 'Roboto',
    }),
  },
});
```

## Platform.OS

```typescript
import { Platform } from 'react-native';

function MyComponent() {
  const isIOS = Platform.OS === 'ios';
  const isAndroid = Platform.OS === 'android';

  return (
    <View>
      {isIOS && <IOSOnlyComponent />}
      <Text>{isAndroid ? 'Android' : 'iOS'}</Text>
    </View>
  );
}
```

## 平台特定文件

```
components/
├── Button.tsx           # 共享逻辑
├── Button.ios.tsx       # iOS 特定
└── Button.android.tsx   # Android 特定
```

```typescript
// 导入会解析到正确的平台文件
import Button from './components/Button';
```

## SafeAreaView

```typescript
import { SafeAreaView, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// 方法 1: SafeAreaView 组件
function Screen() {
  return (
    <SafeAreaView style={styles.container}>
      <Content />
    </SafeAreaView>
  );
}

// 方法 2: useSafeAreaInsets hook（更多控制）
function CustomHeader() {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.header, { paddingTop: insets.top }]}>
      <Text>Header</Text>
    </View>
  );
}

// 方法 3: SafeAreaProvider context
import { SafeAreaProvider } from 'react-native-safe-area-context';

function App() {
  return (
    <SafeAreaProvider>
      <Navigation />
    </SafeAreaProvider>
  );
}
```

## KeyboardAvoidingView

```typescript
import { KeyboardAvoidingView, Platform } from 'react-native';

function FormScreen() {
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
      keyboardVerticalOffset={Platform.select({ ios: 88, android: 0 })}
    >
      <ScrollView>
        <TextInput placeholder="Name" />
        <TextInput placeholder="Email" />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
```

## StatusBar

```typescript
import { StatusBar, Platform } from 'react-native';

function Screen() {
  return (
    <>
      <StatusBar
        barStyle={Platform.OS === 'ios' ? 'dark-content' : 'light-content'}
        backgroundColor={Platform.OS === 'android' ? '#000' : undefined}
      />
      <Content />
    </>
  );
}
```

## Android 返回按钮

```typescript
import { useEffect } from 'react';
import { BackHandler, Platform } from 'react-native';

function useBackHandler(handler: () => boolean) {
  useEffect(() => {
    if (Platform.OS !== 'android') return;

    const subscription = BackHandler.addEventListener(
      'hardwareBackPress',
      handler
    );

    return () => subscription.remove();
  }, [handler]);
}

// 使用
function Screen() {
  useBackHandler(() => {
    if (hasUnsavedChanges) {
      showDiscardAlert();
      return true; // 阻止默认返回
    }
    return false; // 允许默认返回
  });
}
```

## 快速参考

| API | 用途 |
|-----|---------|
| `Platform.OS` | 获取平台 ('ios' / 'android') |
| `Platform.select()` | 平台特定值 |
| `Platform.Version` | 操作系统版本号 |
| `.ios.tsx` / `.android.tsx` | 平台特定文件 |

| 组件 | 用途 |
|-----------|---------|
| `SafeAreaView` | 避开刘海/指示器 |
| `KeyboardAvoidingView` | 键盘处理 |
| `StatusBar` | 状态栏样式 |
| `BackHandler` | Android 返回按钮 |
