"""
Integration tests for Historical Endpoints

Story 12.2 - Historical Query Endpoints
"""

import pytest
from unittest.mock import Mock, patch
from httpx import AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_games_history_endpoint():
    """Test games history endpoint"""
    with patch('src.influxdb_query.InfluxDBClient3'):
        with patch('src.main.influxdb_query') as mock_query:
            mock_query.query_games_history.return_value = [
                {
                    "game_id": "1",
                    "sport": "nfl",
                    "season": "2025",
                    "home_team": "Patriots",
                    "away_team": "Chiefs",
                    "home_score": 21,
                    "away_score": 17,
                    "status": "finished",
                    "time": "2025-10-14T13:00:00"
                }
            ]
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/games/history?team=Patriots&season=2025")
                
                assert response.status_code == 200
                data = response.json()
                assert data["total"] == 1
                assert data["page"] == 1


@pytest.mark.asyncio
async def test_game_timeline_endpoint():
    """Test game timeline endpoint"""
    with patch('src.influxdb_query.InfluxDBClient3'):
        with patch('src.main.influxdb_query') as mock_query:
            mock_query.query_game_timeline.return_value = [
                {"time": "2025-10-14T13:00:00", "home_team": "Patriots", "away_team": "Chiefs", 
                 "home_score": 7, "away_score": 0, "quarter": "1", "time_remaining": "10:00"}
            ]
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/games/timeline/game123?sport=nfl")
                
                assert response.status_code == 200
                data = response.json()
                assert data["game_id"] == "game123"
                assert len(data["timeline"]) == 1


@pytest.mark.asyncio
async def test_team_schedule_endpoint():
    """Test team schedule endpoint"""
    with patch('src.influxdb_query.InfluxDBClient3'):
        with patch('src.main.influxdb_query') as mock_query:
            mock_query.query_games_history.return_value = [
                {
                    "game_id": "1",
                    "sport": "nfl",
                    "season": "2025",
                    "home_team": "Patriots",
                    "away_team": "Chiefs",
                    "home_score": 21,
                    "away_score": 17,
                    "status": "finished",
                    "time": "2025-10-14T13:00:00"
                }
            ]
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/games/schedule/Patriots?season=2025")
                
                assert response.status_code == 200
                data = response.json()
                assert data["team"] == "Patriots"
                assert data["season"] == "2025"
                assert "statistics" in data

