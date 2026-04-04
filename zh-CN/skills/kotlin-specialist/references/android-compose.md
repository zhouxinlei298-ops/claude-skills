# Android 与 Jetpack Compose

## Compose 基础

```kotlin
import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun UserProfile(user: User, onEdit: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = user.name,
                style = MaterialTheme.typography.headlineMedium
            )
            Text(
                text = user.email,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))
            Button(onClick = onEdit) {
                Text("Edit Profile")
            }
        }
    }
}
```

## 状态管理

```kotlin
// ViewModel with StateFlow
class UserViewModel(
    private val repository: UserRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow(UserUiState())
    val uiState: StateFlow<UserUiState> = _uiState.asStateFlow()

    fun loadUser(userId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            try {
                val user = repository.getUser(userId)
                _uiState.update { it.copy(user = user, isLoading = false) }
            } catch (e: Exception) {
                _uiState.update { it.copy(error = e.message, isLoading = false) }
            }
        }
    }
}

data class UserUiState(
    val user: User? = null,
    val isLoading: Boolean = false,
    val error: String? = null
)

// Composable using ViewModel
@Composable
fun UserScreen(
    viewModel: UserViewModel = hiltViewModel(),
    userId: String
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(userId) {
        viewModel.loadUser(userId)
    }

    when {
        uiState.isLoading -> LoadingIndicator()
        uiState.error != null -> ErrorMessage(uiState.error!!)
        uiState.user != null -> UserProfile(uiState.user!!)
    }
}
```

## Material 3 主题

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) {
        darkColorScheme(
            primary = Purple80,
            secondary = PurpleGrey80,
            tertiary = Pink80
        )
    } else {
        lightColorScheme(
            primary = Purple40,
            secondary = PurpleGrey40,
            tertiary = Pink40
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
```

## 导航

```kotlin
import androidx.navigation.compose.*

@Composable
fun AppNavigation() {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = "home"
    ) {
        composable("home") {
            HomeScreen(
                onNavigateToProfile = { userId ->
                    navController.navigate("profile/$userId")
                }
            )
        }

        composable(
            route = "profile/{userId}",
            arguments = listOf(navArgument("userId") { type = NavType.StringType })
        ) { backStackEntry ->
            val userId = backStackEntry.arguments?.getString("userId")
            ProfileScreen(
                userId = userId ?: "",
                onBack = { navController.popBackStack() }
            )
        }

        composable("settings") {
            SettingsScreen()
        }
    }
}
```

## LazyColumn（列表）

```kotlin
@Composable
fun UserList(
    users: List<User>,
    onUserClick: (User) -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(users, key = { it.id }) { user ->
            UserCard(
                user = user,
                onClick = { onUserClick(user) }
            )
        }
    }
}

// Pagination with LazyColumn
@Composable
fun PaginatedList(viewModel: ListViewModel = hiltViewModel()) {
    val items by viewModel.items.collectAsStateWithLifecycle()
    val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()

    LazyColumn {
        items(items, key = { it.id }) { item ->
            ItemCard(item)
        }

        if (isLoading) {
            item {
                CircularProgressIndicator(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                )
            }
        }

        // Load more trigger
        item {
            LaunchedEffect(Unit) {
                viewModel.loadMore()
            }
        }
    }
}
```

## 副作用

```kotlin
@Composable
fun UserScreen(userId: String) {
    // Run once when userId changes
    LaunchedEffect(userId) {
        loadUser(userId)
    }

    // Run on every recomposition
    SideEffect {
        analyticsService.trackScreen("UserScreen")
    }

    // Cleanup when leaving composition
    DisposableEffect(Unit) {
        val listener = setupListener()
        onDispose {
            listener.cleanup()
        }
    }

    // Remember value across recompositions
    val scrollState = rememberScrollState()

    // Derived state
    val isScrolled by remember {
        derivedStateOf { scrollState.value > 0 }
    }
}
```

## 依赖注入（Hilt）

```kotlin
// Application class
@HiltAndroidApp
class MyApplication : Application()

// Module
@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton
    fun provideApiService(): ApiService = ApiServiceImpl()

    @Provides
    @Singleton
    fun provideUserRepository(api: ApiService): UserRepository =
        UserRepositoryImpl(api)
}

// ViewModel with injection
@HiltViewModel
class UserViewModel @Inject constructor(
    private val repository: UserRepository,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val userId: String = savedStateHandle["userId"] ?: ""

    val user: StateFlow<User?> = repository
        .getUserFlow(userId)
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = null
        )
}

// Activity
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                AppNavigation()
            }
        }
    }
}
```

## Remember 与 State

```kotlin
@Composable
fun SearchScreen() {
    // State hoisting
    var query by remember { mutableStateOf("") }
    var results by remember { mutableStateOf<List<Result>>(emptyList()) }

    Column {
        SearchBar(
            query = query,
            onQueryChange = { query = it },
            onSearch = {
                // Trigger search
            }
        )

        ResultsList(results)
    }
}

// Remember with keys
@Composable
fun UserDetail(userId: String) {
    val user = remember(userId) {
        loadUser(userId)
    }

    // rememberSaveable survives process death
    var expanded by rememberSaveable { mutableStateOf(false) }
}
```

## 动画

```kotlin
import androidx.compose.animation.*
import androidx.compose.animation.core.*

@Composable
fun AnimatedContent() {
    var visible by remember { mutableStateOf(false) }

    // Simple fade
    AnimatedVisibility(visible) {
        Text("Hello World")
    }

    // Custom animation
    val alpha by animateFloatAsState(
        targetValue = if (visible) 1f else 0f,
        animationSpec = tween(durationMillis = 300)
    )

    // Animated content
    AnimatedContent(
        targetState = selectedTab,
        transitionSpec = {
            fadeIn() + slideInVertically() togetherWith
                    fadeOut() + slideOutVertically()
        }
    ) { tab ->
        when (tab) {
            0 -> HomeContent()
            1 -> ProfileContent()
        }
    }
}
```

## 性能优化

```kotlin
// Stability annotations
@Immutable
data class User(val id: String, val name: String)

@Stable
class UserState(private val repository: UserRepository) {
    val users: StateFlow<List<User>> = repository.users
}

// Key for recomposition optimization
@Composable
fun ItemList(items: List<Item>) {
    LazyColumn {
        items(items, key = { it.id }) { item ->
            ItemCard(item)
        }
    }
}

// derivedStateOf for expensive calculations
@Composable
fun FilteredList(items: List<Item>, filter: String) {
    val filtered by remember(items, filter) {
        derivedStateOf {
            items.filter { it.name.contains(filter, ignoreCase = true) }
        }
    }

    LazyColumn {
        items(filtered) { item ->
            ItemCard(item)
        }
    }
}
```

## 快速参考

| Composable | 用途 |
|------------|------|
| `remember` | 在重组之间保留值 |
| `rememberSaveable` | 在进程销毁后保留状态 |
| `LaunchedEffect` | 运行挂起函数 |
| `DisposableEffect` | 离开时执行清理 |
| `SideEffect` | 非挂起的副作用 |
| `derivedStateOf` | 派生计算状态 |
| `collectAsStateWithLifecycle` | Flow 转换为 State（生命周期感知） |
| `animateFloatAsState` | 为值变化添加动画 |
| `LazyColumn` | 可滚动列表 |
| `Scaffold` | Material 3 布局结构 |
| `viewModelScope` | ViewModel 协程作用域 |
| `@HiltViewModel` | Hilt 依赖注入 |
