# CLI 设计模式

## 命令层次结构

```
mycli                           # Root command
├── init [options]              # Simple command
├── config
│   ├── get <key>              # Nested subcommand
│   ├── set <key> <value>
│   └── list
├── deploy [environment]        # Command with args
│   ├── --dry-run              # Flag
│   ├── --force
│   └── --config <file>        # Option with value
└── plugins
    ├── install <name>
    ├── list
    └── remove <name>
```

## 标志约定

```bash
# Boolean flags (presence = true)
mycli deploy --force --dry-run

# Short + long forms
mycli -v --verbose
mycli -c config.yml --config config.yml

# Required vs optional
mycli deploy <env>              # Positional (required)
mycli deploy --env production   # Flag (optional)

# Multiple values
mycli install pkg1 pkg2 pkg3    # Variadic args
mycli --exclude node_modules --exclude .git
```

## 配置层级

优先级顺序（从高到低）：

1. **命令行标志** - 明确的用户意图
2. **环境变量** - 运行时上下文
3. **配置文件（项目）** - `.myclirc`、`mycli.config.js`
4. **配置文件（用户）** - `~/.myclirc`、`~/.config/mycli/config.yml`
5. **配置文件（系统）** - `/etc/mycli/config.yml`
6. **默认值** - 硬编码的合理默认值

```javascript
// Example config resolution
const config = {
  ...systemDefaults,
  ...loadSystemConfig(),
  ...loadUserConfig(),
  ...loadProjectConfig(),
  ...loadEnvVars(),
  ...parseCliFlags(),
};
```

## 退出代码

标准 POSIX 退出代码：

```javascript
const EXIT_CODES = {
  SUCCESS: 0,
  GENERAL_ERROR: 1,
  MISUSE: 2,              // Invalid arguments
  PERMISSION_DENIED: 77,
  NOT_FOUND: 127,
  SIGINT: 130,            // Ctrl+C
};
```

## 插件架构

```
mycli/
├── core/                      # Core functionality
├── plugins/
│   ├── aws/                  # Plugin: AWS integration
│   │   ├── package.json
│   │   └── index.js
│   └── github/               # Plugin: GitHub integration
│       ├── package.json
│       └── index.js
└── plugin-loader.js          # Discovery & loading
```

插件发现：
1. 检查 `~/.mycli/plugins/`
2. 检查 `node_modules/mycli-plugin-*`
3. 检查 `MYCLI_PLUGIN_PATH` 环境变量

## 错误处理模式

```javascript
// Good: Actionable error messages
Error: Config file not found at /path/to/config.yml

Tried locations:
  • ./mycli.config.yml
  • ~/.myclirc
  • /etc/mycli/config.yml

Run 'mycli init' to create a config file, or use --config to specify location.

// Bad: Unhelpful errors
Error: ENOENT
```

## 交互式 vs 非交互式

```javascript
// Detect if running in CI/CD
const isCI = process.env.CI === 'true' || !process.stdout.isTTY;

if (isCI) {
  // Non-interactive: fail fast with clear errors
  if (!options.environment) {
    throw new Error('--environment required in non-interactive mode');
  }
} else {
  // Interactive: prompt user
  const environment = await prompt({
    type: 'select',
    message: 'Select environment:',
    choices: ['development', 'staging', 'production'],
  });
}
```

## 状态管理

```
~/.mycli/
├── config.yml           # User configuration
├── cache/               # Cached data
│   ├── plugins.json
│   └── api-responses/
├── credentials.json     # Sensitive data (600 perms)
└── state.json          # Session state
```

## 性能模式

```javascript
// Lazy loading: Don't load unused dependencies
if (command === 'deploy') {
  const deploy = require('./commands/deploy'); // Load on demand
  await deploy.run();
}

// Caching: Avoid repeated API calls
const cache = new Cache('~/.mycli/cache', { ttl: 3600 });
let plugins = await cache.get('plugins');
if (!plugins) {
  plugins = await fetchPlugins();
  await cache.set('plugins', plugins);
}

// Async operations: Don't block unnecessarily
await Promise.all([
  validateConfig(),
  checkForUpdates(),
  loadPlugins(),
]);
```

## 版本和更新

```javascript
// Check for updates (non-blocking)
checkForUpdates().then(update => {
  if (update.available) {
    console.log(`Update available: ${update.version}`);
    console.log(`Run: npm install -g mycli@latest`);
  }
}).catch(() => {
  // Silently fail - don't interrupt user workflow
});

// Version compatibility
const MIN_NODE_VERSION = '18.0.0';
if (!semver.satisfies(process.version, `>=${MIN_NODE_VERSION}`)) {
  console.error(`mycli requires Node.js ${MIN_NODE_VERSION} or higher`);
  process.exit(1);
}
```

## 帮助文本设计

```
USAGE
  mycli deploy [environment] [options]

ARGUMENTS
  environment  Target environment (development|staging|production)

OPTIONS
  -c, --config <file>  Path to config file
  -f, --force          Skip confirmation prompts
  -d, --dry-run        Preview changes without executing
  -v, --verbose        Show detailed output

EXAMPLES
  # Deploy to production
  mycli deploy production

  # Preview staging deployment
  mycli deploy staging --dry-run

  # Use custom config
  mycli deploy --config ./custom.yml

Learn more: https://docs.mycli.dev/deploy
```
