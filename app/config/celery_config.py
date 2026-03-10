"""
Celery Configuration Module

This module contains the configuration settings for Celery task queue
including broker settings, result backend, serialization, and worker settings.
"""

import os
from typing import Dict, Any

# Celery Broker Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Task Configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_PROTOCOL = 2

# Worker Configuration
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100
CELERY_WORKER_MAX_MEMORY_PER_CHILD = 300000  # 300MB

# Task Timeouts
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600      # 10 minutes

# Task Routing
CELERY_TASK_ROUTES = {
    'app.tasks.document_tasks.process_document': {
        'queue': 'document_processing',
        'routing_key': 'document.process'
    },
    'app.tasks.document_tasks.process_batch': {
        'queue': 'batch_processing', 
        'routing_key': 'batch.process'
    }
}

# Result Expiration
CELERY_TASK_RESULT_EXPIRES = 3600  # 1 hour

# Beat Schedule (for periodic tasks)
CELERYBEAT_SCHEDULE = {
    'cleanup-expired-results': {
        'task': 'app.tasks.cleanup_tasks.cleanup_expired_results',
        'schedule': 3600.0,  # Every hour
    },
    'monitor-worker-health': {
        'task': 'app.tasks.monitoring_tasks.check_worker_health',
        'schedule': 300.0,   # Every 5 minutes
    }
}

# Flower Configuration (for monitoring)
FLOWER_URL = os.getenv('FLOWER_URL', 'http://localhost:5555')
FLOWER_BASIC_AUTH = os.getenv('FLOWER_BASIC_AUTH', 'admin:admin')

def get_celery_config() -> Dict[str, Any]:
    """Get Celery configuration as a dictionary."""
    return {
        'broker_url': CELERY_BROKER_URL,
        'result_backend': CELERY_RESULT_BACKEND,
        'task_serializer': CELERY_TASK_SERIALIZER,
        'result_serializer': CELERY_RESULT_SERIALIZER,
        'accept_content': CELERY_ACCEPT_CONTENT,
        'task_protocol': CELERY_TASK_PROTOCOL,
        'worker_prefetch_multiplier': CELERY_WORKER_PREFETCH_MULTIPLIER,
        'worker_max_tasks_per_child': CELERY_WORKER_MAX_TASKS_PER_CHILD,
        'worker_max_memory_per_child': CELERY_WORKER_MAX_MEMORY_PER_CHILD,
        'task_soft_time_limit': CELERY_TASK_SOFT_TIME_LIMIT,
        'task_time_limit': CELERY_TASK_TIME_LIMIT,
        'task_routes': CELERY_TASK_ROUTES,
        'task_result_expires': CELERY_TASK_RESULT_EXPIRES,
        'beat_schedule': CELERYBEAT_SCHEDULE,
    }

def is_celery_configured() -> bool:
    """Check if Celery is properly configured."""
    return bool(CELERY_BROKER_URL and CELERY_RESULT_BACKEND)