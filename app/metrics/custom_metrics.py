"""
Custom Prometheus metrics for document processing.
"""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from prometheus_client.exposition import generate_latest
from starlette_exporter import PrometheusMiddleware

from app.config.metrics_config import MetricsConfig, MetricsSettings


class DocumentAnalyzerMetrics:
    """Custom metrics for document processing operations."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize custom metrics."""
        self.registry = registry or CollectorRegistry()
        
        # Document processing metrics
        self.document_processing_total = Counter(
            'document_processing_total',
            'Total number of documents processed',
            ['document_type', 'status', 'user_id'],
            registry=self.registry
        )
        
        self.document_processing_duration = Histogram(
            'document_processing_duration_seconds',
            'Time taken to process documents',
            ['document_type', 'status'],
            registry=self.registry
        )
        
        self.document_size_bytes = Histogram(
            'document_size_bytes',
            'Size of processed documents',
            ['document_type'],
            registry=self.registry,
            buckets=(1024, 10240, 102400, 1048576, 10485760, 104857600)
        )
        
        # PII detection metrics
        self.pii_detection_total = Counter(
            'pii_detection_total',
            'Total number of PII entities detected',
            ['entity_type', 'document_type'],
            registry=self.registry
        )
        
        self.pii_detection_rate = Gauge(
            'pii_detection_rate',
            'Rate of PII detection per document',
            ['document_type'],
            registry=self.registry
        )
        
        # LLM extraction metrics
        self.llm_extraction_confidence = Histogram(
            'llm_extraction_confidence',
            'Confidence scores for LLM field extraction',
            ['field_name', 'document_type'],
            registry=self.registry,
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
        )
        
        self.llm_extraction_total = Counter(
            'llm_extraction_total',
            'Total number of fields extracted by LLM',
            ['field_name', 'document_type', 'status'],
            registry=self.registry
        )
        
        # Error metrics
        self.error_total = Counter(
            'error_total',
            'Total number of errors by category',
            ['error_type', 'component', 'document_type'],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            'active_connections',
            'Number of active connections',
            ['connection_type'],
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'queue_size',
            'Current queue size for processing',
            ['queue_name'],
            registry=self.registry
        )
    
    def record_document_processing(
        self, 
        document_type: str, 
        status: str, 
        duration: float,
        user_id: str = "anonymous",
        document_size: Optional[int] = None
    ):
        """Record document processing metrics."""
        # Record total count
        self.document_processing_total.labels(
            document_type=document_type,
            status=status,
            user_id=user_id
        ).inc()
        
        # Record duration
        self.document_processing_duration.labels(
            document_type=document_type,
            status=status
        ).observe(duration)
        
        # Record document size if provided
        if document_size is not None:
            self.document_size_bytes.labels(
                document_type=document_type
            ).observe(document_size)
    
    def record_pii_detection(
        self, 
        entity_type: str, 
        document_type: str,
        count: int = 1
    ):
        """Record PII detection metrics."""
        self.pii_detection_total.labels(
            entity_type=entity_type,
            document_type=document_type
        ).inc(count)
    
    def update_pii_detection_rate(self, document_type: str, rate: float):
        """Update PII detection rate."""
        self.pii_detection_rate.labels(
            document_type=document_type
        ).set(rate)
    
    def record_llm_extraction(
        self,
        field_name: str,
        document_type: str,
        confidence: float,
        status: str = "success"
    ):
        """Record LLM extraction metrics."""
        # Record confidence score
        self.llm_extraction_confidence.labels(
            field_name=field_name,
            document_type=document_type
        ).observe(confidence)
        
        # Record extraction count
        self.llm_extraction_total.labels(
            field_name=field_name,
            document_type=document_type,
            status=status
        ).inc()
    
    def record_error(
        self,
        error_type: str,
        component: str,
        document_type: Optional[str] = None
    ):
        """Record error metrics."""
        labels = {
            'error_type': error_type,
            'component': component
        }
        if document_type:
            labels['document_type'] = document_type
        
        self.error_total.labels(**labels).inc()
    
    def update_active_connections(self, connection_type: str, count: int):
        """Update active connections count."""
        self.active_connections.labels(
            connection_type=connection_type
        ).set(count)
    
    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size."""
        self.queue_size.labels(
            queue_name=queue_name
        ).set(size)
    
    @contextmanager
    def time_document_processing(
        self, 
        document_type: str,
        user_id: str = "anonymous"
    ):
        """Context manager to time document processing."""
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            self.record_document_processing(
                document_type=document_type,
                status="success",
                duration=duration,
                user_id=user_id
            )
        except Exception as e:
            duration = time.time() - start_time
            self.record_document_processing(
                document_type=document_type,
                status="error",
                duration=duration,
                user_id=user_id
            )
            self.record_error(
                error_type=type(e).__name__,
                component="document_processing",
                document_type=document_type
            )
            raise
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics."""
        return {
            "document_processing": {
                "total": self.document_processing_total._value._value,
                "duration": {
                    "avg": self.document_processing_duration._sum._value / max(1, self.document_processing_duration._count._value),
                    "max": self.document_processing_duration._buckets[-1][1] if self.document_processing_duration._buckets else 0
                }
            },
            "pii_detection": {
                "total": self.pii_detection_total._value._value,
            },
            "llm_extraction": {
                "total": self.llm_extraction_total._value._value,
                "avg_confidence": self.llm_extraction_confidence._sum._value / max(1, self.llm_extraction_confidence._count._value)
            },
            "errors": {
                "total": self.error_total._value._value
            }
        }
    
    def generate_metrics_output(self) -> bytes:
        """Generate Prometheus metrics output."""
        return generate_latest(self.registry)


# Global metrics instance
metrics = DocumentAnalyzerMetrics()


def get_metrics() -> DocumentAnalyzerMetrics:
    """Get the global metrics instance."""
    return metrics


def setup_prometheus_middleware(app):
    """Set up Prometheus middleware for FastAPI."""
    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)
    
    # Add metrics endpoint
    from fastapi import APIRouter
    from fastapi.responses import Response
    
    router = APIRouter()
    
    @router.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        """Prometheus metrics endpoint."""
        return Response(
            content=metrics.generate_metrics_output(),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    
    app.include_router(router)
    
    return app