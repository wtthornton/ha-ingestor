"""
Tests for InfluxDB Client Wrapper
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.influxdb_client import InfluxDBClientWrapper


class TestInfluxDBClientWrapper:
    """Test cases for InfluxDBClientWrapper class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = InfluxDBClientWrapper(
            url="http://test-influxdb:8086",
            token="test-token",
            org="test-org",
            bucket="test-bucket"
        )
    
    def test_initialization(self):
        """Test client initialization"""
        assert self.client.url == "http://test-influxdb:8086"
        assert self.client.token == "test-token"
        assert self.client.org == "test-org"
        assert self.client.bucket == "test-bucket"
        assert self.client.client is None
        assert self.client.write_api is None
        assert self.client.query_api is None
        assert self.client.points_written == 0
        assert self.client.write_errors == 0
        assert self.client.last_write_time is None
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful connection to InfluxDB"""
        with patch('src.influxdb_client.InfluxDBClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock buckets API
            mock_buckets_api = Mock()
            mock_bucket = Mock()
            mock_bucket.name = "test-bucket"
            mock_buckets_api.find_buckets.return_value = [mock_bucket]
            mock_client.buckets_api.return_value = mock_buckets_api
            
            result = await self.client.connect()
            
            assert result is True
            assert self.client.client is not None
            assert self.client.write_api is not None
            assert self.client.query_api is not None
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure to InfluxDB"""
        with patch('src.influxdb_client.InfluxDBClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")
            
            result = await self.client.connect()
            
            assert result is False
            assert self.client.client is None
    
    @pytest.mark.asyncio
    async def test_write_event_success(self):
        """Test successful event write"""
        # Mock connected client
        self.client.client = Mock()
        self.client.write_api = Mock()
        
        event_data = {
            "event_type": "state_changed",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "new_state": {
                "state": True,
                "entity_id": "light.living_room",
                "attributes": {"brightness": 255}
            },
            "entity_metadata": {
                "domain": "light",
                "device_class": "light"
            }
        }
        
        result = await self.client.write_event(event_data)
        
        assert result is True
        assert self.client.points_written == 1
        assert self.client.last_write_time is not None
        self.client.write_api.write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_write_event_not_connected(self):
        """Test event write when not connected"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        result = await self.client.write_event(event_data)
        
        assert result is False
        assert self.client.points_written == 0
    
    @pytest.mark.asyncio
    async def test_write_event_invalid_data(self):
        """Test event write with invalid data"""
        # Mock connected client
        self.client.client = Mock()
        self.client.write_api = Mock()
        
        # Invalid event data (missing event_type)
        event_data = {
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        result = await self.client.write_event(event_data)
        
        assert result is False
        assert self.client.points_written == 0
    
    @pytest.mark.asyncio
    async def test_write_event_exception(self):
        """Test event write with exception"""
        # Mock connected client
        self.client.client = Mock()
        self.client.write_api = Mock()
        self.client.write_api.write.side_effect = Exception("Write failed")
        
        event_data = {
            "event_type": "state_changed",
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        result = await self.client.write_event(event_data)
        
        assert result is False
        assert self.client.write_errors == 1
    
    @pytest.mark.asyncio
    async def test_write_events_batch_success(self):
        """Test successful batch event write"""
        # Mock connected client
        self.client.client = Mock()
        self.client.write_api = Mock()
        
        events = [
            {
                "event_type": "state_changed",
                "new_state": {"state": "on", "entity_id": "light.living_room"}
            },
            {
                "event_type": "state_changed",
                "new_state": {"state": "off", "entity_id": "light.kitchen"}
            }
        ]
        
        result = await self.client.write_events_batch(events)
        
        assert result == 2
        assert self.client.points_written == 2
        assert self.client.last_write_time is not None
        self.client.write_api.write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_write_events_batch_not_connected(self):
        """Test batch event write when not connected"""
        events = [
            {
                "event_type": "state_changed",
                "new_state": {"state": "on", "entity_id": "light.living_room"}
            }
        ]
        
        result = await self.client.write_events_batch(events)
        
        assert result == 0
        assert self.client.points_written == 0
    
    @pytest.mark.asyncio
    async def test_write_events_batch_exception(self):
        """Test batch event write with exception"""
        # Mock connected client
        self.client.client = Mock()
        self.client.write_api = Mock()
        self.client.write_api.write.side_effect = Exception("Batch write failed")
        
        events = [
            {
                "event_type": "state_changed",
                "new_state": {"state": "on", "entity_id": "light.living_room"}
            }
        ]
        
        result = await self.client.write_events_batch(events)
        
        assert result == 0
        assert self.client.write_errors == 1
    
    @pytest.mark.asyncio
    async def test_query_events_success(self):
        """Test successful event query"""
        # Mock connected client
        self.client.client = Mock()
        self.client.query_api = Mock()
        
        # Mock query result
        mock_record = Mock()
        mock_record.get_time.return_value = Mock()
        mock_record.get_time.return_value.isoformat.return_value = "2024-01-01T12:00:00+00:00"
        mock_record.get_measurement.return_value = "home_assistant_events"
        mock_record.values = {"state": "on"}
        mock_record.tags = {"entity_id": "light.living_room"}
        
        mock_table = Mock()
        mock_table.records = [mock_record]
        
        self.client.query_api.query.return_value = [mock_table]
        
        result = await self.client.query_events("SELECT * FROM home_assistant_events")
        
        assert len(result) == 1
        assert result[0]["time"] == "2024-01-01T12:00:00+00:00"
        assert result[0]["measurement"] == "home_assistant_events"
        assert result[0]["fields"]["state"] == "on"
        assert result[0]["tags"]["entity_id"] == "light.living_room"
    
    @pytest.mark.asyncio
    async def test_query_events_not_connected(self):
        """Test event query when not connected"""
        result = await self.client.query_events("SELECT * FROM home_assistant_events")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_query_events_exception(self):
        """Test event query with exception"""
        # Mock connected client
        self.client.client = Mock()
        self.client.query_api = Mock()
        self.client.query_api.query.side_effect = Exception("Query failed")
        
        result = await self.client.query_events("SELECT * FROM home_assistant_events")
        
        assert result == []
    
    def test_create_point_from_event_state_changed(self):
        """Test creating InfluxDB point from state_changed event"""
        event_data = {
            "event_type": "state_changed",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "new_state": {
                "state": True,
                "entity_id": "light.living_room",
                "attributes": {
                    "brightness": 255,
                    "friendly_name": "Living Room Light"
                }
            },
            "entity_metadata": {
                "domain": "light",
                "device_class": "light",
                "friendly_name": "Living Room Light",
                "unit_of_measurement": None,
                "icon": "mdi:lightbulb"
            }
        }
        
        point = self.client._create_point_from_event(event_data)
        
        assert point is not None
        # Note: We can't easily test the Point object contents without mocking
        # the InfluxDB client library, but we can test that it's created
    
    def test_create_point_from_event_invalid(self):
        """Test creating InfluxDB point from invalid event"""
        # Missing event_type
        event_data = {
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        point = self.client._create_point_from_event(event_data)
        
        assert point is None
    
    def test_is_valid_field_value(self):
        """Test field value validation"""
        # Valid values
        assert self.client._is_valid_field_value("string") is True
        assert self.client._is_valid_field_value(123) is True
        assert self.client._is_valid_field_value(123.45) is True
        assert self.client._is_valid_field_value(True) is True
        assert self.client._is_valid_field_value(None) is True
        
        # Invalid values (complex objects)
        assert self.client._is_valid_field_value({"key": "value"}) is False
        assert self.client._is_valid_field_value([1, 2, 3]) is False
    
    def test_get_statistics(self):
        """Test getting client statistics"""
        # Set up some data
        self.client.points_written = 10
        self.client.write_errors = 2
        self.client.client = Mock()  # Simulate connected
        
        stats = self.client.get_statistics()
        
        assert stats["points_written"] == 10
        assert stats["write_errors"] == 2
        assert abs(stats["success_rate"] - 83.33) < 0.01  # 10/(10+2)*100
        assert stats["connected"] is True
        assert stats["bucket"] == "test-bucket"
        assert stats["org"] == "test-org"
    
    def test_get_statistics_not_connected(self):
        """Test getting statistics when not connected"""
        stats = self.client.get_statistics()
        
        assert stats["connected"] is False
        assert stats["points_written"] == 0
        assert stats["write_errors"] == 0
    
    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing client connection"""
        # Mock connected client
        mock_client = Mock()
        self.client.client = mock_client
        
        await self.client.close()
        
        mock_client.close.assert_called_once()
        assert self.client.client is None
        assert self.client.write_api is None
        assert self.client.query_api is None
    
    @pytest.mark.asyncio
    async def test_close_exception(self):
        """Test closing client with exception"""
        # Mock connected client
        self.client.client = Mock()
        self.client.client.close.side_effect = Exception("Close failed")
        
        # Should not raise exception
        await self.client.close()
        
        # Client should still be None after exception
        assert self.client.client is None
