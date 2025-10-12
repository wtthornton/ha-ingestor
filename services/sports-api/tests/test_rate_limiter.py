"""
Unit tests for RateLimiter
"""

import pytest
import asyncio
import time
from datetime import timedelta

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    """Test rate limiter initializes correctly"""
    limiter = RateLimiter(requests_per_second=2, burst_size=5)
    
    assert limiter.rate == 2
    assert limiter.burst_size == 5
    assert limiter.tokens == 5  # Starts with full burst
    assert limiter.total_requests == 0


@pytest.mark.asyncio
async def test_rate_limiter_allows_burst():
    """Test rate limiter allows burst requests"""
    limiter = RateLimiter(requests_per_second=1, burst_size=3)
    
    start = time.time()
    
    # Should allow 3 immediate requests (burst)
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()
    
    elapsed = time.time() - start
    
    # Should be very fast (burst capacity)
    assert elapsed < 0.5
    assert limiter.total_requests == 3


@pytest.mark.asyncio
async def test_rate_limiter_throttles_requests():
    """Test rate limiter throttles requests beyond burst"""
    limiter = RateLimiter(requests_per_second=2, burst_size=2)
    
    start = time.time()
    
    # Make 5 requests
    for i in range(5):
        await limiter.acquire()
    
    elapsed = time.time() - start
    
    # Should take ~1.5 seconds (2 burst + 3 throttled at 2/s)
    # 3 requests at 2/s = 1.5 seconds minimum
    assert elapsed >= 1.0  # Allow some variance
    assert limiter.total_requests == 5
    assert limiter.total_waits > 0


@pytest.mark.asyncio
async def test_rate_limiter_refills_tokens():
    """Test tokens refill over time"""
    limiter = RateLimiter(requests_per_second=10, burst_size=1)
    
    # Use the token
    await limiter.acquire()
    assert limiter.tokens < 1
    
    # Wait for refill
    await asyncio.sleep(0.2)  # Should refill 2 tokens at 10/s
    
    # Should have tokens available now
    await limiter.acquire()  # Should not block
    
    assert limiter.total_requests == 2


@pytest.mark.asyncio
async def test_rate_limiter_statistics():
    """Test statistics tracking"""
    limiter = RateLimiter(requests_per_second=2, burst_size=2)
    
    # Make some requests
    await limiter.acquire()  # Burst - no wait
    await limiter.acquire()  # Burst - no wait
    await limiter.acquire()  # Wait
    
    stats = limiter.get_statistics()
    
    assert stats['total_requests'] == 3
    assert stats['total_waits'] >= 1
    assert stats['total_wait_time_seconds'] > 0
    assert stats['rate_per_second'] == 2
    assert stats['burst_size'] == 2


@pytest.mark.asyncio
async def test_rate_limiter_reset_statistics():
    """Test statistics reset"""
    limiter = RateLimiter(requests_per_second=5)
    
    await limiter.acquire()
    await limiter.acquire()
    
    assert limiter.total_requests == 2
    
    limiter.reset_statistics()
    
    assert limiter.total_requests == 0
    assert limiter.total_waits == 0
    assert limiter.total_wait_time == 0.0


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_requests():
    """Test rate limiter with concurrent requests"""
    limiter = RateLimiter(requests_per_second=5, burst_size=3)
    
    # Launch 10 concurrent requests
    tasks = [limiter.acquire() for _ in range(10)]
    
    start = time.time()
    await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    # Should throttle properly
    assert limiter.total_requests == 10
    # Verify some requests were delayed (not all instant)
    assert elapsed > 0.5  # Simple check - some throttling occurred


@pytest.mark.asyncio
async def test_rate_limiter_get_hit_rate():
    """Test hit rate calculation in statistics"""
    limiter = RateLimiter(requests_per_second=10, burst_size=10)
    
    # All burst - no waits
    for i in range(5):
        await limiter.acquire()
    
    stats = limiter.get_statistics()
    
    # Most should be from burst (no waits)
    assert stats['wait_percentage'] < 100

