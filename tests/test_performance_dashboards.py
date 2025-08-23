"""Tests for the performance dashboard system."""

import asyncio
from datetime import datetime, timedelta

import pytest

from ha_ingestor.dashboards.anomaly_detector import (
    AnomalyDetector,
    AnomalyPoint,
    AnomalySeverity,
    AnomalyType,
)
from ha_ingestor.dashboards.dashboard_manager import (
    DashboardConfig as ManagerConfig,
)
from ha_ingestor.dashboards.dashboard_manager import (
    DashboardManager,
)
from ha_ingestor.dashboards.operational_dashboard import (
    ConnectionStatus,
    OperationalDashboard,
    ServiceStatus,
)
from ha_ingestor.dashboards.performance_dashboard import (
    DashboardConfig,
    DashboardMetric,
    DashboardPanel,
    PerformanceDashboard,
)
from ha_ingestor.dashboards.trend_analyzer import TrendAnalyzer


class TestDashboardMetric:
    """Test DashboardMetric dataclass."""

    def test_dashboard_metric_creation(self):
        """Test creating a DashboardMetric instance."""
        timestamp = datetime.utcnow()
        metric = DashboardMetric(
            name="CPU Usage",
            value=75.5,
            unit="%",
            timestamp=timestamp,
            trend="up",
            trend_value=2.5,
            status="warning",
            metadata={"source": "system"},
        )

        assert metric.name == "CPU Usage"
        assert metric.value == 75.5
        assert metric.unit == "%"
        assert metric.timestamp == timestamp
        assert metric.trend == "up"
        assert metric.trend_value == 2.5
        assert metric.status == "warning"
        assert metric.metadata == {"source": "system"}

    def test_dashboard_metric_defaults(self):
        """Test DashboardMetric with default values."""
        timestamp = datetime.utcnow()
        metric = DashboardMetric(
            name="Test Metric", value=100.0, unit="count", timestamp=timestamp
        )

        assert metric.trend == "stable"
        assert metric.trend_value == 0.0
        assert metric.status == "normal"
        assert metric.metadata == {}


class TestDashboardPanel:
    """Test DashboardPanel dataclass."""

    def test_dashboard_panel_creation(self):
        """Test creating a DashboardPanel instance."""
        panel = DashboardPanel(
            id="test_panel",
            title="Test Panel",
            type="graph",
            metrics=["metric1", "metric2"],
            position={"x": 0, "y": 0, "width": 6, "height": 4},
            options={"color": "blue"},
        )

        assert panel.id == "test_panel"
        assert panel.title == "Test Panel"
        assert panel.type == "graph"
        assert panel.metrics == ["metric1", "metric2"]
        assert panel.position == {"x": 0, "y": 0, "width": 6, "height": 4}
        assert panel.options == {"color": "blue"}

    def test_dashboard_panel_defaults(self):
        """Test DashboardPanel with default values."""
        panel = DashboardPanel(
            id="test_panel",
            title="Test Panel",
            type="stat",
            metrics=["metric1"],
            position={"x": 0, "y": 0, "width": 4, "height": 2},
        )

        assert panel.options == {}


class TestDashboardConfig:
    """Test DashboardConfig dataclass."""

    def test_dashboard_config_creation(self):
        """Test creating a DashboardConfig instance."""
        panels = [
            DashboardPanel(
                id="panel1",
                title="Panel 1",
                type="graph",
                metrics=["metric1"],
                position={"x": 0, "y": 0, "width": 6, "height": 4},
            )
        ]

        config = DashboardConfig(
            name="Test Dashboard",
            description="Test Description",
            panels=panels,
            refresh_interval=60,
            time_range="6h",
            auto_refresh=False,
        )

        assert config.name == "Test Dashboard"
        assert config.description == "Test Description"
        assert config.panels == panels
        assert config.refresh_interval == 60
        assert config.time_range == "6h"
        assert config.auto_refresh is False

    def test_dashboard_config_defaults(self):
        """Test DashboardConfig with default values."""
        panels = [
            DashboardPanel(
                id="panel1",
                title="Panel 1",
                type="graph",
                metrics=["metric1"],
                position={"x": 0, "y": 0, "width": 6, "height": 4},
            )
        ]

        config = DashboardConfig(
            name="Test Dashboard", description="Test Description", panels=panels
        )

        assert config.refresh_interval == 30
        assert config.time_range == "1h"
        assert config.auto_refresh is True


class TestPerformanceDashboard:
    """Test PerformanceDashboard class."""

    @pytest.fixture
    def dashboard(self):
        """Create a PerformanceDashboard instance for testing."""
        return PerformanceDashboard()

    def test_initialization(self, dashboard):
        """Test dashboard initialization."""
        assert dashboard.dashboards is not None
        assert len(dashboard.dashboards) > 0
        assert "system_performance" in dashboard.dashboards
        assert "application_performance" in dashboard.dashboards
        assert "operational" in dashboard.dashboards

    def test_list_dashboards(self, dashboard):
        """Test listing available dashboards."""
        dashboards = dashboard.list_dashboards()
        assert "system_performance" in dashboards
        assert "application_performance" in dashboards
        assert "operational" in dashboards

    def test_get_dashboard_config(self, dashboard):
        """Test getting dashboard configuration."""
        config = dashboard.get_dashboard_config("system_performance")
        assert config is not None
        assert config.name == "System Performance"
        assert len(config.panels) > 0

    def test_get_dashboard_config_nonexistent(self, dashboard):
        """Test getting non-existent dashboard configuration."""
        config = dashboard.get_dashboard_config("nonexistent")
        assert config is None

    def test_get_status_for_value(self, dashboard):
        """Test status determination for different values."""
        # Test normal case
        status = dashboard._get_status_for_value(50, 80, 95)
        assert status == "normal"

        # Test warning case
        status = dashboard._get_status_for_value(85, 80, 95)
        assert status == "warning"

        # Test critical case
        status = dashboard._get_status_for_value(100, 80, 95)
        assert status == "critical"

        # Test reverse case (lower is worse)
        # In reverse mode, thresholds represent minimum acceptable values
        # Value 50: 50 < 100 (warning threshold) → critical
        # Value 75: 75 < 100 (warning threshold) → critical
        # Value 25: 25 < 100 (warning threshold) → critical
        status = dashboard._get_status_for_value(50, 100, 500, reverse=True)
        assert status == "critical"

        status = dashboard._get_status_for_value(75, 100, 500, reverse=True)
        assert status == "critical"

        status = dashboard._get_status_for_value(25, 100, 500, reverse=True)
        assert status == "critical"

    def test_export_grafana_dashboard(self, dashboard):
        """Test Grafana dashboard export."""
        export = dashboard.export_grafana_dashboard("system_performance")
        assert export is not None
        assert "dashboard" in export
        assert export["dashboard"]["title"] == "System Performance"
        assert "panels" in export["dashboard"]

    def test_get_dashboard_summary(self, dashboard):
        """Test getting dashboard summary."""
        summary = dashboard.get_dashboard_summary()
        assert summary["total_dashboards"] > 0
        assert "dashboards" in summary
        assert "total_metrics" in summary
        assert "last_updated" in summary


class TestTrendAnalyzer:
    """Test TrendAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a TrendAnalyzer instance for testing."""
        return TrendAnalyzer()

    @pytest.fixture
    def sample_data(self):
        """Create sample data for trend analysis."""
        base_time = datetime.utcnow()
        timestamps = [base_time + timedelta(minutes=i) for i in range(20)]
        values = [10 + i * 0.5 for i in range(20)]  # Upward trend
        return list(zip(timestamps, values, strict=False))

    def test_initialization(self, analyzer):
        """Test analyzer initialization."""
        assert analyzer.min_data_points == 10
        assert analyzer.trend_threshold == 0.1
        assert analyzer.confidence_threshold == 0.7
        assert analyzer.prediction_horizon == 3600

    def test_analyze_trend_insufficient_data(self, analyzer):
        """Test trend analysis with insufficient data."""
        data = [(datetime.utcnow(), i) for i in range(5)]  # Less than min_data_points
        result = analyzer.analyze_trend("test_metric", data)
        assert result is None

    def test_analyze_trend_sufficient_data(self, analyzer, sample_data):
        """Test trend analysis with sufficient data."""
        result = analyzer.analyze_trend("test_metric", sample_data)
        assert result is not None
        assert result.metric_name == "test_metric"
        assert result.trend_direction in ["up", "down", "stable"]
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0
        assert result.data_points == 20

    def test_analyze_trend_with_time_range(self, analyzer, sample_data):
        """Test trend analysis with time range filter."""
        time_range = timedelta(minutes=10)
        result = analyzer.analyze_trend("test_metric", sample_data, time_range)
        assert result is not None

    def test_linear_regression(self, analyzer):
        """Test linear regression calculation."""
        x_values = [0, 1, 2, 3, 4]
        y_values = [0, 2, 4, 6, 8]  # Perfect linear relationship

        slope, intercept, r_squared = analyzer._linear_regression(x_values, y_values)
        assert abs(slope - 2.0) < 0.001  # Should be exactly 2
        assert abs(intercept - 0.0) < 0.001  # Should be exactly 0
        assert abs(r_squared - 1.0) < 0.001  # Should be exactly 1

    def test_determine_trend_direction(self, analyzer):
        """Test trend direction determination."""
        stats = {
            "slope": 0.5,
            "r_squared": 0.8,
            "volatility": 0.3,
            "max_value": 100,
            "min_value": 0,
        }

        direction, strength = analyzer._determine_trend_direction(stats)
        assert direction == "up"
        assert strength > 0.0

    def test_calculate_confidence(self, analyzer):
        """Test confidence calculation."""
        stats = {"r_squared": 0.8, "volatility": 0.3}

        confidence = analyzer._calculate_confidence(stats, 20)
        assert confidence > 0.0
        assert confidence <= 1.0

    def test_generate_predictions(self, analyzer):
        """Test prediction generation."""
        stats = {"slope": 0.5, "min_value": 50.0, "max_value": 150.0}
        last_timestamp = datetime.utcnow()
        last_value = 100.0

        predictions = analyzer._generate_predictions(stats, last_timestamp, last_value)
        assert len(predictions) > 0
        assert all(isinstance(p, tuple) for p in predictions)
        assert all(len(p) == 2 for p in predictions)

    def test_analyze_multiple_metrics(self, analyzer, sample_data):
        """Test analyzing multiple metrics."""
        metrics_data = {"metric1": sample_data, "metric2": sample_data}

        results = analyzer.analyze_multiple_metrics(metrics_data)
        assert len(results) == 2
        assert "metric1" in results
        assert "metric2" in results

    def test_get_trend_summary(self, analyzer, sample_data):
        """Test getting trend summary."""
        # Create multiple analyses
        analysis1 = analyzer.analyze_trend("metric1", sample_data)
        analysis2 = analyzer.analyze_trend("metric2", sample_data)

        summary = analyzer.get_trend_summary([analysis1, analysis2])
        assert summary["total_metrics"] == 2
        assert "trends" in summary
        assert "average_confidence" in summary
        assert "average_strength" in summary

    def test_detect_anomalies(self, analyzer, sample_data):
        """Test anomaly detection."""
        current_value = 25.0  # Higher than expected

        result = analyzer.detect_anomalies("test_metric", current_value, sample_data)
        assert "anomaly_detected" in result
        assert "confidence" in result
        assert "z_score" in result

    def test_get_cached_analysis(self, analyzer, sample_data):
        """Test cached analysis retrieval."""
        # First analysis
        result1 = analyzer.analyze_trend("test_metric", sample_data)
        assert result1 is not None

        # Get from cache
        cached = analyzer.get_cached_analysis("test_metric")
        assert cached is not None
        assert cached.metric_name == "test_metric"

    def test_clear_cache(self, analyzer, sample_data):
        """Test cache clearing."""
        # Add some analysis to cache
        analyzer.analyze_trend("test_metric", sample_data)
        assert len(analyzer.analysis_cache) > 0

        # Clear cache
        analyzer.clear_cache()
        assert len(analyzer.analysis_cache) == 0

    def test_get_analysis_statistics(self, analyzer):
        """Test getting analysis statistics."""
        stats = analyzer.get_analysis_statistics()
        assert "cache_size" in stats
        assert "min_data_points" in stats
        assert "trend_threshold" in stats
        assert "confidence_threshold" in stats


class TestAnomalyDetector:
    """Test AnomalyDetector class."""

    @pytest.fixture
    def detector(self):
        """Create an AnomalyDetector instance for testing."""
        return AnomalyDetector()

    @pytest.fixture
    def sample_data(self):
        """Create sample data for anomaly detection."""
        base_time = datetime.utcnow()
        timestamps = [base_time + timedelta(minutes=i) for i in range(25)]
        values = [10.0 + (i % 5) for i in range(25)]  # Some variation
        return list(zip(timestamps, values, strict=False))

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert detector.z_score_threshold == 3.0
        assert detector.iqr_multiplier == 1.5
        assert detector.min_data_points == 20
        assert detector.sensitivity == "medium"

    def test_adjust_thresholds_for_sensitivity(self, detector):
        """Test threshold adjustment for different sensitivity levels."""
        # Test low sensitivity
        detector.sensitivity = "low"
        detector._adjust_thresholds_for_sensitivity()
        assert detector.z_score_threshold == 4.0
        assert detector.iqr_multiplier == 2.0

        # Test high sensitivity
        detector.sensitivity = "high"
        detector._adjust_thresholds_for_sensitivity()
        assert detector.z_score_threshold == 2.5
        assert detector.iqr_multiplier == 1.2

    def test_detect_anomalies_insufficient_data(self, detector):
        """Test anomaly detection with insufficient data."""
        data = [(datetime.utcnow(), i) for i in range(10)]  # Less than min_data_points
        result = detector.detect_anomalies("test_metric", data)
        assert result is None

    def test_detect_anomalies_sufficient_data(self, detector, sample_data):
        """Test anomaly detection with sufficient data."""
        result = detector.detect_anomalies("test_metric", sample_data)
        assert result is not None
        assert result.metric_name == "test_metric"
        assert result.total_data_points == 25
        assert "anomalies_detected" in result.__dict__
        assert "baseline_stats" in result.__dict__
        assert "detection_config" in result.__dict__

    def test_calculate_baseline_statistics(self, detector):
        """Test baseline statistics calculation."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stats = detector._calculate_baseline_statistics(values)

        assert "mean" in stats
        assert "std_dev" in stats
        assert "median" in stats
        assert "q1" in stats
        assert "q3" in stats
        assert "iqr" in stats
        assert stats["mean"] == 5.5
        assert stats["min"] == 1
        assert stats["max"] == 10

    def test_detect_z_score_anomalies(self, detector, sample_data):
        """Test Z-score anomaly detection."""
        timestamps, values = zip(*sample_data, strict=False)
        baseline_stats = detector._calculate_baseline_statistics(values)

        anomalies = detector._detect_z_score_anomalies(
            "test_metric", timestamps, values, baseline_stats
        )

        # Should detect some anomalies if data has variation
        assert isinstance(anomalies, list)

    def test_detect_iqr_anomalies(self, detector, sample_data):
        """Test IQR anomaly detection."""
        timestamps, values = zip(*sample_data, strict=False)
        baseline_stats = detector._calculate_baseline_statistics(values)

        anomalies = detector._detect_iqr_anomalies(
            "test_metric", timestamps, values, baseline_stats
        )

        assert isinstance(anomalies, list)

    def test_detect_trend_changes(self, detector, sample_data):
        """Test trend change detection."""
        timestamps, values = zip(*sample_data, strict=False)
        baseline_stats = detector._calculate_baseline_statistics(values)

        anomalies = detector._detect_trend_changes(
            "test_metric", timestamps, values, baseline_stats
        )

        assert isinstance(anomalies, list)

    def test_detect_level_shifts(self, detector, sample_data):
        """Test level shift detection."""
        timestamps, values = zip(*sample_data, strict=False)
        baseline_stats = detector._calculate_baseline_statistics(values)

        anomalies = detector._detect_level_shifts(
            "test_metric", timestamps, values, baseline_stats
        )

        assert isinstance(anomalies, list)

    def test_calculate_simple_trend(self, detector):
        """Test simple trend calculation."""
        values = [1, 2, 3, 4, 5]
        trend = detector._calculate_simple_trend(values)
        assert trend > 0  # Should be positive for increasing values

        values = [5, 4, 3, 2, 1]
        trend = detector._calculate_simple_trend(values)
        assert trend < 0  # Should be negative for decreasing values

    def test_determine_severity(self, detector):
        """Test severity determination."""
        severity = detector._determine_severity(2.0)
        assert severity == AnomalySeverity.LOW

        severity = detector._determine_severity(4.5)
        assert severity == AnomalySeverity.HIGH

        severity = detector._determine_severity(6.0)
        assert severity == AnomalySeverity.CRITICAL

    def test_deduplicate_anomalies(self, detector):
        """Test anomaly deduplication."""
        # Create some duplicate anomalies
        base_time = datetime.utcnow()
        anomaly1 = AnomalyPoint(
            timestamp=base_time,
            value=100.0,
            expected_value=50.0,
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.HIGH,
            confidence=0.8,
            description="Test anomaly 1",
        )

        anomaly2 = AnomalyPoint(
            timestamp=base_time + timedelta(seconds=30),  # Within 1 minute
            value=110.0,
            expected_value=50.0,
            anomaly_type=AnomalyType.SPIKE,
            severity=AnomalySeverity.HIGH,
            confidence=0.9,
            description="Test anomaly 2",
        )

        anomalies = [anomaly1, anomaly2]
        unique = detector._deduplicate_anomalies(anomalies)

        # Should keep the one with higher confidence
        assert len(unique) == 1
        assert unique[0].confidence == 0.9

    def test_get_anomaly_summary(self, detector, sample_data):
        """Test getting anomaly summary."""
        # First detect some anomalies
        result = detector.detect_anomalies("test_metric", sample_data)
        if result and result.anomalies_detected:
            summary = detector.get_anomaly_summary("test_metric")
            assert "anomalies" in summary
            assert "total_count" in summary
            assert "type_distribution" in summary
            assert "severity_distribution" in summary

    def test_get_detection_statistics(self, detector):
        """Test getting detection statistics."""
        stats = detector.get_detection_statistics()
        assert "total_metrics_monitored" in stats
        assert "total_anomalies_detected" in stats
        assert "z_score_threshold" in stats
        assert "iqr_multiplier" in stats
        assert "sensitivity" in stats

    def test_clear_cache(self, detector):
        """Test cache clearing."""
        detector.baseline_cache["test"] = {"mean": 10.0}
        assert len(detector.baseline_cache) > 0

        detector.clear_cache()
        assert len(detector.baseline_cache) == 0

    def test_update_config(self, detector):
        """Test configuration update."""
        new_config = {
            "z_score_threshold": 4.0,
            "iqr_multiplier": 2.0,
            "sensitivity": "low",
        }

        detector.update_config(new_config)
        assert detector.z_score_threshold == 4.0
        assert detector.iqr_multiplier == 2.0
        assert detector.sensitivity == "low"


class TestOperationalDashboard:
    """Test OperationalDashboard class."""

    @pytest.fixture
    def dashboard(self):
        """Create an OperationalDashboard instance for testing."""
        return OperationalDashboard()

    def test_initialization(self, dashboard):
        """Test dashboard initialization."""
        assert dashboard.health_check_interval == 30
        assert dashboard.connection_check_interval == 15
        assert dashboard.overview_update_interval == 60
        assert dashboard.service_health == {}
        assert dashboard.connection_health == {}
        assert dashboard.system_overview is None

    def test_map_health_status(self, dashboard):
        """Test health status mapping."""
        status = dashboard._map_health_status("healthy")
        assert status == ServiceStatus.HEALTHY

        status = dashboard._map_health_status("degraded")
        assert status == ServiceStatus.DEGRADED

        status = dashboard._map_health_status("unknown")
        assert status == ServiceStatus.UNKNOWN

    def test_map_connection_status(self, dashboard):
        """Test connection status mapping."""
        status = dashboard._map_connection_status("connected")
        assert status == ConnectionStatus.CONNECTED

        status = dashboard._map_connection_status("disconnected")
        assert status == ConnectionStatus.DISCONNECTED

        status = dashboard._map_connection_status("unknown")
        assert status == ConnectionStatus.ERROR

    def test_get_service_health(self, dashboard):
        """Test getting service health."""
        # Test with no services
        health = dashboard.get_service_health()
        assert health == {}

        # Test with specific service (should return error)
        health = dashboard.get_service_health("nonexistent")
        assert "error" in health

    def test_get_connection_health(self, dashboard):
        """Test getting connection health."""
        # Test with no connections
        health = dashboard.get_connection_health()
        assert health == {}

        # Test with specific connection (should return error)
        health = dashboard.get_connection_health("nonexistent")
        assert "error" in health

    def test_get_system_overview(self, dashboard):
        """Test getting system overview."""
        # Initially no overview
        overview = dashboard.get_system_overview()
        assert overview is None

    def test_get_operational_summary(self, dashboard):
        """Test getting operational summary."""
        summary = dashboard.get_operational_summary()
        assert "timestamp" in summary
        assert "system_overview" in summary
        assert "service_health" in summary
        assert "connection_health" in summary
        assert "dashboard_status" in summary

    def test_get_service_status_summary(self, dashboard):
        """Test getting service status summary."""
        summary = dashboard.get_service_status_summary()
        assert summary["total_services"] == 0
        assert "status_distribution" in summary
        assert "last_updated" in summary

    def test_get_connection_status_summary(self, dashboard):
        """Test getting connection status summary."""
        summary = dashboard.get_connection_status_summary()
        assert summary["total_connections"] == 0
        assert "status_distribution" in summary
        assert "last_updated" in summary

    def test_get_dashboard_config(self, dashboard):
        """Test getting dashboard configuration."""
        config = dashboard.get_dashboard_config()
        assert "health_check_interval" in config
        assert "connection_check_interval" in config
        assert "overview_update_interval" in config
        assert "monitoring_active" in config

    def test_update_config(self, dashboard):
        """Test configuration update."""
        new_config = {"health_check_interval": 60, "connection_check_interval": 30}

        dashboard.update_config(new_config)
        assert dashboard.health_check_interval == 60
        assert dashboard.connection_check_interval == 30


class TestDashboardManager:
    """Test DashboardManager class."""

    @pytest.fixture
    def manager(self):
        """Create a DashboardManager instance for testing."""
        config = ManagerConfig(
            enable_trend_analysis=False,
            enable_anomaly_detection=False,
            enable_operational_monitoring=False,
        )
        return DashboardManager(config)

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.config is not None
        assert manager.performance_dashboard is not None
        assert manager.trend_analyzer is not None
        assert manager.anomaly_detector is not None
        assert manager.operational_dashboard is not None
        assert manager.is_running is False
        assert manager._monitoring_tasks == []

    def test_get_dashboard_data_performance(self, manager):
        """Test getting performance dashboard data."""
        data = manager.get_dashboard_data("performance")
        assert data is not None
        assert "total_dashboards" in data
        assert "dashboards" in data

    def test_get_dashboard_data_operational(self, manager):
        """Test getting operational dashboard data."""
        data = manager.get_dashboard_data("operational")
        assert data is not None
        assert "timestamp" in data
        assert "system_overview" in data

    def test_get_dashboard_data_trends(self, manager):
        """Test getting trends data."""
        data = manager.get_dashboard_data("trends")
        assert data is not None
        assert "trend_analyses" in data
        assert "total_metrics_analyzed" in data

    def test_get_dashboard_data_anomalies(self, manager):
        """Test getting anomalies data."""
        data = manager.get_dashboard_data("anomalies")
        assert data is not None
        assert "anomaly_summaries" in data
        assert "total_metrics_with_anomalies" in data

    def test_get_dashboard_data_unknown_type(self, manager):
        """Test getting data for unknown dashboard type."""
        data = manager.get_dashboard_data("unknown_type")
        assert "error" in data

    def test_get_grafana_export(self, manager):
        """Test Grafana dashboard export."""
        export = manager.get_grafana_export("system_performance")
        assert export is not None
        assert "dashboard" in export

    def test_get_trend_analysis(self, manager):
        """Test getting trend analysis for specific metric."""
        # This will fail due to insufficient data, but should return error message
        result = manager.get_trend_analysis("nonexistent_metric")
        assert "error" in result

    def test_get_anomaly_detection(self, manager):
        """Test getting anomaly detection for specific metric."""
        # This will fail due to insufficient data, but should return error message
        result = manager.get_anomaly_detection("nonexistent_metric")
        assert "error" in result

    def test_get_dashboard_status(self, manager):
        """Test getting dashboard status."""
        status = manager.get_dashboard_status()
        assert status.performance_dashboard == "stopped"
        assert status.trend_analyzer == "stopped"
        assert status.anomaly_detector == "stopped"
        assert status.operational_dashboard == "stopped"
        assert status.overall_status == "stopped"
        assert status.uptime.total_seconds() >= 0

    def test_get_comprehensive_summary(self, manager):
        """Test getting comprehensive summary."""
        summary = manager.get_comprehensive_summary()
        assert "timestamp" in summary
        assert "status" in summary
        assert "performance_dashboard" in summary
        assert "operational_dashboard" in summary
        assert "trend_analyzer" in summary
        assert "anomaly_detector" in summary
        assert "configuration" in summary

    def test_update_config(self, manager):
        """Test configuration update."""
        new_config = {
            "performance_refresh_interval": 60,
            "trend_analysis_interval": 600,
        }

        manager.update_config(new_config)
        assert manager.config.performance_refresh_interval == 60
        assert manager.config.trend_analysis_interval == 600


@pytest.mark.asyncio
class TestDashboardAsync:
    """Test async dashboard functionality."""

    @pytest.fixture
    def manager(self):
        """Create a DashboardManager instance for async testing."""
        config = ManagerConfig(
            enable_trend_analysis=False,
            enable_anomaly_detection=False,
            enable_operational_monitoring=False,
        )
        return DashboardManager(config)

    async def test_start_stop_manager(self, manager):
        """Test starting and stopping the dashboard manager."""
        # Start manager
        await manager.start()
        assert manager.is_running is True

        # Stop manager
        await manager.stop()
        assert manager.is_running is False

    async def test_force_refresh_all(self, manager):
        """Test forcing refresh of all components."""
        # This should work even when not running
        await manager.force_refresh_all()
        # No exception should be raised

    async def test_operational_dashboard_lifecycle(self):
        """Test operational dashboard lifecycle."""
        dashboard = OperationalDashboard()

        # Start monitoring
        await dashboard.start_monitoring()

        # Stop monitoring
        await dashboard.stop_monitoring()

        # Should complete without errors

    async def test_performance_dashboard_auto_refresh(self):
        """Test performance dashboard auto-refresh."""
        dashboard = PerformanceDashboard()

        # Start auto-refresh
        task = asyncio.create_task(dashboard.start_auto_refresh())

        # Wait a bit
        await asyncio.sleep(0.1)

        # Cancel task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        # Should complete without errors


if __name__ == "__main__":
    pytest.main([__file__])
