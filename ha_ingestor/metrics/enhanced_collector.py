"""Enhanced metrics collector integrating performance monitoring and Prometheus metrics."""

import asyncio
import time
from typing import Any

from ..monitoring.performance_monitor import get_performance_monitor
from ..utils.logging import get_logger
from .collector import get_metrics_collector
from .prometheus_collector import get_prometheus_collector


class EnhancedMetricsCollector:
    """Enhanced metrics collector that integrates multiple monitoring systems."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize enhanced metrics collector.

        Args:
            config: Configuration dictionary for monitoring settings
        """
        self.logger = get_logger(__name__)
        self.config = config or {}

        # Initialize components
        self.registry = get_metrics_collector()
        self.prometheus_collector = get_prometheus_collector()
        self.performance_monitor = get_performance_monitor()

        # Integration settings
        self.enable_integration = self.config.get("enable_integration", True)
        self.sync_interval = self.config.get("sync_interval", 10.0)  # seconds
        self.enable_auto_sync = self.config.get("enable_auto_sync", True)

        # Auto-sync task
        self._sync_task: asyncio.Task | None = None
        self._running = False
        self._start_time = time.time()

        self.logger.info(
            "Enhanced metrics collector initialized",
            enable_integration=self.enable_integration,
            sync_interval=self.sync_interval,
            enable_auto_sync=self.enable_auto_sync,
        )

    async def start(self) -> None:
        """Start the enhanced metrics collector."""
        self.logger.info("Starting enhanced metrics collector")

        try:
            # Start performance monitoring
            if self.performance_monitor:
                self._sync_task = asyncio.create_task(self._auto_sync_metrics())
                self._running = True
                self.logger.info("Enhanced metrics collector started successfully")

        except Exception as e:
            self.logger.error(
                "Failed to start enhanced metrics collector", error=str(e)
            )
            raise

    async def stop(self) -> None:
        """Stop the enhanced metrics collector."""
        self.logger.info("Stopping enhanced metrics collector")

        try:
            self._running = False

            if self._sync_task and not self._sync_task.done():
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Enhanced metrics collector stopped successfully")

        except Exception as e:
            self.logger.error("Failed to stop enhanced metrics collector", error=str(e))

    async def _auto_sync_metrics(self) -> None:
        """Automatically sync metrics between different collectors."""
        self.logger.info("Starting automatic metrics synchronization")

        try:
            while self._running:
                await self.sync_metrics()
                await asyncio.sleep(self.sync_interval)

        except asyncio.CancelledError:
            self.logger.info("Metrics synchronization cancelled")
        except Exception as e:
            self.logger.error("Metrics synchronization failed", error=str(e))

    async def sync_metrics(self) -> None:
        """Synchronize metrics between different collectors."""
        try:
            if not self.enable_integration:
                return

            # Get current metrics from performance monitor
            performance_summary = self.performance_monitor.get_metrics_summary()

            # Sync system metrics to Prometheus collector
            if "current_metrics" in performance_summary:
                system_metrics = performance_summary["current_metrics"].get(
                    "system", {}
                )
                if system_metrics:
                    await self._sync_system_metrics(system_metrics)

                performance_metrics = performance_summary["current_metrics"].get(
                    "performance", {}
                )
                if performance_metrics:
                    await self._sync_performance_metrics(performance_metrics)

                business_metrics = performance_summary["current_metrics"].get(
                    "business", {}
                )
                if business_metrics:
                    await self._sync_business_metrics(business_metrics)

            self.logger.debug("Metrics synchronization completed")

        except Exception as e:
            self.logger.error("Failed to sync metrics", error=str(e))

    async def _sync_system_metrics(self, system_metrics: dict[str, Any]) -> None:
        """Sync system metrics to Prometheus collector.

        Args:
            system_metrics: System metrics from performance monitor
        """
        try:
            import platform

            import psutil

            hostname = platform.node()

            # Extract system metrics
            cpu_percent = system_metrics.get("cpu_percent", 0.0)
            memory_percent = system_metrics.get("memory_percent", 0.0)
            memory_used_mb = system_metrics.get("memory_used_mb", 0.0)
            disk_usage_percent = system_metrics.get("disk_usage_percent", 0.0)

            # Get I/O counters
            io_counters = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()

            # Convert memory to bytes
            memory_used_bytes = int(memory_used_mb * 1024 * 1024)

            # Update Prometheus collector (placeholder values for I/O metrics)
            self.prometheus_collector.update_system_metrics(
                hostname=hostname,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_bytes=memory_used_bytes,
                disk_usage_percent=disk_usage_percent,
                disk_io_read_bytes=(
                    getattr(io_counters, "read_bytes", 0) if io_counters else 0
                ),
                disk_io_write_bytes=(
                    getattr(io_counters, "write_bytes", 0) if io_counters else 0
                ),
                network_io_sent_bytes=getattr(net_io, "bytes_sent", 0) if net_io else 0,
                network_io_recv_bytes=getattr(net_io, "bytes_recv", 0) if net_io else 0,
            )

        except Exception as e:
            self.logger.error("Failed to sync system metrics", error=str(e))

    async def _sync_performance_metrics(
        self, performance_metrics: dict[str, Any]
    ) -> None:
        """Sync performance metrics to Prometheus collector.

        Args:
            performance_metrics: Performance metrics from performance monitor
        """
        try:
            # Extract performance metrics
            event_processing_rate = performance_metrics.get(
                "event_processing_rate", 0.0
            )
            error_rate = performance_metrics.get("error_rate", 0.0)

            # Update Prometheus collector
            self.prometheus_collector.update_event_processing_rate(
                rate=event_processing_rate, source="overall"
            )

            # Update error metrics
            if error_rate > 0:
                self.prometheus_collector.increment_errors(
                    error_type="processing", component="pipeline", severity="warning"
                )

        except Exception as e:
            self.logger.error("Failed to sync performance metrics", error=str(e))

    async def _sync_business_metrics(self, business_metrics: dict[str, Any]) -> None:
        """Sync business metrics to Prometheus collector.

        Args:
            business_metrics: Business metrics from performance monitor
        """
        try:
            # Extract business metrics
            total_events = business_metrics.get("total_events_processed", 0)
            data_points_written = business_metrics.get("data_points_written", 0)
            deduplication_rate = business_metrics.get("deduplication_rate", 0.0)
            filter_efficiency = business_metrics.get("filter_efficiency", 0.0)
            transformation_success_rate = business_metrics.get(
                "transformation_success_rate", 0.0
            )

            # Update Prometheus collector
            if total_events > 0:
                self.prometheus_collector.increment_events_processed(
                    source="overall", domain="all", entity_id="all", status="success"
                )

            if data_points_written > 0:
                self.prometheus_collector.increment_data_points_written(
                    count=data_points_written,
                    measurement="home_assistant",
                    status="success",
                )

            self.prometheus_collector.update_deduplication_rate(
                rate=deduplication_rate, source="overall"
            )

            self.prometheus_collector.update_filter_efficiency(
                efficiency=filter_efficiency, filter_type="overall"
            )

            self.prometheus_collector.update_transformation_success_rate(
                rate=transformation_success_rate, transformer_type="overall"
            )

        except Exception as e:
            self.logger.error("Failed to sync business metrics", error=str(e))

    def record_event_processing(
        self,
        duration_seconds: float,
        source: str = "unknown",
        domain: str = "unknown",
        entity_id: str = "unknown",
        success: bool = True,
    ) -> None:
        """Record event processing metrics across all collectors.

        Args:
            duration_seconds: Processing duration in seconds
            source: Event source (mqtt, websocket)
            domain: Event domain (light, switch, sensor, etc.)
            entity_id: Entity ID
            success: Whether processing was successful
        """
        try:
            # Record in performance monitor
            if self.performance_monitor:
                duration_ms = duration_seconds * 1000
                self.performance_monitor.record_processing_time(duration_ms)
                self.performance_monitor.record_event_processed(
                    source, domain, entity_id
                )

                if not success:
                    self.performance_monitor.record_error("processing")

            # Record in Prometheus collector
            self.prometheus_collector.observe_event_processing(
                duration_seconds=duration_seconds,
                source=source,
                domain=domain,
                entity_id=entity_id,
            )

            # Record in existing metrics collector
            self.registry.record_event_processed(source, success)

        except Exception as e:
            self.logger.error("Failed to record event processing", error=str(e))

    def record_error(
        self, error_type: str, component: str = "unknown", severity: str = "unknown"
    ) -> None:
        """Record error metrics across all collectors.

        Args:
            error_type: Type of error
            component: Component where error occurred
            severity: Error severity
        """
        try:
            # Record in performance monitor
            if self.performance_monitor:
                self.performance_monitor.record_error(error_type)

            # Record in Prometheus collector
            self.prometheus_collector.increment_errors(
                error_type=error_type, component=component, severity=severity
            )

            # Record in existing metrics collector
            self.registry.record_error(error_type, severity, False)

        except Exception as e:
            self.logger.error("Failed to record error", error=str(e))

    def record_circuit_breaker_state(
        self, state: str, component: str = "unknown"
    ) -> None:
        """Record circuit breaker state across all collectors.

        Args:
            state: Circuit breaker state (closed, half_open, open)
            component: Component name
        """
        try:
            # Record in performance monitor
            if self.performance_monitor:
                self.performance_monitor.record_circuit_breaker_state(component, state)

            # Record in Prometheus collector
            state_value = {"closed": 0, "half_open": 1, "open": 2}.get(state, 0)
            self.prometheus_collector.update_circuit_breaker_state(
                state=state_value, component=component
            )

            # Record in existing metrics collector
            self.registry.record_circuit_breaker_state(component, state)

        except Exception as e:
            self.logger.error("Failed to record circuit breaker state", error=str(e))

    def record_retry_attempt(
        self, component: str = "unknown", operation: str = "unknown"
    ) -> None:
        """Record retry attempt across all collectors.

        Args:
            component: Component name
            operation: Operation name
        """
        try:
            # Record in performance monitor
            if self.performance_monitor:
                self.performance_monitor.record_retry_attempt(component, operation)

            # Record in Prometheus collector
            self.prometheus_collector.increment_retry_attempts(
                component=component, operation=operation
            )

            # Record in existing metrics collector
            self.registry.record_retry_attempt(component, operation)

        except Exception as e:
            self.logger.error("Failed to record retry attempt", error=str(e))

    def get_comprehensive_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics from all collectors.

        Returns:
            Dictionary with comprehensive metrics from all sources
        """
        try:
            # Get metrics from all collectors
            registry_summary = self.registry.get_metrics_summary()
            prometheus_summary = self.prometheus_collector.get_metrics_summary()
            performance_summary = self.performance_monitor.get_metrics_summary()

            return {
                "timestamp": time.time(),
                "registry_metrics": registry_summary,
                "prometheus_metrics": prometheus_summary,
                "performance_metrics": performance_summary,
                "integration_status": {
                    "enabled": self.enable_integration,
                    "auto_sync": self.enable_auto_sync,
                    "running": self._running,
                    "last_sync": time.time(),
                },
            }

        except Exception as e:
            self.logger.error("Failed to get comprehensive metrics", error=str(e))
            return {}

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format from all collectors.

        Returns:
            Prometheus-formatted metrics string
        """
        try:
            # Export from Prometheus collector
            prometheus_metrics = self.prometheus_collector.export_metrics()

            # Export from existing registry
            registry_metrics = self.registry.export_prometheus()

            # Combine metrics
            combined_metrics = f"{prometheus_metrics}\n{registry_metrics}"

            return combined_metrics

        except Exception as e:
            self.logger.error("Failed to export Prometheus metrics", error=str(e))
            return ""

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics in a structured format.

        Returns:
            Dictionary with all metrics data
        """
        try:
            metrics = {}

            # Get basic metrics
            metrics["ha_ingestor_up"] = 1
            metrics["ha_ingestor_uptime_seconds"] = time.time() - getattr(
                self, "_start_time", time.time()
            )

            # Get registry metrics if available
            if self.registry:
                try:
                    registry_metrics = self.registry.get_all_metrics()
                    for name, metric in registry_metrics.items():
                        metrics[name] = (
                            metric.value if hasattr(metric, "value") else str(metric)
                        )
                except AttributeError:
                    # Fallback to metrics summary if get_all_metrics doesn't exist
                    registry_summary = self.registry.get_metrics_summary()
                    if isinstance(registry_summary, dict):
                        metrics.update(registry_summary)

            # Get Prometheus metrics if available
            if self.prometheus_collector:
                try:
                    prometheus_metrics = self.prometheus_collector.get_metrics_summary()
                    metrics.update(prometheus_metrics)
                except Exception:
                    pass

            # Add timestamp
            metrics["timestamp"] = time.time()

            return metrics

        except Exception as e:
            self.logger.error("Failed to get all metrics", error=str(e))
            return {
                "ha_ingestor_up": 1,
                "ha_ingestor_uptime_seconds": time.time()
                - getattr(self, "_start_time", time.time()),
                "timestamp": time.time(),
                "error": "Failed to get metrics",
            }

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the enhanced metrics collector.

        Returns:
            Dictionary with health status information
        """
        try:
            return {
                "status": "healthy" if self._running else "stopped",
                "components": {
                    "registry": "active" if self.registry else "inactive",
                    "prometheus_collector": (
                        "active" if self.prometheus_collector else "inactive"
                    ),
                    "performance_monitor": (
                        "active" if self.performance_monitor else "inactive"
                    ),
                },
                "integration": {
                    "enabled": self.enable_integration,
                    "auto_sync": self.enable_auto_sync,
                    "last_sync": time.time() if self._running else None,
                },
                "metrics_count": {
                    "registry": (
                        len(self.registry.get_metric_names()) if self.registry else 0
                    ),
                    "prometheus": (
                        len(self.prometheus_collector.registry.collect())
                        if self.prometheus_collector
                        else 0
                    ),
                },
            }

        except Exception as e:
            self.logger.error("Failed to get health status", error=str(e))
            return {"status": "error", "error": str(e)}


def create_enhanced_metrics_collector(
    config: dict[str, Any] | None = None
) -> EnhancedMetricsCollector:
    """Create an enhanced metrics collector.

    Args:
        config: Configuration dictionary for monitoring settings

    Returns:
        Configured EnhancedMetricsCollector instance
    """
    return EnhancedMetricsCollector(config)


# Global enhanced collector instance
_global_enhanced_collector: EnhancedMetricsCollector | None = None


def get_enhanced_metrics_collector() -> EnhancedMetricsCollector:
    """Get the global enhanced metrics collector instance.

    Returns:
        Global EnhancedMetricsCollector instance
    """
    global _global_enhanced_collector
    if _global_enhanced_collector is None:
        _global_enhanced_collector = create_enhanced_metrics_collector()
    return _global_enhanced_collector


def set_enhanced_metrics_collector(collector: EnhancedMetricsCollector) -> None:
    """Set the global enhanced metrics collector instance.

    Args:
        collector: EnhancedMetricsCollector instance to set as global
    """
    global _global_enhanced_collector
    _global_enhanced_collector = collector
