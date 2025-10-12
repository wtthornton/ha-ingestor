"""
Tests for Cache Service

Following Context7 KB pytest patterns for async testing
"""

import pytest
import asyncio
from src.cache_service import CacheService


@pytest.fixture
def cache():
    """Fixture for CacheService instance"""
    return CacheService()


@pytest.mark.asyncio
async def test_cache_set_and_get(cache):
    """Test basic cache set and get operations"""
    await cache.set('test_key', 'test_value', ttl=60)
    
    result = await cache.get('test_key')
    assert result == 'test_value'


@pytest.mark.asyncio
async def test_cache_expiry(cache):
    """Test that cache entries expire after TTL"""
    await cache.set('expiring_key', 'value', ttl=1)
    
    # Should exist immediately
    result = await cache.get('expiring_key')
    assert result == 'value'
    
    # Wait for expiry
    await asyncio.sleep(1.1)
    
    # Should be gone
    result = await cache.get('expiring_key')
    assert result is None


@pytest.mark.asyncio
async def test_cache_miss(cache):
    """Test cache miss returns None"""
    result = await cache.get('nonexistent_key')
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete(cache):
    """Test cache deletion"""
    await cache.set('delete_me', 'value')
    assert await cache.get('delete_me') == 'value'
    
    await cache.delete('delete_me')
    assert await cache.get('delete_me') is None


@pytest.mark.asyncio
async def test_cache_clear(cache):
    """Test clearing all cache"""
    await cache.set('key1', 'value1')
    await cache.set('key2', 'value2')
    
    assert await cache.get('key1') == 'value1'
    assert await cache.get('key2') == 'value2'
    
    await cache.clear()
    
    assert await cache.get('key1') is None
    assert await cache.get('key2') is None


def test_cache_is_connected(cache):
    """Test cache connection status"""
    assert cache.is_connected() is True


@pytest.mark.asyncio
async def test_cache_stats(cache):
    """Test cache statistics tracking"""
    # Initial state
    stats = cache.get_stats()
    assert stats['hits'] == 0
    assert stats['misses'] == 0
    assert stats['hit_rate'] == 0
    
    # Cache miss
    await cache.get('nonexistent')
    stats = cache.get_stats()
    assert stats['misses'] == 1
    
    # Cache set and hit
    await cache.set('test', 'value')
    await cache.get('test')
    stats = cache.get_stats()
    assert stats['hits'] == 1
    assert stats['keys_count'] == 1
    assert stats['hit_rate'] > 0


@pytest.mark.asyncio
async def test_cache_overwrites_existing_key(cache):
    """Test that setting an existing key updates the value"""
    await cache.set('key', 'value1')
    assert await cache.get('key') == 'value1'
    
    await cache.set('key', 'value2')
    assert await cache.get('key') == 'value2'

