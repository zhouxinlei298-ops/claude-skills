# Confluence 操作

---

## CQL 基础

### 基本查询结构

```
field OPERATOR value [AND|OR field OPERATOR value]
```

### 常用运算符

| 运算符 | 描述 | 示例 |
|--------|------|------|
| `=` | 精确匹配 | `space = "DEV"` |
| `!=` | 不等于 | `type != attachment` |
| `~` | 包含 | `title ~ "API"` |
| `!~` | 不包含 | `text !~ "deprecated"` |
| `>`, `<`, `>=`, `<=` | 比较 | `lastModified >= "2024-01-01"` |
| `IN` | 多个值 | `space IN ("DEV", "OPS")` |
| `NOT IN` | 排除 | `creator NOT IN ("bot")` |

### 字段参考

**内容字段：**
```cql
type = page                        -- Pages only
type = blogpost                    -- Blog posts
type = attachment                  -- Attachments
type = comment                     -- Comments
space = "DEVDOCS"                  -- Specific space
space.type = global                -- Global spaces
space.type = personal              -- Personal spaces
```

**搜索字段：**
```cql
title ~ "architecture"             -- Title contains
text ~ "kubernetes"                -- Full text search
content ~ "deployment"             -- Content body
label = "official"                 -- Has label
label IN ("api", "reference")      -- Multiple labels
```

**日期字段：**
```cql
created >= "2024-01-01"            -- Created after date
lastModified >= now("-30d")        -- Modified in last 30 days
created >= startOfYear()           -- Created this year
lastModified >= startOfMonth()     -- Modified this month
```

**用户字段：**
```cql
creator = currentUser()            -- Created by me
contributor = "john.doe"           -- Edited by user
mention = currentUser()            -- Mentions me
watcher = currentUser()            -- Pages I watch
favourite = currentUser()          -- My favorites
```

## 基本 CQL 模式

### 文档搜索

```cql
-- API documentation in dev space
space = "DEV" AND label = "api-docs" AND type = page

-- Recently updated architecture docs
label = "architecture" AND lastModified >= now("-7d")

-- Search for code examples
text ~ "```" AND label = "tutorial"

-- 查找过时的文档
label = "needs-review" OR lastModified <= now("-180d")

-- 本月的会议记录
label = "meeting-notes" AND created >= startOfMonth()
```

### Space Management

```cql
-- 多个空间中的所有页面
space IN ("DEV", "OPS", "PRODUCT") AND type = page

-- 个人空间内容
space.type = personal AND creator = currentUser()

-- 已归档内容
label = "archived" AND space = "LEGACY"

-- 模板
type = page AND label = "template"
```

### Content Discovery

```cql
-- 热门页面（经常被查看）
type = page AND space = "DOCS" ORDER BY lastModified DESC

-- 草稿页面
label = "draft" AND type = page

-- 无标签的页面
type = page AND space = "DEV" AND label IS NULL

-- 孤儿页面（无父级）
type = page AND ancestor IS NULL AND space = "DOCS"
```

## MCP Tool Calls

### Searching Content

```typescript
// 基本 CQL 搜索
const searchResult = await client.callTool({
  name: "confluence_search",
  arguments: {
    cql: 'space = "DEV" AND label = "api-docs"',
    limit: 25,
    expand: ["body.storage", "version", "ancestors"]
  }
});

// 解析结果
const results = JSON.parse(searchResult.content[0].text);
for (const page of results.results) {
  console.log(`${page.title} - ${page._links.webui}`);
}

// 带内容预览的搜索
const searchWithContent = await client.callTool({
  name: "confluence_search",
  arguments: {
    cql: 'text ~ "deployment" AND space = "OPS"',
    limit: 10,
    excerpt: true
  }
});
```

### Getting Page Content

```typescript
// 按 ID 获取页面
const page = await client.callTool({
  name: "confluence_get_page",
  arguments: {
    page_id: "123456",
    expand: ["body.storage", "body.view", "version", "ancestors", "children.page"]
  }
});

// 按空间和标题获取页面
const pageByTitle = await client.callTool({
  name: "confluence_get_page_by_title",
  arguments: {
    space_key: "DEV",
    title: "API Reference"
  }
});

// 获取页面子页面
const children = await client.callTool({
  name: "confluence_get_children",
  arguments: {
    page_id: "123456",
    expand: ["page"]
  }
});
```

### Creating Pages

```typescript
// 使用存储格式（XHTML）创建页面
const newPage = await client.callTool({
  name: "confluence_create_page",
  arguments: {
    space_key: "DEV",
    title: "API Authentication Guide",
    parent_id: "123456",  // 可选的父级页面
    body: `
      <h2>Overview</h2>
      <p>This guide covers authentication methods for our API.</p>

      <h2>OAuth 2.0</h2>
      <p>We support OAuth 2.0 with the following grant types:</p>
      <ul>
        <li>Authorization Code</li>
        <li>Client Credentials</li>
      </ul>

      <ac:structured-macro ac:name="code">
        <ac:parameter ac:name="language">bash</ac:parameter>
        <ac:plain-text-body><![CDATA[curl -X POST https://api.example.com/oauth/token \\
  -d "grant_type=client_credentials" \\
  -d "client_id=YOUR_CLIENT_ID" \\
  -d "client_secret=YOUR_SECRET"]]></ac:plain-text-body>
      </ac:structured-macro>

      <h2>API Tokens</h2>
      <p>For simple integrations, use API tokens:</p>
      <ac:structured-macro ac:name="info">
        <ac:rich-text-body>
          <p>API tokens are tied to your user account and have the same permissions.</p>
        </ac:rich-text-body>
      </ac:structured-macro>
    `,
    labels: ["api-docs", "authentication", "official"]
  }
});

console.log(`Created page: ${newPage.content[0].text}`);
```

### Updating Pages

```typescript
// 更新页面内容
await client.callTool({
  name: "confluence_update_page",
  arguments: {
    page_id: "123456",
    title: "API Authentication Guide (Updated)",
    body: "<h2>Updated Content</h2><p>New documentation here...</p>",
    version_number: 5,  // 当前版本 + 1
    version_message: "Added OAuth 2.1 section"
  }
});

// 追加到现有页面
const currentPage = await client.callTool({
  name: "confluence_get_page",
  arguments: {
    page_id: "123456",
    expand: ["body.storage", "version"]
  }
});

const pageData = JSON.parse(currentPage.content[0].text);
const currentBody = pageData.body.storage.value;
const newSection = `
  <h2>New Section</h2>
  <p>Additional content appended to the page.</p>
`;

await client.callTool({
  name: "confluence_update_page",
  arguments: {
    page_id: "123456",
    title: pageData.title,
    body: currentBody + newSection,
    version_number: pageData.version.number + 1
  }
});
```

### Working with Comments

```typescript
// 添加页面评论
await client.callTool({
  name: "confluence_add_comment",
  arguments: {
    page_id: "123456",
    body: "<p>This section needs to be updated for v2.0 changes.</p>"
  }
});

// 获取页面评论
const comments = await client.callTool({
  name: "confluence_get_comments",
  arguments: {
    page_id: "123456",
    expand: ["body.storage", "version"]
  }
});

// 回复评论
await client.callTool({
  name: "confluence_add_comment",
  arguments: {
    page_id: "123456",
    parent_comment_id: "789012",
    body: "<p>Good catch! I'll update this section.</p>"
  }
});
```

### Managing Labels

```typescript
// 为页面添加标签
await client.callTool({
  name: "confluence_add_labels",
  arguments: {
    page_id: "123456",
    labels: ["reviewed", "q1-2024", "api-v2"]
  }
});

// 移除标签
await client.callTool({
  name: "confluence_remove_label",
  arguments: {
    page_id: "123456",
    label: "draft"
  }
});

// 获取页面标签
const labels = await client.callTool({
  name: "confluence_get_labels",
  arguments: {
    page_id: "123456"
  }
});
```

### Space Operations

```typescript
// 获取空间信息
const space = await client.callTool({
  name: "confluence_get_space",
  arguments: {
    space_key: "DEV",
    expand: ["description", "homepage"]
  }
});

// 列出所有空间
const spaces = await client.callTool({
  name: "confluence_list_spaces",
  arguments: {
    type: "global",
    limit: 100
  }
});

// 获取空间内容
const spaceContent = await client.callTool({
  name: "confluence_get_space_content",
  arguments: {
    space_key: "DEV",
    depth: "root",  // 或 "all"
    expand: ["children.page"]
  }
});
```

## Storage Format Reference

### Common Macros

```xml
<!-- 代码块 -->
<ac:structured-macro ac:name="code">
  <ac:parameter ac:name="language">python</ac:parameter>
  <ac:parameter ac:name="title">Example</ac:parameter>
  <ac:plain-text-body><![CDATA[print("Hello, World!")]]></ac:plain-text-body>
</ac:structured-macro>

<!-- 信息面板 -->
<ac:structured-macro ac:name="info">
  <ac:parameter ac:name="title">Note</ac:parameter>
  <ac:rich-text-body>
    <p>Important information here.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<!-- 警告面板 -->
<ac:structured-macro ac:name="warning">
  <ac:rich-text-body>
    <p>Be careful with this operation!</p>
  </ac:rich-text-body>
</ac:structured-macro>

<!-- 目录 -->
<ac:structured-macro ac:name="toc">
  <ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>

<!-- Jira 问题链接 -->
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="key">PROJ-123</ac:parameter>
</ac:structured-macro>

<!-- Jira 问题表格 -->
<ac:structured-macro ac:name="jira">
  <ac:parameter ac:name="jqlQuery">project = PROJ AND sprint in openSprints()</ac:parameter>
  <ac:parameter ac:name="columns">key,summary,status,assignee</ac:parameter>
</ac:structured-macro>

<!-- 可展开部分 -->
<ac:structured-macro ac:name="expand">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body>
    <p>Hidden content here.</p>
  </ac:rich-text-body>
</ac:structured-macro>

<!-- 包含页面 -->
<ac:structured-macro ac:name="include">
  <ac:parameter ac:name=""><ri:page ri:content-title="Shared Footer" /></ac:parameter>
</ac:structured-macro>
```

### Formatting Elements

```xml
<!-- 状态徽章 -->
<ac:structured-macro ac:name="status">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">APPROVED</ac:parameter>
</ac:structured-macro>

<!-- 用户提及 -->
<ac:link><ri:user ri:account-id="557058:f3c7..." /></ac:link>

<!-- 页面链接 -->
<ac:link><ri:page ri:content-title="Target Page" ri:space-key="DEV" /></ac:link>

<!-- 附件 -->
<ac:link><ri:attachment ri:filename="diagram.png" /></ac:link>

<!-- 附件图片 -->
<ac:image><ri:attachment ri:filename="screenshot.png" /></ac:image>

<!-- 外部图片 -->
<ac:image><ri:url ri:value="https://example.com/image.png" /></ac:image>
```

## Pagination Handling

```typescript
async function getAllPages(cql: string): Promise<Page[]> {
  const allPages: Page[] = [];
  let start = 0;
  const limit = 100;

  while (true) {
    const result = await client.callTool({
      name: "confluence_search",
      arguments: {
        cql,
        start,
        limit,
        expand: ["body.storage"]
      }
    });

    const response = JSON.parse(result.content[0].text);
    allPages.push(...response.results);

    if (response.results.length < limit || !response._links.next) {
      break;
    }

    start += limit;
  }

  return allPages;
}
```

## Error Handling

```typescript
async function safeConfluenceCall<T>(operation: () => Promise<T>): Promise<T> {
  try {
    return await operation();
  } catch (error: any) {
    const status = error.response?.status;

    switch (status) {
      case 404:
        throw new Error(`Page or space not found: ${error.message}`);
      case 403:
        throw new Error(`Permission denied. Check space permissions.`);
      case 409:
        throw new Error(`Version conflict. Page was modified. Refresh and retry.`);
      case 429:
        const retryAfter = error.response?.headers?.['retry-after'] || 60;
        throw new Error(`Rate limited. Retry after ${retryAfter} seconds.`);
      default:
        throw error;
    }
  }
}
```

## Common Anti-Patterns

**Avoid:**
```cql
-- 太宽泛（慢）
text ~ "the"

-- 缺少引号
space = DEV DOCS  -- 错误
space = "DEV DOCS"  -- 正确

-- 无效日期格式
created >= 2024-01-01  -- 错误
created >= "2024-01-01"  -- 正确
```

**最佳实践：**
- 尽可能指定空间以加快查询速度
- 使用标签进行分类和过滤
- 结合文本搜索和特定字段
- 缓存频繁访问的页面内容
- 优雅处理版本冲突

## 相关参考

- `common-workflows.md` - 文档同步和自动化
- `jira-queries.md` - 将 Confluence 页面链接到 Jira 问题
- `authentication-patterns.md` - API 访问配置