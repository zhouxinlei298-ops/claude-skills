# Rust 错误处理

## Result 和 Option 基础

```rust
// Result: operation that can fail
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

// Option: value that might be absent
fn find_user(id: u64) -> Option<User> {
    if id == 1 {
        Some(User { id, name: "Alice".to_string() })
    } else {
        None
    }
}

// Using ? operator for propagation
fn calculate(a: f64, b: f64, c: f64) -> Result<f64, String> {
    let x = divide(a, b)?;  // Returns Err early if division fails
    let y = divide(x, c)?;
    Ok(y)
}
```

## 自定义错误类型

```rust
use std::fmt;

// Manual error type
#[derive(Debug)]
enum AppError {
    NotFound(String),
    InvalidInput(String),
    DatabaseError(String),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::NotFound(msg) => write!(f, "Not found: {}", msg),
            AppError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            AppError::DatabaseError(msg) => write!(f, "Database error: {}", msg),
        }
    }
}

impl std::error::Error for AppError {}

// Usage
fn get_user(id: u64) -> Result<User, AppError> {
    if id == 0 {
        return Err(AppError::InvalidInput("ID cannot be zero".to_string()));
    }
    // ... fetch user
    Err(AppError::NotFound(format!("User {} not found", id)))
}
```

## 使用 thiserror

```rust
use thiserror::Error;

#[derive(Error, Debug)]
enum DataError {
    #[error("Data not found: {0}")]
    NotFound(String),

    #[error("Invalid ID: {id}, reason: {reason}")]
    InvalidId { id: u64, reason: String },

    #[error("IO error")]
    Io(#[from] std::io::Error),

    #[error("Parse error")]
    Parse(#[from] std::num::ParseIntError),

    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
}

// Usage with automatic conversions
fn read_config(path: &str) -> Result<Config, DataError> {
    let content = std::fs::read_to_string(path)?;  // Auto-converts io::Error
    let port: u16 = content.parse()?;  // Auto-converts ParseIntError
    Ok(Config { port })
}
```

## 使用 anyhow 处理应用程序

```rust
use anyhow::{Result, Context, bail, ensure};

// Simple error handling for applications
fn process_file(path: &str) -> Result<()> {
    let content = std::fs::read_to_string(path)
        .context(format!("Failed to read file: {}", path))?;

    ensure!(!content.is_empty(), "File is empty");

    if content.len() > 1000 {
        bail!("File too large");
    }

    // Process content...
    Ok(())
}

// Adding context to errors
fn main() -> Result<()> {
    process_file("config.txt")
        .context("Failed to process configuration")?;
    Ok(())
}
```

## Option 组合器

```rust
// map: transform Option<T> to Option<U>
let num: Option<i32> = Some(5);
let doubled = num.map(|n| n * 2);  // Some(10)

// and_then: chain operations
let result = Some(5)
    .and_then(|n| if n > 0 { Some(n * 2) } else { None })
    .and_then(|n| Some(n + 1));  // Some(11)

// or: provide alternative
let value = None.or(Some(42));  // Some(42)

// unwrap_or: provide default
let value = None.unwrap_or(42);  // 42

// unwrap_or_else: compute default lazily
let value = None.unwrap_or_else(|| expensive_computation());

// filter: conditional None
let num = Some(5).filter(|&n| n > 10);  // None

// Pattern matching
match find_user(1) {
    Some(user) => println!("Found: {}", user.name),
    None => println!("User not found"),
}

// if let for simple cases
if let Some(user) = find_user(1) {
    println!("Found: {}", user.name);
}
```

## Result 组合器

```rust
// map: transform Ok value
let result: Result<i32, String> = Ok(5);
let doubled = result.map(|n| n * 2);  // Ok(10)

// map_err: transform error
let result: Result<i32, &str> = Err("error");
let mapped = result.map_err(|e| e.to_uppercase());  // Err("ERROR")

// and_then: chain fallible operations
fn parse_then_double(s: &str) -> Result<i32, std::num::ParseIntError> {
    s.parse::<i32>()
        .and_then(|n| Ok(n * 2))
}

// or_else: provide alternative computation
let result = Err("error").or_else(|_| Ok(42));  // Ok(42)

// unwrap_or: provide default
let value = Err("error").unwrap_or(42);  // 42

// expect: unwrap with custom panic message
let value = result.expect("Failed to parse number");

// Pattern matching
match divide(10.0, 2.0) {
    Ok(result) => println!("Result: {}", result),
    Err(e) => eprintln!("Error: {}", e),
}
```

## 错误转换与 From Trait

```rust
use std::io;
use std::num::ParseIntError;

#[derive(Debug)]
enum MyError {
    Io(io::Error),
    Parse(ParseIntError),
}

impl From<io::Error> for MyError {
    fn from(err: io::Error) -> Self {
        MyError::Io(err)
    }
}

impl From<ParseIntError> for MyError {
    fn from(err: ParseIntError) -> Self {
        MyError::Parse(err)
    }
}

// Now ? operator works with automatic conversion
fn read_and_parse(path: &str) -> Result<i32, MyError> {
    let content = std::fs::read_to_string(path)?;  // io::Error -> MyError
    let number = content.trim().parse()?;  // ParseIntError -> MyError
    Ok(number)
}
```

## 高级错误模式

```rust
// Multiple error sources with Box<dyn Error>
use std::error::Error;

fn complex_operation() -> Result<String, Box<dyn Error>> {
    let file = std::fs::read_to_string("data.txt")?;
    let number: i32 = file.trim().parse()?;
    Ok(format!("Number: {}", number))
}

// Error with backtrace (nightly)
#[derive(Debug)]
struct DetailedError {
    message: String,
    backtrace: std::backtrace::Backtrace,
}

impl DetailedError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            backtrace: std::backtrace::Backtrace::capture(),
        }
    }
}

// Recoverable vs unrecoverable errors
fn might_fail(value: i32) -> Result<i32, String> {
    if value < 0 {
        Err("Negative value".to_string())  // Recoverable
    } else if value > 1000 {
        panic!("Value too large!");  // Unrecoverable
    } else {
        Ok(value * 2)
    }
}
```

## Try 块（Nightly）

```rust
#![feature(try_blocks)]

// Try block for localized error handling
let result: Result<i32, Box<dyn Error>> = try {
    let file = std::fs::read_to_string("config.txt")?;
    let num: i32 = file.trim().parse()?;
    num * 2
};
```

## 错误上下文模式

```rust
use thiserror::Error;

#[derive(Error, Debug)]
#[error("{message}")]
struct ContextError {
    message: String,
    #[source]
    source: Option<Box<dyn Error + Send + Sync>>,
}

impl ContextError {
    fn new(message: impl Into<String>) -> Self {
        Self {
            message: message.into(),
            source: None,
        }
    }

    fn with_source(mut self, source: impl Error + Send + Sync + 'static) -> Self {
        self.source = Some(Box::new(source));
        self
    }
}

// Extension trait for adding context
trait Context<T> {
    fn context(self, message: impl Into<String>) -> Result<T, ContextError>;
}

impl<T, E: Error + Send + Sync + 'static> Context<T> for Result<T, E> {
    fn context(self, message: impl Into<String>) -> Result<T, ContextError> {
        self.map_err(|e| ContextError::new(message).with_source(e))
    }
}
```

## 最佳实践

- 可恢复错误使用 Result，不可恢复的 bug 使用 panic!
- 在生产代码中优先使用 ? 操作符而非 unwrap()
- 使用带描述性消息的 expect() 替代 unwrap()
- 库使用 thiserror（结构化错误）
- 应用程序使用 anyhow（简单的错误处理）
- 为自定义错误类型实现 std::error::Error trait
- 在错误沿调用栈向上传播时添加上下文
- 在 thiserror 中使用 #[from] 实现自动转换
- 在函数文档中记录错误条件
- 使用 Option::ok_or() 将 Option 转换为 Result
- 使用 Result::ok() 将 Result 转换为 Option（丢弃错误）
- 避免使用 String 作为错误类型（使用自定义类型）
- 使用 anyhow 的 ensure! 和 bail! 编写更清晰的检查
- 在边界处记录错误，在库代码中返回错误
