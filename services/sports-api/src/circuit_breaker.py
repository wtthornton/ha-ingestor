"""
Circuit Breaker Pattern for API Resilience
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    Prevents cascading failures by opening circuit after threshold failures.
    Allows recovery testing after timeout period.
    """
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        timeout: timedelta = timedelta(minutes=5),
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Time to wait before attempting recovery
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name
        
        # State
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        
        # Statistics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = 0
        
        logger.info(
            f"Circuit breaker '{name}' initialized",
            extra={
                "failure_threshold": failure_threshold,
                "timeout_seconds": timeout.total_seconds()
            }
        )
    
    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is OPEN or function fails
        """
        self.total_calls += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > self.timeout:
                # Attempt recovery
                self._change_state(CircuitState.HALF_OPEN)
            else:
                logger.warning(
                    f"Circuit breaker '{self.name}' is OPEN - request rejected",
                    extra={
                        "failures": self.failures,
                        "time_since_failure": (
                            (datetime.now() - self.last_failure_time).total_seconds()
                            if self.last_failure_time else 0
                        )
                    }
                )
                raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            
            # Success - handle state transitions
            self.total_successes += 1
            self.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Recovery successful
                self._change_state(CircuitState.CLOSED)
                self.failures = 0
            
            return result
            
        except Exception as e:
            # Failure - track and update state
            self.failures += 1
            self.total_failures += 1
            self.last_failure_time = datetime.now()
            
            logger.warning(
                f"Circuit breaker '{self.name}' - call failed",
                extra={
                    "error": str(e),
                    "failures": self.failures,
                    "threshold": self.failure_threshold,
                    "state": self.state.value
                }
            )
            
            # Check if should open circuit
            if self.failures >= self.failure_threshold and \
               self.state == CircuitState.CLOSED:
                self._change_state(CircuitState.OPEN)
            
            raise
    
    def _change_state(self, new_state: CircuitState) -> None:
        """
        Change circuit breaker state.
        
        Args:
            new_state: New state to transition to
        """
        old_state = self.state
        self.state = new_state
        self.state_changes += 1
        
        logger.warning(
            f"Circuit breaker '{self.name}' state changed",
            extra={
                "old_state": old_state.value,
                "new_state": new_state.value,
                "failures": self.failures
            }
        )
    
    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failures = 0
        logger.info(f"Circuit breaker '{self.name}' reset to CLOSED")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get circuit breaker statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "state": self.state.value,
            "failures": self.failures,
            "failure_threshold": self.failure_threshold,
            "total_calls": self.total_calls,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": (
                self.total_successes / self.total_calls
                if self.total_calls > 0 else 0.0
            ),
            "state_changes": self.state_changes,
            "last_failure_time": (
                self.last_failure_time.isoformat()
                if self.last_failure_time else None
            ),
            "last_success_time": (
                self.last_success_time.isoformat()
                if self.last_success_time else None
            )
        }

