"""
Integration Tests for Quality System
"""

import pytest
import sys
import os
from datetime import datetime, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_validator import DataValidator, ValidationLevel
from quality_metrics import QualityMetricsTracker
from quality_alerts import QualityAlertManager
from quality_dashboard import QualityDashboardAPI
from quality_reporting import QualityReportingSystem


class TestQualitySystemIntegration:
    """Integration tests for the complete quality system"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.data_validator = DataValidator()
        self.quality_metrics = QualityMetricsTracker()
        self.alert_manager = QualityAlertManager()
        self.quality_dashboard = QualityDashboardAPI(
            self.quality_metrics,
            self.alert_manager,
            self.data_validator
        )
        self.quality_reporting = QualityReportingSystem(
            self.quality_metrics,
            self.alert_manager,
            self.data_validator
        )
    
    def test_complete_quality_workflow(self):
        """Test complete quality monitoring workflow"""
        # Test event 1: Valid event
        valid_event = {
            "event_type": "state_changed",
            "timestamp": "2024-12-19T15:30:00.000Z",
            "new_state": {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "last_updated": "2024-12-19T15:30:00.000Z"
            },
            "weather": {
                "temperature": 22.5,
                "humidity": 60,
                "pressure": 1013,
                "timestamp": "2024-12-19T15:30:00.000Z"
            }
        }
        
        # Validate event
        validation_results = self.data_validator.validate_event(valid_event)
        assert self.data_validator.is_event_valid(valid_event) is True
        
        # Record in quality metrics
        self.quality_metrics.record_validation_result(valid_event, validation_results, 100.0)
        
        # Test event 2: Invalid event
        invalid_event = {
            "timestamp": "2024-12-19T15:31:00.000Z"
            # Missing event_type and new_state
        }
        
        # Validate event
        validation_results = self.data_validator.validate_event(invalid_event)
        assert self.data_validator.is_event_valid(invalid_event) is False
        
        # Record in quality metrics
        self.quality_metrics.record_validation_result(invalid_event, validation_results, 150.0)
        
        # Check quality metrics
        current_metrics = self.quality_metrics.get_current_metrics()
        assert current_metrics["total_events"] == 2
        assert current_metrics["valid_events"] == 1
        assert current_metrics["invalid_events"] == 1
        assert current_metrics["enrichment_coverage"] == 50.0  # 1 out of 2 events has weather
        
        # Check entity quality
        entity_quality = self.quality_metrics.get_entity_quality("sensor.temperature")
        assert entity_quality is not None
        assert entity_quality["total_events"] == 1
        assert entity_quality["valid_events"] == 1
        assert entity_quality["quality_score"] == 100.0
        
        # Check validation statistics
        validation_stats = self.data_validator.get_validation_statistics()
        assert validation_stats["total_validations"] == 2
        assert validation_stats["valid_events"] == 1
        assert validation_stats["invalid_events"] == 1
        assert validation_stats["success_rate"] == 50.0
    
    def test_quality_alert_integration(self):
        """Test quality alert integration"""
        # Set low quality threshold to trigger alert
        self.quality_metrics.set_quality_thresholds({
            "min_quality_score": 95.0,
            "max_error_rate": 1.0
        })
        
        # Process events that will trigger alerts
        for i in range(10):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i}",
                    "state": f"value_{i}"
                }
            }
            
            # Make some events invalid to lower quality score
            if i < 3:  # 30% invalid events
                event = {"timestamp": "2024-12-19T15:30:00.000Z"}  # Invalid
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0)
        
        # Check if alerts were triggered
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Should have alerts due to low quality score
        assert len(active_alerts) > 0
        
        # Check alert statistics
        alert_stats = self.alert_manager.get_alert_statistics()
        assert alert_stats["total_alerts"] > 0
        assert alert_stats["active_alerts"] > 0
    
    def test_quality_dashboard_integration(self):
        """Test quality dashboard integration"""
        # Process some events
        for i in range(5):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i}",
                    "state": f"value_{i}"
                }
            }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0 + i)
        
        # Get quality report
        quality_report = self.quality_metrics.get_quality_report()
        
        # Check report structure
        assert "current_metrics" in quality_report
        assert "entity_quality" in quality_report
        assert "problematic_entities" in quality_report
        assert "common_validation_errors" in quality_report
        
        # Check current metrics
        current_metrics = quality_report["current_metrics"]
        assert current_metrics["total_events"] == 5
        assert current_metrics["valid_events"] == 5
        
        # Check entity quality
        entity_quality = quality_report["entity_quality"]
        assert len(entity_quality) == 5  # 5 different entities
        
        # Check health status
        health_status = self.quality_metrics.get_health_status()
        assert "status" in health_status
        assert "health_issues" in health_status
        assert "active_alerts" in health_status
    
    def test_quality_reporting_integration(self):
        """Test quality reporting integration"""
        # Process events to generate data
        for i in range(20):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i % 5}",  # 5 different entities
                    "state": f"value_{i}"
                }
            }
            
            # Add weather to some events
            if i % 3 == 0:
                event["weather"] = {
                    "temperature": 22.5 + i,
                    "humidity": 60,
                    "pressure": 1013,
                    "timestamp": "2024-12-19T15:30:00.000Z"
                }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0 + i)
        
        # Generate quality report
        import asyncio
        
        async def generate_report():
            return await self.quality_reporting.generate_report("daily")
        
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            report = loop.run_until_complete(generate_report())
        finally:
            loop.close()
        
        # Check report structure
        assert report.report_type == "daily"
        assert "current_metrics" in report.data
        assert "quality_trends" in report.data
        assert "entity_quality_summary" in report.data
        assert "alerts_summary" in report.data
        assert "validation_summary" in report.data
        assert "system_health" in report.data
        
        # Check summary
        assert "overall_quality_score" in report.summary
        assert "total_events_processed" in report.summary
        assert "error_rate" in report.summary
        assert "active_alerts" in report.summary
        assert "system_status" in report.summary
        
        # Check recommendations
        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0
        
        # Check entity quality summary
        entity_summary = report.data["entity_quality_summary"]
        assert entity_summary["total_entities"] == 5
        assert entity_summary["problematic_entities"] == 0  # All events are valid
        
        # Check enrichment coverage
        current_metrics = report.data["current_metrics"]
        # Should have some enrichment coverage (about 33% - 7 out of 20 events)
        assert current_metrics["enrichment_coverage"] > 0
    
    def test_quality_threshold_violations(self):
        """Test quality threshold violations and alerting"""
        # Set strict thresholds
        self.quality_metrics.set_quality_thresholds({
            "min_quality_score": 99.0,  # Very strict
            "max_error_rate": 0.1,      # Very strict
            "min_enrichment_coverage": 95.0  # Very strict
        })
        
        # Process events that will violate thresholds
        for i in range(10):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i}",
                    "state": f"value_{i}"
                }
            }
            
            # Make some events invalid
            if i < 2:  # 20% invalid events
                event = {"timestamp": "2024-12-19T15:30:00.000Z"}  # Invalid
            
            # Don't add weather to most events (low enrichment coverage)
            if i < 2:  # Only 20% have weather
                event["weather"] = {
                    "temperature": 22.5,
                    "humidity": 60,
                    "pressure": 1013,
                    "timestamp": "2024-12-19T15:30:00.000Z"
                }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0)
        
        # Check quality metrics
        current_metrics = self.quality_metrics.get_current_metrics()
        
        # Should have low quality score due to invalid events
        assert current_metrics["quality_score"] < 99.0
        
        # Should have high error rate
        assert current_metrics["error_rate"] > 0.1
        
        # Should have low enrichment coverage
        assert current_metrics["enrichment_coverage"] < 95.0
        
        # Check health status
        health_status = self.quality_metrics.get_health_status()
        assert health_status["status"] in ["warning", "critical"]
        assert len(health_status["health_issues"]) > 0
    
    def test_entity_quality_degradation(self):
        """Test entity quality degradation detection"""
        entity_id = "sensor.temperature"
        
        # Process initial valid events
        for i in range(10):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": entity_id,
                    "state": f"value_{i}"
                }
            }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0)
        
        # Check initial quality
        initial_quality = self.quality_metrics.get_entity_quality(entity_id)
        assert initial_quality["quality_score"] == 100.0
        
        # Process invalid events for the same entity
        for i in range(5):
            invalid_event = {
                "timestamp": "2024-12-19T15:30:00.000Z"
                # Missing required fields
            }
            
            validation_results = self.data_validator.validate_event(invalid_event)
            # Manually set entity_id for invalid event
            self.quality_metrics.record_validation_result(invalid_event, validation_results, 100.0)
        
        # Check degraded quality
        degraded_quality = self.quality_metrics.get_entity_quality(entity_id)
        assert degraded_quality["quality_score"] < 100.0
        assert degraded_quality["invalid_events"] > 0
    
    def test_quality_metrics_reset(self):
        """Test quality metrics reset functionality"""
        # Process some events
        for i in range(5):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i}",
                    "state": f"value_{i}"
                }
            }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0)
        
        # Check metrics before reset
        metrics_before = self.quality_metrics.get_current_metrics()
        assert metrics_before["total_events"] == 5
        
        # Reset metrics
        self.quality_metrics.reset_metrics()
        
        # Check metrics after reset
        metrics_after = self.quality_metrics.get_current_metrics()
        assert metrics_after["total_events"] == 0
        assert metrics_after["valid_events"] == 0
        assert metrics_after["invalid_events"] == 0
        
        # Check entity quality is cleared
        entity_quality = self.quality_metrics.get_entity_quality("sensor.test_0")
        assert entity_quality is None
    
    def test_validation_error_tracking(self):
        """Test validation error tracking across components"""
        # Process events with different validation errors
        events_with_errors = [
            {
                "timestamp": "2024-12-19T15:30:00.000Z"
                # Missing event_type
            },
            {
                "event_type": "state_changed",
                "timestamp": "invalid_timestamp"
                # Invalid timestamp format
            },
            {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": "invalid_entity_id",  # Invalid format
                    "state": "22.5"
                }
            }
        ]
        
        # Process events and track errors
        for event in events_with_errors:
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0)
        
        # Check validation statistics
        validation_stats = self.data_validator.get_validation_statistics()
        assert validation_stats["total_validations"] == 3
        assert validation_stats["invalid_events"] == 3
        assert validation_stats["success_rate"] == 0.0
        
        # Check quality report for common errors
        quality_report = self.quality_metrics.get_quality_report()
        common_errors = quality_report["common_validation_errors"]
        
        # Should have tracked different types of errors
        assert len(common_errors) >= 3
        
        # Check error types
        error_messages = [error["error"] for error in common_errors]
        assert any("Missing required field" in msg for msg in error_messages)
        assert any("Invalid timestamp format" in msg for msg in error_messages)
        assert any("Invalid entity_id format" in msg for msg in error_messages)
    
    def test_processing_latency_tracking(self):
        """Test processing latency tracking"""
        # Process events with different processing times
        processing_times = [50.0, 100.0, 150.0, 200.0, 250.0]
        
        for i, latency in enumerate(processing_times):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i}",
                    "state": f"value_{i}"
                }
            }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, latency)
        
        # Check processing latency
        current_metrics = self.quality_metrics.get_current_metrics()
        expected_avg = sum(processing_times) / len(processing_times)
        
        assert abs(current_metrics["processing_latency_avg"] - expected_avg) < 0.1
        assert current_metrics["processing_latency_avg"] == 150.0
    
    def test_quality_system_performance(self):
        """Test quality system performance with many events"""
        # Process many events to test performance
        num_events = 1000
        
        for i in range(num_events):
            event = {
                "event_type": "state_changed",
                "timestamp": "2024-12-19T15:30:00.000Z",
                "new_state": {
                    "entity_id": f"sensor.test_{i % 10}",  # 10 different entities
                    "state": f"value_{i}"
                }
            }
            
            # Add weather to some events
            if i % 4 == 0:
                event["weather"] = {
                    "temperature": 22.5 + (i % 10),
                    "humidity": 60,
                    "pressure": 1013,
                    "timestamp": "2024-12-19T15:30:00.000Z"
                }
            
            validation_results = self.data_validator.validate_event(event)
            self.quality_metrics.record_validation_result(event, validation_results, 100.0 + (i % 50))
        
        # Check final metrics
        current_metrics = self.quality_metrics.get_current_metrics()
        assert current_metrics["total_events"] == num_events
        assert current_metrics["valid_events"] == num_events
        assert current_metrics["quality_score"] == 100.0
        
        # Check entity quality
        entity_quality = self.quality_metrics.get_entity_quality("sensor.test_0")
        assert entity_quality is not None
        assert entity_quality["total_events"] == 100  # 1000 events / 10 entities
        
        # Check enrichment coverage
        expected_coverage = (num_events // 4) / num_events * 100  # 25%
        assert abs(current_metrics["enrichment_coverage"] - expected_coverage) < 1.0
        
        # Check processing latency
        assert current_metrics["processing_latency_avg"] > 0
        assert current_metrics["processing_latency_avg"] < 200.0  # Should be reasonable
    
    def test_quality_system_error_recovery(self):
        """Test quality system error recovery"""
        # Test with malformed events that could cause exceptions
        malformed_events = [
            None,  # None event
            {},    # Empty event
            {"event_type": None},  # None event_type
            {"event_type": "state_changed", "new_state": None},  # None new_state
            {"event_type": "state_changed", "new_state": {"entity_id": None}},  # None entity_id
        ]
        
        # Process malformed events - should not crash
        for event in malformed_events:
            try:
                validation_results = self.data_validator.validate_event(event)
                self.quality_metrics.record_validation_result(event, validation_results, 100.0)
            except Exception as e:
                # Should handle gracefully
                assert "Error" in str(e) or "validation" in str(e).lower()
        
        # Check metrics are still valid
        current_metrics = self.quality_metrics.get_current_metrics()
        assert current_metrics["total_events"] == len(malformed_events)
        
        # Check validation statistics
        validation_stats = self.data_validator.get_validation_statistics()
        assert validation_stats["total_validations"] == len(malformed_events)
        
        # System should still be functional
        health_status = self.quality_metrics.get_health_status()
        assert "status" in health_status
        assert "health_issues" in health_status
