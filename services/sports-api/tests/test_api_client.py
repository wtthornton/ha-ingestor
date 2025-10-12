"""
Unit tests for APISportsClient
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

import aiohttp

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from api_client import APISportsClient


@pytest.mark.asyncio
async def test_api_client_initialization():
    """Test API client initializes correctly"""
    client = APISportsClient('test-api-key', 'https://test.api.com')
    
    assert client.api_key == 'test-api-key'
    assert client.base_url == 'https://test.api.com'
    assert client.session is None
    assert client.requests_made == 0
    assert client.requests_failed == 0


@pytest.mark.asyncio
async def test_api_client_context_manager():
    """Test API client works as async context manager"""
    client = APISportsClient('test-api-key', 'https://test.api.com')
    
    async with client:
        assert client.session is not None
        assert isinstance(client.session, aiohttp.ClientSession)
        assert client.session.timeout.total == 30
        assert client.session.timeout.connect == 10
    
    # Session should be closed after context exit
    assert client.session.closed


@pytest.mark.asyncio
async def test_api_client_headers():
    """Test API client generates correct headers"""
    client = APISportsClient('my-secret-key', 'https://test.api.com')
    
    headers = client._get_headers()
    
    assert headers['x-rapidapi-key'] == 'my-secret-key'
    assert headers['x-rapidapi-host'] == 'api-sports.io'
    assert 'User-Agent' in headers


@pytest.mark.asyncio
async def test_api_client_successful_request():
    """Test API client makes successful request"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    mock_response_data = {'data': 'test response'}
    
    # Create mock response context manager
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = AsyncMock(return_value=None)
    
    with patch.object(aiohttp.ClientSession, '__init__', return_value=None):
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response):
            with patch.object(aiohttp.ClientSession, 'close', new_callable=AsyncMock):
                with patch.object(aiohttp.ClientSession, 'closed', False):
                    async with client:
                        result = await client._request('GET', '/test')
                        
                        assert result == mock_response_data
                        assert client.requests_made == 1
                        assert client.requests_failed == 0
                        assert client.last_request_time is not None


@pytest.mark.asyncio
async def test_api_client_retry_logic():
    """Test retry logic with exponential backoff"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        with patch('asyncio.sleep') as mock_sleep:
            # Create mock responses - fail twice, succeed third time
            mock_success_response = AsyncMock()
            mock_success_response.status = 200
            mock_success_response.json = AsyncMock(return_value={'data': 'ok'})
            mock_success_response.raise_for_status = Mock()
            mock_success_response.__aenter__.return_value = mock_success_response
            mock_success_response.__aexit__.return_value = None
            
            # Create mock session that fails twice
            call_count = 0
            def mock_request(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise aiohttp.ClientError("Connection failed")
                return mock_success_response
            
            mock_session = AsyncMock()
            mock_session.request = Mock(side_effect=mock_request)
            mock_session.closed = False
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            async with client:
                result = await client._request('GET', '/test')
                
                assert result == {'data': 'ok'}
                assert call_count == 3  # Should have retried twice
                assert mock_sleep.call_count == 2  # Two retries
                # Verify exponential backoff delays
                assert mock_sleep.call_args_list[0][0][0] == 0.1  # First retry: 0.1s
                assert mock_sleep.call_args_list[1][0][0] == 0.2  # Second retry: 0.2s


@pytest.mark.asyncio
async def test_api_client_final_retry_failure():
    """Test that final retry failure raises exception"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        with patch('asyncio.sleep'):
            # Create mock session that always fails
            mock_session = AsyncMock()
            mock_session.request = Mock(side_effect=aiohttp.ClientError("Connection failed"))
            mock_session.closed = False
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            async with client:
                with pytest.raises(aiohttp.ClientError):
                    await client._request('GET', '/test')
                
                assert client.requests_failed == 3  # All 3 attempts failed


@pytest.mark.asyncio
async def test_api_client_request_without_context():
    """Test that request without context manager raises error"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    with pytest.raises(RuntimeError, match="Client session not initialized"):
        await client._request('GET', '/test')


@pytest.mark.asyncio
async def test_api_client_statistics():
    """Test client statistics tracking"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    # Set some statistics
    client.requests_made = 10
    client.requests_failed = 2
    client.last_request_time = datetime(2025, 10, 11, 12, 0, 0)
    
    stats = client.get_statistics()
    
    assert stats['requests_made'] == 10
    assert stats['requests_failed'] == 2
    assert stats['success_rate'] == 0.8  # (10-2)/10
    assert '2025-10-11' in stats['last_request_time']


@pytest.mark.asyncio
async def test_api_client_graceful_shutdown():
    """Test graceful shutdown with asyncio.sleep(0)"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    with patch('aiohttp.ClientSession') as mock_session_class:
        with patch('asyncio.sleep') as mock_sleep:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session.close = AsyncMock()
            mock_session_class.return_value = mock_session
            
            async with client:
                pass
            
            # Verify graceful shutdown called asyncio.sleep(0)
            mock_session.close.assert_called_once()
            mock_sleep.assert_called_with(0)


@pytest.mark.asyncio
async def test_api_client_with_parameters():
    """Test request with query parameters"""
    client = APISportsClient('test-key', 'https://api.test.com')
    
    # Create mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'result': 'ok'})
    mock_response.raise_for_status = Mock()
    mock_response.__aenter__.return_value = mock_response
    mock_response.__aexit__.return_value = AsyncMock(return_value=None)
    
    with patch.object(aiohttp.ClientSession, '__init__', return_value=None):
        with patch.object(aiohttp.ClientSession, 'request', return_value=mock_response) as mock_request:
            with patch.object(aiohttp.ClientSession, 'close', new_callable=AsyncMock):
                with patch.object(aiohttp.ClientSession, 'closed', False):
                    async with client:
                        result = await client._request('GET', '/scores', params={'date': '2025-10-11'})
                        
                        assert result == {'result': 'ok'}
                        # Verify request was called with parameters
                        assert mock_request.called

