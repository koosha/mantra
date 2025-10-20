"""
Mantra - Delaware Corporate Law AI Assistant

A RAG-powered chatbot for Delaware corporate law research.
"""

__version__ = "0.1.0"

from .data_extractor import DelawareCaseLawExtractor
from .indexer import DelawareCaseLawIndexer, LegalDocumentChunker
from .query_classifier import QueryClassifier
from .response_generator import LegalResponseGenerator

__all__ = [
    "DelawareCaseLawExtractor",
    "DelawareCaseLawIndexer",
    "LegalDocumentChunker",
    "QueryClassifier",
    "LegalResponseGenerator",
]
