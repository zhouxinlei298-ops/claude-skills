# 队列系统

## 作业模式

```php
namespace App\Jobs;

use App\Models\Post;
use App\Models\User;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class ProcessPost implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $tries = 3;
    public $timeout = 120;
    public $maxExceptions = 3;
    public $backoff = [60, 120, 300]; // 指数退避

    public function __construct(
        public Post $post,
        public ?User $user = null,
    ) {}

    public function handle(): void
    {
        // 处理 post
        $this->post->update(['processed' => true]);

        // 可以访问注入的依赖
        $analytics = app(AnalyticsService::class);
        $analytics->trackPostProcessed($this->post);
    }

    public function failed(\Throwable $exception): void
    {
        // 处理作业失败
        \Log::error('Post processing failed', [
            'post_id' => $this->post->id,
            'error' => $exception->getMessage(),
        ]);
    }
}
```

## 分发作业

```php
use App\Jobs\ProcessPost;

// 立即分发
ProcessPost::dispatch($post);

// 分发到特定队列
ProcessPost::dispatch($post)->onQueue('processing');

// 延迟分发
ProcessPost::dispatch($post)->delay(now()->addMinutes(10));

// 数据库提交后分发
ProcessPost::dispatch($post)->afterCommit();

// 条件分发
ProcessPost::dispatchIf($condition, $post);
ProcessPost::dispatchUnless($condition, $post);

// 同步分发（不使用队列）
ProcessPost::dispatchSync($post);

// 响应后分发
ProcessPost::dispatchAfterResponse($post);
```

## 作业链

```php
use App\Jobs\{OptimizeImage, GenerateThumbnail, PublishPost};

// 链接作业
OptimizeImage::withChain([
    new GenerateThumbnail($post),
    new PublishPost($post),
])->dispatch($post);

// 捕获链中的失败
Bus::chain([
    new ProcessPost($post),
    new NotifyUser($user),
])->catch(function (\Throwable $e) {
    // 处理失败
})->dispatch();
```

## 作业批处理

```php
use Illuminate\Bus\Batch;
use Illuminate\Support\Facades\Bus;

$batch = Bus::batch([
    new ProcessPost($post1),
    new ProcessPost($post2),
    new ProcessPost($post3),
])->then(function (Batch $batch) {
    // 所有作业成功完成
})->catch(function (Batch $batch, \Throwable $e) {
    // 检测到第一批作业失败
})->finally(function (Batch $batch) {
    // 批处理已执行完成
})->name('Process Posts')
->allowFailures()
->dispatch();

// 检查批处理状态
$batch = Bus::findBatch($batchId);
if ($batch->finished()) {
    // 批处理已完成
}
if ($batch->cancelled()) {
    // 批处理已取消
}

// 向现有批处理添加作业
$batch->add([
    new ProcessPost($post4),
]);
```

## 速率限制

```php
use Illuminate\Support\Facades\Redis;

class ProcessPost implements ShouldQueue
{
    public function handle(): void
    {
        Redis::throttle('process-posts')
            ->block(0)
            ->allow(10)
            ->every(60)
            ->then(function () {
                // 获取锁定，处理作业
            }, function () {
                // 无法获取锁定，释放作业返回
                $this->release(10);
            });
    }
}

// 或使用中间件
use Illuminate\Queue\Middleware\RateLimited;

public function middleware(): array
{
    return [new RateLimited('process-posts')];
}
```

## 作业中间件

```php
namespace App\Jobs\Middleware;

class RateLimitedByUser
{
    public function handle($job, $next): void
    {
        Redis::throttle("user:{$job->user->id}")
            ->allow(10)
            ->every(60)
            ->then(function () use ($job, $next) {
                $next($job);
            }, function () use ($job) {
                $job->release(10);
            });
    }
}

// 在作业中使用
use App\Jobs\Middleware\RateLimitedByUser;

public function middleware(): array
{
    return [new RateLimitedByUser];
}

// 跳过中间件
use Illuminate\Queue\Middleware\WithoutOverlapping;

public function middleware(): array
{
    return [
        (new WithoutOverlapping($this->user->id))->expireAfter(180),
    ];
}
```

## 唯一作业

```php
use Illuminate\Contracts\Queue\ShouldBeUnique;

class ProcessPost implements ShouldQueue, ShouldBeUnique
{
    public int $uniqueFor = 3600;

    public function __construct(
        public Post $post,
    ) {}

    public function uniqueId(): string
    {
        return $this->post->id;
    }
}

// 或使用直到处理前唯一
use Illuminate\Contracts\Queue\ShouldBeUniqueUntilProcessing;

class ProcessPost implements ShouldQueue, ShouldBeUniqueUntilProcessing
{
    // ...
}
```

## 失败作业

```php
// 重试失败作业
php artisan queue:retry <job-id>

// 重试所有失败作业
php artisan queue:retry all

// 清空失败作业
php artisan queue:flush

// 清理失败作业
php artisan queue:prune-failed --hours=48

// 在代码中处理
use Illuminate\Support\Facades\Queue;

Queue::failing(function (JobFailed $event) {
    \Log::error('Job failed', [
        'connection' => $event->connectionName,
        'queue' => $event->job->getQueue(),
        'exception' => $event->exception->getMessage(),
    ]);
});
```

## 队列工作进程

```bash
# 启动工作进程
php artisan queue:work

# 处理特定队列
php artisan queue:work --queue=high,default

# 处理一个作业
php artisan queue:work --once

# 优雅地停止工作进程
php artisan queue:restart

# 超时设置
php artisan queue:work --timeout=60

# 内存限制
php artisan queue:work --memory=512

# 重启前最大作业数
php artisan queue:work --max-jobs=1000

# 重启前最大时间
php artisan queue:work --max-time=3600
```

## Horizon 设置

```php
// config/horizon.php
return [
    'environments' => [
        'production' => [
            'supervisor-1' => [
                'connection' => 'redis',
                'queue' => ['default'],
                'balance' => 'auto',
                'maxProcesses' => 10,
                'maxTime' => 0,
                'maxJobs' => 0,
                'memory' => 512,
                'tries' => 3,
                'timeout' => 60,
                'nice' => 0,
            ],
            'supervisor-2' => [
                'connection' => 'redis',
                'queue' => ['high', 'default'],
                'balance' => 'auto',
                'maxProcesses' => 5,
                'tries' => 3,
            ],
        ],
    ],
];

// 启动 Horizon
php artisan horizon

// 终止 Horizon
php artisan horizon:terminate

// 暂停工作进程
php artisan horizon:pause

// 继续工作进程
php artisan horizon:continue

// 检查状态
php artisan horizon:status
```

## 监控

```php
use Illuminate\Queue\Events\JobProcessed;
use Illuminate\Queue\Events\JobFailed;
use Illuminate\Support\Facades\Queue;

// 在 AppServiceProvider 中
public function boot(): void
{
    Queue::before(function (JobProcessing $event) {
        // 作业处理前调用
    });

    Queue::after(function (JobProcessed $event) {
        // 作业处理后调用
        \Log::info('Job processed', [
            'job' => $event->job->resolveName(),
            'time' => $event->job->processingTime(),
        ]);
    });

    Queue::failing(function (JobFailed $event) {
        // 作业失败时调用
        \Log::error('Job failed', [
            'job' => $event->job->resolveName(),
            'exception' => $event->exception,
        ]);
    });
}
```

## 队列配置

```php
// config/queue.php
return [
    'default' => env('QUEUE_CONNECTION', 'sync'),

    'connections' => [
        'sync' => [
            'driver' => 'sync',
        ],

        'database' => [
            'driver' => 'database',
            'table' => 'jobs',
            'queue' => 'default',
            'retry_after' => 90,
            'after_commit' => false,
        ],

        'redis' => [
            'driver' => 'redis',
            'connection' => 'default',
            'queue' => env('REDIS_QUEUE', 'default'),
            'retry_after' => 90,
            'block_for' => null,
            'after_commit' => false,
        ],

        'sqs' => [
            'driver' => 'sqs',
            'key' => env('AWS_ACCESS_KEY_ID'),
            'secret' => env('AWS_SECRET_ACCESS_KEY'),
            'prefix' => env('SQS_PREFIX'),
            'queue' => env('SQS_QUEUE'),
            'region' => env('AWS_DEFAULT_REGION'),
        ],
    ],

    'failed' => [
        'driver' => env('QUEUE_FAILED_DRIVER', 'database-uuids'),
        'database' => env('DB_CONNECTION', 'mysql'),
        'table' => 'failed_jobs',
    ],
];
```

## 最佳实践

1. **保持作业小而专注** - 单一职责
2. **使作业具有幂等性** - 可以安全地多次运行
3. **使用类型提示** - 更好的错误检测
4. **设置合理的超时** - 防止作业挂起
5. **监控失败作业** - 设置警报
6. **对批量操作使用批处理** - 更好的性能
7. **实现适当的错误处理** - 使用 failed() 方法
8. **使用唯一作业** - 防止重复处理
9. **将长时间运行的任务排队** - 不要阻塞请求
10. **对 Redis 队列使用 Horizon** - 更好的监控
