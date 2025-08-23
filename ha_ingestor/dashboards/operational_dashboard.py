"""Operational dashboard for system status and health monitoring."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from ..alerting.alert_manager import AlertManager
from ..health.checks import HealthChecker
from ..monitoring.connection_monitor import ConnectionMonitor
from ..utils.logging import get_logger


class ServiceStatus(Enum):
    """Service status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ConnectionStatus(Enum):
    """Connection status enumeration."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class ServiceHealth:
    """Represents the health status of a service."""

    name: str
    status: ServiceStatus
    last_check: datetime
    response_time: float  # milliseconds
    error_count: int
    warning_count: int
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionHealth:
    """Represents the health status of a connection."""

    name: str
    status: ConnectionStatus
    last_seen: datetime
    uptime: timedelta
    error_count: int
    reconnect_attempts: int
    latency: float  # milliseconds
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemOverview:
    """Overall system status overview."""

    timestamp: datetime
    overall_status: ServiceStatus
    services_healthy: int
    services_degraded: int
    services_unhealthy: int
    total_services: int
    active_alerts: int
    critical_alerts: int
    system_uptime: timedelta
    last_incident: datetime | None
    performance_score: float  # 0.0 to 100.0


class OperationalDashboard:
    """Operational dashboard for monitoring system health and status."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the operational dashboard."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Initialize components
        self.health_checker = HealthChecker()
        self.connection_monitor = ConnectionMonitor()
        self.alert_manager = AlertManager()

        # Dashboard state
        self.service_health: dict[str, ServiceHealth] = {}
        self.connection_health: dict[str, ConnectionHealth] = {}
        self.system_overview: SystemOverview | None = None

        # Configuration
        self.health_check_interval = self.config.get(
            "health_check_interval", 30
        )  # seconds
        self.connection_check_interval = self.config.get(
            "connection_check_interval", 15
        )  # seconds
        self.overview_update_interval = self.config.get(
            "overview_update_interval", 60
        )  # seconds

        # Auto-refresh task
        self._refresh_task: asyncio.Task | None = None

    async def start_monitoring(self) -> None:
        """Start the operational monitoring."""
        try:
            self.logger.info("Starting operational dashboard monitoring")

            # Start auto-refresh task
            self._refresh_task = asyncio.create_task(self._auto_refresh())

            # Perform initial health checks
            await self._perform_health_checks()
            await self._check_connections()
            await self._update_system_overview()

            self.logger.info("Operational dashboard monitoring started successfully")

        except Exception as e:
            self.logger.error(f"Error starting operational monitoring: {e}")
            raise

    async def stop_monitoring(self) -> None:
        """Stop the operational monitoring."""
        try:
            if self._refresh_task:
                self._refresh_task.cancel()
                try:
                    await self._refresh_task
                except asyncio.CancelledError:
                    pass
                self._refresh_task = None

            self.logger.info("Operational dashboard monitoring stopped")

        except Exception as e:
            self.logger.error(f"Error stopping operational monitoring: {e}")

    async def _auto_refresh(self) -> None:
        """Auto-refresh dashboard data."""
        while True:
            try:
                # Perform health checks
                await self._perform_health_checks()

                # Check connections
                await self._check_connections()

                # Update system overview
                await self._update_system_overview()

                # Wait for next refresh cycle
                await asyncio.sleep(self.overview_update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in auto-refresh: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _perform_health_checks(self) -> None:
        """Perform health checks for all services."""
        try:
            # Get health status from health checker
            health_status = await self.health_checker.get_health_status()

            # Update service health
            for service_name, status_info in health_status.items():
                service_health = ServiceHealth(
                    name=service_name,
                    status=self._map_health_status(
                        status_info.get("status", "unknown")
                    ),
                    last_check=datetime.utcnow(),
                    response_time=status_info.get("response_time", 0.0),
                    error_count=status_info.get("error_count", 0),
                    warning_count=status_info.get("warning_count", 0),
                    details=status_info,
                )

                self.service_health[service_name] = service_health

        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")

    async def _check_connections(self) -> None:
        """Check connection health for all monitored connections."""
        try:
            # Get connection status from connection monitor
            connection_status = self.connection_monitor.get_connection_status()

            # Update connection health
            for conn_name, conn_info in connection_status.items():
                connection_health = ConnectionHealth(
                    name=conn_name,
                    status=self._map_connection_status(
                        conn_info.get("status", "unknown")
                    ),
                    last_seen=conn_info.get("last_seen", datetime.utcnow()),
                    uptime=conn_info.get("uptime", timedelta(0)),
                    error_count=conn_info.get("error_count", 0),
                    reconnect_attempts=conn_info.get("reconnect_attempts", 0),
                    latency=conn_info.get("latency", 0.0),
                    details=conn_info,
                )

                self.connection_health[conn_name] = connection_health

        except Exception as e:
            self.logger.error(f"Error checking connections: {e}")

    async def _update_system_overview(self) -> None:
        """Update the overall system overview."""
        try:
            # Calculate service counts
            services_healthy = sum(
                1
                for s in self.service_health.values()
                if s.status == ServiceStatus.HEALTHY
            )
            services_degraded = sum(
                1
                for s in self.service_health.values()
                if s.status == ServiceStatus.DEGRADED
            )
            services_unhealthy = sum(
                1
                for s in self.service_health.values()
                if s.status == ServiceStatus.UNHEALTHY
            )
            total_services = len(self.service_health)

            # Get alert counts
            active_alerts = len(self.alert_manager.get_active_alerts())
            critical_alerts = len(
                [
                    a
                    for a in self.alert_manager.get_active_alerts()
                    if a.severity.value == "critical"
                ]
            )

            # Calculate overall status
            if services_unhealthy > 0:
                overall_status = ServiceStatus.UNHEALTHY
            elif services_degraded > 0:
                overall_status = ServiceStatus.DEGRADED
            elif services_healthy == total_services:
                overall_status = ServiceStatus.HEALTHY
            else:
                overall_status = ServiceStatus.UNKNOWN

            # Calculate performance score
            if total_services > 0:
                performance_score = (services_healthy / total_services) * 100
            else:
                performance_score = 0.0

            # Get system uptime (simplified - in real implementation, get from system)
            system_uptime = timedelta(hours=24)  # Placeholder

            # Find last incident (simplified)
            last_incident = None
            if services_unhealthy > 0:
                last_incident = datetime.utcnow()

            self.system_overview = SystemOverview(
                timestamp=datetime.utcnow(),
                overall_status=overall_status,
                services_healthy=services_healthy,
                services_degraded=services_degraded,
                services_unhealthy=services_unhealthy,
                total_services=total_services,
                active_alerts=active_alerts,
                critical_alerts=critical_alerts,
                system_uptime=system_uptime,
                last_incident=last_incident,
                performance_score=performance_score,
            )

        except Exception as e:
            self.logger.error(f"Error updating system overview: {e}")

    def _map_health_status(self, status: str) -> ServiceStatus:
        """Map health status string to ServiceStatus enum."""
        status_mapping = {
            "healthy": ServiceStatus.HEALTHY,
            "degraded": ServiceStatus.DEGRADED,
            "unhealthy": ServiceStatus.UNHEALTHY,
            "unknown": ServiceStatus.UNKNOWN,
        }
        return status_mapping.get(status.lower(), ServiceStatus.UNKNOWN)

    def _map_connection_status(self, status: str) -> ConnectionStatus:
        """Map connection status string to ConnectionStatus enum."""
        status_mapping = {
            "connected": ConnectionStatus.CONNECTED,
            "disconnected": ConnectionStatus.DISCONNECTED,
            "reconnecting": ConnectionStatus.RECONNECTING,
            "error": ConnectionStatus.ERROR,
        }
        return status_mapping.get(status.lower(), ConnectionStatus.ERROR)

    def get_service_health(self, service_name: str | None = None) -> dict[str, Any]:
        """Get health status for services."""
        if service_name:
            if service_name in self.service_health:
                health = self.service_health[service_name]
                return {
                    "name": health.name,
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "response_time": health.response_time,
                    "error_count": health.error_count,
                    "warning_count": health.warning_count,
                    "details": health.details,
                }
            else:
                return {"error": f"Service '{service_name}' not found"}

        # Return all services
        return {
            service_name: {
                "name": health.name,
                "status": health.status.value,
                "last_check": health.last_check.isoformat(),
                "response_time": health.response_time,
                "error_count": health.error_count,
                "warning_count": health.warning_count,
                "details": health.details,
            }
            for service_name, health in self.service_health.items()
        }

    def get_connection_health(
        self, connection_name: str | None = None
    ) -> dict[str, Any]:
        """Get health status for connections."""
        if connection_name:
            if connection_name in self.connection_health:
                conn = self.connection_health[connection_name]
                return {
                    "name": conn.name,
                    "status": conn.status.value,
                    "last_seen": conn.last_seen.isoformat(),
                    "uptime_seconds": conn.uptime.total_seconds(),
                    "error_count": conn.error_count,
                    "reconnect_attempts": conn.reconnect_attempts,
                    "latency": conn.latency,
                    "details": conn.details,
                }
            else:
                return {"error": f"Connection '{connection_name}' not found"}

        # Return all connections
        return {
            conn_name: {
                "name": conn.name,
                "status": conn.status.value,
                "last_seen": conn.last_seen.isoformat(),
                "uptime_seconds": conn.uptime.total_seconds(),
                "error_count": conn.error_count,
                "reconnect_attempts": conn.reconnect_attempts,
                "latency": conn.latency,
                "details": conn.details,
            }
            for conn_name, conn in self.connection_health.items()
        }

    def get_system_overview(self) -> dict[str, Any] | None:
        """Get the overall system overview."""
        if not self.system_overview:
            return None

        overview = self.system_overview
        return {
            "timestamp": overview.timestamp.isoformat(),
            "overall_status": overview.overall_status.value,
            "services": {
                "healthy": overview.services_healthy,
                "degraded": overview.services_degraded,
                "unhealthy": overview.services_unhealthy,
                "total": overview.total_services,
            },
            "alerts": {
                "active": overview.active_alerts,
                "critical": overview.critical_alerts,
            },
            "system": {
                "uptime_seconds": overview.system_uptime.total_seconds(),
                "last_incident": (
                    overview.last_incident.isoformat()
                    if overview.last_incident
                    else None
                ),
                "performance_score": overview.performance_score,
            },
        }

    def get_operational_summary(self) -> dict[str, Any]:
        """Get a comprehensive operational summary."""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_overview": self.get_system_overview(),
            "service_health": self.get_service_health(),
            "connection_health": self.get_connection_health(),
            "dashboard_status": {
                "monitoring_active": self._refresh_task is not None
                and not self._refresh_task.done(),
                "last_update": datetime.utcnow().isoformat(),
                "health_check_interval": self.health_check_interval,
                "connection_check_interval": self.connection_check_interval,
                "overview_update_interval": self.overview_update_interval,
            },
        }

        return summary

    def get_service_status_summary(self) -> dict[str, Any]:
        """Get a summary of service statuses."""
        if not self.service_health:
            return {
                "total_services": 0,
                "status_distribution": {},
                "last_updated": datetime.utcnow().isoformat(),
            }

        status_counts = {}
        for health in self.service_health.values():
            status = health.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_services": len(self.service_health),
            "status_distribution": status_counts,
            "last_updated": datetime.utcnow().isoformat(),
        }

    def get_connection_status_summary(self) -> dict[str, Any]:
        """Get a summary of connection statuses."""
        if not self.connection_health:
            return {
                "total_connections": 0,
                "status_distribution": {},
                "last_updated": datetime.utcnow().isoformat(),
            }

        status_counts = {}
        for conn in self.connection_health.values():
            status = conn.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_connections": len(self.connection_health),
            "status_distribution": status_counts,
            "last_updated": datetime.utcnow().isoformat(),
        }

    async def force_refresh(self) -> None:
        """Force an immediate refresh of all dashboard data."""
        try:
            self.logger.info("Forcing immediate dashboard refresh")

            await self._perform_health_checks()
            await self._check_connections()
            await self._update_system_overview()

            self.logger.info("Dashboard refresh completed")

        except Exception as e:
            self.logger.error(f"Error during forced refresh: {e}")

    def get_dashboard_config(self) -> dict[str, Any]:
        """Get the current dashboard configuration."""
        return {
            "health_check_interval": self.health_check_interval,
            "connection_check_interval": self.connection_check_interval,
            "overview_update_interval": self.overview_update_interval,
            "monitoring_active": self._refresh_task is not None
            and not self._refresh_task.done(),
        }

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update dashboard configuration."""
        if "health_check_interval" in new_config:
            self.health_check_interval = new_config["health_check_interval"]
        if "connection_check_interval" in new_config:
            self.connection_check_interval = new_config["connection_check_interval"]
        if "overview_update_interval" in new_config:
            self.overview_update_interval = new_config["overview_update_interval"]

        self.logger.info("Operational dashboard configuration updated")
