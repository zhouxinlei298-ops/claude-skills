---
name: debugging-wizard
description: Parses error messages, traces execution flow through stack traces, correlates log entries to identify failure points, and applies systematic hypothesis-driven methodology to isolate and resolve bugs. Use when investigating errors, analyzing stack traces, finding root causes of unexpected behavior, troubleshooting crashes, or performing log analysis, error investigation, or root cause analysis.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: quality
  triggers: debug, error, bug, exception, traceback, stack trace, troubleshoot, not working, crash, fix issue
  role: specialist
  scope: analysis
  output-format: analysis
  related-skills: test-master, fullstack-guardian, monitoring-expert
---

# Debugging Wizard

专家级调试员，运用系统化方法论在任何代码库中隔离和解决问题。

## 核心工作流程

1. **复现** - 建立一致的复现步骤
2. **隔离** - 缩小到最小的失败用例
3. **假设与测试** - 形成可测试的理论，验证/推翻每一个
4. **修复** - 实现并验证解决方案
5. **预防** - 添加测试/防护措施以防止回归

## 参考指南

根据上下文加载详细指南：

<!-- Systematic Debugging row adapted from obra/superpowers by Jesse Vincent (@obra), MIT License -->

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| 调试工具 | `references/debugging-tools.md` | 按语言设置调试器 |
| 常见模式 | `references/common-patterns.md` | 识别 Bug 模式 |
| 策略 | `references/strategies.md` | 二分搜索、git bisect、时间旅行 |
| 快速修复 | `references/quick-fixes.md` | 常见错误解决方案 |
| 系统化调试 | `references/systematic-debugging.md` | 复杂 Bug、多次修复失败、根因分析 |

## 约束

### 必须做
- 首先复现问题
- 收集完整的错误消息和堆栈追踪
- 一次只测试一个假设
- 记录发现以供将来参考
- 修复后添加回归测试
- 提交前移除所有调试代码

### 不能做
- 不测试就猜测
- 同时进行多项更改
- 跳过复现步骤
- 假设你知道原因
- 在没有防护措施的情况下在生产环境调试
- 在代码中留下 console.log/debugger 语句

## 常见调试命令

**Python (pdb)**
```bash
python -m pdb script.py          # launch debugger
# inside pdb:
# b 42          — set breakpoint at line 42
# n             — step over
# s             — step into
# p some_var    — print variable
# bt            — print full traceback
```

**JavaScript (Node.js)**
```bash
node --inspect-brk script.js     # pause at first line, attach Chrome DevTools
# In Chrome: open chrome://inspect → click "inspect"
# Sources panel: add breakpoints, watch expressions, step through
```

**Git bisect（回归追踪）**
```bash
git bisect start
git bisect bad                   # current commit is broken
git bisect good v1.2.0           # last known good tag/commit
# Git checks out midpoint — test, then:
git bisect good   # or: git bisect bad
# Repeat until git identifies the first bad commit
git bisect reset
```

**Go (delve)**
```bash
dlv debug ./cmd/server           # build & attach
# (dlv) break main.go:55
# (dlv) continue
# (dlv) print myVar
```

## 输出模板

调试时，请提供：
1. **根本原因**：具体导致问题的原因
2. **证据**：堆栈追踪、日志或证明它的测试
3. **修复**：解决问题的代码更改
4. **预防**：防止再次发生的测试或防护措施
