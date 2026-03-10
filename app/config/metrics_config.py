"""
Metrics configuration for Prometheus monitoring.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class MetricType(Enum):
    """Types of metrics supported."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricConfig:
    """Configuration for a single metric."""
    name: str
    description: str
    metric_type: MetricType
    labels: List[str]
    unit: Optional[str] = None
    help_text: Optional[str] = None


class MetricsConfig:
    """Configuration for all application metrics."""
    
    # Document processing metrics
    DOCUMENT_PROCESSING_TOTAL = MetricConfig(
        name="document_processing_total",
        description="Total number of documents processed",
        metric_type=MetricType.COUNTER,
        labels=["document_type", "status", "user_id"],
        unit="documents"
    )
    
    DOCUMENT_PROCESSING_DURATION = MetricConfig(
        name="document_processing_duration_seconds",
        description="Time taken to process documents",
        metric_type=MetricType.HISTOGRAM,
        labels=["document_type", "status"],
        unit="seconds"
    )
    
    DOCUMENT_SIZE_BYTES = MetricConfig(
        name="document_size_bytes",
        description="Size of processed documents",
        metric_type=MetricType.HISTOGRAM,
        labels=["document_type"],
        unit="bytes"
    )
    
    # PII detection metrics
    PII_DETECTION_TOTAL = MetricConfig(
        name="pii_detection_total",
        description="Total number of PII entities detected",
        metric_type=MetricType.COUNTER,
        labels=["entity_type", "document_type"],
        unit="entities"
    )
    
    PII_DETECTION_RATE = MetricConfig(
        name="pii_detection_rate",
        description="Rate of PII detection per document",
        metric_type=MetricType.GAUGE,
        labels=["document_type"],
        unit="rate"
    )
    
    # LLM extraction metrics
    LLM_EXTRACTION_CONFIDENCE = MetricConfig(
        name="llm_extraction_confidence",
        description="Confidence scores for LLM field extraction",
        metric_type=MetricType.HISTOGRAM,
        labels=["field_name", "document_type"],
        unit="score"
    )
    
    LLM_EXTRACTION_TOTAL = MetricConfig(
        name="llm_extraction_total",
        description="Total number of fields extracted by LLM",
        metric_type=MetricType.COUNTER,
        labels=["field_name", "document_type", "status"],
        unit="fields"
    )
    
    # Error metrics
    ERROR_TOTAL = MetricConfig(
        name="error_total",
        description="Total number of errors by category",
        metric_type=MetricType.COUNTER,
        labels=["error_type", "component", "document_type"],
        unit="errors"
    )
    
    # System metrics
    ACTIVE_CONNECTIONS = MetricConfig(
        name="active_connections",
        description="Number of active connections",
        metric_type=MetricType.GAUGE,
        labels=["connection_type"],
        unit="connections"
    )
    
    QUEUE_SIZE = MetricConfig(
        name="queue_size",
        description="Current queue size for processing",
        metric_type=MetricType.GAUGE,
        labels=["queue_name"],
        unit="tasks"
    )
    
    # HTTP metrics (handled by starlette-exporter)
    HTTP_REQUEST_DURATION = MetricConfig(
        name="http_request_duration_seconds",
        description="HTTP request duration",
        metric_type=MetricType.HISTOGRAM,
        labels=["method", "endpoint", "status_code"],
        unit="seconds"
    )
    
    HTTP_REQUEST_TOTAL = MetricConfig(
        name="http_request_total",
        description="Total HTTP requests",
        metric_type=MetricType.COUNTER,
        labels=["method", "endpoint", "status_code"],
        unit="requests"
    )
    
    @classmethod
    def get_all_metrics(cls) -> List[MetricConfig]:
        """Get all metric configurations."""
        return [
            cls.DOCUMENT_PROCESSING_TOTAL,
            cls.DOCUMENT_PROCESSING_DURATION,
            cls.DOCUMENT_SIZE_BYTES,
            cls.PII_DETECTION_TOTAL,
            cls.PII_DETECTION_RATE,
            cls.LLM_EXTRACTION_CONFIDENCE,
            cls.LLM_EXTRACTION_TOTAL,
            cls.ERROR_TOTAL,
            cls.ACTIVE_CONNECTIONS,
            cls.QUEUE_SIZE,
            cls.HTTP_REQUEST_DURATION,
            cls.HTTP_REQUEST_TOTAL,
        ]
    
    @classmethod
    def get_metrics_by_type(cls, metric_type: MetricType) -> List[MetricConfig]:
        """Get metrics filtered by type."""
        return [m for m in cls.get_all_metrics() if m.metric_type == metric_type]


class MetricsSettings:
    """Settings for metrics collection."""
    
    # Collection intervals (in seconds)
    COLLECTION_INTERVAL = 30
    METRICS_RETENTION_HOURS = 24 * 7  # 7 days
    
    # Prometheus configuration
    PROMETHEUS_ENABLED = True
    PROMETHEUS_PORT = 8000
    PROMETHEUS_PATH = "/metrics"
    
    # Metrics labels
    DEFAULT_LABELS = {
        "service": "document-analyzer",
        "version": "1.0.0",
        "environment": "production"
    }
    
    # Performance thresholds
    SLOW_REQUEST_THRESHOLD = 5.0  # seconds
    ERROR_RATE_THRESHOLD = 0.05   # 5%
    
    @classmethod
    def get_prometheus_config(cls) -> Dict:
        """Get Prometheus-specific configuration."""
        return {
            "port": cls.PROMETHEUS_PORT,
            "path": cls.PROMETHEUS_PATH,
            "enabled": cls.PROMETHEUS_ENABLED,
            "default_labels": cls.DEFAULT_LABELS
        }