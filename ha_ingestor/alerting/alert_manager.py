"""Alert manager for coordinating alerting operations."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from ..utils.logging import get_logger
from .notification_system import (
    NotificationChannel,
    NotificationConfig,
    NotificationMessage,
    create_notifier,
)
from .rules_engine import (
    AlertInstance,
    AlertRule,
    AlertRulesEngine,
    AlertSeverity,
    AlertStatus,
)
from .threshold_engine import ThresholdEngine


@dataclass
class AlertHistory:
    """Historical alert data for analysis and reporting."""

    alert_id: str
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
    notification_sent: bool = False
    notification_channels: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
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
            "notification_sent": self.notification_sent,
            "notification_channels": self.notification_channels,
        }


@dataclass
class AlertAggregator:
    """Aggregates similar alerts to reduce notification noise."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the alert aggregator."""
        self.config = config or {}
        self.aggregation_window_minutes = self.config.get(
            "aggregation_window_minutes", 5
        )
        self.alert_groups: dict[str, list[AlertInstance]] = {}
        self.last_cleanup = datetime.now(UTC)

    def should_aggregate(self, alert: AlertInstance) -> bool:
        """Check if an alert should be aggregated with existing ones."""
        current_time = datetime.now(UTC)
        cutoff_time = current_time - timedelta(minutes=self.aggregation_window_minutes)

        # Check if we have similar alerts within the aggregation window
        for _group_key, alerts in self.alert_groups.items():
            if self._is_similar_alert(alert, alerts[0]):
                # Check if any alert in the group is within the window
                recent_alerts = []
                for a in alerts:
                    # Handle timezone-naive datetimes by assuming UTC
                    triggered_at = a.triggered_at
                    if triggered_at.tzinfo is None:
                        triggered_at = triggered_at.replace(tzinfo=UTC)
                    if triggered_at >= cutoff_time:
                        recent_alerts.append(a)
                if recent_alerts:
                    return True

        return False

    def add_alert(self, alert: AlertInstance) -> None:
        """Add an alert to the appropriate aggregation group."""
        group_key = self._get_group_key(alert)

        if group_key not in self.alert_groups:
            self.alert_groups[group_key] = []

        self.alert_groups[group_key].append(alert)

        # Cleanup old groups periodically
        if datetime.now(UTC) - self.last_cleanup > timedelta(minutes=10):
            self._cleanup_old_groups()

    def get_aggregated_alerts(self) -> list[AlertInstance]:
        """Get alerts that should trigger notifications (aggregated)."""
        aggregated = []
        current_time = datetime.now(UTC)
        cutoff_time = current_time - timedelta(minutes=self.aggregation_window_minutes)

        for _group_key, alerts in self.alert_groups.items():
            # Get the most recent alert in each group
            recent_alerts = []
            for a in alerts:
                # Handle timezone-naive datetimes by assuming UTC
                triggered_at = a.triggered_at
                if triggered_at.tzinfo is None:
                    triggered_at = triggered_at.replace(tzinfo=UTC)
                if triggered_at >= cutoff_time:
                    recent_alerts.append(a)
            if recent_alerts:
                # Use the highest severity alert in the group
                highest_severity = max(recent_alerts, key=lambda x: x.severity.value)
                aggregated.append(highest_severity)

        return aggregated

    def _get_group_key(self, alert: AlertInstance) -> str:
        """Generate a key for grouping similar alerts."""
        # Group by rule name and severity
        return f"{alert.rule_name}:{alert.severity.value}"

    def _is_similar_alert(self, alert1: AlertInstance, alert2: AlertInstance) -> bool:
        """Check if two alerts are similar enough to aggregate."""
        return (
            alert1.rule_name == alert2.rule_name and alert1.severity == alert2.severity
        )

    def _cleanup_old_groups(self) -> None:
        """Remove old alert groups."""
        cutoff_time = datetime.now(UTC) - timedelta(hours=1)

        for group_key in list(self.alert_groups.keys()):
            # Remove groups with no recent alerts
            recent_alerts = []
            for a in self.alert_groups[group_key]:
                # Handle timezone-naive datetimes by assuming UTC
                triggered_at = a.triggered_at
                if triggered_at.tzinfo is None:
                    triggered_at = triggered_at.replace(tzinfo=UTC)
                if triggered_at >= cutoff_time:
                    recent_alerts.append(a)

            if not recent_alerts:
                del self.alert_groups[group_key]

        self.last_cleanup = datetime.now(UTC)


class AlertManager:
    """Main alert manager that coordinates all alerting components."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the alert manager."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Core components
        self.rules_engine = AlertRulesEngine(config)
        self.threshold_engine = ThresholdEngine(config)
        self.alert_aggregator = AlertAggregator(config)

        # Notification system
        self.notifiers: dict[str, Any] = {}
        self.notification_configs: dict[str, NotificationConfig] = {}

        # State management
        self.is_running = False
        self.check_task: asyncio.Task | None = None
        self.alert_history: list[AlertHistory] = []
        self.max_history_size = (
            self.config.get("alerting_history_retention_days", 30) * 24 * 60
        )  # Convert to minutes

        # Performance tracking
        self.total_alerts_processed = 0
        self.total_notifications_sent = 0
        self.last_check_time = datetime.now(UTC)

        # Initialize notification channels
        self._initialize_notification_channels()

    def _initialize_notification_channels(self) -> None:
        """Initialize notification channels based on configuration."""
        # Email notifications
        if self.config.get("enable_email_alerts", False):
            email_config = NotificationConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                name="Email Alerts",
                config=self.config.get("email_config", {}),
            )
            self.notification_configs["email"] = email_config
            self.notifiers["email"] = create_notifier(email_config)

        # Webhook notifications
        if self.config.get("enable_webhook_alerts", True):
            webhook_config = NotificationConfig(
                channel=NotificationChannel.WEBHOOK,
                enabled=True,
                name="Webhook Alerts",
                config=self.config.get("webhook_config", {}),
            )
            self.notification_configs["webhook"] = webhook_config
            self.notifiers["webhook"] = create_notifier(webhook_config)

        # Slack notifications
        if self.config.get("enable_slack_alerts", False):
            slack_config = NotificationConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                name="Slack Alerts",
                config=self.config.get("slack_config", {}),
            )
            self.notification_configs["slack"] = slack_config
            self.notifiers["slack"] = create_notifier(slack_config)

        # Discord notifications
        if self.config.get("enable_discord_alerts", False):
            discord_config = NotificationConfig(
                channel=NotificationChannel.DISCORD,
                enabled=True,
                name="Discord Alerts",
                config=self.config.get("discord_config", {}),
            )
            self.notification_configs["discord"] = discord_config
            self.notifiers["discord"] = create_notifier(discord_config)

        # PagerDuty notifications
        if self.config.get("enable_pagerduty_alerts", False):
            pagerduty_config = NotificationConfig(
                channel=NotificationChannel.PAGERDUTY,
                enabled=True,
                name="PagerDuty Alerts",
                config=self.config.get("pagerduty_config", {}),
            )
            self.notification_configs["pagerduty"] = pagerduty_config
            self.notifiers["pagerduty"] = create_notifier(pagerduty_config)

        self.logger.info(f"Initialized {len(self.notifiers)} notification channels")

    async def start(self) -> None:
        """Start the alert manager."""
        if self.is_running:
            self.logger.warning("Alert manager is already running")
            return

        self.is_running = True
        self.check_task = asyncio.create_task(self._run_alert_checks())
        self.logger.info("Alert manager started")

    async def stop(self) -> None:
        """Stop the alert manager."""
        if not self.is_running:
            return

        self.is_running = False

        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Alert manager stopped")

    async def _run_alert_checks(self) -> None:
        """Main loop for running alert checks."""
        check_interval = self.config.get("alerting_check_interval", 15.0)

        while self.is_running:
            try:
                await self._check_alerts()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in alert check loop: {e}")
                await asyncio.sleep(check_interval)

    async def _check_alerts(self) -> None:
        """Check for new alerts and process them."""
        try:
            # Clean up expired alerts
            cleaned_count = self.rules_engine.cleanup_expired_alerts()
            if cleaned_count > 0:
                self.logger.debug(f"Cleaned up {cleaned_count} expired alerts")

            # Get aggregated alerts that need notifications
            aggregated_alerts = self.alert_aggregator.get_aggregated_alerts()

            for alert in aggregated_alerts:
                await self._send_notifications(alert)

            self.last_check_time = datetime.now(UTC)

        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule to the manager."""
        self.rules_engine.add_rule(rule)
        self.logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str) -> bool:
        """Remove an alert rule from the manager."""
        return self.rules_engine.remove_rule(rule_name)

    def check_event(self, event_data: dict[str, Any]) -> list[AlertInstance]:
        """Check an event against all alert rules."""
        try:
            # Add data points to threshold engine for time-series analysis
            self._extract_and_add_data_points(event_data)

            # Check rules engine
            triggered_alerts = self.rules_engine.check_rules(event_data)

            # Add to aggregator
            for alert in triggered_alerts:
                self.alert_aggregator.add_alert(alert)

                # Add to history
                history_entry = AlertHistory(
                    alert_id=f"{alert.rule_name}-{int(alert.triggered_at.timestamp())}",
                    rule_name=alert.rule_name,
                    severity=alert.severity,
                    status=alert.status,
                    message=alert.message,
                    triggered_at=alert.triggered_at,
                    expires_at=alert.expires_at,
                    context=alert.context,
                    tags=alert.tags,
                )
                self.alert_history.append(history_entry)

            self.total_alerts_processed += len(triggered_alerts)

            # Clean up old history
            self._cleanup_old_history()

            return triggered_alerts

        except Exception as e:
            self.logger.error(f"Error checking event: {e}")
            return []

    def _extract_and_add_data_points(self, event_data: dict[str, Any]) -> None:
        """Extract numeric values from event data and add to threshold engine."""
        try:
            # Look for common numeric fields
            numeric_fields = [
                "value",
                "temperature",
                "humidity",
                "pressure",
                "battery",
                "voltage",
                "current",
                "power",
                "energy",
                "speed",
                "distance",
                "duration",
            ]

            for field_name in numeric_fields:
                if field_name in event_data:
                    try:
                        value = float(event_data[field_name])
                        self.threshold_engine.add_data_point(
                            field_name, value, metadata={"source": "event"}
                        )
                    except (ValueError, TypeError):
                        continue

            # Also check for nested numeric values
            if "attributes" in event_data and isinstance(
                event_data["attributes"], dict
            ):
                for attr_name, attr_value in event_data["attributes"].items():
                    if isinstance(attr_value, int | float):
                        field_path = f"attributes.{attr_name}"
                        self.threshold_engine.add_data_point(
                            field_path,
                            float(attr_value),
                            metadata={"source": "event_attributes"},
                        )

        except Exception as e:
            self.logger.debug(f"Error extracting data points: {e}")

    async def _send_notifications(self, alert: AlertInstance) -> None:
        """Send notifications for an alert through all configured channels."""
        if not self.notifiers:
            return

        # Create notification message
        message = NotificationMessage(
            title=f"Alert: {alert.rule_name}",
            body=alert.message,
            severity=alert.severity,
            alert_instance=alert,
            channel=NotificationChannel.WEBHOOK,  # Will be overridden per channel
            metadata={"source": "ha_ingestor"},
        )

        notification_sent = False
        sent_channels = []

        for channel_name, notifier in self.notifiers.items():
            try:
                # Update message channel for this notifier
                message.channel = self.notification_configs[channel_name].channel

                success = await notifier.send_notification(message)
                if success:
                    notification_sent = True
                    sent_channels.append(channel_name)
                    self.total_notifications_sent += 1

            except Exception as e:
                self.logger.error(f"Error sending notification via {channel_name}: {e}")

        # Update alert history
        if notification_sent:
            self._update_notification_status(alert, sent_channels)

    def _update_notification_status(
        self, alert: AlertInstance, channels: list[str]
    ) -> None:
        """Update notification status in alert history."""
        alert_id = f"{alert.rule_name}-{int(alert.triggered_at.timestamp())}"

        for history_entry in self.alert_history:
            if history_entry.alert_id == alert_id:
                history_entry.notification_sent = True
                history_entry.notification_channels = channels
                break

    def _cleanup_old_history(self) -> None:
        """Clean up old alert history entries."""
        if len(self.alert_history) <= self.max_history_size:
            return

        # Remove oldest entries
        cutoff_time = datetime.now(UTC) - timedelta(
            minutes=self.max_history_size
        )
        self.alert_history = [
            entry for entry in self.alert_history if entry.triggered_at >= cutoff_time
        ]

    def acknowledge_alert(self, rule_name: str) -> bool:
        """Acknowledge an active alert."""
        return self.rules_engine.acknowledge_alert(rule_name)

    def resolve_alert(self, rule_name: str) -> bool:
        """Resolve an active alert."""
        return self.rules_engine.resolve_alert(rule_name)

    def get_active_alerts(self) -> list[AlertInstance]:
        """Get all currently active alerts."""
        return self.rules_engine.get_active_alerts()

    def get_alert_history(self, limit: int = 100) -> list[AlertHistory]:
        """Get recent alert history."""
        return self.alert_history[-limit:] if self.alert_history else []

    def get_alert_rules(self) -> list[AlertRule]:
        """Get all configured alert rules."""
        return self.rules_engine.list_rules()

    def get_statistics(self) -> dict[str, Any]:
        """Get comprehensive alerting statistics."""
        return {
            "manager": {
                "is_running": self.is_running,
                "total_alerts_processed": self.total_alerts_processed,
                "total_notifications_sent": self.total_notifications_sent,
                "last_check_time": self.last_check_time.isoformat(),
                "alert_history_size": len(self.alert_history),
            },
            "rules_engine": self.rules_engine.get_statistics(),
            "threshold_engine": self.threshold_engine.get_engine_statistics(),
            "notifications": {
                "total_channels": len(self.notifiers),
                "channel_details": {
                    name: notifier.get_statistics()
                    for name, notifier in self.notifiers.items()
                },
            },
            "aggregation": {
                "total_groups": len(self.alert_aggregator.alert_groups),
                "aggregation_window_minutes": self.alert_aggregator.aggregation_window_minutes,
            },
        }
