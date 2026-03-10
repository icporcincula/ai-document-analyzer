# app/exceptions/__init__.py
from .handlers import setup_exception_handlers

class DocumentProcessingError(Exception):
    """Custom exception for document processing errors"""
    def __init__(self, message: str, document_id: str = None, original_error: Exception = None):
        self.message = message
        self.document_id = document_id
        self.original_error = original_error
        super().__init__(self.message)

class PIIAnonymizationError(Exception):
    """Custom exception for PII anonymization errors"""
    def __init__(self, message: str, entity_type: str = None, original_error: Exception = None):
        self.message = message
        self.entity_type = entity_type
        self.original_error = original_error
        super().__init__(self.message)

class ExtractionError(Exception):
    """Custom exception for AI extraction errors"""
    def __init__(self, message: str, model: str = None, original_error: Exception = None):
        self.message = message
        self.model = model
        self.original_error = original_error
        super().__init__(self.message)

class ConfigurationError(Exception):
    """Custom exception for configuration errors"""
    def __init__(self, message: str, config_key: str = None, original_error: Exception = None):
        self.message = message
        self.config_key = config_key
        self.original_error = original_error
        super().__init__(self.message)

class RateLimitError(Exception):
    """Custom exception for rate limiting errors"""
    def __init__(self, message: str, retry_after: int = None, original_error: Exception = None):
        self.message = message
        self.retry_after = retry_after
        self.original_error = original_error
        super().__init__(self.message)

class HealthCheckError(Exception):
    """Custom exception for health check failures"""
    def __init__(self, message: str, service: str = None, original_error: Exception = None):
        self.message = message
        self.service = service
        self.original_error = original_error
        super().__init__(self.message)