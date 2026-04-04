# TypeScript JSDoc

## 函数文档

```typescript
/**
 * Calculate total cost including tax.
 *
 * @param items - List of items to calculate total for
 * @param taxRate - Tax rate as decimal (e.g., 0.08 for 8%)
 * @returns Total cost including tax
 * @throws {Error} If taxRate is negative or items is empty
 *
 * @example
 * ```typescript
 * const total = calculateTotal(items, 0.08);
 * console.log(total); // 108.00
 * ```
 */
function calculateTotal(items: Item[], taxRate = 0): number {
```

## 类文档

```typescript
/**
 * Service for managing user operations.
 *
 * Handles CRUD operations and integrates with authentication system.
 *
 * @example
 * ```typescript
 * const service = new UserService(db, cache);
 * const user = await service.create(userData);
 * ```
 */
class UserService {
  /**
   * Create a new UserService instance.
   *
   * @param db - Database connection
   * @param cache - Redis cache client
   */
  constructor(
    private readonly db: Database,
    private readonly cache: Cache,
  ) {}
}
```

## 接口文档

```typescript
/**
 * User data transfer object.
 *
 * @interface UserDto
 */
interface UserDto {
  /** Unique user identifier */
  id: string;

  /** User's email address (unique) */
  email: string;

  /** User's display name */
  name: string;

  /** Account creation timestamp */
  createdAt: Date;
}
```

## 泛型类型

```typescript
/**
 * Paginated response wrapper.
 *
 * @template T - Type of items in the data array
 */
interface PaginatedResponse<T> {
  /** Array of items for current page */
  data: T[];

  /** Total number of items across all pages */
  total: number;

  /** Current page number (1-indexed) */
  page: number;

  /** Number of items per page */
  limit: number;
}
```

## 异步函数

```typescript
/**
 * Fetch user by ID from database.
 *
 * @param id - User's unique identifier
 * @returns Promise resolving to user data or null if not found
 * @throws {DatabaseError} If connection fails
 *
 * @async
 */
async function findUserById(id: string): Promise<User | null> {
```

## 快速参考

| 标签 | 用途 | 示例 |
|-----|---------|---------|
| `@param` | 参数描述 | `@param name - 用户姓名` |
| `@returns` | 返回值 | `@returns 用户对象` |
| `@throws` | 抛出的异常 | `@throws {Error} 如果无效` |
| `@example` | 使用示例 | 代码块 |
| `@see` | 参考链接 | `@see UserService` |
| `@deprecated` | 标记为已弃用 | `@deprecated 使用 v2 替代` |
| `@template` | 泛型类型参数 | `@template T - 项目类型` |
| `@async` | 异步函数 | 标记异步 |
| `@private` | 私有成员 | 内部使用 |
| `@readonly` | 只读属性 | 不能修改 |

## 常见模式

```typescript
// Optional parameters
/** @param [options] - Optional configuration */

// Default values
/** @param [limit=10] - Items per page (default: 10) */

// Multiple types
/** @param input - Input value (string or number) */

// Callback parameters
/**
 * @callback FilterFn
 * @param item - Item to filter
 * @returns Whether item passes filter
 */
```