"""
Unit tests for Event Detector

Story 12.3 - Adaptive Event Monitor + Webhooks
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.event_detector import GameEventDetector


@pytest.fixture
def mock_sports_client():
    """Mock sports API client"""
    client = Mock()
    client.get_live_games = AsyncMock(return_value=[])
    return client


@pytest.fixture
def mock_webhook_manager():
    """Mock webhook manager"""
    manager = Mock()
    manager.send_event = AsyncMock()
    return manager


@pytest.fixture
def event_detector(mock_sports_client, mock_webhook_manager):
    """Create event detector"""
    return GameEventDetector(
        sports_client=mock_sports_client,
        webhook_manager=mock_webhook_manager,
        check_interval=1  # Fast for testing
    )


@pytest.mark.asyncio
async def test_event_detector_starts_and_stops(event_detector):
    """Test detector can start and stop"""
    await event_detector.start()
    assert event_detector.is_running
    
    await event_detector.stop()
    assert not event_detector.is_running


@pytest.mark.asyncio
async def test_detect_game_started(event_detector, mock_sports_client, mock_webhook_manager):
    """Test game started event detection"""
    # First check - game is scheduled
    mock_sports_client.get_live_games.return_value = [
        {
            'id': 'game1',
            'status': 'scheduled',
            'home_team': {'abbreviation': 'sf'},
            'away_team': {'abbreviation': 'dal'},
            'score': {'home': 0, 'away': 0}
        }
    ]
    
    await event_detector._check_for_events()
    
    # Second check - game is now live
    mock_sports_client.get_live_games.return_value = [
        {
            'id': 'game1',
            'status': 'live',
            'home_team': {'abbreviation': 'sf'},
            'away_team': {'abbreviation': 'dal'},
            'score': {'home': 0, 'away': 0}
        }
    ]
    
    await event_detector._check_for_events()
    
    # Should have triggered game_started event
    mock_webhook_manager.send_event.assert_called()
    call_args = mock_webhook_manager.send_event.call_args
    assert call_args[0][0] == 'game_started'


@pytest.mark.asyncio
async def test_detect_score_changed(event_detector, mock_sports_client, mock_webhook_manager):
    """Test score changed event detection"""
    # First check - game live, score 0-0
    game_before = {
        'id': 'game1',
        'status': 'live',
        'home_team': {'abbreviation': 'sf'},
        'away_team': {'abbreviation': 'dal'},
        'score': {'home': 0, 'away': 0}
    }
    event_detector.previous_games['game1'] = game_before
    
    # Second check - score changed to 7-0
    mock_sports_client.get_live_games.return_value = [
        {
            'id': 'game1',
            'status': 'live',
            'home_team': {'abbreviation': 'sf'},
            'away_team': {'abbreviation': 'dal'},
            'score': {'home': 7, 'away': 0}
        }
    ]
    
    await event_detector._check_for_events()
    
    # Should have triggered score_changed event
    mock_webhook_manager.send_event.assert_called()
    call_args = mock_webhook_manager.send_event.call_args
    assert call_args[0][0] == 'score_changed'

