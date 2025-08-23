"""Performance dashboard for Home Assistant Activity Ingestor."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ..metrics.enhanced_collector import get_enhanced_metrics_collector
from ..monitoring.performance_monitor import get_performance_monitor
from ..utils.logging import get_logger


@dataclass
class DashboardMetric:
    """Represents a metric to be displayed on the dashboard."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    trend: str = "stable"  # up, down, stable
    trend_value: float = 0.0
    status: str = "normal"  # normal, warning, critical
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardPanel:
    """Represents a dashboard panel configuration."""

    id: str
    title: str
    type: str  # graph, stat, table, heatmap
    metrics: list[str]
    position: dict[str, int]  # x, y, width, height
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardConfig:
    """Configuration for a dashboard."""

    name: str
    description: str
    panels: list[DashboardPanel]
    refresh_interval: int = 30  # seconds
    time_range: str = "1h"  # 1h, 6h, 24h, 7d
    auto_refresh: bool = True


class PerformanceDashboard:
    """Main performance dashboard for monitoring system performance."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the performance dashboard."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Get monitoring components
        self.metrics_collector = get_enhanced_metrics_collector()
        self.performance_monitor = get_performance_monitor()

        # Dashboard state
        self.dashboards: dict[str, DashboardConfig] = {}
        self.current_metrics: dict[str, DashboardMetric] = {}
        self.metric_history: dict[str, list[DashboardMetric]] = {}

        # Initialize default dashboards
        self._initialize_default_dashboards()

    def _initialize_default_dashboards(self) -> None:
        """Initialize default dashboard configurations."""

        # System Performance Dashboard
        system_panels = [
            DashboardPanel(
                id="cpu_usage",
                title="CPU Usage",
                type="graph",
                metrics=["cpu_percent", "cpu_count"],
                position={"x": 0, "y": 0, "width": 6, "height": 4},
                options={"yAxis": {"min": 0, "max": 100}, "color": "blue"},
            ),
            DashboardPanel(
                id="memory_usage",
                title="Memory Usage",
                type="graph",
                metrics=["memory_percent", "memory_available"],
                position={"x": 6, "y": 0, "width": 6, "height": 4},
                options={"yAxis": {"min": 0, "max": 100}, "color": "green"},
            ),
            DashboardPanel(
                id="disk_io",
                title="Disk I/O",
                type="graph",
                metrics=["disk_read_bytes", "disk_write_bytes"],
                position={"x": 0, "y": 4, "width": 6, "height": 4},
                options={"yAxis": {"min": 0}, "color": "orange"},
            ),
            DashboardPanel(
                id="network_io",
                title="Network I/O",
                type="graph",
                metrics=["network_bytes_sent", "network_bytes_recv"],
                position={"x": 6, "y": 4, "width": 6, "height": 4},
                options={"yAxis": {"min": 0}, "color": "purple"},
            ),
        ]

        self.dashboards["system_performance"] = DashboardConfig(
            name="System Performance",
            description="Real-time system resource monitoring",
            panels=system_panels,
            refresh_interval=15,
            time_range="1h",
        )

        # Application Performance Dashboard
        app_panels = [
            DashboardPanel(
                id="event_processing",
                title="Event Processing Rate",
                type="graph",
                metrics=["events_per_second", "total_events_processed"],
                position={"x": 0, "y": 0, "width": 8, "height": 4},
                options={"yAxis": {"min": 0}, "color": "red"},
            ),
            DashboardPanel(
                id="pipeline_performance",
                title="Pipeline Performance",
                type="graph",
                metrics=["pipeline_latency", "filter_processing_time"],
                position={"x": 8, "y": 0, "width": 4, "height": 4},
                options={"yAxis": {"min": 0}, "color": "cyan"},
            ),
            DashboardPanel(
                id="error_rates",
                title="Error Rates",
                type="graph",
                metrics=["error_rate", "warning_rate"],
                position={"x": 0, "y": 4, "width": 6, "height": 4},
                options={"yAxis": {"min": 0}, "color": "red"},
            ),
            DashboardPanel(
                id="throughput",
                title="System Throughput",
                type="stat",
                metrics=["total_throughput", "peak_throughput"],
                position={"x": 6, "y": 4, "width": 6, "height": 4},
                options={"colorMode": "value", "graphMode": "area"},
            ),
        ]

        self.dashboards["application_performance"] = DashboardConfig(
            name="Application Performance",
            description="Application-specific performance metrics",
            panels=app_panels,
            refresh_interval=10,
            time_range="1h",
        )

        # Operational Dashboard
        ops_panels = [
            DashboardPanel(
                id="service_status",
                title="Service Status",
                type="stat",
                metrics=["mqtt_status", "websocket_status", "influxdb_status"],
                position={"x": 0, "y": 0, "width": 4, "height": 2},
                options={"colorMode": "background", "graphMode": "none"},
            ),
            DashboardPanel(
                id="connection_health",
                title="Connection Health",
                type="graph",
                metrics=["connection_count", "connection_errors"],
                position={"x": 4, "y": 0, "width": 8, "height": 4},
                options={"yAxis": {"min": 0}, "color": "blue"},
            ),
            DashboardPanel(
                id="alert_summary",
                title="Alert Summary",
                type="table",
                metrics=["active_alerts", "alert_severity_distribution"],
                position={"x": 0, "y": 4, "width": 12, "height": 4},
                options={"showHeader": True, "sortBy": "severity"},
            ),
        ]

        self.dashboards["operational"] = DashboardConfig(
            name="Operational Overview",
            description="System operational status and health",
            panels=ops_panels,
            refresh_interval=20,
            time_range="6h",
        )

    async def collect_metrics(self) -> dict[str, DashboardMetric]:
        """Collect current metrics for all dashboards."""
        try:
            current_time = datetime.utcnow()
            metrics = {}

            # Collect system metrics
            system_metrics = self.performance_monitor.get_system_metrics()
            if system_metrics:
                metrics.update(
                    {
                        "cpu_percent": DashboardMetric(
                            name="CPU Usage",
                            value=system_metrics.cpu_percent,
                            unit="%",
                            timestamp=current_time,
                            status=self._get_status_for_value(
                                system_metrics.cpu_percent, 80, 95
                            ),
                        ),
                        "memory_percent": DashboardMetric(
                            name="Memory Usage",
                            value=system_metrics.memory_percent,
                            unit="%",
                            timestamp=current_time,
                            status=self._get_status_for_value(
                                system_metrics.memory_percent, 80, 95
                            ),
                        ),
                        "disk_read_bytes": DashboardMetric(
                            name="Disk Read",
                            value=system_metrics.disk_read_bytes
                            / (1024 * 1024),  # Convert to MB
                            unit="MB/s",
                            timestamp=current_time,
                        ),
                        "disk_write_bytes": DashboardMetric(
                            name="Disk Write",
                            value=system_metrics.disk_write_bytes
                            / (1024 * 1024),  # Convert to MB
                            unit="MB/s",
                            timestamp=current_time,
                        ),
                        "network_bytes_sent": DashboardMetric(
                            name="Network Sent",
                            value=system_metrics.network_bytes_sent
                            / (1024 * 1024),  # Convert to MB
                            unit="MB/s",
                            timestamp=current_time,
                        ),
                        "network_bytes_recv": DashboardMetric(
                            name="Network Received",
                            value=system_metrics.network_bytes_recv
                            / (1024 * 1024),  # Convert to MB
                            unit="MB/s",
                            timestamp=current_time,
                        ),
                    }
                )

            # Collect performance metrics
            perf_metrics = self.performance_monitor.get_performance_metrics()
            if perf_metrics:
                metrics.update(
                    {
                        "events_per_second": DashboardMetric(
                            name="Events/Second",
                            value=perf_metrics.events_per_second,
                            unit="events/s",
                            timestamp=current_time,
                            status=self._get_status_for_value(
                                perf_metrics.events_per_second, 1000, 5000
                            ),
                        ),
                        "pipeline_latency": DashboardMetric(
                            name="Pipeline Latency",
                            value=perf_metrics.avg_pipeline_latency,
                            unit="ms",
                            timestamp=current_time,
                            status=self._get_status_for_value(
                                perf_metrics.avg_pipeline_latency,
                                100,
                                500,
                                reverse=True,
                            ),
                        ),
                        "total_events_processed": DashboardMetric(
                            name="Total Events",
                            value=perf_metrics.total_events_processed,
                            unit="events",
                            timestamp=current_time,
                        ),
                    }
                )

            # Collect business metrics
            business_metrics = self.performance_monitor.get_business_metrics()
            if business_metrics:
                metrics.update(
                    {
                        "error_rate": DashboardMetric(
                            name="Error Rate",
                            value=business_metrics.error_rate,
                            unit="%",
                            timestamp=current_time,
                            status=self._get_status_for_value(
                                business_metrics.error_rate, 5, 10
                            ),
                        ),
                        "warning_rate": DashboardMetric(
                            name="Warning Rate",
                            value=business_metrics.warning_rate,
                            unit="%",
                            timestamp=current_time,
                            status=self._get_status_for_value(
                                business_metrics.warning_rate, 10, 20
                            ),
                        ),
                    }
                )

            # Update current metrics and history
            self.current_metrics = metrics
            for metric_name, metric in metrics.items():
                if metric_name not in self.metric_history:
                    self.metric_history[metric_name] = []
                self.metric_history[metric_name].append(metric)

                # Keep only last 1000 data points
                if len(self.metric_history[metric_name]) > 1000:
                    self.metric_history[metric_name] = self.metric_history[metric_name][
                        -1000:
                    ]

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return {}

    def _get_status_for_value(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
        reverse: bool = False,
    ) -> str:
        """Determine status based on threshold values."""
        if reverse:
            # For reverse case: lower values are worse
            # In reverse mode, thresholds represent minimum acceptable values (higher is better)
            if value >= critical_threshold:
                return "normal"
            elif value >= warning_threshold:
                return "warning"
            else:
                return "critical"
        else:
            # For normal case: higher values are worse
            if value >= critical_threshold:
                return "critical"
            elif value >= warning_threshold:
                return "warning"
            else:
                return "normal"

    def get_dashboard_config(self, dashboard_name: str) -> DashboardConfig | None:
        """Get dashboard configuration by name."""
        return self.dashboards.get(dashboard_name)

    def list_dashboards(self) -> list[str]:
        """List all available dashboard names."""
        return list(self.dashboards.keys())

    def get_dashboard_data(self, dashboard_name: str) -> dict[str, Any] | None:
        """Get dashboard data for a specific dashboard."""
        config = self.get_dashboard_config(dashboard_name)
        if not config:
            return None

        dashboard_data = {
            "name": config.name,
            "description": config.description,
            "refresh_interval": config.refresh_interval,
            "time_range": config.time_range,
            "auto_refresh": config.auto_refresh,
            "panels": [],
            "last_updated": datetime.utcnow().isoformat(),
        }

        for panel in config.panels:
            panel_data = {
                "id": panel.id,
                "title": panel.title,
                "type": panel.type,
                "position": panel.position,
                "options": panel.options,
                "metrics": [],
            }

            # Add metric data for this panel
            for metric_name in panel.metrics:
                if metric_name in self.current_metrics:
                    metric = self.current_metrics[metric_name]
                    panel_data["metrics"].append(
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "unit": metric.unit,
                            "timestamp": metric.timestamp.isoformat(),
                            "trend": metric.trend,
                            "trend_value": metric.trend_value,
                            "status": metric.status,
                            "metadata": metric.metadata,
                        }
                    )

            dashboard_data["panels"].append(panel_data)

        return dashboard_data

    def get_metric_history(
        self, metric_name: str, time_range: timedelta | None = None
    ) -> list[DashboardMetric]:
        """Get metric history for a specific metric."""
        if metric_name not in self.metric_history:
            return []

        history = self.metric_history[metric_name]

        if time_range:
            cutoff_time = datetime.utcnow() - time_range
            history = [m for m in history if m.timestamp >= cutoff_time]

        return history

    def export_grafana_dashboard(self, dashboard_name: str) -> dict[str, Any] | None:
        """Export dashboard configuration in Grafana format."""
        config = self.get_dashboard_config(dashboard_name)
        if not config:
            return None

        # Convert to Grafana dashboard format
        grafana_dashboard = {
            "dashboard": {
                "id": None,
                "title": config.name,
                "description": config.description,
                "tags": ["ha-ingestor", "performance"],
                "timezone": "browser",
                "refresh": f"{config.refresh_interval}s",
                "time": {"from": f"now-{config.time_range}", "to": "now"},
                "panels": [],
            },
            "overwrite": True,
        }

        for panel in config.panels:
            grafana_panel = {
                "id": panel.id,
                "title": panel.title,
                "type": self._convert_panel_type(panel.type),
                "gridPos": panel.position,
                "targets": [],
            }

            # Add targets for each metric
            for metric_name in panel.metrics:
                target = {
                    "expr": f"ha_ingestor_{metric_name}",
                    "legendFormat": metric_name,
                    "refId": metric_name,
                }
                grafana_panel["targets"].append(target)

            grafana_dashboard["dashboard"]["panels"].append(grafana_panel)

        return grafana_dashboard

    def _convert_panel_type(self, panel_type: str) -> str:
        """Convert internal panel type to Grafana panel type."""
        type_mapping = {
            "graph": "timeseries",
            "stat": "stat",
            "table": "table",
            "heatmap": "heatmap",
        }
        return type_mapping.get(panel_type, "timeseries")

    async def start_auto_refresh(self) -> None:
        """Start automatic dashboard refresh."""
        while True:
            try:
                await self.collect_metrics()
                await asyncio.sleep(30)  # Refresh every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in auto-refresh: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    def get_dashboard_summary(self) -> dict[str, Any]:
        """Get summary of all dashboards."""
        summary = {
            "total_dashboards": len(self.dashboards),
            "dashboards": {},
            "total_metrics": len(self.current_metrics),
            "last_updated": datetime.utcnow().isoformat(),
        }

        for name, config in self.dashboards.items():
            summary["dashboards"][name] = {
                "name": config.name,
                "description": config.description,
                "panels": len(config.panels),
                "refresh_interval": config.refresh_interval,
                "time_range": config.time_range,
            }

        return summary
