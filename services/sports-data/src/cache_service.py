"""
Simple In-Memory Cache Service

For Phase 1, uses Python dict with TTL. Can be upgraded to Redis in Phase 2.
"""

import asyncio
from typing import Optional, Any
import time
from datetime import datetime


class CacheService:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self):
        self.cache: dict[str, tuple[Any, float]] = {}
        self.hits = 0
        self.misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, expiry = self.cache[key]
            current_time = time.time()
            
            if expiry > current_time:
                self.hits += 1
                return value
            else:
                # Expired, remove it
                del self.cache[key]
                self.misses += 1
        else:
            self.misses += 1
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 60):
        """Set value in cache with TTL in seconds"""
        expiry = time.time() + ttl
        self.cache[key] = (value, expiry)
    
    async def delete(self, key: str):
        """Delete a key from cache"""
        if key in self.cache:
            del self.cache[key]
    
    async def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def is_connected(self) -> bool:
        """Check if cache is available (always true for in-memory)"""
        return True
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "keys_count": len(self.cache),
            "timestamp": datetime.utcnow().isoformat()
        }

