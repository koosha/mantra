#!/usr/bin/env python3
"""
Script to build FAISS index from extracted case law.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mantra import DelawareCaseLawIndexer


def main():
    """Build FAISS index."""
    # Initialize indexer
    indexer = DelawareCaseLawIndexer(
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        index_path=os.getenv("FAISS_INDEX_PATH", "./faiss_index"),
        data_path=os.getenv("DATA_DIR", "./data/cases") + "/delaware_cases.json"
    )
    
    # Build index
    indexer.build_index(max_cases=None)


if __name__ == "__main__":
    main()
