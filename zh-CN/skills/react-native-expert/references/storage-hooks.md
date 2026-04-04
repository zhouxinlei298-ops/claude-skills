# 存储与 Hooks

## AsyncStorage

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// 基本操作
await AsyncStorage.setItem('user', JSON.stringify(user));
const user = JSON.parse(await AsyncStorage.getItem('user') || 'null');
await AsyncStorage.removeItem('user');
await AsyncStorage.clear();

// 多个项
await AsyncStorage.multiSet([
  ['user', JSON.stringify(user)],
  ['settings', JSON.stringify(settings)],
]);

const values = await AsyncStorage.multiGet(['user', 'settings']);
```

## useStorage Hook

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useState, useEffect, useCallback } from 'react';

function useStorage<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(initialValue);
  const [loading, setLoading] = useState(true);

  // 挂载时加载
  useEffect(() => {
    AsyncStorage.getItem(key)
      .then((item) => {
        if (item !== null) {
          setValue(JSON.parse(item));
        }
      })
      .finally(() => setLoading(false));
  }, [key]);

  // 持久化更改
  const setStoredValue = useCallback(
    async (newValue: T | ((prev: T) => T)) => {
      const valueToStore =
        newValue instanceof Function ? newValue(value) : newValue;
      setValue(valueToStore);
      await AsyncStorage.setItem(key, JSON.stringify(valueToStore));
    },
    [key, value]
  );

  const removeValue = useCallback(async () => {
    setValue(initialValue);
    await AsyncStorage.removeItem(key);
  }, [key, initialValue]);

  return { value, setValue: setStoredValue, removeValue, loading };
}

// 使用
function Settings() {
  const { value: theme, setValue: setTheme, loading } = useStorage('theme', 'light');

  if (loading) return <Loading />;

  return (
    <Switch
      value={theme === 'dark'}
      onValueChange={(dark) => setTheme(dark ? 'dark' : 'light')}
    />
  );
}
```

## MMKV（更快的替代方案）

```typescript
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

// 同步操作
storage.set('user.name', 'John');
const name = storage.getString('user.name');

storage.set('user.age', 25);
const age = storage.getNumber('user.age');

storage.set('user.premium', true);
const isPremium = storage.getBoolean('user.premium');

storage.delete('user.name');
storage.clearAll();

// JSON 数据
storage.set('user', JSON.stringify(user));
const user = JSON.parse(storage.getString('user') || '{}');
```

## useMMKV Hook

```typescript
import { useMMKVString, useMMKVNumber, useMMKVBoolean } from 'react-native-mmkv';

function Settings() {
  const [theme, setTheme] = useMMKVString('theme');
  const [fontSize, setFontSize] = useMMKVNumber('fontSize');
  const [notifications, setNotifications] = useMMKVBoolean('notifications');

  return (
    <>
      <Switch
        value={theme === 'dark'}
        onValueChange={(dark) => setTheme(dark ? 'dark' : 'light')}
      />
      <Slider value={fontSize} onValueChange={setFontSize} />
      <Switch value={notifications} onValueChange={setNotifications} />
    </>
  );
}
```

## Zustand 与 MMKV

```typescript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

const mmkvStorage = {
  getItem: (name: string) => storage.getString(name) ?? null,
  setItem: (name: string, value: string) => storage.set(name, value),
  removeItem: (name: string) => storage.delete(name),
};

interface SettingsStore {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'settings-storage',
      storage: createJSONStorage(() => mmkvStorage),
    }
  )
);
```

## 快速参考

| 存储方式 | 速度 | 异步 | 使用场景 |
|---------|-------|-------|----------|
| AsyncStorage | 慢 | 是 | 小数据、简单应用 |
| MMKV | 快 | 否 | 大数据、频繁访问 |
| SecureStore | 中等 | 是 | 敏感数据（令牌） |

| Hook | 返回值 |
|------|---------|
| `useStorage()` | { value, setValue, loading } |
| `useMMKVString()` | [value, setValue] |
| `useMMKVNumber()` | [value, setValue] |
| `useMMKVBoolean()` | [value, setValue] |
