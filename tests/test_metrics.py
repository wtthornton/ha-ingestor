"""Tests for the metrics system."""

import time

import pytest

from ha_ingestor.metrics import (
    MetricsCollector,
    MetricsRegistry,
    create_metrics_collector,
)
from ha_ingestor.metrics.collector import get_metrics_collector, set_metrics_collector


class TestMetricsRegistry:
    """Test MetricsRegistry functionality."""

    def test_register_counter(self):
        """Test counter metric registration."""
        registry = MetricsRegistry()
        registry.register_counter("test_counter", "Test counter metric")

        metric = registry.get_metric("test_counter")
        assert metric is not None
        assert metric.name == "test_counter"
        assert metric.type == "counter"
        assert metric.help_text == "Test counter metric"

    def test_register_gauge(self):
        """Test gauge metric registration."""
        registry = MetricsRegistry()
        registry.register_gauge("test_gauge", "Test gauge metric")

        metric = registry.get_metric("test_gauge")
        assert metric is not None
        assert metric.name == "test_gauge"
        assert metric.type == "gauge"

    def test_register_histogram(self):
        """Test histogram metric registration."""
        registry = MetricsRegistry()
        buckets = [0.1, 0.5, 1.0]
        registry.register_histogram("test_histogram", "Test histogram metric", buckets)

        metric = registry.get_metric("test_histogram")
        assert metric is not None
        assert metric.name == "test_histogram"
        assert metric.type == "histogram"
        assert hasattr(metric, "buckets")

    def test_increment_counter(self):
        """Test counter increment."""
        registry = MetricsRegistry()
        registry.register_counter("test_counter", "Test counter")

        registry.increment_counter("test_counter", value=5.0)
        registry.increment_counter("test_counter", value=3.0)

        metric = registry.get_metric("test_counter")
        assert len(metric.values) == 2
        assert metric.values[0].value == 5.0
        assert metric.values[1].value == 3.0

    def test_set_gauge(self):
        """Test gauge value setting."""
        registry = MetricsRegistry()
        registry.register_gauge("test_gauge", "Test gauge")

        registry.set_gauge("test_gauge", 42.0)
        registry.set_gauge("test_gauge", 100.0)

        metric = registry.get_metric("test_gauge")
        assert len(metric.values) == 2
        assert metric.values[0].value == 42.0
        assert metric.values[1].value == 100.0

    def test_observe_histogram(self):
        """Test histogram observation."""
        registry = MetricsRegistry()
        registry.register_histogram("test_histogram", "Test histogram")

        registry.observe_histogram("test_histogram", 0.5)
        registry.observe_histogram("test_histogram", 1.2)

        metric = registry.get_metric("test_histogram")
        assert len(metric.values) == 2
        assert metric.values[0].value == 0.5
        assert metric.values[1].value == 1.2

    def test_export_prometheus(self):
        """Test Prometheus export format."""
        registry = MetricsRegistry()
        registry.register_counter("test_counter", "Test counter")
        registry.increment_counter("test_counter", value=10.0)

        prometheus_data = registry.export_prometheus()

        assert "ha_ingestor_uptime_seconds" in prometheus_data
        assert "test_counter" in prometheus_data
        assert "# HELP test_counter Test counter" in prometheus_data
        assert "# TYPE test_counter counter" in prometheus_data
        assert "test_counter 10.0" in prometheus_data

    def test_get_metrics_summary(self):
        """Test metrics summary generation."""
        registry = MetricsRegistry()
        registry.register_counter("test_counter", "Test counter")
        registry.increment_counter("test_counter", value=5.0)

        summary = registry.get_metrics_summary()

        assert "uptime_seconds" in summary
        assert "total_metrics" in summary
        assert "metrics" in summary
        assert "test_counter" in summary["metrics"]
        assert summary["metrics"]["test_counter"]["latest_value"] == 5.0


class TestMetricsCollector:
    """Test MetricsCollector functionality."""

    def test_default_metrics_setup(self):
        """Test that default metrics are registered."""
        collector = MetricsCollector()

        # Check that key metrics are registered
        metric_names = collector.registry.get_metric_names()
        assert "ha_ingestor_uptime_seconds" in metric_names
        assert "ha_ingestor_events_processed_total" in metric_names
        assert "ha_ingestor_mqtt_connected" in metric_names
        assert "ha_ingestor_websocket_connected" in metric_names
        assert "ha_ingestor_influxdb_connected" in metric_names

    def test_record_event_processed(self):
        """Test event processing metrics recording."""
        collector = MetricsCollector()

        # Record MQTT event
        collector.record_event_processed("mqtt", success=True)

        # Check counters
        mqtt_metric = collector.registry.get_metric("ha_ingestor_events_mqtt_total")
        assert mqtt_metric.values[-1].value == 1.0

        total_metric = collector.registry.get_metric(
            "ha_ingestor_events_processed_total"
        )
        assert total_metric.values[-1].value == 1.0

        # Record failed event
        collector.record_event_processed("websocket", success=False)

        failed_metric = collector.registry.get_metric("ha_ingestor_events_failed_total")
        assert failed_metric.values[-1].value == 1.0

    def test_record_event_deduplicated(self):
        """Test deduplication metrics recording."""
        collector = MetricsCollector()

        collector.record_event_deduplicated()
        collector.record_event_deduplicated()

        metric = collector.registry.get_metric("ha_ingestor_events_deduplicated_total")
        assert len(metric.values) == 2
        # Check that we have two separate increment records
        assert metric.values[0].value == 1.0
        assert metric.values[1].value == 1.0
        # Total count should be sum of all values
        total_count = sum(val.value for val in metric.values)
        assert total_count == 2.0

    def test_record_pipeline_queue_size(self):
        """Test pipeline queue size metrics recording."""
        collector = MetricsCollector()

        collector.record_pipeline_queue_size(42)
        collector.record_pipeline_queue_size(100)

        metric = collector.registry.get_metric("ha_ingestor_pipeline_queue_size")
        assert len(metric.values) == 2
        assert metric.values[-1].value == 100.0

    def test_record_pipeline_processing_time(self):
        """Test pipeline processing time metrics recording."""
        collector = MetricsCollector()

        collector.record_pipeline_processing_time(0.5)
        collector.record_pipeline_processing_time(1.2)

        metric = collector.registry.get_metric(
            "ha_ingestor_pipeline_processing_duration_seconds"
        )
        assert len(metric.values) == 2
        assert metric.values[-1].value == 1.2

    def test_record_client_connection_status(self):
        """Test client connection status metrics recording."""
        collector = MetricsCollector()

        collector.record_client_connection_status("mqtt", True)
        collector.record_client_connection_status("mqtt", False)

        metric = collector.registry.get_metric("ha_ingestor_mqtt_connected")
        assert len(metric.values) == 2
        assert metric.values[0].value == 1.0  # Connected
        assert metric.values[1].value == 0.0  # Disconnected

    def test_record_influxdb_write(self):
        """Test InfluxDB write metrics recording."""
        collector = MetricsCollector()

        # Record successful write
        collector.record_influxdb_write(10, True, 0.5)

        written_metric = collector.registry.get_metric(
            "ha_ingestor_influxdb_points_written_total"
        )
        assert written_metric.values[-1].value == 10.0

        duration_metric = collector.registry.get_metric(
            "ha_ingestor_influxdb_write_duration_seconds"
        )
        assert duration_metric.values[-1].value == 0.5

        # Record failed write
        collector.record_influxdb_write(5, False, 0.1)

        failed_metric = collector.registry.get_metric(
            "ha_ingestor_influxdb_points_failed_total"
        )
        assert failed_metric.values[-1].value == 5.0

    def test_record_error(self):
        """Test error metrics recording."""
        collector = MetricsCollector()

        collector.record_error("general", "error")
        collector.record_error("connection", "warning")

        general_errors = collector.registry.get_metric("ha_ingestor_errors_total")
        # Check that we have two separate increment records
        assert len(general_errors.values) == 2
        # Total count should be sum of all values
        total_count = sum(val.value for val in general_errors.values)
        assert total_count == 2.0

        # Check category-specific errors
        category_errors = collector.registry.get_metric(
            "ha_ingestor_errors_by_category_total"
        )
        assert len(category_errors.values) == 2
        total_category_count = sum(val.value for val in category_errors.values)
        assert total_category_count == 2.0

        # Check severity-specific errors
        severity_errors = collector.registry.get_metric(
            "ha_ingestor_errors_by_severity_total"
        )
        assert len(severity_errors.values) == 2
        total_severity_count = sum(val.value for val in severity_errors.values)
        assert total_severity_count == 2.0

    def test_update_uptime(self):
        """Test uptime metric update."""
        collector = MetricsCollector()

        # Wait a bit to ensure time difference
        time.sleep(0.1)

        collector.update_uptime()

        uptime_metric = collector.registry.get_metric("ha_ingestor_uptime_seconds")
        assert len(uptime_metric.values) > 0
        assert uptime_metric.values[-1].value > 0.0

    def test_collect_component_metrics(self):
        """Test component metrics collection."""
        collector = MetricsCollector()

        component_metrics = {
            "cpu_usage": 75.5,
            "memory_usage": 1024.0,
            "active_connections": 42,
        }

        collector.collect_component_metrics("test_component", component_metrics)

        # Check that component-specific metrics were created
        cpu_metric = collector.registry.get_metric(
            "ha_ingestor_test_component_cpu_usage"
        )
        assert cpu_metric is not None
        assert cpu_metric.values[-1].value == 75.5

        memory_metric = collector.registry.get_metric(
            "ha_ingestor_test_component_memory_usage"
        )
        assert memory_metric is not None
        assert memory_metric.values[-1].value == 1024.0

    def test_export_prometheus(self):
        """Test Prometheus export with metrics collector."""
        collector = MetricsCollector()

        # Add some test data
        collector.record_event_processed("mqtt", success=True)
        collector.record_pipeline_queue_size(10)

        prometheus_data = collector.export_prometheus()

        assert "ha_ingestor_uptime_seconds" in prometheus_data
        assert "ha_ingestor_events_processed_total" in prometheus_data
        assert "ha_ingestor_pipeline_queue_size" in prometheus_data


class TestMetricsCollectorGlobal:
    """Test global metrics collector functionality."""

    def test_get_metrics_collector(self):
        """Test getting global metrics collector."""
        # Clear any existing global collector
        set_metrics_collector(None)

        collector = get_metrics_collector()
        assert collector is not None
        assert isinstance(collector, MetricsCollector)

    def test_set_metrics_collector(self):
        """Test setting global metrics collector."""
        custom_collector = MetricsCollector()
        set_metrics_collector(custom_collector)

        retrieved_collector = get_metrics_collector()
        assert retrieved_collector is custom_collector

    def test_create_metrics_collector(self):
        """Test metrics collector creation."""
        collector = create_metrics_collector()
        assert isinstance(collector, MetricsCollector)
        assert collector.registry is not None


if __name__ == "__main__":
    pytest.main([__file__])
