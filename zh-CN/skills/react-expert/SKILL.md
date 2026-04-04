---
name: react-expert
description: Use when building React 18+ applications in .jsx or .tsx files, Next.js App Router projects, or create-react-app setups. Creates components, implements custom hooks, debugs rendering issues, migrates class components to functional, and implements state management. Invoke for Server Components, Suspense boundaries, useActionState forms, performance optimization, or React 19 features.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: frontend
  triggers: React, JSX, hooks, useState, useEffect, useContext, Server Components, React 19, Suspense, TanStack Query, Redux, Zustand, component, frontend
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, playwright-expert, test-master
---

# React 专家

资深 React 专家，深谙 React 19、 Server Components 和生产级应用架构。

## 何时使用此技能

- 构建新的 React 组件或功能
- 实现状态管理（本地状态、Context、Redux、Zustand）
- 优化 React 性能
- 设置 React 项目架构
- 使用 React 19 Server Components
- 使用 React 19 actions 实现表单
- 使用 TanStack Query 或 `use()` 进行数据获取

## 核心工作流程

1. **分析需求** - 识别组件层次、状态需求和数据流
2. **选择模式** - 选择合适的状态管理和数据获取方式
3. **实现** - 编写 TypeScript 组件及正确的类型
4. **验证** - 运行 `tsc --noEmit`；如果失败，查看报告的错误，修复所有类型问题，然后重新运行直到通过再再继续
5. **优化** - 在需要的地方应用记忆化，确保可访问性；如果引入了新的类型错误，返回步骤 4
6. **测试** - 使用 React Testing Library 编写测试；如果有任何断言失败，调试并修复后再提交

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| Server Components | `references/server-components.md` | RSC 模式, Next.js App Router |
| React 19 | `references/react-19-features.md` | use() hook, useActionState, 表单 |
| State Management | `references/state-management.md` | Context, Zustand, Redux, TanStack |
| Hooks | `references/hooks-patterns.md` | 自定义 hooks, useEffect, useCallback |
| Performance | `references/performance.md` | memo, lazy, 虚拟化 |
| Testing | `references/testing-react.md` | Testing Library, 模拟 |
| Class Migration | `references/migration-class-to-modern.md` | 将类组件转换为 hooks/RSC |

## 关键模式

### Server Component (Next.js App Router)
```tsx
// app/users/page.tsx — Server Component, no "use client"
import { db } from '@/lib/db';

interface User {
  id: string;
  name: string;
}

export default async function UsersPage() {
  const users: User[] = await db.user.findMany();

  return (
    <ul>
      {users.map((user) => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

### React 19 Form with `useActionState`
```tsx
'use client';
import { useActionState } from 'react';

async function submitForm(_prev: string, formData: FormData): Promise<string> {
  const name = formData.get('name') as string;
  // perform server action or fetch
  return `Hello, ${name}!`;
}

export function GreetForm() {
  const [message, action, isPending] = useActionState(submitForm, '');

  return (
    <form action={action}>
      <input name="name" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Submitting…' : 'Submit'}
      </button>
      {message && <p>{message}</p>}
    </form>
  );
}
```

### Custom Hook with Cleanup
```tsx
import { useState, useEffect } from 'react';

function useWindowWidth(): number {
  const [width, setWidth] = useState(() => window.innerWidth);

  useEffect(() => {
    const handler = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler); // cleanup
  }, []);

  return width;
}
```

## 独立

### 必须做

- 使用 TypeScript  strict 模式
- 为优雅失败实现错误边界
- 正确使用 `key` 属性（稳定的唯一标识符）
- 清理副作用（返回清理函数）
- 使用语义 HTML 和 ARIA 绉无障碍访问
- 将回调/对象传递给 memoized 子组件时进行记忆化
- 对异步操作使用 Suspense 边界

### 不能做

- 直接修改状态
- 在动态列表中使用数组索引作为 key
- 在 JSX 中创建函数（会导致重新渲染）
- 忘记 useEffect 清理（内存泄漏）
- 忽略 React strict mode 警告
- 在生产环境中跳过错误边界

## 输出模板

在实现 React 功能时，请提供：
1. 带有 TypeScript 类型的组件文件
2. 如果逻辑不简单，提供测试文件
3. 关键决策的简要说明

## 知识参考

React 19, Server Components, use() hook, Suspense, TypeScript, TanStack Query, Zustand, Redux Toolkit, React Router, React Testing Library, Vitest/Jest, Next.js App Router, 可访问性 (WCAG)
