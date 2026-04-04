# Python 性能优化指南

## 📊 性能分析基础

### 1. 性能分析工具

```python
# 使用 cProfile 进行性能分析
import cProfile
import pstats
from io import StringIO

def profile_function(func, *args, **kwargs):
    """性能分析装饰器"""
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        # 输出统计结果
        s = StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # 打印前10个最耗时的函数
        print(s.getvalue())
        
        return result
    return wrapper

# 使用示例
@profile_function
def process_large_dataset():
    """处理大型数据集"""
    data = range(1_000_000)
    return sum(x * 2 for x in data)
```

### 2. 内存分析

```python
# 使用 memory_profiler 分析内存使用
from memory_profiler import profile

@profile
def memory_intensive_function():
    """内存密集型函数"""
    # 创建大型列表
    large_list = [i for i in range(1_000_000)]
    
    # 创建字典
    large_dict = {str(i): i for i in range(100_000)}
    
    # 返回结果（实际应用中会进一步处理）
    return len(large_list), len(large_dict)

# 使用 line_profiler 分析每行代码的执行时间
from line_profiler import LineProfiler

def profile_lines(func):
    """代码行级性能分析装饰器"""
    def wrapper(*args, **kwargs):
        profiler = LineProfiler()
        profiler_wrapper = profiler(func)
        result = profiler_wrapper(*args, **kwargs)
        profiler.print_stats()
        return result
    return wrapper
```

## 🚀 Pythonic 性能优化

### 1. 列表推导 vs for 循环

```python
# 不推荐：低效的 for 循环
result = []
for i in range(1_000_000):
    if i % 2 == 0:
        result.append(i * 2)

# 推荐：使用列表推导
result = [i * 2 for i in range(1_000_000) if i % 2 == 0]
```

### 2. 生成器 vs 列表

```python
# 列表：占用大量内存
def generate_squares_list(n):
    """生成平方数列表"""
    return [x * x for x in range(n)]

# 生成器：惰性计算，节省内存
def generate_squares_generator(n):
    """生成平方数生成器"""
    for x in range(n):
        yield x * x

# 使用示例
# 列表：一次性加载所有数据到内存
squares_list = generate_squares_list(10_000_000)

# 生成器：逐个生成，内存占用恒定
squares_gen = generate_squares_generator(10_000_000)
for square in squares_gen:
    process(square)  # 逐个处理
```

### 3. 字符串拼接优化

```python
# 不推荐：使用 + 拼接字符串
result = ""
for part in parts:
    result += part

# 推荐：使用 join
result = "".join(parts)

# 对于大量拼接：使用 io.StringIO
from io import StringIO

def build_large_string(parts):
    """构建大型字符串"""
    buffer = StringIO()
    for part in parts:
        buffer.write(part)
    return buffer.getvalue()
```

### 4. 属性访问优化

```python
# 使用 __slots__ 减少内存占用
class PointWithSlots:
    __slots__ = ['x', 'y']  # 固定属性列表
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PointWithoutSlots:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# 性能对比
# PointWithSlots 占用更少内存，属性访问更快
```

## 🎯 数据结构优化

### 1. 列表操作优化

```python
# 避免列表的 O(n) 查找
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 不推荐：in 操作符对列表是 O(n)
if 5 in numbers:
    pass

# 推荐：使用集合（O(1) 查找）
numbers_set = set(numbers)
if 5 in numbers_set:
    pass

# 使用字典进行快速查找
lookup_dict = {i: True for i in numbers}
if 5 in lookup_dict:
    pass
```

### 2. 字典优化

```python
# 使用 defaultdict 简化代码
from collections import defaultdict

# 不推荐
word_count = {}
for word in words:
    if word in word_count:
        word_count[word] += 1
    else:
        word_count[word] = 1

# 推荐
word_count = defaultdict(int)
for word in words:
    word_count[word] += 1

# 使用 Counter 进行计数
from collections import Counter
word_count = Counter(words)
```

### 3. NumPy 向量化操作

```python
import numpy as np

# 不推荐：循环操作
result = []
for x in array:
    result.append(x * 2)

# 推荐：向量化操作
result = array * 2

# 更复杂的向量化操作
# 计算 sqrt(a^2 + b^2)
result = np.sqrt(a**2 + b**2)

# 使用 NumPy 的聚合函数
total = np.sum(array)
mean = np.mean(array)
std = np.std(array)
```

## ⚡ 异步编程优化

### 1. asyncio 最佳实践

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    """获取单个URL"""
    async with session.get(url) as response:
        return await response.text()

async def fetch_multiple_urls(urls):
    """并发获取多个URL"""
    # 创建连接池
    connector = aiohttp.TCPConnector(limit=100)  # 限制并发数
    timeout = aiohttp.ClientTimeout(total=30)  # 设置超时
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout
    ) as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# 使用信号量控制并发
async def bounded_fetch(urls, max_concurrent=10):
    """限制并发的获取"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(url):
        async with semaphore:
            return await fetch_url(url)
    
    tasks = [fetch_with_semaphore(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### 2. 异步上下文管理器

```python
# 自定义异步上下文管理器
class AsyncTimer:
    async def __aenter__(self):
        self.start = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end = time.time()
        print(f"执行时间: {self.end - self.start:.2f}秒")

# 使用示例
async def async_operation():
    async with AsyncTimer():
        await asyncio.sleep(1)
        # 执行异步操作

# 异步文件操作
async def process_file_async():
    async with aiofiles.open('large_file.txt', 'r') as f:
        async for line in f:
            process_line(line)
```

## 🗄️ 数据库优化

### 1. SQLAlchemy 查询优化

```python
# 避免 N+1 查询问题
from sqlalchemy.orm import joinedload, selectinload

# 不推荐：N+1 查询
users = db.query(User).all()
for user in users:
    posts = db.query(Post).filter(Post.user_id == user.id).all()

# 推荐：使用 joinedload
users = db.query(User).options(joinedload(User.posts)).all()

# 推荐：使用 selectinload（适合多对多关系）
users = db.query(User).options(selectinload(User.tags)).all()

# 批量操作
# 不推荐
for user in users:
    db.add(user)
    db.commit()  # 每次提交一个事务

# 推荐
db.add_all(users)
db.commit()  # 一次提交所有数据
```

### 2. 索引优化

```python
# 确保查询使用索引
# 创建复合索引
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), index=True)  # 单列索引
    created_at = Column(DateTime)
    status = Column(String(20))
    
    # 复合索引
    __table_args__ = (
        Index('idx_user_status_created', 'status', 'created_at'),
    )

# 查询时使用索引
# 会使用 idx_user_status_created 索引
users = db.query(User).filter(
    User.status == 'active',
    User.created_at > '2024-01-01'
).all()
```

### 3. 连接池配置

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 创建带连接池的引擎
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,        # 连接池大小
    max_overflow=10,      # 最大溢出连接数
    pool_timeout=30,      # 获取连接超时时间
    pool_recycle=3600,   # 连接回收时间（秒）
    pool_pre_ping=True,  # 连接前ping检查
)
```

## 🔧 Python 运行时优化

### 1. 虚拟环境优化

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装优化后的 Python
# 使用 pyenv 安装特定版本的 Python
pyenv install 3.11.0
pyenv local 3.11.0
```

### 2. 编译优化

```python
# 使用 py_compile 预编译
import py_compile
py_compile.compile('module.py', optimize=2)  # optimize=2 启用所有优化

# 使用 Cython 扩展性能
# setup.py
from distutils.core import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("module.py")
)

# 编译
python setup.py build_ext --inplace
```

### 3. JIT 编译

```python
# 使用 numba 进行 JIT 编译
from numba import jit

@jit(nopython=True)
def compute_sums(values):
    """使用 JIT 编译的函数"""
    total = 0
    for value in values:
        total += value ** 2
    return total

# 使用 PyPy 获得更好的性能
# 直接使用 pypy 运行脚本
# pypy your_script.py
```

## 📈 高级优化技术

### 1. 缓存策略

```python
from functools import lru_cache
import pickle
import redis

# 内存缓存
@lru_cache(maxsize=128)
def expensive_computation(x):
    """缓存计算结果"""
    # 复杂计算
    return x * x * x

# Redis 缓存
redis_client = redis.Redis()

def cached_redis_call(key, func, *args, **kwargs, ttl=3600):
    """带 Redis 缓存的函数调用"""
    # 尝试从缓存获取
    cached_result = redis_client.get(key)
    if cached_result:
        return pickle.loads(cached_result)
    
    # 执行函数
    result = func(*args, **kwargs)
    
    # 存入缓存
    redis_client.setex(key, ttl, pickle.dumps(result))
    
    return result

# 使用 functools.total_ordering 简化类比较
@total_ordering
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def __eq__(self, other):
        return self.age == other.age
    
    def __lt__(self, other):
        return self.age < other.age
```

### 2. 多进程与多线程

```python
import concurrent.futures
import multiprocessing

# 多线程处理 I/O 密集型任务
def process_data_threading(data):
    """使用线程池处理数据"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_item, item) for item in data]
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results

# 多进程处理 CPU 密集型任务
def process_data_multiprocessing(data):
    """使用进程池处理数据"""
    with multiprocessing.Pool() as pool:
        results = pool.map(process_item, data)
    return results

# 使用 asyncio 处理大量并发请求
async def process_requests(urls):
    """处理大量并发请求"""
    semaphore = asyncio.Semaphore(100)  # 限制并发数
    
    async def fetch_with_semaphore(url):
        async with semaphore:
            return await fetch(url)
    
    tasks = [fetch_with_semaphore(url) for url in urls]
    return await asyncio.gather(*tasks)
```

### 3. 内存优化技巧

```python
# 使用 __slots__ 减少内存占用
class OptimizedClass:
    __slots__ = ['x', 'y', 'z']  # 固定属性列表
    
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

# 使用 array 模块处理数值数组
from array import array
# 比 list 更节省内存
numbers = array('i', [1, 2, 3, 4, 5])

# 使用 mmap 处理大文件
import mmap

def process_large_file(filename):
    """使用内存映射处理大文件"""
    with open(filename, 'r+b') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            # 直接访问文件内容而不全部加载到内存
            for line in iter(mm.readline, b""):
                process_line(line.decode('utf-8'))
```

## 📊 性能监控

### 1. 性能监控装饰器

```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time = end_time - start_time
        print(f"{func.__name__} 执行时间: {execution_time:.4f}秒")
        
        # 可以在这里添加更复杂的监控逻辑
        # 比如发送到监控系统、记录日志等
        
        return result
    return wrapper

# 使用示例
@monitor_performance
def fibonacci(n):
    """斐波那契数列计算"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

### 2. 内存使用监控

```python
import psutil
import os

def monitor_memory():
    """监控当前进程的内存使用"""
    process = psutil.Process(os.getpid())
    
    # 内存信息
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # 内存使用百分比
    memory_percent = process.memory_percent()
    print(f"内存使用率: {memory_percent:.2f}%")
    
    return memory_info.rss

# 使用示例
def memory_intensive_task():
    """内存密集型任务"""
    start_memory = monitor_memory()
    
    # 创建大型数据结构
    large_list = [i for i in range(1_000_000)]
    large_dict = {str(i): i for i in range(100_000)}
    
    end_memory = monitor_memory()
    print(f"内存增长: {(end_memory - start_memory) / 1024 / 1024:.2f} MB")
```

### 3. 代码复杂度分析

```python
# 使用 radon 分析代码复杂度
"""
安装: pip install radon

使用命令:
radon cc your_file.py -a -nb
radon cc your_project/ -a -nb
"""

# Cyclomatic Complexity (圈复杂度) 最佳实践:
# - 10以下: 易维护
# - 10-20: 需要重构
# - 20以上: 难以维护

def analyze_complexity():
    """圈复杂度分析"""
    # 避免过深的嵌套
    def good_function(x):
        # 嵌套层次少，易于理解
        if x > 0:
            return x * 2
        else:
            return x / 2
    
    # 避免高复杂度函数
    def bad_function(x, y, z, a, b):
        # 圈复杂度过高
        if x > 0:
            if y < 0:
                if z == 0:
                    if a:
                        if b:
                            return 1
                        else:
                            return 2
                    else:
                        return 3
                else:
                    return 4
            else:
                return 5
        else:
            return 6
```

## 🎯 优化清单

### 1. 代码层面优化

- [ ] 使用列表推导替代 for 循环
- [ ] 使用生成器处理大数据集
- [ ] 使用集合/字典进行快速查找
- [ ] 避免字符串拼接，使用 join
- [ ] 使用 `__slots__` 减少内存占用
- [ ] 使用 NumPy 进行向量化操作

### 2. 数据库优化

- [ ] 避免 N+1 查询问题
- [ ] 创建合适的索引
- [ ] 使用批量操作
- [ ] 配置连接池
- [ ] 使用查询优化技术

### 3. 异步优化

- [ ] 使用 asyncio 进行并发处理
- [ ] 使用信号量控制并发数
- [ ] 使用异步上下文管理器
- [ ] 配置合理的超时设置

### 4. 内存优化

- [ ] 使用内存分析工具识别瓶颈
- [ ] 使用生成器惰性计算
- [ ] 使用内存映射处理大文件
- [ ] 使用 `array` 模块处理数值数据

### 5. 监控与调试

- [ ] 使用性能分析工具
- [ ] 添加性能监控装饰器
- [ ] 监控内存使用情况
- [ ] 分析代码复杂度

## 📚 性能优化资源

### 工具推荐

- **cProfile**: Python 内置性能分析器
- **memory_profiler**: 内存使用分析
- **line_profiler**: 代码行级性能分析
- **py-spy**: 采样性能分析器
- **memory_profiler**: 内存分析
- **objgraph**: 对象引用分析
- **viztracer**: 可视化追踪工具

### 书籍推荐

- 《Python性能优化权威指南》
- 《High Performance Python》
- 《Python Cookbook》（第3版）

### 在线资源

- Python 官方文档性能优化部分
- Real Python 性能优化文章
- PyCon 性能优化演讲视频