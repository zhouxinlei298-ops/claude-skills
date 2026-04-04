---
name: spring-boot-engineer
description: Generates Spring Boot 3.x configurations, creates REST controllers, implements Spring Security 6 authentication flows, sets up Spring Data JPA repositories, and configures reactive WebFlux endpoints. Use when building Spring Boot 3.x applications, microservices, or reactive Java applications; invoke for Spring Data JPA, Spring Security 6, WebFlux, Spring Cloud integration, Java REST API design, or Microservices Java architecture.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: backend
  triggers: Spring Boot, Spring Framework, Spring Cloud, Spring Security, Spring Data JPA, Spring WebFlux, Microservices Java, Java REST API, Reactive Java
  role: specialist
  scope: implementation
  output-format: code
  related-skills: java-architect, database-optimizer, microservices-architect, devops-engineer
---

# Spring Boot 工程师

## 核心工作流程

1. **分析需求** — 识别服务边界、API、数据模型、安全需求
2. **设计架构** — 规划微服务、数据访问、云集成、安全；编码前确认设计方案
3. **实现** — 使用构造器注入和分层架构创建服务（参见下文快速入门）
4. **安全** — 添加 Spring Security、OAuth2、方法级安全、CORS 配置；验证安全规则编译通过且测试通过。如果编译或测试失败：审查错误输出，修复失败的规则或配置，重新运行后再继续
5. **测试** — 编写单元测试、集成测试和切片测试；运行 `./mvnw test`（或 `./gradlew test`）并确认全部通过后再继续。如果测试失败：查看堆栈跟踪，定位失败的断言或组件，修复问题，重新运行完整测试套件
6. **部署** — 通过 Actuator 配置健康检查和可观测性；验证 `/actuator/health` 返回 `UP`。如果状态为 `DOWN`：检查响应中的 `components` 详情，解决故障组件（如数据源、消息代理），然后重新验证

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考文件 | 加载时机 |
|------|----------|----------|
| Web 层 | `references/web.md` | 控制器、REST API、验证、异常处理 |
| 数据访问 | `references/data.md` | Spring Data JPA、仓储、事务、投影 |
| 安全 | `references/security.md` | Spring Security 6、OAuth2、JWT、方法级安全 |
| 云原生 | `references/cloud.md` | Spring Cloud、Config、Discovery、Gateway、弹性 |
| 测试 | `references/testing.md` | @SpringBootTest、MockMvc、Testcontainers、测试切片 |

## 快速入门 — 最小可运行结构

一个标准的 Spring Boot 功能由以下层组成。可以将它们作为复制粘贴的起点。

### 实体

```java
@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotBlank
    private String name;

    @DecimalMin("0.0")
    private BigDecimal price;

    // getters / setters or use @Data (Lombok)
}
```

### 仓储

```java
public interface ProductRepository extends JpaRepository<Product, Long> {
    List<Product> findByNameContainingIgnoreCase(String name);
}
```

### 服务（构造器注入）

```java
@Service
public class ProductService {
    private final ProductRepository repo;

    public ProductService(ProductRepository repo) { // constructor injection — no @Autowired
        this.repo = repo;
    }

    @Transactional(readOnly = true)
    public List<Product> search(String name) {
        return repo.findByNameContainingIgnoreCase(name);
    }

    @Transactional
    public Product create(ProductRequest request) {
        var product = new Product();
        product.setName(request.name());
        product.setPrice(request.price());
        return repo.save(product);
    }
}
```

### REST 控制器

```java
@RestController
@RequestMapping("/api/v1/products")
@Validated
public class ProductController {
    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<Product> search(@RequestParam(defaultValue = "") String name) {
        return service.search(name);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Product create(@Valid @RequestBody ProductRequest request) {
        return service.create(request);
    }
}
```

### DTO（record）

```java
public record ProductRequest(
    @NotBlank String name,
    @DecimalMin("0.0") BigDecimal price
) {}
```

### 全局异常处理器

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, String> handleValidation(MethodArgumentNotValidException ex) {
        return ex.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage));
    }

    @ExceptionHandler(EntityNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public Map<String, String> handleNotFound(EntityNotFoundException ex) {
        return Map.of("error", ex.getMessage());
    }
}
```

### 测试切片

```java
@WebMvcTest(ProductController.class)
class ProductControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean ProductService service;

    @Test
    void createProduct_validRequest_returns201() throws Exception {
        var product = new Product(); product.setName("Widget"); product.setPrice(BigDecimal.TEN);
        when(service.create(any())).thenReturn(product);

        mockMvc.perform(post("/api/v1/products")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""{"name":"Widget","price":10.0}"""))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("Widget"));
    }
}
```

## 约束

### 必须做

| 规则 | 正确模式 |
|------|----------|
| 构造器注入 | `public MyService(Dep dep) { this.dep = dep; }` |
| 验证 API 输入 | 在每个修改型端点上使用 `@Valid @RequestBody MyRequest req` |
| 类型安全的配置 | `@ConfigurationProperties(prefix = "app")` 绑定到 record 或类 |
| 合适的构造型注解 | 业务逻辑用 `@Service`，数据访问用 `@Repository`，HTTP 用 `@RestController` |
| 事务范围 | 多步写操作使用 `@Transactional`；读操作使用 `@Transactional(readOnly = true)` |
| 隐藏内部细节 | 在 `@RestControllerAdvice` 中捕获领域异常；返回问题详情，而非堆栈跟踪 |
| 外部化密钥 | 使用环境变量或 Spring Cloud Config — 绝不放在 `application.properties` 中 |

### 不能做
- 使用字段注入（在字段上使用 `@Autowired`）
- 跳过 API 端点的输入验证
- 当 `@Service`/`@Repository`/`@Controller` 适用时使用 `@Component`
- 混合阻塞式和响应式代码（例如在 WebFlux 链中调用 `.block()`）
- 在 `application.properties`/`application.yml` 中存储密钥或凭据
- 硬编码 URL、凭据或环境特定的值
- 使用已弃用的 Spring Boot 2.x 模式（例如 `WebSecurityConfigurerAdapter`）
