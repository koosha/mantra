"""
Mantra - Delaware Corporate Law AI Assistant

A RAG-powered chatbot for Delaware corporate law research.
"""

__version__ = "0.1.0"

# Core components
from .data_extractor import DelawareCaseLawExtractor
from .indexer import DelawareCaseLawIndexer, LegalDocumentChunker
from .query_classifier import QueryClassifier
from .response_generator import LegalResponseGenerator

# Configuration and utilities
from .config import MantraSettings, get_settings, settings
from .utils import format_sources, extract_case_name_from_url
from .exceptions import (
    MantraException,
    IndexNotLoadedError,
    EmbeddingGenerationError,
    LLMGenerationError,
    get_http_status_code
)

__all__ = [
    # Core components
    "DelawareCaseLawExtractor",
    "DelawareCaseLawIndexer",
    "LegalDocumentChunker",
    "QueryClassifier",
    "LegalResponseGenerator",
    # Configuration
    "MantraSettings",
    "get_settings",
    "settings",
    # Utilities
    "format_sources",
    "extract_case_name_from_url",
    # Exceptions
    "MantraException",
    "IndexNotLoadedError",
    "EmbeddingGenerationError",
    "LLMGenerationError",
    "get_http_status_code",
]
