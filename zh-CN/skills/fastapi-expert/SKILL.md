---
name: fastapi-expert
description: "Use when building high-performance async Python APIs with FastAPI and Pydantic V2. Invoke to create REST endpoints, define Pydantic models, implement authentication flows, set up async SQLAlchemy database operations, add JWT authentication, build WebSocket endpoints, or generate OpenAPI documentation. Trigger terms: FastAPI, Pydantic, async Python, Python API, REST API Python, SQLAlchemy async, JWT authentication, OpenAPI, Swagger Python."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: backend
  triggers: FastAPI, Pydantic, async Python, Python API, REST API Python, SQLAlchemy async, JWT authentication, OpenAPI, Swagger Python
  role: specialist
  scope: implementation
  output-format: code
  related-skills: fullstack-guardian, django-expert, test-master
---

# FastAPI 专家

在异步 Python、Pydantic V2 以及使用 FastAPI 进行生产级 API 开发方面拥有深厚专业知识。

## 何时使用此技能

- 使用 FastAPI 构建 REST API
- 实现 Pydantic V2 验证模式
- 设置异步数据库操作
- 实现 JWT 身份认证/授权
- 创建 WebSocket 端点
- 优化 API 性能

## 核心工作流程

1. **分析需求** — 确定端点、数据模型、认证需求
2. **设计模式** — 创建 Pydantic V2 模型进行验证
3. **实现** — 使用适当的依赖注入编写异步端点
4. **安全** — 添加身份认证、授权、速率限制
5. **测试** — 使用 pytest 和 httpx 编写异步测试；在每个端点组之后运行 `pytest` 并在 `/docs` 验证 OpenAPI 文档

> **每一步之后的检查点：** 在继续之前，确认模式验证正确、端点返回预期的 HTTP 状态码，并且 `/docs` 反映了预期的 API 接口。

## 最小完整示例

模式 + 端点 + 依赖注入组成一个内聚单元：

```python
# schemas.py
from pydantic import BaseModel, EmailStr, field_validator, model_config

class UserCreate(BaseModel):
    model_config = model_config(str_strip_whitespace=True)

    email: EmailStr
    password: str
    name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserResponse(BaseModel):
    model_config = model_config(from_attributes=True)

    id: int
    email: EmailStr
    name: str | None = None
```

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.schemas import UserCreate, UserResponse
from app import crud

router = APIRouter(prefix="/users", tags=["users"])

DbDep = Annotated[AsyncSession, Depends(get_db)]

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: DbDep) -> UserResponse:
    existing = await crud.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return await crud.create_user(db, payload)
```

```python
# crud.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas import UserCreate
from app.security import hash_password

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    user = User(email=payload.email, hashed_password=hash_password(payload.password), name=payload.name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

## JWT 身份认证代码片段

```python
# security.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

SECRET_KEY = "read-from-env"  # use os.environ / settings
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def create_access_token(subject: str, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    payload = {"sub": subject, "exp": datetime.now(timezone.utc) + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject: str | None = data.get("sub")
        if subject is None:
            raise ValueError
        return subject
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

CurrentUser = Annotated[str, Depends(get_current_user)]
```

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考 | 何时加载 |
|------|------|----------|
| Pydantic V2 | `references/pydantic-v2.md` | 创建模式、验证、model_config |
| SQLAlchemy | `references/async-sqlalchemy.md` | 异步数据库、模型、CRUD 操作 |
| 端点 | `references/endpoints-routing.md` | APIRouter、依赖、路由 |
| 身份认证 | `references/authentication.md` | JWT、OAuth2、get_current_user |
| 测试 | `references/testing-async.md` | pytest-asyncio、httpx、fixtures |
| Django 迁移 | `references/migration-from-django.md` | 从 Django/DRF 迁移到 FastAPI |

## 约束

### 必须做
- 到处使用类型提示（FastAPI 需要它们）
- 使用 Pydantic V2 语法（`field_validator`、`model_validator`、`model_config`）
- 使用 `Annotated` 模式进行依赖注入
- 所有 I/O 操作使用 async/await
- 使用 `X | None` 而不是 `Optional[X]`
- 返回正确的 HTTP 状态码
- 为端点编写文档（自动生成的 OpenAPI）

### 不能做
- 使用同步数据库操作
- 跳过 Pydantic 验证
- 以明文形式存储密码
- 在响应中暴露敏感数据
- 使用 Pydantic V1 语法（`@validator`、`class Config`）
- 不正确地混合同步和异步代码
- 硬编码配置值

## 输出模板

实现 FastAPI 功能时，请提供：
1. 模式文件（Pydantic 模型）
2. 端点文件（包含端点的路由）
3. 如果涉及数据库，提供 CRUD 操作
4. 关键决策的简要说明

## 知识参考

FastAPI、Pydantic V2、async SQLAlchemy、Alembic 迁移、JWT/OAuth2、pytest-asyncio、httpx、BackgroundTasks、WebSockets、依赖注入、OpenAPI/Swagger
