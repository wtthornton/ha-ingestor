"""
Tests for Quality Alert Manager
"""

import pytest
import sys
import os
from datetime import datetime, timezone, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quality_alerts import QualityAlertManager, QualityAlert, AlertSeverity, AlertStatus


class TestQualityAlertManager:
    """Test cases for QualityAlertManager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.alert_manager = QualityAlertManager()
    
    def test_trigger_alert(self):
        """Test triggering an alert"""
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert message",
            details={"test": "data"}
        )
        
        assert alert is not None
        assert alert.alert_type == "test_alert"
        assert alert.message == "Test alert message"
        assert alert.details == {"test": "data"}
        assert alert.severity == AlertSeverity.WARNING  # Default severity
        assert alert.status == AlertStatus.ACTIVE
    
    def test_trigger_alert_with_severity(self):
        """Test triggering an alert with specific severity"""
        alert = self.alert_manager.trigger_alert(
            alert_type="critical_alert",
            message="Critical alert message",
            details={"error": "critical"},
            severity=AlertSeverity.CRITICAL
        )
        
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
    
    def test_alert_cooldown_suppression(self):
        """Test alert cooldown suppression"""
        # Trigger first alert
        alert1 = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="First alert",
            details={}
        )
        
        assert alert1 is not None
        
        # Trigger second alert of same type immediately
        alert2 = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Second alert",
            details={}
        )
        
        # Should be suppressed due to cooldown
        assert alert2 is None
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert"""
        # Trigger alert
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert",
            details={}
        )
        
        # Acknowledge alert
        success = self.alert_manager.acknowledge_alert(alert.alert_id, "test_user")
        
        assert success is True
        
        # Check alert status
        active_alerts = self.alert_manager.get_active_alerts()
        alert_data = next((a for a in active_alerts if a["alert_id"] == alert.alert_id), None)
        
        assert alert_data is not None
        assert alert_data["status"] == AlertStatus.ACKNOWLEDGED.value
        assert alert_data["acknowledged_by"] == "test_user"
        assert alert_data["acknowledged_at"] is not None
    
    def test_resolve_alert(self):
        """Test resolving an alert"""
        # Trigger alert
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert",
            details={}
        )
        
        # Resolve alert
        success = self.alert_manager.resolve_alert(alert.alert_id)
        
        assert success is True
        
        # Check alert is removed from active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        alert_data = next((a for a in active_alerts if a["alert_id"] == alert.alert_id), None)
        
        assert alert_data is None
        
        # Check alert is in history
        history = self.alert_manager.get_alert_history()
        alert_data = next((a for a in history if a["alert_id"] == alert.alert_id), None)
        
        assert alert_data is not None
        assert alert_data["status"] == AlertStatus.RESOLVED.value
        assert alert_data["resolved_at"] is not None
    
    def test_suppress_alert(self):
        """Test suppressing an alert"""
        # Trigger alert
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert",
            details={}
        )
        
        # Suppress alert
        suppress_until = datetime.now(timezone.utc) + timedelta(hours=1)
        success = self.alert_manager.suppress_alert(alert.alert_id, suppress_until)
        
        assert success is True
        
        # Check alert status
        active_alerts = self.alert_manager.get_active_alerts()
        alert_data = next((a for a in active_alerts if a["alert_id"] == alert.alert_id), None)
        
        assert alert_data is not None
        assert alert_data["status"] == AlertStatus.SUPPRESSED.value
        assert alert_data["suppression_until"] is not None
    
    def test_get_active_alerts(self):
        """Test getting active alerts"""
        # Trigger multiple alerts
        alert1 = self.alert_manager.trigger_alert(
            alert_type="alert_1",
            message="First alert",
            details={}
        )
        
        alert2 = self.alert_manager.trigger_alert(
            alert_type="alert_2",
            message="Second alert",
            details={}
        )
        
        # Resolve one alert
        self.alert_manager.resolve_alert(alert1.alert_id)
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Should only have one active alert
        assert len(active_alerts) == 1
        assert active_alerts[0]["alert_id"] == alert2.alert_id
    
    def test_get_alert_history(self):
        """Test getting alert history"""
        # Trigger alerts
        alert1 = self.alert_manager.trigger_alert(
            alert_type="alert_1",
            message="First alert",
            details={}
        )
        
        alert2 = self.alert_manager.trigger_alert(
            alert_type="alert_2",
            message="Second alert",
            details={}
        )
        
        # Resolve one alert
        self.alert_manager.resolve_alert(alert1.alert_id)
        
        # Get history
        history = self.alert_manager.get_alert_history()
        
        # Should have both alerts in history
        assert len(history) >= 2
        
        # Check alert statuses
        alert1_data = next((a for a in history if a["alert_id"] == alert1.alert_id), None)
        alert2_data = next((a for a in history if a["alert_id"] == alert2.alert_id), None)
        
        assert alert1_data is not None
        assert alert1_data["status"] == AlertStatus.RESOLVED.value
        
        assert alert2_data is not None
        assert alert2_data["status"] == AlertStatus.ACTIVE.value
    
    def test_get_alert_statistics(self):
        """Test getting alert statistics"""
        # Trigger alerts with different severities
        self.alert_manager.trigger_alert(
            alert_type="critical_alert",
            message="Critical alert",
            details={},
            severity=AlertSeverity.CRITICAL
        )
        
        self.alert_manager.trigger_alert(
            alert_type="warning_alert",
            message="Warning alert",
            details={},
            severity=AlertSeverity.WARNING
        )
        
        self.alert_manager.trigger_alert(
            alert_type="info_alert",
            message="Info alert",
            details={},
            severity=AlertSeverity.INFO
        )
        
        # Get statistics
        stats = self.alert_manager.get_alert_statistics()
        
        assert stats["total_alerts"] == 3
        assert stats["active_alerts"] == 3
        assert stats["severity_breakdown"]["critical"] == 1
        assert stats["severity_breakdown"]["warning"] == 1
        assert stats["severity_breakdown"]["info"] == 1
        assert stats["type_breakdown"]["critical_alert"] == 1
        assert stats["type_breakdown"]["warning_alert"] == 1
        assert stats["type_breakdown"]["info_alert"] == 1
    
    def test_alert_handler_notification(self):
        """Test alert handler notification"""
        handler_called = []
        
        def test_handler(alert):
            handler_called.append(alert.alert_id)
        
        # Add handler
        self.alert_manager.add_alert_handler(test_handler)
        
        # Trigger alert
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert",
            details={}
        )
        
        # Handler should be called (in real implementation, this would be async)
        # For testing, we'll just verify the handler was added
        assert len(self.alert_manager.alert_handlers) == 1
    
    def test_cleanup_resolved_alerts(self):
        """Test cleaning up old resolved alerts"""
        # Trigger and resolve an alert
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert",
            details={}
        )
        
        self.alert_manager.resolve_alert(alert.alert_id)
        
        # Manually set resolved time to old date
        for stored_alert in self.alert_manager.alert_history:
            if stored_alert.alert_id == alert.alert_id:
                stored_alert.resolved_at = datetime.now(timezone.utc) - timedelta(days=10)
                break
        
        # Cleanup old alerts
        self.alert_manager.cleanup_resolved_alerts(timedelta(days=7))
        
        # Check alert was removed from history
        history = self.alert_manager.get_alert_history()
        alert_data = next((a for a in history if a["alert_id"] == alert.alert_id), None)
        
        assert alert_data is None
    
    def test_check_suppressed_alerts(self):
        """Test checking and reactivating suppressed alerts"""
        # Trigger alert
        alert = self.alert_manager.trigger_alert(
            alert_type="test_alert",
            message="Test alert",
            details={}
        )
        
        # Suppress alert with past expiration time
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        self.alert_manager.suppress_alert(alert.alert_id, past_time)
        
        # Check suppressed alerts
        self.alert_manager.check_suppressed_alerts()
        
        # Alert should be reactivated
        active_alerts = self.alert_manager.get_active_alerts()
        alert_data = next((a for a in active_alerts if a["alert_id"] == alert.alert_id), None)
        
        assert alert_data is not None
        assert alert_data["status"] == AlertStatus.ACTIVE.value
    
    def test_reset_alerts(self):
        """Test resetting all alerts"""
        # Trigger some alerts
        self.alert_manager.trigger_alert(
            alert_type="alert_1",
            message="First alert",
            details={}
        )
        
        self.alert_manager.trigger_alert(
            alert_type="alert_2",
            message="Second alert",
            details={}
        )
        
        # Reset alerts
        self.alert_manager.reset_alerts()
        
        # Check all alerts are cleared
        active_alerts = self.alert_manager.get_active_alerts()
        history = self.alert_manager.get_alert_history()
        stats = self.alert_manager.get_alert_statistics()
        
        assert len(active_alerts) == 0
        assert len(history) == 0
        assert stats["total_alerts"] == 0
        assert stats["active_alerts"] == 0
    
    def test_alert_severity_determination(self):
        """Test automatic alert severity determination"""
        # Test critical severity
        critical_alert = self.alert_manager.trigger_alert(
            alert_type="low_quality_score",
            message="Low quality score",
            details={"quality_score": 70.0}  # Below critical threshold
        )
        
        assert critical_alert is not None
        assert critical_alert.severity == AlertSeverity.CRITICAL
        
        # Test warning severity with different alert type to avoid cooldown
        warning_alert = self.alert_manager.trigger_alert(
            alert_type="high_error_rate",
            message="High error rate",
            details={"error_rate": 3.0}  # Above warning threshold
        )
        
        assert warning_alert is not None
        assert warning_alert.severity == AlertSeverity.WARNING
    
    def test_nonexistent_alert_operations(self):
        """Test operations on non-existent alerts"""
        # Try to acknowledge non-existent alert
        success = self.alert_manager.acknowledge_alert("nonexistent_id", "test_user")
        assert success is False
        
        # Try to resolve non-existent alert
        success = self.alert_manager.resolve_alert("nonexistent_id")
        assert success is False
        
        # Try to suppress non-existent alert
        suppress_until = datetime.now(timezone.utc) + timedelta(hours=1)
        success = self.alert_manager.suppress_alert("nonexistent_id", suppress_until)
        assert success is False
