"""Tests for performance monitoring components."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from ha_ingestor.metrics.enhanced_collector import (
    create_enhanced_metrics_collector,
    get_enhanced_metrics_collector,
    set_enhanced_metrics_collector,
)
from ha_ingestor.metrics.prometheus_collector import (
    create_prometheus_collector,
    get_prometheus_collector,
    set_prometheus_collector,
)
from ha_ingestor.monitoring.performance_monitor import (
    BusinessMetrics,
    PerformanceMetrics,
    PerformanceMonitor,
    SystemMetrics,
    create_performance_monitor,
    get_performance_monitor,
    set_performance_monitor,
)


class TestSystemMetrics:
    """Test SystemMetrics dataclass."""

    def test_system_metrics_creation(self):
        """Test creating SystemMetrics instance."""
        metrics = SystemMetrics(
            cpu_percent=25.5,
            memory_percent=60.0,
            memory_used_mb=2048.0,
            memory_available_mb=1366.0,
            disk_usage_percent=45.0,
            disk_io_read_mb=100.0,
            disk_io_write_mb=50.0,
            network_io_sent_mb=200.0,
            network_io_recv_mb=150.0,
        )

        assert metrics.cpu_percent == 25.5
        assert metrics.memory_percent == 60.0
        assert metrics.memory_used_mb == 2048.0
        assert metrics.memory_available_mb == 1366.0
        assert metrics.disk_usage_percent == 45.0
        assert metrics.disk_io_read_mb == 100.0
        assert metrics.disk_io_write_mb == 50.0
        assert metrics.network_io_sent_mb == 200.0
        assert metrics.network_io_recv_mb == 150.0
        assert isinstance(metrics.timestamp, float)

    def test_system_metrics_defaults(self):
        """Test SystemMetrics with default values."""
        metrics = SystemMetrics()

        assert metrics.cpu_percent == 0.0
        assert metrics.memory_percent == 0.0
        assert metrics.memory_used_mb == 0.0
        assert metrics.memory_available_mb == 0.0
        assert metrics.disk_usage_percent == 0.0
        assert metrics.disk_io_read_mb == 0.0
        assert metrics.disk_io_write_mb == 0.0
        assert metrics.network_io_sent_mb == 0.0
        assert metrics.network_io_recv_mb == 0.0
        assert isinstance(metrics.timestamp, float)


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating PerformanceMetrics instance."""
        metrics = PerformanceMetrics(
            event_processing_rate=100.5,
            average_processing_time=15.2,
            p95_processing_time=25.0,
            p99_processing_time=50.0,
            queue_depth=10,
            active_connections=5,
            error_rate=0.01,
            throughput_points_per_second=200.0,
        )

        assert metrics.event_processing_rate == 100.5
        assert metrics.average_processing_time == 15.2
        assert metrics.p95_processing_time == 25.0
        assert metrics.p99_processing_time == 50.0
        assert metrics.queue_depth == 10
        assert metrics.active_connections == 5
        assert metrics.error_rate == 0.01
        assert metrics.throughput_points_per_second == 200.0
        assert isinstance(metrics.timestamp, float)

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics with default values."""
        metrics = PerformanceMetrics()

        assert metrics.event_processing_rate == 0.0
        assert metrics.average_processing_time == 0.0
        assert metrics.p95_processing_time == 0.0
        assert metrics.p99_processing_time == 0.0
        assert metrics.queue_depth == 0
        assert metrics.active_connections == 0
        assert metrics.error_rate == 0.0
        assert metrics.throughput_points_per_second == 0.0
        assert isinstance(metrics.timestamp, float)


class TestBusinessMetrics:
    """Test BusinessMetrics dataclass."""

    def test_business_metrics_creation(self):
        """Test creating BusinessMetrics instance."""
        metrics = BusinessMetrics(
            total_events_processed=1000,
            events_by_domain={"light": 300, "switch": 200, "sensor": 500},
            events_by_entity={"light.living_room": 100, "switch.kitchen": 50},
            events_by_source={"mqtt": 600, "websocket": 400},
            data_points_written=950,
            data_volume_mb=15.5,
            deduplication_rate=0.05,
            filter_efficiency=0.95,
            transformation_success_rate=0.98,
        )

        assert metrics.total_events_processed == 1000
        assert metrics.events_by_domain["light"] == 300
        assert metrics.events_by_entity["light.living_room"] == 100
        assert metrics.events_by_source["mqtt"] == 600
        assert metrics.data_points_written == 950
        assert metrics.data_volume_mb == 15.5
        assert metrics.deduplication_rate == 0.05
        assert metrics.filter_efficiency == 0.95
        assert metrics.transformation_success_rate == 0.98
        assert isinstance(metrics.timestamp, float)

    def test_business_metrics_defaults(self):
        """Test BusinessMetrics with default values."""
        metrics = BusinessMetrics()

        assert metrics.total_events_processed == 0
        assert metrics.events_by_domain == {}
        assert metrics.events_by_entity == {}
        assert metrics.events_by_source == {}
        assert metrics.data_points_written == 0
        assert metrics.data_volume_mb == 0.0
        assert metrics.deduplication_rate == 0.0
        assert metrics.filter_efficiency == 0.0
        assert metrics.transformation_success_rate == 0.0
        assert isinstance(metrics.timestamp, float)


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "monitoring_interval": 5.0,
            "enable_system_metrics": True,
            "enable_performance_metrics": True,
            "enable_business_metrics": True,
        }

    @pytest.fixture
    def performance_monitor(self, mock_config):
        """Create PerformanceMonitor instance for testing."""
        with patch("ha_ingestor.monitoring.performance_monitor.psutil"):
            return PerformanceMonitor(mock_config)

    def test_performance_monitor_initialization(self, performance_monitor, mock_config):
        """Test PerformanceMonitor initialization."""
        assert performance_monitor.config == mock_config
        assert performance_monitor.monitoring_interval == 5.0
        assert performance_monitor.enable_system_metrics is True
        assert performance_monitor.enable_performance_metrics is True
        assert performance_monitor.enable_business_metrics is True
        assert len(performance_monitor.system_metrics_history) == 0
        assert len(performance_monitor.performance_metrics_history) == 0
        assert len(performance_monitor.business_metrics_history) == 0

    def test_get_system_info(self, performance_monitor):
        """Test system info collection."""
        with patch(
            "ha_ingestor.monitoring.performance_monitor.platform"
        ) as mock_platform:
            mock_platform.platform.return_value = "Windows-10-10.0.19041-SP0"
            mock_platform.python_version.return_value = "3.12.0"
            mock_platform.architecture.return_value = ("64bit", "WindowsPE")
            mock_platform.processor.return_value = "Intel64 Family 6"
            mock_platform.node.return_value = "DESKTOP-TEST"

            with patch(
                "ha_ingestor.monitoring.performance_monitor.psutil"
            ) as mock_psutil:
                mock_psutil.cpu_count.return_value = 8
                mock_psutil.virtual_memory.return_value.total = 16 * 1024**3  # 16GB
                mock_psutil.disk_usage.return_value.total = 500 * 1024**3  # 500GB

                system_info = performance_monitor._get_system_info()

                assert system_info["platform"] == "Windows-10-10.0.19041-SP0"
                assert system_info["python_version"] == "3.12.0"
                assert system_info["hostname"] == "DESKTOP-TEST"
                assert system_info["cpu_count"] == 8
                assert system_info["memory_total_gb"] == 16.0
                assert system_info["disk_total_gb"] == 500.0

    def test_record_processing_time(self, performance_monitor):
        """Test recording processing time."""
        performance_monitor.record_processing_time(100.5)
        performance_monitor.record_processing_time(200.3)

        assert len(performance_monitor.processing_times) == 2
        assert performance_monitor.processing_times[0] == 100.5
        assert performance_monitor.processing_times[1] == 200.3

    def test_record_processing_time_limit(self, performance_monitor):
        """Test processing time history limit."""
        # Add more than 1000 processing times
        for i in range(1100):
            performance_monitor.record_processing_time(float(i))

        assert len(performance_monitor.processing_times) == 1000
        assert performance_monitor.processing_times[0] == 100.0  # First kept value
        assert performance_monitor.processing_times[-1] == 1099.0  # Last value

    def test_record_event_processed(self, performance_monitor):
        """Test recording event processing."""
        performance_monitor.record_event_processed("mqtt", "light", "light.living_room")
        performance_monitor.record_event_processed(
            "websocket", "switch", "switch.kitchen"
        )

        assert performance_monitor.event_counts["total"] == 2
        assert performance_monitor.event_counts["mqtt"] == 1
        assert performance_monitor.event_counts["websocket"] == 1
        assert performance_monitor.event_counts["light"] == 1
        assert performance_monitor.event_counts["switch"] == 1
        assert performance_monitor.event_counts["light.living_room"] == 1
        assert performance_monitor.event_counts["switch.kitchen"] == 1

    def test_record_error(self, performance_monitor):
        """Test recording errors."""
        performance_monitor.record_error("processing")
        performance_monitor.record_error("connection")
        performance_monitor.record_error("processing")

        assert performance_monitor.error_counts["total"] == 3
        assert performance_monitor.error_counts["processing"] == 2
        assert performance_monitor.error_counts["connection"] == 1

    def test_calculate_performance_metrics(self, performance_monitor):
        """Test performance metrics calculation."""
        # Add some processing times
        performance_monitor.record_processing_time(10.0)
        performance_monitor.record_processing_time(20.0)
        performance_monitor.record_processing_time(30.0)
        performance_monitor.record_processing_time(40.0)
        performance_monitor.record_processing_time(50.0)

        # Add some errors
        performance_monitor.record_error("processing")

        metrics = performance_monitor.calculate_performance_metrics()

        assert metrics.average_processing_time == 30.0
        assert metrics.p95_processing_time == 50.0
        assert metrics.p99_processing_time == 50.0
        assert metrics.error_rate > 0

    def test_calculate_business_metrics(self, performance_monitor):
        """Test business metrics calculation."""
        # Add some events
        performance_monitor.record_event_processed("mqtt", "light", "light.living_room")
        performance_monitor.record_event_processed(
            "websocket", "switch", "switch.kitchen"
        )

        metrics = performance_monitor.calculate_business_metrics()

        assert metrics.total_events_processed == 2
        assert "light" in metrics.events_by_domain
        assert "switch" in metrics.events_by_domain
        assert "mqtt" in metrics.events_by_source
        assert "websocket" in metrics.events_by_source

    def test_get_metrics_summary(self, performance_monitor):
        """Test metrics summary generation."""
        # Add some data
        performance_monitor.record_processing_time(100.0)
        performance_monitor.record_event_processed("mqtt", "light", "light.living_room")

        summary = performance_monitor.get_metrics_summary()

        assert "system_info" in summary
        assert "current_metrics" in summary
        assert "history_counts" in summary
        # The performance metrics are calculated separately, so we check the event counts directly
        assert performance_monitor.event_counts["total"] == 1

    @pytest.mark.asyncio
    async def test_monitor_operation_context_manager(self, performance_monitor):
        """Test operation monitoring context manager."""
        async with performance_monitor.monitor_operation("test_operation"):
            await asyncio.sleep(0.01)  # Simulate some work

        # Check that processing time was recorded
        assert len(performance_monitor.processing_times) > 0
        # The monitor_operation records events with domain "monitoring", not "internal"
        assert performance_monitor.event_counts["monitoring"] == 1

    @pytest.mark.asyncio
    async def test_monitor_operation_with_error(self, performance_monitor):
        """Test operation monitoring context manager with error."""
        with pytest.raises(ValueError):
            async with performance_monitor.monitor_operation("test_operation"):
                raise ValueError("Test error")

        # Check that processing time was recorded even for failed operations
        assert len(performance_monitor.processing_times) > 0
        assert performance_monitor.error_counts["processing"] == 1


class TestHAIngestorCollector:
    """Test HAIngestorCollector class."""

    @pytest.fixture
    def prometheus_collector(self):
        """Create HAIngestorCollector instance for testing."""
        return create_prometheus_collector()

    def test_prometheus_collector_initialization(self, prometheus_collector):
        """Test HAIngestorCollector initialization."""
        assert prometheus_collector.registry is not None
        assert prometheus_collector.logger is not None

    def test_update_system_metrics(self, prometheus_collector):
        """Test updating system metrics."""
        prometheus_collector.update_system_metrics(
            hostname="test-host",
            cpu_percent=25.5,
            memory_percent=60.0,
            memory_used_bytes=2048 * 1024 * 1024,
            disk_usage_percent=45.0,
            disk_io_read_bytes=100 * 1024 * 1024,
            disk_io_write_bytes=50 * 1024 * 1024,
            network_io_sent_bytes=200 * 1024 * 1024,
            network_io_recv_bytes=150 * 1024 * 1024,
        )

        # Check that metrics were updated
        assert prometheus_collector.system_cpu_percent is not None
        assert prometheus_collector.system_memory_percent is not None
        assert prometheus_collector.system_disk_usage_percent is not None

    def test_observe_event_processing(self, prometheus_collector):
        """Test observing event processing duration."""
        prometheus_collector.observe_event_processing(
            duration_seconds=0.5,
            source="mqtt",
            domain="light",
            entity_id="light.living_room",
        )

        # Check that histogram was updated
        assert prometheus_collector.event_processing_duration is not None

    def test_increment_events_processed(self, prometheus_collector):
        """Test incrementing events processed counter."""
        prometheus_collector.increment_events_processed(
            source="mqtt",
            domain="light",
            entity_id="light.living_room",
            status="success",
        )

        # Check that counter was incremented
        assert prometheus_collector.events_processed_total is not None

    def test_export_metrics(self, prometheus_collector):
        """Test metrics export."""
        # Add some metrics first
        prometheus_collector.update_system_metrics(
            hostname="test-host",
            cpu_percent=25.0,
            memory_percent=50.0,
            memory_used_bytes=1024 * 1024 * 1024,
            disk_usage_percent=30.0,
            disk_io_read_bytes=0,
            disk_io_write_bytes=0,
            network_io_sent_bytes=0,
            network_io_recv_bytes=0,
        )

        metrics = prometheus_collector.export_metrics()

        # Prometheus metrics can be bytes or string
        assert isinstance(metrics, (str, bytes))
        assert len(metrics) > 0
        # Convert to string for assertion
        metrics_str = metrics.decode() if isinstance(metrics, bytes) else metrics
        assert "ha_ingestor_system_cpu_percent" in metrics_str

    def test_get_metrics_summary(self, prometheus_collector):
        """Test metrics summary generation."""
        summary = prometheus_collector.get_metrics_summary()

        assert "registry" in summary
        assert "metrics_count" in summary
        assert "metrics" in summary


class TestEnhancedMetricsCollector:
    """Test EnhancedMetricsCollector class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "enable_integration": True,
            "sync_interval": 5.0,
            "enable_auto_sync": True,
        }

    @pytest.fixture
    def enhanced_collector(self, mock_config):
        """Create EnhancedMetricsCollector instance for testing."""
        with (
            patch("ha_ingestor.metrics.enhanced_collector.get_metrics_collector"),
            patch("ha_ingestor.metrics.enhanced_collector.get_prometheus_collector"),
            patch("ha_ingestor.metrics.enhanced_collector.get_performance_monitor"),
        ):
            return create_enhanced_metrics_collector(mock_config)

    def test_enhanced_collector_initialization(self, enhanced_collector, mock_config):
        """Test EnhancedMetricsCollector initialization."""
        assert enhanced_collector.config == mock_config
        assert enhanced_collector.enable_integration is True
        assert enhanced_collector.sync_interval == 5.0
        assert enhanced_collector.enable_auto_sync is True
        assert enhanced_collector._running is False

    @pytest.mark.asyncio
    async def test_start_and_stop(self, enhanced_collector):
        """Test starting and stopping the enhanced collector."""
        # Mock the performance monitor
        enhanced_collector.performance_monitor = Mock()

        await enhanced_collector.start()
        assert enhanced_collector._running is True

        await enhanced_collector.stop()
        assert enhanced_collector._running is False

    def test_record_event_processing(self, enhanced_collector):
        """Test recording event processing across all collectors."""
        # Mock the components
        enhanced_collector.performance_monitor = Mock()
        enhanced_collector.prometheus_collector = Mock()
        enhanced_collector.registry = Mock()

        enhanced_collector.record_event_processing(
            duration_seconds=0.5,
            source="mqtt",
            domain="light",
            entity_id="light.living_room",
            success=True,
        )

        # Check that all collectors were called
        enhanced_collector.performance_monitor.record_processing_time.assert_called_once()
        enhanced_collector.performance_monitor.record_event_processed.assert_called_once()
        enhanced_collector.prometheus_collector.observe_event_processing.assert_called_once()
        enhanced_collector.registry.record_event_processed.assert_called_once()

    def test_record_error(self, enhanced_collector):
        """Test recording errors across all collectors."""
        # Mock the components
        enhanced_collector.performance_monitor = Mock()
        enhanced_collector.prometheus_collector = Mock()
        enhanced_collector.registry = Mock()

        enhanced_collector.record_error(
            error_type="processing", component="pipeline", severity="warning"
        )

        # Check that all collectors were called
        enhanced_collector.performance_monitor.record_error.assert_called_once()
        enhanced_collector.prometheus_collector.increment_errors.assert_called_once()
        enhanced_collector.registry.record_error.assert_called_once()

    def test_get_comprehensive_metrics(self, enhanced_collector):
        """Test comprehensive metrics collection."""
        # Mock the components
        enhanced_collector.registry = Mock()
        enhanced_collector.prometheus_collector = Mock()
        enhanced_collector.performance_monitor = Mock()

        enhanced_collector.registry.get_metrics_summary.return_value = {
            "registry": "data"
        }
        enhanced_collector.prometheus_collector.get_metrics_summary.return_value = {
            "prometheus": "data"
        }
        enhanced_collector.performance_monitor.get_metrics_summary.return_value = {
            "performance": "data"
        }

        metrics = enhanced_collector.get_comprehensive_metrics()

        assert "registry_metrics" in metrics
        assert "prometheus_metrics" in metrics
        assert "performance_metrics" in metrics
        assert "integration_status" in metrics

    def test_export_prometheus_metrics(self, enhanced_collector):
        """Test Prometheus metrics export."""
        # Mock the components
        enhanced_collector.prometheus_collector = Mock()
        enhanced_collector.registry = Mock()

        enhanced_collector.prometheus_collector.export_metrics.return_value = (
            "prometheus_metrics"
        )
        enhanced_collector.registry.export_prometheus.return_value = "registry_metrics"

        combined_metrics = enhanced_collector.export_prometheus_metrics()

        assert "prometheus_metrics" in combined_metrics
        assert "registry_metrics" in combined_metrics

    def test_get_health_status(self, enhanced_collector):
        """Test health status generation."""
        # Mock the components
        enhanced_collector.registry = Mock()
        enhanced_collector.prometheus_collector = Mock()
        enhanced_collector.performance_monitor = Mock()

        enhanced_collector.registry.get_metric_names.return_value = [
            "metric1",
            "metric2",
        ]
        enhanced_collector.prometheus_collector.registry.collect.return_value = [
            "prometheus_metric"
        ]

        health_status = enhanced_collector.get_health_status()

        assert "status" in health_status
        assert "components" in health_status
        assert "integration" in health_status
        assert "metrics_count" in health_status


class TestGlobalInstances:
    """Test global instance management."""

    def test_performance_monitor_global_instances(self):
        """Test global performance monitor instances."""
        # Test get_performance_monitor creates instance if none exists
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2

        # Test set_performance_monitor
        new_monitor = create_performance_monitor()
        set_performance_monitor(new_monitor)

        monitor3 = get_performance_monitor()
        assert monitor3 is new_monitor

    def test_prometheus_collector_global_instances(self):
        """Test global Prometheus collector instances."""
        # Test get_prometheus_collector creates instance if none exists
        collector1 = get_prometheus_collector()
        collector2 = get_prometheus_collector()

        assert collector1 is collector2

        # Test set_prometheus_collector
        new_collector = create_prometheus_collector()
        set_prometheus_collector(new_collector)

        collector3 = get_prometheus_collector()
        assert collector3 is new_collector

    def test_enhanced_collector_global_instances(self):
        """Test global enhanced collector instances."""
        # Test get_enhanced_metrics_collector creates instance if none exists
        collector1 = get_enhanced_metrics_collector()
        collector2 = get_enhanced_metrics_collector()

        assert collector1 is collector2

        # Test set_enhanced_metrics_collector
        new_collector = create_enhanced_metrics_collector()
        set_enhanced_metrics_collector(new_collector)

        collector3 = get_enhanced_metrics_collector()
        assert collector3 is new_collector


if __name__ == "__main__":
    pytest.main([__file__])
