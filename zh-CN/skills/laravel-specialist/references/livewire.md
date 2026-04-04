# Livewire 组件

## 组件模式

```php
namespace App\Http\Livewire;

use Livewire\Component;
use Livewire\WithPagination;
use Livewire\WithFileUploads;
use App\Models\Post;

class PostList extends Component
{
    use WithPagination, WithFileUploads;

    public string $search = '';
    public string $sortBy = 'created_at';
    public string $sortDirection = 'desc';
    public ?int $categoryId = null;

    protected $queryString = [
        'search' => ['except' => ''],
        'sortBy' => ['except' => 'created_at'],
        'categoryId' => ['except' => null],
    ];

    public function updatingSearch(): void
    {
        $this->resetPage();
    }

    public function sortBy(string $field): void
    {
        if ($this->sortBy === $field) {
            $this->sortDirection = $this->sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            $this->sortBy = $field;
            $this->sortDirection = 'asc';
        }
    }

    public function render()
    {
        return view('livewire.post-list', [
            'posts' => Post::query()
                ->when($this->search, fn($q) => $q->where('title', 'like', "%{$this->search}%"))
                ->when($this->categoryId, fn($q) => $q->where('category_id', $this->categoryId))
                ->orderBy($this->sortBy, $this->sortDirection)
                ->paginate(10),
        ]);
    }
}
```

## Blade 模板

```blade
<div>
    {{-- Search --}}
    <input
        type="text"
        wire:model.debounce.300ms="search"
        placeholder="Search posts..."
        class="form-input"
    >

    {{-- Filter by category --}}
    <select wire:model="categoryId">
        <option value="">All Categories</option>
        @foreach($categories as $category)
            <option value="{{ $category->id }}">{{ $category->name }}</option>
        @endforeach
    </select>

    {{-- Sortable table --}}
    <table>
        <thead>
            <tr>
                <th wire:click="sortBy('title')" style="cursor: pointer">
                    Title
                    @if($sortBy === 'title')
                        <span>{{ $sortDirection === 'asc' ? '↑' : '↓' }}</span>
                    @endif
                </th>
                <th wire:click="sortBy('created_at')" style="cursor: pointer">
                    Date
                    @if($sortBy === 'created_at')
                        <span>{{ $sortDirection === 'asc' ? '↑' : '↓' }}</span>
                    @endif
                </th>
            </tr>
        </thead>
        <tbody>
            @foreach($posts as $post)
                <tr>
                    <td>{{ $post->title }}</td>
                    <td>{{ $post->created_at->diffForHumans() }}</td>
                </tr>
            @endforeach
        </tbody>
    </table>

    {{-- Pagination --}}
    {{ $posts->links() }}

    {{-- Loading states --}}
    <div wire:loading wire:target="search">
        Searching...
    </div>
</div>
```

## 表单组件

```php
namespace App\Http\Livewire;

use Livewire\Component;
use App\Models\Post;

class PostForm extends Component
{
    public ?Post $post = null;
    public string $title = '';
    public string $content = '';
    public array $tags = [];
    public $image;

    protected function rules(): array
    {
        return [
            'title' => 'required|min:3|max:255',
            'content' => 'required|min:10',
            'tags' => 'array|max:5',
            'tags.*' => 'exists:tags,id',
            'image' => 'nullable|image|max:2048',
        ];
    }

    public function mount(?Post $post = null): void
    {
        if ($post) {
            $this->post = $post;
            $this->title = $post->title;
            $this->content = $post->content;
            $this->tags = $post->tags->pluck('id')->toArray();
        }
    }

    public function updated($propertyName): void
    {
        $this->validateOnly($propertyName);
    }

    public function save(): void
    {
        $validated = $this->validate();

        if ($this->post) {
            $this->post->update($validated);
            $message = 'Post updated successfully!';
        } else {
            $this->post = Post::create($validated);
            $message = 'Post created successfully!';
        }

        if ($this->image) {
            $this->post->update([
                'image_path' => $this->image->store('posts', 'public'),
            ]);
        }

        $this->post->tags()->sync($this->tags);

        session()->flash('message', $message);
        $this->redirect(route('posts.show', $this->post));
    }

    public function render()
    {
        return view('livewire.post-form');
    }
}
```

## 表单模板

```blade
<form wire:submit.prevent="save">
    {{-- Title --}}
    <div>
        <label for="title">Title</label>
        <input
            type="text"
            wire:model.defer="title"
            id="title"
            class="@error('title') border-red-500 @enderror"
        >
        @error('title')
            <span class="text-red-500">{{ $message }}</span>
        @enderror
    </div>

    {{-- Content --}}
    <div>
        <label for="content">Content</label>
        <textarea
            wire:model.defer="content"
            id="content"
            class="@error('content') border-red-500 @enderror"
        ></textarea>
        @error('content')
            <span class="text-red-500">{{ $message }}</span>
        @enderror
    </div>

    {{-- Tags --}}
    <div>
        <label>Tags</label>
        @foreach($availableTags as $tag)
            <label>
                <input
                    type="checkbox"
                    wire:model="tags"
                    value="{{ $tag->id }}"
                >
                {{ $tag->name }}
            </label>
        @endforeach
        @error('tags')
            <span class="text-red-500">{{ $message }}</span>
        @enderror
    </div>

    {{-- File Upload --}}
    <div>
        <label>Image</label>
        <input type="file" wire:model="image">

        @error('image')
            <span class="text-red-500">{{ $message }}</span>
        @enderror

        {{-- Upload progress --}}
        <div wire:loading wire:target="image">
            Uploading...
        </div>

        {{-- Preview --}}
        @if ($image)
            <img src="{{ $image->temporaryUrl() }}" alt="Preview">
        @endif
    </div>

    {{-- Submit --}}
    <button type="submit" wire:loading.attr="disabled">
        <span wire:loading.remove>Save</span>
        <span wire:loading>Saving...</span>
    </button>
</form>

@if (session()->has('message'))
    <div class="alert alert-success">
        {{ session('message') }}
    </div>
@endif
```

## 实时验证

```php
class PostForm extends Component
{
    public string $title = '';

    protected $rules = [
        'title' => 'required|min:3|unique:posts,title',
    ];

    // Real-time validation
    public function updated($propertyName): void
    {
        $this->validateOnly($propertyName);
    }

    // Custom validation messages
    protected $messages = [
        'title.required' => 'The post title is required.',
        'title.min' => 'The title must be at least 3 characters.',
        'title.unique' => 'This title is already taken.',
    ];

    // Custom attribute names
    protected $validationAttributes = [
        'title' => 'post title',
    ];
}
```

## 事件

```php
// Emit event
class PostList extends Component
{
    public function deletePost($postId): void
    {
        Post::find($postId)->delete();

        $this->emit('postDeleted', $postId);
    }
}

// Listen to event
class PostStats extends Component
{
    protected $listeners = ['postDeleted' => 'updateStats'];

    public function updateStats($postId): void
    {
        // Update statistics
    }
}

// Emit to specific component
$this->emitTo('post-stats', 'refresh');

// Emit to parent/children
$this->emitUp('saved');
$this->emitSelf('refresh');

// Browser events
$this->dispatchBrowserEvent('post-saved', ['id' => $post->id]);
```

## 监听浏览器事件

```blade
<div
    x-data
    @post-saved.window="alert('Post saved!')"
>
    <!-- content -->
</div>

<script>
window.addEventListener('post-saved', event => {
    console.log('Post ID:', event.detail.id);
});
</script>
```

## 轮询

```blade
{{-- Poll every 2 seconds --}}
<div wire:poll.2s>
    Current time: {{ now() }}
</div>

{{-- Poll specific action --}}
<div wire:poll.5s="checkStatus">
    Status: {{ $status }}
</div>

{{-- Keep polling until condition --}}
<div wire:poll.keep-alive.2s>
    <!-- content -->
</div>
```

## 加载状态

```blade
{{-- Basic loading state --}}
<div wire:loading>
    Loading...
</div>

{{-- Target specific action --}}
<div wire:loading wire:target="save">
    Saving...
</div>

{{-- Hide element while loading --}}
<div wire:loading.remove>
    Content (hidden during load)
</div>

{{-- Delay loading indicator --}}
<div wire:loading.delay>
    This appears after 200ms
</div>

{{-- Custom delay --}}
<div wire:loading.delay.longest>
    This appears after 1s
</div>

{{-- Loading classes --}}
<button
    wire:click="save"
    wire:loading.class="opacity-50"
    wire:loading.class.remove="bg-blue-500"
>
    Save
</button>

{{-- Loading attributes --}}
<button
    wire:click="save"
    wire:loading.attr="disabled"
>
    Save
</button>
```

## Traits

```php
// Pagination
use Livewire\WithPagination;

class PostList extends Component
{
    use WithPagination;

    public function render()
    {
        return view('livewire.post-list', [
            'posts' => Post::paginate(10),
        ]);
    }
}

// File uploads
use Livewire\WithFileUploads;

class UploadPhoto extends Component
{
    use WithFileUploads;

    public $photo;

    public function save(): void
    {
        $this->validate([
            'photo' => 'image|max:1024',
        ]);

        $this->photo->store('photos');
    }
}
```

## 授权

```php
class PostForm extends Component
{
    public Post $post;

    public function mount(Post $post): void
    {
        $this->authorize('update', $post);
        $this->post = $post;
    }

    public function save(): void
    {
        $this->authorize('update', $this->post);
        // Save logic
    }
}
```

## 性能建议

1. **使用 wire:model.defer** -- 在表单提交时批量更新
2. **延迟加载组件** -- 对重操作使用 wire:init
3. **缓存计算属性** -- 使用 #[Computed] 属性
4. **隐藏时禁用轮询** -- 使用 wire:poll.visible
5. **优化查询** -- 预加载关联关系
6. **使用 wire:key** -- 防止整个列表重新渲染
7. **对输入进行防抖** -- 使用 wire:model.debounce
8. **使用分页** -- 不要一次加载所有记录

```php
use Livewire\Attributes\Computed;

class PostList extends Component
{
    #[Computed]
    public function posts()
    {
        return Post::with('user')->paginate(10);
    }

    public function render()
    {
        return view('livewire.post-list');
    }
}
```

```blade
{{-- Access computed property --}}
@foreach($this->posts as $post)
    <!-- content -->
@endforeach
```
