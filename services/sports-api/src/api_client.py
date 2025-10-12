"""
Base API Client for API-SPORTS
Implements Context7 KB best practices for aiohttp
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


class APISportsClient:
    """
    Base API client for API-SPORTS with connection pooling and retry logic.
    
    Implements Context7 KB patterns:
    - TCPConnector for connection pooling
    - ClientTimeout configuration
    - Exponential backoff retry
    - Graceful shutdown
    """
    
    def __init__(self, api_key: str, base_url: str, rate_limiter=None):
        """
        Initialize API client.
        
        Args:
            api_key: API-SPORTS API key
            base_url: Base URL for API endpoints
            rate_limiter: Optional RateLimiter instance
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = rate_limiter
        
        # Statistics
        self.requests_made = 0
        self.requests_failed = 0
        self.last_request_time: Optional[datetime] = None
    
    async def __aenter__(self):
        """
        Async context manager entry.
        
        Creates ClientSession with Context7 KB configuration:
        - Connection pooling (limit=30, limit_per_host=10)
        - Timeout settings (total=30s, connect=10s)
        - Authentication headers
        """
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_headers()
        )
        
        logger.info(
            "API client initialized",
            extra={
                "base_url": self.base_url,
                "connection_limit": 30,
                "timeout_total": 30,
                "timeout_connect": 10
            }
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit with graceful shutdown.
        
        Context7 KB pattern: await asyncio.sleep(0) after session.close()
        for proper connection cleanup.
        """
        if self.session:
            await self.session.close()
            # Graceful shutdown - Context7 KB best practice
            await asyncio.sleep(0)
            
            logger.info(
                "API client closed",
                extra={
                    "requests_made": self.requests_made,
                    "requests_failed": self.requests_failed
                }
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with API authentication.
        
        Returns:
            Dict with authentication and user agent headers
        """
        return {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'api-sports.io',
            'User-Agent': 'HA-Ingestor-Sports/1.0'
        }
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with retry logic.
        
        Implements exponential backoff retry pattern (3 attempts):
        - Attempt 1: immediate
        - Attempt 2: 0.1s delay
        - Attempt 3: 0.2s delay
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for request
            
        Returns:
            JSON response as dictionary
            
        Raises:
            aiohttp.ClientError: On final retry failure
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use 'async with' context manager.")
        
        # Apply rate limiting if configured
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(3):
            try:
                self.last_request_time = datetime.now()
                
                async with self.session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    self.requests_made += 1
                    
                    data = await response.json()
                    
                    logger.debug(
                        "API request successful",
                        extra={
                            "method": method,
                            "endpoint": endpoint,
                            "status": response.status,
                            "attempt": attempt + 1
                        }
                    )
                    
                    return data
                    
            except aiohttp.ClientError as e:
                self.requests_failed += 1
                
                if attempt == 2:  # Final attempt
                    logger.error(
                        "API request failed after retries",
                        extra={
                            "method": method,
                            "endpoint": endpoint,
                            "error": str(e),
                            "attempts": 3
                        }
                    )
                    raise
                
                # Exponential backoff
                wait_time = 0.1 * (attempt + 1)
                logger.warning(
                    "API request failed, retrying",
                    extra={
                        "method": method,
                        "endpoint": endpoint,
                        "error": str(e),
                        "attempt": attempt + 1,
                        "retry_delay": wait_time
                    }
                )
                await asyncio.sleep(wait_time)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with request statistics
        """
        return {
            "requests_made": self.requests_made,
            "requests_failed": self.requests_failed,
            "success_rate": (
                (self.requests_made - self.requests_failed) / self.requests_made
                if self.requests_made > 0 else 0.0
            ),
            "last_request_time": (
                self.last_request_time.isoformat()
                if self.last_request_time else None
            )
        }

