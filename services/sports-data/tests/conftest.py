"""
Shared pytest fixtures for Sports Data service tests

Following Context7 KB best practices from /pytest-dev/pytest
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from datetime import datetime


# ✅ Context7 Best Practice: Shared async client
@pytest.fixture
async def client():
    """Async HTTP client for Sports Data API"""
    from src.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ✅ Context7 Best Practice: Mock cache fixture
@pytest.fixture
def mock_cache():
    """
    Mock cache service for testing without Redis dependency
    
    Automatically cleaned up after each test.
    """
    with patch('src.main.cache') as mock:
        # Configure mock to return empty cache by default
        mock.get.return_value = None
        mock.set.return_value = True
        yield mock


# ✅ Context7 Best Practice: Mock ESPN API client
@pytest.fixture
def mock_espn_api():
    """Mock ESPN API to avoid external API calls in tests"""
    with patch('src.sports_api_client.ESPNClient') as mock:
        mock_instance = AsyncMock()
        mock_instance.get_nfl_games.return_value = []
        mock_instance.get_nhl_games.return_value = []
        mock.return_value = mock_instance
        yield mock


# ✅ Context7 Best Practice: Mock InfluxDB
@pytest.fixture
def mock_influxdb():
    """Mock InfluxDB for testing"""
    with patch('src.influxdb_writer.InfluxDBWriter') as mock:
        mock_instance = AsyncMock()
        mock_instance.write.return_value = True
        mock.return_value = mock_instance
        yield mock


# ✅ Context7 Best Practice: Sample game data fixtures
@pytest.fixture
def sample_nfl_game():
    """Sample NFL game data for testing"""
    return {
        'id': 'game1',
        'status': 'live',
        'home_team': {'abbreviation': 'ne', 'score': 14},
        'away_team': {'abbreviation': 'kc', 'score': 10},
        'start_time': '2025-10-14T13:00:00Z',
        'quarter': 2,
        'clock': '8:45'
    }


@pytest.fixture
def sample_nhl_game():
    """Sample NHL game data for testing"""
    return {
        'id': 'game2',
        'status': 'live',
        'home_team': {'abbreviation': 'bos', 'score': 2},
        'away_team': {'abbreviation': 'wsh', 'score': 1},
        'start_time': '2025-10-14T19:00:00Z',
        'period': 2,
        'clock': '12:30'
    }


@pytest.fixture
def sample_webhook_data():
    """Sample webhook registration data"""
    return {
        'url': 'http://homeassistant.local:8123/api/webhook/test',
        'events': ['game_started', 'score_changed', 'game_ended'],
        'secret': 'test-secret-16-chars-min',
        'team': 'ne',
        'sport': 'nfl'
    }


# ✅ Context7 Best Practice: Parametrized test data
@pytest.fixture(params=[
    ('nfl', 'ne'),
    ('nfl', 'dal'),
    ('nhl', 'bos'),
    ('nhl', 'wsh'),
])
def team_params(request):
    """Parametrized sport and team combinations"""
    sport, team = request.param
    return {'sport': sport, 'team': team}


# ✅ Context7 Best Practice: SQLite webhook database fixture
@pytest.fixture
async def test_webhook_db():
    """Test webhook database with automatic cleanup"""
    from src.webhook_manager import WebhookManager
    import aiosqlite
    
    # Use in-memory SQLite for tests
    manager = WebhookManager(db_path=':memory:')
    await manager.initialize()
    yield manager
    await manager.close()


# ✅ Context7 Best Practice: Test markers
def pytest_configure(config):
    """Register custom pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "webhook: Webhook tests")
    config.addinivalue_line("markers", "nfl: NFL-specific tests")
    config.addinivalue_line("markers", "nhl: NHL-specific tests")

