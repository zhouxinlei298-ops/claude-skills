# 路由 & API 资源

## 路由模式

```php
// routes/web.php
use App\Http\Controllers\PostController;
use Illuminate\Support\Facades\Route;

// 资源路由
Route::resource('posts', PostController::class);

// API 资源（排除 create/edit）
Route::apiResource('posts', PostController::class);

// 部分资源
Route::resource('posts', PostController::class)->only(['index', 'show']);
Route::resource('posts', PostController::class)->except(['destroy']);

// 嵌套资源
Route::resource('posts.comments', CommentController::class);

// 路由分组
Route::prefix('admin')->middleware('auth')->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index']);
    Route::resource('users', UserController::class);
});

// 命名路由
Route::get('/posts/{post}', [PostController::class, 'show'])->name('posts.show');

// 路由模型绑定
Route::get('/posts/{post:slug}', [PostController::class, 'show']);

// 多个绑定
Route::get('/users/{user}/posts/{post:slug}', function (User $user, Post $post) {
    return view('posts.show', compact('user', 'post'));
});
```

## API 路由

```php
// routes/api.php
use App\Http\Controllers\Api\V1\PostController;

Route::prefix('v1')->group(function () {
    // 公开路由
    Route::get('/posts', [PostController::class, 'index']);
    Route::get('/posts/{post}', [PostController::class, 'show']);

    // 受保护路由
    Route::middleware('auth:sanctum')->group(function () {
        Route::post('/posts', [PostController::class, 'store']);
        Route::put('/posts/{post}', [PostController::class, 'update']);
        Route::delete('/posts/{post}', [PostController::class, 'destroy']);
    });
});

// 速率限制
Route::middleware('throttle:60,1')->group(function () {
    Route::apiResource('posts', PostController::class);
});
```

## 控制器

```php
namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\StorePostRequest;
use App\Http\Requests\UpdatePostRequest;
use App\Http\Resources\PostResource;
use App\Http\Resources\PostCollection;
use App\Models\Post;
use Illuminate\Http\Response;

class PostController extends Controller
{
    public function index()
    {
        $posts = Post::with('user')
            ->published()
            ->paginate(15);

        return new PostCollection($posts);
    }

    public function store(StorePostRequest $request)
    {
        $post = Post::create($request->validated());

        return new PostResource($post);
    }

    public function show(Post $post)
    {
        $post->load(['user', 'comments.user']);

        return new PostResource($post);
    }

    public function update(UpdatePostRequest $request, Post $post)
    {
        $post->update($request->validated());

        return new PostResource($post);
    }

    public function destroy(Post $post)
    {
        $post->delete();

        return response()->noContent();
    }
}
```

## 表单请求

```php
namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class StorePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // 或检查用户权限
    }

    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:255'],
            'slug' => ['required', 'string', 'unique:posts,slug'],
            'content' => ['required', 'string'],
            'category_id' => ['required', 'exists:categories,id'],
            'tags' => ['array'],
            'tags.*' => ['exists:tags,id'],
            'published_at' => ['nullable', 'date', 'after:now'],
        ];
    }

    public function messages(): array
    {
        return [
            'title.required' => 'Please provide a post title',
            'slug.unique' => 'This slug is already taken',
        ];
    }

    // 验证前准备数据
    protected function prepareForValidation(): void
    {
        $this->merge([
            'slug' => str($this->title)->slug(),
        ]);
    }
}

class UpdatePostRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'title' => ['sometimes', 'string', 'max:255'],
            'slug' => [
                'sometimes',
                'string',
                Rule::unique('posts', 'slug')->ignore($this->post)
            ],
            'content' => ['sometimes', 'string'],
        ];
    }
}
```

## API 资源

```php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class PostResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'slug' => $this->slug,
            'excerpt' => $this->excerpt,
            'content' => $this->when($request->route()->named('posts.show'), $this->content),
            'published_at' => $this->published_at?->toISOString(),
            'created_at' => $this->created_at->toISOString(),

            // 关联关系
            'author' => new UserResource($this->whenLoaded('user')),
            'comments' => CommentResource::collection($this->whenLoaded('comments')),
            'comments_count' => $this->when($this->comments_count !== null, $this->comments_count),

            // 条件字段
            'is_published' => $this->when($request->user()?->isAdmin(), $this->isPublished()),

            // Pivot 数据
            'role' => $this->whenPivotLoaded('role_user', function () {
                return $this->pivot->role_name;
            }),

            // 链接
            'links' => [
                'self' => route('api.posts.show', $this->id),
            ],
        ];
    }

    public function with(Request $request): array
    {
        return [
            'meta' => [
                'version' => '1.0.0',
            ],
        ];
    }
}
```

## 资源集合

```php
namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\ResourceCollection;

class PostCollection extends ResourceCollection
{
    public function toArray(Request $request): array
    {
        return [
            'data' => $this->collection,
            'meta' => [
                'total' => $this->total(),
                'current_page' => $this->currentPage(),
                'last_page' => $this->lastPage(),
            ],
            'links' => [
                'self' => $request->url(),
            ],
        ];
    }
}

// 或使用匿名集合
return PostResource::collection($posts);
```

## 中间件

```php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class EnsureUserIsAdmin
{
    public function handle(Request $request, Closure $next)
    {
        if (!$request->user()?->isAdmin()) {
            abort(403, 'Unauthorized action.');
        }

        return $next($request);
    }
}

// 在 app/Http/Kernel.php 中注册
protected $middlewareAliases = [
    'admin' => \App\Http\Middleware\EnsureUserIsAdmin::class,
];

// 在路由中使用
Route::middleware('admin')->group(function () {
    Route::resource('users', UserController::class);
});
```

## 响应助手

```php
// JSON 响应
return response()->json(['data' => $posts], 200);

// 已创建响应
return response()->json($post, 201);

// 无内容
return response()->noContent();

// 自定义头
return response()->json($data)->header('X-Custom-Header', 'Value');

// 下载
return response()->download($pathToFile);

// 流
return response()->streamDownload(function () {
    echo 'CSV content...';
}, 'export.csv');
```

## 路由缓存

```bash
# 生成路由缓存
php artisan route:cache

# 清空路由缓存
php artisan route:clear

# 列出所有路由
php artisan route:list

# 过滤路由
php artisan route:list --name=api
php artisan route:list --path=posts
```

## API 版本控制

```php
// routes/api.php
Route::prefix('v1')->name('v1.')->group(function () {
    Route::apiResource('posts', \App\Http\Controllers\Api\V1\PostController::class);
});

Route::prefix('v2')->name('v2.')->group(function () {
    Route::apiResource('posts', \App\Http\Controllers\Api\V2\PostController::class);
});
```

## CORS 配置

```php
// config/cors.php
return [
    'paths' => ['api/*', 'sanctum/csrf-cookie'],
    'allowed_methods' => ['*'],
    'allowed_origins' => ['http://localhost:3000'],
    'allowed_headers' => ['*'],
    'exposed_headers' => [],
    'max_age' => 0,
    'supports_credentials' => true,
];
