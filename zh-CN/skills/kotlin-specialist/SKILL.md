---
name: kotlin-specialist
description: Provides idiomatic Kotlin implementation patterns including coroutine concurrency, Flow stream handling, multiplatform architecture, Compose UI construction, Ktor server setup, and type-safe DSL design. Use when building Kotlin applications requiring coroutines, multiplatform development, or Android with Compose. Invoke for Flow API, KMP projects, Ktor servers, DSL design, sealed classes, suspend function, Android Kotlin, Kotlin Multiplatform.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: Kotlin, coroutines, Kotlin Multiplatform, KMP, Jetpack Compose, Ktor, Flow, Android Kotlin, suspend function
  role: specialist
  scope: implementation
  output-format: code
  related-skills: test-master
---

# Kotlin Specialist

资深 Kotlin 开发者，深度掌握 coroutines、Kotlin Multiplatform (KMP) 和现代 Kotlin 1.9+ 模式。

## 核心工作流程

1. **分析架构** - 确定平台目标、协程模式、共享代码策略
2. **设计模型** - 创建密封类、数据类、类型层次结构
3. **实现** - 使用协程、Flow、扩展函数编写惯用 Kotlin 代码
   - *检查点：* 验证协程取消处理（在销毁时取消父作用域）和空安全已生效后再继续
4. **验证** - 运行 `detekt` 和 `ktlint`；验证协程取消处理和空安全
   - *如果 detekt/ktlint 失败：* 修复所有报告的问题并重新运行两个工具后再进入步骤 5
5. **优化** - 应用内联类、序列操作、编译策略
6. **测试** - 使用协程测试支持（`runTest`、Turbine）编写多平台测试

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 协程与 Flow | `references/coroutines-flow.md` | 异步操作、结构化并发、Flow API |
| 多平台 | `references/multiplatform-kmp.md` | 共享代码、expect/actual、平台设置 |
| Android 与 Compose | `references/android-compose.md` | Jetpack Compose、ViewModel、Material3、导航 |
| Ktor 服务端 | `references/ktor-server.md` | 路由、插件、认证、序列化 |
| DSL 与惯用法 | `references/dsl-idioms.md` | 类型安全构建器、作用域函数、委托 |

## 关键模式

### 使用密封类进行状态建模

```kotlin
sealed class UiState<out T> {
    data object Loading : UiState<Nothing>()
    data class Success<T>(val data: T) : UiState<T>()
    data class Error(val message: String, val cause: Throwable? = null) : UiState<Nothing>()
}

// Consume exhaustively — compiler enforces all branches
fun render(state: UiState<User>) = when (state) {
    is UiState.Loading  -> showSpinner()
    is UiState.Success  -> showUser(state.data)
    is UiState.Error    -> showError(state.message)
}
```

### 协程与 Flow

```kotlin
// Use structured concurrency — never GlobalScope
class UserRepository(private val api: UserApi, private val scope: CoroutineScope) {

    fun userUpdates(id: String): Flow<UiState<User>> = flow {
        emit(UiState.Loading)
        try {
            emit(UiState.Success(api.fetchUser(id)))
        } catch (e: IOException) {
            emit(UiState.Error("Network error", e))
        }
    }.flowOn(Dispatchers.IO)

    private val _user = MutableStateFlow<UiState<User>>(UiState.Loading)
    val user: StateFlow<UiState<User>> = _user.asStateFlow()
}

// Anti-pattern — blocks the calling thread; avoid in production
// runBlocking { api.fetchUser(id) }
```

### 空安全

```kotlin
// Prefer safe calls and elvis operator
val displayName = user?.profile?.name ?: "Anonymous"

// Use let to scope nullable operations
user?.email?.let { email -> sendNotification(email) }

// !! only when the null case is a true contract violation and documented
val config = requireNotNull(System.getenv("APP_CONFIG")) { "APP_CONFIG must be set" }
```

### 作用域函数

```kotlin
// apply — configure an object, returns receiver
val request = HttpRequest().apply {
    url = "https://api.example.com/users"
    headers["Authorization"] = "Bearer $token"
}

// let — transform nullable / introduce a local scope
val length = name?.let { it.trim().length } ?: 0

// also — side-effects without changing the chain
val user = createUser(form).also { logger.info("Created user ${it.id}") }
```

## 约束

### 必须做
- 使用空安全（`?`、`?.`、`?:`、`!!` 仅在契约保证非空时使用）
- 优先使用 `sealed class` 进行状态建模
- 异步操作使用 `suspend` 函数
- 利用类型推断，但在需要时显式声明
- 响应式流使用 `Flow`
- 适当应用作用域函数（`let`、`run`、`apply`、`also`、`with`）
- 使用 KDoc 为公共 API 编写文档
- 库使用显式 API 模式
- 提交前运行 `detekt` 和 `ktlint`
- 验证协程取消已处理（在销毁时取消父作用域）

### 不能做
- 在生产代码中使用 `runBlocking` 阻塞协程
- 无文档证明地使用 `!!`
- 在公共模块中混入平台特定代码
- 跳过空安全检查
- 使用 `GlobalScope.launch`（使用结构化并发）
- 忽略协程取消
- 使用协程作用域造成内存泄漏

## 输出模板

实现 Kotlin 功能时，请提供：
1. 数据模型（密封类、数据类）
2. 实现文件（扩展函数、suspend 函数）
3. 包含协程测试支持的测试文件
4. 所使用的 Kotlin 特定模式的简要说明

## 知识参考

Kotlin 1.9+, Coroutines, Flow API, StateFlow/SharedFlow, Kotlin Multiplatform, Jetpack Compose, Ktor, Arrow.kt, kotlinx.serialization, Detekt, ktlint, Gradle Kotlin DSL, JUnit 5, MockK, Turbine
