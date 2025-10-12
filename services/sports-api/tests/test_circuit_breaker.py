"""
Unit tests for CircuitBreaker - Simple and focused
"""

import pytest
import asyncio
from datetime import timedelta

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from circuit_breaker import CircuitBreaker, CircuitState


@pytest.mark.asyncio
async def test_circuit_breaker_initialization():
    """Test circuit breaker initializes in CLOSED state"""
    cb = CircuitBreaker(failure_threshold=3)
    
    assert cb.state == CircuitState.CLOSED
    assert cb.failures == 0


@pytest.mark.asyncio
async def test_circuit_breaker_allows_calls_when_closed():
    """Test circuit allows calls in CLOSED state"""
    cb = CircuitBreaker()
    
    async def success_func():
        return "success"
    
    result = await cb.call(success_func)
    
    assert result == "success"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit opens after threshold failures"""
    cb = CircuitBreaker(failure_threshold=3)
    
    async def failing_func():
        raise Exception("API Error")
    
    # Fail 3 times
    for i in range(3):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    # Should be OPEN now
    assert cb.state == CircuitState.OPEN
    assert cb.failures == 3


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_when_open():
    """Test circuit rejects calls when OPEN"""
    cb = CircuitBreaker(failure_threshold=2)
    
    async def failing_func():
        raise Exception("Error")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Should reject new calls
    async def any_func():
        return "result"
    
    with pytest.raises(Exception, match="Circuit breaker"):
        await cb.call(any_func)


@pytest.mark.asyncio
async def test_circuit_breaker_transitions_to_half_open():
    """Test circuit transitions to HALF_OPEN after timeout"""
    cb = CircuitBreaker(
        failure_threshold=2,
        timeout=timedelta(milliseconds=100)
    )
    
    async def failing_func():
        raise Exception("Error")
    
    # Open circuit
    for i in range(2):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Wait for timeout
    await asyncio.sleep(0.15)
    
    # Try call - should transition to HALF_OPEN then fail
    async def success_func():
        return "ok"
    
    result = await cb.call(success_func)
    
    # Should have transitioned to HALF_OPEN then CLOSED on success
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_statistics():
    """Test statistics tracking"""
    cb = CircuitBreaker()
    
    async def success_func():
        return "ok"
    
    await cb.call(success_func)
    await cb.call(success_func)
    
    stats = cb.get_statistics()
    
    assert stats['total_calls'] == 2
    assert stats['total_successes'] == 2
    assert stats['state'] == 'closed'


@pytest.mark.asyncio
async def test_circuit_breaker_reset():
    """Test circuit can be reset"""
    cb = CircuitBreaker(failure_threshold=2)
    
    async def failing_func():
        raise Exception("Error")
    
    # Open circuit
    for i in range(2):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Reset
    cb.reset()
    
    assert cb.state == CircuitState.CLOSED
    assert cb.failures == 0

