# Python 打包与项目配置

## 项目结构

```
myproject/
├── pyproject.toml          # 项目元数据与依赖
├── README.md               # 项目描述
├── .gitignore             # Git 忽略规则
├── .python-version        # pyenv 使用的 Python 版本
├── src/
│   └── myproject/
│       ├── __init__.py    # 包初始化
│       ├── py.typed       # PEP 561 类型标记
│       ├── core.py        # 核心功能
│       └── utils.py       # 工具函数
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Pytest 配置
│   └── test_core.py       # 测试
└── docs/
    └── index.md           # 文档
```

## Pyproject.toml 配置

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myproject"
version = "0.1.0"
description = "A Python project"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["python", "package"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]

dependencies = [
    "requests>=2.31.0",
    "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.7.0",
    "black>=23.11.0",
    "ruff>=0.1.6",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.4.0",
]

[project.scripts]
myproject = "myproject.cli:main"

[project.urls]
Homepage = "https://github.com/username/myproject"
Documentation = "https://myproject.readthedocs.io"
Repository = "https://github.com/username/myproject"
Changelog = "https://github.com/username/myproject/blob/main/CHANGELOG.md"

# Tool configurations
[tool.black]
line-length = 100
target-version = ["py311"]
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = []

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # Ignore unused imports in __init__.py

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "third_party.*"
ignore_missing_imports = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov=myproject",
    "--cov-report=term-missing",
    "--cov-report=html",
]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Poetry 项目管理

```toml
# pyproject.toml for Poetry
[tool.poetry]
name = "myproject"
version = "0.1.0"
description = "A Python project"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
license = "MIT"
packages = [{include = "myproject", from = "src"}]

[tool.poetry.dependencies]
python = "^3.11"
requests = "^2.31.0"
pydantic = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
mypy = "^1.7.0"
black = "^23.11.0"
ruff = "^0.1.6"

[tool.poetry.scripts]
myproject = "myproject.cli:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

```bash
# Poetry commands
poetry init                    # Initialize new project
poetry add requests            # Add dependency
poetry add --group dev pytest  # Add dev dependency
poetry install                 # Install dependencies
poetry update                  # Update dependencies
poetry shell                   # Activate virtual environment
poetry run pytest              # Run command in venv
poetry build                   # Build package
poetry publish                 # Publish to PyPI
poetry export -f requirements.txt --output requirements.txt
```

## 虚拟环境

```bash
# Using venv (built-in)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install in editable mode
pip install -e .
pip install -e ".[dev]"    # With optional dependencies

# Using virtualenv
pip install virtualenv
virtualenv venv
source venv/bin/activate

# Using pyenv for Python version management
pyenv install 3.11.6
pyenv local 3.11.6         # Set for current directory
echo "3.11.6" > .python-version
```

## 包的 __init__.py

```python
# src/myproject/__init__.py
"""MyProject - A Python package."""

from myproject.core import main_function, CoreClass
from myproject.utils import helper_function

__version__ = "0.1.0"
__all__ = ["main_function", "CoreClass", "helper_function"]

# Package-level configuration
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
```

## 类型存根文件（py.typed）

```python
# src/myproject/py.typed
# Empty file indicates package includes type hints

# src/myproject/__init__.pyi (optional stub file)
from typing import Any

__version__: str

def main_function(arg: str) -> dict[str, Any]: ...

class CoreClass:
    def __init__(self, name: str) -> None: ...
    def process(self) -> str: ...
```

## CLI 入口点

```python
# src/myproject/cli.py
import sys
from typing import NoReturn

def main() -> NoReturn:
    """Main CLI entry point."""
    print("MyProject CLI")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

## 依赖文件

```bash
# requirements.txt - 生产依赖
requests>=2.31.0,<3.0.0
pydantic>=2.5.0,<3.0.0

# requirements-dev.txt - 开发依赖
-r requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
mypy>=1.7.0
black>=23.11.0
ruff>=0.1.6

# 从 Poetry 生成
poetry export -f requirements.txt --output requirements.txt --without-hashes
poetry export -f requirements.txt --with dev --output requirements-dev.txt
```

## 构建与分发

```bash
# 构建包
python -m build

# 检查包
twine check dist/*

# 上传到 PyPI
twine upload dist/*

# 上传到 Test PyPI
twine upload --repository testpypi dist/*

# 从 Test PyPI 安装
pip install --index-url https://test.pypi.org/simple/ myproject
```

## Setuptools 配置（旧版）

```python
# setup.py (if not using pyproject.toml)
from setuptools import setup, find_packages

setup(
    name="myproject",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.31.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "myproject=myproject.cli:main",
        ],
    },
)
```

## 包数据的清单文件

```
# MANIFEST.in
include README.md
include LICENSE
include pyproject.toml
recursive-include src/myproject *.py
recursive-include src/myproject py.typed
recursive-include tests *.py
prune docs/_build
```

## 版本管理

```python
# src/myproject/__version__.py
__version__ = "0.1.0"

# src/myproject/__init__.py
from myproject.__version__ import __version__

# 在 pyproject.toml 中读取版本
import tomli
from pathlib import Path

def get_version() -> str:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomli.load(f)
    return data["project"]["version"]
```

## 依赖管理最佳实践

```python
# 应用程序应锁定依赖版本
requests==2.31.0
pydantic==2.5.2

# 库应使用版本范围
requests>=2.31.0,<3.0.0
pydantic>=2.5.0,<3.0.0

# 锁定文件
# Poetry: poetry.lock
# pip: requirements.txt 指定精确版本
pip freeze > requirements-lock.txt

# 更新依赖
poetry update
pip install --upgrade -r requirements.txt
```

## CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run tests
      run: |
        pytest --cov --cov-report=xml

    - name: Type check
      run: mypy src

    - name: Lint
      run: |
        black --check src tests
        ruff check src tests

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Pre-commit 钩子

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

```bash
# 安装 pre-commit
pip install pre-commit
pre-commit install

# 手动运行
pre-commit run --all-files
```
