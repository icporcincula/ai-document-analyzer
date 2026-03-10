"""
Metrics collection middleware for FastAPI.
"""

import time
import logging
from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.metrics.custom_metrics import get_metrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = get_metrics()
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Track active connections
        self.metrics.update_active_connections("http", 1)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            self.metrics.record_http_request(
                method=method,
                path=path,
                status_code=response.status_code,
                duration=duration
            )
            
            # Add response headers with metrics
            response.headers["X-Request-Duration"] = str(duration)
            response.headers["X-Service-Version"] = "1.0.0"
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Record error metrics
            self.metrics.record_error(
                error_type=type(e).__name__,
                component="http_middleware",
                document_type=None
            )
            
            # Record failed request metrics
            self.metrics.record_http_request(
                method=method,
                path=path,
                status_code=500,
                duration=duration
            )
            
            # Re-raise the exception
            raise
            
        finally:
            # Update active connections
            self.metrics.update_active_connections("http", -1)
    
    def record_http_request(
        self, 
        method: str, 
        path: str, 
        status_code: int, 
        duration: float
    ):
        """Record HTTP request metrics."""
        # This method is called from the middleware to record HTTP metrics
        # The actual implementation will be in the metrics class
        pass


class QueueMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track queue metrics."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = get_metrics()
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and update queue metrics."""
        # Update queue size before processing
        # This would need to be integrated with your actual queue implementation
        self.metrics.update_queue_size("document_processing", 0)  # Placeholder
        
        response = await call_next(request)
        
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and alerting."""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.metrics = get_metrics()
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and monitor performance."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Check for slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"took {duration:.2f}s"
                )
                self.metrics.record_error(
                    error_type="slow_request",
                    component="performance",
                    document_type=None
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {duration:.2f}s with error: {e}"
            )
            raise


def setup_metrics_middleware(app):
    """Set up all metrics middleware."""
    # Add basic metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    # Add queue metrics middleware
    app.add_middleware(QueueMetricsMiddleware)
    
    # Add performance monitoring middleware
    app.add_middleware(PerformanceMonitoringMiddleware)
    
    return app