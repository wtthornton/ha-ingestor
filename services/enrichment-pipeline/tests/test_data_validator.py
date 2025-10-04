"""
Tests for Data Validator
"""

import pytest
import sys
import os
from datetime import datetime, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_validator import DataValidator, ValidationLevel, ValidationResult


class TestDataValidator:
    """Test cases for DataValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = DataValidator()
    
    def test_validate_valid_event(self):
        """Test validation of a valid event"""
        valid_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "last_updated": "2024-12-19T15:30:00.000Z"
            }
        }
        
        results = self.validator.validate_event(valid_event)
        
        # Should have no errors
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        assert len(errors) == 0
        
        # Should be valid
        assert self.validator.is_event_valid(valid_event) is True
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields"""
        invalid_event = {
            "timestamp": "2024-12-19T15:30:00.000Z"
            # Missing event_type
        }
        
        results = self.validator.validate_event(invalid_event)
        
        # Should have errors for missing fields
        errors = [r for r in results if r.level == ValidationLevel.ERROR]
        assert len(errors) > 0
        
        # Should not be valid
        assert self.validator.is_event_valid(invalid_event) is False
    
    def test_validate_invalid_entity_id_format(self):
        """Test validation with invalid entity ID format"""
        invalid_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "invalid_entity_id",  # Invalid format
                "state": "22.5"
            }
        }
        
        results = self.validator.validate_event(invalid_event)
        
        # Should have format error
        format_errors = [r for r in results if "Invalid entity_id format" in r.message]
        assert len(format_errors) > 0
    
    def test_validate_invalid_timestamp_format(self):
        """Test validation with invalid timestamp format"""
        invalid_event = {
            "event_type": "state_changed",
            "timestamp": "invalid_timestamp",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5"
            }
        }
        
        results = self.validator.validate_event(invalid_event)
        
        # Should have timestamp format error
        timestamp_errors = [r for r in results if "Invalid timestamp format" in r.message]
        assert len(timestamp_errors) > 0
    
    def test_validate_weather_data_ranges(self):
        """Test validation of weather data ranges"""
        event_with_weather = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5"
            },
            "weather": {
                "temperature": 150.0,  # Too high
                "humidity": 150,  # Too high
                "pressure": 500.0  # Too low
            }
        }
        
        results = self.validator.validate_event(event_with_weather)
        
        # Should have warnings for out-of-range values
        warnings = [r for r in results if r.level == ValidationLevel.WARNING]
        assert len(warnings) >= 3  # Temperature, humidity, pressure warnings
    
    def test_validate_state_changed_consistency(self):
        """Test validation of state_changed event consistency"""
        inconsistent_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "old_state": {
                "entity_id": "sensor.temperature",
                "state": "20.0",
                "last_updated": "2024-12-19T15:29:00.000Z"
            },
            "new_state": {
                "entity_id": "sensor.humidity",  # Different entity
                "state": "22.5",
                "last_updated": "2024-12-19T15:30:00.000Z"
            }
        }
        
        results = self.validator.validate_event(inconsistent_event)
        
        # Should have consistency error
        consistency_errors = [r for r in results if "Entity ID mismatch" in r.message]
        assert len(consistency_errors) > 0
    
    def test_validate_timestamp_logic(self):
        """Test validation of timestamp logic"""
        future_event = {
            "event_type": "state_changed",
            "timestamp": "2030-12-19T15:30:00.000Z",  # Far in the future
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5"
            }
        }
        
        results = self.validator.validate_event(future_event)
        
        # Should have warning for future timestamp
        future_warnings = [r for r in results if "too far in the future" in r.message]
        assert len(future_warnings) > 0
    
    def test_validate_weather_enrichment(self):
        """Test validation of weather enrichment data"""
        event_with_incomplete_weather = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5"
            },
            "weather": {
                "temperature": 22.5
                # Missing humidity, pressure, timestamp
            }
        }
        
        results = self.validator.validate_event(event_with_incomplete_weather)
        
        # Should have warnings for missing weather fields
        weather_warnings = [r for r in results if "Missing weather field" in r.message]
        assert len(weather_warnings) >= 3  # humidity, pressure, timestamp
    
    def test_validation_statistics(self):
        """Test validation statistics tracking"""
        # Process some events
        valid_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5"
            }
        }
        
        invalid_event = {
            "timestamp": "2024-12-19T15:30:00.000Z"
            # Missing event_type
        }
        
        # Validate events
        self.validator.validate_event(valid_event)
        self.validator.validate_event(invalid_event)
        
        # Check statistics
        stats = self.validator.get_validation_statistics()
        
        assert stats["total_validations"] == 2
        assert stats["valid_events"] == 1
        assert stats["invalid_events"] == 1
        assert stats["success_rate"] == 50.0
    
    def test_reset_statistics(self):
        """Test statistics reset"""
        # Process an event
        valid_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5"
            }
        }
        
        self.validator.validate_event(valid_event)
        
        # Reset statistics
        self.validator.reset_statistics()
        
        # Check statistics are reset
        stats = self.validator.get_validation_statistics()
        assert stats["total_validations"] == 0
        assert stats["valid_events"] == 0
        assert stats["invalid_events"] == 0
    
    def test_data_type_validation(self):
        """Test data type validation"""
        invalid_types_event = {
            "event_type": 123,  # Should be string
            "timestamp": 456,  # Should be string
            "new_state": {
                "entity_id": 789,  # Should be string
                "state": "22.5"
            }
        }
        
        results = self.validator.validate_event(invalid_types_event)
        
        # Should have type errors
        type_errors = [r for r in results if "must be a" in r.message]
        assert len(type_errors) >= 2  # event_type, timestamp (entity_id validation happens in format validation)
    
    def test_validation_error_handling(self):
        """Test validation error handling"""
        # Test with malformed event that could cause exceptions
        malformed_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": None  # This could cause issues
        }
        
        # Should not raise exception
        results = self.validator.validate_event(malformed_event)
        
        # Should have errors
        assert len(results) > 0
        assert not self.validator.is_event_valid(malformed_event)
