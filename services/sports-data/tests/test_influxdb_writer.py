"""
Unit tests for InfluxDB Writer

Simple tests for InfluxDB writer functionality.
Story 12.1 - InfluxDB Persistence Layer
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.influxdb_writer import InfluxDBWriter, create_influxdb_writer_from_env
from src.circuit_breaker import CircuitBreaker


@pytest.fixture
def mock_influxdb_client():
    """Mock InfluxDB client"""
    with patch('src.influxdb_writer.InfluxDBClient3') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def circuit_breaker():
    """Create circuit breaker for tests"""
    return CircuitBreaker(failure_threshold=3, timeout_seconds=60)


def test_influxdb_writer_disabled_without_client(circuit_breaker):
    """Writer should be disabled if client not available"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', False):
        writer = InfluxDBWriter(
            url="http://localhost:8086",
            token="test-token",
            database="test-db",
            circuit_breaker=circuit_breaker
        )
        assert not writer.enabled


def test_influxdb_writer_initialization(mock_influxdb_client, circuit_breaker):
    """Writer should initialize correctly with valid config"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', True):
        writer = InfluxDBWriter(
            url="http://localhost:8086",
            token="test-token",
            database="test-db",
            circuit_breaker=circuit_breaker
        )
        assert writer.enabled
        assert writer.circuit_breaker == circuit_breaker


@pytest.mark.asyncio
async def test_write_games_success(mock_influxdb_client, circuit_breaker):
    """Writer should successfully write games"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', True):
        writer = InfluxDBWriter(
            url="http://localhost:8086",
            token="test-token",
            database="test-db",
            circuit_breaker=circuit_breaker
        )
        
        games = [
            {'id': '1', 'home_team': 'Patriots', 'away_team': 'Chiefs', 
             'home_score': 21, 'away_score': 17, 'status': 'live'}
        ]
        
        result = await writer.write_games(games, 'nfl')
        
        assert result is True
        assert mock_influxdb_client.write.called
        assert writer.writes_success == 1


@pytest.mark.asyncio
async def test_write_games_respects_circuit_breaker(mock_influxdb_client, circuit_breaker):
    """Writer should not write when circuit is open"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', True):
        writer = InfluxDBWriter(
            url="http://localhost:8086",
            token="test-token",
            database="test-db",
            circuit_breaker=circuit_breaker
        )
        
        # Open the circuit
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        
        games = [{'id': '1', 'home_team': 'Patriots', 'away_team': 'Chiefs'}]
        result = await writer.write_games(games, 'nfl')
        
        assert result is False
        assert not mock_influxdb_client.write.called


@pytest.mark.asyncio
async def test_write_games_handles_errors(mock_influxdb_client, circuit_breaker):
    """Writer should handle write errors gracefully"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', True):
        writer = InfluxDBWriter(
            url="http://localhost:8086",
            token="test-token",
            database="test-db",
            circuit_breaker=circuit_breaker
        )
        
        # Make write fail
        mock_influxdb_client.write.side_effect = Exception("Write failed")
        
        games = [{'id': '1', 'home_team': 'Patriots', 'away_team': 'Chiefs',
                 'home_score': 0, 'away_score': 0, 'status': 'scheduled'}]
        result = await writer.write_games(games, 'nfl')
        
        assert result is False
        assert writer.writes_failed == 1
        assert writer.last_error == "Write failed"


def test_get_stats(mock_influxdb_client, circuit_breaker):
    """Writer should return stats correctly"""
    with patch('src.influxdb_writer.INFLUXDB_AVAILABLE', True):
        writer = InfluxDBWriter(
            url="http://localhost:8086",
            token="test-token",
            database="test-db",
            circuit_breaker=circuit_breaker
        )
        
        stats = writer.get_stats()
        
        assert 'enabled' in stats
        assert 'writes_success' in stats
        assert 'writes_failed' in stats
        assert 'circuit_breaker' in stats
        assert stats['enabled'] is True


def test_create_influxdb_writer_from_env_disabled():
    """Should return None when disabled"""
    with patch.dict('os.environ', {'INFLUXDB_ENABLED': 'false'}):
        writer = create_influxdb_writer_from_env()
        assert writer is None


def test_create_influxdb_writer_from_env_no_token():
    """Should return None when token missing"""
    with patch.dict('os.environ', {'INFLUXDB_ENABLED': 'true', 'INFLUXDB_TOKEN': ''}):
        writer = create_influxdb_writer_from_env()
        assert writer is None

