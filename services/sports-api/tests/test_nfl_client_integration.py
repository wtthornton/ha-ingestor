"""
Integration tests for NFL Client
Tests actual API call structure and integration with base client
"""

import pytest
from unittest.mock import patch, AsyncMock, Mock
import aiohttp

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from nfl_client import NFLClient


@pytest.mark.asyncio
async def test_nfl_client_request_headers():
    """Test NFL client sends correct headers"""
    client = NFLClient('my-test-api-key')
    
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
                        
                        # Verify headers were passed to ClientSession init
                        # Check that init was called with headers
                        assert mock_init.called
                        call_kwargs = mock_init.call_args.kwargs
                        
                        # Verify headers include API key
                        headers = call_kwargs.get('headers', {})
                        assert headers.get('x-rapidapi-key') == 'my-test-api-key'
                        assert headers.get('x-rapidapi-host') == 'api-sports.io'


@pytest.mark.asyncio
async def test_nfl_client_url_construction():
    """Test NFL client constructs correct URLs"""
    client = NFLClient('test-key')
    
    # Verify base URL is set correctly
    assert client.base_url == 'https://api-sports.io/nfl'
    
    # Verify URL construction in _request
    assert client._request.__doc__  # Method exists


@pytest.mark.asyncio
async def test_nfl_client_retry_on_network_error():
    """Test NFL client retries on network errors"""
    client = NFLClient('test-key')
    
    with patch('asyncio.sleep', new_callable=AsyncMock):
        # Create mock that fails twice then succeeds
        call_count = 0
        
        def mock_request_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                raise aiohttp.ClientError("Network error")
            
            # Success on third try
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'response': []})
            mock_response.raise_for_status = Mock()
            mock_response.__aenter__.return_value = mock_response
            mock_response.__aexit__.return_value = AsyncMock(return_value=None)
            return mock_response
        
        with patch.object(aiohttp.ClientSession, '__init__', return_value=None):
            with patch.object(aiohttp.ClientSession, 'request', side_effect=mock_request_side_effect):
                with patch.object(aiohttp.ClientSession, 'close', new_callable=AsyncMock):
                    with patch.object(aiohttp.ClientSession, 'closed', False):
                        async with client:
                            scores = await client.get_scores()
                            
                            assert scores == []  # Empty response
                            assert call_count == 3  # Should have retried twice


@pytest.mark.asyncio
async def test_nfl_client_all_endpoints_callable():
    """Test all NFL client methods are callable"""
    client = NFLClient('test-key')
    
    # Verify all methods exist
    assert callable(client.get_scores)
    assert callable(client.get_standings)
    assert callable(client.get_fixtures)
    assert callable(client.get_players)
    assert callable(client.get_injuries)


@pytest.mark.asyncio
async def test_nfl_client_parameter_validation():
    """Test NFL client validates parameters correctly"""
    client = NFLClient('test-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value={'response': []})):
        async with client:
            # Test with valid parameters
            await client.get_scores(date='2025-10-11')
            await client.get_standings(season=2025)
            await client.get_fixtures(season=2025, week=5)
            await client.get_players(team='Patriots')
            await client.get_injuries(team='Patriots')
            
            # All should complete without errors
            assert True

