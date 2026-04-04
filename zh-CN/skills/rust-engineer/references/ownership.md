# 所有权、借用和生命周期

## 所有权模式

```rust
// Move semantics (ownership transfer)
fn take_ownership(s: String) {
    println!("{}", s);
} // s dropped here

// Borrowing (immutable reference)
fn borrow(s: &String) {
    println!("{}", s);
} // s NOT dropped, caller still owns

// Mutable borrowing
fn borrow_mut(s: &mut String) {
    s.push_str(" world");
}

// Usage
let s = String::from("hello");
borrow(&s);           // OK, immutable borrow
let mut s2 = s;       // Move, s no longer valid
borrow_mut(&mut s2);  // OK, mutable borrow
```

## 生命周期标注

```rust
// Explicit lifetime: returned reference lives as long as input
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Multiple lifetimes
fn first_word<'a, 'b>(s: &'a str, _other: &'b str) -> &'a str {
    s.split_whitespace().next().unwrap_or("")
}

// Lifetime in structs
struct Excerpt<'a> {
    part: &'a str,
}

impl<'a> Excerpt<'a> {
    fn announce_and_return(&self, announcement: &str) -> &'a str {
        println!("Attention: {}", announcement);
        self.part
    }
}

// Static lifetime (lives for entire program)
const GREETING: &'static str = "Hello, world!";
```

## 智能指针

```rust
use std::rc::Rc;
use std::cell::RefCell;
use std::sync::{Arc, Mutex};

// Box: heap allocation, single owner
let b = Box::new(5);

// Rc: reference counting (single-threaded)
let rc1 = Rc::new(vec![1, 2, 3]);
let rc2 = Rc::clone(&rc1);  // Increment count
println!("Count: {}", Rc::strong_count(&rc1));  // 2

// Arc: atomic reference counting (thread-safe)
let arc1 = Arc::new(vec![1, 2, 3]);
let arc2 = Arc::clone(&arc1);
std::thread::spawn(move || {
    println!("{:?}", arc2);
});

// RefCell: interior mutability (runtime borrow checking)
let data = RefCell::new(5);
*data.borrow_mut() += 1;  // Mutable borrow at runtime

// Combining Rc + RefCell for shared mutable state
let shared = Rc::new(RefCell::new(vec![1, 2, 3]));
shared.borrow_mut().push(4);

// Combining Arc + Mutex for thread-safe shared state
let counter = Arc::new(Mutex::new(0));
let counter_clone = Arc::clone(&counter);
std::thread::spawn(move || {
    let mut num = counter_clone.lock().unwrap();
    *num += 1;
});
```

## 内部可变性

```rust
use std::cell::{Cell, RefCell};

// Cell: Copy types only
let c = Cell::new(5);
c.set(10);
let val = c.get();

// RefCell: runtime borrow checking
let data = RefCell::new(vec![1, 2, 3]);
data.borrow_mut().push(4);

// Pattern: mock objects with interior mutability
struct MockLogger {
    messages: RefCell<Vec<String>>,
}

impl MockLogger {
    fn new() -> Self {
        Self { messages: RefCell::new(Vec::new()) }
    }

    fn log(&self, msg: &str) {
        self.messages.borrow_mut().push(msg.to_string());
    }

    fn get_messages(&self) -> Vec<String> {
        self.messages.borrow().clone()
    }
}
```

## Pin 和自引用类型

```rust
use std::pin::Pin;
use std::marker::PhantomPinned;

// Self-referential struct (requires Pin)
struct SelfReferential {
    data: String,
    pointer: *const String,
    _pin: PhantomPinned,
}

impl SelfReferential {
    fn new(data: String) -> Pin<Box<Self>> {
        let mut boxed = Box::pin(Self {
            data,
            pointer: std::ptr::null(),
            _pin: PhantomPinned,
        });

        // Safe: we're not moving the data after this
        let ptr = &boxed.data as *const String;
        unsafe {
            let mut_ref = Pin::as_mut(&mut boxed);
            Pin::get_unchecked_mut(mut_ref).pointer = ptr;
        }

        boxed
    }
}

// Pin in async contexts
async fn pinned_future() {
    // Futures are often self-referential, hence Pin
    let fut = async { 42 };
    let pinned = Box::pin(fut);
    pinned.await;
}
```

## Cow（写时克隆）

```rust
use std::borrow::Cow;

fn process_text(input: &str) -> Cow<str> {
    if input.contains("bad") {
        // Need to modify: allocate new String
        Cow::Owned(input.replace("bad", "good"))
    } else {
        // No modification needed: just borrow
        Cow::Borrowed(input)
    }
}

// Usage
let text1 = "hello world";
let result1 = process_text(text1);  // Borrowed (no allocation)

let text2 = "bad word";
let result2 = process_text(text2);  // Owned (allocated)
```

## Drop Trait 和 RAII

```rust
struct FileGuard {
    name: String,
}

impl FileGuard {
    fn new(name: String) -> Self {
        println!("Opening {}", name);
        Self { name }
    }
}

impl Drop for FileGuard {
    fn drop(&mut self) {
        println!("Closing {}", self.name);
    }
}

// Usage: automatic cleanup
{
    let _file = FileGuard::new("data.txt".to_string());
    // Use file...
} // Drop called automatically here
```

## 常见模式

```rust
// Builder pattern with ownership
struct Config {
    host: String,
    port: u16,
}

impl Config {
    fn builder() -> ConfigBuilder {
        ConfigBuilder::default()
    }
}

struct ConfigBuilder {
    host: Option<String>,
    port: Option<u16>,
}

impl ConfigBuilder {
    fn host(mut self, host: impl Into<String>) -> Self {
        self.host = Some(host.into());
        self
    }

    fn port(mut self, port: u16) -> Self {
        self.port = Some(port);
        self
    }

    fn build(self) -> Result<Config, &'static str> {
        Ok(Config {
            host: self.host.ok_or("host required")?,
            port: self.port.unwrap_or(8080),
        })
    }
}

// Usage
let config = Config::builder()
    .host("localhost")
    .port(3000)
    .build()?;
```

## 最佳实践

- 尽可能优先使用借用（&T）而非所有权转移
- 函数参数使用 &str 而非 String
- 函数参数使用 &[T] 而非 Vec<T>
- 仅在必要时进行克隆（先进行性能分析）
- 条件性克隆使用 Cow<'a, T>
- 在复杂情况下记录生命周期关系
- 跨线程共享可变状态使用 Arc<Mutex<T>>
- 单线程共享可变状态使用 Rc<RefCell<T>>
- 为 RAII 模式实现 Drop
- 需要约束型变时使用 PhantomData
