# 特征工程

---

## 概述

特征工程将原始数据转换为能提升模型性能的特征。生产系统需要通过特征存储（feature stores）实现可重复的转换、特征版本管理和线上/线下一致性。

## 何时使用本参考

- 构建特征转换流水线
- 实现特征存储（Feast、Tecton、自定义）
- 创建数据验证工作流
- 设计特征模式和注册表
- 处理特征漂移和监控

## 何时不使用

- 简单的临时特征创建（直接使用 pandas）
- 一次性探索性分析
- 使用小数据集进行原型设计

---

## 特征转换流水线

### Scikit-learn 模式流水线

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import joblib

def create_feature_pipeline(
    numeric_features: list[str],
    categorical_features: list[str],
) -> ColumnTransformer:
    """Create reproducible feature transformation pipeline."""

    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features),
        ],
        remainder='drop',
        verbose_feature_names_out=False,
    )

    return preprocessor

# Usage with versioning
def save_pipeline(pipeline: ColumnTransformer, version: str, path: str) -> str:
    """Save pipeline with version metadata."""
    import hashlib
    import json
    from datetime import datetime

    artifact_path = f"{path}/feature_pipeline_v{version}.joblib"
    metadata_path = f"{path}/feature_pipeline_v{version}_metadata.json"

    joblib.dump(pipeline, artifact_path)

    metadata = {
        "version": version,
        "created_at": datetime.utcnow().isoformat(),
        "feature_names_in": list(pipeline.feature_names_in_),
        "n_features_out": pipeline.n_features_out_,
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    return artifact_path
```

### 自定义转换器模式

```python
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np
import pandas as pd

class DateFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract features from datetime columns."""

    def __init__(self, date_column: str, features: list[str] = None):
        self.date_column = date_column
        self.features = features or ['year', 'month', 'day', 'dayofweek', 'hour']

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        dt = pd.to_datetime(X[self.date_column])

        feature_map = {
            'year': dt.dt.year,
            'month': dt.dt.month,
            'day': dt.dt.day,
            'dayofweek': dt.dt.dayofweek,
            'hour': dt.dt.hour,
            'is_weekend': dt.dt.dayofweek.isin([5, 6]).astype(int),
            'quarter': dt.dt.quarter,
        }

        for feature in self.features:
            if feature in feature_map:
                X[f"{self.date_column}_{feature}"] = feature_map[feature]

        return X.drop(columns=[self.date_column])

    def get_feature_names_out(self, input_features=None):
        return [f"{self.date_column}_{f}" for f in self.features]

class TargetEncoder(BaseEstimator, TransformerMixin):
    """Target encoding for high-cardinality categorical features."""

    def __init__(self, columns: list[str], smoothing: float = 1.0):
        self.columns = columns
        self.smoothing = smoothing
        self.encodings_: dict = {}
        self.global_mean_: float = None

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.global_mean_ = y.mean()

        for col in self.columns:
            stats = y.groupby(X[col]).agg(['mean', 'count'])
            smooth = (stats['count'] * stats['mean'] + self.smoothing * self.global_mean_) / (
                stats['count'] + self.smoothing
            )
            self.encodings_[col] = smooth.to_dict()

        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col in self.columns:
            X[f"{col}_encoded"] = X[col].map(self.encodings_[col]).fillna(self.global_mean_)
        return X.drop(columns=self.columns)
```

---

## 使用 Feast 的特征存储

### 特征存储设置

```python
# feature_store.yaml
"""
project: ml_project
registry: data/registry.db
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
offline_store:
  type: file
entity_key_serialization_version: 2
"""

# features/user_features.py
from datetime import timedelta
from feast import Entity, Feature, FeatureView, FileSource, Field
from feast.types import Float32, Int64, String

# Define entity
user = Entity(
    name="user_id",
    description="User identifier",
    join_keys=["user_id"],
)

# Define data source
user_stats_source = FileSource(
    path="data/user_stats.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# Define feature view
user_stats_fv = FeatureView(
    name="user_stats",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="total_purchases", dtype=Int64),
        Field(name="avg_purchase_value", dtype=Float32),
        Field(name="days_since_last_purchase", dtype=Int64),
        Field(name="user_segment", dtype=String),
    ],
    source=user_stats_source,
    online=True,
    tags={"team": "ml", "owner": "data-science"},
)
```

### 特征获取模式

```python
from feast import FeatureStore
import pandas as pd
from datetime import datetime

class FeatureService:
    """Production feature service with Feast."""

    def __init__(self, repo_path: str = "."):
        self.store = FeatureStore(repo_path=repo_path)

    def get_training_features(
        self,
        entity_df: pd.DataFrame,
        feature_refs: list[str],
    ) -> pd.DataFrame:
        """Get historical features for training."""
        return self.store.get_historical_features(
            entity_df=entity_df,
            features=feature_refs,
        ).to_df()

    def get_online_features(
        self,
        entity_rows: list[dict],
        feature_refs: list[str],
    ) -> dict:
        """Get features for real-time inference."""
        response = self.store.get_online_features(
            entity_rows=entity_rows,
            features=feature_refs,
        )
        return response.to_dict()

    def materialize_features(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Materialize features to online store."""
        self.store.materialize(start_date=start_date, end_date=end_date)

# Usage
feature_service = FeatureService()

# Training: historical features
entity_df = pd.DataFrame({
    "user_id": [1, 2, 3],
    "event_timestamp": [datetime(2024, 1, 15)] * 3,
})

training_features = feature_service.get_training_features(
    entity_df=entity_df,
    feature_refs=[
        "user_stats:total_purchases",
        "user_stats:avg_purchase_value",
        "user_stats:days_since_last_purchase",
    ],
)

# Inference: online features
online_features = feature_service.get_online_features(
    entity_rows=[{"user_id": 1}],
    feature_refs=["user_stats:total_purchases", "user_stats:avg_purchase_value"],
)
```

---

## 使用 Great Expectations 进行数据验证

### 期望套件定义

```python
import great_expectations as gx
from great_expectations.core import ExpectationSuite
from great_expectations.checkpoint import Checkpoint

def create_feature_expectations(context: gx.DataContext) -> ExpectationSuite:
    """Define data quality expectations for features."""

    suite = context.add_expectation_suite("feature_validation_suite")

    # Column existence
    suite.add_expectation(
        gx.expectations.ExpectColumnToExist(column="user_id")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnToExist(column="purchase_amount")
    )

    # Null checks
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(column="user_id")
    )
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToNotBeNull(
            column="purchase_amount",
            mostly=0.95,  # Allow 5% nulls
        )
    )

    # Value ranges
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="purchase_amount",
            min_value=0,
            max_value=10000,
        )
    )

    # Uniqueness
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeUnique(column="transaction_id")
    )

    # Distribution checks
    suite.add_expectation(
        gx.expectations.ExpectColumnMeanToBeBetween(
            column="purchase_amount",
            min_value=50,
            max_value=500,
        )
    )

    return suite

def validate_features(
    df: pd.DataFrame,
    context: gx.DataContext,
    suite_name: str,
) -> dict:
    """Run validation and return results."""

    datasource = context.sources.add_pandas("runtime_source")
    data_asset = datasource.add_dataframe_asset("runtime_asset")
    batch_request = data_asset.build_batch_request(dataframe=df)

    checkpoint = context.add_or_update_checkpoint(
        name="feature_checkpoint",
        validations=[
            {
                "batch_request": batch_request,
                "expectation_suite_name": suite_name,
            }
        ],
    )

    result = checkpoint.run()

    return {
        "success": result.success,
        "statistics": result.run_results[list(result.run_results.keys())[0]].get("validation_result").statistics,
        "results": result.to_json_dict(),
    }
```

### 数据漂移检测

```python
from scipy import stats
import numpy as np
from dataclasses import dataclass

@dataclass
class DriftResult:
    feature: str
    drift_detected: bool
    statistic: float
    p_value: float
    method: str

class FeatureDriftDetector:
    """Detect distribution drift in features."""

    def __init__(self, significance_level: float = 0.05):
        self.significance_level = significance_level
        self.reference_stats: dict = {}

    def fit(self, reference_df: pd.DataFrame, features: list[str]) -> None:
        """Store reference distribution statistics."""
        for feature in features:
            self.reference_stats[feature] = {
                'mean': reference_df[feature].mean(),
                'std': reference_df[feature].std(),
                'values': reference_df[feature].dropna().values,
            }

    def detect_drift(
        self,
        current_df: pd.DataFrame,
        features: list[str],
    ) -> list[DriftResult]:
        """Detect drift using KS test."""
        results = []

        for feature in features:
            if feature not in self.reference_stats:
                continue

            reference_values = self.reference_stats[feature]['values']
            current_values = current_df[feature].dropna().values

            statistic, p_value = stats.ks_2samp(reference_values, current_values)

            results.append(DriftResult(
                feature=feature,
                drift_detected=p_value < self.significance_level,
                statistic=statistic,
                p_value=p_value,
                method='ks_test',
            ))

        return results

    def detect_drift_psi(
        self,
        current_df: pd.DataFrame,
        feature: str,
        bins: int = 10,
    ) -> DriftResult:
        """Detect drift using Population Stability Index."""
        reference = self.reference_stats[feature]['values']
        current = current_df[feature].dropna().values

        # Create bins from reference distribution
        bin_edges = np.percentile(reference, np.linspace(0, 100, bins + 1))
        bin_edges[0] = -np.inf
        bin_edges[-1] = np.inf

        ref_counts = np.histogram(reference, bins=bin_edges)[0] / len(reference)
        cur_counts = np.histogram(current, bins=bin_edges)[0] / len(current)

        # Avoid log(0)
        ref_counts = np.clip(ref_counts, 0.0001, None)
        cur_counts = np.clip(cur_counts, 0.0001, None)

        psi = np.sum((cur_counts - ref_counts) * np.log(cur_counts / ref_counts))

        return DriftResult(
            feature=feature,
            drift_detected=psi > 0.2,  # PSI > 0.2 indicates significant drift
            statistic=psi,
            p_value=np.nan,
            method='psi',
        )
```

---

## 特征流水线集成

### 完整特征流水线

```python
from typing import Protocol
from abc import abstractmethod
import logging

logger = logging.getLogger(__name__)

class FeatureTransformer(Protocol):
    """Protocol for feature transformers."""

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series = None) -> "FeatureTransformer": ...

    @abstractmethod
    def transform(self, X: pd.DataFrame) -> pd.DataFrame: ...

class FeaturePipeline:
    """Production feature pipeline with validation and monitoring."""

    def __init__(
        self,
        transformers: list[tuple[str, FeatureTransformer]],
        validator: FeatureDriftDetector = None,
        feature_store: FeatureService = None,
    ):
        self.transformers = transformers
        self.validator = validator
        self.feature_store = feature_store
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series = None) -> "FeaturePipeline":
        """Fit all transformers."""
        X_current = X.copy()

        for name, transformer in self.transformers:
            logger.info(f"Fitting transformer: {name}")
            transformer.fit(X_current, y)
            X_current = transformer.transform(X_current)

        if self.validator:
            numeric_cols = X_current.select_dtypes(include=[np.number]).columns.tolist()
            self.validator.fit(X_current, numeric_cols)

        self.is_fitted = True
        return self

    def transform(
        self,
        X: pd.DataFrame,
        validate: bool = True,
    ) -> tuple[pd.DataFrame, list[DriftResult]]:
        """Transform features with optional validation."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before transform")

        X_current = X.copy()

        for name, transformer in self.transformers:
            logger.info(f"Applying transformer: {name}")
            X_current = transformer.transform(X_current)

        drift_results = []
        if validate and self.validator:
            numeric_cols = X_current.select_dtypes(include=[np.number]).columns.tolist()
            drift_results = self.validator.detect_drift(X_current, numeric_cols)

            drifted = [r.feature for r in drift_results if r.drift_detected]
            if drifted:
                logger.warning(f"Drift detected in features: {drifted}")

        return X_current, drift_results

    def save(self, path: str) -> None:
        """Save pipeline artifacts."""
        import pickle

        with open(f"{path}/feature_pipeline.pkl", 'wb') as f:
            pickle.dump({
                'transformers': self.transformers,
                'validator': self.validator,
                'is_fitted': self.is_fitted,
            }, f)

    @classmethod
    def load(cls, path: str) -> "FeaturePipeline":
        """Load pipeline from artifacts."""
        import pickle

        with open(f"{path}/feature_pipeline.pkl", 'rb') as f:
            data = pickle.load(f)

        pipeline = cls(
            transformers=data['transformers'],
            validator=data['validator'],
        )
        pipeline.is_fitted = data['is_fitted']
        return pipeline
```

---

## 最佳实践

### 特征命名约定

```python
# Good: descriptive, includes transformation info
"user_total_purchases_30d"
"product_price_log_scaled"
"category_onehot_electronics"

# Bad: ambiguous, no context
"feature_1"
"x_transformed"
"col"
```

### 特征文档

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class FeatureMetadata:
    """Document feature for registry."""
    name: str
    description: str
    dtype: str
    source_table: str
    transformation: str
    owner: str
    created_at: str
    tags: list[str]
    dependencies: list[str]
    freshness_sla: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "dtype": self.dtype,
            "source_table": self.source_table,
            "transformation": self.transformation,
            "owner": self.owner,
            "created_at": self.created_at,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "freshness_sla": self.freshness_sla,
        }
```

---

## 相关参考

- `training-pipelines.md` - 在训练工作流中使用特征
- `experiment-tracking.md` - 记录特征重要性及元数据
- `model-validation.md` - 在特征集上验证模型性能

## 交叉引用技能

- **Pandas Pro** - 用于特征工程的 DataFrame 操作
- **Data Engineer** - 用于特征计算的数据流水线集成