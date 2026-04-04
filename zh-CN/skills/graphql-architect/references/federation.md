# Apollo Federation

## 子图设置

```typescript
// users-subgraph/schema.graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: ["@key", "@shareable"])

type User @key(fields: "id") {
  id: ID!
  email: String!
  username: String!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users: [User!]!
}

// users-subgraph/resolvers.ts
import { ApolloServer } from '@apollo/server';
import { buildSubgraphSchema } from '@apollo/subgraph';
import { readFileSync } from 'fs';

const typeDefs = readFileSync('./schema.graphql', 'utf8');

const resolvers = {
  User: {
    __resolveReference: async (
      reference: { id: string },
      context: Context
    ): Promise<User> => {
      return context.dataSources.users.findById(reference.id);
    },
  },

  Query: {
    user: async (parent, args: { id: string }, context: Context) => {
      return context.dataSources.users.findById(args.id);
    },
    users: async (parent, args, context: Context) => {
      return context.dataSources.users.findAll();
    },
  },
};

const server = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
});
```

## 实体键和引用

```graphql
# products-subgraph/schema.graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: [
    "@key",
    "@shareable",
    "@interfaceObject"
  ])

# 单一键字段
type Product @key(fields: "id") {
  id: ID!
  name: String!
  price: Float!
  sku: String! @shareable
}

# 复合键
type Variant @key(fields: "productId sku") {
  productId: ID!
  sku: String!
  size: String!
  color: String!
}

# 多个键（标识的不同方式）
type Review @key(fields: "id") @key(fields: "productId authorId") {
  id: ID!
  productId: ID!
  authorId: ID!
  rating: Int!
  content: String!
}
```

## 跨子图扩展类型

```graphql
# users-subgraph 拥有 User
type User @key(fields: "id") {
  id: ID!
  email: String!
  username: String!
}

# posts-subgraph 使用 posts 扩展 User
extend type User @key(fields: "id") {
  id: ID! @external
  posts: [Post!]!
}

type Post @key(fields: "id") {
  id: ID!
  title: String!
  content: String!
  authorId: ID!
  author: User!
}
```

```typescript
// posts-subgraph/resolvers.ts
const resolvers = {
  User: {
    // 引用解析器：按 id 获取用户存根
    __resolveReference: async (
      reference: { id: string },
      context: Context
    ) => {
      return { id: reference.id };
    },

    // 字段解析器：为 User 解析 posts
    posts: async (user: { id: string }, args, context: Context) => {
      return context.dataSources.posts.findByAuthor(user.id);
    },
  },

  Post: {
    // 将 author 解析为 User 实体引用
    author: (post: Post) => {
      return { __typename: 'User', id: post.authorId };
    },
  },
};
```

## Federation 指令

```graphql
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: [
    "@key",
    "@requires",
    "@provides",
    "@external",
    "@shareable",
    "@override",
    "@inaccessible",
    "@tag"
  ])

# @key：用主键定义实体
type Product @key(fields: "id") {
  id: ID!
  name: String!
}

# @external：在另一个子图中定义的字段
extend type User @key(fields: "id") {
  id: ID! @external
  email: String! @external
  isVerified: Boolean! @external
}

# @requires：字段需要外部数据
extend type User @key(fields: "id") {
  id: ID! @external
  email: String! @external
  isVerified: Boolean! @external
  # 只有拥有 email 和 isVerified 才能计算
  canPost: Boolean! @requires(fields: "email isVerified")
}

# @provides：优化提示
type Post @key(fields: "id") {
  id: ID!
  author: User! @provides(fields: "username")
}

# @shareable：字段可由多个子图解析
type Product @key(fields: "id") {
  id: ID!
  sku: String! @shareable
  name: String!
}

# @override：子图之间的迁移
type Product @key(fields: "id") {
  id: ID!
  # 从 legacy-subgraph 覆盖
  price: Float! @override(from: "legacy-subgraph")
}

# @inaccessible：从超级图隐藏
type User @key(fields: "id") {
  id: ID!
  email: String!
  internalId: String! @inaccessible
}

# @tag：组织架构
type Query {
  products: [Product!]! @tag(name: "public")
  adminUsers: [User!]! @tag(name: "admin")
}
```

## 网关配置

```typescript
// gateway/server.ts
import { ApolloGateway, IntrospectAndCompose } from '@apollo/gateway';
import { ApolloServer } from '@apollo/server';

const gateway = new ApolloGateway({
  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'users', url: 'http://localhost:4001/graphql' },
      { name: 'posts', url: 'http://localhost:4002/graphql' },
      { name: 'products', url: 'http://localhost:4003/graphql' },
    ],
    // 轮询架构更新
    pollIntervalInMs: 10000,
  }),

  // 错误处理
  serviceHealthCheck: true,

  // 查询规划调试
  debug: process.env.NODE_ENV === 'development',
});

const server = new ApolloServer({
  gateway,

  // 上下文传播到子图
  context: async ({ req }) => {
    const token = req.headers.authorization || '';
    return { token };
  },
});

await server.listen(4000);
console.log('网关就绪于 http://localhost:4000');
```

## 托管 Federation（Apollo Studio）

```typescript
// gateway/server.ts 与托管 federation
import { ApolloGateway } from '@apollo/gateway';
import { ApolloServer } from '@apollo/server';

const gateway = new ApolloGateway({
  // 不需要子图 URL - 从 Apollo Studio 获取
  // 从 Apollo Uplink 获取架构组合
  async supergraphSdl({ update }) {
    // 从 Apollo Uplink 获取 supergraphSdl
    const supergraphSdl = await fetchSupergraphSdl();
    return {
      supergraphSdl,
      cleanup: async () => {},
    };
  },

  // 子图报告到 Apollo Studio
  import { ApolloServerPluginInlineTrace } from '@apollo/server/plugin/inlineTrace';

const subgraphServer = new ApolloServer({
  schema: buildSubgraphSchema([{ typeDefs, resolvers }]),
  plugins: [
    ApolloServerPluginInlineTrace(),
  ],
});
```

## 值类型 vs 实体

```graphql
# 值类型：没有 @key，由一个子图完全解析
type Address {
  street: String!
  city: String!
  country: String!
  postalCode: String!
}

# 实体：有 @key，可被其他子图扩展
type User @key(fields: "id") {
  id: ID!
  email: String!
  # 实体中嵌入的值类型
  address: Address
}

# 另一个子图可以扩展 User 但不能扩展 Address
extend type User @key(fields: "id") {
  id: ID! @external
  email: String! @external
  orders: [Order!]!
}
```

## 接口对象

```graphql
# accounts-subgraph
type User implements Account @key(fields: "id") {
  id: ID!
  email: String!
  role: String!
}

type AdminUser implements Account @key(fields: "id") {
  id: ID!
  email: String!
  role: String!
  permissions: [String!]!
}

interface Account {
  id: ID!
  email: String!
  role: String!
}

# orders-subgraph（不知道 User/AdminUser）
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.5", import: ["@key", "@interfaceObject"])

type Order @key(fields: "id") {
  id: ID!
  account: Account!
}

# 使用 @interfaceObject 在不了解实现的情况下引用 Account
type Account @key(fields: "id") @interfaceObject {
  id: ID!
}
```

## 查询规划优化

```graphql
# 低效：需要多次往返
type Query {
  user(id: ID!): User
}

type User @key(fields: "id") {
  id: ID!
  posts: [Post!]!
}

type Post @key(fields: "id") {
  id: ID!
  authorId: ID!
  # 低效：解析器需要从 User 子图获取
  author: User!
}

# 更好：直接提供数据以避免额外获取
type Post @key(fields: "id") {
  id: ID!
  authorId: ID!
  # 优化：直接提供用户名
  author: User! @provides(fields: "username")
}

# 网关可以完全从 Post 子图完成一些 User 字段
# 无需从 User 子图获取
```

## Federation 中的错误处理

```typescript
const resolvers = {
  User: {
    __resolveReference: async (
      reference: { id: string },
      context: Context
    ) => {
      try {
        const user = await context.dataSources.users.findById(reference.id);
        if (!user) {
          // 返回 null 表示缺失实体（软错误）
          return null;
        }
        return user;
      } catch (error) {
        // 硬错误传播到客户端
        throw new GraphQLError('Failed to resolve user', {
          extensions: {
            code: 'USER_RESOLUTION_FAILED',
            userId: reference.id,
          },
        });
      }
    },
  },
};
```

## Federation 最佳实践

1. **实体设计**：对需要扩展的类型使用 @key
2. **子图边界**：与团队/服务边界对齐
3. **共享类型**：对真正共享的字段使用 @shareable
4. **迁移**：使用 @override 进行渐进式子图迁移
5. **性能**：使用 @provides 优化查询规划
6. **值类型**：对嵌入数据使用普通类型
7. **组合**：在 CI/CD 中测试架构组合
8. **版本控制**：使用托管 federation 实现安全部署
9. **监控**：跟踪查询规划和解析器性能
10. **文档**：记录实体所有权和扩展模式
