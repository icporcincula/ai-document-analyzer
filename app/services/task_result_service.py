"""
Task Result Service

This service handles storage and retrieval of asynchronous task results
including processing results, errors, and batch processing summaries.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from redis import Redis
from app.models.schemas import ProcessingResult, ProcessingError
from app.utils.config import get_config

logger = logging.getLogger(__name__)


class TaskResultService:
    """Service for managing task results in Redis."""
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.result_ttl = 3600  # 1 hour default TTL
        self.error_ttl = 7200   # 2 hours for errors
        
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
    
    def store_result(self, task_id: str, result: ProcessingResult, 
                    file_path: str, file_type: str, user_id: Optional[str] = None) -> bool:
        """
        Store a successful processing result.
        
        Args:
            task_id: Celery task ID
            result: Processing result object
            file_path: Original file path
            file_type: Type of processed file
            user_id: Optional user identifier
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Create result data structure
            result_data = {
                'task_id': task_id,
                'result_id': result.id,
                'status': 'completed',
                'file_path': file_path,
                'file_type': file_type,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'result_data': {
                    'text': result.text,
                    'pii_entities': result.pii_entities,
                    'statistics': result.statistics,
                    'processing_time': result.processing_time,
                    'language': result.language
                }
            }
            
            # Store in Redis with TTL
            key = f"task_result:{task_id}"
            self.redis_client.setex(
                key, 
                self.result_ttl, 
                json.dumps(result_data, default=str)
            )
            
            # Also store in a user-specific index if user_id provided
            if user_id:
                user_key = f"user_results:{user_id}"
                self.redis_client.zadd(user_key, {task_id: time.time()})
                self.redis_client.expire(user_key, self.result_ttl)
            
            logger.info(f"Stored result for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing result for task {task_id}: {str(e)}")
            return False
    
    def store_error(self, task_id: str, error: ProcessingError,
                   file_path: str, file_type: str, user_id: Optional[str] = None) -> bool:
        """
        Store a processing error.
        
        Args:
            task_id: Celery task ID
            error: Processing error object
            file_path: Original file path
            file_type: Type of processed file
            user_id: Optional user identifier
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Create error data structure
            error_data = {
                'task_id': task_id,
                'status': 'error',
                'file_path': file_path,
                'file_type': file_type,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                'error_data': {
                    'error_type': error.error_type,
                    'error_message': error.error_message,
                    'traceback': error.traceback,
                    'file_path': error.file_path,
                    'file_type': error.file_type
                }
            }
            
            # Store in Redis with longer TTL for errors
            key = f"task_error:{task_id}"
            self.redis_client.setex(
                key,
                self.error_ttl,
                json.dumps(error_data, default=str)
            )
            
            # Also store in a user-specific index if user_id provided
            if user_id:
                user_key = f"user_errors:{user_id}"
                self.redis_client.zadd(user_key, {task_id: time.time()})
                self.redis_client.expire(user_key, self.error_ttl)
            
            logger.info(f"Stored error for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing error for task {task_id}: {str(e)}")
            return False
    
    def store_batch_result(self, task_id: str, batch_result: Dict[str, Any]) -> bool:
        """
        Store a batch processing result.
        
        Args:
            task_id: Celery task ID
            batch_result: Batch processing result dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Add timestamp
            batch_result['timestamp'] = datetime.utcnow().isoformat()
            
            # Store in Redis
            key = f"batch_result:{task_id}"
            self.redis_client.setex(
                key,
                self.result_ttl,
                json.dumps(batch_result, default=str)
            )
            
            # Store individual file results
            for result in batch_result.get('results', []):
                if result.get('status') == 'success':
                    file_task_id = result.get('result_id')
                    if file_task_id:
                        # Create a reference to the batch result
                        file_key = f"task_result:{file_task_id}"
                        existing_data = self.redis_client.get(file_key)
                        if existing_data:
                            data = json.loads(existing_data)
                            data['batch_id'] = task_id
                            self.redis_client.setex(file_key, self.result_ttl, json.dumps(data, default=str))
            
            logger.info(f"Stored batch result for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing batch result for task {task_id}: {str(e)}")
            return False
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task result.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Result data if found, None otherwise
        """
        try:
            key = f"task_result:{task_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            else:
                # Check if it's an error
                error_key = f"task_error:{task_id}"
                error_data = self.redis_client.get(error_key)
                if error_data:
                    return json.loads(error_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving result for task {task_id}: {str(e)}")
            return None
    
    def get_batch_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a batch processing result.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Batch result data if found, None otherwise
        """
        try:
            key = f"batch_result:{task_id}"
            data = self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving batch result for task {task_id}: {str(e)}")
            return None
    
    def get_user_results(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all results for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of results to return
            
        Returns:
            List of result data
        """
        try:
            user_key = f"user_results:{user_id}"
            task_ids = self.redis_client.zrevrange(user_key, 0, limit - 1)
            
            results = []
            for task_id in task_ids:
                result = self.get_result(task_id)
                if result:
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving user results for {user_id}: {str(e)}")
            return []
    
    def get_user_errors(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all errors for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of errors to return
            
        Returns:
            List of error data
        """
        try:
            user_key = f"user_errors:{user_id}"
            task_ids = self.redis_client.zrevrange(user_key, 0, limit - 1)
            
            errors = []
            for task_id in task_ids:
                result = self.get_result(task_id)
                if result and result.get('status') == 'error':
                    errors.append(result)
            
            return errors
            
        except Exception as e:
            logger.error(f"Error retrieving user errors for {user_id}: {str(e)}")
            return []
    
    def cleanup_expired_results(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired results from Redis.
        
        Args:
            max_age_hours: Maximum age in hours for results to keep
            
        Returns:
            Number of expired results cleaned up
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            # Clean up user result indices
            user_result_keys = self.redis_client.keys("user_results:*")
            cleaned_count = 0
            
            for user_key in user_result_keys:
                # Remove expired entries
                removed = self.redis_client.zremrangebyscore(user_key, 0, cutoff_timestamp)
                cleaned_count += removed
                
                # Remove empty keys
                if self.redis_client.zcard(user_key) == 0:
                    self.redis_client.delete(user_key)
            
            # Clean up user error indices
            user_error_keys = self.redis_client.keys("user_errors:*")
            for user_key in user_error_keys:
                removed = self.redis_client.zremrangebyscore(user_key, 0, cutoff_timestamp)
                cleaned_count += removed
                
                if self.redis_client.zcard(user_key) == 0:
                    self.redis_client.delete(user_key)
            
            logger.info(f"Cleaned up {cleaned_count} expired results")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired results: {str(e)}")
            return 0
    
    def get_result_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about stored results.
        
        Args:
            user_id: Optional user identifier to get user-specific stats
            
        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                'total_results': 0,
                'total_errors': 0,
                'success_rate': 0.0,
                'avg_processing_time': 0.0
            }
            
            if user_id:
                # User-specific stats
                user_results = self.get_user_results(user_id)
                user_errors = self.get_user_errors(user_id)
                
                stats['total_results'] = len(user_results)
                stats['total_errors'] = len(user_errors)
                
                if user_results:
                    total_time = sum(r.get('result_data', {}).get('processing_time', 0) for r in user_results)
                    stats['avg_processing_time'] = total_time / len(user_results)
                
                total_tasks = stats['total_results'] + stats['total_errors']
                if total_tasks > 0:
                    stats['success_rate'] = (stats['total_results'] / total_tasks) * 100
                    
            else:
                # System-wide stats (would need to scan all keys, which is expensive)
                # For now, return basic info
                result_keys = self.redis_client.keys("task_result:*")
                error_keys = self.redis_client.keys("task_error:*")
                
                stats['total_results'] = len(result_keys)
                stats['total_errors'] = len(error_keys)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting result stats: {str(e)}")
            return {}