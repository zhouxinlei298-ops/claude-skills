# 现代 PHP 8.3+ 特性

## 严格类型与类型声明

```php
<?php

declare(strict_types=1);

namespace App\Domain\User;

final readonly class User
{
    public function __construct(
        public int $id,
        public string $email,
        public UserStatus $status,
        public \DateTimeImmutable $createdAt,
    ) {}
}

function calculateTotal(int $price, float $taxRate): float
{
    return $price * (1 + $taxRate);
}

// Union types
function processId(int|string $id): string
{
    return is_int($id) ? (string)$id : $id;
}

// Intersection types
interface Timestamped {}
interface Authenticatable {}

function handleUser(Timestamped&Authenticatable $user): void {}
```

## 带方法的枚举

```php
<?php

declare(strict_types=1);

enum UserStatus: string
{
    case ACTIVE = 'active';
    case SUSPENDED = 'suspended';
    case DELETED = 'deleted';

    public function label(): string
    {
        return match($this) {
            self::ACTIVE => 'Active User',
            self::SUSPENDED => 'Suspended',
            self::DELETED => 'Deleted User',
        };
    }

    public function canLogin(): bool
    {
        return $this === self::ACTIVE;
    }

    public static function fromString(string $value): self
    {
        return self::from(strtolower($value));
    }
}

enum HttpStatus: int
{
    case OK = 200;
    case CREATED = 201;
    case BAD_REQUEST = 400;
    case UNAUTHORIZED = 401;
    case NOT_FOUND = 404;
    case SERVER_ERROR = 500;

    public function isSuccess(): bool
    {
        return $this->value >= 200 && $this->value < 300;
    }
}
```

## 只读属性与类

```php
<?php

declare(strict_types=1);

// Readonly class (PHP 8.2+)
final readonly class Money
{
    public function __construct(
        public int $amount,
        public string $currency,
    ) {
        if ($amount < 0) {
            throw new \InvalidArgumentException('Amount cannot be negative');
        }
    }

    public function add(Money $other): self
    {
        if ($this->currency !== $other->currency) {
            throw new \InvalidArgumentException('Currency mismatch');
        }
        return new self($this->amount + $other->amount, $this->currency);
    }
}

// Individual readonly properties
class Configuration
{
    public function __construct(
        public readonly string $apiKey,
        public readonly string $apiSecret,
        private string $cache = '',
    ) {}
}
```

## 属性（元数据）

```php
<?php

declare(strict_types=1);

#[\Attribute(\Attribute::TARGET_CLASS)]
final readonly class Route
{
    public function __construct(
        public string $path,
        public string $method = 'GET',
        public array $middleware = [],
    ) {}
}

#[\Attribute(\Attribute::TARGET_PROPERTY)]
final readonly class Validate
{
    public function __construct(
        public ?string $rule = null,
        public ?int $min = null,
        public ?int $max = null,
    ) {}
}

// Using attributes
#[Route('/api/users', method: 'POST', middleware: ['auth'])]
final class CreateUserController
{
    public function __invoke(CreateUserRequest $request): JsonResponse
    {
        // ...
    }
}

class UserDto
{
    #[Validate(rule: 'email')]
    public string $email;

    #[Validate(min: 8, max: 100)]
    public string $password;
}
```

## 一等可调用对象

```php
<?php

declare(strict_types=1);

class UserService
{
    public function findById(int $id): ?User {}
    public function create(array $data): User {}
}

$service = new UserService();

// PHP 8.1+ first-class callable syntax
$finder = $service->findById(...);
$user = $finder(42);

// Array operations
$numbers = [1, 2, 3, 4, 5];
$doubled = array_map(fn($n) => $n * 2, $numbers);

// Named arguments with callable
$result = array_filter(
    array: $numbers,
    callback: fn($n) => $n % 2 === 0,
);
```

## match 表达式

```php
<?php

declare(strict_types=1);

function getStatusColor(UserStatus $status): string
{
    return match ($status) {
        UserStatus::ACTIVE => 'green',
        UserStatus::SUSPENDED => 'yellow',
        UserStatus::DELETED => 'red',
    };
}

function calculateShipping(int $weight, string $zone): float
{
    return match (true) {
        $weight < 1000 => 5.00,
        $weight < 5000 && $zone === 'local' => 10.00,
        $weight < 5000 => 15.00,
        default => 25.00,
    };
}

// Match with multiple conditions
function getHttpMessage(int $code): string
{
    return match ($code) {
        200, 201, 204 => 'Success',
        400, 422 => 'Client Error',
        401, 403 => 'Unauthorized',
        500, 502, 503 => 'Server Error',
        default => 'Unknown',
    };
}
```

## Fiber（PHP 8.1+）

```php
<?php

declare(strict_types=1);

// Basic fiber example
$fiber = new \Fiber(function (): void {
    $value = \Fiber::suspend('fiber started');
    echo "Received: {$value}\n";
    \Fiber::suspend('second suspend');
    echo "Fiber completed\n";
});

$result1 = $fiber->start();
echo "First result: {$result1}\n";

$result2 = $fiber->resume('data from main');
echo "Second result: {$result2}\n";

$fiber->resume('final data');

// Async-style with fibers
function async(callable $callback): \Fiber
{
    return new \Fiber($callback);
}

function await(\Fiber $fiber): mixed
{
    if (!$fiber->isStarted()) {
        return $fiber->start();
    }
    return $fiber->resume();
}
```

## never 类型

```php
<?php

declare(strict_types=1);

function redirect(string $url): never
{
    header("Location: {$url}");
    exit;
}

function abort(int $code, string $message): never
{
    http_response_code($code);
    echo json_encode(['error' => $message]);
    exit;
}

class NotFoundException extends \Exception
{
    public static function throw(string $resource): never
    {
        throw new self("Resource not found: {$resource}");
    }
}
```

## 快速参考

| 功能 | PHP 版本 | 用法 |
|------|----------|------|
| 只读属性 | 8.1+ | `public readonly string $name` |
| 只读类 | 8.2+ | `readonly class User {}` |
| 枚举 | 8.1+ | `enum Status: string {}` |
| 一等可调用对象 | 8.1+ | `$fn = $obj->method(...)` |
| never 类型 | 8.1+ | `function exit(): never` |
| Fiber | 8.1+ | `new \Fiber(fn() => ...)` |
| 纯交集类型 | 8.1+ | `A&B $param` |
| DNF 类型 | 8.2+ | `(A&B)\|C $param` |
| trait 中的常量 | 8.2+ | `trait T { const X = 1; }` |
