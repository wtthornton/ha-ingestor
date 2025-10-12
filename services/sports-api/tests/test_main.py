"""
Unit tests for Sports API Service main module
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from aiohttp import web

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Mock shared modules before importing main
sys.modules['shared'] = MagicMock()
sys.modules['shared.logging_config'] = MagicMock()
sys.modules['shared.correlation_middleware'] = MagicMock()

# Mock the functions that main.py uses
mock_setup_logging = MagicMock(return_value=MagicMock())

# Create a proper async middleware mock
async def mock_middleware(app, handler):
    async def middleware_handler(request):
        return await handler(request)
    return middleware_handler

mock_create_correlation_middleware = MagicMock(return_value=mock_middleware)

sys.modules['shared.logging_config'].setup_logging = mock_setup_logging
sys.modules['shared.correlation_middleware'].create_correlation_middleware = mock_create_correlation_middleware

from main import SportsAPIService


@pytest.mark.asyncio
async def test_sports_api_service_initialization():
    """Test service initializes with correct configuration"""
    with patch.dict(os.environ, {
        'API_SPORTS_KEY': 'my-test-key',
        'SPORTS_API_PORT': '8015',
        'NFL_ENABLED': 'true',
        'NHL_ENABLED': 'false'
    }):
        service = SportsAPIService()
        
        assert service.api_key == 'my-test-key'
        assert service.port == 8015
        assert service.nfl_enabled is True
        assert service.nhl_enabled is False


@pytest.mark.asyncio
async def test_sports_api_service_missing_api_key():
    """Test service handles missing API key gracefully"""
    with patch.dict(os.environ, {}, clear=True):
        service = SportsAPIService()
        
        # Service should still initialize even without API key
        assert service.api_key is None


@pytest.mark.asyncio
async def test_sports_api_service_default_values():
    """Test service uses default values when env vars not set"""
    with patch.dict(os.environ, {}, clear=True):
        service = SportsAPIService()
        
        assert service.port == 8015
        assert service.nfl_enabled is True
        assert service.nhl_enabled is True


@pytest.mark.asyncio
async def test_sports_api_service_start():
    """Test service start method"""
    with patch.dict(os.environ, {'API_SPORTS_KEY': 'test-key'}):
        service = SportsAPIService()
        
        await service.start()
        
        # Currently just logs, no components to initialize
        # Future stories will add component initialization
        assert True


@pytest.mark.asyncio
async def test_sports_api_service_stop():
    """Test service stop method"""
    with patch.dict(os.environ, {'API_SPORTS_KEY': 'test-key'}):
        service = SportsAPIService()
        
        await service.stop()
        
        # Currently just logs, no components to cleanup
        # Future stories will add component cleanup
        assert True


@pytest.mark.asyncio
async def test_create_app_returns_web_application():
    """Test create_app returns aiohttp Application"""
    with patch.dict(os.environ, {'API_SPORTS_KEY': 'test-key'}):
        service = SportsAPIService()
        app = service.create_app()
        
        assert isinstance(app, web.Application)
        assert len(app.router.routes()) > 0  # Should have at least /health
        assert len(app.middlewares) > 0  # Should have correlation middleware


@pytest.mark.asyncio
async def test_create_app_registers_health_endpoint():
    """Test create_app registers /health endpoint"""
    with patch.dict(os.environ, {'API_SPORTS_KEY': 'test-key'}):
        service = SportsAPIService()
        app = service.create_app()
        
        # Check that /health route exists
        routes = [route.resource.canonical for route in app.router.routes() if hasattr(route.resource, 'canonical')]
        assert '/health' in routes


@pytest.mark.asyncio
async def test_service_components_initialization():
    """Test service initializes components correctly"""
    with patch.dict(os.environ, {'API_SPORTS_KEY': 'test-key'}):
        service = SportsAPIService()
        
        # Components initialized in __init__
        assert service.rate_limiter is not None
        assert service.cache_manager is not None
        
        # Clients initialized in start() method
        assert service.nfl_client is None  # Not started yet
        assert service.nhl_client is None  # Not started yet

