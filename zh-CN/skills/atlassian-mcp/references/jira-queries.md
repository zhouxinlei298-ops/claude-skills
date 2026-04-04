# Jira 查询和操作

---

## JQL 基础

### 基本查询结构

```
field OPERATOR value [AND|OR field OPERATOR value]
```

### 常用运算符

| 运算符 | 描述 | 示例 |
|--------|------|------|
| `=` | 精确匹配 | `project = "PROJ"` |
| `!=` | 不等于 | `status != Done` |
| `~` | 包含（文本搜索） | `summary ~ "login bug"` |
| `!~` | 不包含 | `description !~ "test"` |
| `>`, `<`, `>=`, `<=` | 比较 | `created >= -7d` |
| `IN` | 多个值 | `status IN (Open, "In Progress")` |
| `NOT IN` | 排除值 | `assignee NOT IN (john, jane)` |
| `IS` | 空值检查 | `assignee IS EMPTY` |
| `IS NOT` | 非空 | `resolution IS NOT EMPTY` |
| `WAS` | 历史状态 | `status WAS "In Progress"` |
| `CHANGED` | 字段变更 | `status CHANGED FROM Open` |

### 字段参考

**标准字段：**
```jql
project = PROJ
issuetype = Bug
status = "In Progress"
priority = High
assignee = currentUser()
reporter = "john.doe"
resolution = Unresolved
labels = backend
component = "API"
fixVersion = "2.0"
affectsVersion = "1.5"
```

**日期字段：**
```jql
created >= -30d                    -- Last 30 days
updated >= "2024-01-01"           -- Since specific date
due <= endOfWeek()                 -- Due this week
resolved >= startOfMonth()         -- Resolved this month
```

**文本搜索：**
```jql
summary ~ "authentication"         -- Summary contains
description ~ "error AND login"    -- Description search
text ~ "payment failed"            -- All text fields
comment ~ "blocked"                -- Comment contains
```

## 基本 JQL 模式

### Sprint 和待办事项查询

```jql
-- Current sprint issues
sprint in openSprints() AND project = PROJ

-- Backlog items
sprint IS EMPTY AND resolution IS EMPTY AND project = PROJ

-- Sprint completion
sprint = "Sprint 23" AND status = Done

-- Spillover from last sprint
sprint in closedSprints() AND resolution IS EMPTY

-- Ready for sprint planning
status = "Ready for Dev" AND sprint IS EMPTY
```

### Bug 跟踪

```jql
-- Open bugs by priority
issuetype = Bug AND resolution IS EMPTY ORDER BY priority DESC

-- Critical production bugs
issuetype = Bug AND priority IN (Highest, High)
  AND labels = production AND resolution IS EMPTY

-- Bugs created this week
issuetype = Bug AND created >= startOfWeek()

-- Bugs without reproduction steps
issuetype = Bug AND "Reproduction Steps" IS EMPTY
  AND resolution IS EMPTY

-- Regression bugs
issuetype = Bug AND labels = regression AND fixVersion = "2.0"
```

### 团队工作量

```jql
-- My open issues
assignee = currentUser() AND resolution IS EMPTY

-- Unassigned high priority
assignee IS EMPTY AND priority IN (Highest, High)
  AND resolution IS EMPTY

-- Team member workload
assignee = "jane.smith" AND sprint in openSprints()

-- Blocked issues
status = Blocked OR labels = blocked

-- Stale issues (no update in 14 days)
updated <= -14d AND resolution IS EMPTY
```

### 发布管理

```jql
-- Release candidates
fixVersion = "2.0" AND status = "Ready for Release"

-- Missing fix version
resolution = Done AND fixVersion IS EMPTY AND updated >= -30d

-- Release blockers
fixVersion = "2.0" AND priority = Blocker AND resolution IS EMPTY

-- Changelog items
fixVersion = "2.0" AND resolution = Done ORDER BY issuetype
```

## MCP 工具调用

### 搜索问题

```typescript
// Basic JQL search
const searchResult = await client.callTool({
  name: "jira_search",
  arguments: {
    jql: "project = PROJ AND sprint in openSprints()",
    max_results: 50,
    fields: ["summary", "status", "assignee", "priority"]
  }
});

// Parse response
const issues = JSON.parse(searchResult.content[0].text);
for (const issue of issues.issues) {
  console.log(`${issue.key}: ${issue.fields.summary}`);
}
```

### 获取问题详情

```typescript
// Get single issue with all fields
const issue = await client.callTool({
  name: "jira_get_issue",
  arguments: {
    issue_key: "PROJ-123",
    expand: ["changelog", "comments", "transitions"]
  }
});

// Get issue with specific fields
const issuePartial = await client.callTool({
  name: "jira_get_issue",
  arguments: {
    issue_key: "PROJ-123",
    fields: ["summary", "description", "customfield_10001"]
  }
});
```

### 创建问题

```typescript
// Create a bug
const newBug = await client.callTool({
  name: "jira_create_issue",
  arguments: {
    project_key: "PROJ",
    issue_type: "Bug",
    summary: "Login fails with SSO enabled",
    description: {
      type: "doc",
      version: 1,
      content: [
        {
          type: "paragraph",
          content: [{ type: "text", text: "Users cannot log in when SSO is enabled." }]
        },
        {
          type: "heading",
          attrs: { level: 3 },
          content: [{ type: "text", text: "Steps to Reproduce" }]
        },
        {
          type: "orderedList",
          content: [
            { type: "listItem", content: [{ type: "paragraph", content: [{ type: "text", text: "Enable SSO in settings" }] }] },
            { type: "listItem", content: [{ type: "paragraph", content: [{ type: "text", text: "Log out" }] }] },
            { type: "listItem", content: [{ type: "paragraph", content: [{ type: "text", text: "Attempt to log in via SSO" }] }] }
          ]
        }
      ]
    },
    priority: "High",
    labels: ["sso", "authentication", "production"],
    components: ["Authentication"],
    assignee: "jane.smith"
  }
});

console.log(`Created: ${newBug.content[0].text}`); // PROJ-456
```

### 更新问题

```typescript
// Update issue fields
await client.callTool({
  name: "jira_update_issue",
  arguments: {
    issue_key: "PROJ-123",
    fields: {
      summary: "Updated summary",
      priority: { name: "Highest" },
      labels: ["urgent", "production"]
    }
  }
});

// Add comment
await client.callTool({
  name: "jira_add_comment",
  arguments: {
    issue_key: "PROJ-123",
    body: "Investigating this issue. Initial analysis suggests a race condition."
  }
});

// Transition issue
await client.callTool({
  name: "jira_transition_issue",
  arguments: {
    issue_key: "PROJ-123",
    transition: "In Progress"
  }
});
```

### Sprint 操作

```typescript
// Get active sprints
const sprints = await client.callTool({
  name: "jira_get_sprints",
  arguments: {
    board_id: 42,
    state: "active"
  }
});

// Move issue to sprint
await client.callTool({
  name: "jira_move_to_sprint",
  arguments: {
    sprint_id: 123,
    issue_keys: ["PROJ-100", "PROJ-101", "PROJ-102"]
  }
});

// Get sprint report
const report = await client.callTool({
  name: "jira_get_sprint_report",
  arguments: {
    board_id: 42,
    sprint_id: 123
  }
});
```

### 问题链接

使用 `jira_create_issue_link` 在问题之间创建依赖关系。

> **参数名称违反直觉。** 命名反映了 Jira 内部的"入站/出站"链接方向，而不是自然的英语。每个链接调用都要对照下表验证。

#### "Blocks" 链接的参数语义

| 参数 | 角色 | 含义 |
|------|------|------|
| `inward_issue_key` | **阻塞者** | 此问题阻塞另一个 |
| `outward_issue_key` | **被阻塞者** | 此问题被另一个阻塞 |

**记忆方法：** `inward_issue_key` = 接收入站描述（"is blocked by"）的问题 —— 但它是*阻塞者*。想想："入站键是箭头指向 FROM 的地方。"

#### 单个 Blocks 链接

```typescript
// Make AUTH-1 block AUTH-2
// AUTH-1 will show: "blocks AUTH-2"
// AUTH-2 will show: "is blocked by AUTH-1"
await client.callTool({
  name: "jira_create_issue_link",
  arguments: {
    link_type: "Blocks",
    inward_issue_key: "AUTH-1",   // blocker
    outward_issue_key: "AUTH-2"   // blocked
  }
});
```

#### 链接依赖链

当创建链 A → B → C（A 阻塞 B，B 阻塞 C）时：

```typescript
const chain = [
  { blocker: "AUTH-1", blocked: "AUTH-2" },
  { blocker: "AUTH-2", blocked: "AUTH-3" },
  { blocker: "AUTH-3", blocked: "AUTH-4" }
];

for (const dep of chain) {
  await client.callTool({
    name: "jira_create_issue_link",
    arguments: {
      link_type: "Blocks",
      inward_issue_key: dep.blocker,
      outward_issue_key: dep.blocked
    }
  });

  // Respect rate limits between link operations
  await delay(100);
}
```

#### 其他链接类型

相同的 `inward`/`outward` 模式适用于所有链接类型：

| 链接类型 | `inward_issue_key` 显示 | `outward_issue_key` 显示 |
|----------|--------------------------|---------------------------|
| `Blocks` | "blocks [outward]" | "is blocked by [inward]" |
| `Duplicate` | "duplicates [outward]" | "is duplicated by [inward]" |
| `Relates` | "relates to [outward]" | "relates to [inward]" |

```typescript
// Mark PROJ-10 as a duplicate of PROJ-5
await client.callTool({
  name: "jira_create_issue_link",
  arguments: {
    link_type: "Duplicate",
    inward_issue_key: "PROJ-10",   // the duplicate
    outward_issue_key: "PROJ-5"    // the original
  }
});
```

#### 反模式：反向参数

```typescript
// WRONG — This makes AUTH-2 block AUTH-1 (backwards!)
await client.callTool({
  name: "jira_create_issue_link",
  arguments: {
    link_type: "Blocks",
    inward_issue_key: "AUTH-2",   // accidentally made AUTH-2 the blocker
    outward_issue_key: "AUTH-1"   // accidentally made AUTH-1 the blocked
  }
});
```

始终验证：创建链接后，阻塞者（`inward_issue_key`）应该在 Jira 问题视图中显示 "blocks [outward]"。

## 分页处理

```typescript
async function getAllIssues(jql: string): Promise<Issue[]> {
  const allIssues: Issue[] = [];
  let startAt = 0;
  const maxResults = 100;

  while (true) {
    const result = await client.callTool({
      name: "jira_search",
      arguments: {
        jql,
        start_at: startAt,
        max_results: maxResults,
        fields: ["summary", "status", "assignee"]
      }
    });

    const response = JSON.parse(result.content[0].text);
    allIssues.push(...response.issues);

    if (startAt + response.issues.length >= response.total) {
      break;
    }

    startAt += maxResults;
  }

  return allIssues;
}
```

## 批量操作

```typescript
// Bulk update with JQL
async function bulkUpdateLabels(jql: string, addLabels: string[]) {
  const issues = await getAllIssues(jql);

  for (const issue of issues) {
    const existingLabels = issue.fields.labels || [];
    await client.callTool({
      name: "jira_update_issue",
      arguments: {
        issue_key: issue.key,
        fields: {
          labels: [...new Set([...existingLabels, ...addLabels])]
        }
      }
    });

    // Respect rate limits
    await delay(100);
  }
}

// Usage
await bulkUpdateLabels(
  'project = PROJ AND sprint in openSprints() AND labels = backend',
  ['q4-priority', 'needs-review']
);
```

## 错误处理

```typescript
async function safeJiraCall<T>(
  operation: () => Promise<T>,
  retries = 3
): Promise<T> {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const status = error.response?.status;

      // Don't retry client errors (except rate limits)
      if (status >= 400 && status < 500 && status !== 429) {
        throw error;
      }

      // Rate limited - wait and retry
      if (status === 429) {
        const retryAfter = parseInt(error.response?.headers?.['retry-after'] || '60');
        console.log(`Rate limited. Waiting ${retryAfter}s...`);
        await delay(retryAfter * 1000);
        continue;
      }

      // Server error - exponential backoff
      if (attempt < retries) {
        const backoff = Math.pow(2, attempt) * 1000;
        console.log(`Attempt ${attempt} failed. Retrying in ${backoff}ms...`);
        await delay(backoff);
      } else {
        throw error;
      }
    }
  }
  throw new Error('Unexpected end of retry loop');
}
```

## 常见反模式

**避免：**
```jql
-- Too broad (slow, may timeout)
project IS NOT EMPTY

-- Missing quotes for multi-word values
status = In Progress  -- WRONG
status = "In Progress"  -- CORRECT

-- Case sensitivity issues
assignee = John  -- May fail
assignee = "john.doe@company.com"  -- CORRECT

-- Inefficient ordering
ORDER BY created  -- Missing direction
ORDER BY created DESC  -- CORRECT
```

## 相关参考

- `common-workflows.md` - 端到端工作流模式
- `authentication-patterns.md` - API 调用的凭据设置
- `confluence-operations.md` - 将 Jira 问题链接到 Confluence 页面