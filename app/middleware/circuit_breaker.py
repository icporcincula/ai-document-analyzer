"""
Circuit Breaker Middleware

This middleware implements the circuit breaker pattern for external service calls
to prevent cascading failures and improve system resilience.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests are failing
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreaker:
    """Circuit breaker implementation for external service calls."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Union[type, tuple] = Exception,
                 name: str = "CircuitBreaker"):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds to wait before trying again
            expected_exception: Exception types to count as failures
            name: Name for logging purposes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        # Circuit state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        self.total_requests += 1
        
        # Check if circuit should be opened
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker {self.name}: Attempting reset (half-open)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN. Request rejected.")
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Success path
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 3:  # Require 3 successes to close circuit
                    logger.info(f"Circuit breaker {self.name}: Circuit CLOSED after successful recovery")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
            
            self.total_successes += 1
            self.failure_count = 0  # Reset on success
            return result
            
        except self.expected_exception as e:
            # Failure path
            self.total_failures += 1
            self.failure_count += 1
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit breaker {self.name}: Still failing in half-open state")
                self._open_circuit()
            elif self.failure_count >= self.failure_threshold:
                logger.warning(f"Circuit breaker {self.name}: Opening circuit after {self.failure_count} failures")
                self._open_circuit()
            
            raise e
    
    def _open_circuit(self):
        """Open the circuit breaker."""
        self.state = CircuitState.OPEN
        self.last_failure_time = time.time()
        logger.error(f"Circuit breaker {self.name}: Circuit OPENED due to failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'total_requests': self.total_requests,
            'total_failures': self.total_failures,
            'total_successes': self.total_successes,
            'failure_rate': self.total_failures / max(self.total_requests, 1) * 100,
            'last_failure_time': self.last_failure_time
        }
    
    def reset(self):
        """Manually reset the circuit breaker."""
        logger.info(f"Circuit breaker {self.name}: Manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.last_failure_time = None


class CircuitBreakerMiddleware:
    """Middleware for applying circuit breakers to service calls."""
    
    def __init__(self):
        # Create circuit breakers for different services
        self.presidio_circuit = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=(ConnectionError, TimeoutError, Exception),
            name="PresidioService"
        )
        
        self.openai_circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=120,
            expected_exception=(ConnectionError, TimeoutError, Exception),
            name="OpenAIService"
        )
        
        self.redis_circuit = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=(ConnectionError, TimeoutError),
            name="RedisService"
        )
        
        self.circuits = {
            'presidio': self.presidio_circuit,
            'openai': self.openai_circuit,
            'redis': self.redis_circuit
        }
    
    def protect_presidio_call(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect Presidio service calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.presidio_circuit.call(func, *args, **kwargs)
        return wrapper
    
    def protect_openai_call(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect OpenAI service calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.openai_circuit.call(func, *args, **kwargs)
        return wrapper
    
    def protect_redis_call(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect Redis service calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.redis_circuit.call(func, *args, **kwargs)
        return wrapper
    
    def get_circuit_status(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get circuit breaker status for services.
        
        Args:
            service_name: Specific service name, or None for all services
            
        Returns:
            Circuit breaker status
        """
        if service_name:
            if service_name in self.circuits:
                return self.circuits[service_name].get_state()
            else:
                return {'error': f'Unknown service: {service_name}'}
        
        return {
            service_name: circuit.get_state()
            for service_name, circuit in self.circuits.items()
        }
    
    def reset_circuit(self, service_name: str) -> Dict[str, Any]:
        """
        Manually reset a circuit breaker.
        
        Args:
            service_name: Name of the service circuit to reset
            
        Returns:
            Reset result
        """
        if service_name in self.circuits:
            self.circuits[service_name].reset()
            return {'status': 'success', 'message': f'Circuit {service_name} reset'}
        else:
            return {'status': 'error', 'message': f'Unknown service: {service_name}'}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of all circuits."""
        circuits_status = self.get_circuit_status()
        
        # Determine overall health
        healthy_circuits = 0
        total_circuits = len(circuits_status)
        
        for service_name, status in circuits_status.items():
            if isinstance(status, dict) and status.get('state') == 'closed':
                healthy_circuits += 1
        
        return {
            'overall_health': 'healthy' if healthy_circuits == total_circuits else 'degraded',
            'healthy_circuits': healthy_circuits,
            'total_circuits': total_circuits,
            'circuits': circuits_status
        }


# Global circuit breaker middleware instance
circuit_breaker_middleware = CircuitBreakerMiddleware()


def protect_service_call(service_name: str):
    """
    Decorator to protect service calls with circuit breaker.
    
    Args:
        service_name: Name of the service (presidio, openai, redis)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if service_name == 'presidio':
                return circuit_breaker_middleware.protect_presidio_call(func)(*args, **kwargs)
            elif service_name == 'openai':
                return circuit_breaker_middleware.protect_openai_call(func)(*args, **kwargs)
            elif service_name == 'redis':
                return circuit_breaker_middleware.protect_redis_call(func)(*args, **kwargs)
            else:
                # Fallback to direct call if service not recognized
                return func(*args, **kwargs)
        return wrapper
    return decorator