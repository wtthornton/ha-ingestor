"""
Data Quality Alerting System
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class QualityAlert:
    """Quality alert data structure"""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    suppression_until: Optional[datetime] = None


class QualityAlertManager:
    """Manages quality alerts and notifications"""
    
    def __init__(self):
        self.active_alerts: Dict[str, QualityAlert] = {}
        self.alert_history: List[QualityAlert] = []
        self.alert_handlers: List[Callable] = []
        
        # Alert configuration
        self.alert_config = {
            "cooldown_periods": {
                "low_quality_score": timedelta(minutes=5),
                "high_error_rate": timedelta(minutes=2),
                "low_capture_rate": timedelta(minutes=10),
                "low_enrichment_coverage": timedelta(minutes=15),
                "high_processing_latency": timedelta(minutes=3),
                "validation_failure": timedelta(minutes=1),
                "entity_quality_degradation": timedelta(minutes=30)
            },
            "severity_thresholds": {
                "low_quality_score": {
                    "warning": 90.0,
                    "critical": 80.0
                },
                "high_error_rate": {
                    "warning": 2.0,
                    "critical": 5.0
                },
                "low_capture_rate": {
                    "warning": 95.0,
                    "critical": 90.0
                },
                "low_enrichment_coverage": {
                    "warning": 80.0,
                    "critical": 70.0
                },
                "high_processing_latency": {
                    "warning": 1000.0,
                    "critical": 2000.0
                }
            },
            "max_history_size": 1000
        }
        
        # Alert counters
        self.alert_counters = {
            "total_alerts": 0,
            "active_alerts": 0,
            "acknowledged_alerts": 0,
            "resolved_alerts": 0
        }
    
    def add_alert_handler(self, handler: Callable[[QualityAlert], None]):
        """
        Add an alert handler function
        
        Args:
            handler: Function to call when an alert is triggered
        """
        self.alert_handlers.append(handler)
        logger.info("Alert handler added")
    
    def trigger_alert(self, 
                     alert_type: str, 
                     message: str, 
                     details: Dict[str, Any],
                     severity: Optional[AlertSeverity] = None) -> Optional[QualityAlert]:
        """
        Trigger a quality alert
        
        Args:
            alert_type: Type of alert
            message: Alert message
            details: Alert details
            severity: Alert severity (auto-determined if None)
            
        Returns:
            QualityAlert if triggered, None if suppressed
        """
        try:
            # Check if alert should be suppressed due to cooldown
            if self._should_suppress_alert(alert_type):
                logger.debug(f"Alert suppressed due to cooldown: {alert_type}")
                return None
            
            # Determine severity if not provided
            if severity is None:
                severity = self._determine_alert_severity(alert_type, details)
            
            # Create alert
            alert_id = f"{alert_type}_{int(datetime.now(timezone.utc).timestamp())}"
            alert = QualityAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                details=details,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Update counters
            self.alert_counters["total_alerts"] += 1
            self.alert_counters["active_alerts"] += 1
            
            # Trim history if too large
            if len(self.alert_history) > self.alert_config["max_history_size"]:
                self.alert_history = self.alert_history[-self.alert_config["max_history_size"]:]
            
            # Log alert
            logger.warning(f"QUALITY ALERT [{alert_type}] {severity.value.upper()}: {message}")
            
            # Notify handlers (synchronous for now)
            try:
                for handler in self.alert_handlers:
                    if asyncio.iscoroutinefunction(handler):
                        # Skip async handlers in sync context
                        pass
                    else:
                        handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
            
            return alert
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
            return None
    
    def _should_suppress_alert(self, alert_type: str) -> bool:
        """Check if alert should be suppressed due to cooldown"""
        cooldown_period = self.alert_config["cooldown_periods"].get(alert_type, timedelta(minutes=5))
        
        # Check if there's a recent alert of the same type
        cutoff_time = datetime.now(timezone.utc) - cooldown_period
        
        for alert in self.alert_history[-10:]:  # Check last 10 alerts
            if (alert.alert_type == alert_type and 
                alert.timestamp > cutoff_time and 
                alert.status == AlertStatus.ACTIVE):
                return True
        
        return False
    
    def _determine_alert_severity(self, alert_type: str, details: Dict[str, Any]) -> AlertSeverity:
        """Determine alert severity based on thresholds"""
        thresholds = self.alert_config["severity_thresholds"].get(alert_type, {})
        
        if not thresholds:
            return AlertSeverity.WARNING
        
        # Get the relevant value from details
        value = self._extract_alert_value(alert_type, details)
        
        if value is None:
            return AlertSeverity.WARNING
        
        # Determine severity based on thresholds
        # For low_quality_score, lower values are more severe
        if alert_type == "low_quality_score":
            if "critical" in thresholds and value <= thresholds["critical"]:
                return AlertSeverity.CRITICAL
            elif "warning" in thresholds and value <= thresholds["warning"]:
                return AlertSeverity.WARNING
        else:
            # For other alert types, higher values are more severe
            if "critical" in thresholds and value >= thresholds["critical"]:
                return AlertSeverity.CRITICAL
            elif "warning" in thresholds and value >= thresholds["warning"]:
                return AlertSeverity.WARNING
        
        return AlertSeverity.INFO
    
    def _extract_alert_value(self, alert_type: str, details: Dict[str, Any]) -> Optional[float]:
        """Extract the relevant value for severity determination"""
        value_mapping = {
            "low_quality_score": "quality_score",
            "high_error_rate": "error_rate",
            "low_capture_rate": "capture_rate",
            "low_enrichment_coverage": "enrichment_coverage",
            "high_processing_latency": "processing_latency"
        }
        
        key = value_mapping.get(alert_type)
        if key and key in details:
            return float(details[key])
        
        return None
    
    async def _notify_handlers(self, alert: QualityAlert):
        """Notify all alert handlers"""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: ID of the alert to acknowledge
            acknowledged_by: Who acknowledged the alert
            
        Returns:
            True if acknowledged, False if not found
        """
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now(timezone.utc)
        
        self.alert_counters["acknowledged_alerts"] += 1
        
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return True
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an alert
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            True if resolved, False if not found
        """
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        self.alert_counters["resolved_alerts"] += 1
        self.alert_counters["active_alerts"] -= 1
        
        logger.info(f"Alert resolved: {alert_id}")
        return True
    
    def suppress_alert(self, alert_id: str, suppress_until: datetime) -> bool:
        """
        Suppress an alert until a specific time
        
        Args:
            alert_id: ID of the alert to suppress
            suppress_until: When to stop suppressing
            
        Returns:
            True if suppressed, False if not found
        """
        if alert_id not in self.active_alerts:
            return False
        
        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.SUPPRESSED
        alert.suppression_until = suppress_until
        
        logger.info(f"Alert suppressed until {suppress_until}: {alert_id}")
        return True
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get all active alerts
        
        Returns:
            List of active alert dictionaries
        """
        return [
            {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "suppression_until": alert.suppression_until.isoformat() if alert.suppression_until else None
            }
            for alert in self.active_alerts.values()
        ]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get alert history
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of alert history dictionaries
        """
        recent_alerts = self.alert_history[-limit:] if limit else self.alert_history
        
        return [
            {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
                "acknowledged_by": alert.acknowledged_by,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "suppression_until": alert.suppression_until.isoformat() if alert.suppression_until else None
            }
            for alert in recent_alerts
        ]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get alert statistics
        
        Returns:
            Dictionary with alert statistics
        """
        # Count alerts by severity
        severity_counts = {"info": 0, "warning": 0, "critical": 0}
        for alert in self.active_alerts.values():
            severity_counts[alert.severity.value] += 1
        
        # Count alerts by type
        type_counts = {}
        for alert in self.alert_history:
            alert_type = alert.alert_type
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        
        return {
            "total_alerts": self.alert_counters["total_alerts"],
            "active_alerts": self.alert_counters["active_alerts"],
            "acknowledged_alerts": self.alert_counters["acknowledged_alerts"],
            "resolved_alerts": self.alert_counters["resolved_alerts"],
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "alert_handlers": len(self.alert_handlers),
            "history_size": len(self.alert_history)
        }
    
    def cleanup_resolved_alerts(self, older_than: timedelta = timedelta(days=7)):
        """
        Clean up old resolved alerts
        
        Args:
            older_than: Remove alerts resolved older than this
        """
        cutoff_time = datetime.now(timezone.utc) - older_than
        
        # Remove from history
        self.alert_history = [
            alert for alert in self.alert_history
            if not (alert.status == AlertStatus.RESOLVED and 
                   alert.resolved_at and 
                   alert.resolved_at < cutoff_time)
        ]
        
        logger.info(f"Cleaned up old resolved alerts older than {older_than}")
    
    def check_suppressed_alerts(self):
        """Check and reactivate suppressed alerts that have expired"""
        current_time = datetime.now(timezone.utc)
        reactivated_count = 0
        
        for alert in list(self.active_alerts.values()):
            if (alert.status == AlertStatus.SUPPRESSED and 
                alert.suppression_until and 
                current_time > alert.suppression_until):
                
                alert.status = AlertStatus.ACTIVE
                alert.suppression_until = None
                reactivated_count += 1
                
                logger.info(f"Alert reactivated after suppression: {alert.alert_id}")
        
        if reactivated_count > 0:
            logger.info(f"Reactivated {reactivated_count} suppressed alerts")
    
    def reset_alerts(self):
        """Reset all alerts and counters"""
        self.active_alerts.clear()
        self.alert_history.clear()
        self.alert_counters = {
            "total_alerts": 0,
            "active_alerts": 0,
            "acknowledged_alerts": 0,
            "resolved_alerts": 0
        }
        logger.info("All alerts reset")


# Global alert manager instance
alert_manager = QualityAlertManager()


# Convenience functions for common alert types
def trigger_quality_score_alert(quality_score: float, threshold: float):
    """Trigger a low quality score alert"""
    return alert_manager.trigger_alert(
        alert_type="low_quality_score",
        message=f"Data quality score below threshold: {quality_score:.2f}% (threshold: {threshold:.2f}%)",
        details={"quality_score": quality_score, "threshold": threshold}
    )


def trigger_error_rate_alert(error_rate: float, threshold: float):
    """Trigger a high error rate alert"""
    return alert_manager.trigger_alert(
        alert_type="high_error_rate",
        message=f"Error rate above threshold: {error_rate:.2f}% (threshold: {threshold:.2f}%)",
        details={"error_rate": error_rate, "threshold": threshold}
    )


def trigger_capture_rate_alert(capture_rate: float, threshold: float):
    """Trigger a low capture rate alert"""
    return alert_manager.trigger_alert(
        alert_type="low_capture_rate",
        message=f"Capture rate below threshold: {capture_rate:.2f}% (threshold: {threshold:.2f}%)",
        details={"capture_rate": capture_rate, "threshold": threshold}
    )


def trigger_enrichment_coverage_alert(coverage: float, threshold: float):
    """Trigger a low enrichment coverage alert"""
    return alert_manager.trigger_alert(
        alert_type="low_enrichment_coverage",
        message=f"Enrichment coverage below threshold: {coverage:.2f}% (threshold: {threshold:.2f}%)",
        details={"enrichment_coverage": coverage, "threshold": threshold}
    )


def trigger_processing_latency_alert(latency: float, threshold: float):
    """Trigger a high processing latency alert"""
    return alert_manager.trigger_alert(
        alert_type="high_processing_latency",
        message=f"Processing latency above threshold: {latency:.2f}ms (threshold: {threshold:.2f}ms)",
        details={"processing_latency": latency, "threshold": threshold}
    )


def trigger_validation_failure_alert(entity_id: str, error_count: int):
    """Trigger a validation failure alert"""
    return alert_manager.trigger_alert(
        alert_type="validation_failure",
        message=f"Validation failures for entity {entity_id}: {error_count} errors",
        details={"entity_id": entity_id, "error_count": error_count}
    )


def trigger_entity_quality_degradation_alert(entity_id: str, quality_score: float, previous_score: float):
    """Trigger an entity quality degradation alert"""
    degradation = previous_score - quality_score
    return alert_manager.trigger_alert(
        alert_type="entity_quality_degradation",
        message=f"Entity {entity_id} quality degraded: {quality_score:.2f}% (was {previous_score:.2f}%, -{degradation:.2f}%)",
        details={
            "entity_id": entity_id,
            "current_quality": quality_score,
            "previous_quality": previous_score,
            "degradation": degradation
        }
    )
