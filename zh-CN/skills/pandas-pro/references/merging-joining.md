# 合并与连接

---

## 概述

组合 DataFrame 对于处理关系数据至关重要。本参考涵盖 merge、join、concat 和高级组合策略，基于 pandas 2.0+。

---

## Merge（SQL 风格连接）

### 基本 Merge

```python
import pandas as pd
import numpy as np

# 示例 DataFrame
employees = pd.DataFrame({
    'emp_id': [1, 2, 3, 4, 5],
    'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
    'dept_id': [101, 102, 101, 103, 102],
})

departments = pd.DataFrame({
    'dept_id': [101, 102, 104],
    'dept_name': ['Engineering', 'Sales', 'Marketing'],
})

# 内连接（默认）- 仅匹配行
result = pd.merge(employees, departments, on='dept_id')

# 显式指定 how 参数
result = pd.merge(employees, departments, on='dept_id', how='inner')
```

### 连接类型

```python
# 内连接 - 仅两边匹配的行
inner = pd.merge(employees, departments, on='dept_id', how='inner')
# 结果：4 行（emp_id 4 的 dept_id 103 在 departments 中不存在）

# 左连接 - 左边所有行，右边匹配的行
left = pd.merge(employees, departments, on='dept_id', how='left')
# 结果：5 行（Diana 的 dept_name 为 NaN）

# 右连接 - 右边所有行，左边匹配的行
right = pd.merge(employees, departments, on='dept_id', how='right')
# 结果：4 行（Marketing 没有员工，但被包含）

# 外连接 - 两边所有行
outer = pd.merge(employees, departments, on='dept_id', how='outer')
# 结果：6 行（包含两边不匹配的行）

# 交叉连接 - 笛卡尔积
cross = pd.merge(employees, departments, how='cross')
# 结果：15 行（5 个员工 × 3 个部门）
```

### 不同列名合并

```python
employees = pd.DataFrame({
    'emp_id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'department': [101, 102, 101],
})

departments = pd.DataFrame({
    'id': [101, 102],
    'dept_name': ['Engineering', 'Sales'],
})

# 不同列名
result = pd.merge(
    employees,
    departments,
    left_on='department',
    right_on='id'
)

# 合并后删除重复列
result = result.drop('id', axis=1)
```

### 多列合并

```python
sales = pd.DataFrame({
    'region': ['East', 'East', 'West', 'West'],
    'product': ['A', 'B', 'A', 'B'],
    'sales': [100, 150, 120, 180],
})

targets = pd.DataFrame({
    'region': ['East', 'East', 'West'],
    'product': ['A', 'B', 'A'],
    'target': [90, 140, 110],
})

# 多列合并
result = pd.merge(sales, targets, on=['region', 'product'], how='left')
```

### 按索引合并

```python
# 合并前设置索引
employees_idx = employees.set_index('emp_id')
salaries = pd.DataFrame({
    'emp_id': [1, 2, 3, 4],
    'salary': [80000, 75000, 70000, 65000],
}).set_index('emp_id')

# 按索引合并
result = pd.merge(employees_idx, salaries, left_index=True, right_index=True)

# 混合列和索引
result = pd.merge(
    employees,
    salaries,
    left_on='emp_id',
    right_index=True
)
```

---

## 处理重复列

### 后缀

```python
df1 = pd.DataFrame({
    'id': [1, 2, 3],
    'value': [10, 20, 30],
    'date': ['2024-01-01', '2024-01-02', '2024-01-03'],
})

df2 = pd.DataFrame({
    'id': [1, 2, 3],
    'value': [100, 200, 300],
    'date': ['2024-02-01', '2024-02-02', '2024-02-03'],
})

# 默认后缀
result = pd.merge(df1, df2, on='id')
# 列：id, value_x, date_x, value_y, date_y

# 自定义后缀
result = pd.merge(df1, df2, on='id', suffixes=('_jan', '_feb'))
# 列：id, value_jan, date_jan, value_feb, date_feb
```

### 验证合并基数

```python
# 验证合并关系（pandas 2.0+）
# 验证失败时抛出 MergeError

# 一对一：每个键在两边最多出现一次
result = pd.merge(df1, df2, on='id', validate='one_to_one')  # 或 '1:1'

# 一对多：键仅在左边唯一
result = pd.merge(employees, salaries, on='emp_id', validate='one_to_many')  # 或 '1:m'

# 多对一：键仅在右边唯一
result = pd.merge(salaries, employees, on='emp_id', validate='many_to_one')  # 或 'm:1'

# 多对多：无唯一性要求（默认）
result = pd.merge(df1, df2, on='id', validate='many_to_many')  # 或 'm:m'
```

### 指示列

```python
# 添加指示列显示每行来源
result = pd.merge(
    employees,
    departments,
    on='dept_id',
    how='outer',
    indicator=True
)
# _merge 列值：'left_only'、'right_only'、'both'

# 自定义指示列名
result = pd.merge(
    employees,
    departments,
    on='dept_id',
    how='outer',
    indicator='source'
)

# 按指示列过滤
left_only = result[result['_merge'] == 'left_only']
both = result[result['_merge'] == 'both']
```

---

## Join（基于索引）

### DataFrame.join()

```python
# join() 用于基于索引的连接（更简单的语法）
employees = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'dept_id': [101, 102, 101],
}, index=[1, 2, 3])

salaries = pd.DataFrame({
    'salary': [80000, 75000, 70000],
    'bonus': [5000, 4000, 3500],
}, index=[1, 2, 3])

# 按索引连接
result = employees.join(salaries)

# 连接类型（与 merge 相同）
result = employees.join(salaries, how='left')
result = employees.join(salaries, how='outer')
```

### 按列连接到索引

```python
employees = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'dept_id': [101, 102, 101],
})

departments = pd.DataFrame({
    'dept_name': ['Engineering', 'Sales'],
}, index=[101, 102])

# 将左列连接到右索引
result = employees.join(departments, on='dept_id')
```

### 连接多个 DataFrame

```python
df1 = pd.DataFrame({'a': [1, 2]}, index=['x', 'y'])
df2 = pd.DataFrame({'b': [3, 4]}, index=['x', 'y'])
df3 = pd.DataFrame({'c': [5, 6]}, index=['x', 'y'])

# 一次连接多个
result = df1.join([df2, df3])

# 为重复列使用后缀
result = df1.join([df2, df3], lsuffix='_1', rsuffix='_2')
```

---

## Concat（堆叠 DataFrame）

### 垂直拼接（按行）

```python
# 垂直堆叠 DataFrame
df1 = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30],
})

df2 = pd.DataFrame({
    'name': ['Charlie', 'Diana'],
    'age': [35, 28],
})

# 基本 concat（axis=0 是默认值）
result = pd.concat([df1, df2])

# 重置索引
result = pd.concat([df1, df2], ignore_index=True)

# 跟踪来源
result = pd.concat([df1, df2], keys=['source1', 'source2'])
# 创建 MultiIndex
```

### 水平拼接（按列）

```python
names = pd.DataFrame({'name': ['Alice', 'Bob', 'Charlie']})
ages = pd.DataFrame({'age': [25, 30, 35]})
salaries = pd.DataFrame({'salary': [50000, 60000, 70000]})

# 拼接列（axis=1）
result = pd.concat([names, ages, salaries], axis=1)
```

### 处理不匹配的列

```python
df1 = pd.DataFrame({
    'name': ['Alice', 'Bob'],
    'age': [25, 30],
})

df2 = pd.DataFrame({
    'name': ['Charlie', 'Diana'],
    'salary': [70000, 65000],
})

# 外连接（默认）- 包含所有列
result = pd.concat([df1, df2])
# age 和 salary 列在不存在的位置为 NaN

# 内连接 - 仅公共列
result = pd.concat([df1, df2], join='inner')
# 只有 'name' 列
```

### 带验证的 Concat

```python
# 验证没有索引重叠
try:
    result = pd.concat([df1, df2], verify_integrity=True)
except ValueError as e:
    print(f"Index overlap detected: {e}")

# 替代方案：使用 ignore_index
result = pd.concat([df1, df2], ignore_index=True)
```

---

## 合并与更新

### combine_first() - 填充空缺

```python
# 用另一个 DataFrame 的值填充 NaN
df1 = pd.DataFrame({
    'A': [1, np.nan, 3],
    'B': [np.nan, 2, 3],
}, index=['a', 'b', 'c'])

df2 = pd.DataFrame({
    'A': [10, 20, 30],
    'B': [10, 20, 30],
}, index=['a', 'b', 'c'])

# 用 df2 的值填充 df1 的 NaN
result = df1.combine_first(df2)
# A: [1, 20, 3], B: [10, 2, 3]
```

### update() - 原地更新

```python
df1 = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
}, index=['a', 'b', 'c'])

df2 = pd.DataFrame({
    'A': [10, 20],
    'B': [40, 50],
}, index=['a', 'b'])

# 用 df2 的值更新 df1（原地）
df1.update(df2)
# df1 现在是 A: [10, 20, 3], B: [40, 50, 6]

# 仅在 df2 有非 NaN 值时更新
df1.update(df2, overwrite=False)  # 不覆盖已有值
```

---

## 高级合并模式

### 带聚合的合并

```python
# 一次操作中合并并聚合
orders = pd.DataFrame({
    'order_id': [1, 2, 3, 4],
    'customer_id': [101, 102, 101, 103],
    'amount': [100, 200, 150, 300],
})

customers = pd.DataFrame({
    'customer_id': [101, 102, 103],
    'name': ['Alice', 'Bob', 'Charlie'],
})

# 获取客户汇总
customer_summary = orders.groupby('customer_id').agg(
    total_orders=('order_id', 'count'),
    total_amount=('amount', 'sum'),
).reset_index()

# 与客户信息合并
result = pd.merge(customers, customer_summary, on='customer_id')
```

### Asof 合并（最近匹配）

```python
# 按最近键合并（适用于时间序列）
trades = pd.DataFrame({
    'time': pd.to_datetime(['2024-01-01 10:00:01', '2024-01-01 10:00:03', '2024-01-01 10:00:05']),
    'ticker': ['AAPL', 'AAPL', 'AAPL'],
    'price': [150.0, 151.0, 150.5],
})

quotes = pd.DataFrame({
    'time': pd.to_datetime(['2024-01-01 10:00:00', '2024-01-01 10:00:02', '2024-01-01 10:00:04']),
    'ticker': ['AAPL', 'AAPL', 'AAPL'],
    'bid': [149.5, 150.5, 150.0],
    'ask': [150.5, 151.5, 151.0],
})

# asof 合并 - 为每笔交易找最近的报价
result = pd.merge_asof(
    trades.sort_values('time'),
    quotes.sort_values('time'),
    on='time',
    by='ticker',
    direction='backward'  # 使用最近的报价
)
```

### 条件合并

```python
# 超越键等值的条件合并
# 先合并，再过滤

products = pd.DataFrame({
    'product_id': [1, 2, 3],
    'name': ['Widget', 'Gadget', 'Gizmo'],
    'category': ['A', 'B', 'A'],
})

discounts = pd.DataFrame({
    'category': ['A', 'A', 'B'],
    'min_qty': [10, 50, 20],
    'discount': [0.05, 0.10, 0.08],
})

# 交叉合并后过滤
merged = pd.merge(products, discounts, on='category')
# 然后根据数量条件进行过滤
```

---

## 性能考虑

### 预排序合并

```python
# 合并前排序键以提高性能
df1 = df1.sort_values('key')
df2 = df2.sort_values('key')

# 合并已排序的 DataFrame
result = pd.merge(df1, df2, on='key')
```

### 索引对齐

```python
# 使用索引合并通常比列更快
df1 = df1.set_index('key')
df2 = df2.set_index('key')

# 按索引连接
result = df1.join(df2)
```

### 内存高效合并

```python
# 对于大型 DataFrame，合并前减少内存
# 转换为适当类型
df1['key'] = df1['key'].astype('int32')  # 而不是 int64
df1['category'] = df1['category'].astype('category')

# 仅选择需要的列
cols_needed = ['key', 'value1', 'value2']
result = pd.merge(df1[cols_needed], df2[cols_needed], on='key')
```

---

## 常见合并模式

### 带空值检查的左连接

```python
# 查找左连接后不匹配的行
result = pd.merge(employees, departments, on='dept_id', how='left')
unmatched = result[result['dept_name'].isna()]
```

### 反连接（不在另一表中的行）

```python
# 查找不在特定部门列表中的员工
dept_list = [101, 102]

# 方法 1：使用 isin
not_in_depts = employees[~employees['dept_id'].isin(dept_list)]

# 方法 2：使用带指示器的合并
merged = pd.merge(
    employees,
    pd.DataFrame({'dept_id': dept_list}),
    on='dept_id',
    how='left',
    indicator=True
)
not_in_depts = merged[merged['_merge'] == 'left_only']
```

### 自连接

```python
# 查找同一部门内的配对
employees = pd.DataFrame({
    'emp_id': [1, 2, 3, 4],
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'dept_id': [101, 101, 102, 101],
})

# 自连接找配对
pairs = pd.merge(
    employees,
    employees,
    on='dept_id',
    suffixes=('_1', '_2')
)
# 移除自配对和重复
pairs = pairs[pairs['emp_id_1'] < pairs['emp_id_2']]
```

---

## 最佳实践总结

1. **选择正确的连接类型** - 默认内连接可能丢失数据
2. **验证基数** - 使用 `validate` 参数
3. **使用指示器** - 调试意外结果
4. **处理重复项** - 使用有意义的后缀
5. **预排序提升性能** - 特别是大型 DataFrame
6. **操作后重置索引** - 保持 DataFrame 可用
7. **检查连接后的 NaN** - 了解不匹配的行

---

## 需要避免的反模式

```python
# 错误：不了解基数就合并
result = pd.merge(df1, df2, on='key')  # 可能导致行数爆炸

# 正确：验证关系
result = pd.merge(df1, df2, on='key', validate='one_to_one')

# 错误：重复合并
result = pd.merge(df1, df2, on='key')
result = pd.merge(result, df3, on='key')
result = pd.merge(result, df4, on='key')

# 正确：链式或使用 reduce
from functools import reduce
dfs = [df1, df2, df3, df4]
result = reduce(lambda left, right: pd.merge(left, right, on='key'), dfs)

# 错误：忽略合并指示器
result = pd.merge(df1, df2, on='key', how='outer')

# 正确：检查合并结果
result = pd.merge(df1, df2, on='key', how='outer', indicator=True)
print(result['_merge'].value_counts())
```

---

## 相关参考

- `dataframe-operations.md` - 合并前/后过滤
- `aggregation-groupby.md` - 合并前聚合
- `performance-optimization.md` - 优化大型合并
