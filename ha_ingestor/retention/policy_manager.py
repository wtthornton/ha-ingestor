"""Retention policy manager for Home Assistant Activity Ingestor."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from ..utils.logging import get_logger
from .retention_policies import (
    ArchivalStrategy,
    CompressionLevel,
    DataType,
    RetentionPeriod,
    RetentionPolicy,
    RetentionPolicySummary,
    RetentionStatistics,
)


class RetentionPolicyManager:
    """Manages retention policies and their enforcement."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the retention policy manager."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Policy storage
        self.policies: dict[str, RetentionPolicy] = {}
        self.policy_summaries: dict[str, RetentionPolicySummary] = {}

        # Configuration
        self.default_retention_days = self.config.get("default_retention_days", 90)
        self.cleanup_interval = self.config.get("cleanup_interval", 3600)  # 1 hour
        self.max_cleanup_duration = self.config.get(
            "max_cleanup_duration", 300
        )  # 5 minutes

        # State
        self.is_running = False
        self.last_cleanup = None
        self.next_cleanup = None
        self.cleanup_task: asyncio.Task | None = None

        # Initialize default policies
        self._initialize_default_policies()

    def _initialize_default_policies(self) -> None:
        """Initialize default retention policies."""
        default_policies = [
            # Home Assistant events - keep for 1 year, then compress
            RetentionPolicy(
                name="ha_events_default",
                data_type=DataType.HA_EVENTS,
                retention_period=RetentionPeriod.ONE_YEAR,
                archival_strategy=ArchivalStrategy.COMPRESS,
                compression_level=CompressionLevel.HIGH,
                description="Default policy for Home Assistant events",
                tags=["default", "ha_events"],
            ),
            # System metrics - keep for 6 months, then aggregate
            RetentionPolicy(
                name="system_metrics_default",
                data_type=DataType.SYSTEM_METRICS,
                retention_period=RetentionPeriod.SIX_MONTHS,
                archival_strategy=ArchivalStrategy.AGGREGATE,
                aggregation_interval=timedelta(hours=1),
                description="Default policy for system metrics",
                tags=["default", "system_metrics"],
            ),
            # Performance metrics - keep for 3 months, then sample
            RetentionPolicy(
                name="performance_metrics_default",
                data_type=DataType.PERFORMANCE_METRICS,
                retention_period=RetentionPeriod.THREE_MONTHS,
                archival_strategy=ArchivalStrategy.SAMPLE,
                sampling_rate=0.1,  # Keep 10% of old data
                description="Default policy for performance metrics",
                tags=["default", "performance_metrics"],
            ),
            # Alert history - keep for 1 year, then compress
            RetentionPolicy(
                name="alert_history_default",
                data_type=DataType.ALERT_HISTORY,
                retention_period=RetentionPeriod.ONE_YEAR,
                archival_strategy=ArchivalStrategy.COMPRESS,
                compression_level=CompressionLevel.MEDIUM,
                description="Default policy for alert history",
                tags=["default", "alert_history"],
            ),
            # Connection logs - keep for 1 month, then delete
            RetentionPolicy(
                name="connection_logs_default",
                data_type=DataType.CONNECTION_LOGS,
                retention_period=RetentionPeriod.ONE_MONTH,
                archival_strategy=ArchivalStrategy.DELETE,
                description="Default policy for connection logs",
                tags=["default", "connection_logs"],
            ),
            # Error logs - keep for 3 months, then compress
            RetentionPolicy(
                name="error_logs_default",
                data_type=DataType.ERROR_LOGS,
                retention_period=RetentionPeriod.THREE_MONTHS,
                archival_strategy=ArchivalStrategy.COMPRESS,
                compression_level=CompressionLevel.HIGH,
                description="Default policy for error logs",
                tags=["default", "error_logs"],
            ),
        ]

        for policy in default_policies:
            self.add_policy(policy)

    def add_policy(self, policy: RetentionPolicy) -> bool:
        """Add a new retention policy."""
        try:
            if policy.name in self.policies:
                self.logger.warning(f"Policy '{policy.name}' already exists, updating")
                return self.update_policy(policy.name, policy)

            # Set creation timestamp
            policy.created_at = datetime.utcnow().isoformat()
            policy.updated_at = policy.created_at

            self.policies[policy.name] = policy

            # Initialize summary
            self.policy_summaries[policy.name] = RetentionPolicySummary(
                policy_name=policy.name,
                data_type=policy.data_type,
                total_records=0,
                records_to_archive=0,
                records_archived=0,
                storage_saved_mb=0.0,
                status="active",
            )

            self.logger.info(f"Added retention policy: {policy.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding policy '{policy.name}': {e}")
            return False

    def update_policy(self, policy_name: str, updated_policy: RetentionPolicy) -> bool:
        """Update an existing retention policy."""
        try:
            if policy_name not in self.policies:
                self.logger.error(f"Policy '{policy_name}' not found")
                return False

            # Preserve original creation time
            original_created_at = self.policies[policy_name].created_at

            # Update the policy
            updated_policy.created_at = original_created_at
            updated_policy.updated_at = datetime.utcnow().isoformat()
            updated_policy.name = policy_name  # Ensure name consistency

            self.policies[policy_name] = updated_policy

            self.logger.info(f"Updated retention policy: {policy_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating policy '{policy_name}': {e}")
            return False

    def remove_policy(self, policy_name: str) -> bool:
        """Remove a retention policy."""
        try:
            if policy_name not in self.policies:
                self.logger.warning(f"Policy '{policy_name}' not found")
                return False

            # Check if it's a default policy
            if any("default" in tag for tag in self.policies[policy_name].tags):
                self.logger.warning(f"Cannot remove default policy: {policy_name}")
                return False

            del self.policies[policy_name]
            if policy_name in self.policy_summaries:
                del self.policy_summaries[policy_name]

            self.logger.info(f"Removed retention policy: {policy_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error removing policy '{policy_name}': {e}")
            return False

    def get_policy(self, policy_name: str) -> RetentionPolicy | None:
        """Get a retention policy by name."""
        return self.policies.get(policy_name)

    def get_policies_by_type(self, data_type: DataType) -> list[RetentionPolicy]:
        """Get all policies for a specific data type."""
        return [
            policy for policy in self.policies.values() if policy.data_type == data_type
        ]

    def get_active_policies(self) -> list[RetentionPolicy]:
        """Get all active retention policies."""
        return [policy for policy in self.policies.values() if policy.enabled]

    def list_policies(self) -> list[str]:
        """List all policy names."""
        return list(self.policies.keys())

    def get_policy_summary(self, policy_name: str) -> RetentionPolicySummary | None:
        """Get summary for a specific policy."""
        return self.policy_summaries.get(policy_name)

    def get_all_policy_summaries(self) -> list[RetentionPolicySummary]:
        """Get summaries for all policies."""
        return list(self.policy_summaries.values())

    def get_retention_statistics(self) -> RetentionStatistics:
        """Get overall retention system statistics."""
        active_policies = len(self.get_active_policies())
        total_storage_saved = sum(
            summary.storage_saved_mb for summary in self.policy_summaries.values()
        )
        total_records_archived = sum(
            summary.records_archived for summary in self.policy_summaries.values()
        )

        # Determine system status
        error_count = sum(
            summary.error_count for summary in self.policy_summaries.values()
        )
        if error_count > 10:
            system_status = "error"
        elif error_count > 5:
            system_status = "warning"
        else:
            system_status = "healthy"

        return RetentionStatistics(
            total_policies=len(self.policies),
            active_policies=active_policies,
            total_storage_saved_mb=total_storage_saved,
            total_records_archived=total_records_archived,
            cleanup_jobs_run=0,  # TODO: Track this
            last_cleanup_run=(
                self.last_cleanup.isoformat() if self.last_cleanup else None
            ),
            next_scheduled_cleanup=(
                self.next_cleanup.isoformat() if self.next_cleanup else None
            ),
            system_status=system_status,
        )

    def update_policy_summary(self, policy_name: str, **kwargs: Any) -> bool:
        """Update summary for a specific policy."""
        try:
            if policy_name not in self.policy_summaries:
                return False

            summary = self.policy_summaries[policy_name]
            for key, value in kwargs.items():
                if hasattr(summary, key):
                    setattr(summary, key, value)

            return True

        except Exception as e:
            self.logger.error(f"Error updating policy summary for '{policy_name}': {e}")
            return False

    def validate_policy(self, policy: RetentionPolicy) -> list[str]:
        """Validate a retention policy configuration."""
        errors = []

        # Check required fields
        if not policy.name:
            errors.append("Policy name is required")

        if not policy.data_type:
            errors.append("Data type is required")

        if not policy.retention_period:
            errors.append("Retention period is required")

        if not policy.archival_strategy:
            errors.append("Archival strategy is required")

        # Check sampling rate
        if policy.sampling_rate is not None and not (
            0.0 <= policy.sampling_rate <= 1.0
        ):
            errors.append("Sampling rate must be between 0.0 and 1.0")

        # Check alert threshold
        if policy.alert_threshold <= 0.0 or policy.alert_threshold > 1.0:
            errors.append("Alert threshold must be between 0.0 and 1.0")

        # Check aggregation interval for aggregate strategy
        if (
            policy.archival_strategy == ArchivalStrategy.AGGREGATE
            and policy.aggregation_interval is None
        ):
            errors.append("Aggregation interval is required for aggregate strategy")

        return errors

    def get_policies_for_cleanup(self) -> list[RetentionPolicy]:
        """Get policies that need cleanup based on their configuration."""
        now = datetime.utcnow()
        policies_for_cleanup = []

        for policy in self.get_active_policies():
            if not policy.enabled:
                continue

            # Check if policy should be enforced immediately
            if policy.enforce_immediately:
                policies_for_cleanup.append(policy)
                continue

            # Check if it's time for regular cleanup
            if self.last_cleanup:
                time_since_cleanup = now - self.last_cleanup
                if time_since_cleanup.total_seconds() >= self.cleanup_interval:
                    policies_for_cleanup.append(policy)

        return policies_for_cleanup

    async def start(self) -> None:
        """Start the retention policy manager."""
        if self.is_running:
            self.logger.warning("Retention policy manager is already running")
            return

        try:
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.logger.info("Retention policy manager started")

        except Exception as e:
            self.logger.error(f"Error starting retention policy manager: {e}")
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop the retention policy manager."""
        if not self.is_running:
            return

        try:
            self.is_running = False

            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
                self.cleanup_task = None

            self.logger.info("Retention policy manager stopped")

        except Exception as e:
            self.logger.error(f"Error stopping retention policy manager: {e}")

    async def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self.is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                if not self.is_running:
                    break

                # Perform cleanup
                await self._perform_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _perform_cleanup(self) -> None:
        """Perform cleanup for all policies that need it."""
        try:
            policies_for_cleanup = self.get_policies_for_cleanup()

            if not policies_for_cleanup:
                return

            self.logger.info(
                f"Starting cleanup for {len(policies_for_cleanup)} policies"
            )
            start_time = datetime.utcnow()

            for policy in policies_for_cleanup:
                try:
                    await self._cleanup_policy(policy)
                except Exception as e:
                    self.logger.error(f"Error cleaning up policy '{policy.name}': {e}")
                    self.update_policy_summary(
                        policy.name,
                        error_count=self.policy_summaries[policy.name].error_count + 1,
                        last_error=str(e),
                    )

            self.last_cleanup = datetime.utcnow()
            duration = (self.last_cleanup - start_time).total_seconds()

            if duration > self.max_cleanup_duration:
                self.logger.warning(
                    f"Cleanup took {duration}s, exceeded limit of {self.max_cleanup_duration}s"
                )

            self.logger.info(f"Cleanup completed in {duration:.2f}s")

        except Exception as e:
            self.logger.error(f"Error performing cleanup: {e}")

    async def _cleanup_policy(self, policy: RetentionPolicy) -> None:
        """Cleanup a specific policy."""
        # This is a placeholder - actual cleanup logic will be implemented
        # in the CleanupEngine and ArchivalManager
        self.logger.debug(f"Cleanup placeholder for policy: {policy.name}")

        # Update summary to show cleanup was attempted
        self.update_policy_summary(
            policy.name, last_cleanup=datetime.utcnow().isoformat()
        )
