"""
Tests for Quality Metrics Tracker
"""

import pytest
import sys
import os
from datetime import datetime, timezone, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quality_metrics import QualityMetricsTracker, QualityMetrics
from data_validator import ValidationResult, ValidationLevel


class TestQualityMetricsTracker:
    """Test cases for QualityMetricsTracker"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.tracker = QualityMetricsTracker()
    
    def test_record_validation_result_valid_event(self):
        """Test recording validation result for valid event"""
        event = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        
        validation_results = []  # No validation errors
        
        self.tracker.record_validation_result(event, validation_results, 100.0)
        
        metrics = self.tracker.get_current_metrics()
        
        assert metrics["total_events"] == 1
        assert metrics["valid_events"] == 1
        assert metrics["invalid_events"] == 0
        assert metrics["processing_latency_avg"] == 100.0
    
    def test_record_validation_result_invalid_event(self):
        """Test recording validation result for invalid event"""
        event = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        
        validation_results = [
            ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Missing required field",
                field="event_type"
            )
        ]
        
        self.tracker.record_validation_result(event, validation_results, 150.0)
        
        metrics = self.tracker.get_current_metrics()
        
        assert metrics["total_events"] == 1
        assert metrics["valid_events"] == 0
        assert metrics["invalid_events"] == 1
        assert metrics["errors"] == 1
    
    def test_record_validation_result_with_warnings(self):
        """Test recording validation result with warnings"""
        event = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "weather": {
                "temperature": 150.0  # Out of range
            }
        }
        
        validation_results = [
            ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message="Temperature out of range",
                field="weather.temperature"
            )
        ]
        
        self.tracker.record_validation_result(event, validation_results, 200.0)
        
        metrics = self.tracker.get_current_metrics()
        
        assert metrics["total_events"] == 1
        assert metrics["valid_events"] == 1  # Still valid despite warning
        assert metrics["warnings"] == 1
        assert metrics["errors"] == 0
    
    def test_entity_quality_tracking(self):
        """Test entity-specific quality tracking"""
        event1 = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        
        event2 = {
            "entity_id": "sensor.temperature",
            "state": "23.0",
            "timestamp": "2024-12-19T15:31:00.000Z"
        }
        
        # Record valid events
        self.tracker.record_validation_result(event1, [], 100.0)
        self.tracker.record_validation_result(event2, [], 120.0)
        
        # Get entity quality
        entity_quality = self.tracker.get_entity_quality("sensor.temperature")
        
        assert entity_quality is not None
        assert entity_quality["entity_id"] == "sensor.temperature"
        assert entity_quality["total_events"] == 2
        assert entity_quality["valid_events"] == 2
        assert entity_quality["quality_score"] == 100.0
    
    def test_weather_enrichment_coverage(self):
        """Test weather enrichment coverage tracking"""
        event_with_weather = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "weather": {
                "temperature": 22.5,
                "humidity": 60
            }
        }
        
        event_without_weather = {
            "entity_id": "sensor.humidity",
            "state": "60",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        
        # Record events
        self.tracker.record_validation_result(event_with_weather, [], 100.0)
        self.tracker.record_validation_result(event_without_weather, [], 110.0)
        
        metrics = self.tracker.get_current_metrics()
        
        # Should have 50% enrichment coverage (1 out of 2 events)
        assert metrics["enrichment_coverage"] == 50.0
    
    def test_quality_score_calculation(self):
        """Test quality score calculation"""
        # Record events with different validation results
        valid_event = {"entity_id": "sensor.temperature", "state": "22.5"}
        invalid_event = {"entity_id": "sensor.humidity", "state": "60"}
        warning_event = {"entity_id": "sensor.pressure", "state": "1013"}
        
        # Record valid event
        self.tracker.record_validation_result(valid_event, [], 100.0)
        
        # Record invalid event
        invalid_results = [
            ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Missing field",
                field="timestamp"
            )
        ]
        self.tracker.record_validation_result(invalid_event, invalid_results, 150.0)
        
        # Record event with warning
        warning_results = [
            ValidationResult(
                is_valid=True,
                level=ValidationLevel.WARNING,
                message="Value out of range",
                field="state"
            )
        ]
        self.tracker.record_validation_result(warning_event, warning_results, 120.0)
        
        metrics = self.tracker.get_current_metrics()
        
        # Quality score should be calculated considering errors and warnings
        assert metrics["quality_score"] < 100.0  # Should be penalized
        assert metrics["quality_score"] > 0.0    # Should be positive
    
    def test_quality_report_generation(self):
        """Test quality report generation"""
        # Record some events
        for i in range(10):
            event = {
                "entity_id": f"sensor.test_{i}",
                "state": f"value_{i}",
                "timestamp": "2024-12-19T15:30:00.000Z"
            }
            self.tracker.record_validation_result(event, [], 100.0 + i)
        
        # Generate report
        report = self.tracker.get_quality_report()
        
        assert "current_metrics" in report
        assert "trend_metrics" in report
        assert "entity_quality" in report
        assert "problematic_entities" in report
        assert "common_validation_errors" in report
        assert "active_alerts" in report
        assert "quality_thresholds" in report
        
        # Check current metrics
        current_metrics = report["current_metrics"]
        assert current_metrics["total_events"] == 10
        assert current_metrics["valid_events"] == 10
    
    def test_health_status(self):
        """Test health status calculation"""
        # Record events to establish baseline
        for i in range(5):
            event = {
                "entity_id": f"sensor.test_{i}",
                "state": f"value_{i}",
                "timestamp": "2024-12-19T15:30:00.000Z"
            }
            self.tracker.record_validation_result(event, [], 100.0)
        
        health_status = self.tracker.get_health_status()
        
        assert "status" in health_status
        assert "health_issues" in health_status
        assert "active_alerts" in health_status
        assert "total_entities" in health_status
        assert "metrics_age_seconds" in health_status
        
        # Should be healthy with good metrics
        assert health_status["status"] in ["healthy", "warning"]
    
    def test_quality_thresholds(self):
        """Test quality threshold configuration"""
        # Set custom thresholds
        custom_thresholds = {
            "min_quality_score": 90.0,
            "max_error_rate": 2.0,
            "min_capture_rate": 95.0
        }
        
        self.tracker.set_quality_thresholds(custom_thresholds)
        
        # Check thresholds were updated
        assert self.tracker.quality_thresholds["min_quality_score"] == 90.0
        assert self.tracker.quality_thresholds["max_error_rate"] == 2.0
        assert self.tracker.quality_thresholds["min_capture_rate"] == 95.0
    
    def test_reset_metrics(self):
        """Test metrics reset"""
        # Record some events
        event = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        self.tracker.record_validation_result(event, [], 100.0)
        
        # Reset metrics
        self.tracker.reset_metrics()
        
        # Check metrics are reset
        metrics = self.tracker.get_current_metrics()
        assert metrics["total_events"] == 0
        assert metrics["valid_events"] == 0
        assert metrics["invalid_events"] == 0
        
        # Check entity metrics are cleared
        entity_quality = self.tracker.get_entity_quality("sensor.temperature")
        assert entity_quality is None
    
    def test_processing_latency_averaging(self):
        """Test processing latency averaging"""
        # Record events with different processing times
        processing_times = [100.0, 150.0, 200.0, 120.0, 180.0]
        
        for i, latency in enumerate(processing_times):
            event = {
                "entity_id": f"sensor.test_{i}",
                "state": f"value_{i}",
                "timestamp": "2024-12-19T15:30:00.000Z"
            }
            self.tracker.record_validation_result(event, [], latency)
        
        metrics = self.tracker.get_current_metrics()
        
        # Should calculate average latency
        expected_avg = sum(processing_times) / len(processing_times)
        assert abs(metrics["processing_latency_avg"] - expected_avg) < 0.1
    
    def test_validation_error_tracking(self):
        """Test validation error tracking"""
        event = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        
        validation_results = [
            ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Missing required field",
                field="event_type"
            ),
            ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message="Invalid format",
                field="timestamp"
            )
        ]
        
        self.tracker.record_validation_result(event, validation_results, 100.0)
        
        report = self.tracker.get_quality_report()
        common_errors = report["common_validation_errors"]
        
        # Should track validation errors
        assert len(common_errors) >= 2
        assert any("Missing required field" in error["error"] for error in common_errors)
        assert any("Invalid format" in error["error"] for error in common_errors)
    
    def test_entity_extraction_edge_cases(self):
        """Test entity ID extraction edge cases"""
        # Test with missing entity_id
        event_no_entity = {
            "state": "22.5",
            "timestamp": "2024-12-19T15:30:00.000Z"
        }
        
        self.tracker.record_validation_result(event_no_entity, [], 100.0)
        
        # Should not crash and should handle gracefully
        metrics = self.tracker.get_current_metrics()
        assert metrics["total_events"] == 1
        
        # Test with malformed event structure
        event_malformed = {
            "event_type": "state_changed",
            "new_state": None  # Malformed
        }
        
        self.tracker.record_validation_result(event_malformed, [], 100.0)
        
        # Should not crash
        metrics = self.tracker.get_current_metrics()
        assert metrics["total_events"] == 2
