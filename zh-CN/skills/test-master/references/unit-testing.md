# 单元测试

## Jest/Vitest 模式

```typescript
describe('UserService', () => {
  let service: UserService;
  let mockRepo: jest.Mocked<UserRepository>;

  beforeEach(() => {
    mockRepo = { findById: jest.fn(), save: jest.fn() } as any;
    service = new UserService(mockRepo);
  });

  afterEach(() => jest.clearAllMocks());

  describe('getUser', () => {
    it('returns user when found', async () => {
      const user = { id: '1', name: 'Test' };
      mockRepo.findById.mockResolvedValue(user);

      const result = await service.getUser('1');

      expect(result).toEqual(user);
      expect(mockRepo.findById).toHaveBeenCalledWith('1');
    });

    it('throws NotFoundError when user not found', async () => {
      mockRepo.findById.mockResolvedValue(null);

      await expect(service.getUser('1')).rejects.toThrow(NotFoundError);
    });
  });
});
```

## pytest 模式

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestUserService:
    @pytest.fixture
    def mock_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_repo):
        return UserService(mock_repo)

    async def test_get_user_returns_user(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value={"id": "1", "name": "Test"})

        result = await service.get_user("1")

        assert result == {"id": "1", "name": "Test"}
        mock_repo.find_by_id.assert_called_once_with("1")

    async def test_get_user_raises_not_found(self, service, mock_repo):
        mock_repo.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await service.get_user("1")
```

## Mock 模式

```typescript
// Mock functions
const mockFn = jest.fn();
mockFn.mockReturnValue('value');
mockFn.mockResolvedValue('async value');
mockFn.mockRejectedValue(new Error('error'));

// Mock modules
jest.mock('./database', () => ({
  query: jest.fn(),
}));

// Spy on existing methods
jest.spyOn(console, 'log').mockImplementation(() => {});
```

## 测试组织

```typescript
describe('Feature', () => {
  describe('happy path', () => {
    it('does expected behavior', () => {});
  });

  describe('edge cases', () => {
    it('handles empty input', () => {});
    it('handles max values', () => {});
  });

  describe('error cases', () => {
    it('throws on invalid input', () => {});
  });
});
```

## 快速参考

| 模式 | 用途 |
|------|------|
| `describe()` | 分组相关测试 |
| `it()` / `test()` | 单个测试用例 |
| `beforeEach()` | 每个测试前的设置 |
| `jest.fn()` | 创建 Mock 函数 |
| `mockResolvedValue()` | Mock 异步返回值 |
| `expect().toThrow()` | 断言异常 |
