"""Alerting rules engine for Home Assistant Activity Ingestor."""

import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from ..utils.logging import get_logger


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status values."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class AlertRule:
    """Definition of an alert rule."""

    name: str
    description: str
    severity: AlertSeverity
    enabled: bool = True
    conditions: list[dict[str, Any]] = field(default_factory=list)
    threshold: float | None = None
    threshold_type: str | None = None  # "above", "below", "equals"
    time_window_minutes: int = 5
    cooldown_minutes: int = 15
    notification_channels: list[str] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate alert rule configuration."""
        if self.threshold is not None and self.threshold_type not in [
            "above",
            "below",
            "equals",
        ]:
            raise ValueError("threshold_type must be 'above', 'below', or 'equals'")

        if self.time_window_minutes < 1:
            raise ValueError("time_window_minutes must be at least 1")

        if self.cooldown_minutes < 1:
            raise ValueError("cooldown_minutes must be at least 1")

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert alert rule to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "conditions": self.conditions,
            "threshold": self.threshold,
            "threshold_type": self.threshold_type,
            "time_window_minutes": self.time_window_minutes,
            "cooldown_minutes": self.cooldown_minutes,
            "notification_channels": self.notification_channels,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AlertRule":
        """Create alert rule from dictionary."""
        # Convert string severity back to enum
        if isinstance(data.get("severity"), str):
            data["severity"] = AlertSeverity(data["severity"])

        # Convert string timestamps back to datetime objects
        for timestamp_field in ["created_at", "updated_at"]:
            if isinstance(data.get(timestamp_field), str):
                data[timestamp_field] = datetime.fromisoformat(data[timestamp_field])

        return cls(**data)


@dataclass
class AlertInstance:
    """Instance of a triggered alert."""

    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    triggered_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    expires_at: datetime | None = None
    context: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def acknowledge(self) -> None:
        """Mark alert as acknowledged."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now(UTC)

    def resolve(self) -> None:
        """Mark alert as resolved."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now(UTC)

    def is_expired(self) -> bool:
        """Check if alert has expired."""
        if self.expires_at is None:
            return False
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # If expires_at is timezone-naive, assume UTC
            expires_at = expires_at.replace(tzinfo=UTC)
        return now > expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert alert instance to dictionary."""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "context": self.context,
            "tags": self.tags,
        }


class AlertRulesEngine:
    """Engine for evaluating alert rules and managing alert instances."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the alert rules engine."""
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.rules: dict[str, AlertRule] = {}
        self.active_alerts: dict[str, AlertInstance] = {}
        self.alert_history: list[AlertInstance] = []
        self.last_check_time = datetime.now(UTC)

        # Performance tracking
        self.evaluation_count = 0
        self.alert_count = 0
        self.last_evaluation_time = 0.0

    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule to the engine."""
        if rule.name in self.rules:
            self.logger.warning(f"Overwriting existing rule: {rule.name}")

        self.rules[rule.name] = rule
        self.logger.info(f"Added alert rule: {rule.name} ({rule.severity.value})")

    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule from the engine."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.info(f"Removed alert rule: {rule_name}")
            return True
        return False

    def get_rule(self, rule_name: str) -> AlertRule | None:
        """Get an alert rule by name."""
        return self.rules.get(rule_name)

    def list_rules(self) -> list[AlertRule]:
        """Get all alert rules."""
        return list(self.rules.values())

    def evaluate_rule(self, rule: AlertRule, data: dict[str, Any]) -> bool:
        """Evaluate if an alert rule should trigger based on data."""
        if not rule.enabled:
            return False

        # Check conditions
        for condition in rule.conditions:
            if not self._evaluate_condition(condition, data):
                return False

        # Check threshold if specified
        if rule.threshold is not None and rule.threshold_type is not None:
            if not self._evaluate_threshold(rule, data):
                return False

        return True

    def _evaluate_condition(
        self, condition: dict[str, Any], data: dict[str, Any]
    ) -> bool:
        """Evaluate a single condition against data."""
        field_path = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")

        if not field_path or not operator:
            return False

        # Extract field value from nested data
        field_value = self._extract_field_value(data, field_path)

        # Apply operator
        if operator == "equals":
            return field_value == value
        elif operator == "not_equals":
            return field_value != value
        elif operator == "contains":
            return str(value) in str(field_value)
        elif operator == "not_contains":
            return str(value) not in str(field_value)
        elif operator == "regex":
            try:
                return bool(re.search(str(value), str(field_value)))
            except re.error:
                return False
        elif operator == "in":
            return field_value in value if isinstance(value, list | tuple) else False
        elif operator == "not_in":
            return (
                field_value not in value if isinstance(value, list | tuple) else False
            )
        elif operator == "exists":
            # For exists, we check if the field exists in the data, regardless of its value
            return self._field_exists(data, field_path)
        elif operator == "not_exists":
            # For not_exists, we check if the field does not exist in the data
            return not self._field_exists(data, field_path)

        return False

    def _extract_field_value(self, data: dict[str, Any], field_path: str) -> Any:
        """Extract a field value from nested data using dot notation."""
        keys = field_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        return current

    def _field_exists(self, data: dict[str, Any], field_path: str) -> bool:
        """Check if a field exists in nested data using dot notation."""
        keys = field_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False

        return True

    def _evaluate_threshold(self, rule: AlertRule, data: dict[str, Any]) -> bool:
        """Evaluate threshold conditions."""
        # This will be implemented by the ThresholdEngine
        # For now, return True to allow basic rule evaluation
        return True

    def check_rules(self, data: dict[str, Any]) -> list[AlertInstance]:
        """Check all rules against the provided data."""
        start_time = time.time()
        triggered_alerts = []

        for rule in self.rules.values():
            if self.evaluate_rule(rule, data):
                # Check cooldown
                if self._should_trigger_alert(rule):
                    alert = self._create_alert_instance(rule, data)
                    triggered_alerts.append(alert)
                    self.active_alerts[alert.rule_name] = alert
                    self.alert_history.append(alert)
                    self.alert_count += 1

        self.evaluation_count += 1
        self.last_evaluation_time = time.time() - start_time
        self.last_check_time = datetime.now(UTC)

        return triggered_alerts

    def _should_trigger_alert(self, rule: AlertRule) -> bool:
        """Check if enough time has passed since the last alert for this rule."""
        if rule.name not in self.active_alerts:
            return True

        last_alert = self.active_alerts[rule.name]
        cooldown_delta = timedelta(minutes=rule.cooldown_minutes)

        return datetime.now(UTC) - last_alert.triggered_at > cooldown_delta

    def _create_alert_instance(
        self, rule: AlertRule, data: dict[str, Any]
    ) -> AlertInstance:
        """Create a new alert instance."""
        # Create expiration time
        expires_at = datetime.now(UTC) + timedelta(
            minutes=rule.time_window_minutes
        )

        # Create context with relevant data
        context = {
            "data": data,
            "rule": rule.to_dict(),
            "evaluation_time": datetime.now(UTC).isoformat(),
        }

        # Create message
        message = f"Alert '{rule.name}' triggered: {rule.description}"
        if rule.threshold is not None:
            message += f" (Threshold: {rule.threshold_type} {rule.threshold})"

        alert = AlertInstance(
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=message,
            triggered_at=datetime.now(UTC),
            expires_at=expires_at,
            context=context,
            tags=rule.tags.copy(),
        )

        self.logger.info(f"Alert triggered: {rule.name} ({rule.severity.value})")
        return alert

    def acknowledge_alert(self, rule_name: str) -> bool:
        """Acknowledge an active alert."""
        if rule_name in self.active_alerts:
            self.active_alerts[rule_name].acknowledge()
            self.logger.info(f"Alert acknowledged: {rule_name}")
            return True
        return False

    def resolve_alert(self, rule_name: str) -> bool:
        """Resolve an active alert."""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.resolve()
            # Move to history and remove from active
            self.alert_history.append(alert)
            del self.active_alerts[rule_name]
            self.logger.info(f"Alert resolved: {rule_name}")
            return True
        return False

    def cleanup_expired_alerts(self) -> int:
        """Clean up expired alerts and return count of cleaned alerts."""
        cleaned_count = 0

        # Check active alerts
        expired_active = [
            name for name, alert in self.active_alerts.items() if alert.is_expired()
        ]

        for name in expired_active:
            alert = self.active_alerts[name]
            alert.status = AlertStatus.EXPIRED
            self.alert_history.append(alert)
            del self.active_alerts[name]
            cleaned_count += 1

        # Clean up old history entries (keep last 1000)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired alerts")

        return cleaned_count

    def get_active_alerts(self) -> list[AlertInstance]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> list[AlertInstance]:
        """Get recent alert history."""
        return self.alert_history[-limit:] if self.alert_history else []

    def get_statistics(self) -> dict[str, Any]:
        """Get alerting engine statistics."""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "active_alerts": len(self.active_alerts),
            "total_alerts": self.alert_count,
            "evaluation_count": self.evaluation_count,
            "last_evaluation_time": self.last_evaluation_time,
            "last_check_time": self.last_check_time.isoformat(),
            "alert_history_size": len(self.alert_history),
        }
