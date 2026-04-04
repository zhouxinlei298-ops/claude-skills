# 调试工具

## 按语言分类的调试器

| 语言 | 调试器 | 启动命令 |
|------|--------|----------|
| TypeScript/JS | Node Inspector | `node --inspect` |
| Python | pdb/ipdb | `python -m pdb` |
| Go | Delve | `dlv debug` |
| Rust | rust-gdb/lldb | `rust-gdb ./target/debug/app` |
| Java | JDB/IDE | IDE 调试器 |

## Node.js / TypeScript

```bash
# Start with inspector
node --inspect dist/main.js

# Break on first line
node --inspect-brk dist/main.js

# With ts-node
node --inspect -r ts-node/register src/main.ts
```

```typescript
// In code
debugger; // Breakpoint

// Quick print
console.log({ variable }); // Shows name and value
console.table(arrayOfObjects); // Table format
console.trace('Called from'); // Stack trace
```

## Python

```bash
# Start debugger
python -m pdb script.py

# Post-mortem on exception
python -m pdb -c continue script.py
```

```python
# In code
breakpoint()  # Python 3.7+
import pdb; pdb.set_trace()  # Older Python

# Quick print
print(f"{variable=}")  # Python 3.8+ shows name and value

# Rich debugging
from rich import inspect
inspect(object, methods=True)
```

### pdb 命令

| 命令 | 操作 |
|------|------|
| `n` | 下一行 |
| `s` | 进入 |
| `c` | 继续 |
| `l` | 列出代码 |
| `p expr` | 打印表达式 |
| `pp expr` | 美化打印 |
| `w` | 显示位置（堆栈） |
| `q` | 退出 |

## Go

```bash
# Start delve
dlv debug ./cmd/app

# Attach to running process
dlv attach <pid>

# Debug test
dlv test ./pkg/...
```

```go
// Quick print
log.Printf("%+v", variable) // With field names
fmt.Printf("%#v\n", variable) // Go syntax representation

// Spew for complex structures
import "github.com/davecgh/go-spew/spew"
spew.Dump(variable)
```

### Delve 命令

| 命令 | 操作 |
|------|------|
| `break main.go:42` | 设置断点 |
| `continue` | 继续 |
| `next` | 下一行 |
| `step` | 进入 |
| `print var` | 打印变量 |
| `goroutines` | 列出 goroutine |

## VS Code 调试配置

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug TypeScript",
      "program": "${workspaceFolder}/src/main.ts",
      "preLaunchTask": "tsc: build",
      "outFiles": ["${workspaceFolder}/dist/**/*.js"]
    },
    {
      "type": "python",
      "request": "launch",
      "name": "Debug Python",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal"
    }
  ]
}
```

## 快速参考

| 需求 | 工具 |
|------|------|
| 代码中设置断点 | `debugger;` / `breakpoint()` |
| 带名称打印 | `console.log({x})` / `print(f"{x=}")` |
| 堆栈跟踪 | `console.trace()` / `traceback.print_stack()` |
| 检查对象 | `console.dir(obj)` / `dir(obj)` |
| 单步执行 | IDE 调试器或 CLI 调试器 |