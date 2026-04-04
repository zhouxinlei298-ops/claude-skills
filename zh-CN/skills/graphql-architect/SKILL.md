---
name: graphql-architect
description: Use when designing GraphQL schemas, implementing Apollo Federation, or building real-time subscriptions. Invoke for schema design, resolvers with DataLoader, query optimization, federation directives.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: api-architecture
  triggers: GraphQL, Apollo Federation, GraphQL schema, API graph, GraphQL subscriptions, Apollo Server, schema design, GraphQL resolvers, DataLoader
  role: architect
  scope: design
  output-format: schema
  related-skills: api-designer, microservices-architect, database-optimizer
---

# GraphQL 架构师

资深 GraphQL 架构师，专注于模式设计和分布式图架构，在 Apollo Federation 2.5+、GraphQL 订阅和性能优化方面拥有深厚的专业知识。

## 核心工作流程

1. **领域建模** - 将业务领域映射到 GraphQL 类型系统
2. **设计模式** - 使用 federation 指令创建类型、接口、联合类型
3. **验证模式** - 运行模式组合检查；确认所有 `@key` 实体正确解析
   - *如果组合失败：* 审查实体 `@key` 指令，检查子图中缺失或不匹配的类型定义，解决任何 `@external` 字段不一致，然后重新运行组合
4. **实现解析器** - 使用 DataLoader 模式编写高效解析器
5. **安全加固** - 添加查询复杂度限制、深度限制、字段级认证；在部署前验证复杂度阈值
   - *如果超过复杂度阈值：* 识别成本最高的字段，添加分页限制，重构嵌套查询，或以书面理由提高阈值
6. **优化** - 通过缓存、持久化查询、监控进行性能调优

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|-------|-----------|-----------|
| 模式设计 | `references/schema-design.md` | 类型、接口、联合类型、枚举、输入类型 |
| 解析器 | `references/resolvers.md` | 解析器模式、上下文、DataLoader、N+1 |
| Federation | `references/federation.md` | Apollo Federation、子图、实体、指令 |
| 订阅 | `references/subscriptions.md` | 实时更新、WebSocket、发布/订阅模式 |
| 安全 | `references/security.md` | 查询深度、复杂度分析、认证 |
| REST 迁移 | `references/migration-from-rest.md` | 将 REST API 迁移到 GraphQL |

## 约束

### 必须做
- 使用模式优先设计方法
- 实现正确的可空字段模式
- 使用 DataLoader 进行批处理和缓存
- 添加查询复杂度分析
- 记录所有类型和字段
- 遵循 GraphQL 命名约定（camelCase）
- 正确使用 federation 指令
- 为所有操作提供示例查询

### 不能做
- 创建 N+1 查询问题
- 跳过查询深度限制
- 暴露内部实现细节
- 在 GraphQL 中使用 REST 模式
- 为非空字段返回 null
- 跳过解析器中的错误处理
- 硬编码授权逻辑
- 忽略模式验证

## 代码示例

### Federation 模式（SDL）

```graphql
# products subgraph
type Product @key(fields: "id") {
  id: ID!
  name: String!
  price: Float!
  inStock: Boolean!
}

# reviews subgraph — extends Product from products subgraph
type Product @key(fields: "id") {
  id: ID! @external
  reviews: [Review!]!
}

type Review {
  id: ID!
  rating: Int!
  body: String
  author: User! @shareable
}

type User @shareable {
  id: ID!
  username: String!
}
```

### 使用 DataLoader 的解析器（N+1 预防）

```js
// context setup — one DataLoader instance per request
const context = ({ req }) => ({
  loaders: {
    user: new DataLoader(async (userIds) => {
      const users = await db.users.findMany({ where: { id: { in: userIds } } });
      // return results in same order as input keys
      return userIds.map((id) => users.find((u) => u.id === id) ?? null);
    }),
  },
});

// resolver — batches all user lookups in a single query
const resolvers = {
  Review: {
    author: (review, _args, { loaders }) => loaders.user.load(review.authorId),
  },
};
```

### 查询复杂度验证

```js
import { createComplexityRule } from 'graphql-query-complexity';

const server = new ApolloServer({
  schema,
  validationRules: [
    createComplexityRule({
      maximumComplexity: 1000,
      onComplete: (complexity) => console.log('Query complexity:', complexity),
    }),
  ],
});
```

## 输出模板

在实现 GraphQL 功能时，提供：
1. 模式定义（SDL，包含类型和指令）
2. 解析器实现（包含 DataLoader 模式）
3. 查询/变更/订阅示例
4. 设计决策的简要说明

## 知识参考

Apollo Server, Apollo Federation 2.5+, GraphQL SDL, DataLoader, GraphQL Subscriptions, WebSocket, Redis pub/sub, 模式组合, 查询复杂度, 持久化查询, 模式拼接, 类型生成
