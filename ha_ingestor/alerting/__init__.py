"""Alerting system for Home Assistant Activity Ingestor."""

from .alert_manager import AlertAggregator, AlertHistory, AlertManager
from .dashboard import AlertDashboard
from .notification_system import (
    AlertNotifier,
    DiscordNotifier,
    EmailNotifier,
    NotificationChannel,
    PagerDutyNotifier,
    SlackNotifier,
    WebhookNotifier,
)
from .performance_alerts import (
    PerformanceAlertEngine,
    PerformanceAlertInstance,
    PerformanceAlertRule,
    get_performance_alert_engine,
    set_performance_alert_engine,
)
from .rules_engine import AlertRule, AlertRulesEngine, AlertSeverity, AlertStatus
from .threshold_engine import ThresholdCondition, ThresholdEngine, ThresholdType

__all__ = [
    # Core alerting
    "AlertRule",
    "AlertRulesEngine",
    "AlertSeverity",
    "AlertStatus",
    # Threshold engine
    "ThresholdEngine",
    "ThresholdCondition",
    "ThresholdType",
    # Notification system
    "AlertNotifier",
    "EmailNotifier",
    "WebhookNotifier",
    "SlackNotifier",
    "DiscordNotifier",
    "PagerDutyNotifier",
    "NotificationChannel",
    # Alert management
    "AlertManager",
    "AlertHistory",
    "AlertAggregator",
    # Dashboard
    "AlertDashboard",
    # Performance alerting
    "PerformanceAlertEngine",
    "PerformanceAlertInstance",
    "PerformanceAlertRule",
    "get_performance_alert_engine",
    "set_performance_alert_engine",
]
