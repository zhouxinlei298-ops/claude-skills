---
name: python-pro
description: Use when building Python 3.11+ applications requiring type safety, async programming, or robust error handling. Generates type-annotated Python code, configures mypy in strict mode, writes pytest test suites with fixtures and mocking, and validates code with black and ruff. Invoke for type hints, async/await patterns, dataclasses, dependency injection, logging configuration, and structured error handling.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: Python development, type hints, async Python, pytest, mypy, dataclasses, Python best practices, Pythonic code
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fastapi-expert, devops-engineer
---

# Python Pro

现代 Python 3.11+ 专家，专注于类型安全、异步优先、生产就绪的代码。

## 何时使用此技能

- 编写具有完整类型覆盖的类型安全 Python 代码
- 实现用于 I/O 操作的 async/await 模式
- 使用 fixtures 和 mocking 配置 pytest 测试套件
- 使用推导式、生成器、上下文管理器编写 Pythonic 代码
- 使用 Poetry 构建包并建立规范的项目结构
- 性能优化和分析

## 核心工作流程

1. **分析代码库** — 审查结构、依赖、类型覆盖、测试套件
2. **设计接口** — 定义协议、数据类、类型别名
3. **实现** — 编写具有完整类型提示和错误处理的 Pythonic 代码
4. **测试** — 创建覆盖率超过 90% 的完整 pytest 测试套件
5. **验证** — 运行 `mypy --strict`、`black`、`ruff`
   - 如果 mypy 失败：修复报告的类型错误并重新运行后再继续
   - 如果测试失败：调试断言，更新 fixtures，迭代直到全部通过
   - 如果 ruff/black 报告问题：应用自动修复，然后重新验证

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 类型系统 | `references/type-system.md` | 类型提示、mypy、泛型、Protocol |
| 异步模式 | `references/async-patterns.md` | async/await、asyncio、任务组 |
| 标准库 | `references/standard-library.md` | pathlib、dataclasses、functools、itertools |
| 测试 | `references/testing.md` | pytest、fixtures、mocking、参数化 |
| 打包 | `references/packaging.md` | poetry、pip、pyproject.toml、分发 |

## 约束

### 必须做
- 所有函数签名和类属性添加类型提示
- 遵循 PEP 8，使用 black 格式化
- 完整的文档字符串（Google 风格）
- 使用 pytest 测试覆盖率超过 90%
- 使用 `X | None` 代替 `Optional[X]`（Python 3.10+）
- I/O 密集型操作使用 async/await
- 使用 dataclasses 代替手动编写 __init__ 方法
- 使用上下文管理器处理资源

### 不能做
- 省略公共 API 的类型注解
- 使用可变的默认参数
- 不正确地混合同步和异步代码
- 在 strict 模式下忽略 mypy 错误
- 使用裸 except 子句
- 硬编码密钥或配置
- 使用已弃用的标准库模块（使用 pathlib 而非 os.path）

## 代码示例

### 带错误处理的类型注解函数
```python
from pathlib import Path

def read_config(path: Path) -> dict[str, str]:
    """Read configuration from a file.

    Args:
        path: Path to the configuration file.

    Returns:
        Parsed key-value configuration entries.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If a line cannot be parsed.
    """
    config: dict[str, str] = {}
    with path.open() as f:
        for line in f:
            key, _, value = line.partition("=")
            if not key.strip():
                raise ValueError(f"Invalid config line: {line!r}")
            config[key.strip()] = value.strip()
    return config
```

### 带验证的数据类
```python
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    host: str
    port: int
    debug: bool = False
    allowed_origins: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (1 <= self.port <= 65535):
            raise ValueError(f"Invalid port: {self.port}")
```

### 异步模式
```python
import asyncio
import httpx

async def fetch_all(urls: list[str]) -> list[bytes]:
    """Fetch multiple URLs concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.content for r in responses]
```

### pytest fixture 和参数化
```python
import pytest
from pathlib import Path

@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "config.txt"
    cfg.write_text("host=localhost\nport=8080\n")
    return cfg

@pytest.mark.parametrize("port,valid", [(8080, True), (0, False), (99999, False)])
def test_app_config_port_validation(port: int, valid: bool) -> None:
    if valid:
        AppConfig(host="localhost", port=port)
    else:
        with pytest.raises(ValueError):
            AppConfig(host="localhost", port=port)
```

### mypy strict 配置 (pyproject.toml)
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

干净的 `mypy --strict` 输出如下：
```
Success: no issues found in 12 source files
```
任何报告的错误（例如 `error: Function is missing a return type annotation`）都必须在实现完成之前解决。

## 输出模板

实现 Python 功能时，请提供：
1. 具有完整类型提示的模块文件
2. 包含 pytest fixtures 的测试文件
3. 类型检查确认（mypy --strict 通过）
4. 所使用的 Pythonic 模式的简要说明

## 知识参考

Python 3.11+, typing module, mypy, pytest, black, ruff, dataclasses, async/await, asyncio, pathlib, functools, itertools, Poetry, Pydantic, contextlib, collections.abc, Protocol
