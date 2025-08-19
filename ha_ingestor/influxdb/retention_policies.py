"""Data retention policies and compression strategies for InfluxDB.

This module implements configurable retention periods, data compression,
and archival strategies for the optimized InfluxDB schema.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from ..models.optimized_schema import OptimizedInfluxDBPoint


class RetentionPeriod(Enum):
    """Retention period options for different data types."""

    REAL_TIME = "1d"  # 1 day - high precision, no compression
    RECENT = "7d"  # 7 days - medium precision, light compression
    HISTORICAL = "30d"  # 30 days - low precision, heavy compression
    LONG_TERM = "1y"  # 1 year - aggregated data, maximum compression
    ARCHIVE = "infinite"  # Infinite - external storage


class CompressionLevel(Enum):
    """Compression level options for different retention periods."""

    NONE = 0  # No compression
    LIGHT = 1  # Fast compression (GZIP level 1)
    BALANCED = 6  # Balanced compression (GZIP level 6)
    MAXIMUM = 9  # Maximum compression (GZIP level 9)


@dataclass
class RetentionPolicy:
    """Configuration for a retention policy."""

    name: str
    duration: RetentionPeriod
    replication: int = 1
    default: bool = False
    compression_level: CompressionLevel = CompressionLevel.NONE
    shard_duration: str = "1d"
    hot_duration: str = "1d"
    warm_duration: str = "7d"
    cold_duration: str = "30d"

    # Data processing rules
    aggregate_data: bool = False
    aggregate_interval: str = "1h"
    drop_measurements: list[str] = field(default_factory=list)
    keep_measurements: list[str] = field(default_factory=list)

    # Compression settings
    enable_compression: bool = True
    compression_algorithm: str = "gzip"
    compression_threshold: int = 1024  # bytes

    def __post_init__(self):
        """Validate and set default values."""
        if self.duration == RetentionPeriod.REAL_TIME:
            self.compression_level = CompressionLevel.NONE
            self.aggregate_data = False
        elif self.duration == RetentionPeriod.RECENT:
            self.compression_level = CompressionLevel.LIGHT
            self.aggregate_data = False
        elif self.duration == RetentionPeriod.HISTORICAL:
            self.compression_level = CompressionLevel.BALANCED
            self.aggregate_data = True
        elif self.duration == RetentionPeriod.LONG_TERM:
            self.compression_level = CompressionLevel.MAXIMUM
            self.aggregate_data = True
        elif self.duration == RetentionPeriod.ARCHIVE:
            self.compression_level = CompressionLevel.MAXIMUM
            self.aggregate_data = True


class RetentionPolicyManager:
    """Manages retention policies and data lifecycle."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize retention policy manager.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Default retention policies
        self.policies = self._create_default_policies()

        # Policy enforcement settings
        self.enforce_retention = self.config.get("enforce_retention", True)
        self.auto_cleanup = self.config.get("auto_cleanup", True)
        self.cleanup_interval = timedelta(
            hours=self.config.get("cleanup_interval_hours", 24)
        )

        # Last cleanup time
        self.last_cleanup = datetime.utcnow()

        # Statistics
        self.cleanup_stats = {
            "total_cleanups": 0,
            "total_data_removed": 0,
            "last_cleanup_duration": 0,
            "policy_violations": 0,
        }

    def _create_default_policies(self) -> dict[str, RetentionPolicy]:
        """Create default retention policies."""
        policies = {}

        # Real-time data (1 day)
        policies["real_time"] = RetentionPolicy(
            name="real_time",
            duration=RetentionPeriod.REAL_TIME,
            default=True,
            compression_level=CompressionLevel.NONE,
            shard_duration="1h",
            hot_duration="1d",
        )

        # Recent data (7 days)
        policies["recent"] = RetentionPolicy(
            name="recent",
            duration=RetentionPeriod.RECENT,
            compression_level=CompressionLevel.LIGHT,
            shard_duration="6h",
            hot_duration="1d",
            warm_duration="7d",
        )

        # Historical data (30 days)
        policies["historical"] = RetentionPolicy(
            name="historical",
            duration=RetentionPeriod.HISTORICAL,
            compression_level=CompressionLevel.BALANCED,
            shard_duration="1d",
            hot_duration="1d",
            warm_duration="7d",
            cold_duration="30d",
            aggregate_data=True,
            aggregate_interval="1h",
        )

        # Long-term data (1 year)
        policies["long_term"] = RetentionPolicy(
            name="long_term",
            duration=RetentionPeriod.LONG_TERM,
            compression_level=CompressionLevel.MAXIMUM,
            shard_duration="7d",
            hot_duration="7d",
            warm_duration="30d",
            cold_duration="1y",
            aggregate_data=True,
            aggregate_interval="1d",
        )

        # Archive data (infinite)
        policies["archive"] = RetentionPolicy(
            name="archive",
            duration=RetentionPeriod.ARCHIVE,
            compression_level=CompressionLevel.MAXIMUM,
            shard_duration="30d",
            hot_duration="30d",
            warm_duration="1y",
            cold_duration="infinite",
            aggregate_data=True,
            aggregate_interval="7d",
        )

        return policies

    def get_policy_for_point(self, point: OptimizedInfluxDBPoint) -> RetentionPolicy:
        """Get appropriate retention policy for a data point.

        Args:
            point: Data point to get policy for

        Returns:
            Retention policy to apply
        """
        # Determine policy based on measurement and tags
        measurement = point.measurement

        # Special measurements get specific policies
        if measurement == "ha_metrics":
            return self.policies["long_term"]  # Keep metrics longer
        elif measurement == "ha_system":
            return self.policies["archive"]  # Keep system events forever
        elif measurement in ["ha_automations", "ha_services"]:
            return self.policies["historical"]  # Keep for 30 days

        # Default to recent policy for most data
        return self.policies["recent"]

    def should_aggregate_point(
        self, point: OptimizedInfluxDBPoint, policy: RetentionPolicy
    ) -> bool:
        """Determine if a point should be aggregated.

        Args:
            point: Data point to check
            policy: Retention policy to apply

        Returns:
            True if point should be aggregated
        """
        if not policy.aggregate_data:
            return False

        # Check if point is old enough for aggregation
        point_age = datetime.utcnow() - point.timestamp

        if policy.duration == RetentionPeriod.HISTORICAL:
            return point_age > timedelta(days=7)
        elif policy.duration == RetentionPeriod.LONG_TERM:
            return point_age > timedelta(days=30)
        elif policy.duration == RetentionPeriod.ARCHIVE:
            return point_age > timedelta(days=365)

        return False

    def get_aggregation_interval(self, policy: RetentionPolicy) -> str:
        """Get aggregation interval for a policy.

        Args:
            policy: Retention policy

        Returns:
            Aggregation interval string
        """
        return policy.aggregate_interval

    def should_compress_point(
        self, point: OptimizedInfluxDBPoint, policy: RetentionPolicy
    ) -> bool:
        """Determine if a point should be compressed.

        Args:
            point: Data point to check
            policy: Retention policy to apply

        Returns:
            True if point should be compressed
        """
        if not policy.enable_compression:
            return False

        # Check if point size exceeds compression threshold
        point_size = point.get_size_estimate()
        return point_size > policy.compression_threshold

    def get_compression_settings(self, policy: RetentionPolicy) -> dict[str, Any]:
        """Get compression settings for a policy.

        Args:
            policy: Retention policy

        Returns:
            Compression settings dictionary
        """
        return {
            "algorithm": policy.compression_algorithm,
            "level": policy.compression_level.value,
            "threshold": policy.compression_threshold,
            "enabled": policy.enable_compression,
        }

    def check_retention_violations(
        self, points: list[OptimizedInfluxDBPoint]
    ) -> list[dict[str, Any]]:
        """Check for retention policy violations.

        Args:
            points: List of data points to check

        Returns:
            List of violation details
        """
        violations = []
        current_time = datetime.utcnow()

        for point in points:
            policy = self.get_policy_for_point(point)
            point_age = current_time - point.timestamp

            # Check if point exceeds retention period
            if self._is_retention_violation(point_age, policy.duration):
                violations.append(
                    {
                        "point_id": id(point),
                        "measurement": point.measurement,
                        "timestamp": point.timestamp.isoformat(),
                        "age_days": point_age.days,
                        "policy": policy.name,
                        "max_retention": policy.duration.value,
                        "violation_type": "retention_exceeded",
                    }
                )

        # Update statistics
        if violations:
            self.cleanup_stats["policy_violations"] += len(violations)

        return violations

    def _is_retention_violation(
        self, age: timedelta, retention: RetentionPeriod
    ) -> bool:
        """Check if data age violates retention policy.

        Args:
            age: Age of the data
            retention: Retention period

        Returns:
            True if retention is violated
        """
        if retention == RetentionPeriod.ARCHIVE:
            return False  # Archive data never expires

        max_age = self._get_max_age_for_retention(retention)
        return age > max_age

    def _get_max_age_for_retention(self, retention: RetentionPeriod) -> timedelta:
        """Get maximum age for a retention period.

        Args:
            retention: Retention period

        Returns:
            Maximum age as timedelta
        """
        if retention == RetentionPeriod.REAL_TIME:
            return timedelta(days=1)
        elif retention == RetentionPeriod.RECENT:
            return timedelta(days=7)
        elif retention == RetentionPeriod.HISTORICAL:
            return timedelta(days=30)
        elif retention == RetentionPeriod.LONG_TERM:
            return timedelta(days=365)
        else:
            return timedelta.max  # Infinite

    def cleanup_expired_data(self, force: bool = False) -> dict[str, Any]:
        """Clean up expired data based on retention policies.

        Args:
            force: Force cleanup even if not due

        Returns:
            Cleanup results
        """
        current_time = datetime.utcnow()

        # Check if cleanup is due
        if not force and (current_time - self.last_cleanup) < self.cleanup_interval:
            return {
                "cleanup_performed": False,
                "reason": "cleanup_not_due",
                "next_cleanup": (self.last_cleanup + self.cleanup_interval).isoformat(),
            }

        start_time = datetime.utcnow()

        try:
            # Perform cleanup operations
            cleanup_results = self._perform_cleanup()

            # Update statistics
            cleanup_duration = (datetime.utcnow() - start_time).total_seconds()
            self.cleanup_stats["total_cleanups"] += 1
            self.cleanup_stats["last_cleanup_duration"] = cleanup_duration
            self.last_cleanup = current_time

            self.logger.info(
                "Data cleanup completed",
                duration_seconds=cleanup_duration,
                results=cleanup_results,
            )

            return {
                "cleanup_performed": True,
                "duration_seconds": cleanup_duration,
                "results": cleanup_results,
                "statistics": self.cleanup_stats,
            }

        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
            return {
                "cleanup_performed": False,
                "error": str(e),
                "statistics": self.cleanup_stats,
            }

    def _perform_cleanup(self) -> dict[str, Any]:
        """Perform actual cleanup operations.

        Returns:
            Cleanup operation results
        """
        # This would integrate with InfluxDB to actually remove expired data
        # For now, we'll simulate the cleanup process

        cleanup_results = {
            "policies_processed": 0,
            "data_points_removed": 0,
            "storage_freed_bytes": 0,
            "errors": [],
        }

        for policy_name, policy in self.policies.items():
            try:
                # Simulate cleanup for each policy
                cleanup_results["policies_processed"] += 1

                # In a real implementation, this would:
                # 1. Query InfluxDB for expired data
                # 2. Remove expired data points
                # 3. Update statistics

                self.logger.debug(f"Processed retention policy: {policy_name}")

            except Exception as e:
                cleanup_results["errors"].append(f"Policy {policy_name}: {str(e)}")

        return cleanup_results

    def get_retention_summary(self) -> dict[str, Any]:
        """Get summary of retention policies and statistics.

        Returns:
            Retention summary dictionary
        """
        return {
            "policies": {
                name: {
                    "duration": policy.duration.value,
                    "compression_level": policy.compression_level.value,
                    "aggregate_data": policy.aggregate_data,
                    "aggregate_interval": policy.aggregate_interval,
                    "enable_compression": policy.enable_compression,
                }
                for name, policy in self.policies.items()
            },
            "enforcement": {
                "enforce_retention": self.enforce_retention,
                "auto_cleanup": self.auto_cleanup,
                "cleanup_interval_hours": self.cleanup_interval.total_seconds() / 3600,
            },
            "statistics": self.cleanup_stats,
            "last_cleanup": self.last_cleanup.isoformat(),
            "next_cleanup": (self.last_cleanup + self.cleanup_interval).isoformat(),
        }

    def update_policy(self, policy_name: str, updates: dict[str, Any]) -> bool:
        """Update a retention policy.

        Args:
            policy_name: Name of policy to update
            updates: Dictionary of updates to apply

        Returns:
            True if update was successful
        """
        if policy_name not in self.policies:
            self.logger.error(f"Policy not found: {policy_name}")
            return False

        try:
            policy = self.policies[policy_name]

            # Apply updates
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)

            # Re-validate policy
            policy.__post_init__()

            self.logger.info(f"Updated retention policy: {policy_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to update policy {policy_name}: {e}")
            return False

    def add_custom_policy(self, policy: RetentionPolicy) -> bool:
        """Add a custom retention policy.

        Args:
            policy: Custom retention policy to add

        Returns:
            True if policy was added successfully
        """
        try:
            # Validate policy
            policy.__post_init__()

            # Add to policies
            self.policies[policy.name] = policy

            self.logger.info(f"Added custom retention policy: {policy.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add custom policy: {e}")
            return False

    def remove_policy(self, policy_name: str) -> bool:
        """Remove a retention policy.

        Args:
            policy_name: Name of policy to remove

        Returns:
            True if policy was removed successfully
        """
        if policy_name not in self.policies:
            self.logger.error(f"Policy not found: {policy_name}")
            return False

        if self.policies[policy_name].default:
            self.logger.error(f"Cannot remove default policy: {policy_name}")
            return False

        try:
            del self.policies[policy_name]
            self.logger.info(f"Removed retention policy: {policy_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove policy {policy_name}: {e}")
            return False
