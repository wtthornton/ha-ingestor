"""Metrics collector for integrating with existing components."""

import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from ..utils.logging import get_logger, log_performance
from .registry import MetricsRegistry


class MetricsCollector:
    """Collector for gathering metrics from various components."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.logger = get_logger(__name__)
        self.registry = MetricsRegistry()
        self._setup_default_metrics()
        
    def _setup_default_metrics(self) -> None:
        """Setup default metrics for the service."""
        # Service metrics
        self.registry.register_gauge(
            "ha_ingestor_uptime_seconds",
            "Service uptime in seconds"
        )
        
        # Event processing metrics
        self.registry.register_counter(
            "ha_ingestor_events_processed_total",
            "Total number of events processed"
        )
        self.registry.register_counter(
            "ha_ingestor_events_mqtt_total",
            "Total number of MQTT events processed"
        )
        self.registry.register_counter(
            "ha_ingestor_events_websocket_total",
            "Total number of WebSocket events processed"
        )
        self.registry.register_counter(
            "ha_ingestor_events_deduplicated_total",
            "Total number of events deduplicated"
        )
        self.registry.register_counter(
            "ha_ingestor_events_failed_total",
            "Total number of events that failed processing"
        )
        
        # Pipeline metrics
        self.registry.register_gauge(
            "ha_ingestor_pipeline_queue_size",
            "Current size of the event processing queue"
        )
        self.registry.register_histogram(
            "ha_ingestor_pipeline_processing_duration_seconds",
            "Time taken to process events through the pipeline"
        )
        
        # Client connection metrics
        self.registry.register_gauge(
            "ha_ingestor_mqtt_connected",
            "MQTT client connection status (1=connected, 0=disconnected)"
        )
        self.registry.register_gauge(
            "ha_ingestor_websocket_connected",
            "WebSocket client connection status (1=connected, 0=disconnected)"
        )
        self.registry.register_gauge(
            "ha_ingestor_influxdb_connected",
            "InfluxDB connection status (1=connected, 0=disconnected)"
        )
        
        # Connection performance metrics
        self.registry.register_histogram(
            "ha_ingestor_connection_latency_seconds",
            "Connection latency in seconds"
        )
        self.registry.register_histogram(
            "ha_ingestor_connection_response_time_seconds",
            "Connection response time in seconds"
        )
        self.registry.register_gauge(
            "ha_ingestor_connection_throughput_bps",
            "Connection throughput in bits per second"
        )
        self.registry.register_counter(
            "ha_ingestor_connection_errors_total",
            "Total number of connection errors"
        )
        self.registry.register_counter(
            "ha_ingestor_connection_reconnects_total",
            "Total number of connection reconnections"
        )
        self.registry.register_gauge(
            "ha_ingestor_connection_uptime_seconds",
            "Connection uptime in seconds"
        )
        
        # Filter system metrics
        self.registry.register_counter(
            "ha_ingestor_filters_events_processed_total",
            "Total number of events processed by filters"
        )
        self.registry.register_counter(
            "ha_ingestor_filters_events_filtered_total",
            "Total number of events filtered out by filters"
        )
        self.registry.register_counter(
            "ha_ingestor_filters_cache_hits_total",
            "Total number of filter cache hits"
        )
        self.registry.register_counter(
            "ha_ingestor_filters_cache_misses_total",
            "Total number of filter cache misses"
        )
        self.registry.register_gauge(
            "ha_ingestor_filters_cache_size",
            "Current size of filter caches"
        )
        self.registry.register_histogram(
            "ha_ingestor_filters_processing_duration_seconds",
            "Time taken to process events through filters"
        )
        self.registry.register_histogram(
            "ha_ingestor_filter_chain_processing_duration_seconds",
            "Time taken to process events through the entire filter chain"
        )
        self.registry.register_gauge(
            "ha_ingestor_filter_chain_total_filters",
            "Total number of filters in the chain"
        )
        self.registry.register_gauge(
            "ha_ingestor_filter_chain_filter_rate",
            "Rate of events filtered out by the chain (0.0 to 1.0)"
        )
        
        # Error handling metrics
        self.registry.register_counter(
            "ha_ingestor_errors_total",
            "Total number of errors encountered"
        )
        self.registry.register_counter(
            "ha_ingestor_errors_by_category_total",
            "Total number of errors by category"
        )
        self.registry.register_counter(
            "ha_ingestor_errors_by_severity_total",
            "Total number of errors by severity"
        )
        self.registry.register_counter(
            "ha_ingestor_errors_recovered_total",
            "Total number of errors successfully recovered from"
        )
        self.registry.register_counter(
            "ha_ingestor_errors_unrecovered_total",
            "Total number of errors that could not be recovered from"
        )
        self.registry.register_counter(
            "ha_ingestor_circuit_breaker_opens_total",
            "Total number of circuit breaker opens"
        )
        self.registry.register_gauge(
            "ha_ingestor_circuit_breaker_state",
            "Current circuit breaker state (0=closed, 1=open, 2=half_open)"
        )
        self.registry.register_counter(
            "ha_ingestor_retry_attempts_total",
            "Total number of retry attempts"
        )
        
        # InfluxDB metrics
        self.registry.register_counter(
            "ha_ingestor_influxdb_points_written_total",
            "Total number of data points written to InfluxDB"
        )
        self.registry.register_counter(
            "ha_ingestor_influxdb_points_failed_total",
            "Total number of data points that failed to write to InfluxDB"
        )
        self.registry.register_histogram(
            "ha_ingestor_influxdb_write_duration_seconds",
            "Time taken to write data points to InfluxDB"
        )
        self.registry.register_gauge(
            "ha_ingestor_influxdb_batch_size",
            "Current InfluxDB batch size"
        )
        
        # Enhanced InfluxDB batch performance metrics
        self.registry.register_counter(
            "ha_ingestor_influxdb_batches_processed_total",
            "Total number of batches processed"
        )
        self.registry.register_counter(
            "ha_ingestor_influxdb_batches_failed_total",
            "Total number of batches that failed to process"
        )
        self.registry.register_histogram(
            "ha_ingestor_influxdb_batch_processing_duration_seconds",
            "Time taken to process batches (including optimization and compression)"
        )
        self.registry.register_histogram(
            "ha_ingestor_influxdb_batch_age_seconds",
            "Age of batches before processing (time from first point to flush)"
        )
        self.registry.register_gauge(
            "ha_ingestor_influxdb_batch_compression_ratio",
            "Compression ratio achieved (original_size / compressed_size)"
        )
        self.registry.register_gauge(
            "ha_ingestor_influxdb_batch_optimization_efficiency",
            "Efficiency of batch optimization (points_after / points_before)"
        )
        self.registry.register_counter(
            "ha_ingestor_influxdb_retry_attempts_total",
            "Total number of retry attempts for failed writes"
        )
        self.registry.register_counter(
            "ha_ingestor_influxdb_circuit_breaker_opens_total",
            "Total number of times circuit breaker opened"
        )
        self.registry.register_gauge(
            "ha_ingestor_influxdb_circuit_breaker_state",
            "Current circuit breaker state (0=closed, 1=half_open, 2=open)"
        )
        self.registry.register_histogram(
            "ha_ingestor_influxdb_throughput_points_per_second",
            "Throughput of points written per second"
        )
        self.registry.register_histogram(
            "ha_ingestor_influxdb_throughput_batches_per_second",
            "Throughput of batches processed per second"
        )
        
        # Error metrics
        self.registry.register_counter(
            "ha_ingestor_errors_total",
            "Total number of errors encountered"
        )
        self.registry.register_counter(
            "ha_ingestor_connection_errors_total",
            "Total number of connection errors"
        )
        
        self.logger.info("Default metrics registered", count=len(self.registry.get_metric_names()))
    
    def record_event_processed(self, source: str, success: bool = True) -> None:
        """Record that an event was processed.
        
        Args:
            source: Event source (mqtt, websocket)
            success: Whether processing was successful
        """
        # Increment total events processed
        self.registry.increment_counter("ha_ingestor_events_processed_total")
        
        # Increment source-specific counter
        if source.lower() == "mqtt":
            self.registry.increment_counter("ha_ingestor_events_mqtt_total")
        elif source.lower() == "websocket":
            self.registry.increment_counter("ha_ingestor_events_websocket_total")
        
        # Record failed events
        if not success:
            self.registry.increment_counter("ha_ingestor_events_failed_total")
    
    def record_event_deduplicated(self) -> None:
        """Record that an event was deduplicated."""
        self.registry.increment_counter("ha_ingestor_events_deduplicated_total")
    
    def record_pipeline_queue_size(self, size: int) -> None:
        """Record current pipeline queue size.
        
        Args:
            size: Current queue size
        """
        self.registry.set_gauge("ha_ingestor_pipeline_queue_size", size)
    
    def record_pipeline_processing_time(self, duration_seconds: float) -> None:
        """Record pipeline processing time.
        
        Args:
            duration_seconds: Processing time in seconds
        """
        self.registry.observe_histogram(
            "ha_ingestor_pipeline_processing_duration_seconds",
            duration_seconds
        )
    
    def record_client_connection_status(self, client_type: str, connected: bool) -> None:
        """Record client connection status.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
            connected: Whether client is connected
        """
        metric_name = f"ha_ingestor_{client_type.lower()}_connected"
        status_value = 1.0 if connected else 0.0
        self.registry.set_gauge(metric_name, status_value)
    
    def record_connection_latency(self, client_type: str, latency_seconds: float) -> None:
        """Record connection latency.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
            latency_seconds: Latency in seconds
        """
        self.registry.observe_histogram("ha_ingestor_connection_latency_seconds", latency_seconds, {
            "client_type": client_type.lower()
        })
    
    def record_connection_response_time(self, client_type: str, response_time_seconds: float) -> None:
        """Record connection response time.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
            response_time_seconds: Response time in seconds
        """
        self.registry.observe_histogram("ha_ingestor_connection_response_time_seconds", response_time_seconds, {
            "client_type": client_type.lower()
        })
    
    def record_connection_throughput(self, client_type: str, throughput_bps: float) -> None:
        """Record connection throughput.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
            throughput_bps: Throughput in bits per second
        """
        self.registry.set_gauge("ha_ingestor_connection_throughput_bps", throughput_bps, {
            "client_type": client_type.lower()
        })
    
    def record_connection_error(self, client_type: str) -> None:
        """Record a connection error.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
        """
        self.registry.increment_counter("ha_ingestor_connection_errors_total")
    
    def record_connection_reconnect(self, client_type: str) -> None:
        """Record a connection reconnection.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
        """
        self.registry.increment_counter("ha_ingestor_connection_reconnects_total")
    
    def record_connection_uptime(self, client_type: str, uptime_seconds: float) -> None:
        """Record connection uptime.
        
        Args:
            client_type: Type of client (mqtt, websocket, influxdb)
            uptime_seconds: Uptime in seconds
        """
        self.registry.set_gauge("ha_ingestor_connection_uptime_seconds", uptime_seconds)
    
    def record_influxdb_write(self, points_count: int, success: bool, duration_seconds: float) -> None:
        """Record InfluxDB write operation.
        
        Args:
            points_count: Number of points written
            success: Whether write was successful
            duration_seconds: Write duration in seconds
        """
        if success:
            self.registry.increment_counter(
                "ha_ingestor_influxdb_points_written_total",
                value=points_count
            )
        else:
            self.registry.increment_counter(
                "ha_ingestor_influxdb_points_failed_total",
                value=points_count
            )
        
        # Record write duration
        self.registry.observe_histogram(
            "ha_ingestor_influxdb_write_duration_seconds",
            duration_seconds
        )
    
    def record_influxdb_batch_size(self, batch_size: int) -> None:
        """Record current InfluxDB batch size.
        
        Args:
            batch_size: Current batch size
        """
        self.registry.set_gauge("ha_ingestor_influxdb_batch_size", batch_size)
    
    def record_influxdb_batch_processed(self, success: bool, processing_duration: float, 
                                      batch_age: float, original_size: int, 
                                      optimized_size: int, original_data_size: int, 
                                      compressed_data_size: int) -> None:
        """Record comprehensive InfluxDB batch processing metrics.
        
        Args:
            success: Whether batch processing was successful
            processing_duration: Total processing time including optimization and compression
            batch_age: Age of batch before processing
            original_size: Number of points before optimization
            optimized_size: Number of points after optimization
            original_data_size: Size of data before compression in bytes
            compressed_data_size: Size of data after compression in bytes
        """
        if success:
            self.registry.increment_counter("ha_ingestor_influxdb_batches_processed_total")
        else:
            self.registry.increment_counter("ha_ingestor_influxdb_batches_failed_total")
        
        # Record processing duration
        self.registry.observe_histogram(
            "ha_ingestor_influxdb_batch_processing_duration_seconds",
            processing_duration
        )
        
        # Record batch age
        self.registry.observe_histogram(
            "ha_ingestor_influxdb_batch_age_seconds",
            batch_age
        )
        
        # Record optimization efficiency
        if original_size > 0:
            efficiency = optimized_size / original_size
            self.registry.set_gauge("ha_ingestor_influxdb_batch_optimization_efficiency", efficiency)
        
        # Record compression ratio
        if compressed_data_size > 0:
            compression_ratio = original_data_size / compressed_data_size
            self.registry.set_gauge("ha_ingestor_influxdb_batch_compression_ratio", compression_ratio)
    
    def record_influxdb_retry_attempt(self, attempt_number: int) -> None:
        """Record InfluxDB retry attempt.
        
        Args:
            attempt_number: The retry attempt number
        """
        self.registry.increment_counter("ha_ingestor_influxdb_retry_attempts_total")
    
    def record_influxdb_circuit_breaker_state(self, state: str) -> None:
        """Record InfluxDB circuit breaker state.
        
        Args:
            state: Circuit breaker state (closed, half_open, open)
        """
        state_value = 0.0  # closed
        if state == "half_open":
            state_value = 1.0
        elif state == "open":
            state_value = 2.0
        
        self.registry.set_gauge("ha_ingestor_influxdb_circuit_breaker_state", state_value)
    
    def record_influxdb_circuit_breaker_opened(self) -> None:
        """Record that InfluxDB circuit breaker opened."""
        self.registry.increment_counter("ha_ingestor_influxdb_circuit_breaker_opens_total")
    
    def record_influxdb_throughput(self, points_per_second: float, batches_per_second: float) -> None:
        """Record InfluxDB throughput metrics.
        
        Args:
            points_per_second: Points written per second
            batches_per_second: Batches processed per second
        """
        self.registry.observe_histogram(
            "ha_ingestor_influxdb_throughput_points_per_second",
            points_per_second
        )
        self.registry.observe_histogram(
            "ha_ingestor_influxdb_throughput_batches_per_second",
            batches_per_second
        )
    
    def record_error(self, error_type: str = "general") -> None:
        """Record an error occurrence.
        
        Args:
            error_type: Type of error
        """
        self.registry.increment_counter("ha_ingestor_errors_total")
        
        if error_type.lower() in ["connection", "connect", "network"]:
            self.registry.increment_counter("ha_ingestor_connection_errors_total")
    
    def update_uptime(self) -> None:
        """Update the uptime metric."""
        uptime = self.registry.get_uptime_seconds()
        self.registry.set_gauge("ha_ingestor_uptime_seconds", uptime)
    
    @log_performance("metrics_collection")
    def collect_component_metrics(self, component_name: str, metrics: Dict[str, Any]) -> None:
        """Collect metrics from a specific component.
        
        Args:
            component_name: Name of the component
            metrics: Dictionary of metrics from the component
        """
        try:
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    # Create component-specific metric name
                    full_metric_name = f"ha_ingestor_{component_name}_{metric_name}"
                    
                    # Register if not exists (as gauge)
                    if full_metric_name not in self.registry.get_metric_names():
                        self.registry.register_gauge(
                            full_metric_name,
                            f"{component_name} {metric_name}"
                        )
                    
                    # Set the value
                    self.registry.set_gauge(full_metric_name, float(value))
                    
        except Exception as e:
            self.logger.error("Failed to collect component metrics", 
                            component=component_name, error=str(e))
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        return self.registry.get_metrics_summary()
    
    def export_prometheus(self) -> str:
        """Export all metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        # Update uptime before export
        self.update_uptime()
        return self.registry.export_prometheus()
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics."""
        self.registry.clear_all_metrics()
        self.logger.info("All metrics cleared")
    
    @asynccontextmanager
    async def timed_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations and recording metrics.
        
        Args:
            operation_name: Name of the operation being timed
            labels: Optional labels for the metric
        """
        start_time = time.time()
        try:
            yield
            duration = time.time() - start_time
            
            # Record timing metric
            metric_name = f"ha_ingestor_{operation_name}_duration_seconds"
            
            # Register if not exists
            if metric_name not in self.registry.get_metric_names():
                self.registry.register_histogram(
                    metric_name,
                    f"Duration of {operation_name} operation"
                )
            
            self.registry.observe_histogram(metric_name, duration, labels)
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error("Operation failed", 
                            operation=operation_name, 
                            duration_seconds=duration,
                            error=str(e))
            raise
    
    def record_error(self, category: str, severity: str, recovered: bool = False) -> None:
        """Record an error occurrence.
        
        Args:
            category: Error category
            severity: Error severity
            recovered: Whether the error was recovered from
        """
        try:
            # Increment total errors counter
            self.registry.increment_counter("ha_ingestor_errors_total")
            
            # Increment category-specific counter
            self.registry.increment_counter(
                "ha_ingestor_errors_by_category_total"
            )
            
            # Increment severity-specific counter
            self.registry.increment_counter(
                "ha_ingestor_errors_by_severity_total"
            )
            
            # Increment recovery-specific counter
            if recovered:
                self.registry.increment_counter("ha_ingestor_errors_recovered_total")
            else:
                self.registry.increment_counter("ha_ingestor_errors_unrecovered_total")
                
        except Exception as e:
            self.logger.error("Failed to record error metrics", error=str(e))
    
    def record_circuit_breaker_open(self, component: str) -> None:
        """Record a circuit breaker opening.
        
        Args:
            component: Component name where circuit breaker opened
        """
        try:
            self.registry.increment_counter(
                "ha_ingestor_circuit_breaker_opens_total"
            )
        except Exception as e:
            self.logger.error("Failed to record circuit breaker metrics", error=str(e))
    
    def record_circuit_breaker_state(self, component: str, state: str) -> None:
        """Record circuit breaker state change.
        
        Args:
            component: Component name
            state: Circuit breaker state (closed=0, open=1, half_open=2)
        """
        try:
            state_value = {"closed": 0, "open": 1, "half_open": 2}.get(state, 0)
            self.registry.set_gauge(
                "ha_ingestor_circuit_breaker_state",
                float(state_value)
            )
        except Exception as e:
            self.logger.error("Failed to record circuit breaker state", error=str(e))
    
    def record_retry_attempt(self, component: str, operation: str) -> None:
        """Record a retry attempt.
        
        Args:
            component: Component name
            operation: Operation name
        """
        try:
            self.registry.increment_counter(
                "ha_ingestor_retry_attempts_total"
            )
        except Exception as e:
            self.logger.error("Failed to record retry metrics", error=str(e))
    
    def record_filter_metrics(self, filter_name: str, filter_type: str, 
                            processing_time: float, cache_hit: bool, 
                            event_filtered: bool) -> None:
        """Record metrics for filter operations.
        
        Args:
            filter_name: Name of the filter
            filter_type: Type of the filter (domain, entity, attribute, etc.)
            processing_time: Processing time in seconds
            cache_hit: Whether this was a cache hit
            event_filtered: Whether the event was filtered out
        """
        try:
            # Record processing duration
            self.registry.observe_histogram(
                "ha_ingestor_filters_processing_duration_seconds",
                processing_time
            )
            
            # Record cache metrics
            if cache_hit:
                self.registry.increment_counter(
                    "ha_ingestor_filters_cache_hits_total"
                )
            else:
                self.registry.increment_counter(
                    "ha_ingestor_filters_cache_misses_total"
                )
            
            # Record event processing metrics
            self.registry.increment_counter(
                "ha_ingestor_filters_events_processed_total"
            )
            
            if event_filtered:
                self.registry.increment_counter(
                    "ha_ingestor_filters_events_filtered_total"
                )
                
        except Exception as e:
            self.logger.error("Failed to record filter metrics", error=str(e))
    
    def record_filter_chain_metrics(self, total_filters: int, total_processed: int, 
                                  total_filtered: int, processing_time: float) -> None:
        """Record metrics for filter chain operations.
        
        Args:
            total_filters: Total number of filters in the chain
            total_processed: Total number of events processed
            total_filtered: Total number of events filtered out
            processing_time: Total processing time in seconds
        """
        try:
            # Record filter chain processing duration
            self.registry.observe_histogram(
                "ha_ingestor_filter_chain_processing_duration_seconds",
                processing_time
            )
            
            # Record filter chain statistics
            self.registry.set_gauge(
                "ha_ingestor_filter_chain_total_filters",
                float(total_filters)
            )
            
            # Calculate and record filter rate
            filter_rate = total_filtered / max(total_processed + total_filtered, 1)
            self.registry.set_gauge(
                "ha_ingestor_filter_chain_filter_rate",
                filter_rate
            )
            
        except Exception as e:
            self.logger.error("Failed to record filter chain metrics", error=str(e))
    
    def update_filter_cache_size(self, filter_name: str, filter_type: str, 
                               cache_size: int) -> None:
        """Update filter cache size metrics.
        
        Args:
            filter_name: Name of the filter
            filter_type: Type of the filter
            cache_size: Current cache size
        """
        try:
            self.registry.set_gauge(
                "ha_ingestor_filters_cache_size",
                float(cache_size)
            )
        except Exception as e:
            self.logger.error("Failed to update filter cache size", error=str(e))


def create_metrics_collector() -> MetricsCollector:
    """Create a metrics collector with default configuration.
    
    Returns:
        Configured MetricsCollector instance
    """
    return MetricsCollector()


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance.
    
    Returns:
        Global MetricsCollector instance
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = create_metrics_collector()
    return _global_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """Set the global metrics collector instance.
    
    Args:
        collector: MetricsCollector instance to set as global
    """
    global _global_collector
    _global_collector = collector
