"""
Celery Tasks Module

This module initializes the Celery app and defines the task modules
for asynchronous document processing.
"""

from celery import Celery
from app.config.celery_config import get_celery_config

# Initialize Celery app
celery_app = Celery(
    'ai_document_analyzer',
    broker=get_celery_config()['broker_url'],
    backend=get_celery_config()['result_backend']
)

# Configure Celery app
celery_app.conf.update(get_celery_config())

# Define task modules
celery_app.autodiscover_tasks([
    'app.tasks.document_tasks',
    'app.tasks.cleanup_tasks', 
    'app.tasks.monitoring_tasks',
    'app.tasks.webhook_tasks'
])

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery functionality."""
    print(f'Request: {self.request!r}')
    return 'Celery is working correctly'

if __name__ == '__main__':
    celery_app.start()