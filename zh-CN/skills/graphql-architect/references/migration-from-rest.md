# 从 REST 到 GraphQL 迁移指南

---

## 何时使用本指南

**迁移到 GraphQL 当：**
- 复杂 UI 视图需要多次往返
- 过度获取或获取不足数据存在问题
- 支持不同的客户端需求（移动端、Web、桌面端）
- 团队边界需要联邦 API 架构
- 实时订阅是核心需求
- 跨客户端服务器边界需要类型安全
- API 版本控制复杂性增长

**成功指标：**
- 客户应用程序进行多次顺序 REST 调用
- 不同客户端需要不同的数据形状
- 移动应用受带宽限制
- 前端团队等待后端 API 更改
- 多个 REST 版本同时存在

---

## 何时不应使用 GraphQL

**坚持使用 REST 当：**
- 简单 CRUD 操作和稳定的客户端
- 文件上传/下载是主要用例
- HTTP 缓存至关重要（CDN、浏览器缓存）
- 团队缺乏 GraphQL 专业知识和培训预算
- 主要是服务器到服务器通信
- 静态内容传递是主要需求
- 不需要复杂的数据关系导航
- 复杂的数据关系导航会导致安全风险

**警告信号：**
- 团队为 1-2 名开发者（运营开销）
- 主要是服务器到服务器通信
- 静态内容传递是主要要求
- 不需要复杂的数据关系导航
- 查询复杂性会创建安全风险

---

## 概念映射：REST 到 GraphQL

| REST 概念 | GraphQL 等价项 | 说明 |
|--------------|-------------------|-------|
| GET /users | Query users | 读取操作 |
| GET /users/:id | Query user(id: ID!) | 单个实体获取 |
| POST /users | Mutation createUser | 创建操作 |
| PUT /users/:id | Mutation updateUser | 更新操作 |
| DELETE /users/:id | Mutation deleteUser | 删除操作 |
| PATCH /users/:id | Mutation updateUserPartial | 部分更新 |
| Query params (?filter=...) | Field arguments | 过滤/排序 |
| URL 路径段 | 嵌套字段选择 | 数据关系 |
| 多个端点 | Single query | 消除往返 |
| Webhook 回调 | Subscriptions | 实时更新 |
| HTTP 状态码 | Errors array + data | 部分成功模型 |
| API 版本控制 | Schema 演进 | 版本间的弃用 |
| /users?include=posts | users { posts } | 急切加载控制 |
| 偏移分页 | 基于游标的连接 | Relay 规范 |
| Accept header | Operation selection | 内容协商 |
| OAuth/JWT tokens | Context authentication | 相同的身份验证模式 |

---

## 模式 1：GET 端点到查询

### REST 端点

```typescript
// GET /api/users/:id
interface UserResponse {
  id: string;
  name: string;
  email: string;
  created_at: string;
  posts: Array<{
    id: string;
    title: string;
    published: boolean;
  }>;
}

app.get('/api/users/:id', async (req, res) => {
  const user = await db.users.findById(req.params.id);
  const posts = await db.posts.findByUserId(user.id); // N+1 风险

  res.json({
    id: user.id,
    name: user.name,
    email: user.email,
    created_at: user.createdAt.toISOString(),
    posts: posts.map(p => ({
      id: p.id,
      title: p.title,
      published: p.published
    }))
  });
});
```

### GraphQL Schema

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  createdAt: DateTime!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  published: Boolean!
  author: User!
}

type Query {
  user(id: ID!): User
  users(filter: UserFilter, limit: Int = 20): [User!]!
}

input UserFilter {
  nameContains: String
  createdAfter: DateTime
}

scalar DateTime
```

### 带 DataLoader 的 GraphQL 解析器

```typescript
import DataLoader from 'dataloader';
import { IResolvers } from '@graphql-tools/utils';

// 批处理加载以防止 N+1 查询
const createPostsByUserIdLoader = (db: Database) =>
  new DataLoader<string, Post[]>(async (userIds) => {
    const posts = await db.posts.findByUserIds([...userIds]);

    // 按用户 ID 分组
    const postsByUserId = userIds.map(id =>
      posts.filter(post => post.userId === id)
    );
    return postsByUserId;
  });

interface Context {
  db: Database;
  loaders: {
    userById: DataLoader<string, User>;
    postsByUserId: DataLoader<string, Post[]>;
  };
}

const resolvers: IResolvers<any, Context> = {
  Query: {
    user: async (_, { id }, { loaders }) => {
      return loaders.userById.load(id);
    },
    users: async (_, { filter, limit }, { db }) => {
      return db.users.find(filter, { limit });
    },
  },

  User: {
    posts: async (user, _, { loaders }) => {
      // DataLoader 批处理和缓存这些调用
      return loaders.postsByUserId.load(user.id);
    },
  },
};

// Apollo Server 设置
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';

const server = new ApolloServer<Context>({
  typeDefs,
  resolvers,
});

const { url } = await startStandaloneServer(server, {
  context: async ({ req }) => {
    const db = createDatabaseConnection();

    return {
      db,
      loaders: {
        userById: createUserByIdLoader(db),
        postsByUserId: createPostsByUserIdLoader(db),
      },
    };
  },
});

### 客户端查询示例

```typescript
// 灵活字段选择 - 客户端控制响应形状
const MINIMAL_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
    }
  }
`;

const DETAILED_USER = gql`
  query GetUserWithPosts($id: ID!) {
    user(id: $id) {
      id
      name
      email
      createdAt
      posts {
        id
        title
        published
      }
    }
  }
`;

// 单个查询替换多个 REST 调用
const DASHBOARD_DATA = gql`
  query Dashboard($userId: ID!) {
    user(id: $userId) {
      name
      posts {
        id
        title
      }
    }
    # 否则需要单独的 REST 端点
    users(filter: { createdAfter: "2025-01-01" }, limit: 5) {
      id
      name
    }
  }
`;
```

---

## 模式 2：POST/PUT/DELETE 到变更

### REST 端点

```typescript
// POST /api/users
app.post('/api/users', async (req, res) => {
  const { name, email, password } = req.body;

  if (!name || !email) {
    return res.status(400).json({ error: '缺少必需字段' });
  }

  const user = await db.users.create({ name, email, password });
  res.status(201).json(user);
});

// PUT /api/users/:id
app.put('/api/users/:id', async (req, res) => {
  const user = await db.users.update(req.params.id, req.body);
  res.json(user);
});

// DELETE /api/users/:id
app.delete('/api/users/:id', async (req, res) => {
  await db.users.delete(req.params.id);
  res.status(204).send();
});
```

### GraphQL Schema

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
}

input CreateUserInput {
  name: String!
  email: String!
  password: String!
}

input UpdateUserInput {
  id: ID!
  name: String
  email: String
}

type CreateUserPayload {
  user: User
  errors: [UserError!]!
}

type UpdateUserPayload {
  user: User
  errors: [UserError!]!
}

type DeleteUserPayload {
  deletedId: ID
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
  code: ErrorCode!
}

enum ErrorCode {
  VALIDATION_ERROR
  NOT_FOUND
  UNAUTHORIZED
  INTERNAL_ERROR
}
```

### GraphQL 变更解析器

```typescript
const resolvers: IResolvers<any, Context> = {
  Mutation: {
    createUser: async (_, { input }, { db, user }) => {
      // 验证
      if (!isValidEmail(input.email)) {
        return {
          user: null,
          errors: [{
            field: 'email',
            message: '无效的电子邮件格式',
            code: 'VALIDATION_ERROR',
          }],
        };
      }

      // 检查重复
      const existing = await db.users.findByEmail(input.email);
      if (existing) {
        return {
          user: null,
          errors: [{
            field: 'email',
            message: '电子邮件已注册',
            code: 'VALIDATION_ERROR',
          }],
        };
      }

      const hashedPassword = await bcrypt.hash(input.password, 10);
      const newUser = await db.users.create({
        name: input.name,
        email: input.email,
        password: hashedPassword,
      });

      return {
        user: newUser,
        errors: [],
      };
    },

    updateUser: async (_, { id, input }, { db, user }) => {
      if (!user || user.id !== input.id) {
        return {
          user: null,
          errors: [{
            message: '未授权',
            code: 'UNAUTHORIZED',
          }],
        };
      }

      const updated = await db.users.update(input.id, {
        ...(input.name && { name: input.name }),
        ...(input.email && { email: input.email }),
      });

      return {
        user: updated,
        errors: [],
      };
    },

    deleteUser: async (_, { id }, { db, user }) => {
      if (!user || user.id !== id) {
        return {
          deletedId: null,
          errors: [{
            message: '未授权',
            code: 'UNAUTHORIZED',
          }],
        };
      }

      await db.users.delete(id);

      return {
        deletedId: id,
        errors: [],
      };
    },
  },
};
```

### 客户端变更示例

```typescript
const CREATE_USER = gql`
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
      user {
        id
        name
        email
        createdAt
      }
      errors {
        field
        message
        code
      }
    }
  }
`;

// 带错误处理的使用
const [createUser] = useMutation(CREATE_USER);

const handleSubmit = async (formData) => {
  const { data } = await createUser({
    variables: {
      input: formData,
    },
  });

  if (data.createUser.errors.length > 0) {
    // 处理验证错误
    data.createUser.errors.forEach(error => {
      setFieldError(error.field, error.message);
    });
  } else {
    // 成功 - 使用返回的用户
    navigate(`/users/${data.createUser.user.id}`);
  }
};
```

---

## 模式 3：分页迁移

### REST 偏移量分页

```typescript
// GET /api/posts?page=2&limit=20
app.get('/api/posts', async (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const limit = parseInt(req.query.limit) || 20;
  const offset = (page - 1) * limit;

  const posts = await db.posts.find({
    limit,
    offset,
  });

  const total = await db.posts.count();

  res.json({
    data: posts,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  });
});
```

### GraphQL 基于游标的分页（Relay 连接）

```graphql
type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
    filter: PostFilter
  ): PostConnection!
}

type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

input PostFilter {
  published: Boolean
  authorId: ID
  titleContains: String
}

type Post {
  id: ID!
  title: String!
  published: Boolean!
  authorId: ID!
}
```

### 游标分页解析器

```typescript
import { encodeCursor, decodeCursor } from './cursor-utils';

const resolvers: IResolvers = {
  Query: {
    posts: async (_, args, { db }) => {
      const { first, after, last, before, filter } = args;

      const limit = Math.min(first || 10, 100);
      const cursor = after || last || before ? decodeCursor(after || last || before) : null;

      // 获取额外的一个以确定 hasNextPage
      const posts = await db.posts.findAll({
        limit: limit + 1,
        cursor,
      });

      const hasMore = posts.length > limit;
      const isForward = !!after;
      const nodes = isForward ? posts.slice(0, limit) : posts.reverse().slice(0, limit);
      const edges = nodes.map((post, index) => ({
        node: post,
        cursor: encodeCursor(isForward ? offset + index : offset - index),
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage: isForward ? hasMore : false,
          hasPreviousPage: !isForward ? hasMore : false,
          startCursor: edges[0]?.cursor || null,
          endCursor: edges[edges.length - 1]?.cursor || null,
        },
        totalCount: await db.posts.count(filter),
      };
    },
  },
};

// cursor-utils.ts
export const encodeCursor = (offset: number): string => {
  return Buffer.from(`cursor:${offset}`).toString('base64');
};

export const decodeCursor = (cursor: string): number => {
  const decoded = Buffer.from(cursor, 'base64').toString('utf-8');
  return parseInt(decoded.replace('cursor:', ''));
};
```

### 客户端分页查询

```typescript
const POSTS_QUERY = gql`
  query Posts($first: Int!, $after: String, $filter: PostFilter) {
    posts(first: $first, after: $after, filter: $filter) {
      edges {
        node {
          id
          title
          published
          author {
            name
          }
        }
        cursor
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
`;

// 无限滚动实现
const PostList = () => {
  const { data, loading, fetchMore } = useQuery(POSTS_QUERY, {
    variables: { first: 20 },
  });

  const loadMore = () => {
    fetchMore({
      variables: {
        after: data.posts.pageInfo.endCursor,
      },
      updateQuery: (prev, { fetchMoreResult }) => {
        if (!fetchMoreResult) return prev;
        return {
          posts: {
            ...prev.posts,
            edges: [
              ...prev.posts.edges,
              ...fetchMoreResult.posts.edges,
            ],
          },
        };
      },
    });
  };

  return (
    <div>
      {data?.posts.edges.map(({ node }) => (
        <PostCard key={node.id} post={node} />
      ))}
      {data?.posts.pageInfo.hasNextPage && (
        <button onClick={loadMore}>加载更多</button>
      )}
    </div>
  );
};
```

---

## 模式 4：身份验证转换

### REST 身份验证

```typescript
// REST 中间件
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '') || null;

  if (token) {
    try {
      const payload = jwt.verify(token, process.env.JWT_SECRET);
      req.user = await db.users.findById(payload.userId);
    } catch (error) {
      return res.status(401).json({ error: '无效令牌' });
    }
  }

  next();
});
```

### GraphQL 身份验证 Context

```typescript
import { ApolloServer } from '@apollo/server';
import { GraphQLError } from 'graphql';

interface AuthContext {
  user: User | null;
  requireAuth: () => User;
}

const server = new ApolloServer<AuthContext>({
  typeDefs,
  resolvers,
  context: async ({ req }) => {
    const token = req.headers.authorization?.replace('Bearer ', '') || '';
    let user: User | null = null;
    if (token) {
      try {
        const payload = jwt.verify(token, process.env.JWT_SECRET);
        user = await db.users.findById(payload.userId);
      } catch (error) {
        // 令牌无效 - 继续使用 user = null
      }
    }

    return {
      user,
      requireAuth: (): User => {
        if (!user) {
          throw new GraphQLError('需要身份验证', {
            extensions: {
              code: 'UNAUTHENTICATED',
            },
          });
        }
        return user;
      },
    };
  },
});
```

### 字段级授权

```typescript
const resolvers = {
  User: {
    email: (user, _, { currentUser }) => {
      // 字段级隐私
      if (currentUser?.id === user.id || currentUser?.role === 'ADMIN') {
        return user.email;
      }
      return null;
    },
  },
};
```

---

## BFF（Backend for Frontend）架构

### 多客户端 GraphQL 网关

```typescript
// Schema 拼接以用于不同客户端
import { stitchSchemas } from '@graphql-tools/stitch';

// 移动端优化 schema
const mobileSchema = makeExecutableSchema({
  typeDefs: `
    type Query {
      # 为移动端去规范化，减少往返
      dashboard: MobileDashboard!
      user(id: ID!): MobileUser!
      recentPosts: [Post!]!
      notifications: [Notification!]!
    }
  `,
  resolvers: mobileResolvers,
});

// Web 端点优化 schema
const webSchema = makeExecutableSchema({
  typeDefs: `
    type Query {
      # 用于 Web，支持更多细粒度查询
      user(id: ID!): User!
      posts(filter: PostFilter): PostConnection!
      analytics: Analytics!
    }
  `,
  resolvers: webResolvers,
});

// 客户端特定的服务器
const mobileServer = new ApolloServer({
  schema: mobileSchema,
  introspection: true,
});

const webServer = new ApolloServer({
  schema: webSchema,
  introspection: true,
});

// 基于客户端头的路由
app.use('/graphql', (req, res) => {
  const client = req.headers['x-client-type'];

  if (client === 'mobile') {
    return mobileServer.handleRequest(req, res);
  } else if (client === 'web') {
    return webServer.handleRequest(req, res);
  } else {
    res.status(400).send('未知客户端');
  }
});
```

---

## 增量迁移策略

### 阶段 1：GraphQL 包装器（第 1-2 周）

```typescript
// 使用现有 REST 端点的包装器
const resolvers = {
  Query: {
    user: async (_, { id }) => {
      // 在内部调用现有 REST API
      const response = await fetch(`http://localhost:3000/api/users/${id}`);
      return response.json();
    },
    users: async () => {
      const response = await fetch('http://localhost:3000/api/users');
      return response.json();
    },
  },
};

// 允许 GraphQL 客户端立即开始使用
// 后端团队可以并行工作
```

### 阶段 2：并行实施（第 3-6 周）

```typescript
// 使用 DB 访问直接实现新的解析器
// REST 端点继续运行

const resolvers = {
  Query: {
    user: async (_, { id }, { db }) => {
      // 新实现 - 直接 DB 访问
      return await db.users.findById(id);
    },
  },
};
```

### 阶段 3：客户端迁移（第 7-12 周）

```typescript
// A/B 测试两种实现
// 监控性能和错误率
// 逐步推出到更多用户

// 功能标志
const USE_GRAPHQL = process.env.GRAPHQL_ENABLED === 'true';

// 迁移链接帮助客户端切换
const MIGRATION_GUIDE = 'https://docs.example.com/graphql-migration';
```

### 阶段 4：REST 弃用（第 13 周+）

```typescript
// 弃用警告头
app.get('/api/users/:id', async (req, res) => {
  res.status(410).json({
    error: '此端点已弃用',
    message: '请使用 GraphQL 端点',
    migrationGuide: 'https://docs.example.com/graphql-migration',
    sunsetDate: '2025-06-01',
  });
});
```

---

## 常见陷阱

### 陷阱 1：N+1 查询问题

```typescript
// 不良 - 导致 N+1 查询
const resolvers = {
  User: {
    posts: async (user, _, { db }) => {
      // 每次用户调用获取帖子
      return db.posts.findByUserId(user.id);
    },
  },
};

// 良好 - 使用 DataLoader
const resolvers = {
  User: {
    posts: async (user, _, { loaders }) => {
      // 批处理并缓存
      return loaders.postsByUserId.load(user.id);
    },
  },
};
```

### 陷阱 2：直接暴露数据库架构

```typescript
// 不良 - 紧密耦合到数据库
type User {
  user_id: Int!          # 数据库列名
  first_name: String    # 原始 DB 类型
  last_name: String     # 原始 DB 类型
}

// 良好 - API 优先设计
type User {
  id: ID!                # 抽象标识符
  name: String!          # 计算字段
  email: String!
  createdAt: DateTime!   # 适当类型
}
```

### 陷阱 3：缺少错误处理

```typescript
// 不良 - 错误会终止整个响应
const resolvers = {
  Query: {
    dashboard: async () => {
      const user = await fetchUser();    // 错误时崩溃
      const posts = await fetchPosts();  // 从未到达
      return { user, posts };       // 部分数据
    },
  },
};

// 良好 - 部分成功模型
const resolvers = {
  Query: {
    dashboard: async () => {
      try {
        const user = await fetchUser();
        const posts = await fetchPosts();
        return { user, posts };
      } catch (error) {
        // 返回空对象
        return {};
      }
    },
  },
};
```

### 陷阱 4：忽略查询复杂性

```typescript
// 不良 - 没有深度/复杂性限制
// 客户端可以编写导致服务器的 DOS 查询

const resolvers = {
  Query: {
    // 没有限制的查询
    everything: async () => {
      return await db.getEverything(); // 危险！
    },
  },
};

// 良好 - 实现复杂性限制
import { createComplexityLimitRule } from 'graphql-validation-complexity';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    createComplexityLimitRule(1000, {
      onCost: (cost) => {
        console.log('查询成本：', cost);
      },
    }),
  ],
});
```

### 陷阱 5：过度规范化

```typescript
// 不良 - 太细粒度，需要多个查询
type Query {
  userName(id: ID!): String
  userEmail(id: ID!): String
  userAge(id: ID!): Int
  userAddress(id: ID!): Address
  // 客户需要多次查询获取一个用户
}

// 良好 - 逻辑分组
type Query {
  user(id: ID!): User    // 一次获取所有数据
}
```

---

## 跨参考

**相关技能：**
- **graphql-architect/references/schema-design.md** - 类型和系统模式
- **graphql-architect/references/federation-guide.md** - 多服务 GraphQL 架构
- **backend-developer** - REST API 实现模式
- **api-designer** - API 设计原则和最佳实践

---

## 迁移检查清单

- [ ] 识别最常用的 REST 端点
- [ ] 将 REST 资源映射到 GraphQL 类型
- [ ] 设计 GraphQL Schema（类型、输入、查询）
- [ ] 实现 GraphQL 解析器（或包装 REST）
- [ ] 添加 DataLoader 以批处理 N+1
- [ ] 实现身份验证/授权
- [ ] 实现分页（基于游标）
- [ ] 添加错误处理和验证
- [ ] 编写客户端迁移指南
- [ ] 设置查询复杂性限制
- [ ] 配置监控和指标
- [ ] A/B 测试性能
- [ ] 计划 REST 端点弃用时间线
- [ ] 培训团队 GraphQL 模式

---

**迁移完成条件：**
- 所有关键路径使用 GraphQL
- REST 端点已弃用或保留用于特定用例
- 客户应用程序已迁移
- 性能指标满足或超过 REST 基准
- 团队熟练掌握 GraphQL
