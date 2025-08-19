"""Configuration management for Home Assistant Activity Ingestor."""

import logging
from typing import Optional, Union
from pydantic import Field, field_validator, HttpUrl, AnyUrl
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
    ha_mqtt_username: Optional[str] = Field(
        default=None,
        description="MQTT broker username (if authentication is required)",
    )
    ha_mqtt_password: Optional[str] = Field(
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
        description="Home Assistant WebSocket API URL",
    )
    ha_ws_token: str = Field(
        description="Home Assistant long-lived access token",
    )
    ha_ws_heartbeat_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="WebSocket heartbeat interval in seconds",
    )

    # InfluxDB Configuration
    influxdb_url: HttpUrl = Field(
        description="InfluxDB server URL",
    )
    influxdb_token: str = Field(
        description="InfluxDB authentication token",
    )
    influxdb_org: str = Field(
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

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json, console)",
    )
    log_file: Optional[str] = Field(
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
        return getattr(logging, self.log_level)

    def is_mqtt_authenticated(self) -> bool:
        """Check if MQTT authentication is configured."""
        return bool(self.ha_mqtt_username and self.ha_mqtt_password)

    def get_mqtt_auth_dict(self) -> Optional[dict]:
        """Get MQTT authentication dictionary if configured."""
        if self.is_mqtt_authenticated():
            return {
                "username": self.ha_mqtt_username,
                "password": self.ha_mqtt_password,
            }
        return None


# Global settings instance (lazy-loaded)
_settings: Optional[Settings] = None


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
