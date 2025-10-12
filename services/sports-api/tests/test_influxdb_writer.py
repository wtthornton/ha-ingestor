"""
Unit tests for SportsInfluxDBWriter
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime

# Add src to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# Mock influxdb modules
sys.modules['influxdb_client_3'] = MagicMock()
mock_point = MagicMock()
mock_point.return_value = mock_point
mock_point.tag = MagicMock(return_value=mock_point)
mock_point.field = MagicMock(return_value=mock_point)
mock_point.time = MagicMock(return_value=mock_point)

sys.modules['influxdb_client_3'].Point = mock_point
sys.modules['influxdb_client_3'].InfluxDBClient3 = MagicMock
sys.modules['influxdb_client_3'].WriteOptions = MagicMock
sys.modules['influxdb_client_3'].InfluxDBError = Exception
sys.modules['influxdb_client_3'].write_client_options = MagicMock

# Now we can import
from influxdb_writer import SportsInfluxDBWriter, BatchingCallback


@pytest.mark.asyncio
async def test_writer_initialization():
    """Test InfluxDB writer initializes correctly"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org",
        batch_size=50,
        flush_interval=5000
    )
    
    assert writer.host == "http://localhost:8086"
    assert writer.token == "test-token"
    assert writer.database == "test_db"
    assert writer.batch_size == 50
    assert writer.flush_interval == 5000
    assert writer.total_points_written == 0


@pytest.mark.asyncio
async def test_writer_start():
    """Test writer start method initializes client"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    await writer.start()
    
    assert writer.client is not None


@pytest.mark.asyncio
async def test_write_nfl_score():
    """Test writing NFL score"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    # Initialize
    await writer.start()
    
    # Mock the client.write method
    writer.client.write = Mock()
    
    # Test data
    score = {
        'game_id': '12345',
        'season': 2025,
        'week': 5,
        'home_team': 'Patriots',
        'away_team': 'Chiefs',
        'status': 'finished',
        'home_score': 24,
        'away_score': 21,
        'date': '2025-10-11T18:00:00Z'
    }
    
    # Write score
    result = await writer.write_nfl_score(score)
    
    # Verify
    assert result is True
    assert writer.total_points_written == 1
    assert writer.client.write.called


@pytest.mark.asyncio
async def test_write_nhl_score():
    """Test writing NHL score"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    await writer.start()
    writer.client.write = Mock()
    
    score = {
        'game_id': '67890',
        'season': 2025,
        'home_team': 'Bruins',
        'away_team': 'Canadiens',
        'status': 'finished',
        'home_score': 3,
        'away_score': 2,
        'period': '3',
        'home_shots': 28,
        'away_shots': 22,
        'date': '2025-10-11T19:00:00Z'
    }
    
    result = await writer.write_nhl_score(score)
    
    assert result is True
    assert writer.total_points_written == 1


@pytest.mark.asyncio
async def test_write_player_stats():
    """Test writing player statistics"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    await writer.start()
    writer.client.write = Mock()
    
    stats = {
        'player_id': 'abc123',
        'player_name': 'Tom Brady',
        'team': 'Patriots',
        'position': 'QB',
        'season': 2025,
        'week': 5,
        'stats': {
            'passing_yards': 325,
            'touchdowns': 3,
            'interceptions': 1,
            'qb_rating': 98.5
        }
    }
    
    result = await writer.write_player_stats(stats, sport="nfl")
    
    assert result is True
    assert writer.total_points_written == 1


@pytest.mark.asyncio
async def test_write_injury_report():
    """Test writing injury report"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    await writer.start()
    writer.client.write = Mock()
    
    injury = {
        'player_id': 'xyz789',
        'player_name': 'Rob Gronkowski',
        'team': 'Patriots',
        'status': 'questionable',
        'injury_type': 'knee',
        'updated': '2025-10-11T12:00:00Z'
    }
    
    result = await writer.write_injury_report(injury)
    
    assert result is True
    assert writer.total_points_written == 1


@pytest.mark.asyncio
async def test_write_standings():
    """Test writing standings (batch)"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    await writer.start()
    writer.client.write = Mock()
    
    standings = [
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
        },
        {
            'team': 'Chiefs',
            'conference': 'AFC',
            'division': 'West',
            'wins': 5,
            'losses': 0,
            'ties': 0,
            'win_percentage': 1.000,
            'points_for': 145,
            'points_against': 75,
            'season': 2025
        }
    ]
    
    result = await writer.write_standings(standings, sport="nfl")
    
    assert result == 2  # Both standings written
    assert writer.total_points_written == 2


@pytest.mark.asyncio
async def test_write_error_handling():
    """Test writer handles write errors gracefully"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    await writer.start()
    
    # Mock write to raise exception
    writer.client.write = Mock(side_effect=Exception("Write failed"))
    
    score = {
        'game_id': '123',
        'season': 2025,
        'week': 5,
        'home_team': 'Team1',
        'away_team': 'Team2',
        'status': 'finished'
    }
    
    result = await writer.write_nfl_score(score)
    
    assert result is False
    assert writer.total_points_failed == 1


@pytest.mark.asyncio
async def test_get_statistics():
    """Test statistics tracking"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    # Set statistics
    writer.total_points_written = 95
    writer.total_points_failed = 5
    writer.callback.write_count = 10
    writer.callback.error_count = 1
    writer.callback.retry_count = 2
    
    stats = writer.get_statistics()
    
    assert stats['total_points_written'] == 95
    assert stats['total_points_failed'] == 5
    assert stats['success_rate'] == 0.95
    assert stats['total_errors'] == 1
    assert stats['total_retries'] == 2


@pytest.mark.asyncio
async def test_batching_callback():
    """Test batching callback handlers"""
    callback = BatchingCallback()
    
    # Test success
    callback.success("conf1", "data")
    assert callback.write_count == 1
    
    # Test error
    callback.error("conf2", "data", Exception("Error"))
    assert callback.error_count == 1
    
    # Test retry
    callback.retry("conf3", "data", Exception("Retry"))
    assert callback.retry_count == 1


@pytest.mark.asyncio
async def test_writer_without_client():
    """Test write methods fail gracefully when client not initialized"""
    writer = SportsInfluxDBWriter(
        host="http://localhost:8086",
        token="test-token",
        database="test_db",
        org="test_org"
    )
    
    # Don't call start(), so client is None
    score = {'game_id': '123', 'season': 2025, 'week': 1, 'home_team': 'A', 'away_team': 'B', 'status': 'scheduled'}
    
    result = await writer.write_nfl_score(score)
    assert result is False

