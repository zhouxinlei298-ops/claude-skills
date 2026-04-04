# Entity Framework Core

## DbContext 配置

```csharp
using Microsoft.EntityFrameworkCore;
using Domain.Entities;

namespace Infrastructure.Persistence;

public class ApplicationDbContext : DbContext
{
    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(ApplicationDbContext).Assembly);
    }
}
```

## 实体配置

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using Domain.Entities;

namespace Infrastructure.Persistence.Configurations;

public class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        builder.ToTable("Products");

        builder.HasKey(p => p.Id);

        builder.Property(p => p.Name)
            .IsRequired()
            .HasMaxLength(100);

        builder.Property(p => p.Description)
            .HasMaxLength(500);

        builder.Property(p => p.Price)
            .HasPrecision(18, 2);

        builder.Property(p => p.CreatedAt)
            .IsRequired();

        builder.HasOne(p => p.Category)
            .WithMany(c => c.Products)
            .HasForeignKey(p => p.CategoryId)
            .OnDelete(DeleteBehavior.Restrict);

        builder.HasIndex(p => p.Name);
        builder.HasIndex(p => p.CategoryId);
    }
}

public class CategoryConfiguration : IEntityTypeConfiguration<Category>
{
    public void Configure(EntityTypeBuilder<Category> builder)
    {
        builder.ToTable("Categories");

        builder.HasKey(c => c.Id);

        builder.Property(c => c.Name)
            .IsRequired()
            .HasMaxLength(50);

        builder.HasMany(c => c.Products)
            .WithOne(p => p.Category)
            .HasForeignKey(p => p.CategoryId);

        builder.HasData(
            new Category { Id = 1, Name = "Electronics" },
            new Category { Id = 2, Name = "Books" },
            new Category { Id = 3, Name = "Clothing" }
        );
    }
}
```

## 复杂关系

```csharp
// 带负载的 Many-to-Many
public class OrderItemConfiguration : IEntityTypeConfiguration<OrderItem>
{
    public void Configure(EntityTypeBuilder<OrderItem> builder)
    {
        builder.ToTable("OrderItems");

        builder.HasKey(oi => new { oi.OrderId, oi.ProductId });

        builder.Property(oi => oi.Quantity)
            .IsRequired();

        builder.Property(oi => oi.UnitPrice)
            .HasPrecision(18, 2);

        builder.HasOne(oi => oi.Order)
            .WithMany(o => o.OrderItems)
            .HasForeignKey(oi => oi.OrderId);

        builder.HasOne(oi => oi.Product)
            .WithMany()
            .HasForeignKey(oi => oi.ProductId);
    }
}

// One-to-One
public class UserProfileConfiguration : IEntityTypeConfiguration<UserProfile>
{
    public void Configure(EntityTypeBuilder<UserProfile> builder)
    {
        builder.ToTable("UserProfiles");

        builder.HasKey(up => up.Id);

        builder.HasOne(up => up.User)
            .WithOne(u => u.Profile)
            .HasForeignKey<UserProfile>(up => up.UserId)
            .OnDelete(DeleteBehavior.Cascade);

        builder.OwnsOne(up => up.Address, address =>
        {
            address.Property(a => a.Street).HasMaxLength(200);
            address.Property(a => a.City).HasMaxLength(100);
            address.Property(a => a.Country).HasMaxLength(100);
        });
    }
}
```

## 查询模式

```csharp
// 带过滤的异步查询
public async Task<List<Product>> GetProductsByCategoryAsync(
    int categoryId,
    CancellationToken cancellationToken = default)
{
    return await _context.Products
        .AsNoTracking()
        .Include(p => p.Category)
        .Where(p => p.CategoryId == categoryId)
        .OrderBy(p => p.Name)
        .ToListAsync(cancellationToken);
}

// 分页
public async Task<PagedResult<Product>> GetPagedProductsAsync(
    int page,
    int pageSize,
    CancellationToken cancellationToken = default)
{
    var query = _context.Products
        .AsNoTracking()
        .Include(p => p.Category);

    var totalCount = await query.CountAsync(cancellationToken);

    var items = await query
        .Skip((page - 1) * pageSize)
        .Take(pageSize)
        .ToListAsync(cancellationToken);

    return new PagedResult<Product>(items, totalCount, page, pageSize);
}

// 带 Select 的投影
public async Task<List<ProductDto>> GetProductDtosAsync(
    CancellationToken cancellationToken = default)
{
    return await _context.Products
        .AsNoTracking()
        .Select(p => new ProductDto(
            p.Id,
            p.Name,
            p.Description,
            p.Price,
            p.Category.Name
        ))
        .ToListAsync(cancellationToken);
}

// 带规范模式的复杂过滤
public async Task<List<Product>> GetProductsBySpecificationAsync(
    Expression<Func<Product, bool>> predicate,
    CancellationToken cancellationToken = default)
{
    return await _context.Products
        .AsNoTracking()
        .Where(predicate)
        .ToListAsync(cancellationToken);
}

// 聚合查询
public async Task<decimal> GetTotalRevenueAsync(
    int year,
    CancellationToken cancellationToken = default)
{
    return await _context.Orders
        .AsNoTracking()
        .Where(o => o.CreatedAt.Year == year && o.Status == OrderStatus.Completed)
        .SelectMany(o => o.OrderItems)
        .SumAsync(oi => oi.Quantity * oi.UnitPrice, cancellationToken);
}
```

## CRUD 操作

```csharp
public class ProductRepository : IProductRepository
{
    private readonly ApplicationDbContext _context;

    public ProductRepository(ApplicationDbContext context)
    {
        _context = context;
    }

    public async Task<Product?> GetByIdAsync(
        int id,
        CancellationToken cancellationToken = default)
    {
        return await _context.Products
            .Include(p => p.Category)
            .FirstOrDefaultAsync(p => p.Id == id, cancellationToken);
    }

    public async Task<List<Product>> GetAllAsync(
        CancellationToken cancellationToken = default)
    {
        return await _context.Products
            .AsNoTracking()
            .Include(p => p.Category)
            .ToListAsync(cancellationToken);
    }

    public async Task<Product> AddAsync(
        Product product,
        CancellationToken cancellationToken = default)
    {
        _context.Products.Add(product);
        await _context.SaveChangesAsync(cancellationToken);
        return product;
    }

    public async Task UpdateAsync(
        Product product,
        CancellationToken cancellationToken = default)
    {
        _context.Products.Update(product);
        await _context.SaveChangesAsync(cancellationToken);
    }

    public async Task DeleteAsync(
        int id,
        CancellationToken cancellationToken = default)
    {
        var product = await _context.Products.FindAsync(new object[] { id }, cancellationToken);
        if (product is not null)
        {
            _context.Products.Remove(product);
            await _context.SaveChangesAsync(cancellationToken);
        }
    }
}
```

## 迁移

```csharp
// 添加迁移（通过 CLI）
// dotnet ef migrations add InitialCreate --project Infrastructure --startup-project WebApi

// 迁移文件示例
public partial class InitialCreate : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.CreateTable(
            name: "Categories",
            columns: table => new
            {
                Id = table.Column<int>(nullable: false)
                    .Annotation("SqlServer:Identity", "1, 1"),
                Name = table.Column<string>(maxLength: 50, nullable: false)
            },
            constraints: table =>
            {
                table.PrimaryKey("PK_Categories", x => x.Id);
            });

        migrationBuilder.InsertData(
            table: "Categories",
            columns: new[] { "Id", "Name" },
            values: new object[,]
            {
                { 1, "Electronics" },
                { 2, "Books" },
                { 3, "Clothing" }
            });
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropTable(name: "Categories");
    }
}

// 在启动时应用迁移
public static async Task Main(string[] args)
{
    var host = CreateHostBuilder(args).Build();

    using (var scope = host.Services.CreateScope())
    {
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        await context.Database.MigrateAsync();
    }

    await host.RunAsync();
}
```

## 性能优化

```csharp
// 编译查询用于频繁使用的查询
private static readonly Func<ApplicationDbContext, int, Task<Product?>> _getProductById =
    EF.CompileAsyncQuery((ApplicationDbContext context, int id) =>
        context.Products
            .Include(p => p.Category)
            .FirstOrDefault(p => p.Id == id));

public async Task<Product?> GetByIdOptimizedAsync(int id)
{
    return await _getProductById(_context, id);
}

// 分割查询用于复杂的 Include
public async Task<List<Order>> GetOrdersWithItemsAsync(
    CancellationToken cancellationToken = default)
{
    return await _context.Orders
        .Include(o => o.OrderItems)
            .ThenInclude(oi => oi.Product)
        .AsSplitQuery()
        .ToListAsync(cancellationToken);
}

// 批量操作
public async Task AddRangeAsync(
    List<Product> products,
    CancellationToken cancellationToken = default)
{
    await _context.Products.AddRangeAsync(products, cancellationToken);
    await _context.SaveChangesAsync(cancellationToken);
}

// 复杂查询的原始 SQL
public async Task<List<ProductSalesReport>> GetProductSalesReportAsync(
    int year,
    CancellationToken cancellationToken = default)
{
    return await _context.Database
        .SqlQuery<ProductSalesReport>(
            $@"SELECT p.Id, p.Name, SUM(oi.Quantity) as TotalSold, SUM(oi.Quantity * oi.UnitPrice) as Revenue
               FROM Products p
               INNER JOIN OrderItems oi ON p.Id = oi.ProductId
               INNER JOIN Orders o ON oi.OrderId = o.Id
               WHERE YEAR(o.CreatedAt) = {year}
               GROUP BY p.Id, p.Name
               ORDER BY Revenue DESC")
        .ToListAsync(cancellationToken);
}
```

## 依赖注入

```csharp
// Infrastructure/DependencyInjection.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("DefaultConnection"),
                b => b.MigrationsAssembly(typeof(ApplicationDbContext).Assembly.FullName)));

        services.AddScoped<IApplicationDbContext>(provider =>
            provider.GetRequiredService<ApplicationDbContext>());

        services.AddScoped<IProductRepository, ProductRepository>();

        return services;
    }
}
```

## 快速参考

| 模式 | 用途 |
|---------|-------|
| `AsNoTracking()` | 只读查询以获得更好的性能 |
| `Include()` | 预先加载相关实体 |
| `ThenInclude()` | 加载嵌套关系 |
| `AsSplitQuery()` | 防止笛卡尔爆炸 |
| `FirstOrDefaultAsync()` | 获取单个或 null |
| `ToListAsync()` | 执行查询并获取列表 |
| `AddAsync()` | 添加实体到上下文 |
| `Update()` | 将实体标记为已修改 |
| `Remove()` | 将实体标记为删除 |
| `SaveChangesAsync()` | 将更改持久化到数据库 |
