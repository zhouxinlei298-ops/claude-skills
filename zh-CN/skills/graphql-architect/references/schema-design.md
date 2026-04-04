# GraphQL Schema 设计

## 对象类型

```graphql
"""
具有身份验证和配置文件信息的用户账户。
所有用户必须具有唯一的电子邮件地址。
"""
type User {
  "唯一用户标识符"
  id: ID!
  "用户电子邮件地址（唯一）"
  email: String!
  "显示名称（可选）"
  username: String
  "账户创建时间戳"
  createdAt: DateTime!
  "用户的帖子（分页）"
  posts(first: Int = 10, after: String): PostConnection!
  "用户的配置文件（如果未完成则为可为空）"
  profile: Profile
}

type Profile {
  id: ID!
  bio: String
  avatarUrl: URL
  website: URL
  location: String
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  publishedAt: DateTime
  status: PostStatus!
  tags: [Tag!]!
  comments(first: Int, after: String): CommentConnection!
}
```

## 接口

```graphql
"""
所有可以加时间戳的内容的通用接口
"""
interface Timestamped {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
}

"""
可搜索内容的接口
"""
interface Searchable {
  id: ID!
  title: String!
  description: String
}

type Article implements Timestamped & Searchable {
  id: ID!
  title: String!
  description: String
  content: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  author: User!
}

type Video implements Timestamped & Searchable {
  id: ID!
  title: String!
  description: String
  url: URL!
  duration: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
  uploader: User!
}

# 返回接口的查询
type Query {
  search(query: String!): [Searchable!]!
}
```

## 联合类型

```graphql
"""
内容搜索的结果 - 可以是 Article、Video 或 Podcast
"""
union SearchResult = Article | Video | Podcast

"""
用户可以接收的通知类型
"""
union Notification = CommentNotification | LikeNotification | FollowNotification

type CommentNotification {
  id: ID!
  comment: Comment!
  post: Post!
  createdAt: DateTime!
}

type LikeNotification {
  id: ID!
  liker: User!
  post: Post!
  createdAt: DateTime!
}

type Query {
  searchContent(query: String!): [SearchResult!]!
  notifications(first: Int): [Notification!]!
}
```

## 枚举

```graphql
"""
帖子发布状态
"""
enum PostStatus {
  DRAFT
  PUBLISHED
  ARCHIVED
  DELETED
}

"""
用于授权的用户角色
"""
enum UserRole {
  ADMIN
  MODERATOR
  USER
  GUEST
}

"""
查询的排序方向
"""
enum SortOrder {
  ASC
  DESC
}

type Query {
  posts(
    status: PostStatus
    orderBy: SortOrder = DESC
  ): [Post!]!
}
```

## 输入类型

```graphql
"""
创建新用户的输入
"""
input CreateUserInput {
  email: String!
  password: String!
  username: String
  profile: ProfileInput
}

input ProfileInput {
  bio: String
  avatarUrl: URL
  website: URL
  location: String
}

"""
更新帖子的输入
"""
input UpdatePostInput {
  title: String
  content: String
  status: PostStatus
  tags: [ID!]
}

"""
分页和过滤输入
"""
input PostFilterInput {
  status: PostStatus
  authorId: ID
  tags: [String!]
  search: String
  createdAfter: DateTime
  createdBefore: DateTime
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updatePost(id: ID!, input: UpdatePostInput!): Post!
}

type Query {
  posts(filter: PostFilterInput, first: Int, after: String): PostConnection!
}
```

## 自定义标量

```graphql
"""
ISO 8601 日期时间字符串
"""
scalar DateTime

"""
有效的 URL 字符串
"""
scalar URL

"""
有效的电子邮件地址
"""
scalar Email

"""
JSON 对象
"""
scalar JSON

"""
正整数
"""
scalar PositiveInt

type User {
  id: ID!
  email: Email!
  createdAt: DateTime!
  website: URL
  metadata: JSON
  age: PositiveInt
}
```

## 分页模式

```graphql
"""
基于游标的分页（Relay 规范）
"""
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

type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
  ): PostConnection!
}
```

## 可空 vs 非空最佳实践

```graphql
type User {
  # 非空：保证存在
  id: ID!
  email: String!
  createdAt: DateTime!

  # 可空：可选或可能尚不存在
  username: String
  bio: String
  avatarUrl: URL

  # 可空项的可空列表
  # 列表始终存在但项可为空
  tags: [String]!

  # 非空项的非空列表
  # 列表始终存在，所有项保证非空
  roles: [UserRole!]!

  # 可空项的列表
  # 列表可能为空但如果存在，所有项非空
  posts: [Post!]
}

type Query {
  # 非空：查询始终返回结果（如果没有则为空列表）
  users: [User!]!

  # 可空：如果未找到可能返回 null
  user(id: ID!): User

  # 非空：保证返回结果或错误
  currentUser: User!
}
```

## 字段弃用

```graphql
type User {
  id: ID!
  email: String!

  # 带有迁移路径的弃用字段
  name: String @deprecated(reason: "使用 'username' 代替")
  username: String

  # 带有特定日期的弃用
  legacyId: String @deprecated(
    reason: "迁移到 UUID。将于 2025-06-01 移除"
  )
}
```

## Schema 文档

```graphql
"""
User 表示系统中的已验证账户。
用户可以创建帖子、评论并与内容交互。

示例查询：
```
query GetUser {
  user(id: "123") {
    email
    username
    posts(first: 10) {
      edges {
        node {
          title
        }
      }
    }
  }
}
```
"""
type User {
  "用户的唯一标识符"
  id: ID!

  "电子邮件地址（必须在所有用户中唯一）"
  email: String!

  "可选的显示名称（如果未设置则默认为电子邮件）"
  username: String
}
```

## 设计原则

1. **可空字段**：默认情况下使字段可为空，除非保证存在
2. **列表字段**：对于总是存在且具有非空项的列表使用 `[Type!]!`
3. **文档**：使用描述记录所有类型和字段
4. **命名**：字段使用 camelCase，类型使用 PascalCase
5. **接口**：对类型之间的共享字段使用接口
6. **联合**：对多态返回类型使用联合
7. **输入类型**：为变更创建单独的输入类型
8. **标量**：为域特定类型使用自定义标量
9. **弃用**：标记弃用字段，提供迁移路径
10. **示例**：在文档中包含示例查询
