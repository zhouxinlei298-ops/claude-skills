# React 测试

## 基本组件测试

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

test('renders greeting', () => {
  render(<Greeting name="World" />);
  expect(screen.getByText('Hello, World!')).toBeInTheDocument();
});

test('increments counter on click', async () => {
  const user = userEvent.setup();
  render(<Counter />);

  await user.click(screen.getByRole('button', { name: /increment/i }));

  expect(screen.getByText('1')).toBeInTheDocument();
});
```

## 查询优先级

```tsx
// 首选：可访问性查询（用户如何查找元素）
screen.getByRole('button', { name: /submit/i });
screen.getByLabelText('Email');
screen.getByPlaceholderText('Search...');
screen.getByText('Welcome');

// 备选：Test IDs（当没有可访问性名称时）
screen.getByTestId('custom-element');

// Async queries (wait for element)
await screen.findByText('Loading complete');
```

## 测试表单

```tsx
test('submits form with user data', async () => {
  const handleSubmit = vi.fn();
  const user = userEvent.setup();

  render(<ContactForm onSubmit={handleSubmit} />);

  await user.type(screen.getByLabelText('Name'), 'John Doe');
  await user.type(screen.getByLabelText('Email'), 'john@example.com');
  await user.selectOptions(screen.getByLabelText('Topic'), 'support');
  await user.click(screen.getByRole('button', { name: /submit/i }));

  expect(handleSubmit).toHaveBeenCalledWith({
    name: 'John Doe',
    email: 'john@example.com',
    topic: 'support',
  });
});
```

## 使用 Providers 进行测试

```tsx
function renderWithProviders(
  ui: React.ReactElement,
  { initialState = {}, ...options } = {}
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

test('displays user data', async () => {
  renderWithProviders(<UserProfile userId="123" />);

  await screen.findByText('John Doe');
});
```

## Mock API 调用

```tsx
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
  http.get('/api/users/:id', ({ params }) => {
    return HttpResponse.json({ id: params.id, name: 'John' });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('fetches and displays user', async () => {
  render(<UserProfile userId="123" />);

  await screen.findByText('John');
});

test('handles error', async () => {
  server.use(
    http.get('/api/users/:id', () => {
      return new HttpResponse(null, { status: 500 });
    })
  );

  render(<UserProfile userId="123" />);

  await screen.findByText('Error loading user');
});
```

## 测试 Hooks

```tsx
import { renderHook, act } from '@testing-library/react';

test('useCounter increments', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});

test('useDebounce delays value', async () => {
  vi.useFakeTimers();

  const { result, rerender } = renderHook(
    ({ value }) => useDebounce(value, 500),
    { initialProps: { value: 'initial' } }
  );

  rerender({ value: 'updated' });
  expect(result.current).toBe('initial');

  await act(async () => {
    vi.advanceTimersByTime(500);
  });

  expect(result.current).toBe('updated');
  vi.useRealTimers();
});
```

## 快速参考

| 查询 | 何时使用 |
|-------|----------|
| `getByRole` | 按钮、链接、标题 |
| `getByLabelText` | 表单输入 |
| `getByText` | 非交互文本 |
| `findByX` | 异步/加载内容 |
| `queryByX` | 断言不存在 |

| 模式 | 用例 |
|---------|----------|
| `userEvent.setup()` | 用户交互 |
| `renderHook()` | 测试自定义 hooks |
| `msw` | Mock API 调用 |
| Custom render | 包装 providers |
