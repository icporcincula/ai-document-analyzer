"""
Task Monitoring Service

This service provides comprehensive monitoring for Celery tasks including
execution times, success/failure rates, and performance reporting.
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from app.services.task_result_service import TaskResultService
from app.services.task_progress_service import TaskProgressService
from app.utils.config import get_config

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Service for monitoring Celery task performance and metrics."""
    
    def __init__(self):
        self.config = get_config()
        self.task_result_service = TaskResultService()
        self.task_progress_service = TaskProgressService()
        
        # In-memory metrics storage (in production, use Redis or database)
        self.metrics_buffer = defaultdict(deque)
        self.max_buffer_size = 10000
        self.performance_thresholds = {
            'slow_task_threshold': 300,  # 5 minutes
            'very_slow_task_threshold': 600,  # 10 minutes
            'high_failure_rate_threshold': 0.1,  # 10%
            'low_success_rate_threshold': 0.8  # 80%
        }
    
    def record_task_start(self, task_id: str, task_name: str, 
                         queue_name: str, worker_name: Optional[str] = None):
        """
        Record task start for monitoring.
        
        Args:
            task_id: Celery task ID
            task_name: Name of the task
            queue_name: Queue the task is running on
            worker_name: Name of the worker (optional)
        """
        start_time = time.time()
        
        task_info = {
            'task_id': task_id,
            'task_name': task_name,
            'queue_name': queue_name,
            'worker_name': worker_name,
            'start_time': start_time,
            'status': 'running'
        }
        
        self._add_to_buffer('task_starts', task_info)
        logger.debug(f"Task started: {task_id} on queue {queue_name}")
    
    def record_task_completion(self, task_id: str, task_name: str,
                              success: bool, execution_time: float,
                              queue_name: str, worker_name: Optional[str] = None):
        """
        Record task completion for monitoring.
        
        Args:
            task_id: Celery task ID
            task_name: Name of the task
            success: Whether the task completed successfully
            execution_time: Time taken to complete the task in seconds
            queue_name: Queue the task ran on
            worker_name: Name of the worker (optional)
        """
        completion_time = time.time()
        
        task_result = {
            'task_id': task_id,
            'task_name': task_name,
            'queue_name': queue_name,
            'worker_name': worker_name,
            'success': success,
            'execution_time': execution_time,
            'completion_time': completion_time,
            'status': 'completed'
        }
        
        self._add_to_buffer('task_completions', task_result)
        
        # Record performance metrics
        self._record_performance_metrics(task_name, execution_time, success)
        
        # Check for performance issues
        self._check_performance_thresholds(task_name, execution_time, success)
        
        logger.debug(f"Task completed: {task_id} - Success: {success}, Time: {execution_time:.2f}s")
    
    def record_task_failure(self, task_id: str, task_name: str,
                           error_message: str, queue_name: str,
                           worker_name: Optional[str] = None):
        """
        Record task failure for monitoring.
        
        Args:
            task_id: Celery task ID
            task_name: Name of the task
            error_message: Error message from the failure
            queue_name: Queue the task was running on
            worker_name: Name of the worker (optional)
        """
        failure_time = time.time()
        
        task_failure = {
            'task_id': task_id,
            'task_name': task_name,
            'queue_name': queue_name,
            'worker_name': worker_name,
            'error_message': error_message,
            'failure_time': failure_time,
            'status': 'failed'
        }
        
        self._add_to_buffer('task_failures', task_failure)
        
        # Record failure metrics
        self._record_failure_metrics(task_name, error_message)
        
        logger.warning(f"Task failed: {task_id} - Error: {error_message}")
    
    def get_task_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get comprehensive task performance report.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance report
        """
        cutoff_time = time.time() - (hours * 3600)
        
        # Get task completions within time window
        completions = self._get_buffer_data('task_completions', cutoff_time)
        
        if not completions:
            return {
                'period_hours': hours,
                'total_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'min_execution_time': 0.0,
                'max_execution_time': 0.0,
                'tasks_by_queue': {},
                'tasks_by_worker': {},
                'performance_issues': []
            }
        
        # Calculate basic metrics
        total_tasks = len(completions)
        successful_tasks = sum(1 for task in completions if task['success'])
        failed_tasks = total_tasks - successful_tasks
        success_rate = (successful_tasks / total_tasks) * 100
        
        # Calculate execution time statistics
        execution_times = [task['execution_time'] for task in completions]
        avg_execution_time = sum(execution_times) / len(execution_times)
        min_execution_time = min(execution_times)
        max_execution_time = max(execution_times)
        
        # Group by queue
        tasks_by_queue = defaultdict(lambda: {'count': 0, 'successful': 0, 'failed': 0, 'avg_time': 0})
        for task in completions:
            queue = task['queue_name']
            tasks_by_queue[queue]['count'] += 1
            if task['success']:
                tasks_by_queue[queue]['successful'] += 1
            else:
                tasks_by_queue[queue]['failed'] += 1
        
        # Calculate queue averages
        for queue, stats in tasks_by_queue.items():
            queue_completions = [t for t in completions if t['queue_name'] == queue]
            stats['avg_time'] = sum(t['execution_time'] for t in queue_completions) / len(queue_completions)
            stats['success_rate'] = (stats['successful'] / stats['count']) * 100
        
        # Group by worker
        tasks_by_worker = defaultdict(lambda: {'count': 0, 'successful': 0, 'failed': 0, 'avg_time': 0})
        for task in completions:
            worker = task.get('worker_name', 'unknown')
            tasks_by_worker[worker]['count'] += 1
            if task['success']:
                tasks_by_worker[worker]['successful'] += 1
            else:
                tasks_by_worker[worker]['failed'] += 1
        
        # Calculate worker averages
        for worker, stats in tasks_by_worker.items():
            worker_completions = [t for t in completions if t.get('worker_name') == worker]
            stats['avg_time'] = sum(t['execution_time'] for t in worker_completions) / len(worker_completions)
            stats['success_rate'] = (stats['successful'] / stats['count']) * 100
        
        # Identify performance issues
        performance_issues = self._identify_performance_issues(completions)
        
        return {
            'period_hours': hours,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': round(success_rate, 2),
            'average_execution_time': round(avg_execution_time, 2),
            'min_execution_time': round(min_execution_time, 2),
            'max_execution_time': round(max_execution_time, 2),
            'tasks_by_queue': dict(tasks_by_queue),
            'tasks_by_worker': dict(tasks_by_worker),
            'performance_issues': performance_issues,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_queue_performance(self, queue_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics for a specific queue.
        
        Args:
            queue_name: Name of the queue
            hours: Number of hours to analyze
            
        Returns:
            Queue performance metrics
        """
        cutoff_time = time.time() - (hours * 3600)
        completions = self._get_buffer_data('task_completions', cutoff_time)
        
        queue_completions = [t for t in completions if t['queue_name'] == queue_name]
        
        if not queue_completions:
            return {
                'queue_name': queue_name,
                'period_hours': hours,
                'total_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'min_execution_time': 0.0,
                'max_execution_time': 0.0
            }
        
        total_tasks = len(queue_completions)
        successful_tasks = sum(1 for task in queue_completions if task['success'])
        failed_tasks = total_tasks - successful_tasks
        success_rate = (successful_tasks / total_tasks) * 100
        
        execution_times = [task['execution_time'] for task in queue_completions]
        avg_execution_time = sum(execution_times) / len(execution_times)
        min_execution_time = min(execution_times)
        max_execution_time = max(execution_times)
        
        return {
            'queue_name': queue_name,
            'period_hours': hours,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': round(success_rate, 2),
            'average_execution_time': round(avg_execution_time, 2),
            'min_execution_time': round(min_execution_time, 2),
            'max_execution_time': round(max_execution_time, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_worker_performance(self, worker_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance metrics for a specific worker.
        
        Args:
            worker_name: Name of the worker
            hours: Number of hours to analyze
            
        Returns:
            Worker performance metrics
        """
        cutoff_time = time.time() - (hours * 3600)
        completions = self._get_buffer_data('task_completions', cutoff_time)
        
        worker_completions = [t for t in completions if t.get('worker_name') == worker_name]
        
        if not worker_completions:
            return {
                'worker_name': worker_name,
                'period_hours': hours,
                'total_tasks': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'min_execution_time': 0.0,
                'max_execution_time': 0.0
            }
        
        total_tasks = len(worker_completions)
        successful_tasks = sum(1 for task in worker_completions if task['success'])
        failed_tasks = total_tasks - successful_tasks
        success_rate = (successful_tasks / total_tasks) * 100
        
        execution_times = [task['execution_time'] for task in worker_completions]
        avg_execution_time = sum(execution_times) / len(execution_times)
        min_execution_time = min(execution_times)
        max_execution_time = max(execution_times)
        
        return {
            'worker_name': worker_name,
            'period_hours': hours,
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': round(success_rate, 2),
            'average_execution_time': round(avg_execution_time, 2),
            'min_execution_time': round(min_execution_time, 2),
            'max_execution_time': round(max_execution_time, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time task metrics."""
        # Get recent data (last hour)
        cutoff_time = time.time() - 3600
        
        starts = self._get_buffer_data('task_starts', cutoff_time)
        completions = self._get_buffer_data('task_completions', cutoff_time)
        failures = self._get_buffer_data('task_failures', cutoff_time)
        
        # Calculate real-time metrics
        active_tasks = len(starts) - len(completions)
        
        # Calculate throughput (tasks per minute)
        if len(completions) > 0:
            first_completion = min(c['completion_time'] for c in completions)
            time_window = time.time() - first_completion
            throughput = len(completions) / (time_window / 60) if time_window > 0 else 0
        else:
            throughput = 0
        
        # Calculate current success rate
        if len(completions) > 0:
            success_rate = (sum(1 for c in completions if c['success']) / len(completions)) * 100
        else:
            success_rate = 0
        
        return {
            'active_tasks': active_tasks,
            'completed_tasks': len(completions),
            'failed_tasks': len(failures),
            'throughput_per_minute': round(throughput, 2),
            'success_rate': round(success_rate, 2),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get performance alerts based on thresholds."""
        alerts = []
        
        # Check overall success rate
        recent_completions = self._get_buffer_data('task_completions', time.time() - 3600)
        if recent_completions:
            success_rate = (sum(1 for c in recent_completions if c['success']) / len(recent_completions))
            
            if success_rate < self.performance_thresholds['low_success_rate_threshold']:
                alerts.append({
                    'type': 'low_success_rate',
                    'severity': 'high',
                    'message': f'Overall success rate is {success_rate * 100:.1f}%, below threshold',
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        # Check for slow tasks
        slow_tasks = [c for c in recent_completions 
                     if c['execution_time'] > self.performance_thresholds['slow_task_threshold']]
        
        if slow_tasks:
            alerts.append({
                'type': 'slow_tasks',
                'severity': 'medium',
                'message': f'{len(slow_tasks)} tasks took longer than {self.performance_thresholds["slow_task_threshold"]} seconds',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def cleanup_old_metrics(self, hours: int = 24):
        """Clean up old metrics data."""
        cutoff_time = time.time() - (hours * 3600)
        
        for buffer_name in ['task_starts', 'task_completions', 'task_failures']:
            self._cleanup_buffer(buffer_name, cutoff_time)
    
    def _add_to_buffer(self, buffer_name: str, data: Dict[str, Any]):
        """Add data to a metrics buffer."""
        buffer = self.metrics_buffer[buffer_name]
        buffer.append(data)
        
        # Limit buffer size
        if len(buffer) > self.max_buffer_size:
            buffer.popleft()
    
    def _get_buffer_data(self, buffer_name: str, cutoff_time: float) -> List[Dict[str, Any]]:
        """Get data from buffer after cutoff time."""
        buffer = self.metrics_buffer.get(buffer_name, deque())
        return [item for item in buffer if item.get('completion_time', item.get('start_time', item.get('failure_time', 0))) >= cutoff_time]
    
    def _cleanup_buffer(self, buffer_name: str, cutoff_time: float):
        """Clean up old data from buffer."""
        buffer = self.metrics_buffer.get(buffer_name, deque())
        self.metrics_buffer[buffer_name] = deque([
            item for item in buffer 
            if item.get('completion_time', item.get('start_time', item.get('failure_time', 0))) >= cutoff_time
        ])
    
    def _record_performance_metrics(self, task_name: str, execution_time: float, success: bool):
        """Record performance metrics for analysis."""
        # This could be extended to store more detailed metrics
        pass
    
    def _record_failure_metrics(self, task_name: str, error_message: str):
        """Record failure metrics for analysis."""
        # This could be extended to track failure patterns
        pass
    
    def _check_performance_thresholds(self, task_name: str, execution_time: float, success: bool):
        """Check if task performance exceeds thresholds."""
        if execution_time > self.performance_thresholds['very_slow_task_threshold']:
            logger.warning(f"Task {task_name} took {execution_time:.2f}s - very slow execution detected")
        
        elif execution_time > self.performance_thresholds['slow_task_threshold']:
            logger.warning(f"Task {task_name} took {execution_time:.2f}s - slow execution detected")
    
    def _identify_performance_issues(self, completions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance issues from completion data."""
        issues = []
        
        # Group by task type
        task_groups = defaultdict(list)
        for completion in completions:
            task_groups[completion['task_name']].append(completion)
        
        # Analyze each task type
        for task_name, task_completions in task_groups.items():
            if len(task_completions) < 10:  # Skip tasks with too few samples
                continue
            
            # Check success rate
            success_rate = sum(1 for t in task_completions if t['success']) / len(task_completions)
            if success_rate < self.performance_thresholds['low_success_rate_threshold']:
                issues.append({
                    'type': 'low_success_rate',
                    'task_name': task_name,
                    'success_rate': success_rate * 100,
                    'message': f'Task {task_name} has success rate of {success_rate * 100:.1f}%'
                })
            
            # Check execution time
            execution_times = [t['execution_time'] for t in task_completions if t['success']]
            if execution_times:
                avg_time = sum(execution_times) / len(execution_times)
                if avg_time > self.performance_thresholds['slow_task_threshold']:
                    issues.append({
                        'type': 'high_execution_time',
                        'task_name': task_name,
                        'avg_execution_time': avg_time,
                        'message': f'Task {task_name} has average execution time of {avg_time:.2f}s'
                    })
        
        return issues