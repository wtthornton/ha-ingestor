"""Performance monitoring and resource utilization tracking for Home Assistant Activity Ingestor."""

import asyncio
import platform
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import psutil

from ..metrics import get_metrics_collector
from ..utils.logging import get_logger


@dataclass
class SystemMetrics:
    """System resource utilization metrics."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_io_sent_mb: float = 0.0
    network_io_recv_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceMetrics:
    """Performance-specific metrics."""

    event_processing_rate: float = 0.0  # events per second
    average_processing_time: float = 0.0  # milliseconds
    p95_processing_time: float = 0.0  # 95th percentile
    p99_processing_time: float = 0.0  # 99th percentile
    queue_depth: int = 0
    active_connections: int = 0
    error_rate: float = 0.0  # errors per second
    throughput_points_per_second: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class BusinessMetrics:
    """Business metrics for event processing."""

    total_events_processed: int = 0
    events_by_domain: dict[str, int] = field(default_factory=dict)
    events_by_entity: dict[str, int] = field(default_factory=dict)
    events_by_source: dict[str, int] = field(default_factory=dict)
    data_points_written: int = 0
    data_volume_mb: float = 0.0
    deduplication_rate: float = 0.0
    filter_efficiency: float = 0.0
    transformation_success_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)


class PerformanceMonitor:
    """Monitor system performance and resource utilization."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize performance monitor.

        Args:
            config: Configuration dictionary for monitoring settings
        """
        self.logger = get_logger(__name__)
        self.config = config or {}
        self.metrics_collector = get_metrics_collector()

        # Monitoring configuration
        self.monitoring_interval = self.config.get(
            "monitoring_interval", 30.0
        )  # seconds
        self.enable_system_metrics = self.config.get("enable_system_metrics", True)
        self.enable_performance_metrics = self.config.get(
            "enable_performance_metrics", True
        )
        self.enable_business_metrics = self.config.get("enable_business_metrics", True)

        # Metrics storage
        self.system_metrics_history: list[SystemMetrics] = []
        self.performance_metrics_history: list[PerformanceMetrics] = []
        self.business_metrics_history: list[BusinessMetrics] = []

        # Performance tracking
        self.processing_times: list[float] = []
        self.event_counts: dict[str, int] = {"total": 0, "mqtt": 0, "websocket": 0}
        self.error_counts: dict[str, int] = {
            "total": 0,
            "processing": 0,
            "connection": 0,
        }

        # System info
        self.system_info = self._get_system_info()

        # Register performance metrics
        self._register_performance_metrics()

        self.logger.info(
            "Performance monitor initialized",
            monitoring_interval=self.monitoring_interval,
            system_metrics=self.enable_system_metrics,
            performance_metrics=self.enable_performance_metrics,
            business_metrics=self.enable_business_metrics,
        )

    def _get_system_info(self) -> dict[str, Any]:
        """Get system information."""
        try:
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
            }
        except Exception as e:
            self.logger.error("Failed to get system info", error=str(e))
            return {}

    def _register_performance_metrics(self) -> None:
        """Register performance-specific metrics with the metrics collector."""
        try:
            # System resource metrics
            if self.enable_system_metrics:
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_cpu_percent", "System CPU usage percentage"
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_memory_percent",
                    "System memory usage percentage",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_memory_used_mb", "System memory used in MB"
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_disk_usage_percent",
                    "System disk usage percentage",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_disk_io_read_mb", "System disk read I/O in MB"
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_disk_io_write_mb", "System disk write I/O in MB"
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_network_io_sent_mb",
                    "System network sent I/O in MB",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_system_network_io_recv_mb",
                    "System network received I/O in MB",
                )

            # Performance metrics
            if self.enable_performance_metrics:
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_event_processing_rate",
                    "Event processing rate (events per second)",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_average_processing_time_ms",
                    "Average event processing time in milliseconds",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_p95_processing_time_ms",
                    "95th percentile processing time in milliseconds",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_p99_processing_time_ms",
                    "99th percentile processing time in milliseconds",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_queue_depth",
                    "Current event processing queue depth",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_active_connections",
                    "Number of active connections",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_error_rate",
                    "Error rate (errors per second)",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_performance_throughput_points_per_second",
                    "Data points written per second",
                )

            # Business metrics
            if self.enable_business_metrics:
                self.metrics_collector.registry.register_counter(
                    "ha_ingestor_business_events_by_domain_total",
                    "Total events processed by domain",
                )
                self.metrics_collector.registry.register_counter(
                    "ha_ingestor_business_events_by_entity_total",
                    "Total events processed by entity",
                )
                self.metrics_collector.registry.register_counter(
                    "ha_ingestor_business_events_by_source_total",
                    "Total events processed by source",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_business_deduplication_rate",
                    "Event deduplication rate (0.0 to 1.0)",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_business_filter_efficiency",
                    "Filter efficiency (0.0 to 1.0)",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_business_transformation_success_rate",
                    "Data transformation success rate (0.0 to 1.0)",
                )
                self.metrics_collector.registry.register_gauge(
                    "ha_ingestor_business_data_volume_mb",
                    "Total data volume processed in MB",
                )

            self.logger.info("Performance metrics registered successfully")

        except Exception as e:
            self.logger.error("Failed to register performance metrics", error=str(e))

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system resource utilization metrics.

        Returns:
            SystemMetrics object with current system state
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1.0)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024**2)
            memory_available_mb = memory.available / (1024**2)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_io_read_mb = disk_io.read_bytes / (1024**2) if disk_io else 0.0
            disk_io_write_mb = disk_io.write_bytes / (1024**2) if disk_io else 0.0

            # Network I/O
            network_io = psutil.net_io_counters()
            network_io_sent_mb = (
                network_io.bytes_sent / (1024**2) if network_io else 0.0
            )
            network_io_recv_mb = (
                network_io.bytes_recv / (1024**2) if network_io else 0.0
            )

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_io_read_mb=disk_io_read_mb,
                disk_io_write_mb=disk_io_write_mb,
                network_io_sent_mb=network_io_sent_mb,
                network_io_recv_mb=network_io_recv_mb,
                timestamp=time.time(),
            )

            # Store in history
            self.system_metrics_history.append(metrics)
            if len(self.system_metrics_history) > 100:  # Keep last 100 samples
                self.system_metrics_history.pop(0)

            # Update metrics collector
            if self.enable_system_metrics:
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_cpu_percent", cpu_percent
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_memory_percent", memory_percent
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_memory_used_mb", memory_used_mb
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_disk_usage_percent", disk_usage_percent
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_disk_io_read_mb", disk_io_read_mb
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_disk_io_write_mb", disk_io_write_mb
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_network_io_sent_mb", network_io_sent_mb
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_system_network_io_recv_mb", network_io_recv_mb
                )

            return metrics

        except Exception as e:
            self.logger.error("Failed to collect system metrics", error=str(e))
            return SystemMetrics()

    def record_processing_time(self, processing_time_ms: float) -> None:
        """Record event processing time for performance metrics.

        Args:
            processing_time_ms: Processing time in milliseconds
        """
        try:
            self.processing_times.append(processing_time_ms)

            # Keep only last 1000 processing times for performance
            if len(self.processing_times) > 1000:
                self.processing_times.pop(0)

        except Exception as e:
            self.logger.error("Failed to record processing time", error=str(e))

    def record_event_processed(
        self, source: str, domain: str = "", entity_id: str = ""
    ) -> None:
        """Record event processing for business metrics.

        Args:
            source: Event source (mqtt, websocket)
            domain: Event domain (light, switch, sensor, etc.)
            entity_id: Entity ID
        """
        try:
            # Update total counts
            self.event_counts["total"] += 1
            if source.lower() in ["mqtt", "websocket"]:
                self.event_counts[source.lower()] += 1

            # Update domain counts
            if domain:
                if domain not in self.event_counts:
                    self.event_counts[domain] = 0
                self.event_counts[domain] += 1

            # Update entity counts
            if entity_id:
                if entity_id not in self.event_counts:
                    self.event_counts[entity_id] = 0
                self.event_counts[entity_id] += 1

        except Exception as e:
            self.logger.error("Failed to record event processed", error=str(e))

    def record_error(self, error_type: str) -> None:
        """Record error occurrence for performance metrics.

        Args:
            error_type: Type of error (processing, connection, etc.)
        """
        try:
            self.error_counts["total"] += 1
            if error_type in self.error_counts:
                self.error_counts[error_type] += 1

        except Exception as e:
            self.logger.error("Failed to record error", error=str(e))

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate current performance metrics from collected data.

        Returns:
            PerformanceMetrics object with calculated performance data
        """
        try:
            # Calculate processing rate (events per second)
            current_time = time.time()
            if len(self.processing_times) > 1:
                time_window = 60.0  # Last 60 seconds
                recent_events = sum(
                    1 for _ in self.processing_times[-100:]
                )  # Last 100 events
                event_processing_rate = recent_events / time_window
            else:
                event_processing_rate = 0.0

            # Calculate processing time percentiles
            if self.processing_times:
                sorted_times = sorted(self.processing_times)
                avg_processing_time = sum(self.processing_times) / len(
                    self.processing_times
                )
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)

                p95_processing_time = (
                    sorted_times[p95_index] if p95_index < len(sorted_times) else 0.0
                )
                p99_processing_time = (
                    sorted_times[p99_index] if p99_index < len(sorted_times) else 0.0
                )
            else:
                avg_processing_time = p95_processing_time = p99_processing_time = 0.0

            # Calculate error rate
            if len(self.processing_times) > 0:
                error_rate = self.error_counts["total"] / len(self.processing_times)
            else:
                error_rate = 0.0

            metrics = PerformanceMetrics(
                event_processing_rate=event_processing_rate,
                average_processing_time=avg_processing_time,
                p95_processing_time=p95_processing_time,
                p99_processing_time=p99_processing_time,
                queue_depth=0,  # TODO: Get from actual queue
                active_connections=0,  # TODO: Get from connection monitors
                error_rate=error_rate,
                throughput_points_per_second=0.0,  # TODO: Get from InfluxDB writer
                timestamp=current_time,
            )

            # Store in history
            self.performance_metrics_history.append(metrics)
            if len(self.performance_metrics_history) > 100:
                self.performance_metrics_history.pop(0)

            # Update metrics collector
            if self.enable_performance_metrics:
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_performance_event_processing_rate",
                    event_processing_rate,
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_performance_average_processing_time_ms",
                    avg_processing_time,
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_performance_p95_processing_time_ms",
                    p95_processing_time,
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_performance_p99_processing_time_ms",
                    p99_processing_time,
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_performance_error_rate", error_rate
                )

            return metrics

        except Exception as e:
            self.logger.error("Failed to calculate performance metrics", error=str(e))
            return PerformanceMetrics()

    def calculate_business_metrics(self) -> BusinessMetrics:
        """Calculate current business metrics from collected data.

        Returns:
            BusinessMetrics object with calculated business data
        """
        try:
            # Calculate deduplication rate (placeholder - needs actual deduplication data)
            deduplication_rate = 0.0  # TODO: Calculate from actual deduplication

            # Calculate filter efficiency (placeholder - needs actual filter data)
            filter_efficiency = 0.0  # TODO: Calculate from actual filter data

            # Calculate transformation success rate (placeholder - needs actual transformation data)
            transformation_success_rate = (
                0.0  # TODO: Calculate from actual transformation data
            )

            # Calculate data volume (placeholder - needs actual data size information)
            data_volume_mb = 0.0  # TODO: Calculate from actual data size

            metrics = BusinessMetrics(
                total_events_processed=self.event_counts["total"],
                events_by_domain={
                    k: v
                    for k, v in self.event_counts.items()
                    if k not in ["total", "mqtt", "websocket"]
                },
                events_by_entity={},  # TODO: Populate from actual entity tracking
                events_by_source=self.event_counts.copy(),
                data_points_written=0,  # TODO: Get from InfluxDB writer
                data_volume_mb=data_volume_mb,
                deduplication_rate=deduplication_rate,
                filter_efficiency=filter_efficiency,
                transformation_success_rate=transformation_success_rate,
                timestamp=time.time(),
            )

            # Store in history
            self.business_metrics_history.append(metrics)
            if len(self.business_metrics_history) > 100:
                self.business_metrics_history.pop(0)

            # Update metrics collector
            if self.enable_business_metrics:
                # Update domain-specific counters
                for domain, count in metrics.events_by_domain.items():
                    self.metrics_collector.registry.increment_counter(
                        "ha_ingestor_business_events_by_domain_total",
                        value=count,
                        labels={"domain": domain},
                    )

                # Update source-specific counters
                for source, count in metrics.events_by_source.items():
                    if source not in ["total"]:
                        self.metrics_collector.registry.increment_counter(
                            "ha_ingestor_business_events_by_source_total",
                            value=count,
                            labels={"source": source},
                        )

                # Update business metrics
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_business_deduplication_rate", deduplication_rate
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_business_filter_efficiency", filter_efficiency
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_business_transformation_success_rate",
                    transformation_success_rate,
                )
                self.metrics_collector.registry.set_gauge(
                    "ha_ingestor_business_data_volume_mb", data_volume_mb
                )

            return metrics

        except Exception as e:
            self.logger.error("Failed to calculate business metrics", error=str(e))
            return BusinessMetrics()

    async def start_monitoring(self) -> None:
        """Start continuous monitoring of system and performance metrics."""
        self.logger.info("Starting performance monitoring")

        try:
            while True:
                # Collect system metrics
                if self.enable_system_metrics:
                    await self.collect_system_metrics()

                # Calculate performance metrics
                if self.enable_performance_metrics:
                    self.calculate_performance_metrics()

                # Calculate business metrics
                if self.enable_business_metrics:
                    self.calculate_business_metrics()

                # Wait for next collection interval
                await asyncio.sleep(self.monitoring_interval)

        except asyncio.CancelledError:
            self.logger.info("Performance monitoring cancelled")
        except Exception as e:
            self.logger.error("Performance monitoring failed", error=str(e))

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.logger.info("Stopping performance monitoring")

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of all collected metrics.

        Returns:
            Dictionary with metrics summary
        """
        try:
            current_system = (
                self.system_metrics_history[-1]
                if self.system_metrics_history
                else SystemMetrics()
            )
            current_performance = (
                self.performance_metrics_history[-1]
                if self.performance_metrics_history
                else PerformanceMetrics()
            )
            current_business = (
                self.business_metrics_history[-1]
                if self.business_metrics_history
                else BusinessMetrics()
            )

            return {
                "system_info": self.system_info,
                "current_metrics": {
                    "system": {
                        "cpu_percent": current_system.cpu_percent,
                        "memory_percent": current_system.memory_percent,
                        "memory_used_mb": current_system.memory_used_mb,
                        "disk_usage_percent": current_system.disk_usage_percent,
                        "timestamp": current_system.timestamp,
                    },
                    "performance": {
                        "event_processing_rate": current_performance.event_processing_rate,
                        "average_processing_time_ms": current_performance.average_processing_time,
                        "p95_processing_time_ms": current_performance.p95_processing_time,
                        "p99_processing_time_ms": current_performance.p99_processing_time,
                        "error_rate": current_performance.error_rate,
                        "timestamp": current_performance.timestamp,
                    },
                    "business": {
                        "total_events_processed": current_business.total_events_processed,
                        "data_points_written": current_business.data_points_written,
                        "deduplication_rate": current_business.deduplication_rate,
                        "filter_efficiency": current_business.filter_efficiency,
                        "transformation_success_rate": current_business.transformation_success_rate,
                        "timestamp": current_business.timestamp,
                    },
                },
                "history_counts": {
                    "system_metrics": len(self.system_metrics_history),
                    "performance_metrics": len(self.performance_metrics_history),
                    "business_metrics": len(self.business_metrics_history),
                },
            }

        except Exception as e:
            self.logger.error("Failed to get metrics summary", error=str(e))
            return {}

    @asynccontextmanager
    async def monitor_operation(
        self, operation_name: str, labels: dict[str, str] | None = None
    ) -> AsyncIterator[None]:
        """Context manager for monitoring operation performance.

        Args:
            operation_name: Name of the operation being monitored
            labels: Optional labels for the metric
        """
        start_time = time.time()
        try:
            yield
            duration_ms = (time.time() - start_time) * 1000

            # Record processing time
            self.record_processing_time(duration_ms)

            # Record successful operation
            self.record_event_processed("internal", "monitoring", operation_name)

        except Exception:
            duration_ms = (time.time() - start_time) * 1000

            # Record processing time even for failed operations
            self.record_processing_time(duration_ms)

            # Record error
            self.record_error("processing")

            raise


def create_performance_monitor(
    config: dict[str, Any] | None = None
) -> PerformanceMonitor:
    """Create a performance monitor with the given configuration.

    Args:
        config: Configuration dictionary for monitoring settings

    Returns:
        Configured PerformanceMonitor instance
    """
    return PerformanceMonitor(config)


# Global performance monitor instance
_global_performance_monitor: PerformanceMonitor | None = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance.

    Returns:
        Global PerformanceMonitor instance
    """
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = create_performance_monitor()
    return _global_performance_monitor


def set_performance_monitor(monitor: PerformanceMonitor) -> None:
    """Set the global performance monitor instance.

    Args:
        monitor: PerformanceMonitor instance to set as global
    """
    global _global_performance_monitor
    _global_performance_monitor = monitor
