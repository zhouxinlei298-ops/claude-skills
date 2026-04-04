# OWASP Top 10 防护

## OWASP Top 10 快速参考

| # | 漏洞 | 防护措施 |
|---|-----|---------|
| 1 | 注入 | 参数化查询，ORM |
| 2 | 身份验证失效 | 强密码，多因素认证，安全会话 |
| 3 | 敏感数据暴露 | 静态传输加密 |
| 4 | XXE | 禁用 DTD，使用 JSON |
| 5 | 访问控制失效 | 默认拒绝，服务器端验证 |
| 6 | 安全配置错误 | 安全头，禁用默认值 |
| 7 | XSS | 输出编码，CSP |
| 8 | 不安全反序列化 | 模式验证，允许列表 |
| 9 | 已知漏洞 | 依赖扫描 |
| 10 | 不足的日志和监控 | 记录安全事件 |

## A01: 注入防护

```typescript
// SQL Injection - Use parameterized queries
// ❌ Bad
const bad = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ Good
const good = await db.query('SELECT * FROM users WHERE id = $1', [userId]);

// ✅ Good - Use ORM
const user = await prisma.user.findUnique({ where: { id: userId } });

// Command Injection - Avoid shell execution
// ❌ Bad
exec(`ls ${userInput}`);

// ✅ Good - Use library functions
const files = fs.readdirSync(safeDirectory);
```

## A02: 身份验证失效

```typescript
// Use bcrypt for passwords
const hash = await bcrypt.hash(password, 12);
const isValid = await bcrypt.compare(password, hash);

// Implement account lockout
if (failedAttempts >= 5) {
  await lockAccount(userId, 15 * 60 * 1000); // 15 min
}

// Use secure session configuration
app.use(session({
  secret: process.env.SESSION_SECRET,
  cookie: {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 15 * 60 * 1000, // 15 minutes
  },
}));
```

## A03: 敏感数据暴露

```typescript
// Encrypt sensitive data at rest
import crypto from 'crypto';

function encrypt(text: string, key: Buffer): string {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  // ... encryption logic
}

// Use HTTPS only
app.use((req, res, next) => {
  if (!req.secure) {
    return res.redirect(`https://${req.hostname}${req.url}`);
  }
  next();
});
```

## A05: 访问控制失效

```typescript
// Always validate on server side
async function getResource(userId: string, resourceId: string) {
  const resource = await db.resource.findUnique({ where: { id: resourceId } });

  // Verify ownership
  if (resource.ownerId !== userId) {
    throw new ForbiddenError('Access denied');
  }

  return resource;
}

// Use role-based access
function requireRole(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Forbidden' });
    }
    next();
  };
}
```

## A07: XSS 防护

```typescript
// Use Content Security Policy
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
  },
}));

// Sanitize user input for HTML
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);
```

## 快速参考

| 攻击类型 | 防御措施 |
|---------|---------|
| SQL 注入 | 参数化查询 |
| XSS | 输出编码，CSP |
| CSRF | CSRF 令牌 |
| IDOR | 授权检查 |
| 命令注入 | 避免使用 exec()，验证输入 |