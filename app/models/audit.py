# app/models/audit.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AuditLogEntry(BaseModel):
    """Audit log entry model for tracking API requests"""
    
    timestamp: datetime = Field(description="When the request was made")
    request_id: str = Field(description="Unique identifier for the request")
    client_ip: str = Field(description="IP address of the client")
    method: str = Field(description="HTTP method used")
    path: str = Field(description="Request path")
    user_agent: Optional[str] = Field(default=None, description="User agent string")
    api_key_used: Optional[str] = Field(default=None, description="API key used (masked)")
    status_code: int = Field(description="HTTP response status code")
    processing_time: float = Field(description="Request processing time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if request failed")
    pii_processed: bool = Field(default=False, description="Whether PII was processed in the request")
    document_type: Optional[str] = Field(default=None, description="Type of document processed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AuditLogConfig(BaseModel):
    """Configuration for audit logging"""
    
    enabled: bool = Field(default=True, description="Whether audit logging is enabled")
    log_file: str = Field(default="logs/audit.log", description="Path to audit log file")
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files to keep")
    log_format: str = Field(
        default='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        description="Log format string"
    )