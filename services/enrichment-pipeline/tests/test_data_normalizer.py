"""
Tests for Data Normalizer
"""

import pytest
from datetime import datetime, timezone
from src.data_normalizer import DataNormalizer


class TestDataNormalizer:
    """Test cases for DataNormalizer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.normalizer = DataNormalizer()
    
    def test_initialization(self):
        """Test normalizer initialization"""
        assert self.normalizer.normalized_events == 0
        assert self.normalizer.normalization_errors == 0
        assert self.normalizer.last_normalized_time is None
    
    def test_normalize_timestamp_iso_utc(self):
        """Test timestamp normalization with ISO UTC format"""
        event_data = {
            "event_type": "state_changed",
            "timestamp": "2024-01-01T12:00:00Z",
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["timestamp"].endswith("+00:00")
        assert "2024-01-01T12:00:00" in normalized["timestamp"]
    
    def test_normalize_timestamp_with_timezone(self):
        """Test timestamp normalization with timezone"""
        event_data = {
            "event_type": "state_changed",
            "timestamp": "2024-01-01T12:00:00+05:00",
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["timestamp"].endswith("+00:00")
        # Should be converted to UTC (12:00 +05:00 = 07:00 UTC)
        assert "2024-01-01T07:00:00" in normalized["timestamp"]
    
    def test_normalize_timestamp_no_timezone(self):
        """Test timestamp normalization without timezone (assume UTC)"""
        event_data = {
            "event_type": "state_changed",
            "timestamp": "2024-01-01T12:00:00",
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["timestamp"].endswith("+00:00")
        # The timestamp should be converted to UTC, so we just check it ends with +00:00
        assert "2024-01-01" in normalized["timestamp"]
    
    def test_normalize_state_values_boolean(self):
        """Test state value normalization for boolean values"""
        test_cases = [
            ("on", True),
            ("off", False),
            ("true", True),
            ("false", False),
            ("1", True),
            ("0", False),
            ("yes", True),
            ("no", False),
            ("enabled", True),
            ("disabled", False),
            ("active", True),
            ("inactive", False)
        ]
        
        for state_value, expected in test_cases:
            event_data = {
                "event_type": "state_changed",
                "new_state": {"state": state_value, "entity_id": "light.living_room"}
            }
            
            normalized = self.normalizer.normalize_event(event_data)
            
            assert normalized is not None
            assert normalized["new_state"]["state"] == expected
    
    def test_normalize_state_values_numeric(self):
        """Test state value normalization for numeric values"""
        test_cases = [
            ("123", 123),
            ("123.45", 123.45),
            ("0", False),  # Should be converted to boolean False
            ("1", True),   # Should be converted to boolean True
        ]
        
        for state_value, expected in test_cases:
            event_data = {
                "event_type": "state_changed",
                "new_state": {"state": state_value, "entity_id": "sensor.temperature"}
            }
            
            normalized = self.normalizer.normalize_event(event_data)
            
            assert normalized is not None
            assert normalized["new_state"]["state"] == expected
    
    def test_normalize_state_values_string(self):
        """Test state value normalization for string values"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {"state": "unavailable", "entity_id": "sensor.temperature"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["new_state"]["state"] == "unavailable"
    
    def test_normalize_units_temperature(self):
        """Test unit normalization for temperature"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {
                "state": "22.5",
                "entity_id": "sensor.temperature",
                "attributes": {
                    "unit_of_measurement": "°C",
                    "device_class": "temperature"
                }
            }
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["new_state"]["attributes"]["unit_of_measurement"] == "celsius"
    
    def test_normalize_units_pressure(self):
        """Test unit normalization for pressure"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {
                "state": "1013.25",
                "entity_id": "sensor.pressure",
                "attributes": {
                    "unit_of_measurement": "hPa",
                    "device_class": "pressure"
                }
            }
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["new_state"]["attributes"]["unit_of_measurement"] == "hectopascal"
    
    def test_extract_entity_metadata(self):
        """Test entity metadata extraction"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {
                "state": "on",
                "entity_id": "light.living_room",
                "attributes": {
                    "friendly_name": "Living Room Light",
                    "device_class": "light",
                    "icon": "mdi:lightbulb",
                    "unit_of_measurement": None,
                    "entity_category": "config"
                }
            }
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert "entity_metadata" in normalized
        
        metadata = normalized["entity_metadata"]
        assert metadata["entity_id"] == "light.living_room"
        assert metadata["domain"] == "light"
        assert metadata["device_class"] == "light"
        assert metadata["friendly_name"] == "Living Room Light"
        assert metadata["icon"] == "mdi:lightbulb"
        assert metadata["entity_category"] == "config"
    
    def test_extract_entity_metadata_minimal(self):
        """Test entity metadata extraction with minimal data"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {
                "state": "on",
                "entity_id": "light.living_room"
            }
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert "entity_metadata" in normalized
        
        metadata = normalized["entity_metadata"]
        assert metadata["entity_id"] == "light.living_room"
        assert metadata["domain"] == "light"
        assert metadata["device_class"] is None
        assert metadata["friendly_name"] is None
    
    def test_normalize_event_with_old_state(self):
        """Test event normalization with old state"""
        event_data = {
            "event_type": "state_changed",
            "old_state": {
                "state": "off",
                "entity_id": "light.living_room",
                "last_changed": "2024-01-01T10:00:00Z",
                "last_updated": "2024-01-01T10:00:00Z"
            },
            "new_state": {
                "state": "on",
                "entity_id": "light.living_room",
                "last_changed": "2024-01-01T12:00:00Z",
                "last_updated": "2024-01-01T12:00:00Z"
            }
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        
        # Check old state normalization
        assert normalized["old_state"]["state"] == False  # "off" -> False
        assert normalized["old_state"]["last_changed"].endswith("+00:00")
        assert normalized["old_state"]["last_updated"].endswith("+00:00")
        
        # Check new state normalization
        assert normalized["new_state"]["state"] == True  # "on" -> True
        assert normalized["new_state"]["last_changed"].endswith("+00:00")
        assert normalized["new_state"]["last_updated"].endswith("+00:00")
    
    def test_normalize_event_invalid_data(self):
        """Test event normalization with invalid data"""
        # Missing event_type
        event_data = {
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is None
        assert self.normalizer.normalization_errors == 1
    
    def test_normalize_event_missing_new_state(self):
        """Test event normalization with missing new_state"""
        event_data = {
            "event_type": "state_changed",
            "old_state": {"state": "off", "entity_id": "light.living_room"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is None
        assert self.normalizer.normalization_errors == 1
    
    def test_normalize_event_missing_entity_id(self):
        """Test event normalization with missing entity_id"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {"state": "on"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is None
        assert self.normalizer.normalization_errors == 1
    
    def test_normalize_event_exception_handling(self):
        """Test event normalization exception handling"""
        # Pass None to trigger exception
        normalized = self.normalizer.normalize_event(None)
        
        assert normalized is None
        assert self.normalizer.normalization_errors == 1
    
    def test_get_normalization_statistics(self):
        """Test getting normalization statistics"""
        # Process some events
        self.normalizer.normalized_events = 10
        self.normalizer.normalization_errors = 2
        
        stats = self.normalizer.get_normalization_statistics()
        
        assert stats["normalized_events"] == 10
        assert stats["normalization_errors"] == 2
        assert abs(stats["success_rate"] - 83.33) < 0.01  # 10/(10+2)*100
    
    def test_get_normalization_statistics_no_events(self):
        """Test getting normalization statistics with no events"""
        stats = self.normalizer.get_normalization_statistics()
        
        assert stats["normalized_events"] == 0
        assert stats["normalization_errors"] == 0
        assert stats["success_rate"] == 0
    
    def test_reset_statistics(self):
        """Test resetting statistics"""
        # Set up some data
        self.normalizer.normalized_events = 10
        self.normalizer.normalization_errors = 2
        self.normalizer.last_normalized_time = datetime.now(timezone.utc)
        
        self.normalizer.reset_statistics()
        
        assert self.normalizer.normalized_events == 0
        assert self.normalizer.normalization_errors == 0
        assert self.normalizer.last_normalized_time is None
    
    def test_normalize_event_adds_metadata(self):
        """Test that normalization adds metadata"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {"state": "on", "entity_id": "light.living_room"}
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert "_normalized" in normalized
        
        normalized_metadata = normalized["_normalized"]
        assert "timestamp" in normalized_metadata
        assert "version" in normalized_metadata
        assert "source" in normalized_metadata
        assert normalized_metadata["version"] == "1.0.0"
        assert normalized_metadata["source"] == "enrichment-pipeline"
    
    def test_normalize_event_preserves_original_data(self):
        """Test that normalization preserves original data"""
        event_data = {
            "event_type": "state_changed",
            "new_state": {"state": "on", "entity_id": "light.living_room"},
            "custom_field": "custom_value"
        }
        
        normalized = self.normalizer.normalize_event(event_data)
        
        assert normalized is not None
        assert normalized["event_type"] == "state_changed"
        assert normalized["custom_field"] == "custom_value"
        assert normalized["new_state"]["entity_id"] == "light.living_room"
