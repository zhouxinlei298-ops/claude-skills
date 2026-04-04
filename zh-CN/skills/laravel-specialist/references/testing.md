# 测试

## 功能测试

```php
namespace Tests\Feature;

use Tests\TestCase;
use App\Models\{User, Post};
use Illuminate\Foundation\Testing\RefreshDatabase;

class PostTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_create_post(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->post('/api/posts', [
            'title' => 'Test Post',
            'content' => 'This is a test post content.',
        ]);

        $response->assertStatus(201)
            ->assertJson([
                'data' => [
                    'title' => 'Test Post',
                ],
            ]);

        $this->assertDatabaseHas('posts', [
            'title' => 'Test Post',
            'user_id' => $user->id,
        ]);
    }

    public function test_guest_cannot_create_post(): void
    {
        $response = $this->post('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content',
        ]);

        $response->assertStatus(401);
    }

    public function test_post_requires_valid_data(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)->post('/api/posts', [
            'title' => 'AB', // 太短
        ]);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['title', 'content']);
    }

    public function test_user_can_view_their_posts(): void
    {
        $user = User::factory()->create();
        $posts = Post::factory()->count(3)->create(['user_id' => $user->id]);

        $response = $this->actingAs($user)->get('/api/posts');

        $response->assertStatus(200)
            ->assertJsonCount(3, 'data')
            ->assertJsonStructure([
                'data' => [
                    '*' => ['id', 'title', 'content', 'created_at'],
                ],
            ]);
    }

    public function test_user_can_update_own_post(): void
    {
        $user = User::factory()->create();
        $post = Post::factory()->create(['user_id' => $user->id]);

        $response = $this->actingAs($user)->put("/api/posts/{$post->id}", [
            'title' => 'Updated Title',
            'content' => $post->content,
        ]);

        $response->assertStatus(200);

        $this->assertDatabaseHas('posts', [
            'id' => $post->id,
            'title' => 'Updated Title',
        ]);
    }

    public function test_user_cannot_update_others_post(): void
    {
        $user = User::factory()->create();
        $otherUser = User::factory()->create();
        $post = Post::factory()->create(['user_id' => $otherUser->id]);

        $response = $this->actingAs($user)->put("/api/posts/{$post->id}", [
            'title' => 'Updated Title',
        ]);

        $response->assertStatus(403);
    }
}
```

## 单元测试

```php
namespace Tests\Unit;

use Tests\TestCase;
use App\Models\Post;
use App\Services\PostService;
use Illuminate\Foundation\Testing\RefreshDatabase;

class PostServiceTest extends TestCase
{
    use RefreshDatabase;

    public function test_generates_unique_slug(): void
    {
        $service = new PostService();

        $slug = $service->generateSlug('Test Post');

        $this->assertEquals('test-post', $slug);
    }

    public function test_increments_slug_on_duplicate(): void
    {
        Post::factory()->create(['slug' => 'test-post']);

        $service = new PostService();
        $slug = $service->generateSlug('Test Post');

        $this->assertEquals('test-post-1', $slug);
    }

    public function test_post_excerpt_returns_limited_content(): void
    {
        $post = new Post(['content' => str_repeat('a', 200)]);

        $excerpt = $post->excerpt;

        $this->assertLessThanOrEqual(100, strlen($excerpt));
    }
}
```

## Pest PHP

```php
<?php

use App\Models\{User, Post};

it('allows authenticated users to create posts', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/api/posts', [
            'title' => 'Test Post',
            'content' => 'Content',
        ])
        ->assertStatus(201);

    expect(Post::count())->toBe(1);
});

it('prevents guests from creating posts', function () {
    $this->post('/api/posts', [
        'title' => 'Test Post',
        'content' => 'Content',
    ])->assertStatus(401);
});

test('post requires title and content', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/api/posts', [])
        ->assertJsonValidationErrors(['title', 'content']);
});

// 数据集
it('validates title length', function (string $title, bool $shouldPass) {
    $user = User::factory()->create();

    $response = $this->actingAs($user)->post('/api/posts', [
        'title' => $title,
        'content' => 'Content',
    ]);

    if ($shouldPass) {
        $response->assertStatus(201);
    } else {
        $response->assertJsonValidationErrors(['title']);
    }
})->with([
    ['AB', false],        // 太短
    ['ABC', true],        // 最小有效值
    [str_repeat('A', 255), true],  // 最大有效值
    [str_repeat('A', 256), false], // 太长
]);

// 钩子
beforeEach(function () {
    $this->user = User::factory()->create();
});

afterEach(function () {
    // 清理
});
```

## 工厂

```php
namespace Database\Factories;

use App\Models\{User, Category};
use Illuminate\Database\Eloquent\Factories\Factory;

class PostFactory extends Factory
{
    public function definition(): array
    {
        return [
            'title' => fake()->sentence(),
            'slug' => fake()->slug(),
            'content' => fake()->paragraphs(3, true),
            'excerpt' => fake()->text(100),
            'published_at' => fake()->dateTimeBetween('-1 year', 'now'),
            'user_id' => User::factory(),
            'category_id' => Category::factory(),
        ];
    }

    public function unpublished(): static
    {
        return $this->state(fn (array $attributes) => [
            'published_at' => null,
        ]);
    }

    public function published(): static
    {
        return $this->state(fn (array $attributes) => [
            'published_at' => now(),
        ]);
    }

    public function forUser(User $user): static
    {
        return $this->state(fn (array $attributes) => [
            'user_id' => $user->id,
        ]);
    }

    public function configure(): static
    {
        return $this->afterCreating(function (Post $post) {
            $post->tags()->attach(
                Tag::factory()->count(3)->create()
            );
        });
    }
}

// 使用
$post = Post::factory()->create();
$unpublished = Post::factory()->unpublished()->create();
$posts = Post::factory()->count(10)->create();
$userPosts = Post::factory()->forUser($user)->count(5)->create();

// 带关联关系
$post = Post::factory()
    ->has(Comment::factory()->count(3))
    ->create();

// 用于关联关系
$posts = Post::factory()
    ->count(3)
    ->for($user)
    ->create();
```

## 模拟

```php
use App\Services\ExternalApiService;
use Illuminate\Support\Facades\Http;

public function test_fetches_data_from_external_api(): void
{
    Http::fake([
        'api.example.com/*' => Http::response([
            'data' => ['id' => 1, 'name' => 'Test'],
        ], 200),
    ]);

    $service = new ExternalApiService();
    $result = $service->fetchData();

    $this->assertEquals('Test', $result['name']);

    Http::assertSent(function ($request) {
        return $request->url() === 'https://api.example.com/data' &&
               $request->hasHeader('Authorization');
    });
}

// 模拟事件
use Illuminate\Support\Facades\Event;

Event::fake([PostCreated::class]);

// 测试分发事件的代码

Event::assertDispatched(PostCreated::class, function ($event) {
    return $event->post->id === 1;
});

// 模拟队列
use Illuminate\Support\Facades\Queue;

Queue::fake();

// 测试分发作业的代码

Queue::assertPushed(ProcessPost::class);
Queue::assertPushed(ProcessPost::class, 2);
Queue::assertPushed(ProcessPost::class, function ($job) {
    return $job->post->id === 1;
});

// 模拟通知
use Illuminate\Support\Facades\Notification;

Notification::fake();

// 测试发送通知的代码

Notification::assertSentTo($user, PostPublished::class);

// 模拟存储
use Illuminate\Support\Facades\Storage;

Storage::fake('public');

// 测试文件上传

Storage::disk('public')->assertExists('file.jpg');
Storage::disk('public')->assertMissing('missing.jpg');
```

## 数据库测试

```php
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\DatabaseTransactions;

class PostTest extends TestCase
{
    use RefreshDatabase; // 每次测试前迁移数据库

    // 或使用事务
    use DatabaseTransactions; // 每次测试后回滚

    public function test_database_assertions(): void
    {
        $post = Post::factory()->create([
            'title' => 'Test Post',
        ]);

        $this->assertDatabaseHas('posts', [
            'title' => 'Test Post',
        ]);

        $post->delete();

        $this->assertDatabaseMissing('posts', [
            'id' => $post->id,
        ]);

        $this->assertSoftDeleted('posts', [
            'id' => $post->id,
        ]);
    }

    public function test_model_exists(): void
    {
        $post = Post::factory()->create();

        $this->assertModelExists($post);

        $post->delete();

        $this->assertModelMissing($post);
    }
}
```

## API 测试

```php
public function test_api_returns_paginated_posts(): void
{
    Post::factory()->count(30)->create();

    $response = $this->get('/api/posts');

    $response->assertStatus(200)
        ->assertJsonStructure([
            'data' => [
                '*' => ['id', 'title', 'content'],
            ],
            'meta' => ['total', 'current_page', 'last_page'],
            'links' => ['first', 'last', 'prev', 'next'],
        ])
        ->assertJsonCount(15, 'data'); // 默认每页
}

public function test_api_filters_posts_by_category(): void
{
    $category = Category::factory()->create();
    Post::factory()->count(5)->create(['category_id' => $category->id]);
    Post::factory()->count(5)->create();

    $response = $this->get("/api/posts?category={$category->id}");

    $response->assertJsonCount(5, 'data')
        ->assertJson([
            'data' => [
                ['category_id' => $category->id],
            ],
        ]);
}
```

## 认证测试

```php
use Laravel\Sanctum\Sanctum;

public function test_authenticated_user_can_access_endpoint(): void
{
    $user = User::factory()->create();

    Sanctum::actingAs($user, ['*']);

    $response = $this->get('/api/user');

    $response->assertStatus(200)
        ->assertJson([
            'data' => [
                'id' => $user->id,
                'email' => $user->email,
            ],
        ]);
}

public function test_user_with_wrong_ability_cannot_access(): void
{
    $user = User::factory()->create();

    Sanctum::actingAs($user, ['view-posts']);

    $response = $this->post('/api/posts', [
        'title' => 'Test',
        'content' => 'Content',
    ]);

    $response->assertStatus(403);
}
```

## 运行测试

```bash
# 运行所有测试
php artisan test

# 运行特定测试
php artisan test --filter=test_user_can_create_post

# 运行测试文件
php artisan test tests/Feature/PostTest.php

# 并行测试
php artisan test --parallel

# 带覆盖率
php artisan test --coverage

# 覆盖率最低要求
php artisan test --coverage --min=80

# 失败时停止
php artisan test --stop-on-failure

# Pest 特定
./vendor/bin/pest
./vendor/bin/pest --filter=PostTest
./vendor/bin/pest --coverage
```

## 最佳实践

1. **使用 RefreshDatabase** - 每次测试清理数据库
2. **使用工厂** - 不要手动创建测试数据
3. **测试一件事** - 每个测试应该验证一种行为
4. **使用描述性名称** - test_user_can_create_post
5. **AAA 模式** - Arrange, Act, Assert
6. **模拟外部服务** - 不要进行真实的 API 调用
7. **伪造队列和事件** - 同步测试异步代码
8. **测试边界情况** - 无效数据、权限等
9. **达到 >85% 覆盖率** - 测试关键路径
10. **在 CI/CD 中运行测试** - 自动化测试执行
