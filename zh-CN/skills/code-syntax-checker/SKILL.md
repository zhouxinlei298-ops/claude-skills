---
name: code-syntax-checker
description: 自动检查代码语法和编译验证，支持 Python、JavaScript、TypeScript、Java、C++、Go、Rust 等多种语言。【协作说明】按需被各技术Skill调用，提供语法检查服务，不直接响应最终用户。
tags: ["syntax", "code-check", "verification", "utility", "language-support"]
triggers: ["代码检查", "语法检查", "编译检查", "verify code", "check syntax", "compile check"]
priority: 5
---

# 代码自动语法检查技能

## 🎯 功能概述

本技能自动检查代码语法错误和编译验证，确保代码在执行前没有语法问题。支持多种主流编程语言，包括：

- Python (.py)
- JavaScript (.js)
- TypeScript (.ts)
- Java (.java)
- C++ (.cpp, .cc, .cxx, .h, .hpp)
- C (.c, .h)
- Go (.go)
- Rust (.rs)
- HTML (.html)
- CSS (.css)
- JSON (.json)

## 🔍 检查流程

### 1. 自动检测语言
```python
# 自动检测文件扩展名
file_ext = file_path.split('.')[-1]
language_map = {
    'py': 'python',
    'js': 'javascript', 
    'ts': 'typescript',
    'java': 'java',
    'cpp': 'cpp',
    'c': 'c',
    'go': 'go',
    'rs': 'rust',
    'html': 'html',
    'css': 'css',
    'json': 'json'
}
```

### 2. 语法检查命令

#### Python 语法检查
```bash
python -m py_compile <file>           # 编译检查
python -m ast <file>                   # AST 解析检查
python -m flake8 <file>               # 代码风格检查（需安装）
python -m black --check <file>        # 格式检查（需安装）
```

#### JavaScript 语法检查
```bash
node -c <file>                       # Node.js 语法检查
eslint <file>                        # ESLint 检查（需安装）
```

#### TypeScript 语法检查
```bash
tsc --noEmit <file>                  # TypeScript 编译检查
```

#### Java 语法检查
```bash
javac <file>                         # Java 编译检查
```

#### C/C++ 语法检查
```bash
gcc -fsyntax-only <file>            # GCC 语法检查
clang -fsyntax-only <file>           # Clang 语法检查
```

#### Go 语法检查
```bash
go build -o /dev/null <file>        # Go 编译检查
```

#### Rust 语法检查
```bash
rustc --check <file>                 # Rust 编译检查
```

#### HTML/CSS 检查
```bash
# HTML: 使用 linter 或浏览器验证
# CSS: 使用 csslint 或 stylelint
```

### 3. 自动修复建议
```python
# 自动修复格式问题
def auto_fix_format(code, language):
    if language == 'python':
        return autopep8.fix_code(code)
    elif language == 'javascript':
        return prettier.format(code)
    elif language == 'typescript':
        return prettier.format(code)
    # ... 更多语言的修复
```

## 📝 使用示例

### 示例 1: Python 代码检查
```python
# 要检查的代码
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 10)
print(f"结果: {result}")

# 检查命令
python -m py_compile script.py
```

### 示例 2: JavaScript 代码检查
```javascript
// 要检查的代码
function greet(name) {
    console.log(`Hello, ${name}!`);
    return "Hello, " + name;
}

greet("World");

// 检查命令
node -c script.js
```

### 示例 3: Java 代码检查
```java
// 要检查的代码
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}

// 检查命令
javac HelloWorld.java
```

## 🔧 配置选项

### 检查规则配置
```json
{
    "syntax_check": {
        "strict_mode": true,
        "max_errors": 10,
        "ignore_warnings": false,
        "auto_fix": false
    },
    "languages": {
        "python": {
            "checkers": ["py_compile", "ast", "flake8"],
            "fixers": ["autopep8", "black"]
        },
        "javascript": {
            "checkers": ["node", "eslint"],
            "fixers": ["prettier"]
        }
    }
}
```

### 排除文件
```ini
# .syntax-ignore
*.tmp
*.log
node_modules/
venv/
__pycache__/
*.pyc
```

## 🎯 集成到工作流

### 在代码编写后自动检查
```python
def write_and_check_code(code, filename):
    # 写入文件
    with open(filename, 'w') as f:
        f.write(code)
    
    # 执行语法检查
    result = check_syntax(filename)
    
    if result['success']:
        print("✅ 语法检查通过")
    else:
        print("❌ 语法错误:")
        for error in result['errors']:
            print(f"  - {error}")
    
    return result
```

### 持续集成集成
```yaml
# GitHub Actions 示例
name: Code Syntax Check
on: [push, pull_request]
jobs:
  syntax-check:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Check Python syntax
      run: |
        find . -name "*.py" -exec python -m py_compile {} \;
    - name: Check JavaScript syntax
      run: |
        find . -name "*.js" -exec node -c {} \;
```

## 📊 检查报告

### 详细报告格式
```json
{
    "file": "example.py",
    "language": "python",
    "status": "failed",
    "errors": [
        {
            "line": 5,
            "column": 10,
            "message": "SyntaxError: invalid syntax",
            "code": "E999"
        }
    ],
    "warnings": [],
    "fixes": []
}
```

### 简洁报告
```
📄 example.py (Python)
❌ 错误: 1
⚠️ 警告: 0
✅ 通过: 0
```

## 🚀 高级功能

### 批量检查
```bash
# 检查整个项目
check_syntax_project.py --all

# 检查特定目录
check_syntax_project.py --dir src/

# 检查特定文件
check_syntax_project.py --file main.py
```

### 自动修复
```bash
# 自动修复格式问题
check_syntax_project.py --fix

# 交互式修复
check_syntax_project.py --fix --interactive
```

### 集成开发环境
```python
# VSCode 插件集成
def check_syntax_in_vscode(file_path):
    result = check_syntax(file_path)
    if not result['success']:
        show_error_panel(result['errors'])
```

## 📋 最佳实践

1. **定期检查**: 每次代码提交前进行语法检查
2. **持续集成**: 将语法检查集成到 CI/CD 流程中
3. **团队统一**: 使用统一的代码检查规则
4. **自动修复**: 配置自动格式化工具
5. **错误分类**: 区分语法错误和代码质量问题

## 🔍 故障排除

### 常见问题
1. **编译器未找到**: 确保相关语言的编译器已安装
2. **路径问题**: 使用绝对路径或工作目录路径
3. **权限问题**: 确保文件有读取权限
4. **编码问题**: 使用 UTF-8 编码保存文件

### 调试模式
```bash
# 启用详细输出
check_syntax --verbose

# 显示详细错误信息
check_syntax --debug
```