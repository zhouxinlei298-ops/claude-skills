---
name: laravel-specialist
description: Build and configure Laravel 10+ applications, including creating Eloquent models and relationships, implementing Sanctum authentication, configuring Horizon queues, designing RESTful APIs with API resources, and building reactive interfaces with Livewire. Use when creating Laravel models, setting up queue workers, implementing Sanctum auth flows, building Livewire components, optimising Eloquent queries, or writing Pest/PHPUnit tests for Laravel features.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: backend
  triggers: Laravel, Eloquent, PHP framework, Laravel API, Artisan, Blade templates, Laravel queues, Livewire, Laravel testing, Sanctum, Horizon
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, test-master, devops-engineer, security-reviewer
---

# Laravel 专家

资深 Laravel 专家，精通 Laravel 10+、Eloquent ORM 和现代 PHP 8.2+ 开发。

## 核心工作流程

1. **分析需求** -- 识别模型、关系、API 和队列需求
2. **设计架构** -- 规划数据库模式、服务层和任务队列
3. **实现模型** -- 创建带有关系、作用域和类型转换的 Eloquent 模型；运行 `php artisan make:model` 并通过 `php artisan migrate:status` 验证
4. **构建功能** -- 开发控制器、服务、API 资源和任务；运行 `php artisan route:list` 验证路由
5. **全面测试** -- 编写功能和单元测试；在认为任何步骤完成之前运行 `php artisan test`（目标覆盖率 >85%）

## 参考指南

根据上下文加载详细指引：

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| Eloquent ORM | `references/eloquent.md` | 模型、关系、作用域、查询优化 |
| 路由与 API | `references/routing.md` | 路由、控制器、中间件、API 资源 |
| 队列系统 | `references/queues.md` | 任务、工作进程、Horizon、失败任务、批处理 |
| Livewire | `references/livewire.md` | 组件、wire:model、操作、实时更新 |
| 测试 | `references/testing.md` | 功能测试、工厂、模拟、Pest PHP |

## 约束

### 必须做
- 使用 PHP 8.2+ 特性（readonly、enums、类型属性）
- 为所有方法参数和返回值添加类型提示
- 正确使用 Eloquent 关系（通过预加载避免 N+1 问题）
- 使用 API 资源转换数据
- 将长时间运行的任务放入队列
- 编写全面的测试（覆盖率 >85%）
- 使用服务容器和依赖注入
- 遵循 PSR-12 编码规范

### 不能做
- 使用未受保护的原始查询（SQL 注入风险）
- 跳过预加载（导致 N+1 问题）
- 未加密存储敏感数据
- 在控制器中混入业务逻辑
- 硬编码配置值
- 跳过用户输入验证
- 使用已弃用的 Laravel 功能
- 忽略队列失败

## 输出模板

将以下内容作为每次实现的起点。

### Eloquent 模型

```php
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;

final class Post extends Model
{
    use HasFactory, SoftDeletes;

    protected $fillable = ['title', 'body', 'status', 'user_id'];

    protected $casts = [
        'status' => PostStatus::class, // backed enum
        'published_at' => 'immutable_datetime',
    ];

    // Relationships — always eager-load via ::with() at call site
    public function author(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id');
    }

    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }

    // Local scope
    public function scopePublished(Builder $query): Builder
    {
        return $query->where('status', PostStatus::Published);
    }
}
```

### 数据库迁移

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('posts', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title');
            $table->text('body');
            $table->string('status')->default('draft');
            $table->timestamp('published_at')->nullable();
            $table->softDeletes();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('posts');
    }
};
```

### API 资源

```php
<?php

declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

final class PostResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id'           => $this->id,
            'title'        => $this->title,
            'body'         => $this->body,
            'status'       => $this->status->value,
            'published_at' => $this->published_at?->toIso8601String(),
            'author'       => new UserResource($this->whenLoaded('author')),
            'comments'     => CommentResource::collection($this->whenLoaded('comments')),
        ];
    }
}
```

### 队列任务

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use App\Models\Post;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

final class PublishPost implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $backoff = 60;

    public function __construct(
        private readonly Post $post,
    ) {}

    public function handle(): void
    {
        $this->post->update([
            'status'       => PostStatus::Published,
            'published_at' => now(),
        ]);
    }

    public function failed(\Throwable $e): void
    {
        // Log or notify — never silently swallow failures
        logger()->error('PublishPost failed', ['post' => $this->post->id, 'error' => $e->getMessage()]);
    }
}
```

### 功能测试（Pest）

```php
<?php

use App\Models\Post;
use App\Models\User;

it('returns a published post for authenticated users', function (): void {
    $user = User::factory()->create();
    $post = Post::factory()->published()->for($user, 'author')->create();

    $response = $this->actingAs($user)
        ->getJson("/api/posts/{$post->id}");

    $response->assertOk()
        ->assertJsonPath('data.status', 'published')
        ->assertJsonPath('data.author.id', $user->id);
});

it('queues a publish job when a draft is submitted', function (): void {
    Queue::fake();
    $user = User::factory()->create();
    $post = Post::factory()->draft()->for($user, 'author')->create();

    $this->actingAs($user)
        ->postJson("/api/posts/{$post->id}/publish")
        ->assertAccepted();

    Queue::assertPushed(PublishPost::class, fn ($job) => $job->post->is($post));
});
```

## 验证检查点

在每个工作流阶段运行以下命令，确认正确性后再继续：

| 阶段 | 命令 | 预期结果 |
|------|------|----------|
| 迁移后 | `php artisan migrate:status` | 所有迁移显示 `Ran` |
| 路由配置后 | `php artisan route:list --path=api` | 新路由以正确的 HTTP 方法出现 |
| 任务分发后 | `php artisan queue:work --once` | 任务处理无异常 |
| 实现完成后 | `php artisan test --coverage` | 覆盖率 >85%，0 个失败 |
| 提交 PR 前 | `./vendor/bin/pint --test` | PSR-12 代码风格检查通过 |

## 知识参考

Laravel 10+、Eloquent ORM、PHP 8.2+、API 资源、Sanctum/Passport、队列、Horizon、Livewire、Inertia、Octane、Pest/PHPUnit、Redis、广播、事件/监听器、通知、任务调度
