# 模板元编程

## 可变参数模板

```cpp
#include <iostream>
#include <utility>

// Fold expressions (C++17)
template<typename... Args>
auto sum(Args... args) {
    return (args + ...);  // Unary right fold
}

template<typename... Args>
void print(Args&&... args) {
    ((std::cout << args << ' '), ...);  // Binary left fold
    std::cout << '\n';
}

// Recursive variadic template
template<typename T>
void log(T&& value) {
    std::cout << value << '\n';
}

template<typename T, typename... Args>
void log(T&& first, Args&&... rest) {
    std::cout << first << ", ";
    log(std::forward<Args>(rest)...);
}

// Parameter pack expansion
template<typename... Types>
struct TypeList {
    static constexpr size_t size = sizeof...(Types);
};

template<typename... Args>
auto make_tuple_advanced(Args&&... args) {
    return std::tuple<std::decay_t<Args>...>(std::forward<Args>(args)...);
}
```

## SFINAE 与 if constexpr

```cpp
#include <type_traits>

// SFINAE with std::enable_if (older style)
template<typename T>
std::enable_if_t<std::is_integral_v<T>, T>
double_value(T value) {
    return value * 2;
}

template<typename T>
std::enable_if_t<std::is_floating_point_v<T>, T>
double_value(T value) {
    return value * 2.0;
}

// Modern: if constexpr (C++17)
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral_v<T>) {
        return value * 2;
    } else if constexpr (std::is_floating_point_v<T>) {
        return value * 2.0;
    } else {
        return value;
    }
}

// Detection idiom
template<typename T, typename = void>
struct has_serialize : std::false_type {};

template<typename T>
struct has_serialize<T, std::void_t<decltype(std::declval<T>().serialize())>>
    : std::true_type {};

template<typename T>
constexpr bool has_serialize_v = has_serialize<T>::value;

// Use with if constexpr
template<typename T>
void save(const T& obj) {
    if constexpr (has_serialize_v<T>) {
        obj.serialize();
    } else {
        // Default serialization
    }
}
```

## 类型特征

```cpp
#include <type_traits>

// Custom type traits
template<typename T>
struct remove_all_pointers {
    using type = T;
};

template<typename T>
struct remove_all_pointers<T*> {
    using type = typename remove_all_pointers<T>::type;
};

template<typename T>
using remove_all_pointers_t = typename remove_all_pointers<T>::type;

// Conditional types
template<bool Condition, typename T, typename F>
struct conditional_type {
    using type = T;
};

template<typename T, typename F>
struct conditional_type<false, T, F> {
    using type = F;
};

// Compile-time type selection
template<size_t N>
struct best_integral_type {
    using type = std::conditional_t<N <= 8, uint8_t,
                 std::conditional_t<N <= 16, uint16_t,
                 std::conditional_t<N <= 32, uint32_t, uint64_t>>>;
};

// Check for member functions
template<typename T, typename = void>
struct has_reserve : std::false_type {};

template<typename T>
struct has_reserve<T, std::void_t<decltype(std::declval<T>().reserve(size_t{}))>>
    : std::true_type {};
```

## CRTP（奇异递归模板模式）

```cpp
// Static polymorphism with CRTP
template<typename Derived>
class Shape {
public:
    double area() const {
        return static_cast<const Derived*>(this)->area_impl();
    }

    void draw() const {
        static_cast<const Derived*>(this)->draw_impl();
    }
};

class Circle : public Shape<Circle> {
    double radius_;
public:
    Circle(double r) : radius_(r) {}

    double area_impl() const {
        return 3.14159 * radius_ * radius_;
    }

    void draw_impl() const {
        std::cout << "Drawing circle\n";
    }
};

class Rectangle : public Shape<Rectangle> {
    double width_, height_;
public:
    Rectangle(double w, double h) : width_(w), height_(h) {}

    double area_impl() const {
        return width_ * height_;
    }

    void draw_impl() const {
        std::cout << "Drawing rectangle\n";
    }
};

// CRTP for mixin capabilities
template<typename Derived>
class Printable {
public:
    void print() const {
        std::cout << static_cast<const Derived*>(this)->to_string() << '\n';
    }
};

class User : public Printable<User> {
    std::string name_;
public:
    User(std::string name) : name_(std::move(name)) {}

    std::string to_string() const {
        return "User: " + name_;
    }
};
```

## 模板模板参数

```cpp
#include <vector>
#include <list>
#include <deque>

// Template template parameter
template<typename T, template<typename, typename> class Container>
class Stack {
    Container<T, std::allocator<T>> data_;

public:
    void push(const T& value) {
        data_.push_back(value);
    }

    T pop() {
        T value = data_.back();
        data_.pop_back();
        return value;
    }

    size_t size() const {
        return data_.size();
    }
};

// Usage with different containers
Stack<int, std::vector> vector_stack;
Stack<int, std::deque> deque_stack;
Stack<int, std::list> list_stack;
```

## 编译期计算

```cpp
#include <array>

// Compile-time factorial
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

constexpr int fact_5 = factorial(5);  // Computed at compile time

// Compile-time prime checking
constexpr bool is_prime(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; ++i) {
        if (n % i == 0) return false;
    }
    return true;
}

// Generate compile-time array of primes
template<size_t N>
constexpr auto generate_primes() {
    std::array<int, N> primes{};
    int count = 0;
    int candidate = 2;

    while (count < N) {
        if (is_prime(candidate)) {
            primes[count++] = candidate;
        }
        ++candidate;
    }

    return primes;
}

constexpr auto first_10_primes = generate_primes<10>();
```

## 表达式模板

```cpp
// Lazy evaluation with expression templates
template<typename E>
class VecExpression {
public:
    double operator[](size_t i) const {
        return static_cast<const E&>(*this)[i];
    }

    size_t size() const {
        return static_cast<const E&>(*this).size();
    }
};

class Vec : public VecExpression<Vec> {
    std::vector<double> data_;

public:
    Vec(size_t n) : data_(n) {}

    double operator[](size_t i) const { return data_[i]; }
    double& operator[](size_t i) { return data_[i]; }
    size_t size() const { return data_.size(); }

    // Evaluate expression template
    template<typename E>
    Vec& operator=(const VecExpression<E>& expr) {
        for (size_t i = 0; i < size(); ++i) {
            data_[i] = expr[i];
        }
        return *this;
    }
};

// Binary operation expression
template<typename E1, typename E2>
class VecSum : public VecExpression<VecSum<E1, E2>> {
    const E1& lhs_;
    const E2& rhs_;

public:
    VecSum(const E1& lhs, const E2& rhs) : lhs_(lhs), rhs_(rhs) {}

    double operator[](size_t i) const {
        return lhs_[i] + rhs_[i];
    }

    size_t size() const { return lhs_.size(); }
};

// Operator overload
template<typename E1, typename E2>
VecSum<E1, E2> operator+(const VecExpression<E1>& lhs,
                         const VecExpression<E2>& rhs) {
    return VecSum<E1, E2>(static_cast<const E1&>(lhs),
                          static_cast<const E2&>(rhs));
}

// Usage: a = b + c + d  (no temporaries created!)
```

## 速查表

| 技术 | 使用场景 | 性能特征 |
|------|----------|----------|
| 可变参数模板 | 可变参数 | 零开销 |
| SFINAE | 条件编译 | 编译期 |
| if constexpr | 基于类型的分支 | 零开销 |
| CRTP | 静态多态 | 无虚表开销 |
| 表达式模板 | 惰性求值 | 消除临时对象 |
| 类型特征 | 类型内省 | 编译期 |
| 折叠表达式 | 参数包操作 | 最优 |
| 模板特化 | 类型特定实现 | 零开销 |
