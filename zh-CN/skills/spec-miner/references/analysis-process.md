# 分析流程

## 步骤 1：项目结构

```bash
# Find entry points
Glob: **/main.{ts,js,py,go}
Glob: **/app.{ts,js,py}
Glob: **/index.{ts,js}

# Find routes/controllers
Glob: **/routes/**/*.{ts,js}
Glob: **/controllers/**/*.{ts,js}
Grep: @Controller|@Get|@Post|router\.|app\.get
```

## 步骤 2：数据模型

```bash
# Database schemas
Glob: **/models/**/*.{ts,js,py}
Glob: **/schema*.{ts,js,py,sql}
Glob: **/migrations/**/*
Grep: @Entity|class.*Model|schema\s*=
```

## 步骤 3：业务逻辑

```bash
# Services and logic
Glob: **/services/**/*.{ts,js}
Grep: async.*function|export.*class
```

## 步骤 4：认证与安全

```bash
# Auth patterns
Glob: **/auth/**/*
Glob: **/guards/**/*
Grep: @Guard|middleware|passport|jwt
```

## 步骤 5：外部集成

```bash
# External calls
Grep: fetch\(|axios\.|HttpService|request\(
Glob: **/integrations/**/*
Glob: **/clients/**/*
```

## 步骤 6：配置

```bash
# Config files
Glob: **/*.config.{ts,js}
Glob: **/.env*
Glob: **/config/**/*
```

## 快速参考

| 模式 | 用途 |
|------|------|
| `**/main.{ts,js,py}` | 入口点 |
| `**/routes/**/*` | API 路由 |
| `**/models/**/*` | 数据模型 |
| `@Controller\|@Get` | NestJS 模式 |
| `router.\|app.get` | Express 模式 |