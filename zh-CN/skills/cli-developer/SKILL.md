---
name: cli-developer
description: Use when building CLI tools, implementing argument parsing, or adding interactive prompts. Invoke for parsing flags and subcommands, displaying progress bars and spinners, generating bash/zsh/fish completion scripts, CLI design, shell completions, and cross-platform terminal applications using commander, click, typer, or cobra.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: devops
  triggers: CLI, command-line, terminal app, argument parsing, shell completion, interactive prompt, progress bar, commander, click, typer, cobra
  role: specialist
  scope: implementation
  output-format: code
  related-skills: devops-engineer
---

# CLI Developer

## 核心工作流程

1. **分析用户体验** — 确定用户工作流程、命令层级、常见任务。在编写代码之前，通过列出所有命令及其预期的 `--help` 输出来验证。
2. **设计命令** — 规划子命令、标志、参数和配置。确认标志命名一致且没有破坏现有签名。
3. **实现** — 使用适合该语言的 CLI 框架构建（参见下方参考指南）。连接命令后，运行 `<cli> --help` 验证帮助文本正确渲染，运行 `<cli> --version` 确认版本输出。
4. **打磨** — 添加补全、帮助文本、错误消息和进度指示器。验证 TTY 检测用于彩色输出和优雅的 SIGINT 处理。
5. **测试** — 运行跨平台冒烟测试；基准测试启动时间（目标：<50ms）。

## 参考指南

根据上下文加载详细指南：

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| 设计模式 | `references/design-patterns.md` | 子命令、标志、配置、架构 |
| Node.js CLI | `references/node-cli.md` | commander、yargs、inquirer、chalk |
| Python CLI | `references/python-cli.md` | click、typer、argparse、rich |
| Go CLI | `references/go-cli.md` | cobra、viper、bubbletea |
| UX 模式 | `references/ux-patterns.md` | 进度条、颜色、帮助文本 |

## 快速入门示例

### Node.js（commander）

```js
#!/usr/bin/env node
// npm install commander
const { program } = require('commander');

program
  .name('mytool')
  .description('Example CLI')
  .version('1.0.0');

program
  .command('greet <name>')
  .description('Greet a user')
  .option('-l, --loud', 'uppercase the greeting')
  .action((name, opts) => {
    const msg = `Hello, ${name}!`;
    console.log(opts.loud ? msg.toUpperCase() : msg);
  });

program.parse();
```

关于 Python（click/typer）和 Go（cobra）的快速入门示例，请参见 `references/python-cli.md` 和 `references/go-cli.md`。

## 约束

### 必须做
- 保持启动时间在 50ms 以下
- 提供清晰、可操作的错误消息
- 支持 `--help` 和 `--version` 标志
- 使用一致的标志命名约定
- 优雅处理 SIGINT（Ctrl+C）
- 尽早验证用户输入
- 同时支持交互和非交互模式
- 在 Windows、macOS 和 Linux 上测试

### 不能做

- **不必要的同步 I/O 阻塞** — 使用异步读取或流处理替代。
- **输出将被管道时打印到 stdout** — 将日志/诊断信息写入 stderr。
- **输出不是 TTY 时使用颜色** — 应用颜色前检测：
  ```js
  // Node.js
  const useColor = process.stdout.isTTY;
  ```
  ```python
  # Python
  import sys
  use_color = sys.stdout.isatty()
  ```
  ```go
  // Go
  import "golang.org/x/term"
  useColor := term.IsTerminal(int(os.Stdout.Fd()))
  ```
- **破坏现有命令签名** — 将标志/子命令重命名视为破坏性变更。
- **在 CI/CD 环境中需要交互式输入** — 始终通过标志或环境变量提供非交互式回退。
- **硬编码路径或平台特定逻辑** — 使用 `os.homedir()` / `os.UserHomeDir()` / `Path.home()` 替代。
- **不提供 Shell 补全就发布** — 上述三个框架都有内置的补全生成功能。

## 输出模板

实现 CLI 功能时，请提供：
1. 命令结构（主入口点、子命令）
2. 配置处理（文件、环境变量、标志）
3. 带错误处理的核心实现
4. 如有需要的 Shell 补全脚本
5. UX 决策的简要说明

## 知识参考

CLI 框架（commander、yargs、oclif、click、typer、argparse、cobra、viper）、终端 UI（chalk、inquirer、rich、bubbletea）、测试（快照测试、E2E）、分发（npm、pip、homebrew、releases）、性能优化
