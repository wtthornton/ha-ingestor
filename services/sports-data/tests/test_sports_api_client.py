"""
Tests for Sports API Client

Following Context7 KB pytest patterns with mocking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.sports_api_client import SportsAPIClient
from src.cache_service import CacheService
from src.models import Game, Team


@pytest.fixture
def mock_cache():
    """Fixture for mock cache service"""
    cache = MagicMock(spec=CacheService)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.is_connected = MagicMock(return_value=True)
    return cache


@pytest.fixture
def api_client(mock_cache):
    """Fixture for API client with mocked cache"""
    return SportsAPIClient(cache=mock_cache)


@pytest.mark.asyncio
async def test_get_live_games_no_teams_returns_empty(api_client):
    """Test that no teams selected returns empty list"""
    games = await api_client.get_live_games(team_ids=[])
    assert games == []


@pytest.mark.asyncio
async def test_get_live_games_returns_from_cache(mock_cache, api_client):
    """Test cache hit returns cached data"""
    # Setup cache to return data
    cached_games = [MagicMock(spec=Game)]
    mock_cache.get = AsyncMock(return_value=cached_games)
    
    games = await api_client.get_live_games(team_ids=['sf'])
    
    assert games == cached_games
    mock_cache.get.assert_called_once()


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_get_live_games_fetches_from_api(mock_get, api_client, mock_cache):
    """Test API fetch when cache miss"""
    # Mock API response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'events': []})
    mock_get.return_value.__aenter__.return_value = mock_response
    
    games = await api_client.get_live_games(league='NFL', team_ids=['sf'])
    
    # Should have called cache.set to store results
    mock_cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_game_has_selected_team(api_client):
    """Test team filtering logic"""
    game = Game(
        id='1',
        league='NFL',
        status='live',
        start_time='2025-10-12T20:00:00Z',
        home_team=Team(id='sf', name='49ers', abbreviation='SF', logo='', colors={}),
        away_team=Team(id='sea', name='Seahawks', abbreviation='SEA', logo='', colors={}),
        score={'home': 24, 'away': 17},
        period={'current': 3, 'total': 4}
    )
    
    # Should match if home team is selected
    assert api_client._game_has_selected_team(game, ['sf']) is True
    
    # Should match if away team is selected
    assert api_client._game_has_selected_team(game, ['sea']) is True
    
    # Should not match if different team
    assert api_client._game_has_selected_team(game, ['dal']) is False
    
    # Should not match if no teams
    assert api_client._game_has_selected_team(game, []) is False


@pytest.mark.asyncio
async def test_map_status_conversion(api_client):
    """Test ESPN status mapping"""
    assert api_client._map_status('pre') == 'scheduled'
    assert api_client._map_status('in') == 'live'
    assert api_client._map_status('post') == 'final'
    assert api_client._map_status('unknown') == 'scheduled'  # Default


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_fetch_nfl_scoreboard_success(mock_get, api_client):
    """Test successful NFL scoreboard fetch"""
    # Mock ESPN API response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        'events': [{
            'id': '401547417',
            'date': '2025-10-12T20:00:00Z',
            'competitions': [{
                'status': {
                    'type': {'state': 'in'},
                    'period': 3,
                    'displayClock': '12:45'
                },
                'competitors': [
                    {
                        'id': '25',
                        'homeAway': 'home',
                        'team': {
                            'id': '25',
                            'displayName': 'San Francisco 49ers',
                            'abbreviation': 'SF',
                            'color': 'AA0000',
                            'alternateColor': 'B3995D'
                        },
                        'score': '24',
                        'records': [{'wins': 5, 'losses': 2}]
                    },
                    {
                        'id': '26',
                        'homeAway': 'away',
                        'team': {
                            'id': '26',
                            'displayName': 'Seattle Seahawks',
                            'abbreviation': 'SEA',
                            'color': '002244',
                            'alternateColor': '69BE28'
                        },
                        'score': '17',
                        'records': [{'wins': 4, 'losses': 3}]
                    }
                ]
            }]
        }]
    })
    mock_get.return_value.__aenter__.return_value = mock_response
    
    games = await api_client._fetch_nfl_scoreboard()
    
    assert len(games) == 1
    assert games[0].league == 'NFL'
    assert games[0].status == 'live'
    assert games[0].home_team.id == 'sf'
    assert games[0].away_team.id == 'sea'
    assert games[0].score['home'] == 24
    assert games[0].score['away'] == 17


@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_fetch_handles_api_error(mock_get, api_client):
    """Test error handling for API failures"""
    # Mock API error
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_get.return_value.__aenter__.return_value = mock_response
    
    games = await api_client._fetch_nfl_scoreboard()
    
    # Should return empty list on error
    assert games == []


@pytest.mark.asyncio
async def test_test_connection_success(api_client):
    """Test successful API connection check"""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        result = await api_client.test_connection()
        assert result is True


@pytest.mark.asyncio
async def test_test_connection_failure(api_client):
    """Test failed API connection check"""
    with patch('aiohttp.ClientSession.get', side_effect=Exception('Network error')):
        result = await api_client.test_connection()
        assert result is False

