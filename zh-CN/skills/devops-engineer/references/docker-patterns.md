# Docker 模式

## 多阶段 Dockerfile（Node.js）

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
USER nodejs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/main.js"]
```

## 多阶段 Dockerfile（Python）

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runner
WORKDIR /app
RUN useradd -m -u 1001 appuser
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Docker Compose（开发环境）

```yaml
version: '3.8'
services:
  app:
    build:
      context: .
      target: builder  # Use dev stage
    volumes:
      - .:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/app
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## 安全最佳实践

| 实践 | 实现方式 |
|------|----------|
| 非 root 用户 | `USER nodejs` 或 `USER 1001` |
| 最小基础镜像 | 使用 `-alpine` 或 `-slim` 变体 |
| 镜像中无密钥 | 使用运行时环境变量或密钥管理 |
| 固定版本 | `FROM node:20.10.0-alpine` 而不是 `latest` |
| 扫描镜像 | `docker scout`, `trivy`, `snyk` |
| 健康检查 | `HEALTHCHECK` 指令 |
| .dockerignore | 排除 `node_modules`, `.git`, `.env` |

## .dockerignore 模板

```
node_modules
.git
.env*
*.md
Dockerfile*
docker-compose*
.dockerignore
coverage
.nyc_output
```
