"""
Token Bucket Rate Limiter for API Request Throttling
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API requests.
    
    Implements token bucket algorithm with configurable rate and burst capacity.
    Allows bursts while maintaining average request rate over time.
    """
    
    def __init__(self, requests_per_second: float, burst_size: int = 5):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum average requests per second
            burst_size: Maximum burst capacity (tokens available initially)
        """
        self.rate = requests_per_second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.last_update = datetime.now()
        self.lock = asyncio.Lock()
        
        # Statistics
        self.total_requests = 0
        self.total_waits = 0
        self.total_wait_time = 0.0
        
        logger.info(
            "Rate limiter initialized",
            extra={
                "requests_per_second": requests_per_second,
                "burst_size": burst_size
            }
        )
    
    async def acquire(self) -> None:
        """
        Acquire a token for making a request.
        
        Waits if no tokens are available. Tokens refill at configured rate.
        """
        async with self.lock:
            now = datetime.now()
            elapsed = (now - self.last_update).total_seconds()
            
            # Refill tokens based on time elapsed
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            self.total_requests += 1
            
            if self.tokens >= 1:
                # Token available, consume it
                self.tokens -= 1
                return
            
            # Need to wait for next token
            wait_time = (1 - self.tokens) / self.rate
            self.total_waits += 1
            self.total_wait_time += wait_time
            
            logger.debug(
                "Rate limit delay",
                extra={
                    "wait_time_seconds": wait_time,
                    "tokens_available": self.tokens
                }
            )
            
            await asyncio.sleep(wait_time)
            self.tokens = 0  # Consumed the token we waited for
    
    def get_statistics(self) -> dict:
        """
        Get rate limiter statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_requests": self.total_requests,
            "total_waits": self.total_waits,
            "total_wait_time_seconds": self.total_wait_time,
            "avg_wait_time_seconds": (
                self.total_wait_time / self.total_waits
                if self.total_waits > 0 else 0.0
            ),
            "wait_percentage": (
                (self.total_waits / self.total_requests * 100)
                if self.total_requests > 0 else 0.0
            ),
            "tokens_available": self.tokens,
            "rate_per_second": self.rate,
            "burst_size": self.burst_size
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters"""
        self.total_requests = 0
        self.total_waits = 0
        self.total_wait_time = 0.0
        logger.info("Rate limiter statistics reset")

