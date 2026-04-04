# SQLAlchemy 最佳实践指南

## 📋 SQLAlchemy 基础

### 1. 安装与配置

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 创建数据库引擎
DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # 连接池大小
    max_overflow=20,       # 最大溢出连接数
    pool_timeout=30,       # 获取连接超时时间
    pool_recycle=3600,     # 连接回收时间
    pool_pre_ping=True,    # 连接前ping检查
    echo=True              # 输出SQL语句（开发环境）
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基类
Base = declarative_base()

# 获取数据库会话
def get_db() -> Session:
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2. 定义模型

```python
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, 
    DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    full_name = Column(String(200))
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="user")
    
    # 复合索引
    __table_args__ = (
        Index('idx_user_active_created', 'is_active', 'created_at'),
    )

class Post(Base):
    """文章模型"""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    content = Column(Text)
    excerpt = Column(String(500))
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    is_published = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系定义
    author = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    tags = relationship("PostTag", back_populates="post")

class Category(Base):
    """分类模型"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系定义
    posts = relationship("Post", back_populates="category")

class Comment(Base):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('comments.id'))
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系定义
    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])
    replies = relationship("Comment", backref=backref('parent', remote_side=[id]))

class Tag(Base):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class PostTag(Base):
    """文章-标签关联模型"""
    __tablename__ = 'post_tags'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    tag_id = Column(Integer, ForeignKey('tags.id'), nullable=False)
    
    # 关系定义
    post = relationship("Post", back_populates="tags")
    tag = relationship("Tag")
    
    __table_args__ = (
        Index('idx_post_tag_post_tag', 'post_id', 'tag_id', unique=True),
    )

# 创建所有表
def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

# 删除所有表
def drop_tables():
    """删除数据库表"""
    Base.metadata.drop_all(bind=engine)
```

## 🔍 查询操作

### 1. 基础查询

```python
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func

def basic_queries(db: Session):
    """基础查询示例"""
    
    # 获取所有用户
    users = db.query(User).all()
    
    # 获取单个用户（通过ID）
    user = db.query(User).filter(User.id == 1).first()
    
    # 获取单个用户（通过邮箱）
    user = db.query(User).filter(User.email == "user@example.com").first()
    
    # 获取活跃用户
    active_users = db.query(User).filter(User.is_active == True).all()
    
    # 多条件查询（AND）
    users = db.query(User).filter(
        User.is_active == True,
        User.created_at >= datetime(2024, 1, 1)
    ).all()
    
    # 多条件查询（OR）
    users = db.query(User).filter(
        or_(
            User.username == "admin",
            User.email == "admin@example.com"
        )
    ).all()
    
    # 排序
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    # 限制和偏移
    users = db.query(User).limit(10).offset(20).all()
    
    # 聚合查询
    count = db.query(User).filter(User.is_active == True).count()
    
    # 使用函数
    total_views = db.query(func.sum(Post.view_count)).scalar()
    
    return users
```

### 2. 连接查询

```python
from sqlalchemy.orm import joinedload, contains_eager, aliased

def join_queries(db: Session):
    """连接查询示例"""
    
    # 内连接
    results = db.query(User, Post).join(Post, User.id == Post.author_id).all()
    
    # 左外连接
    results = db.query(User).outerjoin(Post, User.id == Post.author_id).all()
    
    # 使用 joinedload 预加载（避免 N+1 问题）
    users_with_posts = db.query(User).options(
        joinedload(User.posts)
    ).all()
    
    # 多层预加载
    users_with_posts_comments = db.query(User).options(
        joinedload(User.posts).joinedload(Post.comments)
    ).all()
    
    # 使用 selectinload（适合一对多关系）
    users_with_posts = db.query(User).options(
        selectinload(User.posts)
    ).all()
    
    # 使用 subqueryload（适合大数据集）
    users_with_posts = db.query(User).options(
        subqueryload(User.posts)
    ).all()
    
    # 自连接查询（例如：评论的回复）
    CommentAlias = aliased(Comment)
    comments_with_replies = db.query(Comment).join(
        CommentAlias, Comment.id == CommentAlias.parent_id
    ).all()
    
    return results
```

### 3. 高级查询

```python
from sqlalchemy.orm import with_polymorphic, contains_eager
from sqlalchemy import distinct, case

def advanced_queries(db: Session):
    """高级查询示例"""
    
    # DISTINCT 查询
    categories = db.query(distinct(Post.category_id)).all()
    
    # CASE 语句
    posts_with_status = db.query(
        Post,
        case(
            [(Post.is_published == True, "已发布")],
            else_="草稿"
        ).label("status")
    ).all()
    
    # 子查询
    subquery = db.query(
        Post.author_id,
        func.count(Post.id).label('post_count')
    ).group_by(Post.author_id).subquery()
    
    users_with_post_count = db.query(
        User,
        subquery.c.post_count
    ).join(subquery, User.id == subquery.c.author_id).all()
    
    # 窗口函数
    from sqlalchemy import over
    window = over(
        func.row_number(),
        partition_by=Post.category_id,
        order_by=Post.view_count.desc()
    )
    
    top_posts = db.query(
        Post,
        window.label('rank')
    ).filter(window <= 10).all()
    
    # 聚合查询
    category_stats = db.query(
        Category.name,
        func.count(Post.id).label('post_count'),
        func.sum(Post.view_count).label('total_views')
    ).join(Post).group_by(Category.id).all()
    
    return results
```

## 💾 数据库操作（CRUD）

### 1. 创建数据

```python
from sqlalchemy.orm import Session

def create_user(db: Session, user_data: dict) -> User:
    """创建用户"""
    user = User(
        email=user_data["email"],
        username=user_data["username"],
        password_hash=hash_password(user_data["password"]),
        full_name=user_data.get("full_name", "")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_post(db: Session, post_data: dict) -> Post:
    """创建文章"""
    post = Post(
        title=post_data["title"],
        slug=generate_slug(post_data["title"]),
        content=post_data["content"],
        excerpt=post_data.get("excerpt", ""),
        author_id=post_data["author_id"],
        category_id=post_data.get("category_id"),
        is_published=post_data.get("is_published", False),
        published_at=datetime.utcnow() if post_data.get("is_published") else None
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def create_comment(db: Session, comment_data: dict) -> Comment:
    """创建评论"""
    comment = Comment(
        content=comment_data["content"],
        post_id=comment_data["post_id"],
        user_id=comment_data["user_id"],
        parent_id=comment_data.get("parent_id")
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

# 批量创建
def create_posts_batch(db: Session, posts_data: list[dict]) -> list[Post]:
    """批量创建文章"""
    posts = [
        Post(
            title=post_data["title"],
            slug=generate_slug(post_data["title"]),
            content=post_data["content"],
            author_id=post_data["author_id"]
        )
        for post_data in posts_data
    ]
    db.add_all(posts)
    db.commit()
    for post in posts:
        db.refresh(post)
    return posts
```

### 2. 更新数据

```python
from sqlalchemy.orm import Session

def update_user(db: Session, user_id: int, update_data: dict) -> User:
    """更新用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    for key, value in update_data.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def publish_post(db: Session, post_id: int) -> Post:
    """发布文章"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return None
    
    post.is_published = True
    post.published_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    return post

def increment_view_count(db: Session, post_id: int) -> int:
    """增加浏览量（原子操作）"""
    result = db.query(Post).filter(
        Post.id == post_id
    ).update(
        {Post.view_count: Post.view_count + 1},
        synchronize_session=False
    )
    db.commit()
    return result

# 批量更新
def update_posts_category(db: Session, old_category_id: int, new_category_id: int) -> int:
    """批量更新文章分类"""
    result = db.query(Post).filter(
        Post.category_id == old_category_id
    ).update(
        {Post.category_id: new_category_id},
        synchronize_session=False
    )
    db.commit()
    return result
```

### 3. 删除数据

```python
from sqlalchemy.orm import Session

def delete_user(db: Session, user_id: int) -> bool:
    """删除用户"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    return True

def delete_post(db: Session, post_id: int) -> bool:
    """删除文章"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return False
    
    db.delete(post)
    db.commit()
    return True

def delete_unapproved_comments(db: Session, days: int = 30) -> int:
    """删除未批准的旧评论"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    result = db.query(Comment).filter(
        Comment.is_approved == False,
        Comment.created_at < cutoff_date
    ).delete(synchronize_session=False)
    db.commit()
    return result
```

## ⚡ 查询优化

### 1. 避免 N+1 查询

```python
from sqlalchemy.orm import joinedload, selectinload, subqueryload

# 错误：N+1 查询
def get_users_with_posts_bad(db: Session):
    """N+1 查询示例（错误）"""
    users = db.query(User).all()
    for user in users:
        # 每个用户都会发起一次查询
        posts = db.query(Post).filter(Post.author_id == user.id).all()
        user.posts = posts
    return users

# 正确：使用预加载
def get_users_with_posts_good(db: Session):
    """使用预加载（正确）"""
    users = db.query(User).options(
        joinedload(User.posts)
    ).all()
    return users

# 选择合适的预加载方式
def get_users_with_posts_optimized(db: Session):
    """优化的预加载"""
    # 使用 selectinload 适合一对多关系
    users = db.query(User).options(
        selectinload(User.posts)
    ).all()
    
    # 使用 joinedload 适合多对一关系
    posts = db.query(Post).options(
        joinedload(Post.author)
    ).all()
    
    # 使用 subqueryload 适合大数据集
    users = db.query(User).options(
        subqueryload(User.posts)
    ).all()
    
    return users
```

### 2. 索引优化

```python
from sqlalchemy import Index, create_engine

# 在模型中定义索引
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    
    # 复合索引
    __table_args__ = (
        Index('idx_user_active_created', 'is_active', 'created_at'),
    )

# 创建额外的索引
def create_additional_indexes():
    """创建额外的索引"""
    # 在已存在的表上创建索引
    from sqlalchemy import Index, text
    
    # 创建索引
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_post_published_views "
            "ON posts (is_published, view_count DESC)"
        ))
        conn.commit()
    
    # 使用 Index 对象
    with engine.connect() as conn:
        Index(
            'idx_post_author_published',
            Post.author_id,
            Post.is_published
        ).create(bind=conn)
        conn.commit()
```

### 3. 查询优化技巧

```python
from sqlalchemy.orm import load_only, defer, undefer

def optimized_queries(db: Session):
    """优化查询"""
    
    # 只加载需要的列
    users_basic_info = db.query(User).options(
        load_only(User.id, User.username, User.email)
    ).all()
    
    # 延迟加载大型字段
    posts = db.query(Post).options(
        defer(Post.content)
    ).all()
    
    # 需要时才加载大型字段
    post = db.query(Post).options(
        defer(Post.content)
    ).filter(Post.id == 1).first()
    content = post.content  # 在需要时才加载
    
    # 使用切片限制结果
    first_page = db.query(Post).limit(20).all()
    
    # 使用 exists 而不是检查结果
    from sqlalchemy import exists
    has_posts = db.query(
        exists().where(Post.author_id == 1)
    ).scalar()
    
    # 使用 count 而不是获取所有结果并计算长度
    post_count = db.query(Post).filter(Post.is_published == True).count()
    
    return users_basic_info
```

## 🔒 事务管理

### 1. 基础事务

```python
from sqlalchemy.orm import Session

def transaction_example(db: Session):
    """事务示例"""
    try:
        # 开始事务
        user = User(email="user@example.com", username="testuser")
        db.add(user)
        
        # 创建文章
        post = Post(
            title="测试文章",
            slug="test-post",
            content="文章内容",
            author_id=user.id
        )
        db.add(post)
        
        # 提交事务
        db.commit()
        
        return post
    
    except Exception as e:
        # 回滚事务
        db.rollback()
        raise

def nested_transaction_example(db: Session):
    """嵌套事务示例"""
    try:
        # 外层事务
        user = User(email="user@example.com", username="testuser")
        db.add(user)
        
        # 内层事务（保存点）
        savepoint = db.begin_nested()
        try:
            post = Post(
                title="测试文章",
                slug="test-post",
                content="文章内容",
                author_id=user.id
            )
            db.add(post)
            savepoint.commit()
        except Exception:
            savepoint.rollback()
        
        db.commit()
        
        return post
    
    except Exception as e:
        db.rollback()
        raise
```

### 2. 复杂事务

```python
from sqlalchemy import text

def transfer_points(db: Session, from_user_id: int, to_user_id: int, points: int):
    """积分转账"""
    try:
        # 开始事务
        with db.begin():
            # 检查发送用户积分
            from_user = db.query(User).filter(
                User.id == from_user_id
            ).with_for_update().first()
            
            if from_user.points < points:
                raise ValueError("积分不足")
            
            # 检查接收用户
            to_user = db.query(User).filter(
                User.id == to_user_id
            ).with_for_update().first()
            
            if not to_user:
                raise ValueError("接收用户不存在")
            
            # 执行转账
            from_user.points -= points
            to_user.points += points
            
            # 记录转账历史
            transfer = Transfer(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
                points=points
            )
            db.add(transfer)
            
            # 事务自动提交
            return transfer
    
    except Exception as e:
        # 事务自动回滚
        raise

def distributed_transaction_example(db1: Session, db2: Session):
    """分布式事务（两阶段提交）"""
    try:
        # 第一阶段：准备
        db1.begin()
        db2.begin()
        
        # 在 db1 中操作
        user1 = User(email="user1@example.com", username="user1")
        db1.add(user1)
        
        # 在 db2 中操作
        user2 = User(email="user2@example.com", username="user2")
        db2.add(user2)
        
        # 第二阶段：提交
        db1.commit()
        db2.commit()
        
        return True
    
    except Exception as e:
        # 回滚所有操作
        db1.rollback()
        db2.rollback()
        raise
```

## 🧪 测试

### 1. 测试数据库配置

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

@pytest.fixture(scope="function")
def db():
    """数据库测试夹具"""
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)
    
    # 创建会话
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 删除所有表
        Base.metadata.drop_all(bind=test_engine)
```

### 2. 测试 CRUD 操作

```python
def test_create_user(db):
    """测试创建用户"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    }
    
    user = create_user(db, user_data)
    
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.is_active == True

def test_update_user(db):
    """测试更新用户"""
    # 创建用户
    user = create_user(db, {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    
    # 更新用户
    updated_user = update_user(db, user.id, {
        "full_name": "Test User"
    })
    
    assert updated_user.full_name == "Test User"

def test_delete_user(db):
    """测试删除用户"""
    # 创建用户
    user = create_user(db, {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    user_id = user.id
    
    # 删除用户
    result = delete_user(db, user_id)
    
    assert result == True
    assert db.query(User).filter(User.id == user_id).first() is None
```

### 3. 测试查询

```python
def test_get_users_with_posts(db):
    """测试获取用户及其文章"""
    # 创建用户和文章
    user = create_user(db, {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    
    post = create_post(db, {
        "title": "测试文章",
        "slug": "test-post",
        "content": "文章内容",
        "author_id": user.id
    })
    
    # 查询用户及其文章
    users = db.query(User).options(
        joinedload(User.posts)
    ).all()
    
    assert len(users) == 1
    assert len(users[0].posts) == 1
    assert users[0].posts[0].title == "测试文章"
```

## 📚 最佳实践

### 1. 连接池管理

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 配置连接池
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # 连接池大小
    max_overflow=20,       # 最大溢出连接数
    pool_timeout=30,        # 获取连接超时时间（秒）
    pool_recycle=3600,      # 连接回收时间（秒）
    pool_pre_ping=True,     # 连接前ping检查
    pool_reset_on_return='commit'  # 连接返回时重置
)

# 监控连接池状态
def monitor_connection_pool():
    """监控连接池状态"""
    pool = engine.pool
    print(f"连接池状态:")
    print(f"  总连接数: {pool.size()}")
    print(f"  空闲连接: {pool.checkedout()}")
    print(f"  溢出连接: {pool.overflow()}")
```

### 2. 会话管理

```python
from contextlib import contextmanager
from sqlalchemy.orm import Session, sessionmaker

@contextmanager
def get_db_session():
    """数据库会话上下文管理器"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# 使用示例
def with_session_example():
    """使用会话上下文管理器"""
    with get_db_session() as session:
        user = User(email="user@example.com", username="testuser")
        session.add(user)
        # 会话在退出时自动提交
```

### 3. 性能监控

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """查询执行前"""
    context._query_start_time = time.time()
    print(f"执行SQL: {statement}")

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """查询执行后"""
    total = time.time() - context._query_start_time
    print(f"执行时间: {total * 1000:.2f}ms")

# 慢查询监控
@event.listens_for(Engine, "after_cursor_execute")
def slow_query_monitor(conn, cursor, statement, parameters, context, executemany):
    """慢查询监控"""
    total = time.time() - context._query_start_time
    if total > 1.0:  # 超过1秒的查询
        print(f"慢查询检测 ({total:.2f}s): {statement}")
```

## 🔗 相关资源

- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [FastAPI + SQLAlchemy 教程](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- 《Essential SQLAlchemy》书籍