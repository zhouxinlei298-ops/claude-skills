# 输入验证

## Zod 验证

```typescript
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[\w\s-]+$/),
  age: z.number().int().min(0).max(150).optional(),
  role: z.enum(['user', 'admin']).default('user'),
});

function validateUser(data: unknown) {
  return UserSchema.parse(data); // Throws on invalid
}

// Safe parse (no throw)
const result = UserSchema.safeParse(data);
if (!result.success) {
  console.error(result.error.issues);
}
```

## SQL 注入防护

```typescript
// ❌ NEVER do this
const bad = `SELECT * FROM users WHERE id = ${userId}`;
const bad2 = `SELECT * FROM users WHERE name = '${name}'`;

// ✅ Parameterized queries
const good = await db.query(
  'SELECT * FROM users WHERE id = $1 AND name = $2',
  [userId, name]
);

// ✅ Use ORM
const user = await prisma.user.findFirst({
  where: { id: userId, name: name }
});

// ✅ Query builder
const user = await knex('users')
  .where({ id: userId, name: name })
  .first();
```

## 路径穿越防护

```typescript
import path from 'path';

// ❌ Vulnerable
const vulnerable = path.join('/uploads', userInput);

// ✅ Safe - validate and sanitize
function getSecurePath(baseDir: string, userInput: string): string {
  // Remove any path traversal attempts
  const sanitized = path.basename(userInput);

  // Resolve and verify it's within base directory
  const fullPath = path.resolve(baseDir, sanitized);

  if (!fullPath.startsWith(path.resolve(baseDir))) {
    throw new Error('Invalid path');
  }

  return fullPath;
}
```

## 命令注入防护

```typescript
import { execFile } from 'child_process';

// ❌ Never use exec with user input
exec(`convert ${userInput}`); // Vulnerable!

// ✅ Use execFile with arguments array
execFile('convert', ['-resize', '100x100', safeFilename], (error, stdout) => {
  // ...
});

// ✅ Better: Use library functions instead of shell
import sharp from 'sharp';
await sharp(inputPath).resize(100, 100).toFile(outputPath);
```

## URL 验证

```typescript
function validateUrl(input: string, allowedHosts: string[]): URL {
  const url = new URL(input);

  // Check protocol
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new Error('Invalid protocol');
  }

  // Check host allowlist
  if (!allowedHosts.includes(url.hostname)) {
    throw new Error('Host not allowed');
  }

  return url;
}
```

## 文件上传验证

```typescript
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif'];
const MAX_SIZE = 5 * 1024 * 1024; // 5MB

function validateUpload(file: Express.Multer.File) {
  if (!ALLOWED_TYPES.includes(file.mimetype)) {
    throw new Error('Invalid file type');
  }

  if (file.size > MAX_SIZE) {
    throw new Error('File too large');
  }

  // Verify magic bytes (not just extension)
  const buffer = fs.readFileSync(file.path);
  const type = fileType.fromBuffer(buffer);

  if (!type || !ALLOWED_TYPES.includes(type.mime)) {
    throw new Error('Invalid file content');
  }
}
```

## 快速参考

| 输入类型 | 验证方式 |
|---------|---------|
| 邮箱 | 正则表达式 + 最大长度 |
| URL | 协议 + 主机允许列表 |
| 文件路径 | basename + 解析检查 |
| SQL | 参数化查询 |
| 命令 | execFile + 禁用 shell |
| 文件上传 | 类型 + 大小 + 魔数 |