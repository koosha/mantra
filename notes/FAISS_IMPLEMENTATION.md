# FAISS Implementation Guide for Mantra

## Why FAISS?

Based on your decision to use FAISS, here are the key advantages for Mantra:

### Performance Benefits
- **Speed**: 10-100x faster than ChromaDB for similarity search
- **Scalability**: Can easily handle 100K+ documents if you expand beyond Delaware
- **Memory Efficiency**: Multiple index types (Flat, IVF, HNSW) for different tradeoffs
- **GPU Support**: Can leverage GPU acceleration if needed

### Trade-offs to Handle
- **Metadata Filtering**: Need to implement post-filtering (we'll handle this)
- **Persistence**: Need to manually save/load indexes (straightforward)
- **Updates**: Need to rebuild index for new documents (we'll create incremental approach)

## FAISS Index Types

### 1. IndexFlatL2 (Recommended for Start)
- **Type**: Brute force exact search
- **Speed**: Fast for < 100K vectors
- **Accuracy**: 100% (exact)
- **Memory**: ~4KB per document (1536-dim embeddings)
- **Use Case**: Perfect for 2K-10K Delaware cases

### 2. IndexIVFFlat (For Scaling)
- **Type**: Inverted file index with exact search
- **Speed**: Much faster for > 100K vectors
- **Accuracy**: 95-99% (configurable)
- **Memory**: Similar to Flat
- **Use Case**: When you expand to 50K+ cases

### 3. IndexHNSW (Advanced)
- **Type**: Hierarchical Navigable Small World
- **Speed**: Fastest for large datasets
- **Accuracy**: 95-99% (configurable)
- **Memory**: Higher than IVF
- **Use Case**: Production at scale (100K+ cases)

## Implementation Strategy

### Phase 1: Start with IndexFlatL2
- Simple, exact search
- No training required
- Perfect for current dataset size
- Easy to debug and validate

### Phase 2: Upgrade to IndexIVFFlat (if needed)
- When dataset grows > 50K cases
- Requires training on sample vectors
- Configurable speed/accuracy tradeoff

### Phase 3: Consider IndexHNSW (optional)
- For maximum performance at scale
- When you have 100K+ cases

## Metadata Filtering Strategy

Since FAISS doesn't support native metadata filtering, we'll implement a hybrid approach:

### Approach 1: Post-Filtering (Simple)
1. Retrieve top K results from FAISS (e.g., K=20)
2. Filter by metadata in Python
3. Return top N after filtering (e.g., N=4)

**Pros**: Simple, works with any FAISS index
**Cons**: May need to retrieve more results to get enough after filtering

### Approach 2: Pre-Filtering with Multiple Indexes (Advanced)
1. Create separate FAISS indexes for different metadata combinations
2. Route queries to appropriate index
3. Faster but more complex

**Pros**: Faster, more efficient
**Cons**: More indexes to manage, higher storage

### Recommended: Approach 1 (Post-Filtering)
- Simpler to implement and maintain
- Sufficient for dataset size
- Can upgrade to Approach 2 if needed

## Storage Structure

```
faiss_index/
├── index.faiss              # FAISS index file
├── metadata.pkl             # Metadata for all documents
├── docstore.pkl             # Document store (optional)
└── index_config.json        # Index configuration
```

## Metadata Schema

Each document will have associated metadata stored separately:

```python
{
    "doc_id": "case_12345_chunk_0",
    "case_id": 12345,
    "case_name": "Smith v. Van Gorkom",
    "date_filed": "1985-01-29",
    "court": "delaware-supreme",
    "citation_count": 1500,
    "chunk_index": 0,
    "total_chunks": 5,
    "topics": ["duty of care", "business judgment rule"],
    "source_url": "https://...",
    "text": "Full chunk text..."
}
```

## Incremental Updates

### Strategy for Adding New Cases

1. **Load existing index and metadata**
2. **Process new cases** (chunk, embed)
3. **Add to index** using `add()` or `add_with_ids()`
4. **Update metadata** dictionary
5. **Save updated index and metadata**

```python
# Pseudo-code
index = faiss.read_index("faiss_index/index.faiss")
metadata = load_metadata("faiss_index/metadata.pkl")

# Process new cases
new_embeddings, new_metadata = process_new_cases(new_cases)

# Add to index
index.add(new_embeddings)

# Update metadata
metadata.extend(new_metadata)

# Save
faiss.write_index(index, "faiss_index/index.faiss")
save_metadata(metadata, "faiss_index/metadata.pkl")
```

## Search with Metadata Filtering

```python
def search_with_filters(query, filters, k=4, retrieve_k=20):
    """
    Search FAISS with metadata filtering.
    
    Args:
        query: Query text
        filters: Dict of metadata filters
        k: Number of results to return
        retrieve_k: Number to retrieve before filtering
    """
    # 1. Get embeddings for query
    query_embedding = get_embedding(query)
    
    # 2. Search FAISS for top retrieve_k
    distances, indices = index.search(query_embedding, retrieve_k)
    
    # 3. Filter by metadata
    filtered_results = []
    for idx, dist in zip(indices[0], distances[0]):
        doc_metadata = metadata[idx]
        
        # Apply filters
        if matches_filters(doc_metadata, filters):
            filtered_results.append({
                "text": doc_metadata["text"],
                "metadata": doc_metadata,
                "score": dist
            })
            
            if len(filtered_results) >= k:
                break
    
    return filtered_results
```

## Performance Optimization

### 1. Batch Processing
- Process embeddings in batches of 100-1000
- Reduces API calls to OpenAI

### 2. Caching
- Cache embeddings for common queries
- Store embeddings with documents

### 3. Index Optimization
```python
# For IndexFlatL2 (no optimization needed)
index = faiss.IndexFlatL2(dimension)

# For IndexIVFFlat (when scaling)
quantizer = faiss.IndexFlatL2(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist=100)
index.train(training_vectors)  # Train on sample
index.nprobe = 10  # Search 10 clusters (speed/accuracy tradeoff)
```

### 4. Memory Management
- Use memory-mapped indexes for large datasets
- Compress vectors if needed (IndexIVFPQ)

## Migration from ChromaDB (if needed)

If you ever need to switch back to ChromaDB:

```python
# Load FAISS index and metadata
index = faiss.read_index("faiss_index/index.faiss")
metadata = load_metadata("faiss_index/metadata.pkl")

# Create ChromaDB collection
import chromadb
client = chromadb.Client()
collection = client.create_collection("delaware_cases")

# Add documents
for i, meta in enumerate(metadata):
    collection.add(
        documents=[meta["text"]],
        metadatas=[meta],
        ids=[meta["doc_id"]]
    )
```

## Monitoring and Debugging

### Key Metrics to Track
1. **Search latency**: Time to retrieve results
2. **Recall**: Are relevant cases being found?
3. **Index size**: Disk space used
4. **Memory usage**: RAM during search

### Debugging Tools
```python
# Check index stats
print(f"Total vectors: {index.ntotal}")
print(f"Index trained: {index.is_trained}")

# Test search
D, I = index.search(test_vector, k=5)
print(f"Distances: {D}")
print(f"Indices: {I}")

# Validate metadata alignment
assert len(metadata) == index.ntotal
```

## Best Practices

1. **Always save metadata with index**: Keep them in sync
2. **Version your indexes**: Save with timestamps for rollback
3. **Test before production**: Validate search quality
4. **Monitor performance**: Track latency and accuracy
5. **Backup regularly**: FAISS indexes can be large

## Example Configuration

```python
# config.py
FAISS_CONFIG = {
    "index_type": "IndexFlatL2",  # Start simple
    "dimension": 1536,  # text-embedding-3-small
    "metric": "L2",  # Euclidean distance
    "normalize_vectors": True,  # Normalize for cosine similarity
    "retrieve_k": 20,  # Retrieve before filtering
    "return_k": 4,  # Return after filtering
}
```

## Next Steps

1. Implement Component 2 with FAISS
2. Create indexing pipeline
3. Build search with post-filtering
4. Test with sample queries
5. Optimize based on performance
