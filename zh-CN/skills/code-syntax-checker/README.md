# 代码语法检查技能

这是一个用于自动检查代码语法错误的 Claude Code 技能，支持多种编程语言的语法检查和编译验证。

## 功能特性

- 🌐 **多语言支持**: Python、JavaScript、TypeScript、Java、C/C++、Go、Rust、HTML、CSS、JSON
- 🚀 **快速检查**: 并发执行检查，提高效率
- 📊 **详细报告**: 清晰的检查结果报告
- 🔍 **精确定位**: 错误定位到具体行号
- 🛡️ **错误预防**: 在执行前发现语法错误

## 安装要求

确保系统中安装了相应的编译器/解释器：

- Python: `python` 或 `python3`
- JavaScript: `node`
- TypeScript: `tsc`
- Java: `javac`
- C/C++: `gcc` 或 `clang`
- Go: `go`
- Rust: `rustc`
- 可选工具: `flake8`, `eslint`, `prettier`（用于更详细的检查）

## 使用方法

### 1. 直接使用 CLI 工具

```bash
# 检查单个文件
python check_syntax.py script.py

# 检查目录（递归）
python check_syntax.py --dir src/

# 检查多个文件
python check_syntax.py file1.py file2.js file3.java

# 输出 JSON 格式
python check_syntax.py --json file.py
```

### 2. 在 Claude Code 中使用

当您提到以下关键词时，会自动触发此技能：

- "代码检查"
- "语法检查" 
- "编译检查"
- "verify code"
- "check syntax"
- "compile check"

### 3. 示例场景

#### 检查 Python 代码
```
用户: 检查这段代码的语法
def hello(
    print("Hello")
```

#### 检查 JavaScript 代码
```
用户: 验证这段 JavaScript 代码
function test() {
    console.log("Test"
}
```

#### 检查整个项目
```
用户: 检查项目的所有代码文件
```

## 支持的语言

### Python (.py)
- 使用 `python -m py_compile` 进行编译检查
- 使用 `ast` 模块进行语法树解析
- 可选使用 `flake8` 进行代码风格检查

### JavaScript (.js)
- 使用 `node -c` 进行语法检查
- 可选使用 `eslint` 进行详细检查

### TypeScript (.ts)
- 使用 `tsc --noEmit` 进行编译检查

### Java (.java)
- 使用 `javac` 进行编译检查

### C/C++ (.c, .cpp, .h, .hpp)
- 使用 `gcc -fsyntax-only` 或 `clang -fsyntax-only`
- 支持 C11 和 C++11 标准

### Go (.go)
- 使用 `go build -o /dev/null` 进行编译检查

### Rust (.rs)
- 使用 `rustc --check` 进行编译检查

### HTML (.html)
- 基本标签闭合检查
- 可扩展使用 html5validator

### CSS (.css)
- 基本花括号匹配检查
- 可扩展使用 csslint/stylelint

### JSON (.json)
- 使用 `json` 模块进行验证

## 配置选项

### 创建 `.syntax-checker-config.json`

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

创建 `.syntax-ignore` 文件：

```
*.tmp
*.log
node_modules/
venv/
__pycache__/
*.pyc
```

## 输出格式

### 文本格式
```
============================================================
代码语法检查报告
============================================================
总文件数: 5
通过: 4 ✅
失败: 1 ❌
错误: 2 🔴
警告: 3 🟡
============================================================

📄 script.py (python)
❌ 错误:
   行 3: SyntaxError: invalid syntax
```

### JSON 格式
```json
{
    "file": "script.py",
    "language": "python",
    "success": false,
    "errors": [
        {
            "line": 3,
            "column": 10,
            "message": "SyntaxError: invalid syntax",
            "code": "E901"
        }
    ],
    "warnings": []
}
```

## 集成建议

### 1. 编辑器集成
- 将语法检查集成到编辑器中
- 实时反馈语法错误

### 2. Git Hook
- 在 `pre-commit` 钩子中运行语法检查
- 确保提交的代码没有语法错误

### 3. CI/CD 集成
- 在 GitHub Actions 或其他 CI 工具中集成
- 作为构建流程的一部分

### 4. 定期检查
- 使用 cron 定期检查项目
- 自动生成检查报告

## 故障排除

### 常见问题

1. **编译器未找到**
   - 确保相关语言的编译器已安装
   - 添加到系统 PATH

2. **权限问题**
   - 确保文件有读取权限
   - 检查脚本执行权限

3. **编码问题**
   - 使用 UTF-8 编码保存文件
   - 指定编码格式：`--encoding utf-8`

### 调试模式
```bash
python check_syntax.py --verbose script.py
```

## 扩展功能

### 添加新语言支持
1. 在 `check_syntax.py` 中添加新的检查方法
2. 更新 `detect_language` 函数
3. 添加相应的测试用例

### 自定义检查规则
1. 修改 `SyntaxChecker` 类
2. 添加新的检查逻辑
3. 更新配置选项

## 许可证

MIT License - 自由使用和修改