# 性能优化

---

## 概述

优化 pandas 性能对于生产工作流至关重要。本参考涵盖内存优化、向量化、分块处理和性能分析，基于 pandas 2.0+。

---

## 内存分析

### 检查内存使用

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'id': range(1_000_000),
    'name': ['user_' + str(i) for i in range(1_000_000)],
    'category': np.random.choice(['A', 'B', 'C', 'D'], 1_000_000),
    'value': np.random.randn(1_000_000),
    'count': np.random.randint(0, 100, 1_000_000),
})

# 基本内存信息
print(df.info(memory_usage='deep'))

# 按列的详细内存
memory_usage = df.memory_usage(deep=True)
print(memory_usage)
print(f"Total: {memory_usage.sum() / 1e6:.2f} MB")

# 内存占总量的百分比
memory_pct = (memory_usage / memory_usage.sum() * 100).round(2)
print(memory_pct)
```

### 内存分析函数

```python
def memory_profile(df: pd.DataFrame) -> pd.DataFrame:
    """按列分析内存使用并提供优化建议。"""
    memory_bytes = df.memory_usage(deep=True)

    profile = pd.DataFrame({
        'dtype': df.dtypes,
        'non_null': df.count(),
        'null_count': df.isna().sum(),
        'unique': df.nunique(),
        'memory_mb': (memory_bytes / 1e6).round(3),
    })

    # 添加优化建议
    suggestions = []
    for col in df.columns:
        dtype = df[col].dtype
        nunique = df[col].nunique()

        if dtype == 'object':
            if nunique / len(df) < 0.5:  # 少于 50% 唯一值
                suggestions.append(f"Convert to category (only {nunique} unique)")
            else:
                suggestions.append("Consider string dtype")
        elif dtype == 'int64':
            if df[col].max() < 2**31 and df[col].min() >= -2**31:
                suggestions.append("Downcast to int32")
            if df[col].max() < 2**15 and df[col].min() >= -2**15:
                suggestions.append("Downcast to int16")
        elif dtype == 'float64':
            suggestions.append("Consider float32 if precision allows")
        else:
            suggestions.append("OK")

    profile['suggestion'] = suggestions
    return profile

print(memory_profile(df))
```

---

## 内存优化技术

### 降低数值类型精度

```python
# 自动降低整数精度
df['count'] = pd.to_numeric(df['count'], downcast='integer')

# 自动降低浮点精度
df['value'] = pd.to_numeric(df['value'], downcast='float')

# 手动降低精度函数
def downcast_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """通过降低数值类型精度减少内存。"""
    df = df.copy()

    for col in df.select_dtypes(include=['int']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')

    for col in df.select_dtypes(include=['float']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')

    return df

df_optimized = downcast_dtypes(df)
print(f"Before: {df.memory_usage(deep=True).sum() / 1e6:.2f} MB")
print(f"After: {df_optimized.memory_usage(deep=True).sum() / 1e6:.2f} MB")
```

### 使用分类类型

```python
# 将低基数字符串列转换为分类类型
# 唯一值远少于总行数时特别有效

# 转换前
print(f"Object dtype: {df['category'].memory_usage(deep=True) / 1e6:.2f} MB")

# 转换后
df['category'] = df['category'].astype('category')
print(f"Category dtype: {df['category'].memory_usage(deep=True) / 1e6:.2f} MB")

# 自动转换低基数列
def optimize_categories(df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """如果唯一值比例 < threshold，将 object 列转换为 category。"""
    df = df.copy()

    for col in df.select_dtypes(include=['object']).columns:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio < threshold:
            df[col] = df[col].astype('category')

    return df
```

### 稀疏数据类型

```python
# 用于有大量重复值的数据（特别是零/NaN）
sparse_series = pd.arrays.SparseArray([0, 0, 1, 0, 0, 0, 2, 0, 0, 0])

# 创建稀疏 DataFrame
df_sparse = pd.DataFrame({
    'sparse_col': pd.arrays.SparseArray([0] * 9000 + [1] * 1000),
    'dense_col': [0] * 9000 + [1] * 1000,
})

print(f"Sparse: {df_sparse['sparse_col'].memory_usage() / 1e6:.4f} MB")
print(f"Dense: {df_sparse['dense_col'].memory_usage() / 1e6:.4f} MB")
```

### 可空类型（pandas 2.0+）

```python
# 使用可空类型进行正确的空值处理和内存效率
df = df.astype({
    'id': 'Int32',          # 可空 int32
    'count': 'Int16',       # 可空 int16
    'value': 'Float32',     # 可空 float32
    'name': 'string',       # 可空字符串（更节省内存）
    'category': 'category', # 分类
})

# Arrow 支持的类型（更好的内存效率）（pandas 2.0+）
df['name'] = df['name'].astype('string[pyarrow]')
df['category'] = df['category'].astype('category')
```

---

## 向量化

### 用向量化操作替换循环

```python
# 错误：行迭代（极慢）
result = []
for idx, row in df.iterrows():
    if row['value'] > 0:
        result.append(row['value'] * 2)
    else:
        result.append(0)
df['result'] = result

# 正确：使用 np.where 向量化
df['result'] = np.where(df['value'] > 0, df['value'] * 2, 0)

# 正确：使用布尔索引向量化
df['result'] = 0
df.loc[df['value'] > 0, 'result'] = df.loc[df['value'] > 0, 'value'] * 2
```

### 使用 np.select 处理多条件

```python
# 错误：apply 中的嵌套 if-else
def categorize(row):
    if row['value'] < -1:
        return 'very_low'
    elif row['value'] < 0:
        return 'low'
    elif row['value'] < 1:
        return 'medium'
    else:
        return 'high'

df['category'] = df.apply(categorize, axis=1)  # 慢！

# 正确：使用 np.select 向量化
conditions = [
    df['value'] < -1,
    df['value'] < 0,
    df['value'] < 1,
]
choices = ['very_low', 'low', 'medium']
df['category'] = np.select(conditions, choices, default='high')
```

### 字符串操作 - 向量化

```python
# 错误：使用 apply 进行字符串操作
df['upper_name'] = df['name'].apply(lambda x: x.upper())

# 正确：向量化字符串方法
df['upper_name'] = df['name'].str.upper()

# 组合多个字符串操作
df['processed'] = (
    df['name']
    .str.strip()
    .str.lower()
    .str.replace(r'\s+', '_', regex=True)
)
```

### 尽可能避免 apply()

```python
# 错误：使用 apply 进行行计算
df['total'] = df.apply(lambda row: row['a'] + row['b'] + row['c'], axis=1)

# 正确：直接向量化操作
df['total'] = df['a'] + df['b'] + df['c']

# 错误：使用 apply 进行元素操作
df['squared'] = df['value'].apply(lambda x: x ** 2)

# 正确：向量化
df['squared'] = df['value'] ** 2

# apply 适合的场景：复杂自定义逻辑
def complex_calculation(row):
    # 多个依赖和条件逻辑
    if row['type'] == 'A':
        return row['value'] * row['multiplier'] + row['offset']
    else:
        return row['value'] / row['divisor'] - row['adjustment']

# 如果性能关键，考虑重写为向量化
```

---

## 分块处理

### 分块读取大文件

```python
# 分块读取 CSV
chunk_size = 100_000
chunks = []

for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    # 处理每个块
    processed = chunk[chunk['value'] > 0]  # 过滤
    processed = processed.groupby('category')['value'].sum()  # 聚合
    chunks.append(processed)

# 合并结果
result = pd.concat(chunks).groupby(level=0).sum()
```

### 分块处理函数

```python
def process_large_csv(
    filepath: str,
    chunk_size: int = 100_000,
    filter_func=None,
    agg_func=None,
) -> pd.DataFrame:
    """分块处理大型 CSV 文件。"""
    results = []

    for chunk in pd.read_csv(filepath, chunksize=chunk_size):
        # 应用过滤器（如果提供）
        if filter_func:
            chunk = filter_func(chunk)

        # 应用聚合（如果提供）
        if agg_func:
            chunk = agg_func(chunk)

        results.append(chunk)

    # 合并结果
    combined = pd.concat(results, ignore_index=True)

    # 如需要重新聚合
    if agg_func:
        combined = agg_func(combined)

    return combined

# 使用示例
result = process_large_csv(
    'large_file.csv',
    chunk_size=50_000,
    filter_func=lambda df: df[df['value'] > 0],
    agg_func=lambda df: df.groupby('category').agg({'value': 'sum'}),
)
```

### 内存高效迭代

```python
# 必须迭代时，使用 itertuples（而非 iterrows）
# itertuples 比 iterrows 快 10-100 倍

# 错误：iterrows
for idx, row in df.iterrows():
    process(row['name'], row['value'])

# 更好：itertuples
for row in df.itertuples():
    process(row.name, row.value)  # 作为属性访问

# 最佳：向量化操作（完全避免迭代）
```

---

## 查询优化

### 高效过滤

```python
# 顺序很重要 - 先过滤，后计算
# 错误：在所有行上计算，然后过滤
df['expensive_calc'] = df['a'] * df['b'] + np.sin(df['c'])
result = df[df['category'] == 'A']

# 正确：先过滤，在子集上计算
mask = df['category'] == 'A'
result = df[mask].copy()
result['expensive_calc'] = result['a'] * result['b'] + np.sin(result['c'])
```

### 使用 query() 提升性能

```python
# query() 对大型 DataFrame 可以更快（使用 numexpr）
# 传统布尔索引
result = df[(df['value'] > 0) & (df['category'] == 'A')]

# query() 语法（大数据更快）
result = df.query('value > 0 and category == "A"')

# 带变量
threshold = 0
cat = 'A'
result = df.query('value > @threshold and category == @cat')
```

### eval() 用于复杂表达式

```python
# eval() 使用 numexpr 加速计算
# 标准 pandas
df['result'] = df['a'] + df['b'] * df['c'] - df['d']

# 使用 eval（大型 DataFrame 更快）
df['result'] = pd.eval('df.a + df.b * df.c - df.d')

# 使用 inplace 参数原地计算
df.eval('result = a + b * c - d', inplace=True)
```

---

## GroupBy 优化

### 预排序加速 GroupBy

```python
# 先按分组列排序
df = df.sort_values('category')

# 使用 sort=False 因为已排序
result = df.groupby('category', sort=False)['value'].mean()
```

### 使用内置聚合

```python
# 错误：通过 apply 使用自定义函数
result = df.groupby('category')['value'].apply(lambda x: x.mean())

# 正确：内置聚合
result = df.groupby('category')['value'].mean()

# 可用的内置聚合：
# sum, mean, median, min, max, std, var, count, first, last, nth
# size, sem, prod, cumsum, cummax, cummin, cumprod
```

### 已观察的分类

```python
# 对于分类列，使用 observed=True（pandas 2.0+ 默认值）
df['category'] = df['category'].astype('category')

# 避免为未观察到的分类计算
result = df.groupby('category', observed=True)['value'].mean()
```

---

## I/O 优化

### 高效文件格式

```python
# Parquet - 最适合分析工作负载
df.to_parquet('data.parquet', compression='snappy')
df = pd.read_parquet('data.parquet')

# Feather - 最适合 pandas 数据交换
df.to_feather('data.feather')
df = pd.read_feather('data.feather')

# 带优化的 CSV
df.to_csv('data.csv', index=False)
df = pd.read_csv(
    'data.csv',
    dtype={'category': 'category', 'count': 'int32'},
    usecols=['id', 'category', 'value'],  # 仅需要的列
    nrows=10000,  # 测试时限制行数
)
```

### 读取时指定数据类型

```python
# 预先指定数据类型以避免推断开销
dtypes = {
    'id': 'int32',
    'name': 'string',
    'category': 'category',
    'value': 'float32',
    'count': 'int16',
}

df = pd.read_csv('data.csv', dtype=dtypes)

# 高效解析日期
df = pd.read_csv(
    'data.csv',
    dtype=dtypes,
    parse_dates=['date_column'],
    date_format='%Y-%m-%d',  # 显式格式更快
)
```

---

## 性能分析和基准测试

### 操作计时

```python
import time

# 简单计时
start = time.time()
result = df.groupby('category')['value'].mean()
elapsed = time.time() - start
print(f"Elapsed: {elapsed:.4f} seconds")

# 在 Jupyter 中使用 %%timeit
# %%timeit
# df.groupby('category')['value'].mean()
```

### 内存分析

```python
# 跟踪操作前后内存
import tracemalloc

tracemalloc.start()

# 你的操作
df_result = df.groupby('category').agg({'value': 'sum'})

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1e6:.2f} MB")
print(f"Peak memory: {peak / 1e6:.2f} MB")

tracemalloc.stop()
```

### 比较模板

```python
def benchmark_operations(df: pd.DataFrame, operations: dict, n_runs: int = 5):
    """对多个操作进行基准测试。"""
    results = {}

    for name, func in operations.items():
        times = []
        for _ in range(n_runs):
            start = time.time()
            func(df)
            times.append(time.time() - start)

        results[name] = {
            'mean': np.mean(times),
            'std': np.std(times),
            'min': np.min(times),
        }

    return pd.DataFrame(results).T

# 使用示例
operations = {
    'iterrows': lambda df: [row['value'] for _, row in df.iterrows()],
    'itertuples': lambda df: [row.value for row in df.itertuples()],
    'vectorized': lambda df: df['value'].tolist(),
}

benchmark_results = benchmark_operations(df.head(10000), operations)
print(benchmark_results)
```

---

## 最佳实践总结

1. **先分析** - 优化前识别真正的瓶颈
2. **使用适当的数据类型** - int32/float32/category 节省内存
3. **一切向量化** - 尽可能避免循环和 apply
4. **尽早过滤** - 在昂贵操作前减少数据
5. **大文件分块处理** - 分成可管理的块
6. **使用高效文件格式** - Parquet/Feather 优于 CSV
7. **利用内置方法** - 比自定义函数更快

---

## 性能检查清单

部署 pandas 代码前：

- [ ] 使用 `memory_usage(deep=True)` 分析内存
- [ ] 优化数据类型（降低精度、分类类型）
- [ ] 热路径中没有 iterrows/itertuples
- [ ] GroupBy 使用内置聚合
- [ ] 大文件分块处理
- [ ] 计算前先过滤
- [ ] 使用适当的文件格式
- [ ] 使用代表性数据量进行基准测试

---

## 反模式总结

| 反模式 | 替代方案 |
|--------|----------|
| `iterrows()` 用于计算 | 向量化操作 |
| `apply(lambda)` 用于简单操作 | 内置方法 |
| 加载整个大文件 | 分块读取 |
| 低基数字符串列 | 分类类型 |
| 小整数使用 int64 | int32/int16 |
| 多次分别过滤 | 合并布尔掩码 |
| 重复 groupby 调用 | 单次 groupby 多个聚合 |

---

## 相关参考

- `dataframe-operations.md` - 高效索引和过滤
- `aggregation-groupby.md` - 优化的聚合模式
- `merging-joining.md` - 高效的合并策略
