---
name: code-documenter
description: Generates, formats, and validates technical documentation — including docstrings, OpenAPI/Swagger specs, JSDoc annotations, doc portals, and user guides. Use when adding docstrings to functions or classes, creating API documentation, building documentation sites, or writing tutorials and user guides. Invoke for OpenAPI/Swagger specs, JSDoc, doc portals, getting started guides.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: quality
  triggers: documentation, docstrings, OpenAPI, Swagger, JSDoc, comments, API docs, tutorials, user guides, doc site
  role: specialist
  scope: implementation
  output-format: code
  related-skills: spec-miner, fullstack-guardian, code-reviewer
---

# Code Documenter

文档专家，专注于内联文档、API 规范、文档站点和开发者指南。

## 何时使用此技能

适用于任何涉及代码文档、API 规范或面向开发者的指南的任务。有关具体子主题，请参见下方参考表。

## 核心工作流程

1. **发现** - 询问格式偏好和排除项
2. **检测** - 识别语言和框架
3. **分析** - 查找未文档化的代码
4. **文档化** - 应用一致的格式
5. **验证** - 测试所有代码示例是否能编译/运行：
   - Python：对 doctest 块使用 `python -m doctest file.py`；对模块级检查使用 `pytest --doctest-modules`
   - TypeScript/JavaScript：使用 `tsc --noEmit` 确认类型化示例能编译
   - OpenAPI：使用 `npx @redocly/cli lint openapi.yaml` 验证规范
   - 如果验证失败：修复示例并重新验证，然后再进入报告步骤
6. **报告** - 生成覆盖率摘要

## 快速参考示例

### Google 风格文档字符串（Python）
```python
def fetch_user(user_id: int, active_only: bool = True) -> dict:
    """Fetch a single user record by ID.

    Args:
        user_id: Unique identifier for the user.
        active_only: When True, raise an error for inactive users.

    Returns:
        A dict containing user fields (id, name, email, created_at).

    Raises:
        ValueError: If user_id is not a positive integer.
        UserNotFoundError: If no matching user exists.
    """
```

### NumPy 风格文档字符串（Python）
```python
def compute_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors.

    Parameters
    ----------
    vec_a : np.ndarray
        First input vector, shape (n,).
    vec_b : np.ndarray
        Second input vector, shape (n,).

    Returns
    -------
    float
        Cosine similarity in the range [-1, 1].

    Raises
    ------
    ValueError
        If vectors have different lengths.
    """
```

### JSDoc（TypeScript）
```typescript
/**
 * Fetches a paginated list of products from the catalog.
 *
 * @param {string} categoryId - The category to filter by.
 * @param {number} [page=1] - Page number (1-indexed).
 * @param {number} [limit=20] - Maximum items per page.
 * @returns {Promise<ProductPage>} Resolves to a page of product records.
 * @throws {NotFoundError} If the category does not exist.
 *
 * @example
 * const page = await fetchProducts('electronics', 2, 10);
 * console.log(page.items);
 */
async function fetchProducts(
  categoryId: string,
  page = 1,
  limit = 20
): Promise<ProductPage> { ... }
```

## 参考指南

根据上下文加载详细指南：

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| Python 文档字符串 | `references/python-docstrings.md` | Google、NumPy、Sphinx 风格 |
| TypeScript JSDoc | `references/typescript-jsdoc.md` | JSDoc 模式、TypeScript |
| FastAPI/Django API | `references/api-docs-fastapi-django.md` | Python API 文档 |
| NestJS/Express API | `references/api-docs-nestjs-express.md` | Node.js API 文档 |
| 覆盖率报告 | `references/coverage-reports.md` | 生成文档报告 |
| 文档系统 | `references/documentation-systems.md` | 文档站点、静态生成器、搜索、测试 |
| 交互式 API 文档 | `references/interactive-api-docs.md` | OpenAPI 3.1、门户、GraphQL、WebSocket、gRPC、SDK |
| 用户指南和教程 | `references/user-guides-tutorials.md` | 入门、教程、故障排除、FAQ |

## 约束

### 必须做
- 在开始前询问格式偏好
- 检测框架以确定正确的 API 文档策略
- 文档化所有公共函数/类
- 包含参数类型和描述
- 文档化异常/错误
- 测试文档中的代码示例
- 生成覆盖率报告

### 不能做
- 不询问就假设文档字符串格式
- 对框架使用错误的 API 文档策略
- 编写不准确或未经测试的文档
- 跳过错误文档化
- 冗长地文档化显而易见的 getter/setter
- 创建难以维护的文档

## 输出格式

根据任务，请提供：
1. **代码文档：** 已文档化的文件 + 覆盖率报告
2. **API 文档：** OpenAPI 规范 + 门户配置
3. **文档站点：** 站点配置 + 内容结构 + 构建说明
4. **指南/教程：** 带有示例和图表的结构化 Markdown

## 知识参考

Google/NumPy/Sphinx 文档字符串、JSDoc、OpenAPI 3.0/3.1、AsyncAPI、gRPC/protobuf、FastAPI、Django、NestJS、Express、GraphQL、Docusaurus、MkDocs、VitePress、Swagger UI、Redoc、Stoplight
