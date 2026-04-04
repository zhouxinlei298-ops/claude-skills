---
name: atlassian-mcp
description: Integrates with Atlassian products to manage project tracking and documentation via MCP protocol. Use when querying Jira issues with JQL filters, creating and updating tickets with custom fields, searching or editing Confluence pages with CQL, managing sprints and backlogs, setting up MCP server authentication, syncing documentation, or debugging Atlassian API integrations.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: platform
  triggers: Jira, Confluence, Atlassian, MCP, tickets, issues, wiki, JQL, CQL, sprint, backlog, project management
  role: expert
  scope: implementation
  output-format: code
  related-skills: mcp-developer, api-designer, security-reviewer
---

# Atlassian MCP Expert

## 何时使用此技能

- 使用 JQL 过滤器查询 Jira 事务
- 搜索或创建 Confluence 页面
- 自动化 Sprint 工作流和待办事项管理
- 设置 MCP 服务器认证（OAuth/API 令牌）
- 将会议笔记同步到 Jira 事务
- 从事务数据生成文档
- 调试 Atlassian API 集成问题
- 在官方与开源 MCP 服务器之间做出选择

## 核心工作流程

1. **选择服务器** - 选择官方云服务、开源或自托管 MCP 服务器
2. **认证** - 配置 OAuth 2.1、API 令牌或 PAT 凭证
3. **设计查询** - 为 Jira 编写 JQL，为 Confluence 编写 CQL；先用 `maxResults=1` 验证再全量执行
4. **实现工作流** - 构建工具调用，处理分页和错误恢复
5. **验证权限** - 在任何写入或批量操作之前通过只读探测确认所需权限范围
6. **部署** - 配置 IDE 集成，测试权限，监控速率限制

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 服务器设置 | `references/mcp-server-setup.md` | 安装、选择服务器、配置 |
| Jira 操作 | `references/jira-queries.md` | JQL 语法、事务 CRUD、Sprint、看板、事务链接 |
| Confluence 操作 | `references/confluence-operations.md` | CQL 搜索、页面创建、空间、评论 |
| 认证 | `references/authentication-patterns.md` | OAuth 2.0、API 令牌、权限范围 |
| 常用工作流 | `references/common-workflows.md` | 事务分诊、文档同步、Sprint 自动化 |

## 快速入门示例

### JQL 查询示例
```
# 当前用户在 Sprint 中进行中的事务
project = PROJ AND status = "In Progress" AND assignee = currentUser() ORDER BY priority DESC

# 最近 7 天创建的未解决 Bug
project = PROJ AND issuetype = Bug AND status != Done AND created >= -7d ORDER BY created DESC

# 批量操作前先验证：先用 maxResults=1 测试
project = PROJ AND sprint in openSprints() AND status = Open ORDER BY created DESC
```

### CQL 查询示例
```
# 查找特定空间中最近更新的页面
space = "ENG" AND type = page AND lastModified >= "2024-01-01" ORDER BY lastModified DESC

# 在页面文本中搜索关键词
space = "ENG" AND type = page AND text ~ "deployment runbook"
```

### 最小 MCP 服务器配置
```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "@sooperset/mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "user@example.com",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
        "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_EMAIL": "user@example.com",
        "CONFLUENCE_API_TOKEN": "${CONFLUENCE_API_TOKEN}"
      }
    }
  }
}
```
> **注意：** 始终从环境变量或密钥管理器加载 `JIRA_API_TOKEN` 和 `CONFLUENCE_API_TOKEN` — 绝不硬编码凭证。

## 约束

### 必须做
- 尊重用户权限和工作区访问控制
- 在执行之前验证 JQL/CQL 查询（先用 `maxResults=1` 探测）
- 使用指数退避处理速率限制
- 对大结果集使用分页（每页 50-100 项）
- 实现网络故障的错误恢复
- 记录 API 调用用于调试和审计追踪
- 先用只读操作测试
- 记录所需的权限范围
- 在对生产数据进行任何写入或批量操作之前确认

### 不能做
- 在代码中硬编码 API 令牌或 OAuth 密钥
- 忽略 Atlassian API 的速率限制头
- 不验证必填字段就创建事务
- 跳过用户提供查询字符串的输入清理
- 不测试权限边界就部署
- 不经确认就更新生产数据
- 在同一会话中混用不同的认证方法
- 在日志或错误消息中暴露敏感事务数据

## 输出模板

实现 Atlassian MCP 功能时，请提供：
1. MCP 服务器配置（JSON/环境变量）
2. 查询示例（JQL/CQL 及解释）
3. 带有错误处理的工具调用实现
4. 认证设置说明
5. 权限要求的简要说明
