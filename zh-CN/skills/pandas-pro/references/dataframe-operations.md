# DataFrame 操作

---

## 概述

DataFrame 操作是 pandas 工作的基础。本参考涵盖索引、选择、过滤和排序，基于 pandas 2.0+ 最佳实践。

---

## 索引和选择

### 使用 `.loc[]` 进行基于标签的选择

使用 `.loc[]` 进行基于标签的索引。始终优先于链式索引。

```python
import pandas as pd
import numpy as np

# 示例 DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'age': [25, 30, 35, 28],
    'salary': [50000, 60000, 70000, 55000],
    'department': ['Engineering', 'Sales', 'Engineering', 'Marketing']
}, index=['a', 'b', 'c', 'd'])

# 单个值
value = df.loc['a', 'name']  # 'Alice'

# 单行（返回 Series）
row = df.loc['a']

# 多行
rows = df.loc[['a', 'c']]

# 行和列切片（两端都包含）
subset = df.loc['a':'c', 'name':'salary']

# 使用 .loc 进行布尔索引
adults = df.loc[df['age'] >= 30]

# 布尔索引配合列选择
adults_names = df.loc[df['age'] >= 30, 'name']

# 多个条件
engineering_seniors = df.loc[
    (df['department'] == 'Engineering') & (df['age'] >= 30),
    ['name', 'salary']
]
```

### 使用 `.iloc[]` 进行基于位置的选择

使用 `.iloc[]` 进行整数位置索引。

```python
# 按位置获取单个值
value = df.iloc[0, 0]  # 第一行，第一列

# 按位置获取单行
first_row = df.iloc[0]

# 切片行（不包含末尾，类似 Python）
first_three = df.iloc[:3]

# 按位置选择特定行和列
subset = df.iloc[[0, 2], [0, 2]]  # 行 0,2 和列 0,2

# 范围选择
block = df.iloc[1:3, 0:2]  # 行 1-2，列 0-1
```

### 何时使用 `.loc[]` vs `.iloc[]`

| 场景 | 使用 | 示例 |
|------|------|------|
| 已知列名 | `.loc[]` | `df.loc[:, 'name']` |
| 按条件过滤 | `.loc[]` | `df.loc[df['age'] > 25]` |
| 前/后 N 行 | `.iloc[]` | `df.iloc[:5]` 或 `df.iloc[-5:]` |
| 特定行位置 | `.iloc[]` | `df.iloc[[0, 5, 10]]` |
| 列顺序未知 | `.iloc[]` | `df.iloc[:, 0]` |

---

## 过滤 DataFrame

### 布尔掩码

```python
# 单条件
mask = df['age'] > 25
filtered = df[mask]

# 多条件（使用括号！）
mask = (df['age'] > 25) & (df['salary'] < 65000)
filtered = df[mask]

# OR 条件
mask = (df['department'] == 'Engineering') | (df['department'] == 'Sales')
filtered = df[mask]

# NOT 条件
mask = ~(df['department'] == 'Marketing')
filtered = df[mask]
```

### 使用 `.query()` 实现可读性过滤

```python
# 简单查询 - 复杂条件下更具可读性
result = df.query('age > 25 and salary < 65000')

# 使用 @ 引用变量
min_age = 25
result = df.query('age > @min_age')

# 字符串比较
result = df.query('department == "Engineering"')

# 列表内过滤
depts = ['Engineering', 'Sales']
result = df.query('department in @depts')

# 复杂表达式
result = df.query('(age > 25) and (department != "Marketing")')
```

### 使用 `.isin()` 进行多值匹配

```python
# 按多个值过滤
departments = ['Engineering', 'Sales']
filtered = df[df['department'].isin(departments)]

# 取反
filtered = df[~df['department'].isin(departments)]

# 多列
conditions = {
    'department': ['Engineering', 'Sales'],
    'age': [25, 30, 35]
}
# 过滤 department 在列表中且 age 也在列表中的行
mask = df['department'].isin(conditions['department']) & df['age'].isin(conditions['age'])
```

### 使用 `.str` 访问器进行字符串过滤

```python
df = pd.DataFrame({
    'email': ['alice@example.com', 'bob@test.org', 'charlie@example.com'],
    'name': ['Alice Smith', 'Bob Jones', 'Charlie Brown']
})

# 包含
mask = df['email'].str.contains('example')

# 以...开头/结尾
mask = df['email'].str.endswith('.com')
mask = df['name'].str.startswith('A')

# 正则匹配
mask = df['email'].str.match(r'^[a-z]+@example\.com$')

# 不区分大小写
mask = df['name'].str.lower().str.contains('alice')
# 或使用 case 参数
mask = df['name'].str.contains('alice', case=False)

# 处理字符串列中的 NaN
mask = df['email'].str.contains('example', na=False)
```

---

## 排序

### 基本排序

```python
# 按单列排序（升序）
sorted_df = df.sort_values('age')

# 降序排序
sorted_df = df.sort_values('age', ascending=False)

# 按多列排序
sorted_df = df.sort_values(['department', 'salary'], ascending=[True, False])

# 按索引排序
sorted_df = df.sort_index()
sorted_df = df.sort_index(ascending=False)
```

### 高级排序

```python
# 带 NaN 处理的排序
df_with_nan = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'score': [85.0, np.nan, 90.0]
})

# NaN 在末尾（默认）
sorted_df = df_with_nan.sort_values('score', na_position='last')

# NaN 在开头
sorted_df = df_with_nan.sort_values('score', na_position='first')

# 使用 Categorical 自定义排序顺序
order = ['Marketing', 'Sales', 'Engineering']
df['department'] = pd.Categorical(df['department'], categories=order, ordered=True)
sorted_df = df.sort_values('department')

# 按计算值排序而不添加列
sorted_df = df.iloc[df['name'].str.len().argsort()]
```

### 原地排序

```python
# 原地修改 DataFrame
df.sort_values('age', inplace=True)

# 排序后重置索引
df.sort_values('age', inplace=True)
df.reset_index(drop=True, inplace=True)

# 或使用链式调用
df = df.sort_values('age').reset_index(drop=True)
```

---

## 列操作

### 添加和修改列

```python
# 添加新列
df['bonus'] = df['salary'] * 0.1

# 使用 np.where 进行条件列
df['seniority'] = np.where(df['age'] >= 30, 'Senior', 'Junior')

# 使用 np.select 处理多条件
conditions = [
    df['age'] < 25,
    df['age'] < 35,
    df['age'] >= 35
]
choices = ['Junior', 'Mid', 'Senior']
df['level'] = np.select(conditions, choices, default='Unknown')

# 使用 .assign() 进行方法链（返回新 DataFrame）
df_new = df.assign(
    bonus=lambda x: x['salary'] * 0.1,
    total_comp=lambda x: x['salary'] + x['salary'] * 0.1
)
```

### 重命名列

```python
# 重命名特定列
df = df.rename(columns={'name': 'full_name', 'age': 'years'})

# 使用函数重命名所有列
df.columns = df.columns.str.lower().str.replace(' ', '_')

# 使用函数重命名
df = df.rename(columns=str.upper)
```

### 删除列

```python
# 删除单列
df = df.drop('bonus', axis=1)
# 或
df = df.drop(columns=['bonus'])

# 删除多列
df = df.drop(columns=['bonus', 'level'])

# 按条件删除列
cols_to_drop = [col for col in df.columns if col.startswith('temp_')]
df = df.drop(columns=cols_to_drop)
```

### 重排列顺序

```python
# 显式指定顺序
new_order = ['name', 'department', 'age', 'salary']
df = df[new_order]

# 将特定列移到最前
cols = ['salary'] + [c for c in df.columns if c != 'salary']
df = df[cols]

# 使用 .reindex()
df = df.reindex(columns=['name', 'age', 'salary', 'department'])
```

---

## 索引操作

### 设置和重置索引

```python
# 将列设置为索引
df = df.set_index('name')

# 将索引重置为列
df = df.reset_index()

# 完全丢弃索引
df = df.reset_index(drop=True)

# 设置多列为索引（MultiIndex）
df = df.set_index(['department', 'name'])
```

### 使用 MultiIndex

```python
# 创建 MultiIndex DataFrame
df = pd.DataFrame({
    'department': ['Eng', 'Eng', 'Sales', 'Sales'],
    'team': ['Backend', 'Frontend', 'East', 'West'],
    'headcount': [10, 8, 15, 12]
}).set_index(['department', 'team'])

# 从 MultiIndex 中选择
df.loc['Eng']  # 所有 Eng 行
df.loc[('Eng', 'Backend')]  # 特定行

# 使用 .xs() 进行截面选择
df.xs('Backend', level='team')  # 所有 Backend 团队

# 重置特定级别
df.reset_index(level='team')
```

---

## 复制 DataFrame

### 何时使用 `.copy()`

```python
# 修改子集时始终复制
subset = df[df['age'] > 25].copy()
subset['new_col'] = 100  # 安全，不会出现 SettingWithCopyWarning

# 不使用 copy - 可能产生警告或静默失败
# 错误：
# subset = df[df['age'] > 25]
# subset['new_col'] = 100  # SettingWithCopyWarning!

# 深拷贝（默认）- 复制数据
df_copy = df.copy()  # 或 df.copy(deep=True)

# 浅拷贝 - 共享数据，仅复制结构
df_shallow = df.copy(deep=False)
```

---

## 最佳实践总结

1. **使用 `.loc[]` 和 `.iloc[]`** - 永远不要使用链式索引
2. **条件加括号** - `(cond1) & (cond2)` 而不是 `cond1 & cond2`
3. **使用 `.query()` 提高可读性** - 特别是复杂过滤条件时
4. **修改子集前先复制** - 始终使用 `.copy()`
5. **使用向量化操作** - 避免行迭代进行过滤
6. **显式处理 NaN** - 在字符串操作中使用 `na=False`
7. **优先使用方法链** - 使用 `.assign()` 创建列

---

## 需要避免的反模式

```python
# 错误：链式索引
df['A']['B'] = value  # 可能不工作，产生警告

# 正确：使用 .loc
df.loc[:, ('A', 'B')] = value
# 或先选行再赋值：
df.loc[df['A'] > 0, 'B'] = value

# 错误：迭代过滤
result = []
for idx, row in df.iterrows():
    if row['age'] > 25:
        result.append(row)

# 正确：布尔索引
result = df[df['age'] > 25]

# 错误：多次分别赋值
df = df[df['age'] > 25]
df = df[df['salary'] > 50000]

# 正确：合并过滤
df = df[(df['age'] > 25) & (df['salary'] > 50000)]
```

---

## 相关参考

- `data-cleaning.md` - 选择数据后进行清洗
- `aggregation-groupby.md` - 对过滤后的数据进行分组聚合
- `performance-optimization.md` - 优化大数据集的过滤
