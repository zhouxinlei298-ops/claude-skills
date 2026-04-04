---
name: swift-expert
description: Builds iOS/macOS/watchOS/tvOS applications, implements SwiftUI views and state management, designs protocol-oriented architectures, handles async/await concurrency, implements actors for thread safety, and debugs Swift-specific issues. Use when building iOS/macOS applications with Swift 5.9+, SwiftUI, or async/await concurrency. Invoke for protocol-oriented programming, SwiftUI state management, actors, server-side Swift, UIKit integration, Combine, or Vapor.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: Swift, SwiftUI, iOS development, macOS development, async/await Swift, Combine, UIKit, Vapor
  role: specialist
  scope: implementation
  output-format: code
  related-skills:
---

# Swift Expert

## 核心工作流程

1. **架构分析** - 确定平台目标、依赖、设计模式
2. **设计协议** - 使用关联类型创建协议优先的 API
3. **实现** - 编写具有 async/await 和值语义的类型安全代码
4. **优化** - 使用 Instruments 进行性能分析，确保线程安全
5. **测试** - 使用 XCTest 和异步模式编写全面的测试

> **验证检查点：** 步骤 3 之后，运行 `swift build` 验证编译。步骤 4 之后，运行 `swift build -warnings-as-errors` 检查 actor 隔离和 Sendable 警告。步骤 5 之后，运行 `swift test` 确认所有异步测试通过。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| SwiftUI | `references/swiftui-patterns.md` | 构建视图、状态管理、修饰符 |
| 并发 | `references/async-concurrency.md` | async/await、actors、结构化并发 |
| 协议 | `references/protocol-oriented.md` | 协议设计、泛型、类型擦除 |
| 内存 | `references/memory-performance.md` | ARC、weak/unowned、性能优化 |
| 测试 | `references/testing-patterns.md` | XCTest、异步测试、mock 策略 |

## 代码模式

### async/await — 正确 vs 错误

```swift
// ✅ DO: async/await with structured error handling
func fetchUser(id: String) async throws -> User {
    let url = URL(string: "https://api.example.com/users/\(id)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// ❌ DON'T: mixing completion handlers with async context
func fetchUser(id: String) async throws -> User {
    return try await withCheckedThrowingContinuation { continuation in
        // Avoid wrapping existing async APIs this way when a native async version exists
        legacyFetch(id: id) { result in
            continuation.resume(with: result)
        }
    }
}
```

### SwiftUI 状态管理

```swift
// ✅ DO: use @Observable (Swift 5.9+) for view models
@Observable
final class CounterViewModel {
    var count = 0
    func increment() { count += 1 }
}

struct CounterView: View {
    @State private var vm = CounterViewModel()

    var body: some View {
        VStack {
            Text("\(vm.count)")
            Button("Increment", action: vm.increment)
        }
    }
}

// ❌ DON'T: reach for ObservableObject/Published when @Observable suffices
class LegacyViewModel: ObservableObject {
    @Published var count = 0  // Unnecessary boilerplate in Swift 5.9+
}
```

### 面向协议架构

```swift
// ✅ DO: define capability protocols with associated types
protocol Repository<Entity> {
    associatedtype Entity: Identifiable
    func fetch(id: Entity.ID) async throws -> Entity
    func save(_ entity: Entity) async throws
}

struct UserRepository: Repository {
    typealias Entity = User
    func fetch(id: UUID) async throws -> User { /* … */ }
    func save(_ user: User) async throws { /* … */ }
}

// ❌ DON'T: use classes as base types when a protocol fits
class BaseRepository {  // Avoid class inheritance for shared behavior
    func fetch(id: UUID) async throws -> Any { fatalError("Override required") }
}
```

### Actor 实现线程安全

```swift
// ✅ DO: isolate mutable shared state in an actor
actor ImageCache {
    private var cache: [URL: UIImage] = [:]

    func image(for url: URL) -> UIImage? { cache[url] }
    func store(_ image: UIImage, for url: URL) { cache[url] = image }
}

// ❌ DON'T: use a class with manual locking
class UnsafeImageCache {
    private var cache: [URL: UIImage] = [:]
    private let lock = NSLock()  // Error-prone; prefer actor isolation
    func image(for url: URL) -> UIImage? {
        lock.lock(); defer { lock.unlock() }
        return cache[url]
    }
}
```

## 约束

### 必须做
- 适当使用类型提示和类型推断
- 遵循 Swift API 设计指南
- 异步操作使用 `async/await`（参见上方模式）
- 确保并发代码的 `Sendable` 合规性
- 默认使用值类型（`struct`/`enum`）
- 使用 markup 注释（`/// …`）为 API 编写文档
- 使用属性包装器处理横切关注点
- 优化前先使用 Instruments 进行性能分析

### 不能做
- 无正当理由使用强制解包（`!`）
- 在闭包中创建循环引用
- 不正确地混合同步和异步代码
- 忽略 actor 隔离警告
- 不必要地使用隐式解包可选值
- 跳过错误处理
- 当存在 Swift 替代方案时使用 Objective-C 模式
- 硬编码平台特定值

## 输出模板

实现 Swift 功能时，请提供：
1. 协议定义和类型别名
2. 模型类型（具有值语义的 struct/class）
3. 视图实现（SwiftUI）或视图控制器
4. 演示用法的测试
5. 架构决策的简要说明
