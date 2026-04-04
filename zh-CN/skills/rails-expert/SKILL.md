---
name: rails-expert
description: Rails 7+ specialist that optimizes Active Record queries with includes/eager_load, implements Turbo Frames and Turbo Streams for partial page updates, configures Action Cable for WebSocket connections, sets up Sidekiq workers for background job processing, and writes comprehensive RSpec test suites. Use when building Rails 7+ web applications with Hotwire, real-time features, or background job processing. Invoke for Active Record optimization, Turbo Frames/Streams, Action Cable, Sidekiq, RSpec Rails.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: backend
  triggers: Rails, Ruby on Rails, Hotwire, Turbo Frames, Turbo Streams, Action Cable, Active Record, Sidekiq, RSpec Rails
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, database-optimizer
---

# Rails Expert

## 核心工作流程

1. **分析需求** — 识别模型、路由、实时需求和后台任务
2. **搭建资源** — `rails generate model User name:string email:string`、`rails generate controller Users`
3. **运行迁移** — `rails db:migrate` 并使用 `rails db:schema:dump` 验证 schema
   - 如果迁移失败：检查 `db/schema.rb` 是否存在冲突，使用 `rails db:rollback` 回滚，修复后重试
4. **实现功能** — 编写控制器、模型，添加 Hotwire（参见下方参考指南）
5. **验证** — `bundle exec rspec` 必须通过；`bundle exec rubocop` 检查代码风格
   - 如果测试失败：检查错误输出，修复失败的测试用例，使用 `--format documentation` 重新运行获取详细信息
   - 如果在审查中发现 N+1 查询：添加 `includes`/`eager_load`（参见常见模式）并重新运行测试
6. **优化** — 审查 N+1 查询，添加缺失的索引，添加缓存

## 参考指南

根据上下文加载详细指南：

| 主题 | 参考文件 | 加载时机 |
|------|----------|----------|
| Hotwire/Turbo | `references/hotwire-turbo.md` | Turbo Frames、Streams、Stimulus 控制器 |
| Active Record | `references/active-record.md` | 模型、关联、查询、性能 |
| 后台任务 | `references/background-jobs.md` | Sidekiq、任务设计、队列、错误处理 |
| 测试 | `references/rspec-testing.md` | 模型/请求/系统测试、工厂 |
| API 开发 | `references/api-development.md` | API-only 模式、序列化、认证 |

## 常见模式

### 使用 includes/eager_load 防止 N+1 查询

```ruby
# BAD — triggers N+1
posts = Post.all
posts.each { |post| puts post.author.name }

# GOOD — eager load association
posts = Post.includes(:author).all
posts.each { |post| puts post.author.name }

# GOOD — eager_load forces a JOIN (useful when filtering on association)
posts = Post.eager_load(:author).where(authors: { verified: true })
```

### Turbo Frame 设置（局部页面更新）

```erb
<%# app/views/posts/index.html.erb %>
<%= turbo_frame_tag "posts" do %>
  <%= render @posts %>
  <%= link_to "Load More", posts_path(page: @next_page) %>
<% end %>

<%# app/views/posts/_post.html.erb %>
<%= turbo_frame_tag dom_id(post) do %>
  <h2><%= post.title %></h2>
  <%= link_to "Edit", edit_post_path(post) %>
<% end %>
```

```ruby
# app/controllers/posts_controller.rb
def index
  @posts = Post.includes(:author).page(params[:page])
  @next_page = @posts.next_page
end
```

### Sidekiq Worker 模板

```ruby
# app/jobs/send_welcome_email_job.rb
class SendWelcomeEmailJob < ApplicationJob
  queue_as :default
  sidekiq_options retry: 3, dead: false

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome(user).deliver_now
  rescue ActiveRecord::RecordNotFound => e
    Rails.logger.warn("SendWelcomeEmailJob: user #{user_id} not found — #{e.message}")
    # Do not re-raise; record is gone, no point retrying
  end
end

# Enqueue from controller or model callback
SendWelcomeEmailJob.perform_later(user.id)
```

### Strong Parameters（控制器模板）

```ruby
# app/controllers/posts_controller.rb
class PostsController < ApplicationController
  before_action :set_post, only: %i[show edit update destroy]

  def create
    @post = Post.new(post_params)
    if @post.save
      redirect_to @post, notice: "Post created."
    else
      render :new, status: :unprocessable_entity
    end
  end

  private

  def set_post
    @post = Post.find(params[:id])
  end

  def post_params
    params.require(:post).permit(:title, :body, :published_at)
  end
end
```

## 约束

### 必须做
- 在每个涉及关联的集合查询中使用 `includes`/`eager_load` 防止 N+1 查询
- 编写全面的测试，目标覆盖率 >95%
- 将复杂业务逻辑放入 Service Object；保持控制器精简
- 为每个用于 `WHERE`、`ORDER BY` 或 `JOIN` 的列添加数据库索引
- 将耗时操作卸载到 Sidekiq — 绝不在请求周期中同步执行

### 不能做
- 跳过迁移来更改 schema
- 在不进行参数净化的情况下使用原生 SQL（仅限 `sanitize_sql` 或参数化查询）
- 在 URL 中暴露内部 ID 而不考虑安全性

## 输出模板

实现 Rails 功能时，请提供：
1. 迁移文件（如果需要更改 schema）
2. 包含关联和验证的模型文件
3. 包含 RESTful 操作和 strong parameters 的控制器
4. 视图文件或 Hotwire 设置
5. 模型和请求的测试文件
6. 架构决策的简要说明
