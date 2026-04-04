# API 版本控制策略

## 为什么要对 API 进行版本控制？

API 版本控制允许您在保持现有客户端向后兼容性的同时演进 API。破坏性更改需要新版本。

### 破坏性更改

需要新版本的更改：
- 移除或重命名字段
- 更改字段类型（字符串到整数）
- 向请求添加必填字段
- 更改响应结构
- 移除端点
- 为相同场景更改 HTTP 状态码
- 更改身份验证机制

### 非破坏性更改

不需要新版本的安全更改：
- 添加新端点
- 添加可选请求字段
- 向响应添加新字段（客户端应忽略未知字段）
- 修复错误
- 性能改进
- 向现有资源添加新 HTTP 方法

## 版本控制策略

### 1. URI 版本控制

最常见和可见的方法。版本是 URL 路径的一部分。

```http
GET /v1/users/123
GET /v2/users/123
```

**优点：**
- 在 URL 中清晰可见
- 易于理解和实现
- 简单的路由和缓存
- 可以同时运行多个版本

**缺点：**
- 违反 REST 原则（相同资源、不同 URI）
- 需要更新客户端代码以更改版本
- 可能导致 URI 激增

**实现：**
```
/v1/users
/v1/products
/v2/users      # 带有破坏性更改的新版本
/v2/products
```

### 2. 头版本控制

在 HTTP 头（Accept 头或自定义头）中指定版本。

**Accept 头：**
```http
GET /users/123
Accept: application/vnd.myapi.v1+json

GET /users/123
Accept: application/vnd.myapi.v2+json
```

**自定义头：**
```http
GET /users/123
API-Version: 1

GET /users/123
API-Version: 2
```

**优点：**
- URI 保持稳定
- 更符合 REST（相同资源、相同 URI）
- 将版本控制与资源标识分离

**缺点：**
- 可见性较低（更难调试）
- 更复杂的路由
- 难以在浏览器中测试
- 缓存复杂性

### 3. 查询参数版本控制

版本指定为查询参数。

```http
GET /users/123?version=1
GET /users/123?version=2

# 或
GET /users/123?api-version=1
GET /users/123?api-version=2
```

**优点：**
- 简单实现
- 易于测试
- 在 URL 中可见

**缺点：**
- 污染查询字符串
- 非语义（版本不是过滤器）
- 可能干扰其他查询参数

### 4. 内容协商

客户端通过内容协商指定所需版本。

```http
GET /users/123
Accept: application/vnd.myapi+json; version=1

GET /users/123
Accept: application/vnd.myapi+json; version=2
```

**优点：**
- 非常 RESTful
- 灵活的内容类型协商
- 稳定的 URI

**缺点：**
- 复杂实现
- 对开发者不太直观
- 难以测试

## 推荐方法

**URI 版本控制被推荐用于大多数 API**，因为：
- 最明确和可发现
- 易于理解和调试
- 实现和维护简单
- 版本之间清晰分离

```
/v1/users
/v2/users
/v3/users
```

## 版本格式

### 仅主版本

对公共 API 使用简单的主版本（v1、v2、v3）：
```
/v1/users
/v2/users
```

**优点：**
- 简单清晰
- 易于沟通
- 强制仔细考虑破坏性更改

### 基于日期的版本

某些 API 使用日期作为版本：
```
/2024-01-01/users
/2024-06-15/users
```

**由以下使用：** Stripe、GitHub API

**优点：**
- 清楚版本何时发布
- 易于理解时间线
- 没有关于主要/次要的困惑

**缺点：**
- 对客户端不太直观
- 难以理解更改了什么

## 版本生命周期

### 1. 引入阶段

新版本与现有版本一起发布：
```
/v1/users  # 仍然支持
/v2/users  # 新版本可用
```

宣布新版本：
- 解释更改的博客文章
- 迁移指南
- 破坏性更改列表
- v1 弃用时间表

### 2. 弃用阶段

将旧版本标记为弃用但保持运行：

```http
GET /v1/users/123

响应：
Deprecation: true
Sunset: Wed, 15 Jan 2025 00:00:00 GMT
Link: </v2/users/123>; rel="successor-version"

{
  "id": 123,
  "name": "John Doe"
}
```

**弃用头：**
- `Deprecation: true` - 指示版本已弃用
- `Sunset: <date>` - 版本将被移除的时间（RFC 8594）
- `Link: <url>; rel="successor-version"` - 指向新版本

### 3. 停用阶段

旧版本在公告日期关闭。

为弃用端点返回 410 Gone：
```http
GET /v1/users/123

响应：410 Gone
{
  "error": {
    "code": "VERSION_SUNSET",
    "message": "API v1 于 2025-01-15 停用。请使用 v2。",
    "documentation_url": "https://api.example.com/docs/migration-v1-to-v2"
  }
}
```

## 弃用策略

### 推荐时间表

1. **宣布弃用** - 至少在停用前 6 个月
2. **支持期** - 同时运行两个版本 6-12 个月
3. **停用日期** - 提前清楚沟通日期
4. **宽限期** - 完全关闭前 30 天 410 Gone 响应

### 沟通渠道

- API 响应头
- 向注册开发者发送电子邮件
- 博客文章和变更日志
- 仪表板通知
- 文档更新
- 状态页面公告

## 迁移策略

### 提供迁移指南

```markdown
# 从 v1 迁移到 v2

## 破坏性更改

### 用户资源更改

**v1：**
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com"
}
```

**v2：**
```json
{
  "id": 123,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

**迁移：**
- 将 `name` 字段拆分为 `first_name` 和 `last_name`
- 更新客户端代码以使用新字段
```

### 提供工具

- 迁移脚本
- SDK 更新
- API 差异查看器
- 兼容层（临时）

## 版本发现

### 根端点

```http
GET /

响应：
{
  "versions": {
    "v1": {
      "status": "deprecated",
      "sunset_date": "2025-01-15",
      "documentation_url": "https://api.example.com/docs/v1"
    },
    "v2": {
      "status": "current",
      "documentation_url": "https://api.example.com/docs/v2"
    },
    "v3": {
      "status": "beta",
      "documentation_url": "https://api.example.com/docs/v3"
    }
  }
}
```

### 版本信息端点

```http
GET /v2/version

响应：
{
  "version": "v2",
  "released": "2024-01-15",
  "status": "stable",
  "sunset_date": null
}
```

## OpenAPI 版本控制

### 每个版本的单独规范

```
openapi-v1.yaml
openapi-v2.yaml
openapi-v3.yaml
```

每个规范是完整且独立的。

### 单一规范和多个服务器

```yaml
openapi: 3.1.0
info:
  title: My API
  version: 2.0.0
servers:
  - url: https://api.example.com/v1
    description: 版本 1（已弃用）
  - url: https://api.example.com/v2
    description: 版本 2（当前）
```

## 最佳实践

1. **从第一天开始版本控制** - 从 /v1 开始，而不是 /api
2. **仅主版本** - 使用 v1、v2、v3（而不是 v1.1、v1.2）
3. **长期弃用期** - 给客户端时间迁移（6-12 个月）
4. **清楚沟通** - 使用头、文档、电子邮件
5. **维护旧版本** - 同时支持至少 2 个版本
6. **记录更改** - 提供详细的迁移指南
7. **使用语义版本控制** - 用于内部/SDK 版本控制
8. **从不警告就破坏** - 始终宣布破坏性更改
9. **提供工具** - 迁移脚本、更新的 SDK
10. **监控使用** - 跟踪正在使用哪些版本

## 反模式

避免这些错误：

- **没有版本升级的破坏性更改** - 破坏现有客户端
- **太多版本** - 维护噩梦（最多 2-3 个活动版本）
- **短期弃用** - 挫败开发者
- **无迁移路径** - 使升级痛苦
- **意外停用** - 在没有警告的情况下破坏生产应用程序
- **不一致的版本控制** - 不同端点使用不同策略
- **单个端点版本控制** - 在整个 API 中使用一致的版本
