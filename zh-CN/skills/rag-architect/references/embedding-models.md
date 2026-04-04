# 嵌入模型

---

## 模型比较矩阵

| 模型 | 维度 | 最大 Tokens | 优势 | 提供者 |
|------|------|------------|------|--------|
| **text-embedding-3-large** | 3072（或 256-3072） | 8191 | 最佳质量，灵活维度 | OpenAI |
| **text-embedding-3-small** | 1536（或 256-1536） | 8191 | 成本效益好，质量好 | OpenAI |
| **embed-english-v3.0** | 1024 | 512 | 优秀的压缩，快速 | Cohere |
| **embed-multilingual-v3.0** | 1024 | 512 | 100+ 种语言 | Cohere |
| **voyage-large-2** | 1536 | 16000 | 长上下文，代码感知 | Voyage AI |
| **voyage-code-2** | 1536 | 16000 | 代码检索专家 | Voyage AI |
| **BGE-large-en-v1.5** | 1024 | 512 | 开源，高质量 | BAAI |
| **BGE-M3** | 1024 | 8192 | 多语言，多粒度 | BAAI |
| **E5-large-v2** | 1024 | 512 | 强大的基准性能 | Microsoft |
| **GTE-large** | 1024 | 512 | 良好的通用型 | Alibaba |
| **all-MiniLM-L6-v2** | 384 | 256 | 快速，轻量级 | Sentence Transformers |
| **nomic-embed-text-v1.5** | 768 | 8192 | 长上下文，开放权重 | Nomic AI |

---

## 何时使用每个模型

### OpenAI text-embedding-3-large
```
Best For:
- Production RAG requiring highest accuracy
- Enterprise applications with quality SLAs
- Flexible dimension requirements (can reduce to save cost)
- English and major languages

When to Avoid:
- Cost-sensitive high-volume applications
- Air-gapped or offline deployments
- Specialized domains without fine-tuning budget
```

### OpenAI text-embedding-3-small
```
Best For:
- Cost-effective production deployments
- Good quality-to-cost ratio
- General-purpose retrieval tasks
- Quick prototyping with API simplicity

When to Avoid:
- Maximum accuracy requirements
- Specialized technical domains
- When open-source is required
```

### Cohere embed-v3
```
Best For:
- Multi-lingual applications (100+ languages)
- Search-optimized retrieval (search_document/search_query types)
- Compression (int8/binary quantization built-in)
- Production with cost constraints

When to Avoid:
- Very long documents (512 token limit)
- Code-heavy retrieval tasks
```

### Voyage AI
```
Best For:
- Code retrieval and technical documentation
- Long-context documents (16K tokens)
- Domain-specific fine-tuning options
- Legal/financial specialized models

When to Avoid:
- Budget-constrained projects
- Simple general-purpose retrieval
```

### BGE / E5（开源）
```
Best For:
- Self-hosted deployments
- Air-gapped environments
- Cost elimination (no API fees)
- Fine-tuning on custom domains

When to Avoid:
- Teams without GPU infrastructure
- Need for zero maintenance
- Maximum out-of-box quality
```

---

## OpenAI 嵌入

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

def get_embedding(
    text: str,
    model: str = "text-embedding-3-small",
    dimensions: int | None = None
) -> list[float]:
    """Get embedding with optional dimension reduction."""
    params = {"input": text, "model": model}
    if dimensions:
        params["dimensions"] = dimensions

    response = client.embeddings.create(**params)
    return response.data[0].embedding

# Single embedding
embedding = get_embedding("How do I install the software?")

# Batch embeddings (more efficient)
def get_embeddings_batch(
    texts: list[str],
    model: str = "text-embedding-3-small",
    dimensions: int | None = None
) -> list[list[float]]:
    """Batch embed multiple texts."""
    params = {"input": texts, "model": model}
    if dimensions:
        params["dimensions"] = dimensions

    response = client.embeddings.create(**params)
    # Sort by index to maintain order
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

embeddings = get_embeddings_batch(["text1", "text2", "text3"])

# Dimension reduction (cost/storage savings)
# text-embedding-3-large: 3072 -> 1024 (66% storage savings)
reduced_embedding = get_embedding(
    "Installation guide...",
    model="text-embedding-3-large",
    dimensions=1024  # Reduce from 3072
)
```

### 维度权衡

| 原始维度 | 减少后 | 质量损失 | 存储节省 |
|----------|--------|----------|----------|
| 3072 | 1536 | ~1-2% | 50% |
| 3072 | 1024 | ~2-4% | 67% |
| 3072 | 512 | ~5-8% | 83% |
| 3072 | 256 | ~10-15% | 92% |

---

## Cohere 嵌入

```python
import cohere

co = cohere.Client(api_key="your-api-key")

# Document embeddings (for indexing)
doc_embeddings = co.embed(
    texts=["Installation guide content...", "Configuration steps..."],
    model="embed-english-v3.0",
    input_type="search_document",  # Use for documents being indexed
    truncate="END"
).embeddings

# Query embeddings (for search)
query_embedding = co.embed(
    texts=["how to install"],
    model="embed-english-v3.0",
    input_type="search_query",  # Use for search queries
).embeddings[0]

# Multilingual
multilingual_embedding = co.embed(
    texts=["Comment installer le logiciel?"],  # French
    model="embed-multilingual-v3.0",
    input_type="search_query"
).embeddings[0]

# Compressed embeddings (int8)
compressed = co.embed(
    texts=["Document content..."],
    model="embed-english-v3.0",
    input_type="search_document",
    embedding_types=["int8"]  # 4x smaller than float32
).embeddings
```

### Cohere 输入类型

| 类型 | 使用场景 |
|------|----------|
| `search_document` | 在向量数据库中索引的文档 |
| `search_query` | 用户搜索查询 |
| `classification` | 文本分类任务 |
| `clustering` | 文档聚类 |

---

## Voyage AI 嵌入

```python
import voyageai

vo = voyageai.Client(api_key="your-api-key")

# General embeddings
result = vo.embed(
    texts=["Installation guide for the software..."],
    model="voyage-large-2",
    input_type="document"
)
embeddings = result.embeddings

# Code embeddings (specialized)
code_result = vo.embed(
    texts=[
        "def install_package(name):\n    subprocess.run(['pip', 'install', name])",
        "How do I install packages in Python?"
    ],
    model="voyage-code-2",
    input_type="document"  # or "query" for search
)

# Long context (up to 16K tokens)
long_doc_embedding = vo.embed(
    texts=[very_long_document],  # Up to 16K tokens
    model="voyage-large-2",
    input_type="document"
).embeddings[0]
```

---

## 开源模型（Sentence Transformers）

```python
from sentence_transformers import SentenceTransformer

# Load model (downloads on first use)
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

# Single embedding
embedding = model.encode("How do I install the software?")

# Batch encoding (GPU accelerated)
embeddings = model.encode(
    ["doc1", "doc2", "doc3"],
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True  # For cosine similarity
)

# BGE requires instruction prefix for queries
query_embedding = model.encode(
    "Represent this sentence for searching relevant passages: How do I install?"
)

# GPU acceleration
model = SentenceTransformer("BAAI/bge-large-en-v1.5", device="cuda")

# Multi-GPU encoding
pool = model.start_multi_process_pool()
embeddings = model.encode_multi_process(
    sentences=large_corpus,
    pool=pool,
    batch_size=64
)
model.stop_multi_process_pool(pool)
```

### BGE-M3（多语言，多粒度）

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

# Dense, sparse, and colbert embeddings in one call
output = model.encode(
    ["Installation guide in English", "Guide d'installation en francais"],
    return_dense=True,
    return_sparse=True,
    return_colbert_vecs=True
)

dense_embeddings = output["dense_vecs"]
sparse_embeddings = output["lexical_weights"]
colbert_embeddings = output["colbert_vecs"]
```

---

## 嵌入模型微调

### 何时微调

| 场景 | 建议 |
|------|------|
| 领域特定术语（法律、医疗） | 在领域语料库上微调 |
| 检索精度低（<80%） | 使用硬负样本微调 |
| 分布外的查询 | 使用查询-文档对微调 |
| 成本优化 | 微调小模型匹配大模型 |

### 使用 Sentence Transformers 微调

```python
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# Prepare training data
train_examples = [
    InputExample(
        texts=["query: how to install", "doc: Installation guide content..."],
        label=1.0  # Relevance score
    ),
    InputExample(
        texts=["query: how to install", "doc: Unrelated content..."],
        label=0.0  # Negative example
    ),
]

# Load base model
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# Create dataloader
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)

# Contrastive loss for similarity learning
train_loss = losses.CosineSimilarityLoss(model)

# Fine-tune
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=3,
    warmup_steps=100,
    output_path="./fine-tuned-model"
)

# Or use Multiple Negatives Ranking Loss (better for retrieval)
train_examples_mnrl = [
    InputExample(texts=["query", "positive_doc", "negative_doc1", "negative_doc2"])
]
train_loss = losses.MultipleNegativesRankingLoss(model)
```

### 硬负样本挖掘

```python
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search
import torch

def mine_hard_negatives(
    queries: list[str],
    positives: list[str],
    corpus: list[str],
    model: SentenceTransformer,
    top_k: int = 10
) -> list[InputExample]:
    """Mine hard negatives from corpus for each query-positive pair."""

    query_embeddings = model.encode(queries, convert_to_tensor=True)
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
    positive_set = set(positives)

    examples = []
    for i, query in enumerate(queries):
        # Find similar documents that are NOT the positive
        hits = semantic_search(
            query_embeddings[i:i+1],
            corpus_embeddings,
            top_k=top_k + 1
        )[0]

        hard_negatives = [
            corpus[hit["corpus_id"]]
            for hit in hits
            if corpus[hit["corpus_id"]] not in positive_set
        ][:3]  # Top 3 hard negatives

        examples.append(InputExample(
            texts=[query, positives[i]] + hard_negatives
        ))

    return examples
```

---

## 嵌入管道最佳实践

### 文本预处理

```python
import re
from typing import Callable

def clean_for_embedding(text: str) -> str:
    """Clean text before embedding."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that don't add meaning
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
    # Truncate to reasonable length (model dependent)
    text = text[:8000]  # Leave room for tokenization expansion
    return text.strip()

def preprocess_for_embedding(
    text: str,
    prefix: str = "",
    max_length: int = 8000
) -> str:
    """Preprocess with optional prefix (for instruction-tuned models)."""
    cleaned = clean_for_embedding(text)
    prefixed = f"{prefix}{cleaned}" if prefix else cleaned
    return prefixed[:max_length]

# BGE-style prefix for queries
query_text = preprocess_for_embedding(
    "how to install",
    prefix="Represent this sentence for searching relevant passages: "
)
```

### 嵌入缓存

```python
import hashlib
import json
from functools import lru_cache
from pathlib import Path

class EmbeddingCache:
    """Disk-based embedding cache."""

    def __init__(self, cache_dir: str = ".embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _hash_key(self, text: str, model: str) -> str:
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> list[float] | None:
        key = self._hash_key(text, model)
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())
        return None

    def set(self, text: str, model: str, embedding: list[float]) -> None:
        key = self._hash_key(text, model)
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps(embedding))

# Usage
cache = EmbeddingCache()

def get_embedding_cached(text: str, model: str = "text-embedding-3-small") -> list[float]:
    cached = cache.get(text, model)
    if cached:
        return cached

    embedding = get_embedding(text, model)  # Call API
    cache.set(text, model, embedding)
    return embedding
```

### 批处理策略

```python
from typing import Iterator
import asyncio
from openai import AsyncOpenAI

def batch_texts(texts: list[str], batch_size: int = 100) -> Iterator[list[str]]:
    """Yield batches of texts."""
    for i in range(0, len(texts), batch_size):
        yield texts[i:i + batch_size]

async def get_embeddings_async(
    texts: list[str],
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
    max_concurrent: int = 5
) -> list[list[float]]:
    """Async batch embedding with concurrency control."""
    client = AsyncOpenAI()
    semaphore = asyncio.Semaphore(max_concurrent)

    async def embed_batch(batch: list[str]) -> list[list[float]]:
        async with semaphore:
            response = await client.embeddings.create(
                input=batch,
                model=model
            )
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

    batches = list(batch_texts(texts, batch_size))
    results = await asyncio.gather(*[embed_batch(b) for b in batches])

    # Flatten results
    return [emb for batch_result in results for emb in batch_result]
```

---

## 模型选择流程图

```
Start
  │
  ├─ Need offline/self-hosted?
  │   └─ Yes → BGE-large or E5-large (open source)
  │
  ├─ Multi-lingual requirement?
  │   └─ Yes → Cohere embed-multilingual-v3 or BGE-M3
  │
  ├─ Code/technical documentation?
  │   └─ Yes → Voyage-code-2
  │
  ├─ Long documents (>8K tokens)?
  │   └─ Yes → Voyage-large-2 or nomic-embed-text
  │
  ├─ Cost is primary concern?
  │   └─ Yes → text-embedding-3-small (reduced dims)
  │
  ├─ Maximum quality needed?
  │   └─ Yes → text-embedding-3-large
  │
  └─ Default → text-embedding-3-small (best balance)
```

---

## 快速参考

| 任务 | 推荐 |
|------|------|
| 生产 RAG（英语） | text-embedding-3-small/large |
| 多语言 | Cohere embed-multilingual-v3 |
| 代码检索 | Voyage-code-2 |
| 自托管 | BGE-large-en-v1.5 |
| 长文档 | Voyage-large-2, nomic-embed-text |
| 原型设计 | all-MiniLM-L6-v2（快速，免费） |
| 最高质量 | text-embedding-3-large |
| 成本优化 | text-embedding-3-small @ 512 dims |

## 相关技能

- **RAG Architect** - 向量数据库集成
- **Python Pro** - 异步嵌入管道
- **ML Pipeline** - 嵌入模型部署
- **Fine-Tuning Expert** - 自定义嵌入训练