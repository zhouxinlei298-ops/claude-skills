# 聚合与 GroupBy

---

## 概述

聚合将数据从单条记录转换为汇总统计信息。本参考涵盖 GroupBy、数据透视表、交叉表和高级聚合模式，基于 pandas 2.0+。

---

## GroupBy 基础

### 基本 GroupBy

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'department': ['Eng', 'Eng', 'Sales', 'Sales', 'Eng', 'HR'],
    'team': ['Backend', 'Frontend', 'East', 'West', 'Backend', 'Recruit'],
    'employee': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'],
    'salary': [80000, 75000, 65000, 70000, 85000, 60000],
    'years': [5, 3, 7, 4, 6, 2]
})

# 单列分组单聚合
avg_salary = df.groupby('department')['salary'].mean()

# 多个聚合
stats = df.groupby('department')['salary'].agg(['mean', 'min', 'max', 'count'])

# 按多列分组
grouped = df.groupby(['department', 'team'])['salary'].mean()

# 重置索引以获取 DataFrame 而不是 Series
grouped = df.groupby('department')['salary'].mean().reset_index()
```

### 多列多聚合

```python
# 命名聚合（pandas 2.0+ 推荐）
result = df.groupby('department').agg(
    avg_salary=('salary', 'mean'),
    max_salary=('salary', 'max'),
    total_years=('years', 'sum'),
    headcount=('employee', 'count'),
)

# 字典语法（传统方式）
result = df.groupby('department').agg({
    'salary': ['mean', 'max', 'std'],
    'years': ['sum', 'mean'],
})

# 展平多级列名
result.columns = ['_'.join(col).strip() for col in result.columns.values]
```

### 自定义聚合函数

```python
# Lambda 函数
result = df.groupby('department').agg({
    'salary': lambda x: x.max() - x.min(),  # 范围
    'years': lambda x: x.quantile(0.75),    # 第 75 百分位
})

# 命名函数提高清晰度
def salary_range(x):
    return x.max() - x.min()

def coefficient_of_variation(x):
    return x.std() / x.mean() if x.mean() != 0 else 0

result = df.groupby('department').agg(
    salary_range=('salary', salary_range),
    salary_cv=('salary', coefficient_of_variation),
)

# 多个自定义函数
result = df.groupby('department')['salary'].agg([
    ('range', lambda x: x.max() - x.min()),
    ('iqr', lambda x: x.quantile(0.75) - x.quantile(0.25)),
    ('median', 'median'),
])
```

---

## Transform 和 Apply

### Transform - 返回相同形状

```python
# Transform 返回与原始索引相同的 Series
# 用于将聚合值添加回原始 DataFrame

# 添加组均值作为新列
df['dept_avg_salary'] = df.groupby('department')['salary'].transform('mean')

# 组内标准化
df['salary_zscore'] = df.groupby('department')['salary'].transform(
    lambda x: (x - x.mean()) / x.std()
)

# 组内排名
df['salary_rank'] = df.groupby('department')['salary'].transform('rank', ascending=False)

# 占组总计的百分比
df['salary_pct'] = df.groupby('department')['salary'].transform(
    lambda x: x / x.sum() * 100
)

# 用组均值填充缺失值
df['salary'] = df.groupby('department')['salary'].transform(
    lambda x: x.fillna(x.mean())
)
```

### Apply - 灵活操作

```python
# Apply 在每个组 DataFrame 上运行函数
def top_n_by_salary(group, n=2):
    return group.nlargest(n, 'salary')

top_earners = df.groupby('department').apply(top_n_by_salary, n=2)

# apply 后重置索引
top_earners = df.groupby('department', group_keys=False).apply(
    top_n_by_salary, n=2
).reset_index(drop=True)

# 复杂的组操作
def group_summary(group):
    return pd.Series({
        'headcount': len(group),
        'avg_salary': group['salary'].mean(),
        'top_earner': group.loc[group['salary'].idxmax(), 'employee'],
        'avg_tenure': group['years'].mean(),
    })

summary = df.groupby('department').apply(group_summary)
```

### Filter - 保留/移除组

```python
# 只保留满足条件的组
# 平均薪资 > 70000 的组
filtered = df.groupby('department').filter(lambda x: x['salary'].mean() > 70000)

# 成员超过 2 个的组
filtered = df.groupby('department').filter(lambda x: len(x) > 2)

# 组合条件
filtered = df.groupby('department').filter(
    lambda x: (len(x) >= 2) and (x['salary'].mean() > 65000)
)
```

---

## 数据透视表

### 基本数据透视表

```python
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=6),
    'product': ['A', 'B', 'A', 'B', 'A', 'B'],
    'region': ['East', 'East', 'West', 'West', 'East', 'West'],
    'sales': [100, 150, 120, 180, 90, 200],
    'quantity': [10, 15, 12, 18, 9, 20],
})

# 简单透视
pivot = df.pivot_table(
    values='sales',
    index='product',
    columns='region',
    aggfunc='sum'
)

# 多个值
pivot = df.pivot_table(
    values=['sales', 'quantity'],
    index='product',
    columns='region',
    aggfunc='sum'
)

# 多个聚合函数
pivot = df.pivot_table(
    values='sales',
    index='product',
    columns='region',
    aggfunc=['sum', 'mean', 'count']
)
```

### 高级数据透视表选项

```python
# 填充缺失值
pivot = df.pivot_table(
    values='sales',
    index='product',
    columns='region',
    aggfunc='sum',
    fill_value=0
)

# 添加汇总行（总计）
pivot = df.pivot_table(
    values='sales',
    index='product',
    columns='region',
    aggfunc='sum',
    margins=True,
    margins_name='Total'
)

# 多级索引
pivot = df.pivot_table(
    values='sales',
    index=['product', df['date'].dt.month],
    columns='region',
    aggfunc='sum'
)

# 仅使用已观察的分类（分类数据）
pivot = df.pivot_table(
    values='sales',
    index='product',
    columns='region',
    aggfunc='sum',
    observed=True  # pandas 2.0+ 默认值已更改
)
```

### 反透视（Melt）

```python
# 宽格式转长格式
wide_df = pd.DataFrame({
    'product': ['A', 'B'],
    'Q1_sales': [100, 150],
    'Q2_sales': [120, 180],
    'Q3_sales': [90, 200],
})

# Melt 转长格式
long_df = pd.melt(
    wide_df,
    id_vars=['product'],
    value_vars=['Q1_sales', 'Q2_sales', 'Q3_sales'],
    var_name='quarter',
    value_name='sales'
)

# 清理 quarter 列
long_df['quarter'] = long_df['quarter'].str.replace('_sales', '')
```

---

## 交叉表

### 基本交叉表

```python
df = pd.DataFrame({
    'gender': ['M', 'F', 'M', 'F', 'M', 'F', 'M', 'M'],
    'department': ['Eng', 'Eng', 'Sales', 'Sales', 'Eng', 'HR', 'HR', 'Eng'],
    'level': ['Senior', 'Junior', 'Senior', 'Senior', 'Junior', 'Junior', 'Senior', 'Junior'],
})

# 简单交叉表（计数）
ct = pd.crosstab(df['gender'], df['department'])

# 归一化交叉表
ct_pct = pd.crosstab(df['gender'], df['department'], normalize='all')  # 总计
ct_pct = pd.crosstab(df['gender'], df['department'], normalize='index')  # 行
ct_pct = pd.crosstab(df['gender'], df['department'], normalize='columns')  # 列

# 带汇总
ct = pd.crosstab(df['gender'], df['department'], margins=True)

# 多级
ct = pd.crosstab(
    [df['gender'], df['level']],
    df['department']
)
```

### 带聚合的交叉表

```python
df['salary'] = [80000, 75000, 65000, 70000, 85000, 60000, 72000, 78000]

# 带值和聚合的交叉表
ct = pd.crosstab(
    df['gender'],
    df['department'],
    values=df['salary'],
    aggfunc='mean'
)

# 多个聚合
ct = pd.crosstab(
    df['gender'],
    df['department'],
    values=df['salary'],
    aggfunc=['mean', 'sum', 'count']
)
```

---

## 窗口函数与 GroupBy

### 滚动聚合

```python
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=10),
    'product': ['A', 'B'] * 5,
    'sales': [100, 150, 110, 160, 120, 170, 130, 180, 140, 190],
})

# 组内滚动均值
df['rolling_avg'] = df.groupby('product')['sales'].transform(
    lambda x: x.rolling(window=3, min_periods=1).mean()
)

# 扩展聚合
df['cumulative_sales'] = df.groupby('product')['sales'].transform('cumsum')

df['expanding_avg'] = df.groupby('product')['sales'].transform(
    lambda x: x.expanding().mean()
)

# 组内排名
df['sales_rank'] = df.groupby('product')['sales'].rank(method='dense')
```

### Shift 和 Diff

```python
# 组内前一个值
df['prev_sales'] = df.groupby('product')['sales'].shift(1)

# 下一个值
df['next_sales'] = df.groupby('product')['sales'].shift(-1)

# 期间变化
df['sales_change'] = df.groupby('product')['sales'].diff()

# 百分比变化
df['sales_pct_change'] = df.groupby('product')['sales'].pct_change()
```

---

## 常见聚合模式

### 汇总统计

```python
# 按组的全面汇总
def full_summary(group):
    return pd.Series({
        'count': len(group),
        'mean': group['salary'].mean(),
        'std': group['salary'].std(),
        'min': group['salary'].min(),
        'q25': group['salary'].quantile(0.25),
        'median': group['salary'].median(),
        'q75': group['salary'].quantile(0.75),
        'max': group['salary'].max(),
        'sum': group['salary'].sum(),
    })

summary = df.groupby('department').apply(full_summary)
```

### 每组 Top N

```python
# 每个部门薪资最高的 2 人
top_2 = df.groupby('department', group_keys=False).apply(
    lambda x: x.nlargest(2, 'salary')
)

# 排序后使用 head
top_2 = df.sort_values('salary', ascending=False).groupby(
    'department', group_keys=False
).head(2)

# 底部 N
bottom_2 = df.groupby('department', group_keys=False).apply(
    lambda x: x.nsmallest(2, 'salary')
)
```

### 每组首/末行

```python
# 每组第一行
first = df.groupby('department').first()

# 每组最后一行
last = df.groupby('department').last()

# 排序后的第一行
first_by_salary = df.sort_values('salary', ascending=False).groupby(
    'department'
).first()

# 第 n 行
nth = df.groupby('department').nth(1)  # 第二行（0 索引）
```

### 累积操作

```python
# 累积和
df['cum_sales'] = df.groupby('department')['salary'].cumsum()

# 累积最大/最小
df['cum_max'] = df.groupby('department')['salary'].cummax()
df['cum_min'] = df.groupby('department')['salary'].cummin()

# 累积计数
df['cum_count'] = df.groupby('department').cumcount() + 1

# 累积占总计百分比
df['running_pct'] = df.groupby('department')['salary'].transform(
    lambda x: x.cumsum() / x.sum() * 100
)
```

---

## GroupBy 性能技巧

### 高效 GroupBy 操作

```python
# 预排序以加快 groupby 操作
df = df.sort_values('department')
grouped = df.groupby('department', sort=False)  # 已排序

# 分类列使用 observed=True（pandas 2.0+ 默认值）
df['department'] = df['department'].astype('category')
grouped = df.groupby('department', observed=True)['salary'].mean()

# 尽可能避免 apply - 使用内置聚合
# 较慢：
result = df.groupby('department')['salary'].apply(lambda x: x.sum())
# 较快：
result = df.groupby('department')['salary'].sum()

# 自定义聚合使用 numba（如果可用）
@numba.jit(nopython=True)
def custom_agg(values):
    return values.sum() / len(values)
```

### 内存高效聚合

```python
# 对于大型 DataFrame，分别计算聚合
groups = df.groupby('department')

means = groups['salary'].mean()
sums = groups['salary'].sum()
counts = groups.size()

result = pd.DataFrame({
    'mean': means,
    'sum': sums,
    'count': counts
})

# 避免创建中间大型 DataFrame
# 错误：创建完整的转换 DataFrame
df['z_score'] = (df['salary'] - df.groupby('department')['salary'].transform('mean')) / df.groupby('department')['salary'].transform('std')

# 更好：计算一次
group_stats = df.groupby('department')['salary'].agg(['mean', 'std'])
df = df.merge(group_stats, on='department')
df['z_score'] = (df['salary'] - df['mean']) / df['std']
```

---

## 最佳实践总结

1. **使用命名聚合** - 比字典语法更清晰
2. **明智选择 transform vs apply** - Transform 保持相同形状，apply 更灵活
3. **预排序提升性能** - 排序后使用 `sort=False`
4. **优先使用内置聚合** - 比 lambda/apply 更快
5. **使用 observed=True** - 特别是分类数据
6. **需要时重置索引** - 让 DataFrame 更易操作
7. **验证分组计数** - 检查意外的分组

---

## 需要避免的反模式

```python
# 错误：手动迭代分组
for name, group in df.groupby('department'):
    # 处理组
    pass

# 正确：使用向量化操作
df.groupby('department').agg(...)

# 错误：多次 groupby 调用
df.groupby('dept')['salary'].mean()
df.groupby('dept')['salary'].sum()
df.groupby('dept')['salary'].count()

# 正确：单次 groupby，多个聚合
df.groupby('dept')['salary'].agg(['mean', 'sum', 'count'])

# 错误：简单聚合使用 apply
df.groupby('dept')['salary'].apply(np.mean)

# 正确：内置方法
df.groupby('dept')['salary'].mean()
```

---

## 相关参考

- `dataframe-operations.md` - 聚合前过滤
- `merging-joining.md` - 将聚合结果连接回来
- `performance-optimization.md` - 优化大规模聚合
