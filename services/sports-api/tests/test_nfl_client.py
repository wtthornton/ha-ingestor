"""
Unit tests for NFL Client
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

import aiohttp

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from nfl_client import NFLClient
from models import NFLScore, NFLStanding, NFLPlayer, NFLInjury, NFLFixture


# Mock response data
MOCK_NFL_SCORES_RESPONSE = {
    'response': [
        {
            'game_id': '12345',
            'date': '2025-10-11T18:00:00Z',
            'home_team': 'Patriots',
            'away_team': 'Chiefs',
            'home_score': 24,
            'away_score': 21,
            'status': 'finished',
            'quarter': None,
            'time_remaining': None,
            'season': 2025,
            'week': 5
        }
    ]
}

MOCK_NFL_STANDINGS_RESPONSE = {
    'response': [
        {
            'team': 'Patriots',
            'conference': 'AFC',
            'division': 'East',
            'wins': 4,
            'losses': 1,
            'ties': 0,
            'win_percentage': 0.800,
            'points_for': 125,
            'points_against': 98,
            'season': 2025
        }
    ]
}

MOCK_NFL_FIXTURES_RESPONSE = {
    'response': [
        {
            'game_id': '12346',
            'date': '2025-10-13T13:00:00Z',
            'home_team': 'Patriots',
            'away_team': 'Bills',
            'season': 2025,
            'week': 6,
            'venue': 'Gillette Stadium',
            'city': 'Foxborough'
        }
    ]
}

MOCK_NFL_PLAYERS_RESPONSE = {
    'response': [
        {
            'player_id': 'abc123',
            'name': 'Tom Brady',
            'position': 'QB',
            'team': 'Patriots',
            'stats': {
                'passing_yards': 325,
                'touchdowns': 3,
                'interceptions': 1
            }
        }
    ]
}

MOCK_NFL_INJURIES_RESPONSE = {
    'response': [
        {
            'player_id': 'xyz789',
            'player_name': 'Rob Gronkowski',
            'team': 'Patriots',
            'injury_type': 'knee',
            'status': 'questionable',
            'updated': '2025-10-11T12:00:00Z'
        }
    ]
}


@pytest.mark.asyncio
async def test_nfl_client_initialization():
    """Test NFL client initializes with correct base URL"""
    client = NFLClient('test-api-key')
    
    assert client.api_key == 'test-api-key'
    assert client.base_url == 'https://api-sports.io/nfl'


@pytest.mark.asyncio
async def test_get_scores_live():
    """Test fetching live NFL scores"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_SCORES_RESPONSE)):
        async with client:
            scores = await client.get_scores()
            
            assert len(scores) == 1
            assert isinstance(scores[0], NFLScore)
            assert scores[0].game_id == '12345'
            assert scores[0].home_team == 'Patriots'
            assert scores[0].away_team == 'Chiefs'
            assert scores[0].home_score == 24
            assert scores[0].away_score == 21
            assert scores[0].status == 'finished'
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/scores', params={'live': 'all'})


@pytest.mark.asyncio
async def test_get_scores_historical():
    """Test fetching historical NFL scores by date"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_SCORES_RESPONSE)):
        async with client:
            scores = await client.get_scores(date='2025-10-11')
            
            assert len(scores) == 1
            assert scores[0].game_id == '12345'
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/scores', params={'date': '2025-10-11'})


@pytest.mark.asyncio
async def test_get_scores_empty_response():
    """Test get_scores handles empty response"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value={'response': []})):
        async with client:
            scores = await client.get_scores()
            
            assert scores == []


@pytest.mark.asyncio
async def test_get_scores_api_error():
    """Test get_scores handles API errors gracefully"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(side_effect=aiohttp.ClientError("API Error"))):
        async with client:
            scores = await client.get_scores()
            
            assert scores == []  # Should return empty list, not raise


@pytest.mark.asyncio
async def test_get_standings():
    """Test fetching NFL standings"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_STANDINGS_RESPONSE)):
        async with client:
            standings = await client.get_standings(season=2025)
            
            assert len(standings) == 1
            assert isinstance(standings[0], NFLStanding)
            assert standings[0].team == 'Patriots'
            assert standings[0].wins == 4
            assert standings[0].losses == 1
            assert standings[0].win_percentage == 0.800
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/standings', params={'season': 2025})


@pytest.mark.asyncio
async def test_get_standings_error():
    """Test get_standings handles errors gracefully"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(side_effect=Exception("API Error"))):
        async with client:
            standings = await client.get_standings(season=2025)
            
            assert standings == []


@pytest.mark.asyncio
async def test_get_fixtures_full_season():
    """Test fetching full season fixtures"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_FIXTURES_RESPONSE)):
        async with client:
            fixtures = await client.get_fixtures(season=2025)
            
            assert len(fixtures) == 1
            assert isinstance(fixtures[0], NFLFixture)
            assert fixtures[0].game_id == '12346'
            assert fixtures[0].home_team == 'Patriots'
            assert fixtures[0].venue == 'Gillette Stadium'
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/fixtures', params={'season': 2025})


@pytest.mark.asyncio
async def test_get_fixtures_specific_week():
    """Test fetching fixtures for specific week"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_FIXTURES_RESPONSE)):
        async with client:
            fixtures = await client.get_fixtures(season=2025, week=6)
            
            assert len(fixtures) == 1
            
            # Verify request parameters include week
            client._request.assert_called_once_with('GET', '/fixtures', params={'season': 2025, 'week': 6})


@pytest.mark.asyncio
async def test_get_players_by_team():
    """Test fetching players by team"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_PLAYERS_RESPONSE)):
        async with client:
            players = await client.get_players(team='Patriots')
            
            assert len(players) == 1
            assert isinstance(players[0], NFLPlayer)
            assert players[0].player_id == 'abc123'
            assert players[0].name == 'Tom Brady'
            assert players[0].position == 'QB'
            assert players[0].stats['passing_yards'] == 325
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/players', params={'team': 'Patriots'})


@pytest.mark.asyncio
async def test_get_players_by_id():
    """Test fetching specific player"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_PLAYERS_RESPONSE)):
        async with client:
            players = await client.get_players(player_id='abc123')
            
            assert len(players) == 1
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/players', params={'id': 'abc123'})


@pytest.mark.asyncio
async def test_get_injuries_all_teams():
    """Test fetching injuries for all teams"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_INJURIES_RESPONSE)):
        async with client:
            injuries = await client.get_injuries()
            
            assert len(injuries) == 1
            assert isinstance(injuries[0], NFLInjury)
            assert injuries[0].player_name == 'Rob Gronkowski'
            assert injuries[0].status == 'questionable'
            assert injuries[0].injury_type == 'knee'
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/injuries', params={})


@pytest.mark.asyncio
async def test_get_injuries_by_team():
    """Test fetching injuries for specific team"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(return_value=MOCK_NFL_INJURIES_RESPONSE)):
        async with client:
            injuries = await client.get_injuries(team='Patriots')
            
            assert len(injuries) == 1
            
            # Verify request parameters
            client._request.assert_called_once_with('GET', '/injuries', params={'team': 'Patriots'})


@pytest.mark.asyncio
async def test_get_injuries_error():
    """Test get_injuries handles errors gracefully"""
    client = NFLClient('test-api-key')
    
    with patch.object(client, '_request', new=AsyncMock(side_effect=Exception("API Error"))):
        async with client:
            injuries = await client.get_injuries()
            
            assert injuries == []


@pytest.mark.asyncio
async def test_malformed_score_data():
    """Test handling malformed score data"""
    client = NFLClient('test-api-key')
    
    # Missing required fields
    bad_response = {
        'response': [
            {'game_id': '123'},  # Missing required fields
            {  # Good data
                'game_id': '456',
                'date': '2025-10-11T18:00:00Z',
                'home_team': 'Patriots',
                'away_team': 'Chiefs',
                'status': 'scheduled',
                'season': 2025,
                'week': 5
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
async def test_nfl_client_extends_base_client():
    """Test NFL client extends APISportsClient"""
    from api_client import APISportsClient
    
    client = NFLClient('test-api-key')
    
    assert isinstance(client, APISportsClient)
    assert hasattr(client, '_request')
    assert hasattr(client, '_get_headers')


@pytest.mark.asyncio
async def test_nfl_client_uses_base_client_features():
    """Test NFL client uses base client retry and error handling"""
    client = NFLClient('test-api-key')
    
    # Should have access to base client statistics
    assert hasattr(client, 'get_statistics')
    assert hasattr(client, 'requests_made')
    assert hasattr(client, 'requests_failed')

