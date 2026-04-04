# 面向协议编程

## 协议基础

```swift
// Protocol with requirements
protocol Drawable {
    var boundingBox: CGRect { get }
    func draw(in context: CGContext)
}

// Protocol with default implementation
extension Drawable {
    func draw(in context: CGContext) {
        // Default drawing behavior
        context.stroke(boundingBox)
    }
}

// Struct conforming to protocol
struct Circle: Drawable {
    let center: CGPoint
    let radius: CGFloat

    var boundingBox: CGRect {
        CGRect(
            x: center.x - radius,
            y: center.y - radius,
            width: radius * 2,
            height: radius * 2
        )
    }
}
```

## 关联类型

```swift
// Protocol with associated type
protocol Container {
    associatedtype Item
    var count: Int { get }
    mutating func append(_ item: Item)
    subscript(index: Int) -> Item { get }
}

// Generic struct conforming
struct Stack<Element>: Container {
    typealias Item = Element  // Can be inferred
    private var items: [Element] = []

    var count: Int { items.count }

    mutating func append(_ item: Element) {
        items.append(item)
    }

    subscript(index: Int) -> Element {
        items[index]
    }
}

// Using where clause with associated types
extension Container where Item: Equatable {
    func firstIndex(of item: Item) -> Int? {
        for (index, current) in enumerated() where current == item {
            return index
        }
        return nil
    }
}
```

## 协议组合

```swift
// Multiple protocol conformance
protocol Named {
    var name: String { get }
}

protocol Aged {
    var age: Int { get }
}

// Composing protocols
typealias Person = Named & Aged

func greet(_ person: some Named & Aged) {
    print("Hello \(person.name), age \(person.age)")
}

// Protocol composition in constraints
func process<T: Codable & Hashable>(_ items: [T]) {
    // T must conform to both Codable and Hashable
}
```

## 泛型与协议

```swift
// Generic function with protocol constraint
func compare<T: Comparable>(_ a: T, _ b: T) -> T {
    return a > b ? a : b
}

// Generic type with protocol constraint
class Repository<Model: Codable & Identifiable> {
    private var items: [Model.ID: Model] = [:]

    func save(_ model: Model) {
        items[model.id] = model
    }

    func find(id: Model.ID) -> Model? {
        items[id]
    }

    func all() -> [Model] {
        Array(items.values)
    }
}

// Using opaque return types
func makeCollection() -> some Collection {
    return [1, 2, 3, 4, 5]
}

// Primary associated types (Swift 5.7+)
protocol DataSource<Element> {
    associatedtype Element
    func fetch() async throws -> [Element]
}

func loadData<T>(from source: some DataSource<T>) async throws -> [T] {
    try await source.fetch()
}
```

## 类型擦除

```swift
// Problem: Can't use protocol with associated types as type
// protocol Storage {
//     associatedtype Item
//     func store(_ item: Item)
// }
// var storage: Storage  // Error: protocol can only be used as constraint

// Solution: Type-erased wrapper
protocol Storage {
    associatedtype Item
    func store(_ item: Item)
    func retrieve() -> Item?
}

struct AnyStorage<T>: Storage {
    typealias Item = T

    private let _store: (T) -> Void
    private let _retrieve: () -> T?

    init<S: Storage>(_ storage: S) where S.Item == T {
        _store = storage.store
        _retrieve = storage.retrieve
    }

    func store(_ item: T) {
        _store(item)
    }

    func retrieve() -> T? {
        _retrieve()
    }
}

// Now we can use it as a type
class MemoryStorage<T>: Storage {
    private var item: T?

    func store(_ item: T) {
        self.item = item
    }

    func retrieve() -> T? {
        item
    }
}

let storage: AnyStorage<String> = AnyStorage(MemoryStorage<String>())
```

## 协议继承

```swift
// Protocol inheriting from another
protocol Identifiable {
    var id: UUID { get }
}

protocol Timestampable {
    var createdAt: Date { get }
    var updatedAt: Date { get }
}

protocol Entity: Identifiable, Timestampable {
    var version: Int { get }
}

struct User: Entity {
    let id: UUID
    let createdAt: Date
    var updatedAt: Date
    var version: Int
    var name: String
}
```

## 条件一致性

```swift
// Make Array conform to protocol when elements conform
protocol Summarizable {
    var summary: String { get }
}

extension Array: Summarizable where Element: Summarizable {
    var summary: String {
        map { $0.summary }.joined(separator: ", ")
    }
}

struct Task: Summarizable {
    let title: String
    var summary: String { title }
}

let tasks = [Task(title: "Buy milk"), Task(title: "Walk dog")]
print(tasks.summary)  // "Buy milk, Walk dog"
```

## 协议扩展

```swift
// Adding functionality to all conforming types
protocol Collection {
    associatedtype Element
    var count: Int { get }
    subscript(index: Int) -> Element { get }
}

extension Collection {
    var isEmpty: Bool {
        count == 0
    }

    func map<T>(_ transform: (Element) -> T) -> [T] {
        var result: [T] = []
        for i in 0..<count {
            result.append(transform(self[i]))
        }
        return result
    }
}

// Constrained extensions
extension Collection where Element: Numeric {
    func sum() -> Element {
        var total: Element = 0
        for i in 0..<count {
            total += self[i]
        }
        return total
    }
}
```

## 高级模式

```swift
// Phantom types for type safety
enum Celsius {}
enum Fahrenheit {}

struct Temperature<Unit> {
    let value: Double

    init(_ value: Double) {
        self.value = value
    }
}

extension Temperature where Unit == Celsius {
    func toFahrenheit() -> Temperature<Fahrenheit> {
        Temperature<Fahrenheit>(value * 9/5 + 32)
    }
}

extension Temperature where Unit == Fahrenheit {
    func toCelsius() -> Temperature<Celsius> {
        Temperature<Celsius>((value - 32) * 5/9)
    }
}

let celsius = Temperature<Celsius>(100)
let fahrenheit = celsius.toFahrenheit()

// Witness tables pattern
protocol Encoder {
    func encode<T: Encodable>(_ value: T) throws -> Data
}

protocol Decoder {
    func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T
}

struct Codec<E: Encoder, D: Decoder> {
    let encoder: E
    let decoder: D

    func roundtrip<T: Codable>(_ value: T) throws -> T {
        let data = try encoder.encode(value)
        return try decoder.decode(T.self, from: data)
    }
}
```

## 追溯建模

```swift
// Adding protocol conformance to types you don't own
extension Int: Identifiable {
    public var id: Int { self }
}

// Now Int can be used where Identifiable is required
let numbers: [Int] = [1, 2, 3]
ForEach(numbers) { number in
    Text("\(number)")
}
```

## 最佳实践

- 优先使用协议而非基类进行抽象
- 使用协议扩展提供默认实现
- 设计协议时遵循单一职责原则
- 使用关联类型设计泛型协议
- 在需要存储时应用类型擦除
- 利用条件一致性
- 使用不透明返回类型（`some Protocol`）隐藏实现细节
- 组合多个小协议而非设计大协议
- 记录协议的要求和保证
- 考虑使用协议继承实现分层抽象
