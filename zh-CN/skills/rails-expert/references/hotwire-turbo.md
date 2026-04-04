# Hotwire & Turbo

## Turbo Drive

Turbo Drive 自动将链接点击和表单提交转换为 AJAX 请求：

```ruby
# app/controllers/articles_controller.rb
class ArticlesController < ApplicationController
  def create
    @article = Article.new(article_params)

    if @article.save
      redirect_to @article, notice: "Article created!"
    else
      render :new, status: :unprocessable_entity
    end
  end
end
```

```erb
<!-- app/views/articles/new.html.erb -->
<%= form_with model: @article do |f| %>
  <%= f.text_field :title %>
  <%= f.text_area :body %>
  <%= f.submit %>
<% end %>
```

## Turbo Frames

Turbo Frames 启用作用域页面更新：

```erb
<!-- app/views/articles/show.html.erb -->
<%= turbo_frame_tag "article_#{@article.id}" do %>
  <h1><%= @article.title %></h1>
  <p><%= @article.body %></p>
  <%= link_to "Edit", edit_article_path(@article) %>
<% end %>

<!-- app/views/articles/edit.html.erb -->
<%= turbo_frame_tag "article_#{@article.id}" do %>
  <%= form_with model: @article do |f| %>
    <%= f.text_field :title %>
    <%= f.text_area :body %>
    <%= f.submit %>
  <% end %>
<% end %>
```

使用 Turbo Frames 进行延迟加载：

```erb
<%= turbo_frame_tag "expensive_content", src: expensive_content_path, loading: :lazy %>
```

## Turbo Streams

使用 Turbo Streams 进行实时更新：

```ruby
# app/controllers/comments_controller.rb
class CommentsController < ApplicationController
  def create
    @comment = @article.comments.create(comment_params)

    respond_to do |format|
      format.turbo_stream
      format.html { redirect_to @article }
    end
  end
end
```

```erb
<!-- app/views/comments/create.turbo_stream.erb -->
<%= turbo_stream.append "comments" do %>
  <%= render @comment %>
<% end %>

<%= turbo_stream.update "comment_form" do %>
  <%= render "comments/form", comment: Comment.new %>
<% end %>
```

使用 Action Cable 进行广播：

```ruby
# app/models/comment.rb
class Comment < ApplicationRecord
  belongs_to :article

  after_create_commit -> { broadcast_append_to article, target: "comments" }
  after_update_commit -> { broadcast_replace_to article }
  after_destroy_commit -> { broadcast_remove_to article }
end
```

```erb
<!-- app/views/articles/show.html.erb -->
<%= turbo_stream_from @article %>

<div id="comments">
  <%= render @article.comments %>
</div>
```

## Stimulus 控制器

使用 Stimulus 进行 JavaScript 增强：

```javascript
// app/javascript/controllers/dropdown_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["menu"]

  toggle() {
    this.menuTarget.classList.toggle("hidden")
  }

  hide(event) {
    if (!this.element.contains(event.target)) {
      this.menuTarget.classList.add("hidden")
    }
  }
}
```

```erb
<!-- app/views/shared/_dropdown.html.erb -->
<div data-controller="dropdown" data-action="click@window->dropdown#hide">
  <button data-action="dropdown#toggle">Menu</button>
  <div data-dropdown-target="menu" class="hidden">
    <a href="#">Item 1</a>
    <a href="#">Item 2</a>
  </div>
</div>
```

## 使用 Stimulus 进行表单验证

```javascript
// app/javascript/controllers/form_validator_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["input", "error"]

  validate() {
    const value = this.inputTarget.value

    if (value.length < 3) {
      this.errorTarget.textContent = "Must be at least 3 characters"
      this.inputTarget.classList.add("border-red-500")
    } else {
      this.errorTarget.textContent = ""
      this.inputTarget.classList.remove("border-red-500")
    }
  }
}
```

## Turbo Stream 操作

七个核心操作：

```ruby
# append, prepend, replace, update, remove, before, after
turbo_stream.append "target_id", partial: "item", locals: { item: @item }
turbo_stream.prepend "target_id", html: content
turbo_stream.replace "target_id", @item
turbo_stream.update "target_id", html: "<p>Updated</p>"
turbo_stream.remove "target_id"
turbo_stream.before "target_id", partial: "item"
turbo_stream.after "target_id", partial: "item"
```

## 渐进式增强

从可用的 HTML 开始，用 Turbo 增强：

```erb
<!-- 没有 JavaScript 也能工作 -->
<%= form_with model: @article, url: articles_path do |f| %>
  <%= f.text_field :title %>
  <%= f.submit %>
<% end %>

<!-- 用 Turbo Frame 增强 -->
<%= turbo_frame_tag "article_form" do %>
  <%= form_with model: @article do |f| %>
    <%= f.text_field :title %>
    <%= f.submit %>
  <% end %>
<% end %>
```

## 常见模式

内联编辑：

```erb
<%= turbo_frame_tag dom_id(@article, :title) do %>
  <%= link_to @article.title, edit_article_path(@article),
              data: { turbo_frame: dom_id(@article, :title) } %>
<% end %>
```

模态对话框：

```erb
<%= turbo_frame_tag "modal" %>

<%= link_to "Open Modal", new_article_path,
            data: { turbo_frame: "modal" } %>
```

## 性能提示

- 对屏幕外的 frame 使用延迟加载
- 对搜索/自动完成功能的 Stimulus 操作进行防抖
- 缓存 Turbo Stream 部分
- 使用 morphing 进行最小化 DOM 更新
- 最小化 frame 嵌套深度
