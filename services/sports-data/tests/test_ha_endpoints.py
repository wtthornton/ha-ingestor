"""
Integration tests for HA Automation Endpoints

Story 12.3 - Adaptive Event Monitor + Webhooks
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch
from src.main import app


@pytest.mark.asyncio
async def test_game_status_endpoint_playing():
    """Test game status when team is playing"""
    # Mock cache to return live game
    with patch('src.main.cache') as mock_cache:
        mock_cache.get.return_value = [
            {
                'id': 'game1',
                'status': 'live',
                'home_team': {'abbreviation': 'ne'},
                'away_team': {'abbreviation': 'kc'},
                'score': {'home': 14, 'away': 10},
                'start_time': '2025-10-14T13:00:00Z'
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/ha/game-status/ne?sport=nfl")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'playing'
            assert data['opponent'] == 'kc'


@pytest.mark.asyncio
async def test_game_status_endpoint_none():
    """Test game status when no games"""
    with patch('src.main.cache') as mock_cache:
        mock_cache.get.return_value = []
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/ha/game-status/ne?sport=nfl")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'none'


@pytest.mark.asyncio
async def test_game_context_endpoint():
    """Test game context endpoint"""
    with patch('src.main.cache') as mock_cache:
        mock_cache.get.return_value = [
            {
                'id': 'game1',
                'status': 'live',
                'home_team': {'abbreviation': 'ne'},
                'away_team': {'abbreviation': 'kc'}
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/ha/game-context/ne?sport=nfl")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'playing'
            assert data['current_game'] is not None


@pytest.mark.asyncio
async def test_webhook_registration():
    """Test webhook registration endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/webhooks/register",
            json={
                "url": "http://homeassistant.local:8123/api/webhook/test",
                "events": ["game_started", "score_changed"],
                "secret": "test-secret-16-chars-min",
                "team": "ne"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert 'webhook_id' in data
        assert data['team'] == 'ne'

