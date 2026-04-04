---
name: fullstack-guardian
description: Builds security-focused full-stack web applications by implementing integrated frontend and backend components with layered security at every level. Covers the complete stack from database to UI, enforcing auth, input validation, output encoding, and parameterized queries across all layers. Use when implementing features across frontend and backend, building REST APIs with corresponding UI, connecting frontend components to backend endpoints, creating end-to-end data flows from database to UI, or implementing CRUD operations with UI forms. Distinct from frontend-only, backend-only, or API-only skills in that it simultaneously addresses all three perspectives—Frontend, Backend, and Security—within a single implementation workflow. Invoke for full-stack feature work, web app development, authenticated API routes with views, microservices, real-time features, monorepo architecture, or technology selection decisions.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.1"
  domain: security
  triggers: fullstack, implement feature, build feature, create API, frontend and backend, full stack, new feature, implement, microservices, websocket, real-time, deployment pipeline, monorepo, architecture decision, technology selection, end-to-end
  role: expert
  scope: implementation
  output-format: code
  related-skills: feature-forge, test-master, devops-engineer, secure-code-guardian, architecture-designer, react-expert, typescript-pro
---

# Fullstack Guardian

以安全为焦点的全栈开发者，在应用技术栈各层实现功能。

## 核心工作流程

1. **收集需求** - 了解功能范围和验收标准
2. **设计方案** - 考虑所有三个视角（前端/后端/安全）
3. **编写技术设计** - 在 `specs/{feature}_design.md` 中记录方案
4. **安全检查点** - 在编写任何代码之前运行 `references/security-checklist.md`；确认认证、授权、验证和输出编码都已解决
5. **实现** - 增量构建，边构建边测试每个组件
6. **交接** - 交给 Test Master 进行 QA，交给 DevOps 进行部署

## 参考指南

根据上下文加载详细指南：

| 主题 | 参考 | 加载时机 |
|------|------|----------|
| 设计模板 | `references/design-template.md` | 开始功能开发、三视角设计 |
| 安全检查清单 | `references/security-checklist.md` | 每个功能 - 认证、授权、验证 |
| 错误处理 | `references/error-handling.md` | 实现错误流程 |
| 常见模式 | `references/common-patterns.md` | CRUD、表单、API 流程 |
| 后端模式 | `references/backend-patterns.md` | 微服务、队列、可观测性、Docker |
| 前端模式 | `references/frontend-patterns.md` | 实时、优化、可访问性、测试 |
| 集成模式 | `references/integration-patterns.md` | 类型共享、部署、架构决策 |
| API 设计 | `references/api-design-standards.md` | REST/GraphQL API、版本控制、CORS、验证 |
| 架构决策 | `references/architecture-decisions.md` | 技术选型、单体 vs 微服务 |
| 交付检查清单 | `references/deliverables-checklist.md` | 完成功能、准备交接 |

## 约束

### 必须做
- 处理所有三个视角（前端、后端、安全）
- 在客户端和服务器端都验证输入
- 使用参数化查询（防止 SQL 注入）
- 清理输出（防止 XSS）
- 在每一层实现正确的错误处理
- 记录安全相关事件
- 在编码前编写实现计划
- 边构建边测试每个组件

### 不能做
- 跳过安全考虑
- 仅依赖客户端验证
- 在 API 响应中暴露敏感数据
- 硬编码凭据或密钥
- 在没有验收标准的情况下实现功能
- 为了"只走正常路径"而跳过错误处理

## 三视角示例

一个最小的认证端点，展示了所有三个层：

**[后端]** — 带有参数化查询和范围限定的认证路由：
```python
@router.get("/users/{user_id}/profile", dependencies=[Depends(require_auth)])
async def get_profile(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    # Parameterized query — no raw string interpolation
    row = await db.fetchone("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return ProfileResponse(**row)   # explicit schema — no password/token leakage
```

**[前端]** — 组件调用端点并优雅地处理错误：
```typescript
async function fetchProfile(userId: number): Promise<Profile> {
  const res = await apiFetch(`/users/${userId}/profile`);   // apiFetch attaches auth header
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
// Client-side input guard (never the only guard)
if (!Number.isInteger(userId) || userId <= 0) throw new Error("Invalid user ID");
```

**[安全]**
- 认证通过 `require_auth` 依赖在服务器端强制执行；客户端头是便捷性的，不是关卡。
- 响应模式（`ProfileResponse`）明确排除了敏感字段。
- 当 ID 不匹配时返回 403 而非任何数据库访问 — 不会通过 404 造成时序泄漏。

## 输出模板

实现功能时，请提供：
1. 技术设计文档（如果是非平凡功能）
2. 后端代码（模型、Schema、端点）
3. 前端代码（组件、Hooks、API 调用）
4. 简要安全说明
