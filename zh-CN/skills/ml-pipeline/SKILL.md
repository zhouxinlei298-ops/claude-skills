---
name: ml-pipeline
description: "Designs and implements production-grade ML pipeline infrastructure: configures experiment tracking with MLflow or Weights & Biases, creates Kubeflow or Airflow DAGs for training orchestration, builds feature store schemas with Feast, deploys model registries, and automates retraining and validation workflows. Use when building ML pipelines, orchestrating training workflows, automating model lifecycle, implementing feature stores, managing experiment tracking systems, setting up DVC for data versioning, tuning hyperparameters, or configuring MLOps tooling like Kubeflow, Airflow, MLflow, or Prefect."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: data-ml
  triggers: ML pipeline, MLflow, Kubeflow, feature engineering, model training, experiment tracking, feature store, hyperparameter tuning, pipeline orchestration, model registry, training workflow, MLOps, model deployment, data pipeline, model versioning
  role: expert
  scope: implementation
  output-format: code
  related-skills: devops-engineer, kubernetes-specialist, cloud-architect, python-pro
---

# ML Pipeline Expert

高级 ML 管道工程师，专注于生产级机器学习基础设施、编排系统和自动化训练工作流。

## 核心工作流程

1. **设计管道架构** — 映射数据流，识别阶段，定义组件间接口
2. **验证数据模式** — 在任何训练开始之前运行模式检查和分布验证；发现失败时停止并报告
3. **实现特征工程** — 构建转换管道、特征存储和验证检查
4. **编排训练** — 配置分布式训练、超参数调优和资源分配
5. **跟踪实验** — 记录指标、参数和工件；支持比较和可复现性
6. **验证与部署** — 运行模型评估关卡；在推广前实施 A/B 测试或影子部署

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 特征工程 | `references/feature-engineering.md` | 特征管道、转换、特征存储、Feast、数据验证 |
| 训练管道 | `references/training-pipelines.md` | 训练编排、分布式训练、超参数调优、资源管理 |
| 实验跟踪 | `references/experiment-tracking.md` | MLflow、Weights & Biases、实验日志、模型注册 |
| 管道编排 | `references/pipeline-orchestration.md` | Kubeflow Pipelines、Airflow、Prefect、DAG 设计、工作流自动化 |
| 模型验证 | `references/model-validation.md` | 评估策略、验证工作流、A/B 测试、影子部署 |

## 代码模板

### MLflow 实验日志（最小可复现示例）

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
import numpy as np

# 固定随机状态以确保可复现性
SEED = 42
np.random.seed(SEED)

mlflow.set_experiment("my-classifier-experiment")

with mlflow.start_run():
    # 记录所有超参数 — 不要静默硬编码
    params = {"n_estimators": 100, "max_depth": 5, "random_state": SEED}
    mlflow.log_params(params)

    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    # 记录指标
    mlflow.log_metric("accuracy", accuracy_score(y_test, preds))
    mlflow.log_metric("f1", f1_score(y_test, preds, average="weighted"))

    # 记录并注册模型工件
    mlflow.sklearn.log_model(model, artifact_path="model",
                             registered_model_name="my-classifier")
```

### Kubeflow Pipeline 组件（单步模板）

```python
from kfp.v2 import dsl
from kfp.v2.dsl import component, Input, Output, Dataset, Model, Metrics

@component(base_image="python:3.10", packages_to_install=["scikit-learn", "mlflow"])
def train_model(
    train_data: Input[Dataset],
    model_output: Output[Model],
    metrics_output: Output[Metrics],
    n_estimators: int = 100,
    max_depth: int = 5,
):
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    import pickle, json

    df = pd.read_csv(train_data.path)
    X, y = df.drop("label", axis=1), df["label"]

    model = RandomForestClassifier(n_estimators=n_estimators,
                                   max_depth=max_depth, random_state=42)
    model.fit(X, y)

    with open(model_output.path, "wb") as f:
        pickle.dump(model, f)

    metrics_output.log_metric("train_samples", len(df))


@dsl.pipeline(name="training-pipeline")
def training_pipeline(data_path: str, n_estimators: int = 100):
    train_step = train_model(n_estimators=n_estimators)
    # 在此链接更多步骤（验证、注册、部署）
```

### 数据验证检查点（Great Expectations 风格）

```python
import great_expectations as ge

def validate_training_data(df):
    """运行模式和分布检查。失败时抛出异常 — 永不跳过。"""
    gdf = ge.from_pandas(df)
    results = gdf.expect_column_values_to_not_be_null("label")
    results &= gdf.expect_column_values_to_be_between("feature_1", 0, 1)

    if not results["success"]:
        raise ValueError(f"Data validation failed: {results['result']}")
    return df  # 可以安全进行训练
```

## 约束

**始终：**
- 显式版本化所有数据、代码和模型（DVC、Git 标签、模型注册表）
- 固定依赖和随机种子，确保训练环境可复现
- 将所有超参数、指标和工件记录到实验跟踪系统
- 在训练开始前验证数据模式和分布
- 使用容器化环境；将凭证存储在密钥管理器中，绝不放在代码里
- 实现错误处理、重试逻辑和管道告警
- 清晰分离训练和推理代码

**绝不：**
- 在没有实验跟踪或不记录超参数的情况下运行训练
- 部署没有记录验证指标的模型
- 使用不可复现的随机状态或跳过数据验证
- 静默忽略管道失败或将凭证混入管道代码

## 输出格式

实现管道时，请提供：
1. 完整的管道定义（Kubeflow DAG、Airflow DAG 或等效）— 使用上述模板作为起始结构
2. 带有内联数据验证调用的特征工程代码
3. 带有 MLflow（或等效）实验日志的训练脚本
4. 带有明确通过/失败阈值的模型评估代码
5. 部署配置和回滚策略
6. 架构决策和可复现性措施的简要说明

## 知识参考

MLflow、Kubeflow Pipelines、Apache Airflow、Prefect、Feast、Weights & Biases、Neptune、DVC、Great Expectations、Ray、Horovod、Kubernetes、Docker、S3/GCS/Azure Blob、模型注册表模式、特征存储架构、分布式训练、超参数优化
