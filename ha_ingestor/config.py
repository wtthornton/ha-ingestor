"""
Configuration management for Home Assistant Activity Ingestor.

AI ASSISTANT CONTEXT:
This module manages all configuration settings for the ha-ingestor service.
It uses Pydantic for validation and environment variable management.

Key patterns used:
- Pydantic BaseSettings for configuration management
- Environment variable overrides with validation
- Field validation with constraints and descriptions
- Configuration grouping by service (MQTT, WebSocket, InfluxDB, etc.)

Common modifications:
- Add new configuration options for new features
- Modify validation rules for existing fields
- Add new configuration sections for new services
- Update default values and constraints

Related files:
- .env: Environment variable template
- env.example: Example environment configuration
- ha_ingestor/main.py: Main application that uses these settings
- ha_ingestor/mqtt/: MQTT client that uses MQTT settings
- ha_ingestor/websocket/: WebSocket client that uses WebSocket settings
- ha_ingestor/influxdb/: InfluxDB client that uses InfluxDB settings

Environment Variables:
- All settings can be overridden via environment variables
- Use UPPER_SNAKE_CASE for environment variable names
- Example: HA_MQTT_HOST overrides ha_mqtt_host
"""

import logging
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Home Assistant MQTT Configuration
    ha_mqtt_host: str = Field(
        default="localhost",
        description="Home Assistant MQTT broker hostname or IP address",
    )
    ha_mqtt_port: int = Field(
        default=1883,
        ge=1,
        le=65535,
        description="Home Assistant MQTT broker port",
    )
    ha_mqtt_username: str | None = Field(
        default=None,
        description="MQTT broker username (if authentication is required)",
    )
    ha_mqtt_password: str | None = Field(
        default=None,
        description="MQTT broker password (if authentication is required)",
    )
    ha_mqtt_client_id: str = Field(
        default="ha-ingestor",
        description="MQTT client ID for this service",
    )
    ha_mqtt_keepalive: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="MQTT keepalive interval in seconds",
    )

    # Home Assistant WebSocket Configuration
    ha_ws_url: str = Field(
        default="ws://localhost:8123/api/websocket",
        description="Home Assistant WebSocket API URL",
    )
    ha_ws_token: str = Field(
        default="",
        description="Home Assistant long-lived access token",
    )
    ha_ws_heartbeat_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="WebSocket heartbeat interval in seconds",
    )

    # WebSocket Event Filtering Configuration
    ws_enable_event_filtering: bool = Field(
        default=True, description="Enable advanced WebSocket event type filtering"
    )
    ws_default_event_types: list[str] = Field(
        default=[
            "state_changed",
            "event",
            "service_registered",
            "service_removed",
            "component_loaded",
            "user_updated",
            "device_registry_updated",
            "entity_registry_updated",
        ],
        description="Default Home Assistant event types to subscribe to",
    )
    ws_event_filter_rules: dict[str, Any] = Field(
        default_factory=dict, description="Advanced event filtering rules and patterns"
    )
    ws_enable_event_patterns: bool = Field(
        default=False, description="Enable regex-based event type pattern matching"
    )
    ws_event_cache_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Event filtering cache size for performance",
    )
    ws_enable_event_statistics: bool = Field(
        default=True, description="Enable event type statistics and monitoring"
    )

    # InfluxDB Configuration
    influxdb_url: str = Field(
        default="http://localhost:8086",
        description="InfluxDB server URL",
    )
    influxdb_token: str = Field(
        default="",
        description="InfluxDB authentication token",
    )
    influxdb_org: str = Field(
        default="my-org",
        description="InfluxDB organization name",
    )
    influxdb_bucket: str = Field(
        default="home_assistant",
        description="InfluxDB bucket name for storing data",
    )
    influxdb_batch_size: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Number of points to batch before writing to InfluxDB",
    )
    influxdb_batch_timeout: float = Field(
        default=10.0,
        ge=0.1,
        le=300.0,
        description="Maximum time to wait before writing batch to InfluxDB (seconds)",
    )
    influxdb_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts for failed writes",
    )
    influxdb_retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Base delay between retry attempts (seconds)",
    )
    influxdb_retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Exponential backoff multiplier for retries",
    )
    influxdb_retry_jitter: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Jitter factor for retry delays (0.0 = no jitter, 0.5 = ±50%)",
    )
    influxdb_write_timeout: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="HTTP write timeout for InfluxDB requests (seconds)",
    )
    influxdb_connect_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="HTTP connection timeout for InfluxDB requests (seconds)",
    )
    influxdb_compression: str = Field(
        default="gzip",
        description="Compression algorithm for batch data (gzip, deflate, none)",
    )
    influxdb_compression_level: int = Field(
        default=6,
        ge=1,
        le=9,
        description="Compression level (1=fast, 9=best compression)",
    )
    influxdb_optimize_batches: bool = Field(
        default=True,
        description="Enable batch optimization (deduplication, sorting, etc.)",
    )

    # Schema Optimization Configuration
    influxdb_schema_optimization_enabled: bool = Field(
        default=True,
        description="Enable advanced InfluxDB schema optimization",
    )
    influxdb_max_tag_cardinality: int = Field(
        default=10000,
        ge=1000,
        le=100000,
        description="Maximum tag cardinality before optimization",
    )
    influxdb_tag_compression_threshold: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Tag value length threshold for compression",
    )
    influxdb_field_compression_threshold: int = Field(
        default=256,
        ge=64,
        le=1024,
        description="Field value length threshold for compression",
    )
    influxdb_measurement_consolidation: bool = Field(
        default=True,
        description="Enable measurement consolidation for better performance",
    )
    influxdb_auto_schema_evolution: bool = Field(
        default=True,
        description="Enable automatic schema evolution and optimization",
    )
    influxdb_schema_analysis_interval: float = Field(
        default=300.0,  # 5 minutes
        ge=60.0,
        le=3600.0,
        description="Schema analysis and optimization interval in seconds",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, console)",
    )
    log_file: str | None = Field(
        default=None,
        description="Log file path (if None, logs to console)",
    )
    log_max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="Maximum log file size in bytes before rotation",
    )
    log_backup_count: int = Field(
        default=5,
        description="Number of backup log files to keep",
    )

    # Service Configuration
    service_name: str = Field(
        default="ha-ingestor",
        description="Service name for logging and monitoring",
    )
    service_host: str = Field(
        default="0.0.0.0",
        description="Host to bind the service to",
    )
    service_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port to bind the service to",
    )

    # Monitoring Configuration
    monitoring_enabled: bool = Field(
        default=True,
        description="Enable enhanced monitoring and metrics collection",
    )
    monitoring_interval: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="Monitoring interval in seconds",
    )
    enable_system_metrics: bool = Field(
        default=True,
        description="Enable system resource utilization monitoring",
    )
    enable_performance_metrics: bool = Field(
        default=True,
        description="Enable performance-specific metrics collection",
    )
    enable_business_metrics: bool = Field(
        default=True,
        description="Enable business metrics for event processing",
    )
    enable_prometheus_integration: bool = Field(
        default=True,
        description="Enable Prometheus metrics integration",
    )
    metrics_sync_interval: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        description="Metrics synchronization interval in seconds",
    )

    # Alerting Configuration
    alerting_enabled: bool = Field(
        default=True,
        description="Enable alerting system",
    )
    alerting_check_interval: float = Field(
        default=15.0,
        ge=5.0,
        le=300.0,
        description="Alerting check interval in seconds",
    )
    alerting_history_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to retain alert history",
    )
    enable_email_alerts: bool = Field(
        default=False,
        description="Enable email-based alert notifications",
    )
    enable_webhook_alerts: bool = Field(
        default=True,
        description="Enable webhook-based alert notifications",
    )
    enable_slack_alerts: bool = Field(
        default=False,
        description="Enable Slack-based alert notifications",
    )
    enable_discord_alerts: bool = Field(
        default=False,
        description="Enable Discord-based alert notifications",
    )
    enable_pagerduty_alerts: bool = Field(
        default=False,
        description="Enable PagerDuty-based alert notifications",
    )
    alert_cooldown_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Minimum time between repeated alerts in minutes",
    )
    alert_aggregation_window_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Time window for aggregating similar alerts in minutes",
    )

    # Advanced MQTT Features (disabled by default for deployment)
    mqtt_enable_pattern_matching: bool = Field(
        default=False,
        description="Enable advanced MQTT topic pattern matching and wildcards",
    )
    mqtt_max_patterns: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Maximum number of topic patterns that can be registered",
    )
    mqtt_pattern_cache_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum size of pattern matching cache for performance",
    )
    mqtt_enable_dynamic_subscriptions: bool = Field(
        default=False, description="Enable dynamic topic subscription management"
    )
    mqtt_subscription_timeout: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Timeout for dynamic subscriptions in seconds",
    )
    mqtt_enable_topic_optimization: bool = Field(
        default=False, description="Enable automatic topic subscription optimization"
    )
    mqtt_topic_optimization_interval: int = Field(
        default=60,
        ge=30,
        le=300,
        description="Interval for topic optimization in seconds",
    )

    # Advanced MQTT Wildcard and Pattern Features
    mqtt_enable_advanced_wildcards: bool = Field(
        default=False,
        description="Enable advanced wildcard patterns beyond standard MQTT + and #",
    )
    mqtt_enable_regex_patterns: bool = Field(
        default=False, description="Enable regex-based topic pattern matching"
    )
    mqtt_enable_topic_aliases: bool = Field(
        default=False, description="Enable topic aliases for complex pattern matching"
    )
    mqtt_max_wildcard_depth: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum depth for multi-level wildcard patterns",
    )
    mqtt_enable_pattern_validation: bool = Field(
        default=True, description="Enable strict validation of topic patterns"
    )
    mqtt_pattern_priority_levels: int = Field(
        default=10,
        ge=5,
        le=100,
        description="Number of priority levels for topic patterns",
    )

    # MQTT Performance Configuration
    mqtt_max_reconnect_attempts: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of MQTT reconnection attempts",
    )
    mqtt_initial_reconnect_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Initial MQTT reconnection delay in seconds",
    )
    mqtt_max_reconnect_delay: float = Field(
        default=300.0,
        ge=60.0,
        le=1800.0,
        description="Maximum MQTT reconnection delay in seconds",
    )
    mqtt_reconnect_backoff_multiplier: float = Field(
        default=2.0,
        ge=1.1,
        le=5.0,
        description="MQTT reconnection backoff multiplier",
    )
    mqtt_reconnect_jitter: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="MQTT reconnection jitter factor (0-0.5)",
    )

    # Data Retention and Cleanup Configuration
    retention_enabled: bool = Field(
        default=True,
        description="Enable data retention and cleanup policies",
    )
    retention_cleanup_interval: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Retention cleanup interval in seconds (5 minutes to 24 hours)",
    )
    retention_max_cleanup_duration: int = Field(
        default=300,
        ge=60,
        le=1800,
        description="Maximum duration for cleanup operations in seconds (1-30 minutes)",
    )
    retention_max_concurrent_jobs: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum concurrent cleanup jobs",
    )
    retention_batch_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Batch size for cleanup operations",
    )
    retention_job_timeout: int = Field(
        default=300,
        ge=60,
        le=1800,
        description="Timeout for cleanup jobs in seconds (1-30 minutes)",
    )
    retention_retry_delay: int = Field(
        default=60,
        ge=30,
        le=300,
        description="Delay between retry attempts in seconds (30 seconds to 5 minutes)",
    )
    retention_enforce_immediately: bool = Field(
        default=False,
        description="Apply retention policies to existing data immediately",
    )
    retention_dry_run: bool = Field(
        default=False,
        description="Run retention cleanup in dry-run mode (no actual deletion)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate log format is one of the allowed values."""
        allowed_formats = ["json", "console"]
        if v.lower() not in allowed_formats:
            raise ValueError(f"log_format must be one of {allowed_formats}")
        return v.lower()

    @field_validator("ha_mqtt_host")
    @classmethod
    def validate_mqtt_host(cls, v: str) -> str:
        """Validate MQTT host is not empty."""
        if not v or not v.strip():
            raise ValueError("MQTT host cannot be empty")
        return v.strip()

    @field_validator("ha_ws_token")
    @classmethod
    def validate_ws_token(cls, v: str) -> str:
        """Validate WebSocket token is not empty."""
        if not v or not v.strip():
            raise ValueError("WebSocket token cannot be empty")
        return v.strip()

    @field_validator("influxdb_token")
    @classmethod
    def validate_influxdb_token(cls, v: str) -> str:
        """Validate InfluxDB token is not empty."""
        if not v or not v.strip():
            raise ValueError("InfluxDB token cannot be empty")
        return v.strip()

    @field_validator("influxdb_org")
    @classmethod
    def validate_influxdb_org(cls, v: str) -> str:
        """Validate InfluxDB organization is not empty."""
        if not v or not v.strip():
            raise ValueError("InfluxDB organization cannot be empty")
        return v.strip()

    @field_validator("ha_ws_url")
    @classmethod
    def validate_ws_url(cls, v: str) -> str:
        """Validate WebSocket URL format."""
        if not v or not v.strip():
            raise ValueError("WebSocket URL cannot be empty")

        v = v.strip()
        if not (v.startswith("ws://") or v.startswith("wss://")):
            raise ValueError("WebSocket URL must start with 'ws://' or 'wss://'")

        return v

    def get_log_level(self) -> int:
        """Get the logging level as an integer."""
        level = getattr(logging, self.log_level)
        if not isinstance(level, int):
            raise ValueError(f"Invalid log level: {self.log_level}")
        return level

    def is_mqtt_authenticated(self) -> bool:
        """Check if MQTT authentication is configured."""
        return bool(self.ha_mqtt_username and self.ha_mqtt_password)

    def get_mqtt_auth_dict(self) -> dict[str, str] | None:
        """Get MQTT authentication dictionary if configured."""
        if self.is_mqtt_authenticated():
            # We know these are not None because is_mqtt_authenticated() checks for them
            username = self.ha_mqtt_username
            password = self.ha_mqtt_password
            if username is not None and password is not None:
                return {
                    "username": username,
                    "password": password,
                }
        return None


# Global settings instance (lazy-loaded)
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global _settings
    _settings = Settings()
    return _settings


# Convenience alias
settings = get_settings
