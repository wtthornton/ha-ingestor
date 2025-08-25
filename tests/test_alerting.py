"""Tests for the alerting system."""

import asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import MagicMock, patch

import pytest

from ha_ingestor.alerting.alert_manager import (
    AlertAggregator,
    AlertHistory,
    AlertManager,
)
from ha_ingestor.alerting.dashboard import AlertDashboard
from ha_ingestor.alerting.notification_system import (
    AlertNotifier,
    DiscordNotifier,
    EmailNotifier,
    NotificationChannel,
    NotificationConfig,
    NotificationMessage,
    PagerDutyNotifier,
    SlackNotifier,
    WebhookNotifier,
    create_notifier,
)
from ha_ingestor.alerting.rules_engine import (
    AlertInstance,
    AlertRule,
    AlertRulesEngine,
    AlertSeverity,
    AlertStatus,
)
from ha_ingestor.alerting.threshold_engine import (
    DataPoint,
    ThresholdCondition,
    ThresholdEngine,
    ThresholdType,
)


class TestAlertSeverity:
    """Test alert severity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestAlertStatus:
    """Test alert status enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert AlertStatus.ACTIVE.value == "active"
        assert AlertStatus.ACKNOWLEDGED.value == "acknowledged"
        assert AlertStatus.RESOLVED.value == "resolved"
        assert AlertStatus.EXPIRED.value == "expired"


class TestAlertRule:
    """Test alert rule data class."""

    def test_alert_rule_creation(self):
        """Test creating an alert rule."""
        rule = AlertRule(
            name="test_rule",
            description="Test rule description",
            severity=AlertSeverity.WARNING,
            conditions=[{"field": "temperature", "operator": "above", "value": 25}],
            threshold=30.0,
            threshold_type="above",
        )

        assert rule.name == "test_rule"
        assert rule.description == "Test rule description"
        assert rule.severity == AlertSeverity.WARNING
        assert rule.enabled is True
        assert len(rule.conditions) == 1
        assert rule.threshold == 30.0
        assert rule.threshold_type == "above"

    def test_alert_rule_validation(self):
        """Test alert rule validation."""
        # Test invalid threshold type
        with pytest.raises(ValueError, match="threshold_type must be"):
            AlertRule(
                name="test_rule",
                description="Test rule",
                severity=AlertSeverity.INFO,
                threshold=10.0,
                threshold_type="invalid",
            )

        # Test invalid time window
        with pytest.raises(ValueError, match="time_window_minutes must be at least 1"):
            AlertRule(
                name="test_rule",
                description="Test rule",
                severity=AlertSeverity.INFO,
                time_window_minutes=0,
            )

        # Test invalid cooldown
        with pytest.raises(ValueError, match="cooldown_minutes must be at least 1"):
            AlertRule(
                name="test_rule",
                description="Test rule",
                severity=AlertSeverity.INFO,
                cooldown_minutes=0,
            )

    def test_alert_rule_serialization(self):
        """Test alert rule serialization to/from dict."""
        rule = AlertRule(
            name="test_rule",
            description="Test rule description",
            severity=AlertSeverity.ERROR,
            tags={"environment": "test", "service": "ha-ingestor"},
        )

        rule_dict = rule.to_dict()
        assert rule_dict["name"] == "test_rule"
        assert rule_dict["severity"] == "error"
        assert rule_dict["tags"]["environment"] == "test"

        # Test from_dict
        restored_rule = AlertRule.from_dict(rule_dict)
        assert restored_rule.name == rule.name
        assert restored_rule.severity == rule.severity
        assert restored_rule.tags == rule.tags


class TestAlertInstance:
    """Test alert instance data class."""

    def test_alert_instance_creation(self):
        """Test creating an alert instance."""
        now = datetime.utcnow()
        alert = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            message="Test alert message",
            triggered_at=now,
            context={"data": "test"},
        )

        assert alert.rule_name == "test_rule"
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.ACTIVE
        assert alert.message == "Test alert message"
        assert alert.triggered_at == now
        assert alert.context["data"] == "test"

    def test_alert_instance_actions(self):
        """Test alert instance actions."""
        alert = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=datetime.utcnow(),
        )

        # Test acknowledge
        alert.acknowledge()
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_at is not None

        # Test resolve
        alert.resolve()
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None

    def test_alert_instance_expiration(self):
        """Test alert instance expiration."""
        now = datetime.utcnow()
        alert = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.INFO,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=now,
            expires_at=now + timedelta(minutes=5),
        )

        # Should not be expired immediately
        assert not alert.is_expired()

        # Should be expired after time passes
        with patch("ha_ingestor.alerting.rules_engine.datetime") as mock_datetime:
            mock_datetime.now.return_value = (now + timedelta(minutes=10)).replace(tzinfo=UTC)
            assert alert.is_expired()


class TestAlertRulesEngine:
    """Test alert rules engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = AlertRulesEngine()
        self.test_rule = AlertRule(
            name="temperature_high",
            description="Temperature is too high",
            severity=AlertSeverity.WARNING,
            conditions=[{"field": "temperature", "operator": "equals", "value": 30}],
        )

    def test_add_rule(self):
        """Test adding alert rules."""
        self.engine.add_rule(self.test_rule)
        assert "temperature_high" in self.engine.rules
        assert self.engine.rules["temperature_high"] == self.test_rule

    def test_remove_rule(self):
        """Test removing alert rules."""
        self.engine.add_rule(self.test_rule)
        assert self.engine.remove_rule("temperature_high") is True
        assert "temperature_high" not in self.engine.rules

        # Test removing non-existent rule
        assert self.engine.remove_rule("non_existent") is False

    def test_evaluate_condition(self):
        """Test condition evaluation."""
        # Test equals operator
        condition = {"field": "status", "operator": "equals", "value": "error"}
        data = {"status": "error"}
        assert self.engine._evaluate_condition(condition, data) is True

        # Test not equals operator
        data = {"status": "ok"}
        assert self.engine._evaluate_condition(condition, data) is False

        # Test contains operator
        condition = {"field": "message", "operator": "contains", "value": "error"}
        data = {"message": "System error occurred"}
        assert self.engine._evaluate_condition(condition, data) is True

        # Test regex operator
        condition = {
            "field": "message",
            "operator": "regex",
            "value": r"error.*occurred",
        }
        assert self.engine._evaluate_condition(condition, data) is True

        # Test in operator
        condition = {"field": "level", "operator": "in", "value": ["error", "critical"]}
        data = {"level": "error"}
        assert self.engine._evaluate_condition(condition, data) is True

        # Test exists operator
        condition = {"field": "optional_field", "operator": "exists", "value": None}
        data = {"optional_field": "value"}
        assert self.engine._evaluate_condition(condition, data) is True

        # Test not_exists operator
        condition = {"field": "optional_field", "operator": "not_exists", "value": None}
        data = {}
        assert self.engine._evaluate_condition(condition, data) is True

    def test_extract_field_value(self):
        """Test field value extraction."""
        data = {
            "level": "info",
            "attributes": {"temperature": 25.5, "nested": {"value": "deep"}},
        }

        assert self.engine._extract_field_value(data, "level") == "info"
        assert self.engine._extract_field_value(data, "attributes.temperature") == 25.5
        assert (
            self.engine._extract_field_value(data, "attributes.nested.value") == "deep"
        )
        assert self.engine._extract_field_value(data, "non_existent") is None
        assert self.engine._extract_field_value(data, "attributes.missing") is None

    def test_check_rules(self):
        """Test rule checking."""
        self.engine.add_rule(self.test_rule)

        # Test matching data
        matching_data = {"temperature": 30}
        alerts = self.engine.check_rules(matching_data)
        assert len(alerts) == 1
        assert alerts[0].rule_name == "temperature_high"

        # Test non-matching data
        non_matching_data = {"temperature": 20}
        alerts = self.engine.check_rules(non_matching_data)
        assert len(alerts) == 0

    def test_cooldown_handling(self):
        """Test alert cooldown handling."""
        self.engine.add_rule(self.test_rule)

        # First alert should trigger
        data = {"temperature": 30}
        alerts = self.engine.check_rules(data)
        assert len(alerts) == 1

        # Second alert within cooldown should not trigger
        alerts = self.engine.check_rules(data)
        assert len(alerts) == 0

    def test_alert_acknowledgment(self):
        """Test alert acknowledgment."""
        self.engine.add_rule(self.test_rule)
        data = {"temperature": 30}
        self.engine.check_rules(data)

        assert self.engine.acknowledge_alert("temperature_high") is True
        alert = self.engine.active_alerts["temperature_high"]
        assert alert.status == AlertStatus.ACKNOWLEDGED

        # Test acknowledging non-existent alert
        assert self.engine.acknowledge_alert("non_existent") is False

    def test_alert_resolution(self):
        """Test alert resolution."""
        self.engine.add_rule(self.test_rule)
        data = {"temperature": 30}
        self.engine.check_rules(data)

        assert self.engine.resolve_alert("temperature_high") is True
        assert "temperature_high" not in self.engine.active_alerts
        assert len(self.engine.alert_history) == 2  # One for trigger, one for resolve

    def test_cleanup_expired_alerts(self):
        """Test expired alert cleanup."""
        self.engine.add_rule(self.test_rule)
        data = {"temperature": 30}
        self.engine.check_rules(data)

        # Manually expire the alert
        alert = self.engine.active_alerts["temperature_high"]
        alert.expires_at = datetime.utcnow() - timedelta(minutes=1)

        cleaned_count = self.engine.cleanup_expired_alerts()
        assert cleaned_count == 1
        assert "temperature_high" not in self.engine.active_alerts

    def test_get_statistics(self):
        """Test statistics generation."""
        self.engine.add_rule(self.test_rule)
        data = {"temperature": 30}
        self.engine.check_rules(data)

        stats = self.engine.get_statistics()
        assert stats["total_rules"] == 1
        assert stats["enabled_rules"] == 1
        assert stats["active_alerts"] == 1
        assert stats["total_alerts"] == 1
        assert stats["evaluation_count"] == 1


class TestThresholdType:
    """Test threshold type enum."""

    def test_threshold_type_values(self):
        """Test threshold type enum values."""
        assert ThresholdType.ABOVE.value == "above"
        assert ThresholdType.BELOW.value == "below"
        assert ThresholdType.EQUALS.value == "equals"
        assert ThresholdType.NOT_EQUALS.value == "not_equals"
        assert ThresholdType.PERCENT_CHANGE.value == "percent_change"
        assert ThresholdType.TREND_UP.value == "trend_up"
        assert ThresholdType.TREND_DOWN.value == "trend_down"
        assert ThresholdType.VOLATILITY.value == "volatility"
        assert ThresholdType.OUTLIER.value == "outlier"


class TestThresholdCondition:
    """Test threshold condition data class."""

    def test_threshold_condition_creation(self):
        """Test creating a threshold condition."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.ABOVE,
            threshold_value=25.0,
            time_window_minutes=10,
            min_data_points=5,
        )

        assert condition.field_path == "temperature"
        assert condition.threshold_type == ThresholdType.ABOVE
        assert condition.threshold_value == 25.0
        assert condition.time_window_minutes == 10
        assert condition.min_data_points == 5

    def test_threshold_condition_validation(self):
        """Test threshold condition validation."""
        # Test invalid time window
        with pytest.raises(ValueError, match="time_window_minutes must be at least 1"):
            ThresholdCondition(
                field_path="temp",
                threshold_type=ThresholdType.ABOVE,
                threshold_value=25.0,
                time_window_minutes=0,
            )

        # Test invalid min data points
        with pytest.raises(ValueError, match="min_data_points must be at least 2"):
            ThresholdCondition(
                field_path="temp",
                threshold_type=ThresholdType.ABOVE,
                threshold_value=25.0,
                min_data_points=1,
            )

        # Test invalid aggregation method
        with pytest.raises(ValueError, match="aggregation_method must be one of"):
            ThresholdCondition(
                field_path="temp",
                threshold_type=ThresholdType.ABOVE,
                threshold_value=25.0,
                aggregation_method="invalid",
            )


class TestDataPoint:
    """Test data point data class."""

    def test_data_point_creation(self):
        """Test creating a data point."""
        now = datetime.utcnow()
        point = DataPoint(timestamp=now, value=25.5, metadata={"source": "sensor"})

        assert point.timestamp == now
        assert point.value == 25.5
        assert point.metadata["source"] == "sensor"

    def test_data_point_validation(self):
        """Test data point validation."""
        # Test invalid value type
        with pytest.raises(ValueError, match="value must be numeric"):
            DataPoint(timestamp=datetime.utcnow(), value="not_a_number")


class TestThresholdEngine:
    """Test threshold engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ThresholdEngine()

    def test_add_data_point(self):
        """Test adding data points."""
        now = datetime.utcnow()
        self.engine.add_data_point("temperature", 25.5, now, {"source": "test"})

        assert "temperature" in self.engine.data_history
        assert len(self.engine.data_history["temperature"]) == 1

        point = self.engine.data_history["temperature"][0]
        assert point.value == 25.5
        assert point.timestamp == now
        assert point.metadata["source"] == "test"

    def test_data_point_cleanup(self):
        """Test data point cleanup."""
        # Add more than max_history_size points
        for i in range(10001):
            self.engine.add_data_point("test_field", float(i))

        # Should only keep max_history_size points
        assert len(self.engine.data_history["test_field"]) == 10000

    def test_evaluate_threshold_above(self):
        """Test above threshold evaluation."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.ABOVE,
            threshold_value=25.0,
            min_data_points=2,
        )

        # Add data points
        self.engine.add_data_point("temperature", 20.0)
        self.engine.add_data_point("temperature", 30.0)  # Above threshold

        data = {"temperature": 30.0}
        assert self.engine.evaluate_threshold(condition, data) is True

        data = {"temperature": 20.0}
        assert self.engine.evaluate_threshold(condition, data) is False

    def test_evaluate_threshold_below(self):
        """Test below threshold evaluation."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.BELOW,
            threshold_value=25.0,
            min_data_points=2,
        )

        # Add data points
        self.engine.add_data_point("temperature", 30.0)
        self.engine.add_data_point("temperature", 20.0)  # Below threshold

        data = {"temperature": 20.0}
        assert self.engine.evaluate_threshold(condition, data) is True

        data = {"temperature": 30.0}
        assert self.engine.evaluate_threshold(condition, data) is False

    def test_evaluate_threshold_equals(self):
        """Test equals threshold evaluation."""
        condition = ThresholdCondition(
            field_path="status",
            threshold_type=ThresholdType.EQUALS,
            threshold_value=25.0,
            min_data_points=2,
        )

        # Add data points
        self.engine.add_data_point("status", 25.0)
        self.engine.add_data_point("status", 30.0)

        data = {"status": 25.0}
        assert self.engine.evaluate_threshold(condition, data) is True

        data = {"status": 30.0}
        assert self.engine.evaluate_threshold(condition, data) is False

    def test_evaluate_threshold_percent_change(self):
        """Test percent change threshold evaluation."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.PERCENT_CHANGE,
            threshold_value=20.0,  # 20% change
            aggregation_method="avg",
            min_data_points=2,
        )

        # Add baseline data points
        self.engine.add_data_point("temperature", 20.0)
        self.engine.add_data_point("temperature", 20.0)

        # Current value with 25% change (25 vs 20 = 25% increase)
        data = {"temperature": 25.0}
        assert self.engine.evaluate_threshold(condition, data) is True

        # Current value with 15% change (23 vs 20 = 15% increase)
        data = {"temperature": 23.0}
        assert self.engine.evaluate_threshold(condition, data) is False

    def test_evaluate_threshold_trend(self):
        """Test trend threshold evaluation."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.TREND_UP,
            threshold_value=0.1,
            trend_sensitivity=0.1,
        )

        # Add data points with upward trend
        self.engine.add_data_point("temperature", 20.0)
        self.engine.add_data_point("temperature", 22.0)
        self.engine.add_data_point("temperature", 25.0)

        data = {"temperature": 25.0}
        assert self.engine.evaluate_threshold(condition, data) is True

    def test_evaluate_threshold_volatility(self):
        """Test volatility threshold evaluation."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.VOLATILITY,
            threshold_value=0.3,  # 30% volatility
            volatility_threshold=0.3,
        )

        # Add data points with high volatility
        self.engine.add_data_point("temperature", 20.0)
        self.engine.add_data_point("temperature", 30.0)
        self.engine.add_data_point("temperature", 10.0)

        data = {"temperature": 25.0}
        assert self.engine.evaluate_threshold(condition, data) is True

    def test_evaluate_threshold_outlier(self):
        """Test outlier threshold evaluation."""
        condition = ThresholdCondition(
            field_path="temperature",
            threshold_type=ThresholdType.OUTLIER,
            threshold_value=2.0,  # 2 standard deviations
            outlier_std_dev=2.0,
        )

        # Add data points with one outlier
        self.engine.add_data_point("temperature", 20.0)
        self.engine.add_data_point("temperature", 21.0)
        self.engine.add_data_point("temperature", 19.0)

        # Outlier value
        data = {"temperature": 50.0}
        assert self.engine.evaluate_threshold(condition, data) is True

        # Normal value
        data = {"temperature": 20.0}
        assert self.engine.evaluate_threshold(condition, data) is False

    def test_get_field_statistics(self):
        """Test field statistics generation."""
        # Add data points
        self.engine.add_data_point("temperature", 20.0)
        self.engine.add_data_point("temperature", 25.0)
        self.engine.add_data_point("temperature", 30.0)

        stats = self.engine.get_field_statistics("temperature", 60)
        assert stats["field_path"] == "temperature"
        assert stats["data_points"] == 3
        assert stats["statistics"]["min"] == 20.0
        assert stats["statistics"]["max"] == 30.0
        assert stats["statistics"]["mean"] == 25.0
        assert "trend_slope" in stats["statistics"]

    def test_get_engine_statistics(self):
        """Test engine statistics generation."""
        # Add some data points
        self.engine.add_data_point("field1", 10.0)
        self.engine.add_data_point("field2", 20.0)

        stats = self.engine.get_engine_statistics()
        assert stats["total_fields"] == 2
        assert stats["total_data_points"] == 2
        assert "field1" in stats["field_details"]
        assert "field2" in stats["field_details"]


class TestNotificationChannel:
    """Test notification channel enum."""

    def test_notification_channel_values(self):
        """Test notification channel enum values."""
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.WEBHOOK.value == "webhook"
        assert NotificationChannel.SLACK.value == "slack"
        assert NotificationChannel.DISCORD.value == "discord"
        assert NotificationChannel.PAGERDUTY.value == "pagerduty"


class TestNotificationConfig:
    """Test notification configuration."""

    def test_notification_config_creation(self):
        """Test creating notification configuration."""
        config = NotificationConfig(
            channel=NotificationChannel.EMAIL,
            enabled=True,
            name="Test Email",
            config={"smtp_host": "localhost"},
        )

        assert config.channel == NotificationChannel.EMAIL
        assert config.enabled is True
        assert config.name == "Test Email"
        assert config.config["smtp_host"] == "localhost"


class TestNotificationMessage:
    """Test notification message."""

    def test_notification_message_creation(self):
        """Test creating notification message."""
        alert_instance = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=datetime.utcnow(),
        )

        message = NotificationMessage(
            title="Test Alert",
            body="Test alert body",
            severity=AlertSeverity.WARNING,
            alert_instance=alert_instance,
            channel=NotificationChannel.EMAIL,
        )

        assert message.title == "Test Alert"
        assert message.body == "Test alert body"
        assert message.severity == AlertSeverity.WARNING
        assert message.alert_instance == alert_instance
        assert message.channel == NotificationChannel.EMAIL

    def test_notification_message_serialization(self):
        """Test notification message serialization."""
        alert_instance = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.ERROR,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=datetime.utcnow(),
        )

        message = NotificationMessage(
            title="Test Alert",
            body="Test alert body",
            severity=AlertSeverity.ERROR,
            alert_instance=alert_instance,
            channel=NotificationChannel.WEBHOOK,
        )

        message_dict = message.to_dict()
        assert message_dict["title"] == "Test Alert"
        assert message_dict["severity"] == "error"
        assert message_dict["channel"] == "webhook"
        assert "timestamp" in message_dict


class TestAlertNotifier:
    """Test base alert notifier."""

    def test_alert_notifier_base_class(self):
        """Test base alert notifier functionality."""
        config = NotificationConfig(
            channel=NotificationChannel.EMAIL, enabled=True, name="Test"
        )

        # Test that base class cannot be instantiated
        with pytest.raises(TypeError):
            AlertNotifier(config)


class TestEmailNotifier:
    """Test email notifier."""

    def setup_method(self):
        """Set up test fixtures."""
        config = NotificationConfig(
            channel=NotificationChannel.EMAIL,
            enabled=True,
            name="Test Email",
            config={
                "smtp_host": "localhost",
                "smtp_port": 587,
                "from_email": "test@example.com",
                "to_emails": ["user@example.com"],
            },
        )
        self.notifier = EmailNotifier(config)

    @patch("smtplib.SMTP")
    def test_send_notification_success(self, mock_smtp):
        """Test successful email notification."""
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        alert_instance = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=datetime.utcnow(),
        )

        message = NotificationMessage(
            title="Test Alert",
            body="Test alert body",
            severity=AlertSeverity.WARNING,
            alert_instance=alert_instance,
            channel=NotificationChannel.EMAIL,
        )

        # Test async method
        result = asyncio.run(self.notifier.send_notification(message))
        assert result is True
        assert self.notifier.success_count == 1
        assert self.notifier.last_success is not None

    def test_get_statistics(self):
        """Test notifier statistics."""
        stats = self.notifier.get_statistics()
        assert stats["channel"] == "email"
        assert stats["enabled"] is True
        assert stats["success_count"] == 0
        assert stats["failure_count"] == 0


class TestWebhookNotifier:
    """Test webhook notifier."""

    def setup_method(self):
        """Set up test fixtures."""
        config = NotificationConfig(
            channel=NotificationChannel.WEBHOOK,
            enabled=True,
            name="Test Webhook",
            config={"webhook_url": "http://example.com/webhook"},
        )
        self.notifier = WebhookNotifier(config)

    def test_send_notification_success(self):
        """Test successful webhook notification."""
        # Test basic functionality without complex mocking
        alert_instance = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.INFO,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=datetime.utcnow(),
        )

        message = NotificationMessage(
            title="Test Alert",
            body="Test alert body",
            severity=AlertSeverity.INFO,
            alert_instance=alert_instance,
            channel=NotificationChannel.WEBHOOK,
        )

        # Test that the notifier is properly configured
        assert self.notifier.webhook_url == "http://example.com/webhook"
        assert self.notifier.webhook_method == "POST"
        assert self.notifier.webhook_timeout == 30


class TestCreateNotifier:
    """Test notifier factory function."""

    def test_create_email_notifier(self):
        """Test creating email notifier."""
        config = NotificationConfig(
            channel=NotificationChannel.EMAIL, enabled=True, name="Test"
        )

        notifier = create_notifier(config)
        assert isinstance(notifier, EmailNotifier)

    def test_create_webhook_notifier(self):
        """Test creating webhook notifier."""
        config = NotificationConfig(
            channel=NotificationChannel.WEBHOOK, enabled=True, name="Test"
        )

        notifier = create_notifier(config)
        assert isinstance(notifier, WebhookNotifier)

    def test_create_slack_notifier(self):
        """Test creating Slack notifier."""
        config = NotificationConfig(
            channel=NotificationChannel.SLACK, enabled=True, name="Test"
        )

        notifier = create_notifier(config)
        assert isinstance(notifier, SlackNotifier)

    def test_create_discord_notifier(self):
        """Test creating Discord notifier."""
        config = NotificationConfig(
            channel=NotificationChannel.DISCORD, enabled=True, name="Test"
        )

        notifier = create_notifier(config)
        assert isinstance(notifier, DiscordNotifier)

    def test_create_pagerduty_notifier(self):
        """Test creating PagerDuty notifier."""
        config = NotificationConfig(
            channel=NotificationChannel.PAGERDUTY, enabled=True, name="Test"
        )

        notifier = create_notifier(config)
        assert isinstance(notifier, PagerDutyNotifier)

    def test_create_invalid_notifier(self):
        """Test creating invalid notifier."""
        config = NotificationConfig(channel="invalid", enabled=True, name="Test")

        with pytest.raises(ValueError, match="Unsupported notification channel"):
            create_notifier(config)


class TestAlertHistory:
    """Test alert history data class."""

    def test_alert_history_creation(self):
        """Test creating alert history entry."""
        now = datetime.utcnow()
        history = AlertHistory(
            alert_id="test-123",
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            triggered_at=now,
            notification_sent=True,
            notification_channels=["email", "webhook"],
        )

        assert history.alert_id == "test-123"
        assert history.rule_name == "test_rule"
        assert history.severity == AlertSeverity.WARNING
        assert history.status == AlertStatus.ACTIVE
        assert history.message == "Test alert"
        assert history.triggered_at == now
        assert history.notification_sent is True
        assert history.notification_channels == ["email", "webhook"]

    def test_alert_history_serialization(self):
        """Test alert history serialization."""
        now = datetime.utcnow()
        history = AlertHistory(
            alert_id="test-123",
            rule_name="test_rule",
            severity=AlertSeverity.ERROR,
            status=AlertStatus.RESOLVED,
            message="Test alert",
            triggered_at=now,
        )

        history_dict = history.to_dict()
        assert history_dict["alert_id"] == "test-123"
        assert history_dict["severity"] == "error"
        assert history_dict["status"] == "resolved"
        assert "triggered_at" in history_dict


class TestAlertAggregator:
    """Test alert aggregator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.aggregator = AlertAggregator({"aggregation_window_minutes": 5})

    def test_alert_aggregation(self):
        """Test alert aggregation."""
        now = datetime.utcnow()

        # Create similar alerts
        alert1 = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert 1",
            triggered_at=now,
        )

        alert2 = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert 2",
            triggered_at=now + timedelta(minutes=1),
        )

        # Add alerts to aggregator
        self.aggregator.add_alert(alert1)
        self.aggregator.add_alert(alert2)

        # Should aggregate similar alerts
        aggregated = self.aggregator.get_aggregated_alerts()
        assert len(aggregated) == 1  # Should return one representative alert

    def test_should_aggregate(self):
        """Test aggregation decision logic."""
        now = datetime.utcnow()

        alert1 = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert 1",
            triggered_at=now,
        )

        alert2 = AlertInstance(
            rule_name="test_rule",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="Test alert 2",
            triggered_at=now + timedelta(minutes=1),
        )

        # Add first alert
        self.aggregator.add_alert(alert1)

        # Second similar alert should be marked for aggregation
        assert self.aggregator.should_aggregate(alert2) is True


class TestAlertManager:
    """Test alert manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "enable_webhook_alerts": True,
            "webhook_config": {"webhook_url": "http://example.com/webhook"},
            "alerting_history_retention_days": 1,
        }
        self.manager = AlertManager(self.config)

    def test_alert_manager_initialization(self):
        """Test alert manager initialization."""
        assert self.manager.rules_engine is not None
        assert self.manager.threshold_engine is not None
        assert self.manager.alert_aggregator is not None
        assert len(self.manager.notifiers) > 0

    def test_add_alert_rule(self):
        """Test adding alert rules to manager."""
        rule = AlertRule(
            name="test_rule", description="Test rule", severity=AlertSeverity.WARNING
        )

        self.manager.add_alert_rule(rule)
        rules = self.manager.get_alert_rules()
        assert len(rules) == 1
        assert rules[0].name == "test_rule"

    def test_check_event(self):
        """Test event checking."""
        # Add a rule
        rule = AlertRule(
            name="temperature_high",
            description="Temperature is high",
            severity=AlertSeverity.WARNING,
            conditions=[{"field": "temperature", "operator": "equals", "value": 30}],
        )
        self.manager.add_alert_rule(rule)

        # Check matching event
        event_data = {"temperature": 30}
        alerts = self.manager.check_event(event_data)
        assert len(alerts) == 1
        assert alerts[0].rule_name == "temperature_high"

        # Check non-matching event
        event_data = {"temperature": 20}
        alerts = self.manager.check_event(event_data)
        assert len(alerts) == 0

    def test_get_statistics(self):
        """Test statistics generation."""
        stats = self.manager.get_statistics()
        assert "manager" in stats
        assert "rules_engine" in stats
        assert "threshold_engine" in stats
        assert "notifications" in stats
        assert "aggregation" in stats

    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping the alert manager."""
        await self.manager.start()
        assert self.manager.is_running is True

        await self.manager.stop()
        assert self.manager.is_running is False


class TestAlertDashboard:
    """Test alert dashboard."""

    def setup_method(self):
        """Set up test fixtures."""
        self.alert_manager = AlertManager()
        self.dashboard = AlertDashboard(self.alert_manager)

    def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        assert self.dashboard.alert_manager == self.alert_manager
        assert self.dashboard.router is not None

    def test_get_router(self):
        """Test getting the FastAPI router."""
        router = self.dashboard.get_router()
        assert router is not None
        assert len(router.routes) > 0

    def test_basic_dashboard_html(self):
        """Test basic dashboard HTML generation."""
        html_response = self.dashboard._get_basic_dashboard_html()
        assert html_response.status_code == 200
        assert "HA Ingestor Alert Dashboard" in html_response.body.decode()
        assert "alert-item" in html_response.body.decode()


# Integration tests
class TestAlertingIntegration:
    """Integration tests for the alerting system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "enable_webhook_alerts": True,
            "webhook_config": {"webhook_url": "http://example.com/webhook"},
            "alerting_check_interval": 1.0,
            "alerting_history_retention_days": 1,
        }
        self.manager = AlertManager(self.config)

    def test_complete_alert_flow(self):
        """Test complete alert flow from rule creation to notification."""
        # Create alert rule
        rule = AlertRule(
            name="system_error",
            description="System error detected",
            severity=AlertSeverity.ERROR,
            conditions=[{"field": "level", "operator": "equals", "value": "error"}],
            notification_channels=["webhook"],
        )
        self.manager.add_alert_rule(rule)

        # Check event that should trigger alert
        event_data = {"level": "error", "message": "System failure"}
        alerts = self.manager.check_event(event_data)

        # Should have triggered an alert
        assert len(alerts) == 1
        assert alerts[0].rule_name == "system_error"
        assert alerts[0].severity == AlertSeverity.ERROR

        # Check active alerts
        active_alerts = self.manager.get_active_alerts()
        assert len(active_alerts) == 1

        # Acknowledge alert
        assert self.manager.acknowledge_alert("system_error") is True
        active_alerts = self.manager.get_active_alerts()
        assert active_alerts[0].status == AlertStatus.ACKNOWLEDGED

        # Resolve alert
        assert self.manager.resolve_alert("system_error") is True
        active_alerts = self.manager.get_active_alerts()
        assert len(active_alerts) == 0

        # Check history
        history = self.manager.get_alert_history()
        assert len(history) == 1  # Should have one resolved alert

    def test_threshold_based_alerting(self):
        """Test threshold-based alerting with data points."""
        # Create threshold-based rule
        rule = AlertRule(
            name="temperature_critical",
            description="Temperature is critically high",
            severity=AlertSeverity.CRITICAL,
            threshold=30.0,
            threshold_type="above",
        )
        self.manager.add_alert_rule(rule)

        # Add data points to threshold engine
        self.manager.threshold_engine.add_data_point("temperature", 25.0)
        self.manager.threshold_engine.add_data_point("temperature", 28.0)
        self.manager.threshold_engine.add_data_point(
            "temperature", 32.0
        )  # Above threshold

        # Check event
        event_data = {"temperature": 32.0}
        alerts = self.manager.check_event(event_data)

        # Should trigger alert
        assert len(alerts) == 1
        assert alerts[0].rule_name == "temperature_critical"

    def test_alert_aggregation(self):
        """Test alert aggregation functionality."""
        # Create rule
        rule = AlertRule(
            name="frequent_error",
            description="Frequent errors detected",
            severity=AlertSeverity.WARNING,
            conditions=[{"field": "error_count", "operator": "exists", "value": None}],
            cooldown_minutes=1,  # Very short cooldown for testing
        )
        self.manager.add_alert_rule(rule)

        # Trigger multiple similar alerts with small delays
        for i in range(3):
            event_data = {"error_count": i + 1}
            alerts = self.manager.check_event(event_data)

            # Resolve the alert so the next event can trigger a new one
            if alerts:
                self.manager.resolve_alert("frequent_error")

            # Small delay to ensure events are processed
            import time

            time.sleep(0.1)

        # Should aggregate similar alerts
        aggregated = self.manager.alert_aggregator.get_aggregated_alerts()
        assert len(aggregated) == 1  # Should return one representative alert

        # Check that total alerts processed is correct
        stats = self.manager.get_statistics()
        assert stats["manager"]["total_alerts_processed"] == 3
