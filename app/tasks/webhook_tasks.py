"""
Webhook Tasks

This module contains Celery tasks for sending webhook notifications.
"""

import logging
from celery import current_task
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)

# Initialize webhook service
webhook_service = WebhookService()


@current_task.task(bind=True)
def send_task_completion_webhook(self, task_id: str, webhook_url: str, 
                                user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send webhook notification for task completion.
    
    Args:
        task_id: The task ID that completed
        webhook_url: The webhook URL to send notification to
        user_id: Optional user identifier
        
    Returns:
        Webhook result
    """
    try:
        result = webhook_service.send_completion_webhook(task_id, webhook_url, user_id)
        
        logger.info(f"Webhook sent for task {task_id}: {result['status']}")
        
        return {
            'status': result['status'],
            'task_id': task_id,
            'webhook_url': webhook_url,
            'user_id': user_id,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error sending webhook for task {task_id}: {str(e)}")
        return {
            'status': 'failed',
            'task_id': task_id,
            'webhook_url': webhook_url,
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def send_batch_completion_webhook(self, batch_id: str, webhook_url: str,
                                 user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send webhook notification for batch completion.
    
    Args:
        batch_id: The batch task ID that completed
        webhook_url: The webhook URL to send notification to
        user_id: Optional user identifier
        
    Returns:
        Webhook result
    """
    try:
        result = webhook_service.send_batch_completion_webhook(batch_id, webhook_url, user_id)
        
        logger.info(f"Batch webhook sent for batch {batch_id}: {result['status']}")
        
        return {
            'status': result['status'],
            'batch_id': batch_id,
            'webhook_url': webhook_url,
            'user_id': user_id,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error sending batch webhook for batch {batch_id}: {str(e)}")
        return {
            'status': 'failed',
            'batch_id': batch_id,
            'webhook_url': webhook_url,
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def validate_webhook_url_task(self, webhook_url: str) -> Dict[str, Any]:
    """
    Validate a webhook URL.
    
    Args:
        webhook_url: The webhook URL to validate
        
    Returns:
        Validation result
    """
    try:
        from app.config.webhook_config import validate_webhook_url
        
        validation_result = validate_webhook_url(webhook_url)
        
        logger.info(f"Webhook URL validation for {webhook_url}: {validation_result['valid']}")
        
        return {
            'status': 'success',
            'webhook_url': webhook_url,
            'validation_result': validation_result,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error validating webhook URL {webhook_url}: {str(e)}")
        return {
            'status': 'failed',
            'webhook_url': webhook_url,
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def cleanup_webhook_stats(self, hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old webhook statistics.
    
    Args:
        hours: Number of hours to keep stats for
        
    Returns:
        Cleanup summary
    """
    try:
        cleaned_count = webhook_service.cleanup_old_webhooks(hours)
        
        logger.info(f"Webhook stats cleanup completed: {cleaned_count} items removed")
        
        return {
            'status': 'success',
            'cleaned_count': cleaned_count,
            'hours_kept': hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in webhook stats cleanup: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }