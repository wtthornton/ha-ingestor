"""Monitoring and health tracking for the retention system."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..utils.logging import get_logger
from .archival_manager import ArchivalManager
from .cleanup_engine import CleanupEngine


@dataclass
class RetentionHealthCheck:
    """Result of a retention system health check."""

    timestamp: str
    overall_status: str  # healthy, warning, error
    policy_count: int
    active_policy_count: int
    policies_with_errors: int
    cleanup_engine_status: str
    archival_manager_status: str
    storage_utilization_percent: float
    last_cleanup_run: str | None = None
    next_scheduled_cleanup: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class RetentionAlert:
    """Alert for retention system issues."""

    id: str
    severity: str  # info, warning, error, critical
    category: (
        str  # policy_violation, cleanup_failure, archival_failure, storage_critical
    )
    message: str
    timestamp: str
    policy_name: str | None = None
    data_type: str | None = None
    context: dict[str, Any] | None = None
    acknowledged: bool = False
    resolved: bool = False


class RetentionMonitor:
    """Monitors the health and performance of the retention system."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the retention monitor."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Configuration
        self.health_check_interval = self.config.get(
            "health_check_interval", 300
        )  # 5 minutes
        self.alert_retention_days = self.config.get("alert_retention_days", 30)
        self.storage_warning_threshold = self.config.get(
            "storage_warning_threshold", 80.0
        )
        self.storage_critical_threshold = self.config.get(
            "storage_critical_threshold", 95.0
        )
        self.policy_error_threshold = self.config.get("policy_error_threshold", 5)

        # Components
        self.policy_manager = None
        self.cleanup_engine = None
        self.archival_manager = None

        # State
        self.is_running = False
        self.monitoring_task: asyncio.Task | None = None

        # Health tracking
        self.health_history: list[RetentionHealthCheck] = []
        self.active_alerts: dict[str, RetentionAlert] = {}
        self.alert_history: list[RetentionAlert] = []

        # Statistics
        self.total_health_checks = 0
        self.total_alerts_generated = 0

    def set_components(
        self,
        policy_manager: Any,
        cleanup_engine: CleanupEngine,
        archival_manager: ArchivalManager,
    ) -> None:
        """Set the component references for monitoring."""
        self.policy_manager = policy_manager
        self.cleanup_engine = cleanup_engine
        self.archival_manager = archival_manager

    async def start(self) -> None:
        """Start the retention monitor."""
        if self.is_running:
            self.logger.warning("Retention monitor is already running")
            return

        try:
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("Retention monitor started")

        except Exception as e:
            self.logger.error(f"Error starting retention monitor: {e}")
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop the retention monitor."""
        if not self.is_running:
            return

        try:
            self.is_running = False

            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None

            self.logger.info("Retention monitor stopped")

        except Exception as e:
            self.logger.error(f"Error stopping retention monitor: {e}")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running:
            try:
                # Perform health check
                await self._perform_health_check()

                # Wait for next check
                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _perform_health_check(self) -> None:
        """Perform a comprehensive health check."""
        try:
            self.logger.debug("Performing retention system health check")

            # Collect component statuses
            policy_status = await self._check_policy_health()
            cleanup_status = await self._check_cleanup_engine_health()
            archival_status = await self._check_archival_manager_health()
            storage_status = await self._check_storage_health()

            # Determine overall status
            overall_status = self._determine_overall_status(
                policy_status, cleanup_status, archival_status, storage_status
            )

            # Generate warnings and recommendations
            warnings, errors, recommendations = self._generate_insights(
                policy_status, cleanup_status, archival_status, storage_status
            )

            # Create health check result
            health_check = RetentionHealthCheck(
                timestamp=datetime.utcnow().isoformat(),
                overall_status=overall_status,
                policy_count=policy_status.get("total_policies", 0),
                active_policy_count=policy_status.get("active_policies", 0),
                policies_with_errors=policy_status.get("policies_with_errors", 0),
                cleanup_engine_status=cleanup_status.get("status", "unknown"),
                archival_manager_status=archival_status.get("status", "unknown"),
                storage_utilization_percent=storage_status.get(
                    "utilization_percent", 0.0
                ),
                last_cleanup_run=policy_status.get("last_cleanup_run"),
                next_scheduled_cleanup=policy_status.get("next_scheduled_cleanup"),
                warnings=warnings,
                errors=errors,
                recommendations=recommendations,
            )

            # Store health check
            self.health_history.append(health_check)
            self.total_health_checks += 1

            # Limit history size
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-1000:]

            # Generate alerts if needed
            await self._generate_alerts(health_check)

            self.logger.info(f"Health check completed: {overall_status}")

        except Exception as e:
            self.logger.error(f"Error performing health check: {e}")

    async def _check_policy_health(self) -> dict[str, Any]:
        """Check the health of retention policies."""
        try:
            if not self.policy_manager:
                return {"status": "unknown", "error": "Policy manager not available"}

            # Get policy statistics
            stats = self.policy_manager.get_retention_statistics()
            summaries = self.policy_manager.get_all_policy_summaries()

            # Count policies with errors
            policies_with_errors = sum(
                1 for summary in summaries if summary.error_count > 0
            )

            return {
                "status": "healthy" if policies_with_errors == 0 else "warning",
                "total_policies": stats.total_policies,
                "active_policies": stats.active_policies,
                "policies_with_errors": policies_with_errors,
                "last_cleanup_run": stats.last_cleanup_run,
                "next_scheduled_cleanup": stats.next_scheduled_cleanup,
                "system_status": stats.system_status,
            }

        except Exception as e:
            self.logger.error(f"Error checking policy health: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_cleanup_engine_health(self) -> dict[str, Any]:
        """Check the health of the cleanup engine."""
        try:
            if not self.cleanup_engine:
                return {"status": "unknown", "error": "Cleanup engine not available"}

            stats = self.cleanup_engine.get_statistics()

            # Determine status based on active jobs and errors
            if stats["is_running"]:
                if stats["active_jobs"] > 0:
                    status = "running"
                else:
                    status = "idle"
            else:
                status = "stopped"

            return {
                "status": status,
                "is_running": stats["is_running"],
                "active_jobs": stats["active_jobs"],
                "queued_jobs": stats["queued_jobs"],
                "total_jobs_processed": stats["total_jobs_processed"],
                "worker_count": stats["worker_count"],
            }

        except Exception as e:
            self.logger.error(f"Error checking cleanup engine health: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_archival_manager_health(self) -> dict[str, Any]:
        """Check the health of the archival manager."""
        try:
            if not self.archival_manager:
                return {"status": "unknown", "error": "Archival manager not available"}

            stats = self.archival_manager.get_statistics()

            # Determine status
            if stats["is_running"]:
                if stats["active_jobs"] > 0:
                    status = "running"
                else:
                    status = "idle"
            else:
                status = "stopped"

            return {
                "status": status,
                "is_running": stats["is_running"],
                "active_jobs": stats["active_jobs"],
                "queued_jobs": stats["queued_jobs"],
                "total_jobs_processed": stats["total_jobs_processed"],
                "locations": stats["locations"],
                "worker_count": stats["worker_count"],
            }

        except Exception as e:
            self.logger.error(f"Error checking archival manager health: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_storage_health(self) -> dict[str, Any]:
        """Check storage utilization and health."""
        try:
            # This is a placeholder - actual storage checking will be implemented
            # based on the storage backend and available metrics

            # Simulate storage check
            utilization_percent = 75.0  # Placeholder

            if utilization_percent >= self.storage_critical_threshold:
                status = "critical"
            elif utilization_percent >= self.storage_warning_threshold:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "utilization_percent": utilization_percent,
                "warning_threshold": self.storage_warning_threshold,
                "critical_threshold": self.storage_critical_threshold,
            }

        except Exception as e:
            self.logger.error(f"Error checking storage health: {e}")
            return {"status": "error", "error": str(e)}

    def _determine_overall_status(
        self,
        policy_status: dict[str, Any],
        cleanup_status: dict[str, Any],
        archival_status: dict[str, Any],
        storage_status: dict[str, Any],
    ) -> str:
        """Determine overall system status."""
        statuses = [
            policy_status.get("status", "unknown"),
            cleanup_status.get("status", "unknown"),
            archival_status.get("status", "unknown"),
            storage_status.get("status", "unknown"),
        ]

        if "error" in statuses or "critical" in statuses:
            return "error"
        elif "warning" in statuses:
            return "warning"
        else:
            return "healthy"

    def _generate_insights(
        self,
        policy_status: dict[str, Any],
        cleanup_status: dict[str, Any],
        archival_status: dict[str, Any],
        storage_status: dict[str, Any],
    ) -> tuple[list[str], list[str], list[str]]:
        """Generate warnings, errors, and recommendations."""
        warnings = []
        errors = []
        recommendations = []

        # Policy insights
        if policy_status.get("policies_with_errors", 0) > 0:
            warnings.append(
                f"{policy_status['policies_with_errors']} policies have errors"
            )
            recommendations.append("Review and fix policy errors")

        if policy_status.get("status") == "error":
            errors.append("Policy manager is in error state")
            recommendations.append("Check policy manager logs and restart if necessary")

        # Cleanup engine insights
        if cleanup_status.get("status") == "stopped":
            warnings.append("Cleanup engine is stopped")
            recommendations.append("Start the cleanup engine")

        if cleanup_status.get("queued_jobs", 0) > 10:
            warnings.append("High number of queued cleanup jobs")
            recommendations.append("Consider increasing cleanup engine workers")

        # Archival manager insights
        if archival_status.get("status") == "stopped":
            warnings.append("Archival manager is stopped")
            recommendations.append("Start the archival manager")

        if archival_status.get("queued_jobs", 0) > 5:
            warnings.append("High number of queued archival jobs")
            recommendations.append("Consider increasing archival manager workers")

        # Storage insights
        if storage_status.get("status") == "critical":
            errors.append("Storage utilization is critical")
            recommendations.append(
                "Immediate action required: clean up data or expand storage"
            )
        elif storage_status.get("status") == "warning":
            warnings.append("Storage utilization is high")
            recommendations.append(
                "Consider implementing more aggressive retention policies"
            )

        return warnings, errors, recommendations

    async def _generate_alerts(self, health_check: RetentionHealthCheck) -> None:
        """Generate alerts based on health check results."""
        try:
            # Check for critical issues
            if health_check.overall_status == "error":
                await self._create_alert(
                    severity="critical",
                    category="system_health",
                    message="Retention system is in error state",
                    context={"health_check": health_check.__dict__},
                )

            # Check for storage critical
            if (
                health_check.storage_utilization_percent
                >= self.storage_critical_threshold
            ):
                await self._create_alert(
                    severity="critical",
                    category="storage_critical",
                    message=f"Storage utilization is critical: {health_check.storage_utilization_percent:.1f}%",
                    context={"utilization": health_check.storage_utilization_percent},
                )

            # Check for policy errors
            if health_check.policies_with_errors > self.policy_error_threshold:
                await self._create_alert(
                    severity="warning",
                    category="policy_violation",
                    message=f"Multiple policies have errors: {health_check.policies_with_errors}",
                    context={"error_count": health_check.policies_with_errors},
                )

            # Check for stopped components
            if health_check.cleanup_engine_status == "stopped":
                await self._create_alert(
                    severity="warning",
                    category="component_stopped",
                    message="Cleanup engine is stopped",
                    context={"component": "cleanup_engine"},
                )

            if health_check.archival_manager_status == "stopped":
                await self._create_alert(
                    severity="warning",
                    category="component_stopped",
                    message="Archival manager is stopped",
                    context={"component": "archival_manager"},
                )

        except Exception as e:
            self.logger.error(f"Error generating alerts: {e}")

    async def _create_alert(
        self,
        severity: str,
        category: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Create a new retention alert."""
        try:
            alert_id = (
                f"retention_{category}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            )

            alert = RetentionAlert(
                id=alert_id,
                severity=severity,
                category=category,
                message=message,
                timestamp=datetime.utcnow().isoformat(),
                context=context,
            )

            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.total_alerts_generated += 1

            self.logger.info(f"Created retention alert: {severity} - {message}")

        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")

    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        try:
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].acknowledged = True
                return True
            return False

        except Exception as e:
            self.logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True

                # Move to history
                del self.active_alerts[alert_id]

                return True
            return False

        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")
            return False

    def get_health_summary(self) -> dict[str, Any]:
        """Get a summary of the current system health."""
        try:
            if not self.health_history:
                return {
                    "status": "unknown",
                    "message": "No health checks performed yet",
                }

            latest_health = self.health_history[-1]

            return {
                "overall_status": latest_health.overall_status,
                "last_check": latest_health.timestamp,
                "policy_count": latest_health.policy_count,
                "active_policy_count": latest_health.active_policy_count,
                "policies_with_errors": latest_health.policies_with_errors,
                "cleanup_engine_status": latest_health.cleanup_engine_status,
                "archival_manager_status": latest_health.archival_manager_status,
                "storage_utilization_percent": latest_health.storage_utilization_percent,
                "active_alerts": len(self.active_alerts),
                "total_alerts": self.total_alerts_generated,
            }

        except Exception as e:
            self.logger.error(f"Error getting health summary: {e}")
            return {"status": "error", "error": str(e)}

    def get_health_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get health check history."""
        try:
            history = self.health_history[-limit:] if self.health_history else []
            return [check.__dict__ for check in history]

        except Exception as e:
            self.logger.error(f"Error getting health history: {e}")
            return []

    def get_active_alerts(self) -> list[dict[str, Any]]:
        """Get all active alerts."""
        try:
            return [alert.__dict__ for alert in self.active_alerts.values()]

        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []

    def get_alert_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get alert history."""
        try:
            history = self.alert_history[-limit:] if self.alert_history else []
            return [alert.__dict__ for alert in history]

        except Exception as e:
            self.logger.error(f"Error getting alert history: {e}")
            return []

    def get_statistics(self) -> dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "total_health_checks": self.total_health_checks,
            "total_alerts_generated": self.total_alerts_generated,
            "active_alerts": len(self.active_alerts),
            "total_alerts": len(self.alert_history),
            "health_history_size": len(self.health_history),
            "is_running": self.is_running,
            "health_check_interval": self.health_check_interval,
        }
