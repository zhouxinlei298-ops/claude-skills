# 数据清洗

---

## 概述

数据清洗对于可靠的分析至关重要。本参考涵盖使用 pandas 2.0+ 模式处理缺失值、重复项、类型转换和数据验证。

---

## 缺失值

### 检测缺失值

```python
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'name': ['Alice', 'Bob', None, 'Diana'],
    'age': [25, np.nan, 35, 28],
    'salary': [50000, 60000, np.nan, np.nan],
    'department': ['Eng', '', 'Eng', 'Sales']
})

# 检查是否有缺失值
df.isna().any()  # 每列
df.isna().any().any()  # 整个 DataFrame

# 统计缺失值
df.isna().sum()  # 每列
df.isna().sum().sum()  # 总计

# 缺失值百分比
(df.isna().sum() / len(df) * 100).round(2)

# 有任何缺失值的行
df[df.isna().any(axis=1)]

# 所有值都完整的行
df[df.notna().all(axis=1)]

# 缺失值热图信息
missing_info = pd.DataFrame({
    'missing': df.isna().sum(),
    'percent': (df.isna().sum() / len(df) * 100).round(2),
    'dtype': df.dtypes
})
```

### 处理缺失值 - 删除

```python
# 删除有缺失值的行
df_clean = df.dropna()

# 删除指定列有缺失值的行
df_clean = df.dropna(subset=['name', 'age'])

# 删除所有值都缺失的行
df_clean = df.dropna(how='all')

# 删除非空值不足最低数量的行
df_clean = df.dropna(thresh=3)  # 保留至少有 3 个非空值的行

# 删除有缺失值的列
df_clean = df.dropna(axis=1)

# 删除缺失超过 50% 的列
threshold = len(df) * 0.5
df_clean = df.dropna(axis=1, thresh=threshold)
```

### 处理缺失值 - 填充

```python
# 用常量填充
df['age'] = df['age'].fillna(0)

# 用列均值/中位数/众数填充
df['age'] = df['age'].fillna(df['age'].mean())
df['salary'] = df['salary'].fillna(df['salary'].median())
df['department'] = df['department'].fillna(df['department'].mode()[0])

# 前向填充（使用前一个值）
df['salary'] = df['salary'].ffill()

# 后向填充（使用后一个值）
df['salary'] = df['salary'].bfill()

# 每列使用不同的填充值
fill_values = {'age': 0, 'salary': df['salary'].median(), 'name': 'Unknown'}
df = df.fillna(fill_values)

# 使用插值填充（数值数据）
df['salary'] = df['salary'].interpolate(method='linear')

# 按组填充（用组均值填充）
df['salary'] = df.groupby('department')['salary'].transform(
    lambda x: x.fillna(x.mean())
)
```

### 处理空字符串与 NaN

```python
# 空字符串不会被检测为 NaN
df['department'].isna().sum()  # 不会计算 ''

# 将空字符串替换为 NaN
df['department'] = df['department'].replace('', np.nan)
# 或
df['department'] = df['department'].replace(r'^\s*$', np.nan, regex=True)

# 将多个值替换为 NaN
df = df.replace(['', 'N/A', 'null', 'None', '-'], np.nan)

# 读取文件时使用 na_values
df = pd.read_csv('file.csv', na_values=['', 'N/A', 'null', 'None', '-'])
```

---

## 处理重复项

### 检测重复项

```python
df = pd.DataFrame({
    'id': [1, 2, 2, 3, 4, 4],
    'name': ['Alice', 'Bob', 'Bob', 'Charlie', 'Diana', 'Diana'],
    'email': ['a@x.com', 'b@x.com', 'b@x.com', 'c@x.com', 'd@x.com', 'd2@x.com']
})

# 检查重复行（所有列）
df.duplicated().sum()

# 检查特定列
df.duplicated(subset=['id']).sum()
df.duplicated(subset=['name', 'email']).sum()

# 查看重复行
df[df.duplicated(keep=False)]  # 所有重复项
df[df.duplicated(keep='first')]  # 除第一次出现外的重复项
df[df.duplicated(keep='last')]  # 除最后一次出现外的重复项

# 按键统计重复数
df.groupby('id').size().loc[lambda x: x > 1]
```

### 删除重复项

```python
# 删除重复行（保留第一个）
df_clean = df.drop_duplicates()

# 保留最后一个
df_clean = df.drop_duplicates(keep='last')

# 删除所有重复项（不保留）
df_clean = df.drop_duplicates(keep=False)

# 基于特定列
df_clean = df.drop_duplicates(subset=['id'])
df_clean = df.drop_duplicates(subset=['name', 'email'], keep='last')

# 原地修改
df.drop_duplicates(inplace=True)
```

### 通过聚合处理重复项

```python
# 不删除而是聚合重复项
df_agg = df.groupby('id').agg({
    'name': 'first',
    'email': lambda x: ', '.join(x.unique())
}).reset_index()

# 保留最大/最小值的行
df_best = df.loc[df.groupby('id')['score'].idxmax()]

# 为重复项排名
df['rank'] = df.groupby('id').cumcount() + 1
```

---

## 类型转换

### 检查和转换类型

```python
# 检查当前类型
df.dtypes
df.info()

# 转换为特定类型
df['age'] = df['age'].astype(int)
df['salary'] = df['salary'].astype(float)
df['name'] = df['name'].astype(str)

# 带错误处理的安全转换
df['age'] = pd.to_numeric(df['age'], errors='coerce')  # 无效值 -> NaN
df['age'] = pd.to_numeric(df['age'], errors='ignore')  # 无效值保留原始值

# 转换多列
df = df.astype({'age': 'int64', 'salary': 'float64'})

# 将 object 转换为 string（pandas 2.0+ StringDtype）
df['name'] = df['name'].astype('string')  # 可空字符串类型
```

### 日期时间转换

```python
df = pd.DataFrame({
    'date_str': ['2024-01-15', '2024-02-20', 'invalid', '2024-03-10'],
    'timestamp': [1705276800, 1708387200, 1710028800, 1710028800]
})

# 字符串转日期时间
df['date'] = pd.to_datetime(df['date_str'], errors='coerce')

# 指定格式以加快解析
df['date'] = pd.to_datetime(df['date_str'], format='%Y-%m-%d', errors='coerce')

# Unix 时间戳转日期时间
df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

# 提取组件
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.day_name()

# 处理混合格式
df['date'] = pd.to_datetime(df['date_str'], format='mixed', dayfirst=False)
```

### 分类类型转换

```python
# 转换为分类类型（对低基数字符串节省内存）
df['department'] = df['department'].astype('category')

# 有序分类
df['size'] = pd.Categorical(
    df['size'],
    categories=['Small', 'Medium', 'Large'],
    ordered=True
)

# 检查内存节省
print(f"Object: {df['department'].nbytes}")
df['department'] = df['department'].astype('category')
print(f"Category: {df['department'].nbytes}")
```

### 可空整数类型（pandas 2.0+）

```python
# 标准 int 不支持 NaN
# 使用可空整数类型
df['age'] = df['age'].astype('Int64')  # 注意大写 I

# 所有可空类型
df = df.astype({
    'count': 'Int64',      # 可空整数
    'price': 'Float64',    # 可空浮点数
    'flag': 'boolean',     # 可空布尔值
    'name': 'string',      # 可空字符串
})

# 带空值处理的转换
df['age'] = pd.array([1, 2, None, 4], dtype='Int64')
```

---

## 字符串清洗

### 常见字符串操作

```python
df = pd.DataFrame({
    'name': ['  Alice  ', 'BOB', 'charlie', None, 'Diana Smith'],
    'email': ['ALICE@EXAMPLE.COM', 'bob@test', 'invalid', None, 'diana@example.com']
})

# 去除空白
df['name'] = df['name'].str.strip()

# 大小写规范化
df['name'] = df['name'].str.lower()
df['name'] = df['name'].str.upper()
df['name'] = df['name'].str.title()  # 首字母大写

# 替换模式
df['name'] = df['name'].str.replace(r'\s+', ' ', regex=True)  # 多个空格变一个
df['phone'] = df['phone'].str.replace(r'[^0-9]', '', regex=True)  # 只保留数字

# 使用正则提取
df['domain'] = df['email'].str.extract(r'@(.+)$')
df['first_name'] = df['name'].str.extract(r'^(\w+)')

# 分割字符串
df[['first', 'last']] = df['name'].str.split(' ', n=1, expand=True)
```

### 字符串验证

```python
# 检查模式
df['valid_email'] = df['email'].str.match(r'^[\w.]+@[\w.]+\.\w+$', na=False)

# 字符串长度
df['name_length'] = df['name'].str.len()
df['valid_length'] = df['name'].str.len().between(2, 50)

# 包含检查
df['has_domain'] = df['email'].str.contains('@', na=False)
```

---

## 数据验证

### 验证函数

```python
def validate_dataframe(df: pd.DataFrame) -> dict:
    """全面的 DataFrame 验证。"""
    report = {
        'rows': len(df),
        'columns': len(df.columns),
        'duplicates': df.duplicated().sum(),
        'missing_by_column': df.isna().sum().to_dict(),
        'dtypes': df.dtypes.astype(str).to_dict(),
    }
    return report

# 范围验证
def validate_range(series: pd.Series, min_val, max_val) -> pd.Series:
    """返回范围内值的布尔掩码。"""
    return series.between(min_val, max_val)

df['valid_age'] = validate_range(df['age'], 0, 120)

# 自定义验证
def validate_email(series: pd.Series) -> pd.Series:
    """验证邮箱格式。"""
    pattern = r'^[\w.+-]+@[\w-]+\.[\w.-]+$'
    return series.str.match(pattern, na=False)

df['valid_email'] = validate_email(df['email'])
```

### 使用 pandera 进行模式验证

```python
# 使用 pandera 进行模式验证（生产环境推荐）
import pandera as pa
from pandera import Column, Check

schema = pa.DataFrameSchema({
    'name': Column(str, Check.str_length(min_value=1, max_value=100)),
    'age': Column(int, Check.in_range(0, 120)),
    'email': Column(str, Check.str_matches(r'^[\w.+-]+@[\w-]+\.[\w.-]+$')),
    'salary': Column(float, Check.greater_than(0), nullable=True),
})

# 验证 DataFrame
try:
    schema.validate(df)
except pa.errors.SchemaError as e:
    print(f"Validation failed: {e}")
```

---

## 数据清洗管道

### 方法链模式

```python
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """使用方法链的完整数据清洗管道。"""
    return (
        df
        # 复制一份
        .copy()
        # 标准化列名
        .rename(columns=lambda x: x.lower().strip().replace(' ', '_'))
        # 删除完全空的行
        .dropna(how='all')
        # 清洗字符串列
        .assign(
            name=lambda x: x['name'].str.strip().str.title(),
            email=lambda x: x['email'].str.lower().str.strip(),
        )
        # 处理缺失值
        .fillna({'department': 'Unknown'})
        # 转换类型
        .astype({'age': 'Int64', 'department': 'category'})
        # 删除重复项
        .drop_duplicates(subset=['email'])
        # 重置索引
        .reset_index(drop=True)
    )

df_clean = clean_dataframe(df)
```

### 带验证的管道

```python
def clean_and_validate(
    df: pd.DataFrame,
    required_columns: list[str],
    unique_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """清洗 DataFrame 并返回验证报告。"""

    # 验证必需列是否存在
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 跟踪清洗统计
    stats = {
        'initial_rows': len(df),
        'dropped_empty': 0,
        'dropped_duplicates': 0,
        'filled_missing': {},
    }

    # 清洗
    df = df.copy()

    # 删除空行
    before = len(df)
    df = df.dropna(how='all')
    stats['dropped_empty'] = before - len(df)

    # 处理重复项
    if unique_columns:
        before = len(df)
        df = df.drop_duplicates(subset=unique_columns)
        stats['dropped_duplicates'] = before - len(df)

    stats['final_rows'] = len(df)

    return df, stats
```

---

## 最佳实践总结

1. **始终先检查数据质量** - 使用 `.info()`、`.describe()` 和缺失值分析
2. **记录清洗决策** - 跟踪删除/填充了什么以及原因
3. **使用可空类型** - `Int64`、`string`、`boolean` 用于正确的空值处理
4. **清洗后验证** - 确保数据符合预期
5. **使用方法链** - 可读、可维护的清洗管道
6. **修改前复制** - 避免 SettingWithCopyWarning
7. **处理边缘情况** - 空字符串、空白、无效格式

---

## 需要避免的反模式

```python
# 错误：不了解影响就删除 NaN
df = df.dropna()  # 可能丢失大量数据

# 正确：先调查，再做决定
print(f"Missing values: {df.isna().sum()}")
print(f"Rows affected: {df.isna().any(axis=1).sum()}")
# 然后做出明智的决定

# 错误：没有领域知识就填充
df['age'] = df['age'].fillna(0)  # 年龄 0 不合理

# 正确：使用适当的填充策略
df['age'] = df['age'].fillna(df['age'].median())

# 错误：没有错误处理的类型转换
df['id'] = df['id'].astype(int)  # 遇到 NaN 或无效值会失败

# 正确：安全转换
df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
```

---

## 相关参考

- `dataframe-operations.md` - 针对性清洗的选择和过滤
- `aggregation-groupby.md` - 聚合重复项而不是删除
- `performance-optimization.md` - 高效清洗大数据集
