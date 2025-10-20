"""
Test script for the FAISS indexer.
Tests indexing and search functionality with a small sample.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mantra import DelawareCaseLawIndexer


def test_indexing():
    """Test building a small index."""
    print("=" * 80)
    print("Testing FAISS Indexer")
    print("=" * 80)
    
    # Initialize indexer
    indexer = DelawareCaseLawIndexer(
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        index_path="./faiss_index_test",
        data_path="./data/cases/delaware_cases.json"
    )
    
    print("\n1. Building index with 5 cases for testing...")
    print("This will take a minute or two...\n")
    
    # Build index with limited cases
    indexer.build_index(max_cases=5)
    
    print("\n2. Testing search functionality...")
    
    # Test queries
    test_queries = [
        "What is fiduciary duty?",
        "Explain the business judgment rule",
        "What are the requirements for entire fairness review?"
    ]
    
    for query in test_queries:
        print(f"\n{'=' * 80}")
        print(f"Query: {query}")
        print('=' * 80)
        
        results = indexer.search(query, k=2)
        
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Case: {result['metadata']['case_name']}")
            print(f"  Date: {result['metadata']['date_filed']}")
            print(f"  Court: {result['metadata']['court']}")
            print(f"  Similarity: {result['similarity']:.4f}")
            print(f"  Text preview: {result['text'][:200]}...")
    
    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\nIf you see search results above, the indexer is working correctly!")
    print("You can now run the full indexing with: python indexer.py")
    print("=" * 80)


def test_filters():
    """Test search with metadata filters."""
    print("\n" + "=" * 80)
    print("Testing Metadata Filtering")
    print("=" * 80)
    
    # Load existing test index
    indexer = DelawareCaseLawIndexer(
        index_path="./faiss_index_test",
        data_path="./data/cases/delaware_cases.json"
    )
    
    try:
        indexer.load_index()
        
        # Test with court filter
        print("\nSearching with filter: court='delaware-supreme'")
        results = indexer.search(
            query="fiduciary duty",
            k=2,
            filters={"court": "delaware-supreme"}
        )
        
        print(f"Found {len(results)} results from Delaware Supreme Court")
        for result in results:
            print(f"  - {result['metadata']['case_name']} ({result['metadata']['court']})")
        
        # Test with date filter
        print("\nSearching with filter: date_filed >= 2015-01-01")
        results = indexer.search(
            query="fiduciary duty",
            k=2,
            filters={"date_filed": {"$gte": "2015-01-01"}}
        )
        
        print(f"Found {len(results)} results from 2015 onwards")
        for result in results:
            print(f"  - {result['metadata']['case_name']} ({result['metadata']['date_filed']})")
        
        print("\n" + "=" * 80)
        print("Filter Test Complete!")
        print("=" * 80)
        
    except FileNotFoundError:
        print("Test index not found. Run test_indexing() first.")


if __name__ == "__main__":
    # Run indexing test
    test_indexing()
    
    # Run filter test
    test_filters()
