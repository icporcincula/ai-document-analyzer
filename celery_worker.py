"""
Celery Worker Configuration

This module configures and starts Celery workers for the document processing system.
It includes optimized worker settings for production use.
"""

import os
import logging
from celery import Celery
from app.config.celery_config import get_celery_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'ai_document_analyzer',
    broker=get_celery_config()['broker_url'],
    backend=get_celery_config()['result_backend']
)

# Configure Celery app with production settings
celery_config = get_celery_config()
celery_app.conf.update(celery_config)

# Worker-specific configuration
celery_app.conf.update(
    # Worker settings
    worker_prefetch_multiplier=1,  # Don't prefetch too many tasks
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
    worker_max_memory_per_child=300000,  # 300MB memory limit per worker child
    
    # Task settings
    task_acks_late=True,  # Acknowledge tasks after completion, not after receipt
    task_reject_on_worker_lost=True,  # Re-queue tasks if worker is lost
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Beat settings (for periodic tasks)
    beat_schedule={
        'cleanup-expired-results': {
            'task': 'app.tasks.cleanup_tasks.cleanup_expired_results',
            'schedule': 3600.0,  # Every hour
        },
        'monitor-worker-health': {
            'task': 'app.tasks.monitoring_tasks.check_worker_health',
            'schedule': 300.0,   # Every 5 minutes
        },
        'cleanup-old-metrics': {
            'task': 'app.tasks.monitoring_tasks.cleanup_old_metrics',
            'schedule': 7200.0,  # Every 2 hours
        }
    }
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    'app.tasks.document_tasks',
    'app.tasks.cleanup_tasks',
    'app.tasks.monitoring_tasks',
    'app.tasks.webhook_tasks'
])

if __name__ == '__main__':
    # Start worker with optimized settings
    celery_app.start()