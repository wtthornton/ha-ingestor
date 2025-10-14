"""
Unit tests for Circuit Breaker

Simple tests for circuit breaker functionality.
Story 12.1 - InfluxDB Persistence Layer
"""

import pytest
from datetime import datetime, timedelta
from src.circuit_breaker import CircuitBreaker


def test_circuit_breaker_starts_closed():
    """Circuit breaker should start in closed state"""
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
    assert not cb.is_open()


def test_circuit_breaker_opens_after_threshold():
    """Circuit breaker should open after threshold failures"""
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
    
    cb.record_failure()  # 1
    assert not cb.is_open()
    
    cb.record_failure()  # 2
    assert not cb.is_open()
    
    cb.record_failure()  # 3 - should open
    assert cb.is_open()


def test_circuit_breaker_resets_on_success():
    """Circuit breaker should reset failure count on success"""
    cb = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
    
    cb.record_failure()  # 1
    cb.record_failure()  # 2
    assert cb.failure_count == 2
    
    cb.record_success()
    assert cb.failure_count == 0
    assert not cb.is_open()


def test_circuit_breaker_auto_recovers_after_timeout():
    """Circuit breaker should auto-recover after timeout"""
    cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)
    
    # Open the circuit
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open()
    
    # Wait for timeout
    import time
    time.sleep(1.1)
    
    # Circuit should allow retry
    assert not cb.is_open()


def test_circuit_breaker_get_status():
    """Circuit breaker should report correct status"""
    cb = CircuitBreaker(failure_threshold=2)
    
    assert cb.get_status() == 'closed'
    
    cb.record_failure()
    cb.record_failure()
    assert cb.get_status() == 'open'

