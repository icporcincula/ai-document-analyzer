"""
Cleanup Tasks

This module contains Celery tasks for cleaning up expired data and maintaining
system performance.
"""

import logging
from celery import current_task
from app.services.task_result_service import TaskResultService
from app.monitoring.task_monitor import TaskMonitor

logger = logging.getLogger(__name__)

# Initialize services
task_result_service = TaskResultService()
task_monitor = TaskMonitor()


@current_task.task(bind=True)
def cleanup_expired_results(self, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up expired task results from Redis.
    
    Args:
        max_age_hours: Maximum age in hours for results to keep
        
    Returns:
        Cleanup summary
    """
    try:
        # Clean up task results
        cleaned_results = task_result_service.cleanup_expired_results(max_age_hours)
        
        # Clean up task monitor metrics
        task_monitor.cleanup_old_metrics(max_age_hours)
        
        logger.info(f"Cleanup completed: {cleaned_results} expired results removed")
        
        return {
            'status': 'success',
            'cleaned_results': cleaned_results,
            'max_age_hours': max_age_hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def cleanup_old_progress_data(self, max_age_hours: int = 1) -> Dict[str, Any]:
    """
    Clean up old task progress data.
    
    Args:
        max_age_hours: Maximum age in hours for progress data to keep
        
    Returns:
        Cleanup summary
    """
    try:
        # Clean up completed task progress data
        cleaned_progress = task_result_service.cleanup_completed_tasks(max_age_hours)
        
        logger.info(f"Progress cleanup completed: {cleaned_progress} records removed")
        
        return {
            'status': 'success',
            'cleaned_progress': cleaned_progress,
            'max_age_hours': max_age_hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in progress cleanup task: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def cleanup_webhook_data(self, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old webhook retry data.
    
    Args:
        max_age_hours: Maximum age in hours for webhook data to keep
        
    Returns:
        Cleanup summary
    """
    try:
        # Clean up old webhook data
        cleaned_webhooks = task_result_service.cleanup_old_webhooks(max_age_hours)
        
        logger.info(f"Webhook cleanup completed: {cleaned_webhooks} items removed")
        
        return {
            'status': 'success',
            'cleaned_webhooks': cleaned_webhooks,
            'max_age_hours': max_age_hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in webhook cleanup task: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def cleanup_health_monitoring_data(self, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old health monitoring data.
    
    Args:
        max_age_hours: Maximum age in hours for monitoring data to keep
        
    Returns:
        Cleanup summary
    """
    try:
        # Clean up old health monitoring history
        task_result_service.cleanup_old_history(max_age_hours)
        
        logger.info(f"Health monitoring cleanup completed")
        
        return {
            'status': 'success',
            'max_age_hours': max_age_hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in health monitoring cleanup task: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }