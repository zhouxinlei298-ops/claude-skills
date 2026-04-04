---
name: javascript-pro
description: Writes, debugs, and refactors JavaScript code using modern ES2023+ features, async/await patterns, ESM module systems, and Node.js APIs. Use when building vanilla JavaScript applications, implementing Promise-based async flows, optimising browser or Node.js performance, working with Web Workers or Fetch API, or reviewing .js/.mjs/.cjs files for correctness and best practices.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: language
  triggers: JavaScript, ES2023, async await, Node.js, vanilla JavaScript, Web Workers, Fetch API, browser API, module system
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian
---

# JavaScript Pro

## 何时使用此技能

- 构建原生 JavaScript 应用程序
- 实现 async/await 模式和 Promise 处理
- 使用现代模块系统（ESM/CJS）
- 优化浏览器性能和内存使用
- 开发 Node.js 后端服务
- 实现 Web Workers、Service Workers 或浏览器 API

## 核心工作流程

1. **分析需求** — 审查 `package.json`、模块系统、Node 版本、浏览器目标；确认 `.js`/`.mjs`/`.cjs` 约定
2. **设计架构** — 规划模块、异步流程和错误处理策略
3. **实现** — 使用正确的模式和优化编写 ES2023+ 代码
4. **验证** — 运行代码检查器（`eslint --fix`）；如果检查器失败，修复所有报告的问题并重新运行后再继续。使用 DevTools 或 `--inspect` 检查内存泄漏，验证打包体积；如果发现泄漏，在继续之前解决它们
5. **测试** — 使用 Jest 编写全面的测试，覆盖率达到 85% 以上；如果覆盖率不足，添加缺失的测试用例并重新运行。确认没有未处理的 Promise 拒绝

## 参考指南

根据上下文加载详细指南：

| 主题 | 参考 | 加载时机 |
|-------|-----------|-----------|
| 现代语法 | `references/modern-syntax.md` | ES2023+ 特性、可选链、私有字段 |
| 异步模式 | `references/async-patterns.md` | Promise、async/await、错误处理、事件循环 |
| 模块 | `references/modules.md` | ESM 与 CJS、动态导入、package.json 导出 |
| 浏览器 API | `references/browser-apis.md` | Fetch、Web Workers、Storage、IntersectionObserver |
| Node 要点 | `references/node-essentials.md` | fs/promises、streams、EventEmitter、worker threads |

## 约束

### 必须做
- 专门使用 ES2023+ 特性
- 使用 `X | null` 或 `X | undefined` 模式
- 使用可选链（`?.`）和空值合并（`??`）
- 所有异步操作使用 async/await
- 新项目使用 ESM（`import`/`export`）
- 使用 try/catch 实现适当的错误处理
- 为复杂函数添加 JSDoc 注释
- 遵循函数式编程原则

### 不能做
- 使用 `var`（始终使用 `const` 或 `let`）
- 使用基于回调的模式（优先使用 Promise）
- 在同一模块中混合使用 CommonJS 和 ESM
- 忽略内存泄漏或性能问题
- 在异步函数中跳过错误处理
- 在 Node.js 中使用同步 I/O
- 修改函数参数
- 在浏览器中创建阻塞操作

## 关键模式与示例

### Async/Await 错误处理
```js
// ✅ Correct — always handle async errors explicitly
async function fetchUser(id) {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (err) {
    console.error("fetchUser failed:", err);
    return null;
  }
}

// ❌ Incorrect — unhandled rejection, no null guard
async function fetchUser(id) {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

### 可选链与空值合并
```js
// ✅ Correct
const city = user?.address?.city ?? "Unknown";

// ❌ Incorrect — throws if address is undefined
const city = user.address.city || "Unknown";
```

### ESM 模块结构
```js
// ✅ Correct — named exports, no default-only exports for libraries
// utils/math.mjs
export const add = (a, b) => a + b;
export const multiply = (a, b) => a * b;

// consumer.mjs
import { add } from "./utils/math.mjs";

// ❌ Incorrect — mixing require() with ESM
const { add } = require("./utils/math.mjs");
```

### 避免使用 var / 优先使用 const
```js
// ✅ Correct
const MAX_RETRIES = 3;
let attempts = 0;

// ❌ Incorrect
var MAX_RETRIES = 3;
var attempts = 0;
```

## 输出模板

实现 JavaScript 功能时，请提供：
1. 带有清晰导出的模块文件
2. 具有全面覆盖率的测试文件
3. 公共 API 的 JSDoc 文档
4. 所使用模式的简要说明
