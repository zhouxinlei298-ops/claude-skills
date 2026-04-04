# Trait、泛型和类型系统

## 基础 Trait 定义

```rust
// Simple trait
trait Drawable {
    fn draw(&self);
}

// Trait with default implementation
trait Describable {
    fn describe(&self) -> String {
        String::from("No description available")
    }
}

// Implementing traits
struct Circle {
    radius: f64,
}

impl Drawable for Circle {
    fn draw(&self) {
        println!("Drawing circle with radius {}", self.radius);
    }
}

impl Describable for Circle {
    fn describe(&self) -> String {
        format!("A circle with radius {}", self.radius)
    }
}
```

## 关联类型

```rust
// Associated types vs generic parameters
trait Container {
    type Item;

    fn add(&mut self, item: Self::Item);
    fn get(&self, index: usize) -> Option<&Self::Item>;
}

impl Container for Vec<i32> {
    type Item = i32;

    fn add(&mut self, item: i32) {
        self.push(item);
    }

    fn get(&self, index: usize) -> Option<&i32> {
        self.get(index)
    }
}

// Iterator trait (standard library example)
trait MyIterator {
    type Item;

    fn next(&mut self) -> Option<Self::Item>;
}
```

## 泛型 Trait 和约束

```rust
// Generic trait with multiple bounds
fn print_info<T>(item: &T)
where
    T: std::fmt::Display + std::fmt::Debug,
{
    println!("Display: {}", item);
    println!("Debug: {:?}", item);
}

// Generic struct with trait bounds
struct Pair<T: PartialOrd> {
    first: T,
    second: T,
}

impl<T: PartialOrd> Pair<T> {
    fn new(first: T, second: T) -> Self {
        Self { first, second }
    }

    fn larger(&self) -> &T {
        if self.first > self.second {
            &self.first
        } else {
            &self.second
        }
    }
}

// Blanket implementation
trait MyTrait {
    fn do_something(&self);
}

impl<T: std::fmt::Display> MyTrait for T {
    fn do_something(&self) {
        println!("Value: {}", self);
    }
}
```

## Trait 对象（动态分发）

```rust
// Static dispatch (monomorphization)
fn static_dispatch<T: Drawable>(item: &T) {
    item.draw();
}

// Dynamic dispatch (trait objects)
fn dynamic_dispatch(item: &dyn Drawable) {
    item.draw();
}

// Storing trait objects
struct Canvas {
    shapes: Vec<Box<dyn Drawable>>,
}

impl Canvas {
    fn new() -> Self {
        Self { shapes: Vec::new() }
    }

    fn add_shape(&mut self, shape: Box<dyn Drawable>) {
        self.shapes.push(shape);
    }

    fn draw_all(&self) {
        for shape in &self.shapes {
            shape.draw();
        }
    }
}

// Object safety: traits must meet criteria
trait ObjectSafe {
    fn method(&self);  // OK: takes &self
}

trait NotObjectSafe {
    fn generic<T>(&self);  // NOT OK: generic method
    fn by_value(self);     // NOT OK: takes self by value
}
```

## Derive 宏

```rust
// Standard derive macros
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
struct User {
    id: u64,
    name: String,
}

// Deriving more traits
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
struct Point {
    x: i32,
    y: i32,
}

// Custom derive with serde
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct Config {
    host: String,
    port: u16,
}
```

## 高级 Trait 模式

```rust
// Extension trait pattern
trait StringExt {
    fn truncate_to(&self, max_len: usize) -> String;
}

impl StringExt for str {
    fn truncate_to(&self, max_len: usize) -> String {
        if self.len() <= max_len {
            self.to_string()
        } else {
            format!("{}...", &self[..max_len])
        }
    }
}

// Sealed trait pattern (prevent external implementation)
mod sealed {
    pub trait Sealed {}
}

pub trait MySealed: sealed::Sealed {
    fn method(&self);
}

struct MyType;
impl sealed::Sealed for MyType {}
impl MySealed for MyType {
    fn method(&self) {
        println!("Implemented");
    }
}

// Supertraits
trait Printable {
    fn print(&self);
}

trait Loggable: Printable {  // Supertrait: must also impl Printable
    fn log(&self) {
        self.print();  // Can call supertrait methods
    }
}
```

## 关联常量

```rust
trait Config {
    const MAX_SIZE: usize;
    const DEFAULT_TIMEOUT: u64;
}

struct ServerConfig;

impl Config for ServerConfig {
    const MAX_SIZE: usize = 1024;
    const DEFAULT_TIMEOUT: u64 = 30;
}

fn use_config<T: Config>() {
    println!("Max size: {}", T::MAX_SIZE);
}
```

## 泛型关联类型（GAT）

```rust
// GATs allow generics in associated types
trait LendingIterator {
    type Item<'a> where Self: 'a;

    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>>;
}

struct WindowsMut<'data, T> {
    data: &'data mut [T],
    index: usize,
}

impl<'data, T> LendingIterator for WindowsMut<'data, T> {
    type Item<'a> = &'a mut [T] where Self: 'a;

    fn next<'a>(&'a mut self) -> Option<Self::Item<'a>> {
        if self.index >= self.data.len() {
            return None;
        }

        let start = self.index;
        self.index += 2;

        Some(&mut self.data[start..start.min(self.data.len())])
    }
}
```

## 标记 Trait

```rust
use std::marker::{PhantomData, Send, Sync};

// Send: type can be transferred across thread boundaries
// Sync: type can be shared between threads (&T is Send)

// Custom marker trait
trait Trusted {}

struct TrustedData<T> {
    data: T,
    _marker: PhantomData<T>,
}

impl<T: Trusted> TrustedData<T> {
    fn new(data: T) -> Self {
        Self {
            data,
            _marker: PhantomData,
        }
    }
}
```

## 运算符重载

```rust
use std::ops::{Add, Mul};

#[derive(Debug, Clone, Copy)]
struct Vector2D {
    x: f64,
    y: f64,
}

impl Add for Vector2D {
    type Output = Self;

    fn add(self, other: Self) -> Self {
        Self {
            x: self.x + other.x,
            y: self.y + other.y,
        }
    }
}

impl Mul<f64> for Vector2D {
    type Output = Self;

    fn mul(self, scalar: f64) -> Self {
        Self {
            x: self.x * scalar,
            y: self.y * scalar,
        }
    }
}

// Usage
let v1 = Vector2D { x: 1.0, y: 2.0 };
let v2 = Vector2D { x: 3.0, y: 4.0 };
let v3 = v1 + v2;
let v4 = v1 * 2.5;
```

## From/Into 转换 Trait

```rust
struct UserId(u64);

impl From<u64> for UserId {
    fn from(id: u64) -> Self {
        UserId(id)
    }
}

// Into is automatically implemented
fn accept_user_id(id: impl Into<UserId>) {
    let user_id = id.into();
    println!("User ID: {}", user_id.0);
}

// TryFrom for fallible conversions
use std::convert::TryFrom;

impl TryFrom<i64> for UserId {
    type Error = &'static str;

    fn try_from(value: i64) -> Result<Self, Self::Error> {
        if value < 0 {
            Err("User ID cannot be negative")
        } else {
            Ok(UserId(value as u64))
        }
    }
}
```

## Const Trait（Nightly）

```rust
// Const trait implementations (requires nightly)
#![feature(const_trait_impl)]

#[const_trait]
trait ConstAdd {
    fn add(self, other: Self) -> Self;
}

impl const ConstAdd for i32 {
    fn add(self, other: Self) -> Self {
        self + other
    }
}

const fn compute() -> i32 {
    5.add(10)  // Can use in const context
}
```

## 最佳实践

- 当每次实现只有一个明确的类型时，优先使用关联类型
- 当可能同时使用多种类型时，使用泛型参数
- 保持 trait 小而专注（单一职责）
- 使用扩展 trait 为现有类型添加功能
- 记录 trait 的要求和不变量
- 使用标记 trait 提供编译时保证
- 性能优先时使用静态分发，灵活性优先时使用动态分发
- 尽可能使用 #[derive] 而非手动实现
- 实现标准 trait（Debug、Clone 等）以更好地融入生态系统
- 需要时使用 sealed trait 防止外部实现
