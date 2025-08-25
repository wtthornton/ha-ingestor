"""Dashboard manager for orchestrating all dashboard components."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from ..utils.logging import get_logger
from .anomaly_detector import AnomalyDetector
from .operational_dashboard import OperationalDashboard
from .performance_dashboard import PerformanceDashboard
from .performance_alert_dashboard import (
    PerformanceAlertDashboard,
    get_performance_alert_dashboard,
    set_performance_alert_dashboard,
)
from .retention_dashboard import RetentionDashboard
from .schema_optimization_dashboard import SchemaOptimizationDashboard
from .trend_analyzer import TrendAnalyzer


@dataclass
class DashboardConfig:
    """Configuration for the dashboard manager."""

    # Performance dashboard settings
    performance_refresh_interval: int = 30  # seconds
    performance_time_range: str = "1h"  # 1h, 6h, 24h, 7d

    # Trend analysis settings
    trend_analysis_interval: int = 300  # 5 minutes
    trend_min_data_points: int = 10
    trend_confidence_threshold: float = 0.7

    # Anomaly detection settings
    anomaly_detection_interval: int = 600  # 10 minutes
    anomaly_sensitivity: str = "medium"  # low, medium, high
    anomaly_z_score_threshold: float = 3.0

    # Operational dashboard settings
    operational_refresh_interval: int = 60  # seconds
    health_check_interval: int = 30  # seconds
    connection_check_interval: int = 15  # seconds

    # Performance alert dashboard settings
    performance_alert_refresh_interval: int = 30  # seconds
    performance_alert_history_size: int = 1000
    enable_performance_alerting: bool = True

    # Retention dashboard settings
    retention_dashboard_refresh_interval: int = 30  # seconds
    retention_dashboard_history_size: int = 100
    enable_retention_management: bool = True

    # General settings
    auto_start: bool = True
    enable_grafana_export: bool = True
    enable_trend_analysis: bool = True
    enable_anomaly_detection: bool = True
    enable_operational_monitoring: bool = True


@dataclass
class DashboardStatus:
    """Status of all dashboard components."""

    timestamp: datetime
    performance_dashboard: str  # running, stopped, error
    trend_analyzer: str
    anomaly_detector: str
    operational_dashboard: str
    schema_optimization_dashboard: str
    performance_alert_dashboard: str
    retention_dashboard: str
    overall_status: str
    last_error: str | None
    uptime: timedelta


class DashboardManager:
    """Manages all dashboard components and provides unified interface."""

    def __init__(self, config: DashboardConfig | None = None) -> None:
        """Initialize the dashboard manager."""
        self.config = config or DashboardConfig()
        self.logger = get_logger(__name__)

        # Initialize dashboard components
        self.performance_dashboard = PerformanceDashboard(
            {
                "refresh_interval": self.config.performance_refresh_interval,
                "time_range": self.config.performance_time_range,
            }
        )

        self.trend_analyzer = TrendAnalyzer(
            {
                "min_data_points": self.config.trend_min_data_points,
                "confidence_threshold": self.config.trend_confidence_threshold,
            }
        )

        self.anomaly_detector = AnomalyDetector(
            {
                "sensitivity": self.config.anomaly_sensitivity,
                "z_score_threshold": self.config.anomaly_z_score_threshold,
            }
        )

        self.operational_dashboard = OperationalDashboard(
            {
                "health_check_interval": self.config.health_check_interval,
                "connection_check_interval": self.config.connection_check_interval,
                "overview_update_interval": self.config.operational_refresh_interval,
            }
        )

        self.schema_optimization_dashboard = SchemaOptimizationDashboard()
        
        self.performance_alert_dashboard = PerformanceAlertDashboard(
            {
                "refresh_interval": self.config.performance_alert_refresh_interval,
                "max_history_display": self.config.performance_alert_history_size,
                "enable_auto_refresh": self.config.enable_performance_alerting,
            }
        )

        # Initialize retention dashboard (will be properly initialized when retention system is available)
        self.retention_dashboard: RetentionDashboard | None = None

        # Manager state
        self.start_time = datetime.utcnow()
        self.is_running = False
        self._monitoring_tasks: list[asyncio.Task] = []
        self._last_error: str | None = None

    async def start(self) -> None:
        """Start all dashboard components."""
        try:
            self.logger.info("Starting dashboard manager")

            # Start performance dashboard auto-refresh
            if self.config.enable_trend_analysis:
                perf_task = asyncio.create_task(self._performance_monitoring_loop())
                self._monitoring_tasks.append(perf_task)

            # Start trend analysis loop
            if self.config.enable_trend_analysis:
                trend_task = asyncio.create_task(self._trend_analysis_loop())
                self._monitoring_tasks.append(trend_task)

            # Start anomaly detection loop
            if self.config.enable_anomaly_detection:
                anomaly_task = asyncio.create_task(self._anomaly_detection_loop())
                self._monitoring_tasks.append(anomaly_task)

            # Start operational dashboard
            if self.config.enable_operational_monitoring:
                await self.operational_dashboard.start_monitoring()

            # Start performance alert dashboard
            if self.config.enable_performance_alerting:
                await self.performance_alert_dashboard.start()

            # Start retention dashboard if available
            if self.config.enable_retention_management and self.retention_dashboard:
                await self.retention_dashboard.start()

            self.is_running = True
            self.logger.info("Dashboard manager started successfully")

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error starting dashboard manager: {e}")
            raise

    async def stop(self) -> None:
        """Stop all dashboard components."""
        try:
            self.logger.info("Stopping dashboard manager")

            # Cancel all monitoring tasks
            for task in self._monitoring_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            self._monitoring_tasks.clear()

            # Stop operational dashboard
            if self.config.enable_operational_monitoring:
                await self.operational_dashboard.stop_monitoring()

            # Stop performance alert dashboard
            await self.performance_alert_dashboard.stop()

            # Stop retention dashboard
            if self.retention_dashboard:
                await self.retention_dashboard.stop()

            self.is_running = False
            self.logger.info("Dashboard manager stopped successfully")

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error stopping dashboard manager: {e}")
            raise

    async def _performance_monitoring_loop(self) -> None:
        """Continuous loop for performance monitoring."""
        while self.is_running:
            try:
                await self.performance_dashboard.collect_metrics()
                await asyncio.sleep(self.config.performance_refresh_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _trend_analysis_loop(self) -> None:
        """Continuous loop for trend analysis."""
        while self.is_running:
            try:
                # Get metric history from performance dashboard
                metric_history = self.performance_dashboard.metric_history

                # Analyze trends for each metric
                for metric_name, history in metric_history.items():
                    if len(history) >= self.config.trend_min_data_points:
                        # Convert to format expected by trend analyzer
                        data_points = [(m.timestamp, m.value) for m in history]

                        # Analyze trend
                        trend_analysis = self.trend_analyzer.analyze_trend(
                            metric_name, data_points
                        )

                        if (
                            trend_analysis
                            and trend_analysis.confidence
                            >= self.config.trend_confidence_threshold
                        ):
                            self.logger.debug(
                                f"Trend detected for {metric_name}: {trend_analysis.trend_direction}"
                            )

                await asyncio.sleep(self.config.trend_analysis_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self.logger.error(f"Error in trend analysis loop: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _anomaly_detection_loop(self) -> None:
        """Continuous loop for anomaly detection."""
        while self.is_running:
            try:
                # Get metric history from performance dashboard
                metric_history = self.performance_dashboard.metric_history

                # Detect anomalies for each metric
                for metric_name, history in metric_history.items():
                    if len(history) >= 20:  # Minimum data points for anomaly detection
                        # Convert to format expected by anomaly detector
                        data_points = [(m.timestamp, m.value) for m in history]

                        # Detect anomalies
                        anomaly_result = self.anomaly_detector.detect_anomalies(
                            metric_name, data_points
                        )

                        if anomaly_result and anomaly_result.anomalies_detected:
                            self.logger.info(
                                f"Anomalies detected for {metric_name}: {len(anomaly_result.anomalies_detected)}"
                            )

                await asyncio.sleep(self.config.anomaly_detection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._last_error = str(e)
                self.logger.error(f"Error in anomaly detection loop: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def get_dashboard_data(
        self, dashboard_type: str, dashboard_name: str | None = None
    ) -> dict[str, Any] | None:
        """Get data from a specific dashboard."""
        try:
            if dashboard_type == "performance":
                if dashboard_name:
                    return self.performance_dashboard.get_dashboard_data(dashboard_name)
                else:
                    return self.performance_dashboard.get_dashboard_summary()

            elif dashboard_type == "operational":
                if dashboard_name == "overview":
                    return self.operational_dashboard.get_system_overview()
                elif dashboard_name == "services":
                    return self.operational_dashboard.get_service_health()
                elif dashboard_name == "connections":
                    return self.operational_dashboard.get_connection_health()
                else:
                    return self.operational_dashboard.get_operational_summary()

            elif dashboard_type == "trends":
                # Get trend analysis for all metrics
                metric_history = self.performance_dashboard.metric_history
                trend_analyses = {}

                for metric_name, history in metric_history.items():
                    if len(history) >= self.config.trend_min_data_points:
                        data_points = [(m.timestamp, m.value) for m in history]
                        analysis = self.trend_analyzer.analyze_trend(
                            metric_name, data_points
                        )
                        if analysis:
                            trend_analyses[metric_name] = {
                                "trend_direction": analysis.trend_direction,
                                "trend_strength": analysis.trend_strength,
                                "confidence": analysis.confidence,
                                "slope": analysis.slope,
                                "r_squared": analysis.r_squared,
                                "data_points": analysis.data_points,
                                "time_range_seconds": analysis.time_range.total_seconds(),
                                "analysis_time": analysis.analysis_time.isoformat(),
                            }

                return {
                    "trend_analyses": trend_analyses,
                    "total_metrics_analyzed": len(trend_analyses),
                    "analysis_time": datetime.utcnow().isoformat(),
                }

            elif dashboard_type == "anomalies":
                # Get anomaly detection results for all metrics
                metric_history = self.performance_dashboard.metric_history
                anomaly_summaries = {}

                for metric_name, history in metric_history.items():
                    if len(history) >= 20:
                        data_points = [(m.timestamp, m.value) for m in history]
                        summary = self.anomaly_detector.get_anomaly_summary(metric_name)
                        if summary["total_count"] > 0:
                            anomaly_summaries[metric_name] = summary

                return {
                    "anomaly_summaries": anomaly_summaries,
                    "total_metrics_with_anomaly": len(anomaly_summaries),
                    "detection_time": datetime.utcnow().isoformat(),
                }

            elif dashboard_type == "performance_alerts":
                # Get performance alert dashboard data
                if dashboard_name == "overview":
                    return await self.performance_alert_dashboard.get_dashboard_data()
                elif dashboard_name == "active_alerts":
                    return await self.performance_alert_dashboard._get_active_alerts_summary()
                elif dashboard_name == "alert_history":
                    return await self.performance_alert_dashboard._get_alert_history_summary()
                elif dashboard_name == "statistics":
                    return await self.performance_alert_dashboard._get_alert_statistics()
                elif dashboard_name == "recommendations":
                    return await self.performance_alert_dashboard._get_recommendations()
                else:
                    return await self.performance_alert_dashboard.get_dashboard_data()

            else:
                return {"error": f"Unknown dashboard type: {dashboard_type}"}

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e)}

    def get_grafana_export(self, dashboard_name: str) -> dict[str, Any] | None:
        """Export dashboard configuration in Grafana format."""
        try:
            if not self.config.enable_grafana_export:
                return {"error": "Grafana export is disabled"}

            return self.performance_dashboard.export_grafana_dashboard(dashboard_name)

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error exporting Grafana dashboard: {e}")
            return {"error": str(e)}

    def get_trend_analysis(
        self, metric_name: str, time_range: timedelta | None = None
    ) -> dict[str, Any] | None:
        """Get trend analysis for a specific metric."""
        try:
            if not self.config.enable_trend_analysis:
                return {"error": "Trend analysis is disabled"}

            # Get metric history
            history = self.performance_dashboard.get_metric_history(
                metric_name, time_range
            )

            if not history:
                return {"error": f"No data available for metric: {metric_name}"}

            # Convert to format expected by trend analyzer
            data_points = [(m.timestamp, m.value) for m in history]

            # Analyze trend
            analysis = self.trend_analyzer.analyze_trend(
                metric_name, data_points, time_range
            )

            if not analysis:
                return {"error": f"Insufficient data for trend analysis: {metric_name}"}

            return {
                "metric_name": analysis.metric_name,
                "trend_direction": analysis.trend_direction,
                "trend_strength": analysis.trend_strength,
                "confidence": analysis.confidence,
                "slope": analysis.slope,
                "r_squared": analysis.r_squared,
                "data_points": analysis.data_points,
                "time_range_seconds": analysis.time_range.total_seconds(),
                "analysis_time": analysis.analysis_time.isoformat(),
                "predictions": [
                    {"timestamp": ts.isoformat(), "value": val}
                    for ts, val in (analysis.predictions or [])
                ],
                "metadata": analysis.metadata,
            }

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error getting trend analysis: {e}")
            return {"error": str(e)}

    def get_anomaly_detection(
        self, metric_name: str, time_range: timedelta | None = None
    ) -> dict[str, Any] | None:
        """Get anomaly detection results for a specific metric."""
        try:
            if not self.config.enable_anomaly_detection:
                return {"error": "Anomaly detection is disabled"}

            # Get metric history
            history = self.performance_dashboard.get_metric_history(
                metric_name, time_range
            )

            if not history:
                return {"error": f"No data available for metric: {metric_name}"}

            # Convert to format expected by anomaly detector
            data_points = [(m.timestamp, m.value) for m in history]

            # Detect anomalies
            result = self.anomaly_detector.detect_anomalies(
                metric_name, data_points, time_range
            )

            if not result:
                return {
                    "error": f"Insufficient data for anomaly detection: {metric_name}"
                }

            return {
                "metric_name": result.metric_name,
                "anomalies_detected": [
                    {
                        "timestamp": a.timestamp.isoformat(),
                        "value": a.value,
                        "expected_value": a.expected_value,
                        "anomaly_type": a.anomaly_type.value,
                        "severity": a.severity.value,
                        "confidence": a.confidence,
                        "description": a.description,
                        "metadata": a.metadata,
                    }
                    for a in result.anomalies_detected
                ],
                "baseline_stats": result.baseline_stats,
                "detection_config": result.detection_config,
                "analysis_time": result.analysis_time.isoformat(),
                "total_data_points": result.total_data_points,
                "anomaly_rate": result.anomaly_rate,
            }

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error getting anomaly detection: {e}")
            return {"error": str(e)}

    def get_dashboard_status(self) -> DashboardStatus:
        """Get the status of all dashboard components."""
        uptime = datetime.utcnow() - self.start_time

        # Determine component statuses
        perf_status = (
            "running"
            if self.is_running and self.config.enable_trend_analysis
            else "stopped"
        )
        trend_status = (
            "running"
            if self.is_running and self.config.enable_trend_analysis
            else "stopped"
        )
        anomaly_status = (
            "running"
            if self.is_running and self.config.enable_anomaly_detection
            else "stopped"
        )
        ops_status = (
            "running"
            if self.is_running and self.config.enable_operational_monitoring
            else "stopped"
        )
        schema_opt_status = (
            "running"
            if self.is_running and self.schema_optimization_dashboard
            else "stopped"
        )
        perf_alert_status = (
            "running"
            if self.is_running and self.config.enable_performance_alerting
            else "stopped"
        )
        retention_status = (
            "running"
            if self.is_running and self.config.enable_retention_management and self.retention_dashboard
            else "stopped"
        )

        # Determine overall status
        if self.is_running and all(
            [
                perf_status == "running",
                trend_status == "running",
                anomaly_status == "running",
                ops_status == "running",
                schema_opt_status == "running",
                perf_alert_status == "running",
                retention_status == "running",
            ]
        ):
            overall_status = "healthy"
        elif self.is_running:
            overall_status = "degraded"
        else:
            overall_status = "stopped"

        return DashboardStatus(
            timestamp=datetime.utcnow(),
            performance_dashboard=perf_status,
            trend_analyzer=trend_status,
            anomaly_detector=anomaly_status,
            operational_dashboard=ops_status,
            schema_optimization_dashboard=schema_opt_status,
            performance_alert_dashboard=perf_alert_status,
            retention_dashboard=retention_status,
            overall_status=overall_status,
            last_error=self._last_error,
            uptime=uptime,
        )

    async def get_comprehensive_summary(self) -> dict[str, Any]:
        """Get a comprehensive summary of all dashboard components."""
        try:
            summary: dict[str, Any] = {
                "timestamp": datetime.now(UTC).isoformat(),
                "status": self.get_dashboard_status().__dict__,
                "performance_dashboard": self.performance_dashboard.get_dashboard_summary(),
                "operational_dashboard": self.operational_dashboard.get_operational_summary(),
                "trend_analyzer": self.trend_analyzer.get_analysis_statistics(),
                "anomaly_detector": self.anomaly_detector.get_detection_statistics(),
                "schema_optimization_dashboard": await self.schema_optimization_dashboard.get_dashboard_data(),
                "performance_alert_dashboard": await self.performance_alert_dashboard.get_dashboard_data(),
                "retention_dashboard": await self.retention_dashboard.get_dashboard_data() if self.retention_dashboard else None,
                "configuration": {
                    "performance_refresh_interval": self.config.performance_refresh_interval,
                    "trend_analysis_interval": self.config.trend_analysis_interval,
                    "anomaly_detection_interval": self.config.anomaly_detection_interval,
                    "operational_refresh_interval": self.config.operational_refresh_interval,
                    "performance_alert_refresh_interval": self.config.performance_alert_refresh_interval,
                    "performance_alert_history_size": self.config.performance_alert_history_size,
                    "retention_dashboard_refresh_interval": self.config.retention_dashboard_refresh_interval,
                    "retention_dashboard_history_size": self.config.retention_dashboard_history_size,
                    "enable_trend_analysis": self.config.enable_trend_analysis,
                    "enable_anomaly_detection": self.config.enable_anomaly_detection,
                    "enable_operational_monitoring": self.config.enable_operational_monitoring,
                    "enable_performance_alerting": self.config.enable_performance_alerting,
                    "enable_retention_management": self.config.enable_retention_management,
                },
            }

            # Convert datetime objects to ISO format
            status_dict = summary["status"]
            if isinstance(status_dict, dict):
                if "timestamp" in status_dict and hasattr(
                    status_dict["timestamp"], "isoformat"
                ):
                    status_dict["timestamp"] = status_dict["timestamp"].isoformat()
                if "uptime" in status_dict and hasattr(
                    status_dict["uptime"], "total_seconds"
                ):
                    status_dict["uptime"] = status_dict["uptime"].total_seconds()

            return summary

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error getting comprehensive summary: {e}")
            return {"error": str(e)}

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update dashboard configuration."""
        try:
            # Update configuration object
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Update component configurations
            self.performance_dashboard.config.update(
                {
                    "refresh_interval": self.config.performance_refresh_interval,
                    "time_range": self.config.performance_time_range,
                }
            )

            self.trend_analyzer.update_config(
                {
                    "min_data_points": self.config.trend_min_data_points,
                    "confidence_threshold": self.config.trend_confidence_threshold,
                }
            )

            self.anomaly_detector.update_config(
                {
                    "sensitivity": self.config.anomaly_sensitivity,
                    "z_score_threshold": self.config.anomaly_z_score_threshold,
                }
            )

            self.operational_dashboard.update_config(
                {
                    "health_check_interval": self.config.health_check_interval,
                    "connection_check_interval": self.config.connection_check_interval,
                    "overview_update_interval": self.config.operational_refresh_interval,
                }
            )

            self.performance_alert_dashboard.config.update(
                {
                    "refresh_interval": self.config.performance_alert_refresh_interval,
                    "max_history_display": self.config.performance_alert_history_size,
                    "enable_auto_refresh": self.config.enable_performance_alerting,
                }
            )

            self.logger.info("Dashboard configuration updated")

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error updating configuration: {e}")
            raise

    async def force_refresh_all(self) -> None:
        """Force refresh of all dashboard components."""
        try:
            self.logger.info("Forcing refresh of all dashboard components")

            # Refresh performance dashboard
            await self.performance_dashboard.collect_metrics()

            # Refresh operational dashboard
            await self.operational_dashboard.force_refresh()

            self.logger.info("All dashboard components refreshed")

        except Exception as e:
            self._last_error = str(e)
            self.logger.error(f"Error during forced refresh: {e}")
            raise
