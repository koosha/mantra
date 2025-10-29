"""
Custom exceptions for Mantra application.
Provides specific error types for better error handling and debugging.
"""


class MantraException(Exception):
    """Base exception for all Mantra-specific errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class IndexError(MantraException):
    """Base exception for index-related errors."""
    pass


class IndexNotLoadedError(IndexError):
    """Raised when trying to use an index that hasn't been loaded."""

    def __init__(self, index_path: str = None):
        message = "FAISS index not loaded"
        details = {"index_path": index_path} if index_path else {}
        super().__init__(message, details)


class IndexNotFoundError(IndexError):
    """Raised when index files cannot be found."""

    def __init__(self, index_path: str):
        message = f"Index files not found at: {index_path}"
        super().__init__(message, {"index_path": index_path})


class IndexDimensionMismatchError(IndexError):
    """Raised when loaded index dimension doesn't match current embedding model."""

    def __init__(self, expected: int, actual: int, model: str):
        message = "Index dimension mismatch"
        details = {
            "expected_dimension": expected,
            "actual_dimension": actual,
            "embedding_model": model
        }
        super().__init__(message, details)


class EmbeddingError(MantraException):
    """Base exception for embedding generation errors."""
    pass


class EmbeddingGenerationError(EmbeddingError):
    """Raised when embedding generation fails."""

    def __init__(self, message: str, model: str = None, batch_size: int = None):
        details = {}
        if model:
            details["model"] = model
        if batch_size:
            details["batch_size"] = batch_size
        super().__init__(message, details)


class LLMError(MantraException):
    """Base exception for LLM-related errors."""
    pass


class LLMGenerationError(LLMError):
    """Raised when LLM response generation fails."""

    def __init__(self, message: str, model: str = None, prompt_length: int = None):
        details = {}
        if model:
            details["model"] = model
        if prompt_length:
            details["prompt_length"] = prompt_length
        super().__init__(message, details)


class LLMRateLimitError(LLMError):
    """Raised when LLM API rate limit is exceeded."""

    def __init__(self, retry_after: int = None):
        message = "LLM API rate limit exceeded"
        details = {"retry_after_seconds": retry_after} if retry_after else {}
        super().__init__(message, details)


class DataError(MantraException):
    """Base exception for data-related errors."""
    pass


class DataNotFoundError(DataError):
    """Raised when required data files cannot be found."""

    def __init__(self, file_path: str):
        message = f"Data file not found: {file_path}"
        super().__init__(message, {"file_path": file_path})


class DataValidationError(DataError):
    """Raised when data fails validation checks."""

    def __init__(self, message: str, field: str = None, value: any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, details)


class ConfigurationError(MantraException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, setting: str = None):
        details = {"setting": setting} if setting else {}
        super().__init__(message, details)


class ClassificationError(MantraException):
    """Raised when query classification fails."""

    def __init__(self, message: str, query: str = None):
        details = {"query": query[:100] if query else None}
        super().__init__(message, details)


# HTTP Status Code Mappings for FastAPI
ERROR_STATUS_CODES = {
    IndexNotLoadedError: 503,  # Service Unavailable
    IndexNotFoundError: 503,
    IndexDimensionMismatchError: 500,  # Internal Server Error
    EmbeddingGenerationError: 500,
    LLMGenerationError: 500,
    LLMRateLimitError: 429,  # Too Many Requests
    DataNotFoundError: 404,  # Not Found
    DataValidationError: 400,  # Bad Request
    ConfigurationError: 500,
    ClassificationError: 500,
}


def get_http_status_code(exception: Exception) -> int:
    """
    Get appropriate HTTP status code for an exception.

    Args:
        exception: Exception instance

    Returns:
        HTTP status code (defaults to 500 for unknown errors)
    """
    return ERROR_STATUS_CODES.get(type(exception), 500)
