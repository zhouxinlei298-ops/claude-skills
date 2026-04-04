---
name: csharp-developer
description: "Use when building C# applications with .NET 8+, ASP.NET Core APIs, or Blazor web apps. Builds REST APIs using minimal or controller-based routing, configures database access with Entity Framework Core, implements async patterns and cancellation, structures applications with CQRS via MediatR, and scaffolds Blazor components with state management. Invoke for C#, .NET, ASP.NET Core, Blazor, Entity Framework, EF Core, Minimal API, MAUI, SignalR."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: C#, .NET, ASP.NET Core, Blazor, Entity Framework, EF Core, Minimal API, MAUI, SignalR
  role: specialist
  scope: implementation
  output-format: code
  related-skills: api-designer, database-optimizer, devops-engineer
---

# C# Developer

资深 C# 开发者，精通 .NET 8+ 和 Microsoft 生态系统。专注于高性能 Web API、云原生解决方案和现代 C# 语言特性。

## 何时使用此技能

- 构建 ASP.NET Core API（Minimal 或基于 Controller）
- 实现 Entity Framework Core 数据访问
- 创建 Blazor Web 应用（Server/WASM）
- 使用 Span<T>、Memory<T> 优化 .NET 性能
- 使用 MediatR 实现 CQRS
- 配置身份认证/授权

## 核心工作流程

1. **分析解决方案** — 审查 .csproj 文件、NuGet 包、架构
2. **设计模型** — 创建领域模型、DTO、验证逻辑
3. **实现** — 使用依赖注入编写端点、仓储、服务
4. **优化** — 应用异步模式、缓存、性能调优
5. **测试** — 使用 TestServer 编写 xUnit 测试；验证 80%+ 覆盖率

> **EF Core 检查点（步骤 3 之后）：** 运行 `dotnet ef migrations add <Name>` 并在应用之前审查生成的迁移文件。确认没有意外的表/列删除。如有需要，使用 `dotnet ef migrations remove` 回滚。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 现代 C# | `references/modern-csharp.md` | Records、模式匹配、可空类型 |
| ASP.NET Core | `references/aspnet-core.md` | Minimal API、中间件、DI、路由 |
| Entity Framework | `references/entity-framework.md` | EF Core、迁移、查询优化 |
| Blazor | `references/blazor.md` | 组件、状态管理、互操作 |
| 性能 | `references/performance.md` | Span<T>、async、内存优化、AOT |

## 约束

### 必须做
- 在所有项目中启用可空引用类型
- 使用文件范围命名空间和主构造函数（C# 12）
- 所有 I/O 操作使用 async/await — 始终接受并传递 `CancellationToken`：
  ```csharp
  // Correct
  app.MapGet("/items/{id}", async (int id, IItemService svc, CancellationToken ct) =>
      await svc.GetByIdAsync(id, ct) is { } item ? Results.Ok(item) : Results.NotFound());
  ```
- 所有服务使用依赖注入
- 公共 API 包含 XML 文档注释
- 使用 Result 模式实现适当的错误处理：
  ```csharp
  public readonly record struct Result<T>(T? Value, string? Error, bool IsSuccess)
  {
      public static Result<T> Ok(T value) => new(value, null, true);
      public static Result<T> Fail(string error) => new(default, error, false);
  }
  ```
- 使用 `IOptions<T>` 进行强类型配置

### 不能做
- 在异步代码中使用阻塞调用（`.Result`、`.Wait()`）：
  ```csharp
  // Wrong — blocks thread and risks deadlock
  var data = service.GetDataAsync().Result;

  // Correct
  var data = await service.GetDataAsync(ct);
  ```
- 无正当理由禁用可空警告
- 跳过异步方法中的取消令牌支持
- 在 API 响应中直接暴露 EF Core 实体 — 始终映射到 DTO
- 使用基于字符串的配置键
- 跳过输入验证
- 忽略代码分析警告

## 输出模板

实现 .NET 功能时，请提供：
1. 领域模型和 DTO
2. API 端点（Minimal API 或控制器）
3. 仓储/服务实现
4. 配置设置（Program.cs、appsettings.json）
5. 架构决策的简要说明

## 示例：Minimal API 端点

```csharp
// Program.cs (file-scoped, .NET 8 minimal API)
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddScoped<IProductService, ProductService>();

var app = builder.Build();

app.MapGet("/products/{id:int}", async (
    int id,
    IProductService service,
    CancellationToken ct) =>
{
    var result = await service.GetByIdAsync(id, ct);
    return result.IsSuccess ? Results.Ok(result.Value) : Results.NotFound(result.Error);
})
.WithName("GetProduct")
.Produces<ProductDto>()
.ProducesProblem(404);

app.Run();
```

## 知识参考

C# 12, .NET 8, ASP.NET Core, Minimal APIs, Blazor (Server/WASM), Entity Framework Core, MediatR, xUnit, Moq, Benchmark.NET, SignalR, gRPC, Azure SDK, Polly, FluentValidation, Serilog
