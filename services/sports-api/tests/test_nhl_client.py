"""
Unit tests for NHL Client
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

import aiohttp

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from nhl_client import NHLClient
from models import NHLScore, NHLStanding, NHLFixture


# Mock response data
MOCK_NHL_SCORES_RESPONSE = {
    'response': [
        {
            'game_id': '67890',
            'date': '2025-10-11T19:00:00Z',
            'home_team': 'Bruins',
            'away_team': 'Canadiens',
            'home_score': 3,
            'away_score': 2,
            'status': 'finished',
            'period': '3',
            'time_remaining': None,
            'season': 2025,
            'home_shots': 28,
            'away_shots': 22
        }
    ]
}

MOCK_NHL_STANDINGS_RESPONSE = {
    'response': [
        {
            'team': 'Bruins',
            'conference': 'Eastern',
            'division': 'Atlantic',
            'wins': 8,
            'losses': 2,
            'overtime_losses': 1,
            'points': 17,
            'games_played': 11,
            'season': 2025
        }
    ]
}

MOCK_NHL_FIXTURES_RESPONSE = {
    'response': [
        {
            'game_id': '67891',
            'date': '2025-10-13T19:00:00Z',
            'home_team': 'Bruins',
            'away_team': 'Maple Leafs',
            'season': 2025,
            'venue': 'TD Garden',
            'city': 'Boston'
        }
    ]
}


@pytest.mark.asyncio
async def test_nhl_client_initialization():
    """Test NHL client initializes with correct base URL"""
    client = NHLClient('test-api-key')
    
    assert client.api_key == 'test-api-key'
    assert client.base_url == 'https://api-sports.io/nhl'


@pytest.mark.asyncio
async def test_get_scores_live():
    """Test fetching live NHL scores"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NHL_SCORES_RESPONSE)):
        async with client:
            scores = await client.get_scores()
            
            assert len(scores) == 1
            assert isinstance(scores[0], NHLScore)
            assert scores[0].game_id == '67890'
            assert scores[0].home_team == 'Bruins'
            assert scores[0].away_team == 'Canadiens'
            assert scores[0].home_score == 3
            assert scores[0].away_score == 2
            assert scores[0].period == '3'
            assert scores[0].home_shots == 28
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/scores', params={'live': 'all'})


@pytest.mark.asyncio
async def test_get_scores_historical():
    """Test fetching historical NHL scores by date"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NHL_SCORES_RESPONSE)):
        async with client:
            scores = await client.get_scores(date='2025-10-11')
            
            assert len(scores) == 1
            assert scores[0].game_id == '67890'
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/scores', params={'date': '2025-10-11'})


@pytest.mark.asyncio
async def test_get_scores_empty_response():
    """Test get_scores handles empty response"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value={'response': []})):
        async with client:
            scores = await client.get_scores()
            
            assert scores == []


@pytest.mark.asyncio
async def test_get_scores_api_error():
    """Test get_scores handles API errors gracefully"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(side_effect=aiohttp.ClientError("API Error"))):
        async with client:
            scores = await client.get_scores()
            
            assert scores == []  # Should return empty list, not raise


@pytest.mark.asyncio
async def test_get_standings():
    """Test fetching NHL standings"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NHL_STANDINGS_RESPONSE)):
        async with client:
            standings = await client.get_standings(season=2025)
            
            assert len(standings) == 1
            assert isinstance(standings[0], NHLStanding)
            assert standings[0].team == 'Bruins'
            assert standings[0].wins == 8
            assert standings[0].losses == 2
            assert standings[0].overtime_losses == 1
            assert standings[0].points == 17
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/standings', params={'season': 2025})


@pytest.mark.asyncio
async def test_get_standings_error():
    """Test get_standings handles errors gracefully"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(side_effect=Exception("API Error"))):
        async with client:
            standings = await client.get_standings(season=2025)
            
            assert standings == []


@pytest.mark.asyncio
async def test_get_fixtures():
    """Test fetching NHL fixtures"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NHL_FIXTURES_RESPONSE)):
        async with client:
            fixtures = await client.get_fixtures(season=2025)
            
            assert len(fixtures) == 1
            assert isinstance(fixtures[0], NHLFixture)
            assert fixtures[0].game_id == '67891'
            assert fixtures[0].home_team == 'Bruins'
            assert fixtures[0].venue == 'TD Garden'
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/fixtures', params={'season': 2025})


@pytest.mark.asyncio
async def test_get_fixtures_error():
    """Test get_fixtures handles errors gracefully"""
    client = NHLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(side_effect=Exception("API Error"))):
        async with client:
            fixtures = await client.get_fixtures(season=2025)
            
            assert fixtures == []


@pytest.mark.asyncio
async def test_malformed_score_data():
    """Test handling malformed score data"""
    client = NHLClient('test-api-key')
    
    # Missing required fields
    bad_response = {
        'response': [
            {'game_id': '123'},  # Missing required fields
            {  # Good data
                'game_id': '456',
                'date': '2025-10-11T19:00:00Z',
                'home_team': 'Bruins',
                'away_team': 'Canadiens',
                'status': 'scheduled',
                'season': 2025
            }
        ]
    }
    
    with patch.object(client, '_request', new=AsyncMock(return_value=bad_response)):
        async with client:
            scores = await client.get_scores()
            
            # Should skip malformed data and return only valid scores
            assert len(scores) == 1
            assert scores[0].game_id == '456'


@pytest.mark.asyncio
async def test_nhl_client_extends_base_client():
    """Test NHL client extends APISportsClient"""
    from api_client import APISportsClient
    
    client = NHLClient('test-api-key')
    
    assert isinstance(client, APISportsClient)
    assert hasattr(client, '_request')
    assert hasattr(client, '_get_headers')


@pytest.mark.asyncio
async def test_nhl_client_shares_api_key_with_nfl():
    """Test NHL client uses same API key format as NFL"""
    client = NHLClient('shared-api-key')
    
    headers = client._get_headers()
    
    # Same authentication pattern as NFL
    assert headers['x-rapidapi-key'] == 'shared-api-key'
    assert headers['x-rapidapi-host'] == 'api-sports.io'

