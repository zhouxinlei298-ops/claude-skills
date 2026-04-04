---
name: pandas-pro
description: Performs pandas DataFrame operations for data analysis, manipulation, and transformation. Use when working with pandas DataFrames, data cleaning, aggregation, merging, or time series analysis. Invoke for data manipulation tasks such as joining DataFrames on multiple keys, pivoting tables, resampling time series, handling NaN values with interpolation or forward-fill, groupby aggregations, type conversion, or performance optimization of large datasets.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: data-ml
  triggers: pandas, DataFrame, data manipulation, data cleaning, aggregation, groupby, merge, join, time series, data wrangling, pivot table, data transformation
  role: expert
  scope: implementation
  output-format: code
  related-skills: python-pro
---

# Pandas Pro

高级 pandas 开发专家，专注于高效的数据操作、分析和转换工作流，具备生产级性能模式经验。

## 核心工作流程

1. **评估数据结构** — 检查数据类型、内存使用、缺失值、数据质量：
   ```python
   print(df.dtypes)
   print(df.memory_usage(deep=True).sum() / 1e6, "MB")
   print(df.isna().sum())
   print(df.describe(include="all"))
   ```
2. **设计转换方案** — 规划向量化操作，避免循环，确定索引策略
3. **高效实现** — 使用向量化方法、方法链、适当的索引
4. **验证结果** — 检查数据类型、形状、空值计数和行数：
   ```python
   assert result.shape[0] == expected_rows, f"Row count mismatch: {result.shape[0]}"
   assert result.isna().sum().sum() == 0, "Unexpected nulls after transform"
   assert set(result.columns) == expected_cols
   ```
5. **优化** — 分析内存，应用分类类型，必要时使用分块处理

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| DataFrame 操作 | `references/dataframe-operations.md` | 索引、选择、过滤、排序 |
| 数据清洗 | `references/data-cleaning.md` | 缺失值、重复项、类型转换 |
| 聚合与 GroupBy | `references/aggregation-groupby.md` | GroupBy、数据透视、交叉表、聚合 |
| 合并与连接 | `references/merging-joining.md` | Merge、join、concat、组合策略 |
| 性能优化 | `references/performance-optimization.md` | 内存使用、向量化、分块处理 |

## 代码模式

### 向量化操作（前后对比）

```python
# ❌ 避免：逐行迭代
for i, row in df.iterrows():
    df.at[i, 'tax'] = row['price'] * 0.2

# ✅ 使用：向量化赋值
df['tax'] = df['price'] * 0.2
```

### 使用 `.copy()` 安全子集化

```python
# ❌ 避免：链式索引会触发 SettingWithCopyWarning
df['A']['B'] = 1

# ✅ 使用：修改子集时使用 .loc[] 并显式复制
subset = df.loc[df['status'] == 'active', :].copy()
subset['score'] = subset['score'].fillna(0)
```

### GroupBy 聚合

```python
summary = (
    df.groupby(['region', 'category'], observed=True)
    .agg(
        total_sales=('revenue', 'sum'),
        avg_price=('price', 'mean'),
        order_count=('order_id', 'nunique'),
    )
    .reset_index()
)
```

### 带验证的合并

```python
merged = pd.merge(
    left_df, right_df,
    on=['customer_id', 'date'],
    how='left',
    validate='m:1',          # 断言右表键唯一
    indicator=True,
)
unmatched = merged[merged['_merge'] != 'both']
print(f"Unmatched rows: {len(unmatched)}")
merged.drop(columns=['_merge'], inplace=True)
```

### 缺失值处理

```python
# 先前向填充，再对数值间隙进行插值
df['price'] = df['price'].ffill().interpolate(method='linear')

# 分类列用众数填充，数值列用中位数填充
for col in df.select_dtypes(include='object'):
    df[col] = df[col].fillna(df[col].mode()[0])
for col in df.select_dtypes(include='number'):
    df[col] = df[col].fillna(df[col].median())
```

### 时间序列重采样

```python
daily = (
    df.set_index('timestamp')
    .resample('D')
    .agg({'revenue': 'sum', 'sessions': 'count'})
    .fillna(0)
)
```

### 数据透视表

```python
pivot = df.pivot_table(
    values='revenue',
    index='region',
    columns='product_line',
    aggfunc='sum',
    fill_value=0,
    margins=True,
)
```

### 内存优化

```python
# 降低数值精度，将低基数字符串转换为分类类型
df['category'] = df['category'].astype('category')
df['count'] = pd.to_numeric(df['count'], downcast='integer')
df['score'] = pd.to_numeric(df['score'], downcast='float')
print(df.memory_usage(deep=True).sum() / 1e6, "MB after optimization")
```

## 约束

### 必须做
- 使用向量化操作代替循环
- 设置适当的数据类型（低基数字符串使用分类类型）
- 使用 `.memory_usage(deep=True)` 检查内存使用
- 显式处理缺失值（不要静默丢弃）
- 使用方法链提高可读性
- 在操作过程中保持索引完整性
- 在转换前后验证数据质量
- 修改子集时使用 `.copy()` 避免 SettingWithCopyWarning

### 不能做
- 除非绝对必要，否则不要使用 `.iterrows()` 遍历 DataFrame 行
- 不要使用链式索引（`df['A']['B']`）— 使用 `.loc[]` 或 `.iloc[]`
- 不要忽略 SettingWithCopyWarning 消息
- 不要在不分块的情况下加载整个大型数据集
- 不要使用已弃用的方法（`.ix`、`.append()` — 使用 `pd.concat()`）
- 不要将可以在 pandas 中完成的操作转换为 Python 列表
- 不要在没有验证的情况下假设数据是干净的

## 输出模板

实现 pandas 解决方案时，请提供：
1. 使用向量化和适当索引的代码
2. 解释复杂转换的注释
3. 如果数据集较大，说明内存/性能注意事项
4. 数据验证检查（数据类型、空值、形状）
