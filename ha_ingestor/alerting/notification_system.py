"""Notification system for alerting channels."""

import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

import aiohttp

from ..utils.logging import get_logger
from .rules_engine import AlertInstance, AlertSeverity


class NotificationChannel(Enum):
    """Supported notification channels."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    PAGERDUTY = "pagerduty"


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""

    channel: NotificationChannel
    enabled: bool = True
    name: str = ""
    config: dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize default config."""
        if self.config is None:
            self.config = {}


@dataclass
class NotificationMessage:
    """A notification message to be sent."""

    title: str
    body: str
    severity: AlertSeverity
    alert_instance: AlertInstance
    channel: NotificationChannel
    metadata: dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize default metadata."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "title": self.title,
            "body": self.body,
            "severity": self.severity.value,
            "alert_instance": self.alert_instance.to_dict(),
            "channel": self.channel.value,
            "metadata": self.metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }


class AlertNotifier(ABC):
    """Base class for alert notifiers."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize the notifier."""
        self.config = config
        self.logger = get_logger(__name__)
        self.success_count = 0
        self.failure_count = 0
        self.last_success = None
        self.last_failure = None

    @abstractmethod
    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send a notification message."""
        pass

    def get_statistics(self) -> dict[str, Any]:
        """Get notifier statistics."""
        return {
            "channel": self.config.channel.value,
            "enabled": self.config.enabled,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_success": (
                self.last_success.isoformat() if self.last_success else None
            ),
            "last_failure": (
                self.last_failure.isoformat() if self.last_failure else None
            ),
        }


class EmailNotifier(AlertNotifier):
    """Email-based alert notifier."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize email notifier."""
        super().__init__(config)
        self.smtp_host = config.config.get("smtp_host", "localhost")
        self.smtp_port = config.config.get("smtp_port", 587)
        self.smtp_username = config.config.get("smtp_username")
        self.smtp_password = config.config.get("smtp_password")
        self.smtp_use_tls = config.config.get("smtp_use_tls", True)
        self.from_email = config.config.get("from_email", "alerts@ha-ingestor.local")
        self.to_emails = config.config.get("to_emails", [])

    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send email notification."""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = f"[{message.severity.value.upper()}] {message.title}"

            # Create HTML body
            html_body = self._create_html_body(message)
            msg.attach(MIMEText(html_body, "html"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()

                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            self.success_count += 1
            self.last_success = datetime.utcnow()
            self.logger.info(
                f"Email notification sent successfully to {len(self.to_emails)} recipients"
            )
            return True

        except Exception as e:
            self.failure_count += 1
            self.last_failure = datetime.utcnow()
            self.logger.error(f"Failed to send email notification: {e}")
            return False

    def _create_html_body(self, message: NotificationMessage) -> str:
        """Create HTML email body."""
        severity_color = {
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#dc3545",
            AlertSeverity.CRITICAL: "#721c24",
        }.get(message.severity, "#6c757d")

        return f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: {severity_color}; color: white; padding: 20px; text-align: center;">
                    <h1>{message.title}</h1>
                    <p style="margin: 0; font-size: 18px;">{message.severity.value.upper()}</p>
                </div>

                <div style="padding: 20px; background-color: #f8f9fa;">
                    <p style="font-size: 16px; line-height: 1.6;">{message.body}</p>

                    <div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 20px;">
                        <h3>Alert Details</h3>
                        <p><strong>Rule:</strong> {message.alert_instance.rule_name}</p>
                        <p><strong>Triggered:</strong> {message.alert_instance.triggered_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <p><strong>Status:</strong> {message.alert_instance.status.value}</p>
                    </div>

                    <div style="margin-top: 20px; padding: 15px; background-color: #e9ecef; border-radius: 5px;">
                        <p style="margin: 0; font-size: 14px; color: #6c757d;">
                            This alert was sent by HA Ingestor at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """


class WebhookNotifier(AlertNotifier):
    """Webhook-based alert notifier."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize webhook notifier."""
        super().__init__(config)
        self.webhook_url = config.config.get("webhook_url")
        self.webhook_method = config.config.get("webhook_method", "POST")
        self.webhook_headers = config.config.get("webhook_headers", {})
        self.webhook_timeout = config.config.get("webhook_timeout", 30)

    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send webhook notification."""
        if not self.webhook_url:
            self.logger.error("Webhook URL not configured")
            return False

        try:
            payload = message.to_dict()

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.webhook_method,
                    url=self.webhook_url,
                    json=payload,
                    headers=self.webhook_headers,
                    timeout=aiohttp.ClientTimeout(total=self.webhook_timeout),
                ) as response:
                    if response.status in [200, 201, 202]:
                        self.success_count += 1
                        self.last_success = datetime.utcnow()
                        self.logger.info(
                            f"Webhook notification sent successfully to {self.webhook_url}"
                        )
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

        except Exception as e:
            self.failure_count += 1
            self.last_failure = datetime.utcnow()
            self.logger.error(f"Failed to send webhook notification: {e}")
            return False


class SlackNotifier(AlertNotifier):
    """Slack-based alert notifier."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize Slack notifier."""
        super().__init__(config)
        self.webhook_url = config.config.get("webhook_url")
        self.channel = config.config.get("channel", "#alerts")
        self.username = config.config.get("username", "HA Ingestor")
        self.icon_emoji = config.config.get("icon_emoji", ":warning:")

    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send Slack notification."""
        if not self.webhook_url:
            self.logger.error("Slack webhook URL not configured")
            return False

        try:
            # Create Slack message
            slack_message = {
                "channel": self.channel,
                "username": self.username,
                "icon_emoji": self.icon_emoji,
                "attachments": [
                    {
                        "color": self._get_severity_color(message.severity),
                        "title": message.title,
                        "text": message.body,
                        "fields": [
                            {
                                "title": "Rule",
                                "value": message.alert_instance.rule_name,
                                "short": True,
                            },
                            {
                                "title": "Severity",
                                "value": message.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Status",
                                "value": message.alert_instance.status.value,
                                "short": True,
                            },
                            {
                                "title": "Triggered",
                                "value": message.alert_instance.triggered_at.strftime(
                                    "%Y-%m-%d %H:%M:%S UTC"
                                ),
                                "short": True,
                            },
                        ],
                        "footer": "HA Ingestor",
                        "ts": int(datetime.utcnow().timestamp()),
                    }
                ],
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        self.success_count += 1
                        self.last_success = datetime.utcnow()
                        self.logger.info(
                            f"Slack notification sent successfully to {self.channel}"
                        )
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

        except Exception as e:
            self.failure_count += 1
            self.last_failure = datetime.utcnow()
            self.logger.error(f"Failed to send Slack notification: {e}")
            return False

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get Slack color for severity level."""
        return {
            AlertSeverity.INFO: "#17a2b8",
            AlertSeverity.WARNING: "#ffc107",
            AlertSeverity.ERROR: "#dc3545",
            AlertSeverity.CRITICAL: "#721c24",
        }.get(severity, "#6c757d")


class DiscordNotifier(AlertNotifier):
    """Discord-based alert notifier."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize Discord notifier."""
        super().__init__(config)
        self.webhook_url = config.config.get("webhook_url")
        self.username = config.config.get("username", "HA Ingestor")
        self.avatar_url = config.config.get("avatar_url")

    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send Discord notification."""
        if not self.webhook_url:
            self.logger.error("Discord webhook URL not configured")
            return False

        try:
            # Create Discord embed
            embed = {
                "title": message.title,
                "description": message.body,
                "color": self._get_severity_color(message.severity),
                "fields": [
                    {
                        "name": "Rule",
                        "value": message.alert_instance.rule_name,
                        "inline": True,
                    },
                    {
                        "name": "Severity",
                        "value": message.severity.value.upper(),
                        "inline": True,
                    },
                    {
                        "name": "Status",
                        "value": message.alert_instance.status.value,
                        "inline": True,
                    },
                    {
                        "name": "Triggered",
                        "value": message.alert_instance.triggered_at.strftime(
                            "%Y-%m-%d %H:%M:%S UTC"
                        ),
                        "inline": True,
                    },
                ],
                "footer": {"text": "HA Ingestor"},
                "timestamp": datetime.utcnow().isoformat(),
            }

            discord_message = {"username": self.username, "embeds": [embed]}

            if self.avatar_url:
                discord_message["avatar_url"] = self.avatar_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=discord_message,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status in [200, 204]:
                        self.success_count += 1
                        self.last_success = datetime.utcnow()
                        self.logger.info("Discord notification sent successfully")
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

        except Exception as e:
            self.failure_count += 1
            self.last_failure = datetime.utcnow()
            self.logger.error(f"Failed to send Discord notification: {e}")
            return False

    def _get_severity_color(self, severity: AlertSeverity) -> int:
        """Get Discord color for severity level."""
        return {
            AlertSeverity.INFO: 0x17A2B8,
            AlertSeverity.WARNING: 0xFFC107,
            AlertSeverity.ERROR: 0xDC3545,
            AlertSeverity.CRITICAL: 0x721C24,
        }.get(severity, 0x6C757D)


class PagerDutyNotifier(AlertNotifier):
    """PagerDuty-based alert notifier."""

    def __init__(self, config: NotificationConfig) -> None:
        """Initialize PagerDuty notifier."""
        super().__init__(config)
        self.api_key = config.config.get("api_key")
        self.service_id = config.config.get("service_id")
        self.escalation_policy_id = config.config.get("escalation_policy_id")
        self.api_url = "https://api.pagerduty.com/incidents"

    async def send_notification(self, message: NotificationMessage) -> bool:
        """Send PagerDuty notification."""
        if not all([self.api_key, self.service_id]):
            self.logger.error("PagerDuty API key or service ID not configured")
            return False

        try:
            # Create PagerDuty incident
            incident_data = {
                "incident": {
                    "type": "incident",
                    "title": message.title,
                    "service": {"id": self.service_id, "type": "service_reference"},
                    "urgency": (
                        "high"
                        if message.severity
                        in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]
                        else "low"
                    ),
                    "body": {"type": "incident_body", "details": message.body},
                    "incident_key": f"ha-ingestor-{message.alert_instance.rule_name}-{int(datetime.utcnow().timestamp())}",
                }
            }

            if self.escalation_policy_id:
                incident_data["incident"]["escalation_policy"] = {
                    "id": self.escalation_policy_id,
                    "type": "escalation_policy_reference",
                }

            headers = {
                "Authorization": f"Token token={self.api_key}",
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Content-Type": "application/json",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=incident_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 201:
                        self.success_count += 1
                        self.last_success = datetime.utcnow()
                        self.logger.info("PagerDuty incident created successfully")
                        return True
                    else:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

        except Exception as e:
            self.failure_count += 1
            self.last_failure = datetime.utcnow()
            self.logger.error(f"Failed to create PagerDuty incident: {e}")
            return False


def create_notifier(config: NotificationConfig) -> AlertNotifier:
    """Factory function to create the appropriate notifier."""
    if config.channel == NotificationChannel.EMAIL:
        return EmailNotifier(config)
    elif config.channel == NotificationChannel.WEBHOOK:
        return WebhookNotifier(config)
    elif config.channel == NotificationChannel.SLACK:
        return SlackNotifier(config)
    elif config.channel == NotificationChannel.DISCORD:
        return DiscordNotifier(config)
    elif config.channel == NotificationChannel.PAGERDUTY:
        return PagerDutyNotifier(config)
    else:
        raise ValueError(f"Unsupported notification channel: {config.channel}")
