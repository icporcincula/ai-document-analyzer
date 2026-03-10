"""
Database models for result storage and management.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class AnalysisResult(Base):
    """Model for storing analysis results."""
    
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    status = Column(String, default="completed", nullable=False)
    
    # Analysis data
    extracted_fields = Column(JSON, nullable=False)
    pii_entities_found = Column(JSON, default=list)
    confidence = Column(Float, nullable=False)
    
    # Metadata
    processing_time_seconds = Column(Float, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Export tracking
    exported_at = Column(DateTime, nullable=True)
    export_format = Column(String, nullable=True)
    
    # GDPR compliance
    data_retention_until = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "task_id": self.task_id,
            "filename": self.filename,
            "document_type": self.document_type,
            "status": self.status,
            "extracted_fields": self.extracted_fields,
            "pii_entities_found": self.pii_entities_found,
            "confidence": self.confidence,
            "processing_time_seconds": self.processing_time_seconds,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "exported_at": self.exported_at.isoformat() if self.exported_at else None,
            "export_format": self.export_format,
            "data_retention_until": self.data_retention_until.isoformat() if self.data_retention_until else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "is_deleted": self.is_deleted
        }


class ExportHistory(Base):
    """Model for tracking export operations."""
    
    __tablename__ = "export_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, index=True, nullable=False)
    export_format = Column(String, nullable=False)
    export_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    exported_by = Column(String, nullable=True)  # User ID if available
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "export_format": self.export_format,
            "export_count": self.export_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "exported_by": self.exported_by
        }


class MetricsSnapshot(Base):
    """Model for storing periodic metrics snapshots."""
    
    __tablename__ = "metrics_snapshots"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # Document processing metrics
    total_documents = Column(Integer, default=0, nullable=False)
    successful_documents = Column(Integer, default=0, nullable=False)
    failed_documents = Column(Integer, default=0, nullable=False)
    avg_processing_time = Column(Float, default=0.0, nullable=False)
    
    # PII detection metrics
    total_pii_entities = Column(Integer, default=0, nullable=False)
    avg_pii_per_document = Column(Float, default=0.0, nullable=False)
    
    # System metrics
    active_connections = Column(Integer, default=0, nullable=False)
    queue_size = Column(Integer, default=0, nullable=False)
    
    # Export metrics
    total_exports = Column(Integer, default=0, nullable=False)
    csv_exports = Column(Integer, default=0, nullable=False)
    excel_exports = Column(Integer, default=0, nullable=False)
    json_exports = Column(Integer, default=0, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "total_documents": self.total_documents,
            "successful_documents": self.successful_documents,
            "failed_documents": self.failed_documents,
            "avg_processing_time": self.avg_processing_time,
            "total_pii_entities": self.total_pii_entities,
            "avg_pii_per_document": self.avg_pii_per_document,
            "active_connections": self.active_connections,
            "queue_size": self.queue_size,
            "total_exports": self.total_exports,
            "csv_exports": self.csv_exports,
            "excel_exports": self.excel_exports,
            "json_exports": self.json_exports
        }


class AuditLog(Base):
    """Model for audit logging."""
    
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    action = Column(String, nullable=False)  # e.g., "document_upload", "result_export", "result_delete"
    user_id = Column(String, nullable=True)
    task_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }