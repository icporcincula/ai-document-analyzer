"""
Enhanced Task Result Service with database integration.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.utils.config import get_settings
from app.models.schemas import DocumentAnalysisResponse
from app.database.models import AnalysisResult, ExportHistory, MetricsSnapshot, AuditLog
from app.database.session import get_db

logger = logging.getLogger(__name__)


class EnhancedTaskResultService:
    """Enhanced service for managing task results with database integration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.results_dir = self.settings.results_dir
        self.max_results = self.settings.max_results
        
        # Ensure results directory exists
        os.makedirs(self.results_dir, exist_ok=True)
    
    def store_result(self, task_id: str, result: DocumentAnalysisResponse) -> bool:
        """Store analysis result to database and file."""
        try:
            # Create result data
            result_data = {
                "task_id": task_id,
                "filename": result.filename,
                "document_type": result.document_type,
                "status": "completed",
                "extracted_fields": result.extracted_fields,
                "pii_entities_found": result.pii_entities_found,
                "confidence": result.confidence,
                "processing_time_seconds": result.processing_time_seconds,
                "file_size": result.file_size,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": result.metadata
            }
            
            # Store to database
            try:
                db = next(get_db())
                db_result = AnalysisResult(
                    task_id=task_id,
                    filename=result.filename,
                    document_type=result.document_type,
                    status="completed",
                    extracted_fields=result.extracted_fields,
                    pii_entities_found=result.pii_entities_found,
                    confidence=result.confidence,
                    processing_time_seconds=result.processing_time_seconds,
                    file_size=result.file_size,
                    data_retention_until=datetime.utcnow() + timedelta(days=30)  # 30 days retention
                )
                db.add(db_result)
                db.commit()
                db.refresh(db_result)
                db.close()
                
                logger.info(f"Stored result to database for task {task_id}")
            except Exception as db_error:
                logger.warning(f"Database storage failed for task {task_id}: {str(db_error)}")
            
            # Store to file as backup
            result_file = os.path.join(self.results_dir, f"{task_id}.json")
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            # Clean up old results if needed
            self._cleanup_old_results()
            
            # Log the action
            self._log_audit_action("document_upload", task_id=task_id, details=f"Document processed: {result.filename}")
            
            logger.info(f"Stored result for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing result for task {task_id}: {str(e)}")
            return False
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis result by task ID."""
        try:
            # Try database first
            try:
                db = next(get_db())
                db_result = db.query(AnalysisResult).filter(
                    AnalysisResult.task_id == task_id,
                    AnalysisResult.is_deleted == False
                ).first()
                db.close()
                
                if db_result:
                    return db_result.to_dict()
            except Exception as db_error:
                logger.warning(f"Database retrieval failed for task {task_id}: {str(db_error)}")
            
            # Fallback to file storage
            result_file = os.path.join(self.results_dir, f"{task_id}.json")
            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    result_data = json.load(f)
                return result_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving result for task {task_id}: {str(e)}")
            return None
    
    def get_task_history(self, page: int = 1, page_size: int = 10, search: str = "") -> Dict[str, Any]:
        """Get paginated task history."""
        try:
            # Try database first
            try:
                db = next(get_db())
                query = db.query(AnalysisResult).filter(AnalysisResult.is_deleted == False)
                
                # Apply search filter
                if search:
                    query = query.filter(
                        or_(
                            AnalysisResult.task_id.contains(search),
                            AnalysisResult.filename.contains(search),
                            AnalysisResult.document_type.contains(search)
                        )
                    )
                
                # Get total count
                total = query.count()
                
                # Apply pagination
                results = query.order_by(desc(AnalysisResult.created_at)).offset((page - 1) * page_size).limit(page_size).all()
                db.close()
                
                # Convert to dict format
                items = [result.to_dict() for result in results]
                
                return {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
                
            except Exception as db_error:
                logger.warning(f"Database history query failed: {str(db_error)}")
            
            # Fallback to file storage
            result_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
            
            # Filter by search term if provided
            if search:
                result_files = [
                    f for f in result_files 
                    if search.lower() in f.lower()
                ]
            
            # Sort by creation time (newest first)
            result_files.sort(key=lambda f: os.path.getctime(os.path.join(self.results_dir, f)), reverse=True)
            
            # Calculate pagination
            total = len(result_files)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_files = result_files[start_idx:end_idx]
            
            # Load results
            items = []
            for filename in paginated_files:
                try:
                    with open(os.path.join(self.results_dir, filename), 'r') as f:
                        result_data = json.load(f)
                        items.append({
                            "task_id": result_data.get("task_id", ""),
                            "filename": result_data.get("filename", ""),
                            "document_type": result_data.get("document_type", ""),
                            "status": result_data.get("status", ""),
                            "created_at": result_data.get("created_at", ""),
                            "processing_time": result_data.get("processing_time_seconds", 0),
                            "file_size": result_data.get("file_size", 0),
                            "pii_count": len(result_data.get("pii_entities_found", []))
                        })
                except Exception as e:
                    logger.warning(f"Error loading result file {filename}: {str(e)}")
                    continue
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Error getting task history: {str(e)}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    def delete_task_result(self, task_id: str) -> bool:
        """Delete a specific task result (soft delete)."""
        try:
            # Try database first
            try:
                db = next(get_db())
                db_result = db.query(AnalysisResult).filter(
                    AnalysisResult.task_id == task_id,
                    AnalysisResult.is_deleted == False
                ).first()
                
                if db_result:
                    db_result.is_deleted = True
                    db_result.deleted_at = datetime.utcnow()
                    db.commit()
                    db.close()
                    
                    # Log the action
                    self._log_audit_action("result_delete", task_id=task_id, details="Result soft deleted")
                    
                    logger.info(f"Soft deleted result for task {task_id} in database")
                    return True
            except Exception as db_error:
                logger.warning(f"Database deletion failed for task {task_id}: {str(db_error)}")
            
            # Fallback to file deletion
            result_file = os.path.join(self.results_dir, f"{task_id}.json")
            if os.path.exists(result_file):
                os.remove(result_file)
                
                # Log the action
                self._log_audit_action("result_delete", task_id=task_id, details="Result file deleted")
                
                logger.info(f"Deleted result file for task {task_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting result for task {task_id}: {str(e)}")
            return False
    
    def export_result(self, task_id: str, export_format: str, exported_by: Optional[str] = None) -> bool:
        """Track export operation."""
        try:
            # Record export in database
            db = next(get_db())
            export_record = ExportHistory(
                task_id=task_id,
                export_format=export_format,
                exported_by=exported_by
            )
            db.add(export_record)
            
            # Update analysis result export tracking
            db_result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
            if db_result:
                db_result.exported_at = datetime.utcnow()
                db_result.export_format = export_format
            
            db.commit()
            db.close()
            
            # Log the action
            self._log_audit_action(
                "result_export", 
                task_id=task_id, 
                details=f"Exported as {export_format}",
                exported_by=exported_by
            )
            
            logger.info(f"Tracked export for task {task_id} as {export_format}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking export for task {task_id}: {str(e)}")
            return False
    
    def get_export_stats(self) -> Dict[str, Any]:
        """Get export statistics."""
        try:
            db = next(get_db())
            
            # Get export counts by format
            export_stats = db.query(
                ExportHistory.export_format,
                func.count(ExportHistory.id).label('count')
            ).group_by(ExportHistory.export_format).all()
            
            db.close()
            
            return {
                "total_exports": sum(count for _, count in export_stats),
                "by_format": {format: count for format, count in export_stats}
            }
            
        except Exception as e:
            logger.error(f"Error getting export stats: {str(e)}")
            return {"total_exports": 0, "by_format": {}}
    
    def cleanup_old_results(self, max_age_hours: int = 24) -> int:
        """Clean up old result files and database entries."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            # Clean up database entries
            try:
                db = next(get_db())
                old_results = db.query(AnalysisResult).filter(
                    AnalysisResult.created_at < cutoff_time,
                    AnalysisResult.is_deleted == False
                ).all()
                
                for result in old_results:
                    result.is_deleted = True
                    result.deleted_at = datetime.utcnow()
                
                db.commit()
                db.close()
                
                deleted_count += len(old_results)
                logger.info(f"Soft deleted {len(old_results)} old database results")
                
            except Exception as db_error:
                logger.warning(f"Database cleanup failed: {str(db_error)}")
            
            # Clean up file storage
            for filename in os.listdir(self.results_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.results_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old result files and database entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0
    
    def _cleanup_old_results(self):
        """Internal cleanup method."""
        try:
            result_files = [f for f in os.listdir(self.results_dir) if f.endswith('.json')]
            
            if len(result_files) > self.max_results:
                # Sort by creation time and remove oldest
                result_files.sort(key=lambda f: os.path.getctime(os.path.join(self.results_dir, f)))
                
                files_to_delete = result_files[:-self.max_results]
                for filename in files_to_delete:
                    os.remove(os.path.join(self.results_dir, filename))
                
                logger.info(f"Cleaned up {len(files_to_delete)} old result files")
                
        except Exception as e:
            logger.error(f"Error during internal cleanup: {str(e)}")
    
    def _log_audit_action(self, action: str, task_id: Optional[str] = None, details: Optional[str] = None, exported_by: Optional[str] = None):
        """Log audit action."""
        try:
            db = next(get_db())
            audit_log = AuditLog(
                action=action,
                task_id=task_id,
                details=details,
                user_id=exported_by
            )
            db.add(audit_log)
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"Failed to log audit action: {str(e)}")