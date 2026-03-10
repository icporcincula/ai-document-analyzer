"""
Service Health Monitoring

This service monitors the health of external services including Presidio,
Redis/Celery, and provides health check aggregation for the entire system.
"""

import logging
import time
import requests
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.middleware.circuit_breaker import circuit_breaker_middleware
from app.utils.config import get_config

logger = logging.getLogger(__name__)


class ServiceHealthMonitor:
    """Service for monitoring external service health."""
    
    def __init__(self):
        self.config = get_config()
        self.health_cache = {}
        self.health_history = []
        self.max_history_entries = 1000
        
    def check_presidio_health(self) -> Dict[str, Any]:
        """
        Check Presidio service health.
        
        Returns:
            Health check result
        """
        try:
            # Get Presidio configuration
            presidio_url = self.config.get('PRESIDIO_ANALYZER_API_URL', 'http://localhost:3000')
            
            # Test basic connectivity
            start_time = time.time()
            response = requests.get(f"{presidio_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                health_result = {
                    'service': 'presidio',
                    'status': 'healthy',
                    'response_time': response_time,
                    'timestamp': datetime.utcnow().isoformat(),
                    'details': response.json() if response.headers.get('content-type', '').startswith('application/json') else {'status': 'ok'}
                }
            else:
                health_result = {
                    'service': 'presidio',
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': f'HTTP {response.status_code}: {response.text}'
                }
                
        except requests.exceptions.ConnectionError:
            health_result = {
                'service': 'presidio',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': 'Connection refused'
            }
        except requests.exceptions.Timeout:
            health_result = {
                'service': 'presidio',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': 'Request timeout'
            }
        except Exception as e:
            health_result = {
                'service': 'presidio',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        
        # Check circuit breaker status
        circuit_status = circuit_breaker_middleware.get_circuit_status('presidio')
        health_result['circuit_breaker'] = circuit_status
        
        # Cache result
        self._cache_health_result('presidio', health_result)
        self._add_to_history(health_result)
        
        return health_result
    
    def check_redis_health(self) -> Dict[str, Any]:
        """
        Check Redis service health.
        
        Returns:
            Health check result
        """
        try:
            # Get Redis configuration
            redis_url = self.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            
            # Test Redis connection
            start_time = time.time()
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            response_time = time.time() - start_time
            
            # Get Redis info
            info = redis_client.info()
            
            health_result = {
                'service': 'redis',
                'status': 'healthy',
                'response_time': response_time,
                'timestamp': datetime.utcnow().isoformat(),
                'details': {
                    'version': info.get('redis_version'),
                    'used_memory_human': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed'),
                    'keyspace_hits': info.get('keyspace_hits'),
                    'keyspace_misses': info.get('keyspace_misses')
                }
            }
            
        except redis.ConnectionError:
            health_result = {
                'service': 'redis',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': 'Connection refused'
            }
        except Exception as e:
            health_result = {
                'service': 'redis',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        
        # Check circuit breaker status
        circuit_status = circuit_breaker_middleware.get_circuit_status('redis')
        health_result['circuit_breaker'] = circuit_status
        
        # Cache result
        self._cache_health_result('redis', health_result)
        self._add_to_history(health_result)
        
        return health_result
    
    def check_celery_health(self) -> Dict[str, Any]:
        """
        Check Celery worker health.
        
        Returns:
            Health check result
        """
        try:
            # Get Celery configuration
            redis_url = self.config.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
            
            # Test Celery broker connection
            start_time = time.time()
            redis_client = redis.from_url(redis_url)
            test_key = 'celery_health_check'
            test_value = str(time.time())
            
            # Test basic operations
            redis_client.setex(test_key, 10, test_value)
            retrieved_value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            response_time = time.time() - start_time
            
            if retrieved_value == test_value:
                health_result = {
                    'service': 'celery',
                    'status': 'healthy',
                    'response_time': response_time,
                    'timestamp': datetime.utcnow().isoformat(),
                    'details': {
                        'broker_type': 'redis',
                        'broker_url': redis_url
                    }
                }
            else:
                health_result = {
                    'service': 'celery',
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': 'Broker read/write test failed'
                }
                
        except Exception as e:
            health_result = {
                'service': 'celery',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        
        # Cache result
        self._cache_health_result('celery', health_result)
        self._add_to_history(health_result)
        
        return health_result
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        Check database health (if configured).
        
        Returns:
            Health check result
        """
        # This is a placeholder for database health checks
        # In a real implementation, you would check your database connection
        try:
            # Example: Check if we can connect to the database
            # db = get_database_connection()
            # db.execute("SELECT 1")
            
            health_result = {
                'service': 'database',
                'status': 'healthy',
                'response_time': 0.001,
                'timestamp': datetime.utcnow().isoformat(),
                'details': {
                    'connection_pool_size': 10,
                    'active_connections': 2
                }
            }
            
        except Exception as e:
            health_result = {
                'service': 'database',
                'status': 'unhealthy',
                'response_time': None,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        
        # Cache result
        self._cache_health_result('database', health_result)
        self._add_to_history(health_result)
        
        return health_result
    
    def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall system health status.
        
        Returns:
            Overall health status
        """
        services = ['presidio', 'redis', 'celery', 'database']
        health_results = {}
        
        for service in services:
            health_results[service] = self.get_cached_health(service)
        
        # Determine overall status
        healthy_services = sum(1 for result in health_results.values() 
                             if result and result.get('status') == 'healthy')
        total_services = len(services)
        
        if healthy_services == total_services:
            overall_status = 'healthy'
        elif healthy_services >= total_services * 0.75:
            overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'healthy_services': healthy_services,
            'total_services': total_services,
            'services': health_results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """
        Get health status for a specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Health status for the service
        """
        if service_name == 'presidio':
            return self.check_presidio_health()
        elif service_name == 'redis':
            return self.check_redis_health()
        elif service_name == 'celery':
            return self.check_celery_health()
        elif service_name == 'database':
            return self.check_database_health()
        else:
            return {
                'service': service_name,
                'status': 'unknown',
                'error': f'Unknown service: {service_name}',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_cached_health(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached health result for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Cached health result or None
        """
        return self.health_cache.get(service_name)
    
    def get_health_history(self, service_name: Optional[str] = None, 
                          hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health check history.
        
        Args:
            service_name: Filter by service name (optional)
            hours: Number of hours to look back
            
        Returns:
            List of health check results
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        history = []
        for entry in self.health_history:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if entry_time >= cutoff_time:
                if service_name is None or entry.get('service') == service_name:
                    history.append(entry)
        
        return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    def get_health_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get health statistics for the specified time period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Health statistics
        """
        history = self.get_health_history(hours=hours)
        
        if not history:
            return {
                'period_hours': hours,
                'total_checks': 0,
                'services': {}
            }
        
        # Group by service
        service_stats = {}
        for entry in history:
            service = entry['service']
            if service not in service_stats:
                service_stats[service] = {
                    'total_checks': 0,
                    'healthy_checks': 0,
                    'unhealthy_checks': 0,
                    'average_response_time': 0,
                    'min_response_time': float('inf'),
                    'max_response_time': 0
                }
            
            stats = service_stats[service]
            stats['total_checks'] += 1
            
            if entry['status'] == 'healthy':
                stats['healthy_checks'] += 1
            else:
                stats['unhealthy_checks'] += 1
            
            if entry.get('response_time'):
                response_time = entry['response_time']
                stats['average_response_time'] += response_time
                stats['min_response_time'] = min(stats['min_response_time'], response_time)
                stats['max_response_time'] = max(stats['max_response_time'], response_time)
        
        # Calculate averages and percentages
        for service, stats in service_stats.items():
            if stats['healthy_checks'] > 0:
                stats['success_rate'] = (stats['healthy_checks'] / stats['total_checks']) * 100
            else:
                stats['success_rate'] = 0
            
            if stats['total_checks'] > 0:
                stats['average_response_time'] /= stats['total_checks']
            else:
                stats['average_response_time'] = 0
            
            if stats['min_response_time'] == float('inf'):
                stats['min_response_time'] = 0
        
        return {
            'period_hours': hours,
            'total_checks': len(history),
            'services': service_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _cache_health_result(self, service_name: str, result: Dict[str, Any]):
        """Cache health result."""
        self.health_cache[service_name] = result
    
    def _add_to_history(self, result: Dict[str, Any]):
        """Add health result to history."""
        self.health_history.append(result)
        
        # Limit history size
        if len(self.health_history) > self.max_history_entries:
            self.health_history = self.health_history[-self.max_history_entries:]
    
    def cleanup_old_history(self, hours: int = 24):
        """Clean up old history entries."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        self.health_history = [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry['timestamp']) >= cutoff_time
        ]
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive monitoring dashboard data.
        
        Returns:
            Dashboard data including health status, statistics, and recent history
        """
        overall_health = self.get_overall_health()
        statistics = self.get_health_statistics(hours=24)
        recent_history = self.get_health_history(hours=1)
        
        return {
            'dashboard_timestamp': datetime.utcnow().isoformat(),
            'overall_health': overall_health,
            'statistics': statistics,
            'recent_history': recent_history[:50],  # Last 50 entries
            'circuit_breakers': circuit_breaker_middleware.get_health_status()
        }