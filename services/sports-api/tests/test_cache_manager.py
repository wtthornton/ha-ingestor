"""
Unit tests for CacheManager
"""

import pytest
import asyncio
from datetime import timedelta

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from cache_manager import CacheManager


@pytest.mark.asyncio
async def test_cache_manager_initialization():
    """Test cache manager initializes correctly"""
    cache = CacheManager()
    
    assert len(cache.cache) == 0
    assert cache.hits == 0
    assert cache.misses == 0
    assert len(cache.ttls) > 0


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Test basic cache set and get"""
    cache = CacheManager()
    
    await cache.set("test_key", "test_value", "default")
    value = await cache.get("test_key", "default")
    
    assert value == "test_value"
    assert cache.hits == 1
    assert cache.sets == 1


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss returns None"""
    cache = CacheManager()
    
    value = await cache.get("nonexistent_key", "default")
    
    assert value is None
    assert cache.misses == 1


@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Test cache expires after TTL"""
    cache = CacheManager()
    
    # Override TTL for testing (very short)
    cache.ttls['test_type'] = timedelta(milliseconds=100)
    
    await cache.set("test_key", "test_value", "test_type")
    
    # Should hit immediately
    value = await cache.get("test_key", "test_type")
    assert value == "test_value"
    assert cache.hits == 1
    
    # Wait for expiration
    await asyncio.sleep(0.15)
    
    # Should miss after expiration
    value = await cache.get("test_key", "test_type")
    assert value is None
    assert cache.misses == 1
    assert cache.evictions == 1


@pytest.mark.asyncio
async def test_cache_different_ttls():
    """Test different TTLs for different cache types"""
    cache = CacheManager()
    
    # Check TTL configuration
    assert cache.ttls['scores_live'] == timedelta(seconds=15)
    assert cache.ttls['scores_recent'] == timedelta(minutes=5)
    assert cache.ttls['fixtures'] == timedelta(hours=1)
    assert cache.ttls['standings'] == timedelta(hours=1)


@pytest.mark.asyncio
async def test_cache_invalidate():
    """Test manual cache invalidation"""
    cache = CacheManager()
    
    await cache.set("test_key", "test_value", "default")
    
    # Invalidate
    result = await cache.invalidate("test_key")
    
    assert result is True
    assert "test_key" not in cache.cache
    
    # Try to invalidate again
    result = await cache.invalidate("test_key")
    assert result is False


@pytest.mark.asyncio
async def test_cache_clear():
    """Test clearing all cache entries"""
    cache = CacheManager()
    
    await cache.set("key1", "value1", "default")
    await cache.set("key2", "value2", "default")
    await cache.set("key3", "value3", "default")
    
    count = await cache.clear()
    
    assert count == 3
    assert len(cache.cache) == 0


@pytest.mark.asyncio
async def test_cache_hit_rate():
    """Test hit rate calculation"""
    cache = CacheManager()
    
    await cache.set("key1", "value1", "default")
    
    # 3 hits
    await cache.get("key1", "default")
    await cache.get("key1", "default")
    await cache.get("key1", "default")
    
    # 1 miss
    await cache.get("key2", "default")
    
    hit_rate = cache.get_hit_rate()
    
    # 3 hits out of 4 requests = 0.75
    assert hit_rate == 0.75


@pytest.mark.asyncio
async def test_cache_statistics():
    """Test statistics collection"""
    cache = CacheManager()
    
    await cache.set("key1", "value1", "default")
    await cache.get("key1", "default")  # Hit
    await cache.get("key2", "default")  # Miss
    
    stats = cache.get_statistics()
    
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['sets'] == 1
    assert stats['cache_size'] == 1
    assert 'hit_rate' in stats
    assert 'hit_rate_percentage' in stats


@pytest.mark.asyncio
async def test_cache_reset_statistics():
    """Test statistics reset"""
    cache = CacheManager()
    
    await cache.set("key1", "value1", "default")
    await cache.get("key1", "default")
    
    assert cache.hits == 1
    
    cache.reset_statistics()
    
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.sets == 0


@pytest.mark.asyncio
async def test_cache_stores_complex_objects():
    """Test cache can store complex objects"""
    cache = CacheManager()
    
    complex_obj = {
        'list': [1, 2, 3],
        'dict': {'nested': 'value'},
        'number': 42
    }
    
    await cache.set("complex", complex_obj, "default")
    value = await cache.get("complex", "default")
    
    assert value == complex_obj
    assert value['list'] == [1, 2, 3]

