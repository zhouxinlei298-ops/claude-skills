# Minimal APIs

## 基本端点模式

```csharp
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);

// 添加服务
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// 配置中间件
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// 简单的 GET 端点
app.MapGet("/api/products", async (IProductService service) =>
{
    var products = await service.GetAllAsync();
    return Results.Ok(products);
});

// 带路由参数的 GET
app.MapGet("/api/products/{id:int}", async (int id, IProductService service) =>
{
    var product = await service.GetByIdAsync(id);
    return product is not null
        ? Results.Ok(product)
        : Results.NotFound();
});

// 带验证的 POST
app.MapPost("/api/products", async (
    [FromBody] CreateProductRequest request,
    IProductService service) =>
{
    var product = await service.CreateAsync(request);
    return Results.Created($"/api/products/{product.Id}", product);
})
.WithName("CreateProduct")
.Produces<ProductResponse>(StatusCodes.Status201Created)
.ProducesValidationProblem();

// PUT 端点
app.MapPut("/api/products/{id:int}", async (
    int id,
    [FromBody] UpdateProductRequest request,
    IProductService service) =>
{
    var success = await service.UpdateAsync(id, request);
    return success ? Results.NoContent() : Results.NotFound();
});

// DELETE 端点
app.MapDelete("/api/products/{id:int}", async (int id, IProductService service) =>
{
    await service.DeleteAsync(id);
    return Results.NoContent();
});

app.Run();
```

## 路由组

```csharp
var app = builder.Build();

var api = app.MapGroup("/api")
    .WithOpenApi()
    .RequireAuthorization();

var products = api.MapGroup("/products")
    .WithTags("Products");

products.MapGet("/", GetAllProducts);
products.MapGet("/{id:int}", GetProductById);
products.MapPost("/", CreateProduct);
products.MapPut("/{id:int}", UpdateProduct);
products.MapDelete("/{id:int}", DeleteProduct);

static async Task<IResult> GetAllProducts(IProductService service)
{
    var products = await service.GetAllAsync();
    return Results.Ok(products);
}

static async Task<IResult> GetProductById(int id, IProductService service)
{
    var product = await service.GetByIdAsync(id);
    return product is not null ? Results.Ok(product) : Results.NotFound();
}
```

## 过滤器和验证

```csharp
using FluentValidation;

// 带验证的请求 DTO
public record CreateProductRequest(
    string Name,
    string Description,
    decimal Price,
    int CategoryId
);

public class CreateProductValidator : AbstractValidator<CreateProductRequest>
{
    public CreateProductValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(100);

        RuleFor(x => x.Price)
            .GreaterThan(0)
            .LessThan(1000000);

        RuleFor(x => x.CategoryId)
            .GreaterThan(0);
    }
}

// 端点过滤器用于验证
public class ValidationFilter<T> : IEndpointFilter where T : class
{
    private readonly IValidator<T> _validator;

    public ValidationFilter(IValidator<T> validator)
    {
        _validator = validator;
    }

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        var request = context.Arguments.OfType<T>().FirstOrDefault();
        if (request is null)
        {
            return Results.BadRequest("Invalid request");
        }

        var validationResult = await _validator.ValidateAsync(request);
        if (!validationResult.IsValid)
        {
            return Results.ValidationProblem(
                validationResult.ToDictionary());
        }

        return await next(context);
    }
}

// 注册和使用
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

app.MapPost("/api/products", CreateProduct)
    .AddEndpointFilter<ValidationFilter<CreateProductRequest>>();
```

## 依赖注入

```csharp
// 服务注册
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IProductRepository, ProductRepository>();

// 多参数绑定
app.MapPost("/api/orders", async (
    CreateOrderRequest request,
    IOrderService orderService,
    IEmailService emailService,
    ILogger<Program> logger,
    CancellationToken ct) =>
{
    logger.LogInformation("Creating order for {CustomerId}", request.CustomerId);

    var order = await orderService.CreateAsync(request, ct);
    await emailService.SendOrderConfirmationAsync(order.Id, ct);

    return Results.Created($"/api/orders/{order.Id}", order);
});
```

## 响应模式

```csharp
// 类型化响应
public record ProductResponse(
    int Id,
    string Name,
    string Description,
    decimal Price,
    string CategoryName
);

// Results.Ok 带类型化响应
app.MapGet("/api/products/{id:int}", async (int id, IProductService service) =>
{
    var product = await service.GetByIdAsync(id);
    return product is not null
        ? Results.Ok(product)
        : Results.NotFound(new { Message = "Product not found" });
})
.Produces<ProductResponse>(StatusCodes.Status200OK)
.Produces(StatusCodes.Status404NotFound);

// 自定义结果类型
public class PagedResult<T>
{
    public required List<T> Items { get; init; }
    public required int TotalCount { get; init; }
    public required int Page { get; init; }
    public required int PageSize { get; init; }
}

app.MapGet("/api/products", async (
    [AsParameters] PaginationParams pagination,
    IProductService service) =>
{
    var result = await service.GetPagedAsync(
        pagination.Page,
        pagination.PageSize);
    return Results.Ok(result);
})
.Produces<PagedResult<ProductResponse>>();

public record PaginationParams(int Page = 1, int PageSize = 10);
```

## 错误处理

```csharp
// 全局异常处理器
app.UseExceptionHandler(exceptionHandlerApp =>
{
    exceptionHandlerApp.Run(async context =>
    {
        var exceptionHandlerFeature =
            context.Features.Get<IExceptionHandlerFeature>();
        var exception = exceptionHandlerFeature?.Error;

        var problemDetails = new ProblemDetails
        {
            Status = StatusCodes.Status500InternalServerError,
            Title = "An error occurred",
            Detail = exception?.Message
        };

        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        await context.Response.WriteAsJsonAsync(problemDetails);
    });
});

// 用于错误处理的自定义端点过滤器
public class ErrorHandlingFilter : IEndpointFilter
{
    private readonly ILogger<ErrorHandlingFilter> _logger;

    public ErrorHandlingFilter(ILogger<ErrorHandlingFilter> logger)
    {
        _logger = logger;
    }

    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext context,
        EndpointFilterDelegate next)
    {
        try
        {
            return await next(context);
        }
        catch (ValidationException ex)
        {
            _logger.LogWarning(ex, "Validation failed");
            return Results.ValidationProblem(ex.Errors.ToDictionary(
                e => e.PropertyName,
                e => new[] { e.ErrorMessage }
            ));
        }
        catch (NotFoundException ex)
        {
            _logger.LogWarning(ex, "Resource not found");
            return Results.NotFound(new { Message = ex.Message });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unhandled exception");
            return Results.Problem("An unexpected error occurred");
        }
    }
}
```

## 快速参考

| 模式 | 用途 |
|---------|-------|
| `Results.Ok(data)` | 200 带响应体 |
| `Results.Created(uri, data)` | 201 带位置头 |
| `Results.NoContent()` | 204 无响应体 |
| `Results.BadRequest()` | 400 验证错误 |
| `Results.NotFound()` | 404 资源未找到 |
| `Results.Unauthorized()` | 401 需要身份验证 |
| `Results.Forbid()` | 403 授权失败 |
| `app.MapGroup()` | 分组相关端点 |
| `.WithTags()` | OpenAPI 标签分组 |
| `.Produces<T>()` | 记录响应类型 |
