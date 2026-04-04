---
name: rag-architect
description: Designs and implements production-grade RAG systems by chunking documents, generating embeddings, configuring vector stores, building hybrid search pipelines, applying reranking, and evaluating retrieval quality. Use when building RAG systems, vector databases, or knowledge-grounded AI applications requiring semantic search, document retrieval, context augmentation, similarity search, or embedding-based indexing.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: data-ml
  triggers: RAG, retrieval-augmented generation, vector search, embeddings, semantic search, vector database, document retrieval, knowledge base, context retrieval, similarity search
  role: architect
  scope: system-design
  output-format: architecture
  related-skills: python-pro, database-optimizer, monitoring-expert, api-designer
---

# RAG Architect

## 核心工作流程

1. **需求分析** — 识别检索需求、延迟约束、准确性要求和规模
2. **向量存储设计** — 选择数据库、模式设计、索引策略、分片方案
3. **分块策略** — 文档分割、重叠、语义边界、元数据丰富
4. **检索管道** — 嵌入选择、查询转换、混合搜索、重排序
5. **评估与迭代** — 指标跟踪、检索调试、持续优化

每个步骤在继续之前都要进行验证（参见下文的检查点）。

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| 向量数据库 | `references/vector-databases.md` | 比较 Pinecone、Weaviate、Chroma、pgvector、Qdrant |
| 嵌入模型 | `references/embedding-models.md` | 选择嵌入、微调、维度权衡 |
| 分块策略 | `references/chunking-strategies.md` | 文档分割、重叠、语义分块 |
| 检索优化 | `references/retrieval-optimization.md` | 混合搜索、重排序、查询扩展、过滤 |
| RAG 评估 | `references/rag-evaluation.md` | 指标、评估框架、检索调试 |

## 实现示例

### 1. 文档分块

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 在你的领域数据上评估 chunk_size — 不要盲目使用 512
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " "],
)

chunks = splitter.create_documents(
    texts=[doc.page_content for doc in raw_docs],
    metadatas=[{"source": doc.metadata["source"], "timestamp": doc.metadata.get("timestamp")} for doc in raw_docs],
)
```

**检查点：** `assert all(c.metadata.get("source") for c in chunks), "Missing source metadata"`

### 2. 生成嵌入与索引

```python
from openai import OpenAI
import qdrant_client
from qdrant_client.models import VectorParams, Distance, PointStruct

client = OpenAI()
qdrant = qdrant_client.QdrantClient("localhost", port=6333)

# 创建集合
qdrant.recreate_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
)

def embed_chunks(chunks: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    response = client.embeddings.create(input=chunks, model=model)
    return [r.embedding for r in response.data]

# 使用确定性 ID 进行幂等 upsert 和去重
import hashlib, uuid

points = []
for i, chunk in enumerate(chunks):
    doc_id = str(uuid.UUID(hashlib.md5(chunk.page_content.encode()).hexdigest()))
    embedding = embed_chunks([chunk.page_content])[0]
    points.append(PointStruct(id=doc_id, vector=embedding, payload=chunk.metadata))

qdrant.upsert(collection_name="knowledge_base", points=points)
```

**检查点：** `assert qdrant.count("knowledge_base").count == len(set(p.id for p in points)), "Deduplication failed"`

### 3. 混合搜索（向量 + BM25）

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, SparseVector
from rank_bm25 import BM25Okapi

def hybrid_search(query: str, tenant_id: str, top_k: int = 20) -> list:
    # 稠密检索
    query_embedding = embed_chunks([query])[0]
    tenant_filter = Filter(must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))])
    dense_results = qdrant.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=tenant_filter,
        limit=top_k,
    )

    # 稀疏检索（BM25）
    corpus = [r.payload.get("text", "") for r in dense_results]
    bm25 = BM25Okapi([doc.split() for doc in corpus])
    bm25_scores = bm25.get_scores(query.split())

    # 倒数排名融合
    ranked = sorted(
        zip(dense_results, bm25_scores),
        key=lambda x: 0.6 * x[0].score + 0.4 * x[1],
        reverse=True,
    )
    return [r for r, _ in ranked[:top_k]]
```

**检查点：** `assert len(hybrid_search("test query", tenant_id="demo")) > 0, "Hybrid search returned no results"`

### 4. 重排序 Top-K 结果

```python
import cohere

co = cohere.Client("YOUR_API_KEY")

def rerank(query: str, results: list, top_n: int = 5) -> list:
    docs = [r.payload.get("text", "") for r in results]
    reranked = co.rerank(query=query, documents=docs, top_n=top_n, model="rerank-english-v3.0")
    return [results[r.index] for r in reranked.results]
```

### 5. 检索评估

```python
# 针对标注的评估集运行 precision@k 和 recall@k
# python evaluate.py --metrics precision@10 recall@10 mrr --collection knowledge_base

from ragas import evaluate
from ragas.metrics import context_precision, context_recall, faithfulness, answer_relevancy
from datasets import Dataset

eval_dataset = Dataset.from_dict({
    "question": questions,
    "contexts": retrieved_contexts,
    "answer": generated_answers,
    "ground_truth": ground_truth_answers,
})

results = evaluate(eval_dataset, metrics=[context_precision, context_recall, faithfulness, answer_relevancy])
print(results)
```

**检查点：** 在进入 LLM 集成之前，目标 `context_precision >= 0.7` 和 `context_recall >= 0.6`。

## 约束

### 必须做
- 在确定之前，在你的领域数据上评估多个嵌入模型
- 为生产系统实现混合搜索（向量 + 关键词）
- 为多租户或特定领域检索添加元数据过滤器
- 衡量检索指标（precision@k、recall@k、MRR、NDCG）
- 在将上下文传递给 LLM 之前对 top-k 结果进行重排序
- 使用确定性 ID 实现幂等摄入和去重
- 持续监控检索延迟和质量
- 版本化嵌入并规划模型迁移

### 不能做
- 不在你的领域数据上评估就使用默认分块大小（512）
- 跳过元数据丰富（来源、时间戳、章节）
- 仅关注 LLM 输出质量而忽略检索质量指标
- 存储未预处理/清洗的原始文档
- 仅使用余弦相似度处理复杂的多领域检索
- 不在生产规模数据量上测试就部署
- 忘记处理边缘情况（空结果、格式错误的文档）
- 将嵌入模型与应用代码紧密耦合

## 输出模板

设计 RAG 架构时，请交付：
1. 系统架构图（摄入 + 检索管道）
2. 向量数据库选择及权衡分析
3. 分块策略及示例和理由
4. 检索管道设计（查询 → 结果流程）
5. 包含指标、基准和通过/失败阈值的评估计划
