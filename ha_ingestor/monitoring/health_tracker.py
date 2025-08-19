"""Service health tracking and monitoring."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..metrics import get_metrics_collector
from ..utils.logging import get_logger


class ServiceStatus(Enum):
    """Service status enumeration."""

    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceHealth:
    """Service health information."""

    service_name: str
    status: ServiceStatus
    start_time: datetime | None = None
    last_heartbeat: datetime | None = None
    uptime_seconds: float = 0.0
    error_count: int = 0
    warning_count: int = 0
    last_error: str | None = None
    last_warning: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status in [ServiceStatus.RUNNING, ServiceStatus.DEGRADED]

    def is_running(self) -> bool:
        """Check if service is running."""
        return self.status == ServiceStatus.RUNNING

    def needs_attention(self) -> bool:
        """Check if service needs attention."""
        return self.status in [ServiceStatus.DEGRADED, ServiceStatus.ERROR]

    def update_uptime(self) -> None:
        """Update service uptime."""
        if self.start_time:
            self.uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()


class HealthTracker:
    """Service health tracking and monitoring."""

    def __init__(self) -> None:
        """Initialize health tracker."""
        self.logger = get_logger(__name__)
        self.metrics_collector = get_metrics_collector()

        # Service health tracking
        self._services: dict[str, ServiceHealth] = {}
        self._health_checks: dict[str, Callable[..., Any]] = {}

        # Monitoring configuration
        self._check_interval = 60.0  # seconds
        self._heartbeat_timeout = 300.0  # seconds - 5 minutes

        # Monitoring task
        self._monitoring_task: asyncio.Task | None = None
        self._running = False

        # Health check callbacks
        self._on_service_unhealthy: Callable[[str, ServiceHealth], None] | None = None
        self._on_service_recovered: Callable[[str, ServiceHealth], None] | None = None

    def register_service(
        self, service_name: str, health_check: Callable | None = None
    ) -> None:
        """Register a service for health tracking.

        Args:
            service_name: Name of the service
            health_check: Optional health check function
        """
        self._services[service_name] = ServiceHealth(
            service_name=service_name, status=ServiceStatus.UNKNOWN
        )

        if health_check:
            self._health_checks[service_name] = health_check

        self.logger.info("Registered service for health tracking", service=service_name)

    def unregister_service(self, service_name: str) -> None:
        """Unregister a service from health tracking.

        Args:
            service_name: Name of the service
        """
        if service_name in self._services:
            del self._services[service_name]
        if service_name in self._health_checks:
            del self._health_checks[service_name]

        self.logger.info(
            "Unregistered service from health tracking", service=service_name
        )

    def set_service_status(
        self,
        service_name: str,
        status: ServiceStatus,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Set the status of a service.

        Args:
            service_name: Name of the service
            status: New status
            details: Additional status details
        """
        if service_name not in self._services:
            self.logger.warning("Service not registered", service=service_name)
            return

        service = self._services[service_name]
        previous_status = service.status

        # Update status
        service.status = status

        # Handle status-specific logic
        if status == ServiceStatus.STARTING:
            service.start_time = datetime.utcnow()
            service.uptime_seconds = 0.0
            service.error_count = 0
            service.warning_count = 0

        elif status == ServiceStatus.RUNNING:
            if service.start_time is None:
                service.start_time = datetime.utcnow()
            service.last_heartbeat = datetime.utcnow()

        elif status == ServiceStatus.ERROR:
            service.error_count += 1
            if details and "error" in details:
                service.last_error = details["error"]

        elif status == ServiceStatus.DEGRADED:
            service.warning_count += 1
            if details and "warning" in details:
                service.last_warning = details["warning"]

        # Update details
        if details:
            service.details.update(details)

        # Update uptime
        service.update_uptime()

        # Log status change
        self.logger.info(
            "Service status changed",
            service=service_name,
            previous_status=previous_status.value,
            new_status=status.value,
            details=details,
        )

        # Check for health state changes
        if previous_status != status:
            self._check_health_state_change(
                service_name, service, previous_status, status
            )

        # Update metrics
        self._update_service_metrics(service_name, service)

    def record_heartbeat(self, service_name: str) -> None:
        """Record a heartbeat for a service.

        Args:
            service_name: Name of the service
        """
        if service_name not in self._services:
            return

        service = self._services[service_name]
        service.last_heartbeat = datetime.utcnow()
        service.update_uptime()

        # Update metrics
        self._update_service_metrics(service_name, service)

    def record_error(
        self, service_name: str, error: str, details: dict[str, Any] | None = None
    ) -> None:
        """Record an error for a service.

        Args:
            service_name: Name of the service
            error: Error message
            details: Additional error details
        """
        if service_name not in self._services:
            return

        service = self._services[service_name]
        service.error_count += 1
        service.last_error = error

        if details:
            service.details.update(details)

        # Update status to error if currently running
        if service.status == ServiceStatus.RUNNING:
            service.status = ServiceStatus.ERROR

        # Update metrics
        self._update_service_metrics(service_name, service)

        self.logger.warning(
            "Service error recorded", service=service_name, error=error, details=details
        )

    def record_warning(
        self, service_name: str, warning: str, details: dict[str, Any] | None = None
    ) -> None:
        """Record a warning for a service.

        Args:
            service_name: Name of the service
            warning: Warning message
            details: Additional warning details
        """
        if service_name not in self._services:
            return

        service = self._services[service_name]
        service.warning_count += 1
        service.last_warning = warning

        if details:
            service.details.update(details)

        # Update status to degraded if currently running
        if service.status == ServiceStatus.RUNNING:
            service.status = ServiceStatus.DEGRADED

        # Update metrics
        self._update_service_metrics(service_name, service)

        self.logger.warning(
            "Service warning recorded",
            service=service_name,
            warning=warning,
            details=details,
        )

    def set_health_callbacks(
        self,
        on_unhealthy: Callable | None = None,
        on_recovered: Callable | None = None,
    ) -> None:
        """Set health state change callbacks.

        Args:
            on_unhealthy: Callback when service becomes unhealthy
            on_recovered: Callback when service recovers
        """
        self._on_service_unhealthy = on_unhealthy
        self._on_service_recovered = on_recovered

    async def start_monitoring(self) -> None:
        """Start the health monitoring loop."""
        if self._running:
            self.logger.warning("Health monitoring already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started health monitoring")

    async def stop_monitoring(self) -> None:
        """Stop the health monitoring loop."""
        if not self._running:
            return

        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None

        self.logger.info("Stopped health monitoring")

    async def _monitoring_loop(self) -> None:
        """Main health monitoring loop."""
        try:
            while self._running:
                await self._check_all_services()
                await asyncio.sleep(self._check_interval)
        except asyncio.CancelledError:
            self.logger.debug("Health monitoring loop cancelled")
        except Exception as e:
            self.logger.error("Error in health monitoring loop", error=str(e))
        finally:
            self.logger.debug("Health monitoring loop stopped")

    async def _check_all_services(self) -> None:
        """Check health of all registered services."""
        for service_name, health_check in self._health_checks.items():
            try:
                await self._check_service_health(service_name, health_check)
            except Exception as e:
                self.logger.error(
                    "Error checking service health", service=service_name, error=str(e)
                )

        # Check for stale heartbeats
        await self._check_heartbeat_timeouts()

    async def _check_service_health(
        self, service_name: str, health_check: Callable
    ) -> None:
        """Check health of a specific service.

        Args:
            service_name: Name of the service
            health_check: Health check function
        """
        if service_name not in self._services:
            return

        try:
            # Perform health check
            if asyncio.iscoroutinefunction(health_check):
                result = await health_check()
            else:
                result = health_check()

            # Update service based on health check result
            if result is True or result is None:
                # Service is healthy
                if self._services[service_name].status != ServiceStatus.RUNNING:
                    self.set_service_status(service_name, ServiceStatus.RUNNING)
            else:
                # Service is unhealthy
                error_msg = (
                    str(result) if result is not False else "Health check failed"
                )
                self.record_error(service_name, error_msg)

        except Exception as e:
            self.record_error(service_name, f"Health check error: {str(e)}")

    async def _check_heartbeat_timeouts(self) -> None:
        """Check for services with stale heartbeats."""
        now = datetime.utcnow()

        for service_name, service in self._services.items():
            if service.last_heartbeat and service.status == ServiceStatus.RUNNING:

                time_since_heartbeat = (now - service.last_heartbeat).total_seconds()

                if time_since_heartbeat > self._heartbeat_timeout:
                    self.logger.warning(
                        "Service heartbeat timeout",
                        service=service_name,
                        seconds_since_heartbeat=time_since_heartbeat,
                    )

                    # Mark service as degraded
                    self.set_service_status(
                        service_name,
                        ServiceStatus.DEGRADED,
                        {"warning": f"Heartbeat timeout ({time_since_heartbeat:.1f}s)"},
                    )

    def _check_health_state_change(
        self,
        service_name: str,
        service: ServiceHealth,
        previous_status: ServiceStatus,
        new_status: ServiceStatus,
    ) -> None:
        """Check for health state changes and trigger callbacks.

        Args:
            service_name: Name of the service
            service: Service health object
            previous_status: Previous status
            new_status: New status
        """
        # Check if service became unhealthy
        if previous_status in [
            ServiceStatus.RUNNING,
            ServiceStatus.DEGRADED,
        ] and new_status in [ServiceStatus.ERROR, ServiceStatus.STOPPED]:

            if self._on_service_unhealthy:
                try:
                    self._on_service_unhealthy(service_name, service)
                except Exception as e:
                    self.logger.error(
                        "Error in unhealthy callback",
                        service=service_name,
                        error=str(e),
                    )

        # Check if service recovered
        elif (
            previous_status in [ServiceStatus.ERROR, ServiceStatus.DEGRADED]
            and new_status == ServiceStatus.RUNNING
        ):

            if self._on_service_recovered:
                try:
                    self._on_service_recovered(service_name, service)
                except Exception as e:
                    self.logger.error(
                        "Error in recovered callback",
                        service=service_name,
                        error=str(e),
                    )

    def _update_service_metrics(
        self, service_name: str, service: ServiceHealth
    ) -> None:
        """Update metrics for a service.

        Args:
            service_name: Name of the service
            service: Service health object
        """
        # Record service status metric
        status_value = 1.0 if service.is_healthy() else 0.0
        self.metrics_collector.collect_component_metrics(
            f"{service_name}_service",
            {
                "status": status_value,
                "uptime_seconds": service.uptime_seconds,
                "error_count": service.error_count,
                "warning_count": service.warning_count,
            },
        )

    def get_service_health(self, service_name: str) -> ServiceHealth | None:
        """Get health information for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            ServiceHealth object or None if not found
        """
        return self._services.get(service_name)

    def get_all_services_health(self) -> dict[str, ServiceHealth]:
        """Get health information for all services.

        Returns:
            Dictionary of service names to ServiceHealth objects
        """
        return self._services.copy()

    def get_overall_health_status(self) -> ServiceStatus:
        """Get overall health status of all services.

        Returns:
            Overall service status
        """
        if not self._services:
            return ServiceStatus.UNKNOWN

        statuses = [service.status for service in self._services.values()]

        if ServiceStatus.ERROR in statuses:
            return ServiceStatus.ERROR
        elif ServiceStatus.DEGRADED in statuses:
            return ServiceStatus.DEGRADED
        elif all(status == ServiceStatus.RUNNING for status in statuses):
            return ServiceStatus.RUNNING
        elif ServiceStatus.STARTING in statuses:
            return ServiceStatus.STARTING
        elif ServiceStatus.STOPPING in statuses:
            return ServiceStatus.STOPPING
        else:
            return ServiceStatus.UNKNOWN

    def is_healthy(self) -> bool:
        """Check if all services are healthy.

        Returns:
            True if all services are healthy, False otherwise
        """
        return self.get_overall_health_status() in [
            ServiceStatus.RUNNING,
            ServiceStatus.DEGRADED,
        ]

    def get_health_summary(self) -> dict[str, Any]:
        """Get a summary of all service health.

        Returns:
            Dictionary with health summary
        """
        summary = {
            "overall_status": self.get_overall_health_status().value,
            "healthy_services": 0,
            "total_services": len(self._services),
            "services": {},
        }

        for service_name, service in self._services.items():
            summary["services"][service_name] = {
                "status": service.status.value,
                "uptime_seconds": service.uptime_seconds,
                "error_count": service.error_count,
                "warning_count": service.warning_count,
                "last_heartbeat": (
                    service.last_heartbeat.isoformat()
                    if service.last_heartbeat
                    else None
                ),
                "last_error": service.last_error,
                "last_warning": service.last_warning,
            }

            if service.is_healthy():
                summary["healthy_services"] += 1

        return summary


# Global health tracker instance
_global_tracker: HealthTracker | None = None


def get_health_tracker() -> HealthTracker:
    """Get the global health tracker instance.

    Returns:
        Global HealthTracker instance
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = HealthTracker()
    return _global_tracker


def set_health_tracker(tracker: HealthTracker) -> None:
    """Set the global health tracker instance.

    Args:
        tracker: HealthTracker instance to set as global
    """
    global _global_tracker
    _global_tracker = tracker
