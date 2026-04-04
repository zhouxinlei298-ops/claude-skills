# 向量数据库

---

## 数据库对比矩阵

| 特性 | Pinecone | Weaviate | Qdrant | Chroma | pgvector |
|------|----------|----------|--------|--------|----------|
| **托管方式** | 仅托管 | 托管 + 自托管 | 托管 + 自托管 | 自托管（云测试版） | 自托管 |
| **混合搜索** | 是（稀疏-稠密） | 是（BM25 + 向量） | 是（稀疏向量） | 有限 | 手动（+ pg_trgm） |
| **过滤功能** | 优秀 | 优秀 | 优秀 | 基础 | SQL 原生 |
| **最大维度** | 20,000 | 无限制 | 65,535 | 无限制 | 2,000 |
| **定价模式** | 按向量/查询 | 按节点 | 按节点 | 免费（开源） | 免费（扩展） |
| **多租户** | 命名空间 | 多租户类 | 集合 + 载荷 | 集合 | 模式/RLS |
| **最佳用途** | 企业 SaaS | 语义应用 | 高性能 | 原型设计 | PostgreSQL 用户 |

## 何时使用每个数据库

### Pinecone
```
Best For:
- Enterprise RAG with strict SLAs
- Teams wanting zero infrastructure management
- Applications needing sparse-dense hybrid search
- High-volume production with predictable costs

When to Avoid:
- Cost-sensitive projects (expensive at scale)
- Need for self-hosting or data residency
- Complex filtering requirements beyond metadata
- Wanting to avoid vendor lock-in
```

### Weaviate
```
Best For:
- Semantic search with built-in vectorization
- Multi-modal (text, image) applications
- GraphQL-native teams
- Hybrid BM25 + vector search requirements

When to Avoid:
- Simple embedding storage only
- Memory-constrained environments
- Teams unfamiliar with GraphQL
```

### Qdrant
```
Best For:
- High-performance, low-latency requirements
- Complex filtering with payload indexes
- Rust/performance-focused teams
- Self-hosted with full control

When to Avoid:
- Teams wanting fully managed simplicity
- GraphQL preference (REST/gRPC only)
```

### Chroma
```
Best For:
- Local development and prototyping
- LangChain/LlamaIndex integration
- Simple RAG proof-of-concepts
- Educational projects

When to Avoid:
- Production workloads at scale
- Multi-tenant applications
- High availability requirements
```

### pgvector
```
Best For:
- Existing PostgreSQL infrastructure
- Transactional + vector in same DB
- SQL-native teams
- Cost optimization (no new infra)

When to Avoid:
- Vectors > 2000 dimensions
- Billions of vectors (scaling limits)
- Sub-millisecond latency requirements
```

---

## Pinecone 设置

```python
from pinecone import Pinecone, ServerlessSpec

# Initialize client
pc = Pinecone(api_key="your-api-key")

# Create index with serverless
pc.create_index(
    name="rag-index",
    dimension=1536,  # OpenAI ada-002
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)

# Get index reference
index = pc.Index("rag-index")

# Upsert vectors with metadata
index.upsert(
    vectors=[
        {
            "id": "doc-1",
            "values": embedding_vector,
            "metadata": {
                "source": "manual.pdf",
                "page": 42,
                "section": "installation",
                "tenant_id": "acme-corp"
            }
        }
    ],
    namespace="production"
)

# Query with metadata filter
results = index.query(
    vector=query_embedding,
    top_k=10,
    include_metadata=True,
    namespace="production",
    filter={
        "tenant_id": {"$eq": "acme-corp"},
        "section": {"$in": ["installation", "setup"]}
    }
)

# Hybrid search (sparse-dense)
from pinecone_text.sparse import BM25Encoder

bm25 = BM25Encoder()
bm25.fit(corpus)  # Fit on your documents

results = index.query(
    vector=dense_embedding,
    sparse_vector=bm25.encode_queries(query_text),
    top_k=10,
    alpha=0.5  # Balance dense vs sparse
)
```

---

## Weaviate 设置

```python
import weaviate
from weaviate.classes.config import Configure, Property, DataType

# Connect to Weaviate Cloud
client = weaviate.connect_to_weaviate_cloud(
    cluster_url="https://your-cluster.weaviate.network",
    auth_credentials=weaviate.auth.AuthApiKey("your-api-key")
)

# Or self-hosted
client = weaviate.connect_to_local(
    host="localhost",
    port=8080
)

# Create collection with vectorizer
client.collections.create(
    name="Document",
    vectorizer_config=Configure.Vectorizer.text2vec_openai(
        model="text-embedding-3-small"
    ),
    properties=[
        Property(name="content", data_type=DataType.TEXT),
        Property(name="source", data_type=DataType.TEXT),
        Property(name="page", data_type=DataType.INT),
        Property(name="tenant_id", data_type=DataType.TEXT, index_filterable=True)
    ]
)

# Insert with auto-vectorization
documents = client.collections.get("Document")
documents.data.insert(
    properties={
        "content": "Installation guide content...",
        "source": "manual.pdf",
        "page": 42,
        "tenant_id": "acme-corp"
    }
)

# Or with pre-computed vector
documents.data.insert(
    properties={"content": "...", "source": "..."},
    vector=precomputed_embedding
)

# Hybrid search (BM25 + vector)
from weaviate.classes.query import MetadataQuery, Filter

results = documents.query.hybrid(
    query="how to install",
    alpha=0.5,  # 0=BM25 only, 1=vector only
    limit=10,
    filters=Filter.by_property("tenant_id").equal("acme-corp"),
    return_metadata=MetadataQuery(score=True, explain_score=True)
)

for obj in results.objects:
    print(f"Score: {obj.metadata.score}, Content: {obj.properties['content'][:100]}")

client.close()
```

---

## Qdrant 设置

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    PayloadSchemaType
)

# Connect to Qdrant Cloud
client = QdrantClient(
    url="https://your-cluster.qdrant.io",
    api_key="your-api-key"
)

# Or local
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="documents",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)

# Create payload index for fast filtering
client.create_payload_index(
    collection_name="documents",
    field_name="tenant_id",
    field_schema=PayloadSchemaType.KEYWORD
)

# Upsert points
client.upsert(
    collection_name="documents",
    points=[
        PointStruct(
            id="doc-1",
            vector=embedding_vector,
            payload={
                "content": "Installation guide...",
                "source": "manual.pdf",
                "page": 42,
                "tenant_id": "acme-corp"
            }
        )
    ]
)

# Search with filter
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=10,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="tenant_id",
                match=MatchValue(value="acme-corp")
            )
        ]
    ),
    with_payload=True
)

# Batch upsert for large datasets
from qdrant_client.models import Batch

client.upsert(
    collection_name="documents",
    points=Batch(
        ids=ids_list,
        vectors=vectors_list,
        payloads=payloads_list
    )
)
```

---

## Chroma 设置

```python
import chromadb
from chromadb.config import Settings

# Persistent local storage
client = chromadb.PersistentClient(
    path="./chroma_data",
    settings=Settings(anonymized_telemetry=False)
)

# Create collection with custom embedding function
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

embedding_fn = OpenAIEmbeddingFunction(
    api_key="your-openai-key",
    model_name="text-embedding-3-small"
)

collection = client.get_or_create_collection(
    name="documents",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

# Add documents (auto-embeds)
collection.add(
    ids=["doc-1", "doc-2"],
    documents=["Installation guide...", "Configuration steps..."],
    metadatas=[
        {"source": "manual.pdf", "page": 42},
        {"source": "manual.pdf", "page": 43}
    ]
)

# Or with pre-computed embeddings
collection.add(
    ids=["doc-3"],
    embeddings=[precomputed_vector],
    metadatas=[{"source": "guide.pdf"}],
    documents=["Original text for reference"]
)

# Query
results = collection.query(
    query_texts=["how to install"],
    n_results=10,
    where={"source": "manual.pdf"},
    include=["documents", "metadatas", "distances"]
)

# Update existing document
collection.update(
    ids=["doc-1"],
    documents=["Updated installation guide..."],
    metadatas=[{"source": "manual_v2.pdf", "page": 42}]
)
```

---

## pgvector 设置

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI dimensions
    source VARCHAR(255),
    page INTEGER,
    tenant_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index (recommended for most cases)
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Or IVFFlat for very large datasets
CREATE INDEX ON documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create index on filter columns
CREATE INDEX ON documents (tenant_id);
```

```python
import psycopg2
from pgvector.psycopg2 import register_vector

conn = psycopg2.connect("postgresql://localhost/ragdb")
register_vector(conn)

# Insert with embedding
cur = conn.cursor()
cur.execute(
    """
    INSERT INTO documents (content, embedding, source, page, tenant_id)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id
    """,
    ("Installation guide...", embedding_vector, "manual.pdf", 42, "acme-corp")
)

# Similarity search with filter
cur.execute(
    """
    SELECT id, content, source, page,
           1 - (embedding <=> %s) AS similarity
    FROM documents
    WHERE tenant_id = %s
    ORDER BY embedding <=> %s
    LIMIT 10
    """,
    (query_embedding, "acme-corp", query_embedding)
)

results = cur.fetchall()

# Hybrid search with pg_trgm
cur.execute(
    """
    SELECT id, content,
           (0.5 * (1 - (embedding <=> %s))) +
           (0.5 * similarity(content, %s)) AS hybrid_score
    FROM documents
    WHERE tenant_id = %s
      AND content %% %s  -- Trigram similarity threshold
    ORDER BY hybrid_score DESC
    LIMIT 10
    """,
    (query_embedding, query_text, "acme-corp", query_text)
)
```

---

## 索引调优指南

### HNSW 参数

| 参数 | 描述 | 权衡 |
|------|------|------|
| `m` | 每个节点的连接数 | 更高 = 更好召回率，更多内存 |
| `ef_construction` | 构建时搜索宽度 | 更高 = 更好的索引，更慢构建 |
| `ef_search` | 查询时搜索宽度 | 更高 = 更好召回率，更慢查询 |

```python
# Qdrant HNSW tuning
client.update_collection(
    collection_name="documents",
    hnsw_config=HnswConfigDiff(
        m=16,                    # Default: 16, increase for better recall
        ef_construct=100,        # Default: 100, higher for better index
        full_scan_threshold=10000  # Use brute force below this size
    )
)

# Query-time ef adjustment
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    limit=10,
    search_params=SearchParams(hnsw_ef=128)  # Higher for better recall
)
```

### 缩放量化

```python
# Qdrant scalar quantization (4x memory reduction)
from qdrant_client.models import ScalarQuantization, ScalarQuantizationConfig

client.update_collection(
    collection_name="documents",
    quantization_config=ScalarQuantization(
        scalar=ScalarQuantizationConfig(
            type="int8",
            quantile=0.99,
            always_ram=True
        )
    )
)
```

---

## 多租户模式

### 命名空间隔离（Pinecone）
```python
# Tenant data in separate namespaces
index.upsert(vectors=[...], namespace="tenant-acme")
index.upsert(vectors=[...], namespace="tenant-globex")

# Query within tenant namespace
results = index.query(
    vector=query_embedding,
    namespace="tenant-acme",
    top_k=10
)
```

### 元数据过滤（Qdrant/Weaviate）
```python
# Add tenant_id to all documents
point = PointStruct(
    id="doc-1",
    vector=embedding,
    payload={"tenant_id": "acme", "content": "..."}
)

# Always filter by tenant
results = client.search(
    collection_name="documents",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[FieldCondition(key="tenant_id", match=MatchValue(value="acme"))]
    )
)
```

### 每租户集合（高隔离性）
```python
# Create tenant-specific collection
client.create_collection(
    collection_name=f"docs_{tenant_id}",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)
```

---

## 决策流程图

```
Start
  │
  ├─ Need managed service with zero ops?
  │   └─ Yes → Pinecone
  │
  ├─ Have existing PostgreSQL?
  │   └─ Yes → pgvector (if vectors < 2000 dims)
  │
  ├─ Need built-in vectorization?
  │   └─ Yes → Weaviate
  │
  ├─ Need maximum performance + self-host?
  │   └─ Yes → Qdrant
  │
  ├─ Prototyping / local development?
  │   └─ Yes → Chroma
  │
  └─ Default recommendation → Qdrant (balance of features/performance)
```

---

## 快速参考

| 任务 | Pinecone | Weaviate | Qdrant | pgvector |
|------|----------|----------|--------|----------|
| 创建索引/集合 | `create_index()` | `collections.create()` | `create_collection()` | `CREATE TABLE` |
| 插入 | `upsert()` | `data.insert()` | `upsert()` | `INSERT` |
| 搜索 | `query()` | `query.near_vector()` | `search()` | `ORDER BY <=>` |
| 过滤 | `filter={}` | `Filter.by_property()` | `query_filter=Filter()` | `WHERE` |
| 删除 | `delete()` | `data.delete_by_id()` | `delete()` | `DELETE` |
| 混合搜索 | sparse_vector 参数 | `query.hybrid()` | 稀疏向量 | 手动 |

## 相关技能

- **Database Optimizer** - 索引调优和查询性能
- **Cloud Architect** - 向量数据库托管的架构决策
- **Python Pro** - 使用异步客户端的实现模式