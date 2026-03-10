# app/middleware/audit.py
import logging
import time
import uuid
from datetime import datetime
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import os

from app.models.audit import AuditLogEntry
from app.utils.config import get_settings

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive audit logging"""
    
    def __init__(self, app, log_file: str = None):
        super().__init__(app)
        self.settings = get_settings()
        
        # Setup audit logger
        self.audit_logger = logging.getLogger("audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file or self.settings.audit_log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Setup file handler with rotation
        if not self.audit_logger.handlers:
            from logging.handlers import RotatingFileHandler
            
            handler = RotatingFileHandler(
                filename=log_file or self.settings.audit_log_file,
                maxBytes=self.settings.audit_log_max_file_size,
                backupCount=self.settings.audit_log_backup_count,
                encoding='utf-8'
            )
            
            formatter = logging.Formatter(
                '%(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
            self.audit_logger.propagate = False

    async def dispatch(self, request: Request, call_next):
        """Process request and log audit information"""
        if not self.settings.audit_log_enabled:
            return await call_next(request)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Record start time
        start_time = time.time()
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Get API key (masked)
        api_key = self._get_masked_api_key(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Determine if PII was processed
        pii_processed = self._check_pii_processed(request, response)
        
        # Get document type if applicable
        document_type = self._get_document_type(request)
        
        # Create audit log entry
        audit_entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            request_id=request_id,
            client_ip=client_ip,
            method=request.method,
            path=request.url.path,
            user_agent=user_agent,
            api_key_used=api_key,
            status_code=response.status_code,
            processing_time=processing_time,
            pii_processed=pii_processed,
            document_type=document_type
        )
        
        # Log the audit entry
        self._log_audit_entry(audit_entry)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct connection
        if request.client:
            return request.client.host
        
        return "Unknown"
    
    def _get_masked_api_key(self, request: Request) -> Optional[str]:
        """Extract and mask API key from request headers"""
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            api_key = authorization[7:]  # Remove "Bearer " prefix
            if len(api_key) > 8:
                return f"{api_key[:4]}...{api_key[-4:]}"
            return f"{api_key[:2]}..."
        return None
    
    def _check_pii_processed(self, request: Request, response: Response) -> bool:
        """Check if PII was processed in this request"""
        # This is a simple heuristic - in a real implementation,
        # you might want to track this more explicitly
        return request.url.path == "/api/v1/analyze"
    
    def _get_document_type(self, request: Request) -> Optional[str]:
        """Extract document type from request if available"""
        # For analyze endpoint, we could extract this from query params
        # or from the response, but for now we'll leave it as None
        # This would need to be enhanced based on your specific needs
        return None
    
    def _log_audit_entry(self, entry: AuditLogEntry):
        """Log the audit entry"""
        log_message = (
            f"REQUEST_ID={entry.request_id} "
            f"IP={entry.client_ip} "
            f"METHOD={entry.method} "
            f"PATH={entry.path} "
            f"STATUS={entry.status_code} "
            f"TIME={entry.processing_time:.3f}s "
            f"PII_PROCESSED={entry.pii_processed} "
            f"API_KEY={entry.api_key_used or 'None'} "
            f"USER_AGENT={entry.user_agent}"
        )
        
        self.audit_logger.info(log_message)