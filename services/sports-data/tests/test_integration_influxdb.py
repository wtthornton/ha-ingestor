"""
Integration tests for InfluxDB persistence

Simple integration tests to verify end-to-end flow.
Story 12.1 - InfluxDB Persistence Layer
"""

import pytest
from unittest.mock import Mock, patch
from httpx import AsyncClient
from src.main import app


@pytest.fixture
def mock_influxdb():
    """Mock InfluxDB for integration tests"""
    with patch('src.influxdb_writer.InfluxDBClient3') as mock:
        mock_instance = Mock()
        mock_instance.write = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_health_endpoint_includes_influxdb_status(mock_influxdb):
    """Health endpoint should include InfluxDB status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert 'influxdb' in data
        assert isinstance(data['influxdb'], dict)


@pytest.mark.asyncio
async def test_live_games_endpoint_with_influxdb(mock_influxdb):
    """Live games endpoint should work with InfluxDB enabled"""
    with patch('src.sports_api_client.SportsAPIClient.get_live_games') as mock_get_games:
        mock_get_games.return_value = [
            {
                'id': 'test-1',
                'home_team': 'Patriots',
                'away_team': 'Chiefs',
                'home_score': 21,
                'away_score': 17,
                'status': 'live',
                'start_time': '2025-10-14T13:00:00Z',
                'quarter': '3'
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/games/live?league=nfl&team_ids=ne,kc")
            
            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 1
            
            # Note: InfluxDB write happens in background task, not directly testable here


@pytest.mark.asyncio
async def test_upcoming_games_endpoint_with_influxdb(mock_influxdb):
    """Upcoming games endpoint should work with InfluxDB enabled"""
    with patch('src.sports_api_client.SportsAPIClient.get_upcoming_games') as mock_get_games:
        mock_get_games.return_value = [
            {
                'id': 'test-2',
                'home_team': 'Patriots',
                'away_team': 'Bills',
                'home_score': 0,
                'away_score': 0,
                'status': 'scheduled',
                'start_time': '2025-10-21T13:00:00Z',
                'quarter': 'Pregame'
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/games/upcoming?league=nfl&team_ids=ne")
            
            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 1


@pytest.mark.asyncio
async def test_service_continues_without_influxdb():
    """Service should work even if InfluxDB is disabled"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', False):
        with patch('src.sports_api_client.SportsAPIClient.get_live_games') as mock_get_games:
            mock_get_games.return_value = []
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/games/live?league=nfl&team_ids=ne")
                
                assert response.status_code == 200
                data = response.json()
                assert 'games' in data

