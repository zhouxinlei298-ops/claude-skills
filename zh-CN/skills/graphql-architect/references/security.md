# GraphQL 安全

## 查询深度限制

```typescript
import depthLimit from 'graphql-depth-limit';
import { ApolloServer } from '@apollo/server';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    // 将查询深度限制为 7 层
    depthLimit(7, {
      ignore: [
        '_service',
        '_entities',
        'pageInfo',
        'edges',
        'node',
      ],
    }),
  ],
});

// 示例：此查询将被拒绝（深度 > 7）
// query TooDeep {
//   user {
//     posts {
//       author {
//         posts {
//           author {
//             posts {
//               author {
//                 posts {  // 深度 7
//                   author { // 深度 8 - 被拒绝
//                     name
//                   }
//                 }
//               }
//             }
//           }
//         }
//       }
//     }
//   }
// }
```

## 查询复杂度分析

```typescript
import { createComplexityRule } from 'graphql-validation-complexity';
import { GraphQLError } from 'graphql';

// 定义字段复杂度
const complexityRule = createComplexityRule({
  maximumComplexity: 1000,
  variables: {},
  onCost: (cost) => {
    console.log('查询成本：', cost);
  },
  createError(cost, documentNode) {
    return new GraphQLError(
      `查询过于复杂：${cost}。最大允许：1000`,
      {
        extensions: {
          code: 'COMPLEXITY_LIMIT_EXCEEDED',
          cost,
          limit: 1000,
        },
      }
    );
  },
  estimators: [
    // 简单字段：成本 1
    {
      estimateComplexity: ({ type }) => {
        if (type.toString() === 'String' || type.toString() === 'Int') {
          return 1;
        }
        return 0;
      },
    },
    // 列表字段：基于 `first` 参数的成本
    {
      estimateComplexity: ({ args, childComplexity }) => {
        const first = args.first || 10;
        return first * childComplexity;
      },
    },
  ],
});

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [complexityRule],
});
```

## 自定义复杂度指令

```graphql
# Schema 定义
directive @cost(
  complexity: Int!
  multipliers: [String!]
) on FIELD_DEFINITION

type Query {
  # 简单查询：成本 1
  user(id: ID!): User

  # 列表查询：成本乘以 `first` 参数
  users(first: Int = 10): [User!]! @cost(complexity: 1, multipliers: ["first"])

  # 昂贵查询：成本 50
  analytics: Analytics! @cost(complexity: 50)
}

type User {
  id: ID!
  name: String! @cost(complexity: 1)

  # 相关列表：成本乘以 `first`
  posts(first: Int = 10): [Post!]! @cost(complexity: 2, multipliers: ["first"])

  # 昂贵的计算
  recommendations: [User!]! @cost(complexity: 20)
}
```

```typescript
// 复杂度计算器实现
import { DirectiveNode } from 'graphql';

function calculateComplexity(
  field: any,
  args: Record<string, any>,
  childComplexity: number
): number {
  const costDirective = field.astNode?.directives?.find(
    (d: DirectiveNode) => d.name.value === 'cost'
  );

  if (!costDirective) {
    return 1 + childComplexity;
  }

  const complexity =
    costDirective.arguments?.find((a) => a.name.value === 'complexity')
      ?.value.value || 1;

  const multipliers =
    costDirective.arguments?.find((a) => a.name.value === 'multipliers')
      ?.value.values || [];

  let cost = complexity;
  for (const multiplier of multipliers) {
    const argValue = args[multiplier.value] || 1;
    cost *= argValue;
  }

  return cost + childComplexity;
}
```

## 速率限制

```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import Redis from 'ioredis';

// 基于 IP 的速率限制
const limiter = rateLimit({
  store: new RedisStore({
    client: new Redis(),
  }),
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 100, // 每个窗口 100 个请求
  message: '来自此 IP 的请求过多',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/graphql', limiter);

// 基于用户的速率限制（更复杂）
import { RateLimiterRedis } from 'rate-limiter-flexible';

const rateLimiter = new RateLimiterRedis({
  storeClient: new Redis(),
  points: 1000, // 点数
  duration: 60, // 每 60 秒
  blockDuration: 60 * 5, // 如果超出则阻塞 5 分钟
});

// 在 context 创建中
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }) => {
    const userId = getUserId(req);

    try {
      await rateLimiter.consume(userId, 1);
    } catch (error) {
      throw new GraphQLError('超出速率限制', {
        extensions: {
          code: 'RATE_LIMIT_EXCEEDED',
          retryAfter: error.msBeforeNext / 1000,
        },
      });
    }

    return { userId };
  },
});
```

## 身份验证

```typescript
import jwt from 'jsonwebtoken';
import { GraphQLError } from 'graphql';

// JWT 验证
function verifyToken(token: string): User | null {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!);
    return decoded as User;
  } catch (error) {
    return null;
  }
}

// 带身份验证的 context
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }): Promise<Context> => {
    const authHeader = req.headers.authorization || '';
    const token = authHeader.replace('Bearer ', '');

    let user: User | null = null;
    if (token) {
      user = verifyToken(token);
    }

    return {
      user,
      dataSources: createDataSources(),
    };
  },
});

// 受保护的解析器
const resolvers = {
  Query: {
    me: (parent, args, context: Context) => {
      if (!context.user) {
        throw new GraphQLError('未授权', {
          extensions: { code: 'UNAUTHENTICATED' },
        });
      }
      return context.user;
    },
  },

  Mutation: {
    createPost: (parent, args, context: Context) => {
      if (!context.user) {
        throw new GraphQLError('未授权', {
          extensions: { code: 'UNAUTHENTICATED' },
        });
      }

      return context.dataSources.posts.create({
        ...args.input,
        authorId: context.user.id,
      });
    },
  },
};
```

## 授权模式

```typescript
// 基于指令的授权
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { defaultFieldResolver } from 'graphql';

function authDirective(directiveName: string) {
  return (schema: GraphQLSchema) =>
    mapSchema(schema, {
      [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
        const authDirective = getDirective(
          schema,
          fieldConfig,
          directiveName
        )?.[0];

        if (authDirective) {
          const { requires } = authDirective;
          const { resolve = defaultFieldResolver } = fieldConfig;

          fieldConfig.resolve = async (source, args, context, info) => {
            // 检查用户是否具有所需角色
            if (!context.user) {
              throw new GraphQLError('未授权', {
                extensions: { code: 'UNAUTHENTICATED' },
              });
            }

            if (requires && !context.user.roles.includes(requires)) {
              throw new GraphQLError('禁止访问', {
                extensions: {
                  code: 'FORBIDDEN',
                  requiredRole: requires,
                },
              });
            }

            return resolve(source, args, context, info);
          };
        }

        return fieldConfig;
      },
    });
}

// 带指令的 schema
const typeDefs = gql`
  directive @auth(requires: Role) on FIELD_DEFINITION

  enum Role {
    ADMIN
    USER
    GUEST
  }

  type Query {
    publicData: String!
    userData: String! @auth(requires: USER)
    adminData: String! @auth(requires: ADMIN)
  }
`;

const schema = authDirective('auth')(makeExecutableSchema({ typeDefs, resolvers }));
```

## 字段级授权

```typescript
// 行级安全
const resolvers = {
  Query: {
    posts: async (parent, args, context: Context) => {
      // 基于用户权限过滤
      const posts = await context.dataSources.posts.findAll();

      return posts.filter((post) => {
        // 公开帖子对所有人可见
        if (post.isPublic) return true;

        // 私有帖子仅对作者可见
        if (context.user?.id === post.authorId) return true;

        // 检查用户是否为管理员
        if (context.user?.roles.includes('ADMIN')) return true;

        return false;
      });
    },
  },

  Post: {
    // 除非查看者是作者或管理员，否则隐藏电子邮件
    authorEmail: (post: Post, args, context: Context) => {
      if (!context.user) return null;

      if (
        context.user.id === post.authorId ||
        context.user.roles.includes('ADMIN')
      ) {
        return post.authorEmail;
      }

      return null;
    },
  },
};
```

## 查询白名单

```typescript
// 持久化查询（自动白名单）
import { createPersistedQueryLink } from '@apollo/client/link/persisted-queries';
import { createHash } from 'crypto';

// 客户端
const link = createPersistedQueryLink({
  sha256: (query) => createHash('sha256').update(query).digest('hex'),
  useGETForHashedQueries: true,
});

// 服务端
import { ApolloServerPluginInlineTrace } from '@apollo/server/plugin/inlineTrace';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  persistedQueries: {
    cache: new Map(), // 或 Redis
  },
  // 生产环境中仅允许持久化查询
  allowBatchedHttpRequests: false,
  introspection: process.env.NODE_ENV !== 'production',
});

// 手动白名单
const allowedOperations = new Set([
  'GetUser',
  'GetPosts',
  'CreatePost',
  'UpdatePost',
]);

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    {
      async requestDidStart() {
        return {
          async didResolveOperation(requestContext) {
            const operationName = requestContext.operationName;

            if (!operationName || !allowedOperations.has(operationName)) {
              throw new GraphQLError('不允许的操作', {
                extensions: { code: 'OPERATION_NOT_ALLOWED' },
              });
            }
          },
        };
      },
    },
  ],
});
```

## 输入验证

```typescript
import { z } from 'zod';

// 用于输入验证的 Zod schema
const CreatePostSchema = z.object({
  title: z.string().min(3).max(200),
  content: z.string().min(10).max(10000),
  tags: z.array(z.string()).max(5),
  isPublic: z.boolean(),
});

const resolvers = {
  Mutation: {
    createPost: async (
      parent,
      args: { input: any },
      context: Context
    ) => {
      // 验证输入
      const validationResult = CreatePostSchema.safeParse(args.input);

      if (!validationResult.success) {
        throw new GraphQLError('无效输入', {
          extensions: {
            code: 'BAD_USER_INPUT',
            validationErrors: validationResult.error.errors,
          },
        });
      }

      const input = validationResult.data;
      return context.dataSources.posts.create(input);
    },
  },
};
```

## 内省控制

```typescript
// 在生产环境中禁用内省
import { ApolloServer } from '@apollo/server';
import { ApolloServerPluginLandingPageDisabled } from '@apollo/server/plugin/disabled';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',
  plugins:
    process.env.NODE_ENV === 'production'
      ? [ApolloServerPluginLandingPageDisabled()]
      : [],
});

// 条件内省（仅管理员）
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: false, // 默认禁用
  plugins: [
    {
      async requestDidStart({ request, contextValue }) {
        // 允许管理员进行内省
        if (
          request.operationName === 'IntrospectionQuery' &&
          !contextValue.user?.isAdmin
        ) {
          throw new GraphQLError('内省已禁用', {
            extensions: { code: 'FORBIDDEN' },
          });
        }
      },
    },
  ],
});
```

## CSRF 保护

```typescript
import csrf from 'csurf';

// 变更的 CSRF 保护
const csrfProtection = csrf({ cookie: true });

app.post('/graphql', csrfProtection, expressMiddleware(server));

// 客户端必须发送 CSRF 令牌
// fetch('/graphql', {
//   method: 'POST',
//   headers: {
//     'CSRF-Token': csrfToken,
//   },
//   body: JSON.stringify({ query }),
// });
```

## 安全最佳实践

1. **深度限制**：防止深度嵌套查询
2. **复杂度分析**：计算并限制查询成本
3. **速率限制**：限制每个用户/IP 的请求数
4. **身份验证**：在 context 中验证用户身份
5. **授权**：在解析器中检查权限
6. **输入验证**：验证所有变更输入
7. **查询白名单**：在生产环境中使用持久化查询
8. **内省控制**：在生产环境中禁用
9. **错误清理**：不要在错误中暴露敏感数据
10. **CORS 配置**：限制允许的来源
11. **仅 HTTPS**：生产环境中始终使用 HTTPS
12. **审计日志**：记录敏感操作
