# Django 到 FastAPI 迁移指南

---

## 何时使用本指南

**在以下情况下迁移到 FastAPI：**
- 需要 async/await 进行 I/O 密集型操作
- 需要 WebSocket 或 Server-Sent Events
- 希望自动生成 OpenAPI/Swagger 文档
- 需要为 API 密集型工作负载提供更好的性能
- 希望使用现代 Python 类型提示和编辑器支持
- 从 Django 单体应用构建微服务
- 需要更低的资源消耗

**在以下情况下不要迁移：**
- 大量使用 Django 管理后台界面
- 存在复杂的 Django ORM 模型继承
- 复杂的表单处理和验证
- 需要服务端模板渲染
- 团队缺乏异步 Python 经验
- Django 生态插件是关键依赖
- 迁移成本超过业务价值

---

## 概念映射：Django/DRF -> FastAPI

| Django/DRF 概念 | FastAPI 对应 | 说明 |
|----------------|-------------|------|
| `models.Model` | Pydantic `BaseModel` + SQLAlchemy | 将模式与 ORM 分离 |
| `serializers.Serializer` | Pydantic `BaseModel` | 类型安全的验证 |
| `ModelSerializer` | 多个 Pydantic 模型 | 创建/读取/更新模式 |
| `ViewSet` | `APIRouter` + 路径操作 | 更显式的路由 |
| `GenericAPIView` | 依赖注入 | 基于函数的方式 |
| `@api_view` 装饰器 | `@router.get/post` | 内置 HTTP 方法 |
| `urls.py` | `APIRouter` + `app.include_router` | 嵌套路由 |
| `settings.py` | `pydantic-settings` | 基于环境的配置 |
| `middleware` | 中间件 + 依赖 | 更细粒度的控制 |
| `permissions` | 依赖 | 可组合的认证 |
| `authentication` | OAuth2 + JWT 依赖 | 基于标准 |
| `pagination` | 查询参数 + 依赖 | 手动实现 |
| `filters` | 查询参数 | 类型安全的过滤 |
| `Django ORM` | SQLAlchemy 2.0+ | 异步支持 |
| `select_related` | `selectinload` | 预加载 |
| `prefetch_related` | `joinedload` | 连接策略 |
| `pytest-django` | `pytest + httpx` | 异步测试客户端 |
| `admin.py` | 外部工具（SQLAdmin 等） | 非内置 |

---

## 序列化器 -> Pydantic V2 迁移

### Django REST Framework 序列化器

```python
# Django DRF
from rest_framework import serializers
from .models import User, Post

class UserSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at', 'post_count']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'email': {'write_only': True}
        }

    def get_post_count(self, obj):
        return obj.posts.count()

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username too short")
        return value

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'tags', 'published']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        return post
```

### FastAPI Pydantic V2 模式

```python
# FastAPI with Pydantic V2
from pydantic import BaseModel, EmailStr, Field, field_validator, computed_field
from datetime import datetime
from typing import Annotated

# Base schemas
class UserBase(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr

# Create schema (input)
class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8)]

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError("Username too short")
        return v

# Update schema (partial)
class UserUpdate(BaseModel):
    username: Annotated[str | None, Field(min_length=3, max_length=50)] = None
    email: EmailStr | None = None

# Read schema (output) - analogous to read_only_fields
class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = {
        "from_attributes": True  # Pydantic V2: replaces orm_mode
    }

# Read schema with relations - analogous to SerializerMethodField
class UserReadWithStats(UserRead):
    post_count: int

    @computed_field  # Pydantic V2 computed fields
    @property
    def display_name(self) -> str:
        return f"@{self.username}"

# Nested schemas
class PostBase(BaseModel):
    title: Annotated[str, Field(max_length=200)]
    content: str
    tags: list[str] = []
    published: bool = False

class PostCreate(PostBase):
    pass

class PostRead(PostBase):
    id: int
    author: UserRead  # Nested serialization
    created_at: datetime

    model_config = {"from_attributes": True}

# Embedding vs side-loading
class PostReadMinimal(BaseModel):
    """Minimal post representation (just ID)"""
    id: int
    title: str
    author_id: int  # Side-loaded reference

    model_config = {"from_attributes": True}
```

---

## ViewSet -> APIRouter 迁移

### Django REST Framework ViewSet

```python
# Django DRF ViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            return queryset.filter(author=self.request.user)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        post = self.get_object()
        post.published = True
        post.save()
        return Response({'status': 'published'})

    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_posts = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_posts, many=True)
        return Response(serializer.data)
```

### FastAPI APIRouter 与依赖

```python
# FastAPI APIRouter
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from .database import get_db
from .auth import get_current_user
from .models import Post as PostModel, User as UserModel
from .schemas import PostRead, PostCreate, PostUpdate, UserRead

router = APIRouter(prefix="/posts", tags=["posts"])

# Dependency for database session
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[UserModel, Depends(get_current_user)]

# List posts (GET /posts)
@router.get("/", response_model=list[PostRead])
async def list_posts(
    db: DbSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
):
    """Analogous to ViewSet.list()"""
    result = await db.execute(
        select(PostModel)
        .where(PostModel.author_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    posts = result.scalars().all()
    return posts

# Create post (POST /posts)
@router.post("/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Analogous to ViewSet.create()"""
    post = PostModel(**post_data.model_dump(), author_id=current_user.id)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post

# Retrieve single post (GET /posts/{post_id})
@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Analogous to ViewSet.retrieve()"""
    result = await db.execute(
        select(PostModel).where(
            PostModel.id == post_id,
            PostModel.author_id == current_user.id
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Update post (PUT /posts/{post_id})
@router.put("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Analogous to ViewSet.update()"""
    result = await db.execute(
        select(PostModel).where(
            PostModel.id == post_id,
            PostModel.author_id == current_user.id
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Update only provided fields
    for field, value in post_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return post

# Delete post (DELETE /posts/{post_id})
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Analogous to ViewSet.destroy()"""
    result = await db.execute(
        select(PostModel).where(
            PostModel.id == post_id,
            PostModel.author_id == current_user.id
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()

# Custom action: Publish (POST /posts/{post_id}/publish)
@router.post("/{post_id}/publish", response_model=dict)
async def publish_post(
    post_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    """Analogous to @action(detail=True)"""
    result = await db.execute(
        select(PostModel).where(
            PostModel.id == post_id,
            PostModel.author_id == current_user.id
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.published = True
    await db.commit()
    return {"status": "published"}

# Custom collection action: Recent posts (GET /posts/recent)
@router.get("/actions/recent", response_model=list[PostRead])
async def recent_posts(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(10, le=50),
):
    """Analogous to @action(detail=False)"""
    result = await db.execute(
        select(PostModel)
        .where(PostModel.author_id == current_user.id)
        .order_by(PostModel.created_at.desc())
        .limit(limit)
    )
    posts = result.scalars().all()
    return posts
```

---

## Django ORM -> 异步 SQLAlchemy

### Django ORM 模型

```python
# Django models
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
        ]

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=False)

    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']
```

### SQLAlchemy 2.0 异步模型

```python
# SQLAlchemy 2.0 models
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, ForeignKey, Index
from datetime import datetime
from typing import List

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Columns with type hints
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships (analogous to related_name)
    posts: Mapped[List["Post"]] = relationship(back_populates="author")

    __table_args__ = (
        Index('ix_users_username', 'username'),
    )

class Post(Base):
    __tablename__ = 'posts'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    published: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship
    author: Mapped["User"] = relationship(back_populates="posts")

    __table_args__ = (
        Index('ix_posts_created_at', 'created_at'),
    )
```

### 查询模式：Django ORM 对比 SQLAlchemy

```python
# Django ORM queries
from django.db.models import Count, Q

# Simple filter
posts = Post.objects.filter(published=True)

# Select related (JOIN)
posts = Post.objects.select_related('author').filter(published=True)

# Prefetch related (separate query)
users = User.objects.prefetch_related('posts').all()

# Complex filtering
posts = Post.objects.filter(
    Q(published=True) | Q(author__username='admin')
).order_by('-created_at')[:10]

# Aggregation
user_stats = User.objects.annotate(
    post_count=Count('posts')
).filter(post_count__gte=5)
```

```python
# SQLAlchemy 2.0 async queries
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload, joinedload

# Simple filter
async def get_published_posts(db: AsyncSession):
    result = await db.execute(
        select(Post).where(Post.published == True)
    )
    return result.scalars().all()

# Eager loading with JOIN (selectinload = separate query)
async def get_posts_with_authors(db: AsyncSession):
    result = await db.execute(
        select(Post)
        .options(selectinload(Post.author))
        .where(Post.published == True)
    )
    return result.scalars().all()

# Prefetch related (joinedload = single query with JOIN)
async def get_users_with_posts(db: AsyncSession):
    result = await db.execute(
        select(User).options(joinedload(User.posts))
    )
    return result.unique().scalars().all()

# Complex filtering
async def get_complex_posts(db: AsyncSession):
    result = await db.execute(
        select(Post)
        .join(Post.author)
        .where(
            or_(
                Post.published == True,
                User.username == 'admin'
            )
        )
        .order_by(Post.created_at.desc())
        .limit(10)
    )
    return result.scalars().all()

# Aggregation
async def get_user_stats(db: AsyncSession):
    result = await db.execute(
        select(User, func.count(Post.id).label('post_count'))
        .join(Post)
        .group_by(User.id)
        .having(func.count(Post.id) >= 5)
    )
    return result.all()
```

---

## 身份认证：SimpleJWT -> FastAPI JWT

### Django SimpleJWT

```python
# Django settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# Views
from rest_framework_simplejwt.views import TokenObtainPairView

# Usage in ViewSet
from rest_framework.permissions import IsAuthenticated

class ProtectedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
```

### FastAPI JWT 身份认证

```python
# auth.py - FastAPI JWT implementation
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Annotated

# Configuration
SECRET_KEY = "your-secret-key"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency: Get current user from token
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(UserModel).where(UserModel.username == token_data.username)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

# Login endpoint
auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Authenticate user
    result = await db.execute(
        select(UserModel).where(UserModel.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint usage
@router.get("/protected")
async def protected_route(current_user: Annotated[UserModel, Depends(get_current_user)]):
    return {"message": f"Hello {current_user.username}"}
```

---

## 测试迁移

### Django/DRF 测试

```python
# Django pytest
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username='test', password='test123')

@pytest.mark.django_db
def test_create_post(api_client, user):
    api_client.force_authenticate(user=user)
    response = api_client.post('/api/posts/', {
        'title': 'Test Post',
        'content': 'Test content'
    })
    assert response.status_code == 201
    assert response.data['title'] == 'Test Post'
```

### FastAPI 测试

```python
# FastAPI pytest with httpx
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.database import get_db, Base
from app.models import User

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def auth_headers(client, db_session):
    # Create test user
    user = User(username="test", email="test@example.com")
    user.hashed_password = get_password_hash("test123")
    db_session.add(user)
    await db_session.commit()

    # Get token
    response = await client.post("/auth/token", data={
        "username": "test",
        "password": "test123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_post(client, auth_headers):
    response = await client.post(
        "/posts/",
        json={"title": "Test Post", "content": "Test content"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Post"

@pytest.mark.asyncio
async def test_list_posts(client, auth_headers, db_session):
    # Create test data
    user = await db_session.execute(select(User).where(User.username == "test"))
    user = user.scalar_one()

    post = Post(title="Test", content="Content", author_id=user.id)
    db_session.add(post)
    await db_session.commit()

    # Test endpoint
    response = await client.get("/posts/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
```

---

## 增量迁移策略

### 阶段一：并行 API（绞杀者模式）

Django 和 FastAPI 并行运行，逐步迁移端点。

```python
# Nginx routing config
location /api/v2/ {
    proxy_pass http://fastapi:8000;
}

location /api/ {
    proxy_pass http://django:8001;
}
```

**方法：**
1. 使用共享数据库搭建 FastAPI（初始为只读）
2. 首先迁移 GET 端点（风险最低）
3. 添加写端点，对两个系统进行双写
4. 验证数据一致性
5. 逐步切换流量（使用功能开关）

### 阶段二：共享数据库迁移

```python
# FastAPI with existing Django database
from sqlalchemy import MetaData

# Reflect existing Django tables
metadata = MetaData()
metadata.reflect(bind=engine, only=['users', 'posts'])

# Or define models matching Django schema
class User(Base):
    __tablename__ = 'auth_user'  # Django's user table
    # Map to Django's column names
```

### 阶段三：数据库模式现代化

流量迁移完成后，进行模式现代化：
- 移除 Django 特有字段（`content_type`、`permissions`）
- 简化表名（移除应用前缀）
- 添加数据库级别约束
- 为异步查询优化索引

### 阶段四：完全切换

```python
# Decommission Django
# 1. Archive Django admin usage
# 2. Export management commands to FastAPI CLI
# 3. Migrate background tasks to Celery/Dramatiq
# 4. Remove Django dependency
```

---

## 常见陷阱

### 1. Async/Await 错误

**错误：**
```python
# Blocking call in async function
@router.get("/users")
async def get_users(db: AsyncSession):
    users = db.execute(select(User)).scalars().all()  # Missing await
    return users
```

**正确：**
```python
@router.get("/users")
async def get_users(db: AsyncSession):
    result = await db.execute(select(User))  # Await async operation
    users = result.scalars().all()
    return users
```

### 2. 缺少 `from_attributes`（orm_mode）

**错误：**
```python
class UserRead(BaseModel):
    id: int
    username: str
    # Missing config - won't work with SQLAlchemy models
```

**正确：**
```python
class UserRead(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}  # Pydantic V2
```

### 3. 会话管理

**错误：**
```python
# Reusing session across requests
db_session = async_sessionmaker(engine)()

@router.get("/users")
async def get_users():
    return await db_session.execute(select(User))  # Session leak
```

**正确：**
```python
# Dependency injection per request
async def get_db():
    async with async_sessionmaker(engine)() as session:
        yield session
        await session.commit()

@router.get("/users")
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### 4. 关联加载

**错误：**
```python
# Lazy loading in async (causes errors)
user = await db.get(User, user_id)
posts = user.posts  # Error: lazy loading not supported in async
```

**正确：**
```python
# Eager loading with selectinload
result = await db.execute(
    select(User).options(selectinload(User.posts)).where(User.id == user_id)
)
user = result.scalar_one()
posts = user.posts  # Already loaded
```

### 5. 事务处理

**错误：**
```python
# Auto-commit not configured
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession):
    db_user = User(**user.dict())
    db.add(db_user)
    # Missing commit - changes lost
    return db_user
```

**正确：**
```python
@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession):
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()  # Explicit commit
    await db.refresh(db_user)  # Refresh to get DB-generated fields
    return db_user
```

---

## 交叉引用

有关全面的迁移策略和现代化模式：
- **Legacy Modernizer**: `/skills/legacy-modernizer/references/migration-strategies.md`
  - 绞杀者模式实现
  - 功能开关策略
  - 回滚流程
  - 数据迁移管道

---

## 迁移检查清单

**迁移前：**
- [ ] 异步就绪评估（I/O 密集型工作负载？）
- [ ] 团队异步 Python 经验验证
- [ ] 数据库兼容性验证（异步驱动可用）
- [ ] 管理后台替代方案确定
- [ ] 迁移时间表获批（6-12 个月为现实预期）

**迁移期间：**
- [ ] 并行部署配置完成
- [ ] 监控和告警设置完成
- [ ] 负载测试完成
- [ ] 数据一致性验证自动化
- [ ] 回滚流程测试通过

**迁移后：**
- [ ] Django 依赖已移除
- [ ] 文档已更新
- [ ] 团队培训已完成
- [ ] 性能提升已度量
- [ ] 成本节约已验证

---

**关键要点：** 增量迁移。从读取密集型端点开始，充分验证，然后逐步迁移写操作。始终保持回滚能力。
