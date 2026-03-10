"""
Monitoring Tasks

This module contains Celery tasks for system monitoring and health checks.
"""

import logging
from celery import current_task
from app.services.health_monitor import ServiceHealthMonitor
from app.monitoring.task_monitor import TaskMonitor

logger = logging.getLogger(__name__)

# Initialize services
health_monitor = ServiceHealthMonitor()
task_monitor = TaskMonitor()


@current_task.task(bind=True)
def check_worker_health(self) -> Dict[str, Any]:
    """
    Check worker health and system status.
    
    Returns:
        Health check summary
    """
    try:
        # Get overall system health
        overall_health = health_monitor.get_overall_health()
        
        # Get real-time task metrics
        real_time_metrics = task_monitor.get_real_time_metrics()
        
        # Get performance alerts
        alerts = task_monitor.get_performance_alerts()
        
        health_summary = {
            'overall_health': overall_health,
            'real_time_metrics': real_time_metrics,
            'alerts': alerts,
            'timestamp': None,  # Will be set by task result service
            'task_id': self.request.id
        }
        
        logger.info(f"Worker health check completed: {overall_health['overall_status']}")
        
        return {
            'status': 'success',
            'health_summary': health_summary,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in worker health check: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def cleanup_old_metrics(self, hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old monitoring metrics.
    
    Args:
        hours: Number of hours to keep metrics for
        
    Returns:
        Cleanup summary
    """
    try:
        # Clean up old task monitor metrics
        task_monitor.cleanup_old_metrics(hours)
        
        logger.info(f"Metrics cleanup completed: old metrics older than {hours} hours removed")
        
        return {
            'status': 'success',
            'hours_kept': hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in metrics cleanup: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
    """
    Generate performance report for the specified time period.
    
    Args:
        hours: Number of hours to analyze
        
    Returns:
        Performance report
    """
    try:
        # Get task performance report
        task_report = task_monitor.get_task_performance_report(hours)
        
        # Get health statistics
        health_stats = health_monitor.get_health_statistics(hours)
        
        # Get monitoring dashboard
        dashboard = health_monitor.get_monitoring_dashboard()
        
        performance_report = {
            'task_performance': task_report,
            'health_statistics': health_stats,
            'monitoring_dashboard': dashboard,
            'period_hours': hours,
            'timestamp': None,  # Will be set by task result service
            'task_id': self.request.id
        }
        
        logger.info(f"Performance report generated for {hours} hours")
        
        return {
            'status': 'success',
            'performance_report': performance_report,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def check_service_health(self, service_name: str) -> Dict[str, Any]:
    """
    Check health of a specific service.
    
    Args:
        service_name: Name of the service to check
        
    Returns:
        Service health status
    """
    try:
        health_status = health_monitor.get_service_health(service_name)
        
        logger.info(f"Service health check completed for {service_name}: {health_status.get('status')}")
        
        return {
            'status': 'success',
            'service_name': service_name,
            'health_status': health_status,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error checking service health for {service_name}: {str(e)}")
        return {
            'status': 'failed',
            'service_name': service_name,
            'error': str(e),
            'task_id': self.request.id
        }


@current_task.task(bind=True)
def cleanup_health_history(self, hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old health monitoring history.
    
    Args:
        hours: Number of hours to keep history for
        
    Returns:
        Cleanup summary
    """
    try:
        # Clean up old health history
        health_monitor.cleanup_old_history(hours)
        
        logger.info(f"Health history cleanup completed: old history older than {hours} hours removed")
        
        return {
            'status': 'success',
            'hours_kept': hours,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"Error in health history cleanup: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'task_id': self.request.id
        }