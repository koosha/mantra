# Final Technology Stack for Mantra Case Law RAG

## ✅ Confirmed Stack

### Vector Database: **FAISS**
- **Version**: faiss-cpu 1.7.4
- **Index Type**: IndexFlatL2 (to start)
- **Why**: Performance, scalability, and speed for similarity search

### Embeddings: **OpenAI text-embedding-3-small**
- **Dimensions**: 1536
- **Cost**: $0.02 per 1M tokens
- **Why**: Excellent quality-to-cost ratio, 6.5x cheaper than large model

### LLM: **GPT-4**
- **Model**: gpt-4
- **Temperature**: 0 (for consistent legal analysis)
- **Why**: Best reasoning for complex legal queries

### Framework: **LangChain**
- **Version**: 0.1.0
- **Why**: Excellent FAISS integration, RAG patterns, and chain management

### UI: **Streamlit**
- **Version**: 1.30.0
- **Why**: Rapid development, great for chat interfaces

### Data Source: **CourtListener API**
- **Focus**: Delaware Supreme Court & Chancery Court
- **Date Range**: 2005-present
- **Topics**: Corporate governance (fiduciary duty, Revlon, Corwin, etc.)

---

## Updated Files

### 1. `requirements.txt`
```
# Core LangChain
langchain==0.1.0
langchain-community==0.0.20
langchain-openai==0.0.5

# Vector Database
faiss-cpu==1.7.4

# OpenAI
openai==1.12.0

# Web Framework
streamlit==1.30.0

# Utilities
python-dotenv==1.0.0
requests==2.31.0
numpy==1.24.3
pickle5==0.0.11

# Document Processing
pypdf==3.17.1
unstructured==0.10.30
```

### 2. `.env.example`
```
OPENAI_API_KEY=your-openai-api-key-here
COURTLISTENER_API_TOKEN=your-courtlistener-token-here
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4
FAISS_INDEX_PATH=./faiss_index
METADATA_PATH=./faiss_index/metadata.pkl
DATA_DIR=./data/cases
```

### 3. `app.py`
- Updated to use FAISS instead of ChromaDB
- Using OpenAI embeddings (text-embedding-3-small)
- Using GPT-4 for LLM
- Simplified imports

---

## FAISS Implementation Strategy

### Phase 1: Basic Implementation (Current)
- **Index Type**: IndexFlatL2
- **Search**: Exact similarity search
- **Metadata**: Post-filtering approach
- **Dataset**: 2K-10K Delaware cases

### Phase 2: Optimization (If Needed)
- **Index Type**: IndexIVFFlat
- **Search**: Approximate with configurable accuracy
- **When**: Dataset grows > 50K cases

### Phase 3: Advanced (Optional)
- **Index Type**: IndexHNSW
- **Search**: Maximum performance
- **When**: Dataset > 100K cases or need GPU acceleration

---

## Metadata Filtering Approach

Since FAISS doesn't support native metadata filtering, we'll use **post-filtering**:

1. **Retrieve** top K results from FAISS (e.g., K=20)
2. **Filter** by metadata in Python (court, date, topics)
3. **Return** top N after filtering (e.g., N=4)

**Benefits**:
- Simple to implement
- Works with any FAISS index
- Sufficient for dataset size
- Can upgrade to pre-filtering if needed

---

## Storage Structure

```
faiss_index/
├── index.faiss              # FAISS vector index
├── metadata.pkl             # Document metadata
├── docstore.pkl             # Document store
└── index_config.json        # Configuration

data/
└── cases/
    ├── delaware_cases.json  # Raw case data
    ├── summary_stats.json   # Statistics
    └── individual/          # Individual cases
```

---

## Cost Analysis

### One-Time Indexing Cost
- **Dataset**: 2,500 cases × 6,500 tokens = 16.25M tokens
- **Embedding Cost**: $0.33 (text-embedding-3-small)

### Monthly Operating Cost (1,000 queries)
- **Query Embeddings**: ~$0.05
- **LLM (GPT-4)**: ~$150
- **Total**: ~$150/month

### Cost Optimization Options
- Use GPT-4o-mini for simpler queries (~$15/month instead of $150)
- Cache common queries
- Batch processing for indexing

---

## Performance Expectations

### Search Latency
- **FAISS Search**: < 10ms for 10K vectors
- **OpenAI Embedding**: ~100-200ms per query
- **GPT-4 Generation**: ~2-5 seconds
- **Total**: ~2-5 seconds per query

### Scalability
- **Current**: 2K-10K cases (excellent performance)
- **Future**: Can scale to 100K+ with IndexIVFFlat
- **GPU**: Can add GPU support if needed

---

## Key Advantages of FAISS

1. **Speed**: 10-100x faster than ChromaDB for similarity search
2. **Scalability**: Handles millions of vectors efficiently
3. **Flexibility**: Multiple index types for different needs
4. **Memory Efficiency**: Optimized memory usage
5. **Production Ready**: Battle-tested by Meta
6. **GPU Support**: Can leverage GPU acceleration

---

## Trade-offs Handled

1. **No Native Metadata Filtering**
   - ✅ Solution: Post-filtering approach

2. **Manual Persistence**
   - ✅ Solution: Save/load with pickle and FAISS methods

3. **Index Updates**
   - ✅ Solution: Incremental add with metadata sync

4. **Complexity**
   - ✅ Solution: LangChain abstracts most complexity

---

## Next Steps

### Immediate (Component 2)
1. ✅ Data extraction (completed)
2. 🔄 Document processing and chunking
3. 🔄 Embedding generation
4. 🔄 FAISS index creation
5. 🔄 Metadata management

### Short-term (Components 3-4)
- Query classification
- Relevance filtering
- Response generation
- Citation formatting

### Medium-term (Component 5)
- Enhanced UI
- Search filters
- Source display
- Query suggestions

---

## Migration Notes

If you ever need to switch to ChromaDB or another vector DB:

```python
# FAISS to ChromaDB
from langchain_community.vectorstores import Chroma

# Load FAISS
faiss_store = FAISS.load_local("faiss_index", embeddings)

# Convert to ChromaDB
docs = faiss_store.docstore._dict.values()
chroma_store = Chroma.from_documents(docs, embeddings)
```

LangChain's VectorStore interface makes this straightforward.

---

## Documentation Created

1. ✅ `FAISS_IMPLEMENTATION.md` - Detailed FAISS guide
2. ✅ `TECH_STACK_FINAL.md` - This document
3. ✅ `TECH_STACK_COMPARISON.md` - Original comparison
4. ✅ `COMPONENT_1_SUMMARY.md` - Data extraction guide
5. ✅ Updated `requirements.txt`
6. ✅ Updated `.env.example`
7. ✅ Updated `app.py`

---

## Ready to Proceed

All files updated for FAISS. Ready to implement **Component 2: Document Processing & Indexing**.
