"""Retry logic and circuit breaker utilities for external service calls."""

import asyncio
import random
import time
from typing import Any, Callable, Optional, TypeVar, Union
from functools import wraps

import tenacity
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)
from tenacity.retry import retry_base
from tenacity.wait import wait_base

from .logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

# Exception types that should trigger retries
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    asyncio.TimeoutError,
)


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker pattern implementation for external service calls."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery
            expected_exception: Exception type that counts as failure
            name: Name for logging and identification
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        # Circuit state
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        # Metrics
        self._total_calls = 0
        self._successful_calls = 0
        self._failed_calls = 0
        self._circuit_opens = 0
        
        logger.debug("Circuit breaker initialized",
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout)
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self._state == "OPEN":
            # Check if recovery timeout has passed
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN", name=self.name)
            else:
                return True
        return False
    
    def record_success(self) -> None:
        """Record successful call."""
        self._total_calls += 1
        self._successful_calls += 1
        self._failure_count = 0
        
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
            logger.info("Circuit breaker closed after successful call", name=self.name)
    
    def record_failure(self, exception: Exception) -> None:
        """Record failed call."""
        self._total_calls += 1
        self._failed_calls += 1
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold and self._state == "CLOSED":
            self._state = "OPEN"
            self._circuit_opens += 1
            logger.warning("Circuit breaker opened due to failures",
                          name=self.name,
                          failure_count=self._failure_count,
                          failure_threshold=self.failure_threshold)
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "total_calls": self._total_calls,
            "successful_calls": self._successful_calls,
            "failed_calls": self._failed_calls,
            "circuit_opens": self._circuit_opens,
            "last_failure_time": self._last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }


def create_retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = RETRYABLE_EXCEPTIONS,
    before_sleep: Optional[Callable] = None,
    after: Optional[Callable] = None,
    **kwargs
) -> retry_base:
    """Create a retry decorator with configurable parameters.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_exceptions: Tuple of exceptions that should trigger retries
        before_sleep: Function to call before sleeping
        after: Function to call after all attempts
        **kwargs: Additional tenacity parameters
    
    Returns:
        Configured retry decorator
    """
    wait_strategy = wait_exponential(
        multiplier=base_delay,
        max=max_delay,
        exp_base=exponential_base
    )
    
    if jitter:
        wait_strategy = wait_random_exponential(
            multiplier=base_delay,
            max=max_delay,
            exp_base=exponential_base
        )
    
    if before_sleep is None:
        before_sleep = before_sleep_log(logger, "WARNING")
    
    if after is None:
        after = after_log(logger, "INFO")
    
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_strategy,
        retry=retry_if_exception_type(retry_exceptions),
        before_sleep=before_sleep,
        after=after,
        **kwargs
    )


def create_async_retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: tuple = RETRYABLE_EXCEPTIONS,
    before_sleep: Optional[Callable] = None,
    after: Optional[Callable] = None,
    **kwargs
) -> retry_base:
    """Create an async retry decorator with configurable parameters.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retry_exceptions: Tuple of exceptions that should trigger retries
        before_sleep: Function to call before sleeping
        after: Function to call after all attempts
        **kwargs: Additional tenacity parameters
    
    Returns:
        Configured async retry decorator
    """
    return create_retry_decorator(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_exceptions=retry_exceptions,
        before_sleep=before_sleep,
        after=after,
        **kwargs
    )


def with_circuit_breaker(
    circuit_breaker: CircuitBreaker,
    fallback: Optional[Callable] = None,
    fallback_args: tuple = (),
    fallback_kwargs: dict = None
):
    """Decorator to apply circuit breaker pattern to a function.
    
    Args:
        circuit_breaker: CircuitBreaker instance
        fallback: Fallback function to call when circuit is open
        fallback_args: Arguments to pass to fallback function
        fallback_kwargs: Keyword arguments to pass to fallback function
    
    Returns:
        Decorated function
    """
    if fallback_kwargs is None:
        fallback_kwargs = {}
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if circuit_breaker.is_open():
                if fallback:
                    logger.warning("Circuit breaker open, using fallback",
                                  circuit_breaker=circuit_breaker.name)
                    return fallback(*fallback_args, **fallback_kwargs)
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker {circuit_breaker.name} is open"
                    )
            
            try:
                result = func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except circuit_breaker.expected_exception as e:
                circuit_breaker.record_failure(e)
                raise
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            if circuit_breaker.is_open():
                if fallback:
                    logger.warning("Circuit breaker open, using fallback",
                                  circuit_breaker=circuit_breaker.name)
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*fallback_args, **fallback_kwargs)
                    else:
                        return fallback(*fallback_args, **fallback_kwargs)
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker {circuit_breaker.name} is open"
                    )
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except circuit_breaker.expected_exception as e:
                circuit_breaker.record_failure(e)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# Pre-configured retry decorators for common use cases
mqtt_retry = create_retry_decorator(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retry_exceptions=(ConnectionError, TimeoutError, OSError)
)

websocket_retry = create_async_retry_decorator(
    max_attempts=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    retry_exceptions=(ConnectionError, TimeoutError, OSError, asyncio.TimeoutError)
)

influxdb_retry = create_async_retry_decorator(
    max_attempts=5,
    base_delay=0.5,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
    retry_exceptions=(ConnectionError, TimeoutError, OSError, asyncio.TimeoutError)
)

# Common circuit breaker configurations
mqtt_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    expected_exception=ConnectionError,
    name="mqtt_client"
)

websocket_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    expected_exception=ConnectionError,
    name="websocket_client"
)

influxdb_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0,
    expected_exception=Exception,
    name="influxdb_writer"
)
