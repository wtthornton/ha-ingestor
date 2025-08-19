"""Custom Prometheus collector for Home Assistant Activity Ingestor."""

from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest
from prometheus_client.core import CollectorRegistry, Metric

from ..utils.logging import get_logger


class HAIngestorCollector:
    """Custom Prometheus collector for HA Ingestor metrics."""

    def __init__(self, registry: CollectorRegistry | None = None) -> None:
        """Initialize the custom collector.

        Args:
            registry: Optional Prometheus registry to use
        """
        self.logger = get_logger(__name__)
        self.registry = registry or CollectorRegistry()

        # System metrics
        self.system_cpu_percent = Gauge(
            "ha_ingestor_system_cpu_percent",
            "System CPU usage percentage",
            ["hostname"],
            registry=self.registry,
        )

        self.system_memory_percent = Gauge(
            "ha_ingestor_system_memory_percent",
            "System memory usage percentage",
            ["hostname"],
            registry=self.registry,
        )

        self.system_memory_used_bytes = Gauge(
            "ha_ingestor_system_memory_used_bytes",
            "System memory used in bytes",
            ["hostname"],
            registry=self.registry,
        )

        self.system_disk_usage_percent = Gauge(
            "ha_ingestor_system_disk_usage_percent",
            "System disk usage percentage",
            ["hostname", "mountpoint"],
            registry=self.registry,
        )

        self.system_disk_io_read_bytes = Counter(
            "ha_ingestor_system_disk_io_read_bytes_total",
            "Total disk read I/O in bytes",
            ["hostname"],
            registry=self.registry,
        )

        self.system_disk_io_write_bytes = Counter(
            "ha_ingestor_system_disk_io_write_bytes_total",
            "Total disk write I/O in bytes",
            ["hostname"],
            registry=self.registry,
        )

        self.system_network_io_sent_bytes = Counter(
            "ha_ingestor_system_network_io_sent_bytes_total",
            "Total network sent I/O in bytes",
            ["hostname", "interface"],
            registry=self.registry,
        )

        self.system_network_io_recv_bytes = Counter(
            "ha_ingestor_system_network_io_recv_bytes_total",
            "Total network received I/O in bytes",
            ["hostname", "interface"],
            registry=self.registry,
        )

        # Performance metrics
        self.event_processing_duration = Histogram(
            "ha_ingestor_event_processing_duration_seconds",
            "Event processing duration in seconds",
            ["source", "domain", "entity_id"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry,
        )

        self.event_processing_rate = Gauge(
            "ha_ingestor_event_processing_rate_events_per_second",
            "Event processing rate in events per second",
            ["source"],
            registry=self.registry,
        )

        self.queue_depth = Gauge(
            "ha_ingestor_queue_depth",
            "Current event processing queue depth",
            ["queue_name"],
            registry=self.registry,
        )

        self.active_connections = Gauge(
            "ha_ingestor_active_connections",
            "Number of active connections",
            ["connection_type"],
            registry=self.registry,
        )

        # Business metrics
        self.events_processed_total = Counter(
            "ha_ingestor_events_processed_total",
            "Total number of events processed",
            ["source", "domain", "entity_id", "status"],
            registry=self.registry,
        )

        self.data_points_written_total = Counter(
            "ha_ingestor_data_points_written_total",
            "Total number of data points written to InfluxDB",
            ["measurement", "status"],
            registry=self.registry,
        )

        self.data_volume_bytes = Counter(
            "ha_ingestor_data_volume_bytes_total",
            "Total data volume processed in bytes",
            ["source", "type"],
            registry=self.registry,
        )

        self.deduplication_rate = Gauge(
            "ha_ingestor_deduplication_rate",
            "Event deduplication rate (0.0 to 1.0)",
            ["source"],
            registry=self.registry,
        )

        self.filter_efficiency = Gauge(
            "ha_ingestor_filter_efficiency",
            "Filter efficiency (0.0 to 1.0)",
            ["filter_type"],
            registry=self.registry,
        )

        self.transformation_success_rate = Gauge(
            "ha_ingestor_transformation_success_rate",
            "Data transformation success rate (0.0 to 1.0)",
            ["transformer_type"],
            registry=self.registry,
        )

        # Error metrics
        self.errors_total = Counter(
            "ha_ingestor_errors_total",
            "Total number of errors",
            ["error_type", "component", "severity"],
            registry=self.registry,
        )

        self.circuit_breaker_state = Gauge(
            "ha_ingestor_circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=half_open, 2=open)",
            ["component"],
            registry=self.registry,
        )

        self.retry_attempts_total = Counter(
            "ha_ingestor_retry_attempts_total",
            "Total number of retry attempts",
            ["component", "operation"],
            registry=self.registry,
        )

        # Service info
        self.service_info = Info(
            "ha_ingestor",
            "Home Assistant Activity Ingestor service information",
            registry=self.registry,
        )

        # Initialize service info
        self.service_info.info(
            {
                "version": "1.0.0",
                "service": "ha-ingestor",
                "description": "Production-grade Python service for ingesting Home Assistant activity to InfluxDB",
            }
        )

        self.logger.info("Custom Prometheus collector initialized")

    def collect(self) -> list[Metric]:
        """Collect all metrics.

        Returns:
            List of Prometheus metrics
        """
        try:
            # This method is called by Prometheus client to collect metrics
            # All our metrics are already registered with the registry
            # so we just return an empty list - the registry handles the rest
            return []

        except Exception as e:
            self.logger.error("Failed to collect metrics", error=str(e))
            return []

    def update_system_metrics(
        self,
        hostname: str,
        cpu_percent: float,
        memory_percent: float,
        memory_used_bytes: int,
        disk_usage_percent: float,
        disk_io_read_bytes: int,
        disk_io_write_bytes: int,
        network_io_sent_bytes: int,
        network_io_recv_bytes: int,
        mountpoint: str = "/",
        interface: str = "default",
    ) -> None:
        """Update system resource metrics.

        Args:
            hostname: System hostname
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            memory_used_bytes: Memory used in bytes
            disk_usage_percent: Disk usage percentage
            disk_io_read_bytes: Disk read I/O in bytes
            disk_io_write_bytes: Disk write I/O in bytes
            network_io_sent_bytes: Network sent I/O in bytes
            network_io_recv_bytes: Network received I/O in bytes
            mountpoint: Disk mountpoint
            interface: Network interface name
        """
        try:
            # Update system metrics
            self.system_cpu_percent.labels(hostname=hostname).set(cpu_percent)
            self.system_memory_percent.labels(hostname=hostname).set(memory_percent)
            self.system_memory_used_bytes.labels(hostname=hostname).set(
                memory_used_bytes
            )
            self.system_disk_usage_percent.labels(
                hostname=hostname, mountpoint=mountpoint
            ).set(disk_usage_percent)

            # Update cumulative I/O counters
            self.system_disk_io_read_bytes.labels(hostname=hostname).inc(
                disk_io_read_bytes
            )
            self.system_disk_io_write_bytes.labels(hostname=hostname).inc(
                disk_io_write_bytes
            )
            self.system_network_io_sent_bytes.labels(
                hostname=hostname, interface=interface
            ).inc(network_io_sent_bytes)
            self.system_network_io_recv_bytes.labels(
                hostname=hostname, interface=interface
            ).inc(network_io_recv_bytes)

        except Exception as e:
            self.logger.error("Failed to update system metrics", error=str(e))

    def observe_event_processing(
        self,
        duration_seconds: float,
        source: str = "unknown",
        domain: str = "unknown",
        entity_id: str = "unknown",
    ) -> None:
        """Observe event processing duration.

        Args:
            duration_seconds: Processing duration in seconds
            source: Event source (mqtt, websocket)
            domain: Event domain (light, switch, sensor, etc.)
            entity_id: Entity ID
        """
        try:
            self.event_processing_duration.labels(
                source=source, domain=domain, entity_id=entity_id
            ).observe(duration_seconds)

        except Exception as e:
            self.logger.error("Failed to observe event processing", error=str(e))

    def update_event_processing_rate(
        self, rate: float, source: str = "unknown"
    ) -> None:
        """Update event processing rate.

        Args:
            rate: Processing rate in events per second
            source: Event source
        """
        try:
            self.event_processing_rate.labels(source=source).set(rate)

        except Exception as e:
            self.logger.error("Failed to update event processing rate", error=str(e))

    def update_queue_depth(self, depth: int, queue_name: str = "default") -> None:
        """Update queue depth.

        Args:
            depth: Current queue depth
            queue_name: Name of the queue
        """
        try:
            self.queue_depth.labels(queue_name=queue_name).set(depth)

        except Exception as e:
            self.logger.error("Failed to update queue depth", error=str(e))

    def update_active_connections(
        self, count: int, connection_type: str = "unknown"
    ) -> None:
        """Update active connections count.

        Args:
            count: Number of active connections
            connection_type: Type of connection
        """
        try:
            self.active_connections.labels(connection_type=connection_type).set(count)

        except Exception as e:
            self.logger.error("Failed to update active connections", error=str(e))

    def increment_events_processed(
        self,
        source: str = "unknown",
        domain: str = "unknown",
        entity_id: str = "unknown",
        status: str = "success",
    ) -> None:
        """Increment events processed counter.

        Args:
            source: Event source
            domain: Event domain
            entity_id: Entity ID
            status: Processing status
        """
        try:
            self.events_processed_total.labels(
                source=source, domain=domain, entity_id=entity_id, status=status
            ).inc()

        except Exception as e:
            self.logger.error("Failed to increment events processed", error=str(e))

    def increment_data_points_written(
        self, count: int = 1, measurement: str = "unknown", status: str = "success"
    ) -> None:
        """Increment data points written counter.

        Args:
            count: Number of data points
            measurement: InfluxDB measurement name
            status: Write status
        """
        try:
            self.data_points_written_total.labels(
                measurement=measurement, status=status
            ).inc(count)

        except Exception as e:
            self.logger.error("Failed to increment data points written", error=str(e))

    def increment_data_volume(
        self, bytes_count: int, source: str = "unknown", data_type: str = "unknown"
    ) -> None:
        """Increment data volume counter.

        Args:
            bytes_count: Data volume in bytes
            source: Data source
            data_type: Type of data
        """
        try:
            self.data_volume_bytes.labels(source=source, type=data_type).inc(
                bytes_count
            )

        except Exception as e:
            self.logger.error("Failed to increment data volume", error=str(e))

    def update_deduplication_rate(self, rate: float, source: str = "unknown") -> None:
        """Update deduplication rate.

        Args:
            rate: Deduplication rate (0.0 to 1.0)
            source: Data source
        """
        try:
            self.deduplication_rate.labels(source=source).set(rate)

        except Exception as e:
            self.logger.error("Failed to update deduplication rate", error=str(e))

    def update_filter_efficiency(
        self, efficiency: float, filter_type: str = "unknown"
    ) -> None:
        """Update filter efficiency.

        Args:
            efficiency: Filter efficiency (0.0 to 1.0)
            filter_type: Type of filter
        """
        try:
            self.filter_efficiency.labels(filter_type=filter_type).set(efficiency)

        except Exception as e:
            self.logger.error("Failed to update filter efficiency", error=str(e))

    def update_transformation_success_rate(
        self, rate: float, transformer_type: str = "unknown"
    ) -> None:
        """Update transformation success rate.

        Args:
            rate: Success rate (0.0 to 1.0)
            transformer_type: Type of transformer
        """
        try:
            self.transformation_success_rate.labels(
                transformer_type=transformer_type
            ).set(rate)

        except Exception as e:
            self.logger.error(
                "Failed to update transformation success rate", error=str(e)
            )

    def increment_errors(
        self,
        error_type: str = "unknown",
        component: str = "unknown",
        severity: str = "unknown",
    ) -> None:
        """Increment error counter.

        Args:
            error_type: Type of error
            component: Component where error occurred
            severity: Error severity
        """
        try:
            self.errors_total.labels(
                error_type=error_type, component=component, severity=severity
            ).inc()

        except Exception as e:
            self.logger.error("Failed to increment error counter", error=str(e))

    def update_circuit_breaker_state(
        self, state: int, component: str = "unknown"
    ) -> None:
        """Update circuit breaker state.

        Args:
            state: Circuit breaker state (0=closed, 1=half_open, 2=open)
            component: Component name
        """
        try:
            self.circuit_breaker_state.labels(component=component).set(state)

        except Exception as e:
            self.logger.error("Failed to update circuit breaker state", error=str(e))

    def increment_retry_attempts(
        self, component: str = "unknown", operation: str = "unknown"
    ) -> None:
        """Increment retry attempts counter.

        Args:
            component: Component name
            operation: Operation name
        """
        try:
            self.retry_attempts_total.labels(
                component=component, operation=operation
            ).inc()

        except Exception as e:
            self.logger.error("Failed to increment retry attempts", error=str(e))

    def export_metrics(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        try:
            return generate_latest(self.registry)

        except Exception as e:
            self.logger.error("Failed to export metrics", error=str(e))
            return ""

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of all registered metrics.

        Returns:
            Dictionary with metrics summary
        """
        try:
            metrics = {}

            # Collect all metrics from the registry
            for metric in self.registry.collect():
                metric_name = metric.name
                metric_type = metric.type
                metric_samples = []

                for sample in metric.samples:
                    metric_samples.append(
                        {
                            "name": sample.name,
                            "labels": sample.labels,
                            "value": sample.value,
                            "timestamp": sample.timestamp,
                            "exemplar": sample.exemplar,
                        }
                    )

                metrics[metric_name] = {
                    "type": metric_type,
                    "help": metric.documentation,
                    "samples": metric_samples,
                }

            return {
                "registry": str(self.registry),
                "metrics_count": len(metrics),
                "metrics": metrics,
            }

        except Exception as e:
            self.logger.error("Failed to get metrics summary", error=str(e))
            return {}


def create_prometheus_collector(
    registry: CollectorRegistry | None = None,
) -> HAIngestorCollector:
    """Create a custom Prometheus collector.

    Args:
        registry: Optional Prometheus registry to use

    Returns:
        Configured HAIngestorCollector instance
    """
    return HAIngestorCollector(registry)


# Global collector instance
_global_collector: HAIngestorCollector | None = None


def get_prometheus_collector() -> HAIngestorCollector:
    """Get the global Prometheus collector instance.

    Returns:
        Global HAIngestorCollector instance
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = create_prometheus_collector()
    return _global_collector


def set_prometheus_collector(collector: HAIngestorCollector) -> None:
    """Set the global Prometheus collector instance.

    Args:
        collector: HAIngestorCollector instance to set as global
    """
    global _global_collector
    _global_collector = collector
