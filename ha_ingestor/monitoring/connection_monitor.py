"""Enhanced connection monitoring and health tracking."""

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from ..metrics import get_metrics_collector
from ..utils.logging import get_logger


class ConnectionStatus(Enum):
    """Connection status enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    FAILING = "failing"


@dataclass
class ConnectionMetrics:
    """Connection performance metrics."""

    latency_ms: float = 0.0
    throughput_bps: float = 0.0
    packet_loss_percent: float = 0.0
    connection_time_ms: float = 0.0
    last_heartbeat_ms: float = 0.0
    uptime_seconds: float = 0.0
    reconnect_count: int = 0
    error_count: int = 0

    def update_latency(self, latency_ms: float) -> None:
        """Update latency with exponential moving average."""
        alpha = 0.1
        if self.latency_ms == 0.0:
            self.latency_ms = latency_ms
        else:
            self.latency_ms = alpha * latency_ms + (1 - alpha) * self.latency_ms

    def update_throughput(
        self, bytes_transferred: int, duration_seconds: float
    ) -> None:
        """Update throughput calculation."""
        if duration_seconds > 0:
            current_throughput = (
                bytes_transferred * 8
            ) / duration_seconds  # bits per second
            alpha = 0.1
            if self.throughput_bps == 0.0:
                self.throughput_bps = current_throughput
            else:
                self.throughput_bps = (
                    alpha * current_throughput + (1 - alpha) * self.throughput_bps
                )


@dataclass
class ConnectionHealth:
    """Connection health information."""

    service_name: str
    status: ConnectionStatus
    last_check: datetime
    response_time_ms: float
    error_message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)

    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return self.status in [ConnectionStatus.CONNECTED, ConnectionStatus.DEGRADED]

    def is_critical(self) -> bool:
        """Check if connection is in critical state."""
        return self.status == ConnectionStatus.FAILING


class ConnectionMonitor:
    """Enhanced connection monitoring for all services."""

    def __init__(self) -> None:
        """Initialize connection monitor."""
        self.logger = get_logger(__name__)
        self.metrics_collector = get_metrics_collector()

        # Connection health tracking
        self._connections: dict[str, ConnectionHealth] = {}
        self._health_checks: dict[str, Callable[..., Any]] = {}

        # Monitoring configuration
        self._check_interval = 30.0  # seconds
        self._degraded_threshold = (
            1000.0  # ms - response time threshold for degraded status
        )
        self._failing_threshold = (
            5000.0  # ms - response time threshold for failing status
        )

        # Monitoring task
        self._monitoring_task: asyncio.Task | None = None
        self._running = False

        # Performance tracking
        self._last_throughput_check = time.time()
        self._bytes_transferred = 0

    def add_connection(self, service_name: str, health_check: Callable) -> None:
        """Add a connection to monitor.

        Args:
            service_name: Name of the service to monitor
            health_check: Function that returns connection health
        """
        # Create connection health record
        connection_health = ConnectionHealth(
            service_name=service_name,
            status=ConnectionStatus.DISCONNECTED,
            last_check=datetime.now(UTC),
            response_time_ms=0.0,
        )
        self._connections[service_name] = connection_health
        self._health_checks[service_name] = health_check

        self.logger.info("Added connection to monitor", service=service_name)

    def remove_connection(self, service_name: str) -> None:
        """Remove a connection from monitoring.

        Args:
            service_name: Name of the service to remove
        """
        if service_name in self._connections:
            del self._connections[service_name]
        if service_name in self._health_checks:
            del self._health_checks[service_name]

        self.logger.info("Removed connection from monitoring", service=service_name)

    async def start_monitoring(self) -> None:
        """Start the connection monitoring loop."""
        if self._running:
            self.logger.warning("Monitoring already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started connection monitoring")

    async def stop_monitoring(self) -> None:
        """Stop the connection monitoring loop."""
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

        self.logger.info("Stopped connection monitoring")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        try:
            while self._running:
                await self._check_all_connections()
                await asyncio.sleep(self._check_interval)
        except asyncio.CancelledError:
            self.logger.debug("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error("Error in monitoring loop", error=str(e))
        finally:
            self.logger.debug("Monitoring loop stopped")

    async def _check_all_connections(self) -> None:
        """Check health of all monitored connections."""
        for service_name, health_check in self._health_checks.items():
            try:
                await self._check_connection(service_name, health_check)
            except Exception as e:
                self.logger.error(
                    "Error checking connection health",
                    service=service_name,
                    error=str(e),
                )

    async def _check_connection(
        self, service_name: str, health_check: Callable
    ) -> None:
        """Check health of a specific connection.

        Args:
            service_name: Name of the service
            health_check: Health check function
        """
        start_time = time.time()

        try:
            # Perform health check
            if asyncio.iscoroutinefunction(health_check):
                result = await health_check()
            else:
                result = health_check()

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Update connection health
            connection = self._connections[service_name]
            connection.last_check = datetime.now(UTC)
            connection.response_time_ms = response_time
            connection.metrics.update_latency(response_time)

            # Determine status based on response time
            if response_time <= self._degraded_threshold:
                connection.status = ConnectionStatus.CONNECTED
            elif response_time <= self._failing_threshold:
                connection.status = ConnectionStatus.DEGRADED
            else:
                connection.status = ConnectionStatus.FAILING

            # Clear any previous error
            connection.error_message = None

            # Update metrics
            self._update_connection_metrics(service_name, connection)

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            error_message = str(e)

            # Update connection health with error
            connection = self._connections[service_name]
            connection.last_check = datetime.now(UTC)
            connection.response_time_ms = response_time
            connection.status = ConnectionStatus.FAILING
            connection.error_message = error_message
            connection.metrics.error_count += 1

            # Update metrics
            self._update_connection_metrics(service_name, connection)

            self.logger.warning(
                "Connection health check failed",
                service=service_name,
                error=error_message,
            )

    def _update_connection_metrics(
        self, service_name: str, connection: ConnectionHealth
    ) -> None:
        """Update metrics for a connection.

        Args:
            service_name: Name of the service
            connection: Connection health information
        """
        # Update connection status metric
        status_value = 1.0 if connection.is_healthy() else 0.0
        self.metrics_collector.record_client_connection_status(
            service_name, connection.is_healthy()
        )

        # Record connection quality metrics
        self.metrics_collector.collect_component_metrics(
            f"{service_name}_connection",
            {
                "latency_ms": connection.metrics.latency_ms,
                "response_time_ms": connection.response_time_ms,
                "uptime_seconds": connection.metrics.uptime_seconds,
                "reconnect_count": connection.metrics.reconnect_count,
                "error_count": connection.metrics.error_count,
            },
        )

    def record_connection_event(
        self,
        service_name: str,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a connection-related event.

        Args:
            service_name: Name of the service
            event_type: Type of event (connect, disconnect, reconnect, error)
            details: Additional event details
        """
        if service_name not in self._connections:
            return

        connection = self._connections[service_name]
        now = datetime.now(UTC)

        if event_type == "connect":
            connection.status = ConnectionStatus.CONNECTED
            connection.metrics.uptime_seconds = 0.0
            connection.metrics.connection_time_ms = 0.0
            self.logger.info("Connection established", service=service_name)

        elif event_type == "disconnect":
            connection.status = ConnectionStatus.DISCONNECTED
            self.logger.info("Connection lost", service=service_name)

        elif event_type == "reconnect":
            connection.metrics.reconnect_count += 1
            self.logger.info(
                "Connection reestablished",
                service=service_name,
                reconnect_count=connection.metrics.reconnect_count,
            )

        elif event_type == "error":
            connection.metrics.error_count += 1
            connection.status = ConnectionStatus.FAILING
            if details:
                connection.error_message = details.get("error", "Unknown error")
            self.logger.warning(
                "Connection error", service=service_name, details=details
            )

        # Update last check time
        connection.last_check = now

        # Update metrics
        self._update_connection_metrics(service_name, connection)

    def record_data_transfer(self, service_name: str, bytes_transferred: int) -> None:
        """Record data transfer for throughput calculation.

        Args:
            service_name: Name of the service
            bytes_transferred: Number of bytes transferred
        """
        if service_name not in self._connections:
            return

        now = time.time()
        duration = now - self._last_throughput_check

        if duration >= 1.0:  # Update throughput every second
            connection = self._connections[service_name]
            connection.metrics.update_throughput(self._bytes_transferred, duration)

            # Reset counters
            self._bytes_transferred = bytes_transferred
            self._last_throughput_check = now
        else:
            self._bytes_transferred += bytes_transferred

    def get_connection_health(self, service_name: str) -> ConnectionHealth | None:
        """Get health information for a specific connection.

        Args:
            service_name: Name of the service

        Returns:
            ConnectionHealth object or None if not found
        """
        return self._connections.get(service_name)

    def get_all_connections_health(self) -> dict[str, ConnectionHealth]:
        """Get health information for all connections.

        Returns:
            Dictionary of service names to ConnectionHealth objects
        """
        return self._connections.copy()

    def get_overall_health_status(self) -> ConnectionStatus:
        """Get overall health status of all connections.

        Returns:
            Overall connection status
        """
        if not self._connections:
            return ConnectionStatus.DISCONNECTED

        statuses = [conn.status for conn in self._connections.values()]

        if ConnectionStatus.FAILING in statuses:
            return ConnectionStatus.FAILING
        elif ConnectionStatus.DEGRADED in statuses:
            return ConnectionStatus.DEGRADED
        elif all(status == ConnectionStatus.CONNECTED for status in statuses):
            return ConnectionStatus.CONNECTED
        else:
            return ConnectionStatus.DISCONNECTED

    def is_healthy(self) -> bool:
        """Check if all connections are healthy.

        Returns:
            True if all connections are healthy, False otherwise
        """
        return self.get_overall_health_status() in [
            ConnectionStatus.CONNECTED,
            ConnectionStatus.DEGRADED,
        ]

    def get_connection_summary(self) -> dict[str, Any]:
        """Get a summary of all connection health.

        Returns:
            Dictionary with connection summary
        """
        summary = {
            "overall_status": self.get_overall_health_status().value,
            "healthy_connections": 0,
            "total_connections": len(self._connections),
            "connections": {},
        }

        for service_name, connection in self._connections.items():
            summary["connections"][service_name] = {
                "status": connection.status.value,
                "response_time_ms": connection.response_time_ms,
                "last_check": connection.last_check.isoformat(),
                "latency_ms": connection.metrics.latency_ms,
                "uptime_seconds": connection.metrics.uptime_seconds,
                "reconnect_count": connection.metrics.reconnect_count,
                "error_count": connection.metrics.error_count,
            }

            if connection.is_healthy():
                summary["healthy_connections"] += 1

        return summary


# Global connection monitor instance
_global_monitor: ConnectionMonitor | None = None


def get_connection_monitor() -> ConnectionMonitor:
    """Get the global connection monitor instance.

    Returns:
        Global ConnectionMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ConnectionMonitor()
    return _global_monitor


def set_connection_monitor(monitor: ConnectionMonitor) -> None:
    """Set the global connection monitor instance.

    Args:
        monitor: ConnectionMonitor instance to set as global
    """
    global _global_monitor
    _global_monitor = monitor
