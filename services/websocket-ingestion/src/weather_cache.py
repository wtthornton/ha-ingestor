"""
Weather Data Caching System
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import OrderedDict
import json

logger = logging.getLogger(__name__)


class WeatherCache:
    """In-memory weather data cache with TTL support"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize weather cache
        
        Args:
            max_size: Maximum number of cached entries
            default_ttl: Default TTL in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Cache storage using OrderedDict for LRU eviction
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
        
        # Cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Cleanup interval
        self.cleanup_interval = 60  # seconds
    
    async def start(self):
        """Start the cache cleanup task"""
        if self.is_running:
            return
        
        self.is_running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Weather cache started with max_size={self.max_size}, ttl={self.default_ttl}s")
    
    async def stop(self):
        """Stop the cache cleanup task"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Weather cache stopped")
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get weather data from cache
        
        Args:
            key: Cache key (location or coordinates)
            
        Returns:
            Weather data or None if not found/expired
        """
        self.total_requests += 1
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        # Check if entry is expired
        entry = self.cache[key]
        if self._is_expired(entry):
            # Remove expired entry
            del self.cache[key]
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        
        logger.debug(f"Cache hit for key: {key}")
        return entry["data"]
    
    async def put(self, key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Put weather data in cache
        
        Args:
            key: Cache key (location or coordinates)
            data: Weather data to cache
            ttl: TTL in seconds (optional, uses default if not provided)
            
        Returns:
            True if successfully cached
        """
        try:
            # Use provided TTL or default
            cache_ttl = ttl if ttl is not None else self.default_ttl
            
            # Create cache entry
            entry = {
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "ttl": cache_ttl
            }
            
            # Remove existing entry if it exists
            if key in self.cache:
                del self.cache[key]
            
            # Add new entry
            self.cache[key] = entry
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            
            # Evict if cache is full
            if len(self.cache) > self.max_size:
                await self._evict_lru()
            
            logger.debug(f"Cached weather data for key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching weather data for key {key}: {e}")
            return False
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        try:
            timestamp = datetime.fromisoformat(entry["timestamp"])
            ttl = entry["ttl"]
            expiry_time = timestamp + timedelta(seconds=ttl)
            return datetime.now() > expiry_time
        except Exception:
            return True
    
    async def _evict_lru(self):
        """Evict least recently used entry"""
        if self.cache:
            # Remove first item (least recently used)
            key, _ = self.cache.popitem(last=False)
            self.evictions += 1
            logger.debug(f"Evicted cache entry for key: {key}")
    
    async def _cleanup_loop(self):
        """Cleanup loop for expired entries"""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                if not self.is_running:
                    break
                
                # Find expired entries
                expired_keys = []
                for key, entry in self.cache.items():
                    if self._is_expired(entry):
                        expired_keys.append(key)
                
                # Remove expired entries
                for key in expired_keys:
                    del self.cache[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
    
    async def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Weather cache cleared")
    
    async def clear_expired(self):
        """Clear only expired cache entries"""
        expired_keys = []
        for key, entry in self.cache.items():
            if self._is_expired(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        hit_rate = 0
        if self.total_requests > 0:
            hit_rate = (self.hits / self.total_requests) * 100
        
        return {
            "is_running": self.is_running,
            "max_size": self.max_size,
            "current_size": len(self.cache),
            "default_ttl": self.default_ttl,
            "total_requests": self.total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 2),
            "cleanup_interval": self.cleanup_interval
        }
    
    def get_cache_keys(self) -> list:
        """Get list of cache keys"""
        return list(self.cache.keys())
    
    def configure_max_size(self, max_size: int):
        """Configure maximum cache size"""
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        
        self.max_size = max_size
        logger.info(f"Updated cache max_size to {max_size}")
    
    def configure_ttl(self, ttl: int):
        """Configure default TTL"""
        if ttl <= 0:
            raise ValueError("TTL must be positive")
        
        self.default_ttl = ttl
        logger.info(f"Updated cache TTL to {ttl}s")
    
    def configure_cleanup_interval(self, interval: int):
        """Configure cleanup interval"""
        if interval <= 0:
            raise ValueError("Cleanup interval must be positive")
        
        self.cleanup_interval = interval
        logger.info(f"Updated cleanup interval to {interval}s")
    
    def reset_statistics(self):
        """Reset cache statistics"""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
        logger.info("Weather cache statistics reset")
