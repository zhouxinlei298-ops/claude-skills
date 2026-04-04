# 测试模式

---

## 设置

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.js']
  }
})
```

```javascript
// vitest.setup.js
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

vi.stubGlobal('fetch', vi.fn())

config.global.stubs = {
  'router-link': { template: '<a><slot /></a>' }
}
```

---

## 组件测试基础

```javascript
// Button.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from './Button.vue'

describe('Button', () => {
  it('renders slot content', () => {
    const wrapper = mount(Button, { slots: { default: '点击我' } })
    expect(wrapper.text()).toBe('点击我')
  })

  it('applies variant class', () => {
    const wrapper = mount(Button, { props: { variant: 'danger' } })
    expect(wrapper.classes()).toContain('btn--danger')
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('is disabled when prop is true', () => {
    const wrapper = mount(Button, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
```

---

## 测试 v-model

```javascript
// TextInput.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TextInput from './TextInput.vue'

describe('TextInput', () => {
  it('emits update:modelValue on input', async () => {
    const wrapper = mount(TextInput, { props: { modelValue: '' } })
    await wrapper.find('input').setValue('新值')
    expect(wrapper.emitted('update:modelValue')).toEqual([['新值']])
  })
})
```

---

## 测试异步

```javascript
// UserList.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UserList from './UserList.vue'

describe('UserList', () => {
  beforeEach(() => vi.resetAllMocks())

  it('renders users after fetch', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ id: 1, name: 'Alice' }])
    })

    const wrapper = mount(UserList)
    await flushPromises()

    expect(wrapper.text()).toContain('Alice')
  })

  it('shows error on failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('网络错误'))

    const wrapper = mount(UserList)
    await flushPromises()

    expect(wrapper.find('[data-test="error"]').exists()).toBe(true)
  })
})
```

---

## 模拟 Composables

```javascript
// Header.test.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, computed } from 'vue'
import Header from './Header.vue'
import * as useAuthModule from '@/composables/useAuth'

describe('Header', () => {
  it('shows login button when logged out', () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: ref(null),
      isLoggedIn: computed(() => false),
      login: vi.fn(),
      logout: vi.fn()
    })

    const wrapper = mount(Header)
    expect(wrapper.find('[data-test="login-btn"]').exists()).toBe(true)
  })

  it('shows user menu when logged in', () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: ref({ id: 1, name: 'John' }),
      isLoggedIn: computed(() => true),
      login: vi.fn(),
      logout: vi.fn()
    })

    const wrapper = mount(Header)
    expect(wrapper.find('[data-test="user-menu"]').exists()).toBe(true)
  })
})
```

---

## 使用 Pinia 测试

```javascript
// CartSummary.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import CartSummary from './CartSummary.vue'
import { useCartStore } from '@/stores/cart'

describe('CartSummary', () => {
  it('displays cart total', () => {
    const wrapper = mount(CartSummary, {
      global: {
        plugins: [createTestingPinia({
          initialState: {
            cart: { items: [{ productId: 1, quantity: 2, price: 100 }] }
          }
        })]
      }
    })

    expect(wrapper.text()).toContain('$200')
  })

  it('calls checkout action', async () => {
    const wrapper = mount(CartSummary, {
      global: { plugins: [createTestingPinia()] }
    })

    await wrapper.find('[data-test="checkout-btn"]').trigger('click')
    expect(useCartStore().checkout).toHaveBeenCalled()
  })
})
```

---

## 测试 Provide/Inject

```javascript
// ChildComponent.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import ChildComponent from './ChildComponent.vue'

describe('ChildComponent', () => {
  it('uses injected theme', () => {
    const wrapper = mount(ChildComponent, {
      global: { provide: { theme: ref('dark') } }
    })
    expect(wrapper.classes()).toContain('theme-dark')
  })
})
```

---

## 快速参考

| 任务 | 代码 |
|------|------|
| 挂载 | `mount(Component, { props, slots, global })` |
| 查找 | `wrapper.find('[data-test="x"]')` |
| 触发 | `await wrapper.trigger('click')` |
| 检查触发的事件 | `wrapper.emitted('event')` |
| 设置输入 | `await wrapper.find('input').setValue('x')` |
| 等待异步 | `await flushPromises()` |
| 模拟 composable | `vi.spyOn(module, 'fn').mockReturnValue()` |
| 模拟 fetch | `global.fetch = vi.fn().mockResolvedValue()` |
| 测试 Pinia | `createTestingPinia({ initialState })` |
| 提供 | `global: { provide: { key: value } }` |
| 存根组件 | `global: { stubs: { Comp: true } }` |
