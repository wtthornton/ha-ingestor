"""Core retention policy definitions and enums."""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum


class RetentionPeriod(Enum):
    """Standard retention periods."""

    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    INDEFINITE = "indefinite"

    def to_timedelta(self) -> timedelta:
        """Convert retention period to timedelta."""
        if self == RetentionPeriod.INDEFINITE:
            return timedelta.max

        period_map = {
            RetentionPeriod.ONE_DAY: timedelta(days=1),
            RetentionPeriod.ONE_WEEK: timedelta(weeks=1),
            RetentionPeriod.ONE_MONTH: timedelta(days=30),
            RetentionPeriod.THREE_MONTHS: timedelta(days=90),
            RetentionPeriod.SIX_MONTHS: timedelta(days=180),
            RetentionPeriod.ONE_YEAR: timedelta(days=365),
            RetentionPeriod.TWO_YEARS: timedelta(days=730),
            RetentionPeriod.FIVE_YEARS: timedelta(days=1825),
        }

        return period_map.get(self, timedelta(days=30))


class CompressionLevel(Enum):
    """Data compression levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"

    def get_compression_ratio(self) -> float:
        """Get expected compression ratio for this level."""
        ratio_map = {
            CompressionLevel.NONE: 1.0,
            CompressionLevel.LOW: 0.8,
            CompressionLevel.MEDIUM: 0.6,
            CompressionLevel.HIGH: 0.4,
            CompressionLevel.MAXIMUM: 0.2,
        }
        return ratio_map.get(self, 1.0)


class DataType(Enum):
    """Types of data for retention policies."""

    # Home Assistant events
    HA_EVENTS = "ha_events"
    HA_STATES = "ha_states"
    HA_LOGS = "ha_logs"

    # System metrics
    SYSTEM_METRICS = "system_metrics"
    PERFORMANCE_METRICS = "performance_metrics"
    BUSINESS_METRICS = "business_metrics"

    # Application data
    ALERTS = "alerts"
    ALERT_HISTORY = "alert_history"
    DASHBOARD_DATA = "dashboard_data"

    # Connection data
    CONNECTION_LOGS = "connection_logs"
    ERROR_LOGS = "error_logs"
    ACCESS_LOGS = "access_logs"

    # Raw data
    MQTT_MESSAGES = "mqtt_messages"
    WEBSOCKET_EVENTS = "websocket_events"
    INFLUXDB_POINTS = "influxdb_points"


class ArchivalStrategy(Enum):
    """Data archival strategies."""

    DELETE = "delete"  # Simply delete old data
    COMPRESS = "compress"  # Compress old data in place
    ARCHIVE = "archive"  # Move to archival storage
    SAMPLE = "sample"  # Keep only samples of old data
    AGGREGATE = "aggregate"  # Aggregate old data into summaries


@dataclass
class RetentionPolicy:
    """Configuration for data retention policy."""

    name: str
    data_type: DataType
    retention_period: RetentionPeriod
    archival_strategy: ArchivalStrategy
    compression_level: CompressionLevel = CompressionLevel.MEDIUM

    # Optional configurations
    min_data_points: int | None = None  # Minimum points to keep
    max_data_points: int | None = None  # Maximum points to keep
    sampling_rate: float | None = None  # For sampling strategy (0.0-1.0)
    aggregation_interval: timedelta | None = None  # For aggregation strategy

    # Policy enforcement
    enabled: bool = True
    enforce_immediately: bool = False  # Apply to existing data
    dry_run: bool = False  # Don't actually delete/archive

    # Monitoring and alerting
    alert_on_violation: bool = True
    alert_threshold: float = 0.9  # Alert when 90% of retention period reached

    # Metadata
    description: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        """Validate policy configuration."""
        if self.sampling_rate is not None and not (0.0 <= self.sampling_rate <= 1.0):
            raise ValueError("sampling_rate must be between 0.0 and 1.0")

        if self.alert_threshold <= 0.0 or self.alert_threshold > 1.0:
            raise ValueError("alert_threshold must be between 0.0 and 1.0")

    def get_retention_days(self) -> int:
        """Get retention period in days."""
        return self.retention_period.to_timedelta().days

    def should_archive(self, data_age: timedelta) -> bool:
        """Check if data should be archived based on age."""
        return data_age >= self.retention_period.to_timedelta()

    def should_alert(self, data_age: timedelta) -> bool:
        """Check if alert should be triggered."""
        retention_delta = self.retention_period.to_timedelta()
        threshold_delta = retention_delta * self.alert_threshold
        return data_age >= threshold_delta

    def get_estimated_storage_savings(self, current_size_mb: float) -> float:
        """Estimate storage savings from this policy."""
        if self.archival_strategy == ArchivalStrategy.DELETE:
            return current_size_mb

        compression_ratio = self.compression_level.get_compression_ratio()
        if self.archival_strategy == ArchivalStrategy.COMPRESS:
            return current_size_mb * (1.0 - compression_ratio)

        if self.archival_strategy == ArchivalStrategy.SAMPLE and self.sampling_rate:
            return current_size_mb * (1.0 - self.sampling_rate)

        if self.archival_strategy == ArchivalStrategy.AGGREGATE:
            # Assume aggregation reduces data by 80%
            return current_size_mb * 0.8

        return 0.0


@dataclass
class RetentionPolicySummary:
    """Summary of retention policy status."""

    policy_name: str
    data_type: DataType
    total_records: int
    records_to_archive: int
    records_archived: int
    storage_saved_mb: float
    last_cleanup: str | None = None
    next_cleanup: str | None = None
    status: str = "active"  # active, paused, error
    error_count: int = 0
    last_error: str | None = None


@dataclass
class RetentionStatistics:
    """Overall retention system statistics."""

    total_policies: int
    active_policies: int
    total_storage_saved_mb: float
    total_records_archived: int
    cleanup_jobs_run: int
    last_cleanup_run: str | None = None
    next_scheduled_cleanup: str | None = None
    system_status: str = "healthy"  # healthy, warning, error
