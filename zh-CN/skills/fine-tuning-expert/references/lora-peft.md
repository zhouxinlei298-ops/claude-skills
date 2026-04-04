# LoRA 和参数高效微调

---

## 概述

参数高效微调（PEFT）方法只训练模型参数的一小部分，同时保持基础模型冻结。这大大减少了内存需求，使在消费级硬件上微调大模型成为可能。

## 何时使用 PEFT 与全微调

| 方法 | 使用场景 | 避免场景 |
|--------|----------|------------|
| **LoRA** | 7B+ 模型，VRAM 有限，需要多个任务适配器 | 非常小的模型（<1B），需要最高质量 |
| **QLoRA** | 13B+ 模型，单 GPU，内存受限 | 高吞吐量训练，推理速度关键 |
| **全微调** | 小模型，计算资源充足，需要最高性能 | 大模型，资源有限 |
| **前缀微调** | 生成任务，需要可解释的软提示 | 复杂推理任务 |
| **IA3** | 极端效率需求，推理开销关键 | 需要高适配器容量的任务 |

## LoRA 配置

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2"  # Use Flash Attention if available
)

# LoRA configuration for instruction tuning
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                          # Rank - start with 8-16, increase if underfitting
    lora_alpha=32,                 # Alpha - typically 2x rank
    lora_dropout=0.05,             # Dropout for regularization
    target_modules=[               # Target attention layers
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
        "gate_proj", "up_proj", "down_proj"       # MLP (optional, increases capacity)
    ],
    bias="none",                   # "none", "all", or "lora_only"
    modules_to_save=None           # Modules to train fully (e.g., embed_tokens for new tokens)
)

# Create PEFT model
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: 13,631,488 || all params: 8,043,163,648 || trainable%: 0.1695
```

### 秩选择指南

```python
def recommend_lora_rank(task_complexity: str, dataset_size: int, model_size_b: float) -> int:
    """
    Recommend LoRA rank based on task and resources.

    Args:
        task_complexity: "simple" (classification), "moderate" (QA), "complex" (creative)
        dataset_size: Number of training examples
        model_size_b: Model size in billions of parameters
    """
    base_rank = {
        "simple": 8,
        "moderate": 16,
        "complex": 32
    }[task_complexity]

    # Adjust for dataset size
    if dataset_size < 1000:
        rank = max(4, base_rank // 2)  # Reduce rank to prevent overfitting
    elif dataset_size > 50000:
        rank = min(64, base_rank * 2)  # Can support higher rank
    else:
        rank = base_rank

    # Adjust for model size (larger models may need lower rank)
    if model_size_b > 30:
        rank = max(4, rank // 2)

    return rank

# Example usage
rank = recommend_lora_rank("moderate", dataset_size=10000, model_size_b=8)
print(f"Recommended rank: {rank}")  # 16
```

## QLoRA 配置

QLoRA 将 4-bit 量化与 LoRA 结合，实现极高的内存效率。

```python
from transformers import BitsAndBytesConfig
import torch

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NormalFloat4 for better quality
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True        # Nested quantization for more savings
)

# Load quantized model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B",
    quantization_config=bnb_config,
    device_map="auto",
    attn_implementation="flash_attention_2"
)

# Prepare model for kbit training
from peft import prepare_model_for_kbit_training
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

# Apply LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)
```

### 内存比较

| 模型 | 全微调 | LoRA (r=16) | QLoRA (r=16) |
|-------|---------|-------------|--------------|
| Llama 3.1 8B | ~64 GB | ~18 GB | ~6 GB |
| Llama 3.1 70B | ~560 GB | ~160 GB | ~48 GB |
| Mistral 7B | ~56 GB | ~16 GB | ~5 GB |

## 使用 PEFT 训练

```python
from transformers import TrainingArguments, Trainer
from trl import SFTTrainer

training_args = TrainingArguments(
    output_dir="./lora-output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,      # Effective batch size = 16
    learning_rate=2e-4,                  # Higher LR for LoRA than full FT
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    logging_steps=10,
    save_strategy="steps",
    save_steps=100,
    evaluation_strategy="steps",
    eval_steps=100,
    bf16=True,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": False},
    optim="paged_adamw_8bit",            # Memory-efficient optimizer
    max_grad_norm=0.3,
    group_by_length=True,                # Group similar length sequences
    report_to="wandb"
)

# Using TRL's SFTTrainer for instruction tuning
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
    packing=True,                        # Pack short sequences for efficiency
    dataset_text_field="text"
)

trainer.train()
```

## 目标模块选择

不同架构有不同的模块名称：

```python
# Common target modules by architecture
TARGET_MODULES = {
    "llama": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "mistral": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "falcon": ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"],
    "gpt2": ["c_attn", "c_proj", "c_fc"],
    "phi": ["q_proj", "k_proj", "v_proj", "dense", "fc1", "fc2"],
    "qwen2": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
}

def get_target_modules(model_name: str, include_mlp: bool = True) -> list[str]:
    """Get appropriate target modules for a model architecture."""
    name_lower = model_name.lower()

    for arch, modules in TARGET_MODULES.items():
        if arch in name_lower:
            if include_mlp:
                return modules
            # Return only attention modules
            attention_keywords = ["q_proj", "k_proj", "v_proj", "o_proj", "query", "key", "value", "attn"]
            return [m for m in modules if any(kw in m.lower() for kw in attention_keywords)]

    # Default for unknown architectures - inspect model
    raise ValueError(f"Unknown architecture: {model_name}. Inspect model.named_modules() to find target modules.")
```

## 适配器合并策略

```python
from peft import PeftModel

# Load base model and adapter
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B")
model = PeftModel.from_pretrained(base_model, "path/to/lora-adapter")

# Method 1: Merge adapter weights into base model
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./merged-model")

# Method 2: Merge multiple adapters (weighted combination)
from peft import add_weighted_adapter

# Load multiple adapters
model = PeftModel.from_pretrained(base_model, "adapter1", adapter_name="adapter1")
model.load_adapter("adapter2", adapter_name="adapter2")
model.load_adapter("adapter3", adapter_name="adapter3")

# Combine with weights
model.add_weighted_adapter(
    adapters=["adapter1", "adapter2", "adapter3"],
    weights=[0.5, 0.3, 0.2],
    adapter_name="combined",
    combination_type="linear"  # or "svd", "cat"
)
model.set_adapter("combined")
```

## DoRA（权重分解 LoRA）

DoRA 通过将权重分解为幅度和方向分量来改进 LoRA。

```python
from peft import LoraConfig

# DoRA configuration
dora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    use_dora=True,  # Enable DoRA
    task_type=TaskType.CAUSAL_LM
)

# Training is identical to LoRA
model = get_peft_model(model, dora_config)
```

## rsLoRA（秩稳定 LoRA）

更高秩的适当缩放：

```python
from peft import LoraConfig

# rsLoRA for high-rank training
rslora_config = LoraConfig(
    r=64,  # Higher rank
    lora_alpha=64,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    use_rslora=True,  # Rank-stabilized scaling
    task_type=TaskType.CAUSAL_LM
)
```

## 常见问题与解决方案

### 问题：损失不下降

```python
# Check 1: Verify adapter is training
for name, param in model.named_parameters():
    if param.requires_grad:
        print(f"Training: {name}")

# Check 2: Increase rank or alpha
config = LoraConfig(r=32, lora_alpha=64, ...)

# Check 3: Reduce learning rate
training_args = TrainingArguments(learning_rate=1e-4, ...)
```

### 问题：内存不足

```python
# Solution 1: Use QLoRA
bnb_config = BitsAndBytesConfig(load_in_4bit=True, ...)

# Solution 2: Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Solution 3: Reduce batch size, increase gradient accumulation
training_args = TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16
)

# Solution 4: Use 8-bit optimizer
training_args = TrainingArguments(optim="paged_adamw_8bit")
```

### 问题：适配器无法加载

```python
# Ensure architecture matches
from peft import PeftModel, PeftConfig

# Check adapter config
config = PeftConfig.from_pretrained("path/to/adapter")
print(f"Base model: {config.base_model_name_or_path}")
print(f"Target modules: {config.target_modules}")

# Load with correct base model
base_model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
model = PeftModel.from_pretrained(base_model, "path/to/adapter")
```

## 快速参考

| 参数 | 典型范围 | 影响 |
|-----------|---------------|--------|
| `r`（秩） | 4-64 | 适配器容量；越高表达能力越强 |
| `lora_alpha` | r 到 2*r | 缩放因子；越高更新幅度越大 |
| `lora_dropout` | 0.0-0.1 | 正则化；小数据集增加此值 |
| `learning_rate` | 1e-5 到 3e-4 | LoRA 比全微调容忍更高的 LR |
| `target_modules` | attention + MLP | 更多模块 = 更高容量 + 内存 |

## 相关参考

- `hyperparameter-tuning.md` - 学习率调度器、批量大小
- `deployment-optimization.md` - 适配器合并、推理量化
- `dataset-preparation.md` - 训练数据格式化

---