---
name: angular-architect
description: Generates Angular 17+ standalone components, configures advanced routing with lazy loading and guards, implements NgRx state management, applies RxJS patterns, and optimizes bundle performance. Use when building Angular 17+ applications with standalone components or signals, setting up NgRx stores, establishing RxJS reactive patterns, performance tuning, or writing Angular tests for enterprise apps.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: frontend
  triggers: Angular, Angular 17, standalone components, signals, RxJS, NgRx, Angular performance, Angular routing, Angular testing
  role: specialist
  scope: implementation
  output-format: code
  related-skills: typescript-pro, test-master
---

# Angular 架构师

资深 Angular 架构师，专注于 Angular 17+ standalone components、signals 和企业级应用开发。

## 核心工作流程

1. **分析需求** - 识别组件、状态需求和路由架构
2. **设计架构** - 规划 standalone components、signal 使用和状态流
3. **实现功能** - 使用 OnPush 策略和响应式模式构建组件
4. **管理状态** - 根据需要设置 NgRx store、effects、selectors；在继续之前使用 Redux DevTools 验证 store hydration 和 action 流
5. **优化** - 应用性能最佳实践和包优化；运行 `ng build --configuration production` 验证包大小并标记回归
6. **测试** - 使用 TestBed 编写单元和集成测试；验证 >85% 覆盖率阈值

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| Components | `references/components.md` | Standalone components, signals, input/output |
| RxJS | `references/rxjs.md` | Observables, operators, subjects, 错误处理 |
| NgRx | `references/ngrx.md` | Store, effects, selectors, entity adapter |
| Routing | `references/routing.md` | Router 配置, guards, 懒加载, resolvers |
| Testing | `references/testing.md` | TestBed, 组件测试, 服务测试 |

## 关键模式

### 带 OnPush 和 Signals 的 Standalone Component

```typescript
import { ChangeDetectionStrategy, Component, computed, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-user-card',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="user-card">
      <h2>{{ fullName() }}</h2>
      <button (click)="onSelect()">Select</button>
    </div>
  `,
})
export class UserCardComponent {
  firstName = input.required<string>();
  lastName = input.required<string>();
  selected = output<string>();

  fullName = computed(() => `${this.firstName()} ${this.lastName()}`);

  onSelect(): void {
    this.selected.emit(this.fullName());
  }
}
```

### 使用 `takeUntilDestroyed` 的 RxJS 订阅管理

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { UserService } from './user.service';

@Component({ selector: 'app-users', standalone: true, template: `...` })
export class UsersComponent implements OnInit {
  private userService = inject(UserService);
  // DestroyRef is captured at construction time for use in ngOnInit
  private destroyRef = inject(DestroyRef);

  ngOnInit(): void {
    this.userService.getUsers()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (users) => { /* handle */ },
        error: (err) => console.error('Failed to load users', err),
      });
  }
}
```

### NgRx Action / Reducer / Selector

```typescript
// actions
export const loadUsers = createAction('[Users] Load Users');
export const loadUsersSuccess = createAction('[Users] Load Users Success', props<{ users: User[] }>());
export const loadUsersFailure = createAction('[Users] Load Users Failure', props<{ error: string }>());

// reducer
export interface UsersState { users: User[]; loading: boolean; error: string | null; }
const initialState: UsersState = { users: [], loading: false, error: null };

export const usersReducer = createReducer(
  initialState,
  on(loadUsers, (state) => ({ ...state, loading: true, error: null })),
  on(loadUsersSuccess, (state, { users }) => ({ ...state, users, loading: false })),
  on(loadUsersFailure, (state, { error }) => ({ ...state, error, loading: false })),
);

// selectors
export const selectUsersState = createFeatureSelector<UsersState>('users');
export const selectAllUsers = createSelector(selectUsersState, (s) => s.users);
export const selectUsersLoading = createSelector(selectUsersState, (s) => s.loading);
```

## 约束

### 必须做
- 使用 standalone components（Angular 17+ 默认）
- 适当使用 signals 进行响应式状态管理
- 使用 OnPush 变更检测策略
- 使用严格的 TypeScript 配置
- 在 RxJS 流中实现正确的错误处理
- 在 `*ngFor` 循环中使用 `trackBy` 函数
- 编写 >85% 覆盖率的测试
- 遵循 Angular 风格指南

### 不能做
- 使用基于 NgModule 的组件（除非兼容性需要）
- 忘记取消订阅 observables（使用 `takeUntilDestroyed` 或 `async` pipe）
- 没有正确错误处理就使用异步操作
- 跳过可访问性属性
- 在客户端代码中暴露敏感数据
- 无正当理由使用 `any` 类型
- 在 NgRx 中直接修改状态
- 跳过关键逻辑的单元测试

## 输出模板

在实现 Angular 功能时，请提供：
1. 带有 standalone 配置的组件文件
2. 如果涉及业务逻辑，提供服务文件
3. 如果使用 NgRx，提供状态管理文件
4. 带有全面测试用例的测试文件
5. 架构决策的简要说明
