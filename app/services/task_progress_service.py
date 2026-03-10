"""
Task Progress Service

This service handles real-time progress tracking for asynchronous tasks
including stage updates, progress percentages, and task completion status.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from redis import Redis
from app.utils.config import get_config

logger = logging.getLogger(__name__)


class TaskProgressService:
    """Service for managing task progress tracking in Redis."""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.progress_ttl = 7200  # 2 hours TTL for progress data
        
    def _get_redis_client(self) -> Redis:
        """Get Redis client connection."""
        config = get_config()
        redis_url = config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        
        # Parse Redis URL
        if redis_url.startswith('redis://'):
            # Extract host and port from URL
            parts = redis_url.replace('redis://', '').split(':')
            host = parts[0]
            port = int(parts[1].split('/')[0]) if len(parts) > 1 else 6379
            
            return Redis(host=host, port=port, decode_responses=True)
        else:
            # Default connection
            return Redis(host='localhost', port=6379, decode_responses=True)
    
    def update_progress(self, task_id: str, stage: str, message: str, 
                       progress: Optional[float] = None, completed: bool = False, 
                       error: bool = False) -> bool:
        """
        Update task progress information.
        
        Args:
            task_id: Celery task ID
            stage: Current processing stage
            message: Human-readable progress message
            progress: Optional progress percentage (0-100)
            completed: Whether the task is completed
            error: Whether the task encountered an error
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Create progress data structure
            progress_data = {
                'task_id': task_id,
                'stage': stage,
                'message': message,
                'progress': progress,
                'completed': completed,
                'error': error,
                'timestamp': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().timestamp()
            }
            
            # Store in Redis with TTL
            key = f"task_progress:{task_id}"
            self.redis_client.setex(
                key,
                self.progress_ttl,
                json.dumps(progress_data, default=str)
            )
            
            # Also store in a progress index for active tasks
            if not completed:
                active_key = "active_tasks"
                self.redis_client.zadd(active_key, {task_id: time.time()})
                self.redis_client.expire(active_key, self.progress_ttl)
            
            logger.debug(f"Updated progress for task {task_id}: {stage} - {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating progress for task {task_id}: {str(e)}")
            return False
    
    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve current progress for a task.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Progress data if found, None otherwise
        """
        try:
            key = f"task_progress:{task_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving progress for task {task_id}: {str(e)}")
            return None
    
    def get_active_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all active (in-progress) tasks.
        
        Args:
            limit: Maximum number of active tasks to return
            
        Returns:
            List of active task progress data
        """
        try:
            active_key = "active_tasks"
            task_ids = self.redis_client.zrevrange(active_key, 0, limit - 1)
            
            active_tasks = []
            for task_id in task_ids:
                progress = self.get_progress(task_id)
                if progress:
                    active_tasks.append(progress)
            
            return active_tasks
            
        except Exception as e:
            logger.error(f"Error retrieving active tasks: {str(e)}")
            return []
    
    def get_task_history(self, task_id: str, include_completed: bool = True) -> List[Dict[str, Any]]:
        """
        Get complete progress history for a task.
        
        Args:
            task_id: Celery task ID
            include_completed: Whether to include completed tasks
            
        Returns:
            List of progress updates in chronological order
        """
        try:
            # For now, we only store the latest progress
            # In a more sophisticated implementation, we could store a history
            progress = self.get_progress(task_id)
            if progress:
                return [progress]
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving task history for {task_id}: {str(e)}")
            return []
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Mark a task as cancelled.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            return self.update_progress(
                task_id=task_id,
                stage='cancelled',
                message='Task was cancelled by user',
                completed=True,
                error=True
            )
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 1) -> int:
        """
        Clean up completed task progress data.
        
        Args:
            max_age_hours: Maximum age in hours for completed task data to keep
            
        Returns:
            Number of completed tasks cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Get all active task keys
            active_key = "active_tasks"
            task_ids = self.redis_client.zrange(active_key, 0, -1)
            
            cleaned_count = 0
            for task_id in task_ids:
                progress = self.get_progress(task_id)
                if progress and progress.get('completed'):
                    # Check if it's older than the cutoff
                    updated_at = progress.get('updated_at', 0)
                    if updated_at < cutoff_timestamp:
                        # Remove from active tasks and progress data
                        self.redis_client.zrem(active_key, task_id)
                        self.redis_client.delete(f"task_progress:{task_id}")
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} completed task progress records")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up completed task progress: {str(e)}")
            return 0
    
    def get_progress_stats(self) -> Dict[str, Any]:
        """
        Get statistics about task progress.
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                'active_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0,
                'cancelled_tasks': 0,
                'avg_processing_time': 0.0
            }
            
            # Get active tasks
            active_key = "active_tasks"
            active_tasks = self.redis_client.zcard(active_key)
            stats['active_tasks'] = active_tasks
            
            # For completed/failed stats, we would need to scan progress keys
            # This is a simplified version
            progress_keys = self.redis_client.keys("task_progress:*")
            
            completed_count = 0
            failed_count = 0
            cancelled_count = 0
            total_time = 0
            time_count = 0
            
            for key in progress_keys:
                data = self.redis_client.get(key)
                if data:
                    progress = json.loads(data)
                    if progress.get('completed'):
                        if progress.get('error'):
                            if progress.get('stage') == 'cancelled':
                                cancelled_count += 1
                            else:
                                failed_count += 1
                        else:
                            completed_count += 1
                        
                        # Calculate processing time if available
                        processing_time = progress.get('processing_time')
                        if processing_time:
                            total_time += processing_time
                            time_count += 1
            
            stats['completed_tasks'] = completed_count
            stats['failed_tasks'] = failed_count
            stats['cancelled_tasks'] = cancelled_count
            
            if time_count > 0:
                stats['avg_processing_time'] = total_time / time_count
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting progress stats: {str(e)}")
            return {}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status information for a task.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Comprehensive task status
        """
        try:
            progress = self.get_progress(task_id)
            if not progress:
                return {
                    'task_id': task_id,
                    'status': 'unknown',
                    'message': 'Task not found or expired'
                }
            
            status = {
                'task_id': task_id,
                'stage': progress.get('stage'),
                'message': progress.get('message'),
                'progress': progress.get('progress'),
                'completed': progress.get('completed', False),
                'error': progress.get('error', False),
                'timestamp': progress.get('timestamp'),
                'updated_at': progress.get('updated_at')
            }
            
            # Determine overall status
            if progress.get('completed'):
                if progress.get('error'):
                    if progress.get('stage') == 'cancelled':
                        status['status'] = 'cancelled'
                    else:
                        status['status'] = 'failed'
                else:
                    status['status'] = 'completed'
            else:
                status['status'] = 'in_progress'
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'error',
                'message': f'Error retrieving status: {str(e)}'
            }