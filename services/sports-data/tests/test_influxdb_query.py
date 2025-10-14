"""
Unit tests for InfluxDB Query Module

Story 12.2 - Historical Query Endpoints
"""

import pytest
from unittest.mock import Mock, patch
from src.influxdb_query import InfluxDBQuery


@pytest.fixture
def mock_client():
    """Mock InfluxDB client"""
    return Mock()


def test_query_games_history_basic(mock_client):
    """Test basic games history query"""
    with patch('src.influxdb_query.InfluxDBClient3') as MockClient:
        MockClient.return_value = mock_client
        
        query = InfluxDBQuery("http://localhost:8086", "token", "sports_data")
        
        # Mock response
        mock_reader = Mock()
        mock_table = Mock()
        mock_df = Mock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {"game_id": "1", "home_team": "Patriots", "away_team": "Chiefs"}
        ]
        mock_table.to_pandas.return_value = mock_df
        mock_reader.read_all.return_value = mock_table
        mock_client.query.return_value = mock_reader
        
        result = query.query_games_history("nfl", team="Patriots")
        
        assert len(result) == 1
        assert result[0]["home_team"] == "Patriots"


def test_query_game_timeline(mock_client):
    """Test game timeline query"""
    with patch('src.influxdb_query.InfluxDBClient3') as MockClient:
        MockClient.return_value = mock_client
        
        query = InfluxDBQuery("http://localhost:8086", "token", "sports_data")
        
        # Mock response
        mock_reader = Mock()
        mock_table = Mock()
        mock_df = Mock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [
            {"time": "2025-10-14", "home_score": 7, "away_score": 0}
        ]
        mock_table.to_pandas.return_value = mock_df
        mock_reader.read_all.return_value = mock_table
        mock_client.query.return_value = mock_reader
        
        result = query.query_game_timeline("game123", "nfl")
        
        assert len(result) == 1
        assert result[0]["home_score"] == 7

