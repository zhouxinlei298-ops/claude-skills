# GraphQL 订阅

## 基本订阅设置

```typescript
// schema.graphql
type Subscription {
  postCreated: Post!
  postUpdated(id: ID!): Post!
  commentAdded(postId: ID!): Comment!
  userOnline: User!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
}

// server.ts
import { createServer } from 'http';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';
import { makeExecutableSchema } from '@graphql-tools/schema';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import express from 'express';

const schema = makeExecutableSchema({ typeDefs, resolvers });

const app = express();
const httpServer = createServer(app);

// 用于订阅的 WebSocket 服务器
const wsServer = new WebSocketServer({
  server: httpServer,
  path: '/graphql',
});

const serverCleanup = useServer(
  {
    schema,
    context: async (ctx, msg, args) => {
      // 从连接参数中提取身份验证
      const token = ctx.connectionParams?.authorization;
      const user = token ? await verifyToken(token) : null;
      return { user };
    },
  },
  wsServer
);

const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginDrainHttpServer({ httpServer }),
    {
      async serverWillStart() {
        return {
          async drainServer() {
            await serverCleanup.dispose();
          },
        };
      },
    },
  ],
});

await server.start();
app.use('/graphql', express.json(), expressMiddleware(server));

httpServer.listen(4000);
```

## PubSub 实现

```typescript
// pubsub.ts
import { RedisPubSub } from 'graphql-redis-subscriptions';
import Redis from 'ioredis';

// 内存中（仅开发环境）
import { PubSub } from 'graphql-subscriptions';
export const pubsub = new PubSub();

// Redis（生产环境）
const options = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times: number) => Math.min(times * 50, 2000),
};

export const pubsub = new RedisPubSub({
  publisher: new Redis(options),
  subscriber: new Redis(options),
});

// 强类型事件名称
export const EVENTS = {
  POST_CREATED: 'POST_CREATED',
  POST_UPDATED: 'POST_UPDATED',
  COMMENT_ADDED: 'COMMENT_ADDED',
  USER_ONLINE: 'USER_ONLINE',
} as const;
```

## 订阅解析器

```typescript
import { withFilter } from 'graphql-subscriptions';
import { pubsub, EVENTS } from './pubsub';

const resolvers = {
  Subscription: {
    // 简单订阅
    postCreated: {
      subscribe: () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
    },

    // 带过滤的订阅
    postUpdated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.POST_UPDATED]),
        (payload, variables) => {
          // 仅发送特定帖子的更新
          return payload.postUpdated.id === variables.id;
        }
      ),
    },

    // 带授权的过滤订阅
    commentAdded: {
      subscribe: withFilter(
        (parent, args, context) => {
          // 订阅前检查身份验证
          if (!context.user) {
            throw new Error('未授权');
          }
          return pubsub.asyncIterator([EVENTS.COMMENT_ADDED]);
        },
        async (payload, variables, context) => {
          // 按帖子过滤并检查权限
          if (payload.commentAdded.postId !== variables.postId) {
            return false;
          }

          // 检查用户是否有权访问帖子
          const post = await context.dataSources.posts.findById(
            variables.postId
          );
          return post && post.isPublic || post.authorId === context.user.id;
        }
      ),
    },

    // 带多个过滤器的复杂订阅
    userOnline: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.USER_ONLINE]),
        (payload, variables, context) => {
          // 仅通知好友
          return context.user.friends.includes(payload.userOnline.id);
        }
      ),
    },
  },

  Mutation: {
    createPost: async (parent, args, context) => {
      const post = await context.dataSources.posts.create(args.input);

      // 发布事件
      await pubsub.publish(EVENTS.POST_CREATED, {
        postCreated: post,
      });

      return post;
    },

    updatePost: async (parent, args: { id: string; input: any }, context) => {
      const post = await context.dataSources.posts.update(
        args.id,
        args.input
      );

      await pubsub.publish(EVENTS.POST_UPDATED, {
        postUpdated: post,
      });

      return post;
    },

    addComment: async (parent, args, context) => {
      const comment = await context.dataSources.comments.create(args.input);

      await pubsub.publish(EVENTS.COMMENT_ADDED, {
        commentAdded: comment,
      });

      return comment;
    },
  },
};
```

## 高级过滤

```typescript
// 类型安全的 payload
interface PostCreatedPayload {
  postCreated: Post;
  tags: string[];
  isPublic: boolean;
}

const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
        async (
          payload: PostCreatedPayload,
          variables: { tags?: string[]; authorId?: string },
          context: Context
        ) => {
          // 按标签过滤
          if (variables.tags && variables.tags.length > 0) {
            const hasMatchingTag = payload.tags.some(tag =>
              variables.tags!.includes(tag)
            );
            if (!hasMatchingTag) return false;
          }

          // 按作者过滤
          if (variables.authorId) {
            if (payload.postCreated.authorId !== variables.authorId) {
              return false;
            }
          }

          // 检查权限
          if (!payload.isPublic) {
            return (
              context.user?.id === payload.postCreated.authorId ||
              context.user?.isAdmin
            );
          }

          return true;
        }
      ),
    },
  },
};
```

## 连接管理

```typescript
import { useServer } from 'graphql-ws/lib/use/ws';

const wsServer = useServer(
  {
    schema,

    // 连接生命周期
    onConnect: async (ctx) => {
      console.log('客户端已连接');
      const token = ctx.connectionParams?.authorization;

      if (!token) {
        throw new Error('缺少身份验证令牌');
      }

      const user = await verifyToken(token);
      if (!user) {
        throw new Error('无效令牌');
      }

      return { user };
    },

    onDisconnect: (ctx, code, reason) => {
      console.log('客户端已断开连接', code, reason);
    },

    // 订阅生命周期
    onSubscribe: async (ctx, msg) => {
      console.log('客户端已订阅', msg.payload.operationName);

      // 速率限制
      const subscriptionCount = getUserSubscriptionCount(ctx.user.id);
      if (subscriptionCount >= 10) {
        throw new Error('订阅过多');
      }

      return { ctx, msg };
    },

    onComplete: (ctx, msg) => {
      console.log('订阅已完成', msg.id);
    },

    // Keep-alive
    connectionInitWaitTimeout: 10000,

    // 每个订阅的 context
    context: async (ctx, msg, args) => {
      const user = ctx.extra.user;
      return {
        user,
        dataSources: createDataSources(),
        subscriptionId: msg.id,
      };
    },
  },
  wsServer
);
```

## 订阅模式

```typescript
// 模式 1：实体更新
type Subscription {
  entityUpdated(id: ID!): Entity!
}

// 模式 2：集合更新
type Subscription {
  entityAdded: Entity!
  entityDeleted: ID!
}

// 模式 3：事件流
type Subscription {
  events(types: [EventType!]): Event!
}

// 模式 4：实时查询（带间隔）
type Subscription {
  liveQuery(query: String!): [SearchResult!]!
}

// resolvers.ts
const resolvers = {
  Subscription: {
    // 实时查询实现
    liveQuery: {
      subscribe: async function* (parent, args, context) {
        while (true) {
          const results = await context.dataSources.search(args.query);
          yield { liveQuery: results };
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      },
    },
  },
};
```

## 错误处理

```typescript
const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
        async (payload, variables, context) => {
          try {
            // 检查权限
            if (!context.user) {
              throw new GraphQLError('未授权', {
                extensions: { code: 'UNAUTHENTICATED' },
              });

              return true;
            }
          } catch (error) {
            // 记录错误但不传播到客户端
            console.error('订阅过滤器错误：', error);
            return false;
          }
        }
      ),

      // 解析订阅 payload
      resolve: (payload) => {
        try {
          return payload.postCreated;
        } catch (error) {
          throw new GraphQLError('订阅解析失败', {
            extensions: { code: 'SUBSCRIPTION_RESOLVE_ERROR' },
          });
        }
      },
    },
  },
};
```

## 客户端使用

```typescript
// Apollo Client 设置
import { ApolloClient, InMemoryCache, split, HttpLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

const httpLink = new HttpLink({
  uri: 'http://localhost:4000/graphql',
});

const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:4000/graphql',
    connectionParams: {
      authorization: `Bearer ${token}`,
    },
  })
);

const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});

// 订阅事件
const subscription = client
  .subscribe({
    query: gql`
      subscription OnPostCreated {
        postCreated {
          id
          title
          author {
            username
          }
        }
      }
    `,
  })
  .subscribe({
    next: (data) => console.log('新帖子：', data),
    error: (err) => console.error('订阅错误：', err),
    complete: () => console.log('订阅已完成'),
  });

// 取消订阅
subscription.unsubscribe();
```

## 订阅扩展

```typescript
// 使用 Redis 进行多实例部署
import { RedisPubSub } from 'graphql-redis-subscriptions';

// 水平扩展模式
const pubsub = new RedisPubSub({
  publisher: new Redis(redisConfig),
  subscriber: new Redis(redisConfig),
  // 通道前缀用于隔离
  publisherPrefix: 'graphql:pub:',
  subscriberPrefix: 'graphql:sub:',
});

// 每实例连接限制
const MAX_CONNECTIONS_PER_INSTANCE = 10000;

// 带粘性会话的负载均衡
// 确保同一用户连接到同一服务器实例
// 用于连接状态管理
```

## 订阅最佳实践

1. **身份验证**：始终在 onConnect 和过滤器中验证身份
2. **授权**：在 withFilter 中检查权限
3. **速率限制**：限制每个用户的订阅数
4. **过滤**：使用 withFilter 进行服务端过滤
5. **清理**：在断开连接时始终清理订阅
6. **扩展**：使用 Redis PubSub 进行多实例部署
7. **错误处理**：在过滤器和解析器中优雅地处理错误
8. **测试**：测试订阅生命周期和过滤
9. **监控**：跟踪活动连接和订阅数
10. **性能**：避免订阅解析器中的 N+1 问题
