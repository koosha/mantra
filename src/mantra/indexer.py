import os
import json
import pickle
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import faiss
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LegalDocumentChunker:
    """
    Intelligent chunking for legal documents.
    Preserves legal structure and citations.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target size for each chunk
            chunk_overlap: Overlap between chunks to preserve context
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Legal-aware separators (in order of preference)
        self.separators = [
            "\n\n\n",  # Major section breaks
            "\n\n",    # Paragraph breaks
            "\n",      # Line breaks
            ". ",      # Sentence breaks
            ", ",      # Clause breaks
            " ",       # Word breaks
        ]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=self.separators
        )
    
    def chunk_case(self, case_data: Dict) -> List[Dict]:
        """
        Chunk a single case into smaller pieces with metadata.
        
        Args:
            case_data: Case dictionary from data_extractor
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        plain_text = case_data.get("plain_text", "")
        
        if not plain_text or len(plain_text.strip()) < 100:
            logger.warning(f"Case {case_data.get('id')} has insufficient text")
            return []
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(plain_text)
        
        # Create chunk documents with metadata
        chunk_docs = []
        for i, chunk_text in enumerate(chunks):
            chunk_doc = {
                "text": chunk_text,
                "metadata": {
                    "case_id": case_data.get("id"),
                    "case_name": case_data.get("case_name", "Unknown"),
                    "case_name_full": case_data.get("case_name_full", ""),
                    "date_filed": case_data.get("date_filed", ""),
                    "court": case_data.get("court", ""),
                    "citation_count": case_data.get("citation_count", 0),
                    "author_str": case_data.get("author_str", ""),
                    "absolute_url": case_data.get("absolute_url", ""),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_id": f"case_{case_data.get('id')}_chunk_{i}",
                }
            }
            chunk_docs.append(chunk_doc)
        
        return chunk_docs


class DelawareCaseLawIndexer:
    """
    Creates and manages FAISS index for Delaware case law.
    """
    
    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        index_path: str = "./faiss_index",
        data_path: str = "./data/cases/delaware_cases.json"
    ):
        """
        Initialize the indexer.
        
        Args:
            embedding_model: OpenAI embedding model to use
            index_path: Path to save FAISS index
            data_path: Path to case law JSON data
        """
        self.embedding_model = embedding_model
        self.index_path = index_path
        self.data_path = data_path
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Initialize chunker
        self.chunker = LegalDocumentChunker(chunk_size=1000, chunk_overlap=200)
        
        # Create index directory
        os.makedirs(index_path, exist_ok=True)
        
        # Index and metadata will be loaded/created
        self.index = None
        self.metadata = []
        self.dimension = 1536  # Default for text-embedding-3-small
    
    def load_cases(self) -> List[Dict]:
        """
        Load cases from JSON file.
        
        Returns:
            List of case dictionaries
        """
        logger.info(f"Loading cases from {self.data_path}")
        
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        logger.info(f"Loaded {len(cases)} cases")
        return cases
    
    def process_cases(self, cases: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Process cases into chunks with metadata.

        Args:
            cases: List of case dictionaries

        Returns:
            Tuple of (texts, metadata)
        """
        logger.info("Processing cases into chunks...")

        all_chunks = []
        for case in cases:
            chunks = self.chunker.chunk_case(case)
            all_chunks.extend(chunks)

        # Extract texts for embedding generation
        texts = [chunk["text"] for chunk in all_chunks]

        # Create metadata that includes the text
        metadata = []
        for chunk in all_chunks:
            meta = chunk["metadata"].copy()
            meta["text"] = chunk["text"]  # Keep text with metadata
            metadata.append(meta)

        logger.info(f"Created {len(texts)} chunks from {len(cases)} cases")
        logger.info(f"Average chunks per case: {len(texts) / len(cases):.1f}")

        return texts, metadata
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """
        Generate embeddings for texts in batches.
        
        Args:
            texts: List of text strings
            batch_size: Number of texts to embed at once
            
        Returns:
            Numpy array of embeddings
        """
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        logger.info(f"Using model: {self.embedding_model}")
        
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")
            
            try:
                # Generate embeddings for batch
                batch_embeddings = self.embeddings.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {batch_num}: {e}")
                raise
        
        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        logger.info(f"Generated embeddings shape: {embeddings_array.shape}")
        
        return embeddings_array
    
    def create_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """
        Create FAISS index from embeddings.
        
        Args:
            embeddings: Numpy array of embeddings
            
        Returns:
            FAISS index
        """
        logger.info("Creating FAISS index...")
        
        dimension = embeddings.shape[1]
        self.dimension = dimension
        
        # Create IndexFlatL2 for exact search
        # L2 distance (can normalize for cosine similarity)
        index = faiss.IndexFlatL2(dimension)
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add vectors to index
        index.add(embeddings)
        
        logger.info(f"Created FAISS index with {index.ntotal} vectors")
        logger.info(f"Index dimension: {dimension}")
        logger.info(f"Index type: IndexFlatL2 (exact search)")
        
        return index
    
    def save_index(self, index: faiss.Index, metadata: List[Dict]):
        """
        Save FAISS index and metadata to disk.
        
        Args:
            index: FAISS index
            metadata: List of metadata dictionaries
        """
        logger.info(f"Saving index to {self.index_path}")
        
        # Save FAISS index
        index_file = os.path.join(self.index_path, "index.faiss")
        faiss.write_index(index, index_file)
        logger.info(f"Saved FAISS index: {index_file}")
        
        # Save metadata
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        logger.info(f"Saved metadata: {metadata_file}")
        
        # Save configuration
        config = {
            "embedding_model": self.embedding_model,
            "dimension": self.dimension,
            "total_vectors": index.ntotal,
            "index_type": "IndexFlatL2",
            "created_at": datetime.now().isoformat(),
            "total_cases": len(set(m["case_id"] for m in metadata)),
            "total_chunks": len(metadata),
        }
        
        config_file = os.path.join(self.index_path, "config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved configuration: {config_file}")
    
    def load_index(self) -> Tuple[faiss.Index, List[Dict]]:
        """
        Load FAISS index and metadata from disk.
        
        Returns:
            Tuple of (index, metadata)
        """
        logger.info(f"Loading index from {self.index_path}")
        
        # Load FAISS index
        index_file = os.path.join(self.index_path, "index.faiss")
        if not os.path.exists(index_file):
            raise FileNotFoundError(f"Index file not found: {index_file}")
        
        index = faiss.read_index(index_file)
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
        
        # Load metadata
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        if not os.path.exists(metadata_file):
            raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
        
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        logger.info(f"Loaded metadata for {len(metadata)} chunks")
        
        # Load configuration
        config_file = os.path.join(self.index_path, "config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Index created at: {config.get('created_at')}")
            logger.info(f"Total cases: {config.get('total_cases')}")
        
        self.index = index
        self.metadata = metadata
        
        return index, metadata
    
    def build_index(self, max_cases: Optional[int] = None):
        """
        Build complete FAISS index from case law data.
        
        Args:
            max_cases: Maximum number of cases to process (for testing)
        """
        logger.info("=" * 80)
        logger.info("Building FAISS Index for Delaware Case Law")
        logger.info("=" * 80)
        
        # Load cases
        cases = self.load_cases()
        
        if max_cases:
            cases = cases[:max_cases]
            logger.info(f"Limited to {max_cases} cases for testing")
        
        # Process cases into chunks
        texts, metadata = self.process_cases(cases)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts, batch_size=100)
        
        # Create FAISS index
        index = self.create_faiss_index(embeddings)
        
        # Save index and metadata
        self.save_index(index, metadata)
        
        # Store in instance
        self.index = index
        self.metadata = metadata
        
        logger.info("=" * 80)
        logger.info("INDEX BUILD COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total cases indexed: {len(cases)}")
        logger.info(f"Total chunks created: {len(texts)}")
        logger.info(f"Average chunks per case: {len(texts) / len(cases):.1f}")
        logger.info(f"Index saved to: {self.index_path}")
        logger.info("=" * 80)
    
    def search(
        self,
        query: str,
        k: int = 4,
        filters: Optional[Dict] = None,
        retrieve_k: int = 20
    ) -> List[Dict]:
        """
        Search the index with optional metadata filtering.
        
        Args:
            query: Query text
            k: Number of results to return
            filters: Metadata filters (e.g., {"court": "delaware-supreme"})
            retrieve_k: Number to retrieve before filtering
            
        Returns:
            List of result dictionaries
        """
        if self.index is None:
            raise ValueError("Index not loaded. Call load_index() or build_index() first.")
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_vector)
        
        # Search FAISS
        distances, indices = self.index.search(query_vector, retrieve_k)
        
        # Collect results with metadata
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                result = {
                    "text": self.metadata[idx].get("text", ""),
                    "metadata": self.metadata[idx],
                    "score": float(dist),
                    "similarity": 1 - float(dist)  # Convert distance to similarity
                }
                
                # Apply filters if provided
                if filters:
                    if self._matches_filters(result["metadata"], filters):
                        results.append(result)
                else:
                    results.append(result)
                
                # Stop if we have enough results
                if len(results) >= k:
                    break
        
        return results[:k]
    
    def _matches_filters(self, metadata: Dict, filters: Dict) -> bool:
        """
        Check if metadata matches filters.
        
        Args:
            metadata: Document metadata
            filters: Filter criteria
            
        Returns:
            True if matches all filters
        """
        for key, value in filters.items():
            if key not in metadata:
                return False
            
            # Handle different filter types
            if isinstance(value, dict):
                # Range filters (e.g., {"date_filed": {"$gte": "2020-01-01"}})
                if "$gte" in value and metadata[key] < value["$gte"]:
                    return False
                if "$lte" in value and metadata[key] > value["$lte"]:
                    return False
                if "$gt" in value and metadata[key] <= value["$gt"]:
                    return False
                if "$lt" in value and metadata[key] >= value["$lt"]:
                    return False
            else:
                # Exact match
                if metadata[key] != value:
                    return False
        
        return True


def main():
    """
    Main function to build the index.
    """
    # Initialize indexer
    indexer = DelawareCaseLawIndexer(
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        index_path=os.getenv("FAISS_INDEX_PATH", "./faiss_index"),
        data_path=os.getenv("DATA_DIR", "./data/cases") + "/delaware_cases.json"
    )
    
    # Build index
    # Set max_cases to a small number for testing (e.g., 10)
    # Set to None to process all cases
    indexer.build_index(max_cases=None)


if __name__ == "__main__":
    main()
