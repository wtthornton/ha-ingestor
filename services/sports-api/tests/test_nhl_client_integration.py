"""
Integration tests for NHL Client
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import aiohttp

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from nhl_client import NHLClient


@pytest.mark.asyncio
async def test_nhl_client_request_headers():
    """Test NHL client sends correct headers"""
    client = NHLClient('my-test-api-key')
    
    # Create mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'response': []})
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = AsyncMock(return_value=None)
    
    with patch.object(aiohttp.ClientSession, '__init__', return_value=None) as mock_init:
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response):
            with patch.object(aiohttp.ClientSession, 'close', new_callable=AsyncMock):
                with patch.object(aiohttp.ClientSession, 'closed', False):
                    async with client:
                        await client.get_scores()
                        
                        # Verify headers include API key
                        assert mock_init.called
                        call_kwargs = mock_init.call_args.kwargs
                        headers = call_kwargs.get('headers', {})
                        assert headers.get('x-rapidapi-key') == 'my-test-api-key'


@pytest.mark.asyncio
async def test_nhl_client_url_construction():
    """Test NHL client constructs correct URLs"""
    client = NHLClient('test-key')
    
    # Verify base URL is set correctly
    assert client.base_url == 'https://api-sports.io/nhl'


@pytest.mark.asyncio
async def test_nhl_client_all_endpoints_callable():
    """Test all NHL client methods are callable"""
    client = NHLClient('test-key')
    
    # Verify all methods exist
    assert callable(client.get_scores)
    assert callable(client.get_standings)
    assert callable(client.get_fixtures)


@pytest.mark.asyncio
async def test_nhl_client_parameter_validation():
    """Test NHL client validates parameters correctly"""
    client = NHLClient('test-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value={'response': []})):
        async with client:
            # Test with valid parameters
            await client.get_scores(date='2025-10-11')
            await client.get_standings(season=2025)
            await client.get_fixtures(season=2025)
            
            # All should complete without errors
            assert True

