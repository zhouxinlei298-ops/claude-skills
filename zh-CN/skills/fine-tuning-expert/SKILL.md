---
name: fine-tuning-expert
description: "Use when fine-tuning LLMs, training custom models, or adapting foundation models for specific tasks. Invoke for configuring LoRA/QLoRA adapters, preparing JSONL training datasets, setting hyperparameters for fine-tuning runs, adapter training, transfer learning, finetuning with Hugging Face PEFT, OpenAI fine-tuning, instruction tuning, RLHF, DPO, or quantizing and deploying fine-tuned models. Trigger terms include: LoRA, QLoRA, PEFT, finetuning, fine-tuning, adapter tuning, LLM training, model training, custom model."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: data-ml
  triggers: fine-tuning, fine tuning, finetuning, LoRA, QLoRA, PEFT, adapter tuning, transfer learning, model training, custom model, LLM training, instruction tuning, RLHF, model optimization, quantization
  role: expert
  scope: implementation
  output-format: code
  related-skills: devops-engineer
---

# Fine-Tuning Expert

高级 ML 工程师，专注于 LLM 微调、参数高效方法和生产模型优化。

## 核心工作流程

1. **数据集准备** — 验证和格式化数据；在训练开始前运行质量检查
   - 检查点：`python validate_dataset.py --input data.jsonl` — 在继续之前修复所有错误
2. **方法选择** — 根据 GPU 内存和任务需求选择 PEFT 技术
   - 大多数任务使用 LoRA；GPU 内存受限时使用 QLoRA（4 位）；仅对小模型进行全量微调
3. **训练** — 配置超参数，监控损失曲线，定期保存检查点
   - 检查点：验证损失必须下降；平稳或上升表明过拟合
4. **评估** — 与基础模型对比基准测试；在留出集和边缘情况上测试
   - 检查点：收集困惑度、任务特定指标（BLEU/ROUGE）和延迟数据
5. **部署** — 合并适配器权重，量化，在服务之前测量推理吞吐量

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| LoRA/PEFT | `references/lora-peft.md` | 参数高效微调、适配器 |
| 数据集准备 | `references/dataset-preparation.md` | 训练数据格式化、质量检查 |
| 超参数 | `references/hyperparameter-tuning.md` | 学习率、批量大小、调度器 |
| 评估 | `references/evaluation-metrics.md` | 基准测试、指标、模型比较 |
| 部署 | `references/deployment-optimization.md` | 模型合并、量化、服务 |

## 最小可行示例 — 使用 Hugging Face PEFT 进行 LoRA 微调

```python
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import torch

# 1. 加载基础模型和分词器
model_id = "meta-llama/Llama-3-8B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# 2. 配置 LoRA 适配器
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,               # rank — 增加以获得更多容量，减少以节省内存
    lora_alpha=32,      # 缩放因子；通常为 rank 的 2 倍
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()  # 验证：应为总参数的 ~0.1-1%

# 3. 加载和格式化数据集（Alpaca 风格 JSONL）
dataset = load_dataset("json", data_files={"train": "train.jsonl", "test": "test.jsonl"})

def format_prompt(example):
    return {"text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"}

dataset = dataset.map(format_prompt)

# 4. 训练参数
training_args = TrainingArguments(
    output_dir="./checkpoints",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,     # 有效批量大小 = 16
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,                 # 始终使用预热
    fp16=False,
    bf16=True,
    logging_steps=10,
    eval_strategy="steps",
    eval_steps=100,
    save_steps=200,
    load_best_model_at_end=True,
)

# 5. 训练
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["test"],
    dataset_text_field="text",
    max_seq_length=2048,
)
trainer.train()

# 6. 仅保存适配器权重
model.save_pretrained("./lora-adapter")
tokenizer.save_pretrained("./lora-adapter")
```

**QLoRA 变体** — 在加载模型之前添加以下行以启用 4 位量化：
```python
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map="auto")
```

**将适配器合并到基础模型以进行部署：**
```python
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16)
merged = PeftModel.from_pretrained(base, "./lora-adapter").merge_and_unload()
merged.save_pretrained("./merged-model")
```

## 约束

### 必须做
- 在训练之前验证数据集质量
- 对大型模型（>7B）使用参数高效方法
- 监控训练/验证损失曲线
- 记录超参数和训练配置
- 版本化数据集和模型检查点
- 始终包含学习率预热

### 不能做
- 跳过数据质量验证
- 在小数据集上过拟合 — 使用正则化（dropout、权重衰减）和早停
- 合并不兼容的适配器（rank、基础模型或目标模块不匹配）
- 不在留出集和延迟基准上评估就部署

## 输出模板

实现微调时，请始终提供：
1. **数据集准备脚本**，包含验证逻辑（模式检查、token 长度直方图、去重）
2. **训练配置**（完整的 `TrainingArguments` + `LoraConfig` 块，带注释）
3. **评估脚本**，报告困惑度、任务特定指标和延迟
4. **简要设计理由** — 为什么为此任务选择此 PEFT 方法、rank 和学习率
