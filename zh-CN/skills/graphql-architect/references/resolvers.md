# GraphQL 解析器

## 基本解析器模式

```typescript
import { GraphQLResolveInfo } from 'graphql';

// 解析器签名
type Resolver<TSource, TArgs, TContext, TReturn> = (
  parent: TSource,
  args: TArgs,
  context: TContext,
  info: GraphQLResolveInfo
) => Promise<TReturn> | TReturn;

// 用户解析器
const resolvers = {
  Query: {
    user: async (
      parent,
      args: { id: string },
      context: Context
    ): Promise<User | null> => {
      return context.dataSources.users.findById(args.id);
    },

    users: async (
      parent,
      args: { first?: number; after?: string },
      context: Context
    ): Promise<User[]> => {
      return context.dataSources.users.findAll(args);
    },
  },

  Mutation: {
    createUser: async (
      parent,
      args: { input: CreateUserInput },
      context: Context
    ): Promise<User> => {
      if (!context.user) {
        throw new Error('Unauthorized');
      }
      return context.dataSources.users.create(args.input);
    },
  },
};
```

## Context 设置

```typescript
import { Request } from 'express';
import { User } from './models';
import { DataSources } from './datasources';

export interface Context {
  user: User | null;
  dataSources: DataSources;
  loaders: Loaders;
  req: Request;
  authToken: string | null;
}

// Apollo Server context
const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: async ({ req }): Promise<Context> => {
    // 提取身份验证令牌
    const authToken = req.headers.authorization?.replace('Bearer ', '') || null;

    // 验证用户
    let user: User | null = null;
    if (authToken) {
      user = await verifyToken(authToken);
    }

    // 创建数据源
    const dataSources = new DataSources({
      db: prisma,
      redis: redisClient,
    });

    // 创建 DataLoaders
    const loaders = createLoaders(dataSources);

    return {
      user,
      dataSources,
      loaders,
      req,
      authToken,
    };
  },
});
```

## DataLoader 用于 N+1 预防

```typescript
import DataLoader from 'dataloader';

// 创建 loaders
export function createLoaders(dataSources: DataSources): Loaders {
  return {
    userLoader: new DataLoader<string, User>(
      async (ids: readonly string[]) => {
        const users = await dataSources.users.findByIds([...ids]);
        // 按输入 id 的顺序返回
        return ids.map(id => users.find(u => u.id === id) || null);
      },
      {
        cache: true,
        batchScheduleFn: (callback) => setTimeout(callback, 10),
      }
    ),

    postsByAuthorLoader: new DataLoader<string, Post[]>(
      async (authorIds: readonly string[]) => {
        const posts = await dataSources.posts.findByAuthorIds([...authorIds]);
        // 按作者分组
        return authorIds.map(authorId =>
          posts.filter(p => p.authorId === authorId)
        );
      }
    ),
  };
}

// 使用 DataLoader 的字段解析器
const resolvers = {
  Post: {
    author: async (
      post: Post,
      args,
      context: Context
    ): Promise<User> => {
      // 将多个请求批处理到单个 DB 查询
      return context.loaders.userLoader.load(post.authorId);
    },
  },

  User: {
    posts: async (
      user: User,
      args,
      context: Context
    ): Promise<Post[]> => {
      return context.loaders.postsByAuthorLoader.load(user.id);
    },
  },
};
```

## 字段解析器

```typescript
const resolvers = {
  User: {
    // 简单字段解析器
    fullName: (user: User): string => {
      return `${user.firstName} ${user.lastName}`;
    },

    // 带有 DB 查询的异步字段解析器
    postCount: async (
      user: User,
      args,
      context: Context
    ): Promise<number> => {
      return context.dataSources.posts.countByAuthor(user.id);
    },

    // 带有参数的字段解析器
    posts: async (
      user: User,
      args: { first?: number; status?: PostStatus },
      context: Context
    ): Promise<Post[]> => {
      return context.dataSources.posts.findByAuthor(user.id, {
        limit: args.first,
        status: args.status,
      });
    },

    // 带有条件逻辑的可空字段
    profile: async (
      user: User,
      args,
      context: Context
    ): Promise<Profile | null> => {
      if (!user.hasProfile) return null;
      return context.loaders.profileLoader.load(user.id);
    },
  },
};
```

## 接口解析器

```typescript
const resolvers = {
  // 接口类型解析器
  Searchable: {
    __resolveType(obj: Article | Video | Podcast): string {
      if ('content' in obj) return 'Article';
      if ('duration' in obj) return 'Video';
      if ('audioUrl' in obj) return 'Podcast';
      throw new Error('Unknown Searchable type');
    },
  },

  // 通用接口字段（共享解析器）
  Article: {
    id: (article: Article) => article.id,
    title: (article: Article) => article.title,
    description: (article: Article) => article.description,
  },

  Video: {
    id: (video: Video) => video.id,
    title: (video: Video) => video.title,
    description: (video: Video) => video.description,
  },
};
```

## 联合解析器

```typescript
const resolvers = {
  // 联合类型解析器
  SearchResult: {
    __resolveType(
      obj: Article | Video | Podcast,
      context: Context,
      info: GraphQLResolveInfo
    ): string {
      if ('content' in obj) return 'Article';
      if ('duration' in obj && 'url' in obj) return 'Video';
      if ('audioUrl' in obj) return 'Podcast';
      throw new Error('Unknown SearchResult type');
    },
  },

  Query: {
    searchContent: async (
      parent,
      args: { query: string },
      context: Context
    ): Promise<(Article | Video | Podcast)[]> => {
      // 返回不同类型的混合数组
      const [articles, videos, podcasts] = await Promise.all([
        context.dataSources.articles.search(args.query),
        context.dataSources.videos.search(args.query),
        context.dataSources.podcasts.search(args.query),
      ]);
      return [...articles, ...videos, ...podcasts];
    },
  },
};
```

## 错误处理

```typescript
import { GraphQLError } from 'graphql';
import { ApolloServerErrorCode } from '@apollo/server/errors';

const resolvers = {
  Query: {
    user: async (
      parent,
      args: { id: string },
      context: Context
    ): Promise<User> => {
      const user = await context.dataSources.users.findById(args.id);

      if (!user) {
        throw new GraphQLError('User not found', {
          extensions: {
            code: 'USER_NOT_FOUND',
            http: { status: 404 },
            userId: args.id,
          },
        });
      }

      return user;
    },
  },

  Mutation: {
    updateUser: async (
      parent,
      args: { id: string; input: UpdateUserInput },
      context: Context
    ): Promise<User> => {
      // 检查身份验证
      if (!context.user) {
        throw new GraphQLError('Unauthorized', {
          extensions: {
            code: ApolloServerErrorCode.UNAUTHENTICATED,
            http: { status: 401 },
          },
        });
      }

      // 检查授权
      if (context.user.id !== args.id && !context.user.isAdmin) {
        throw new GraphQLError('Forbidden', {
          extensions: {
            code: ApolloServerErrorCode.FORBIDDEN,
            http: { status: 403 },
          },
        });
      }

      try {
        return await context.dataSources.users.update(args.id, args.input);
      } catch (error) {
        throw new GraphQLError('Failed to update user', {
          extensions: {
            code: 'UPDATE_FAILED',
            originalError: error,
          },
        });
      }
    },
  },
};
```

## 分页解析器

```typescript
import { encodeCursor, decodeCursor } from './utils/cursor';

const resolvers = {
  Query: {
    posts: async (
      parent,
      args: { first?: number; after?: string },
      context: Context
    ): Promise<PostConnection> => {
      const limit = Math.min(args.first || 10, 100);
      const cursor = args.after ? decodeCursor(args.after) : null;

      // 获取额外的一个以确定 hasNextPage
      const posts = await context.dataSources.posts.findAll({
        limit: limit + 1,
        cursor,
      });

      const hasNextPage = posts.length > limit;
      const edges = posts.slice(0, limit).map(post => ({
        node: post,
        cursor: encodeCursor(post.id),
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!cursor,
          startCursor: edges[0]?.cursor || null,
          endCursor: edges[edges.length - 1]?.cursor || null,
        },
        totalCount: await context.dataSources.posts.count(),
      };
    },
  },
};
```

## 批处理模式

```typescript
// 批处理多个查询
class UserDataSource {
  private db: PrismaClient;

  async findByIds(ids: string[]): Promise<User[]> {
    // 单个查询而不是 N 个查询
    return this.db.user.findMany({
      where: { id: { in: ids } },
    });
  }

  async findByEmails(emails: string[]): Promise<User[]> {
    return this.db.user.findMany({
      where: { email: { in: emails } },
    });
  }
}

// 带有缓存的 DataLoader
const userLoader = new DataLoader<string, User>(
  async (ids) => {
    console.log('批处理用户查询：', ids.length);
    const users = await dataSources.users.findByIds([...ids]);
    return ids.map(id => users.find(u => u.id === id) || null);
  },
  {
    cache: true,
    maxBatchSize: 100,
    batchScheduleFn: (callback) => setTimeout(callback, 10),
  }
);
```

## 解析器最佳实践

1. **使用 DataLoader**：始终批处理和缓存数据库查询
2. **避免 N+1**：对所有的外键关系使用 DataLoader
3. **类型安全**：使用 TypeScript 进行解析器类型安全
4. **错误处理**：抛出带有正确代码和扩展的 GraphQLError
5. **授权**：在解析器中检查权限，而不是数据源
6. **分页**：为列表实现基于游标的分页
7. **Context**：保持 context 创建轻量级
8. **缓存**：每个请求使用 DataLoader 缓存
9. **批处理**：使用 DataLoader 或在数据源中批处理查询
10. **测试**：使用模拟的 context 对解析器进行单元测试
