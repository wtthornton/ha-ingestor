"""
TTL-Based Cache Manager for API Responses
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class CacheManager:
    """
    In-memory cache with TTL (Time To Live) support.
    
    Provides intelligent caching with different TTLs for different data types:
    - Live scores: 15 seconds (frequent updates during games)
    - Recent scores: 5 minutes (less frequent updates after games)
    - Fixtures: 1 hour (schedules don't change often)
    - Standings: 1 hour (updated daily)
    - Injuries: 30 minutes (updated periodically)
    """
    
    def __init__(self):
        """Initialize cache manager"""
        self.cache: Dict[str, Tuple[Any, datetime]] = {}
        
        # TTL configuration by cache type
        self.ttls: Dict[str, timedelta] = {
            'scores_live': timedelta(seconds=15),
            'scores_recent': timedelta(minutes=5),
            'fixtures': timedelta(hours=1),
            'standings': timedelta(hours=1),
            'injuries': timedelta(minutes=30),
            'players': timedelta(minutes=30),
            'default': timedelta(minutes=5)
        }
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.evictions = 0
        
        logger.info(
            "Cache manager initialized",
            extra={"ttl_types": len(self.ttls)}
        )
    
    async def get(
        self, 
        key: str, 
        cache_type: str = 'default'
    ) -> Optional[Any]:
        """
        Get cached value if not expired.
        
        Args:
            key: Cache key
            cache_type: Type of cache (determines TTL)
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self.cache:
            self.misses += 1
            logger.debug(f"Cache miss: {key}")
            return None
        
        value, timestamp = self.cache[key]
        ttl = self.ttls.get(cache_type, self.ttls['default'])
        
        # Check if expired
        if datetime.now() - timestamp > ttl:
            del self.cache[key]
            self.evictions += 1
            self.misses += 1
            logger.debug(
                f"Cache expired: {key}",
                extra={
                    "age_seconds": (datetime.now() - timestamp).total_seconds(),
                    "ttl_seconds": ttl.total_seconds()
                }
            )
            return None
        
        self.hits += 1
        logger.debug(
            f"Cache hit: {key}",
            extra={"cache_type": cache_type}
        )
        return value
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        cache_type: str = 'default'
    ) -> None:
        """
        Set cached value with timestamp.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cache (determines TTL)
        """
        self.cache[key] = (value, datetime.now())
        self.sets += 1
        
        logger.debug(
            f"Cache set: {key}",
            extra={
                "cache_type": cache_type,
                "ttl_seconds": self.ttls.get(cache_type, self.ttls['default']).total_seconds()
            }
        )
    
    async def invalidate(self, key: str) -> bool:
        """
        Manually invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if key was found and removed, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
            logger.info(f"Cache invalidated: {key}")
            return True
        return False
    
    async def clear(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared: {count} entries")
        return count
    
    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.
        
        Returns:
            Hit rate as percentage (0.0 to 1.0)
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.hits + self.misses
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "evictions": self.evictions,
            "hit_rate": self.get_hit_rate(),
            "hit_rate_percentage": f"{self.get_hit_rate() * 100:.1f}%",
            "total_requests": total_requests,
            "cache_size": len(self.cache),
            "ttl_config": {k: v.total_seconds() for k, v in self.ttls.items()}
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters"""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.evictions = 0
        logger.info("Cache statistics reset")

