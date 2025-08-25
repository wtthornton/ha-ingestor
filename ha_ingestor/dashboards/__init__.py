"""Performance dashboards for Home Assistant Activity Ingestor."""

from .advanced_analytics import AdvancedAnalytics, AnalyticsResult, TrendAnalysis
from .anomaly_detector import AnomalyDetector
from .dashboard_manager import DashboardManager
from .operational_dashboard import OperationalDashboard
from .performance_alert_dashboard import (
    PerformanceAlertDashboard,
    get_performance_alert_dashboard,
    set_performance_alert_dashboard,
)
from .performance_dashboard import PerformanceDashboard
from .retention_dashboard import RetentionDashboard
from .schema_optimization_dashboard import (
    SchemaOptimizationDashboard,
    get_schema_optimization_dashboard,
    set_schema_optimization_dashboard,
)
from .trend_analyzer import TrendAnalyzer

__all__ = [
    "PerformanceDashboard",
    "TrendAnalyzer",
    "AnomalyDetector",
    "OperationalDashboard",
    "DashboardManager",
    "PerformanceAlertDashboard",
    "get_performance_alert_dashboard",
    "set_performance_alert_dashboard",
    "SchemaOptimizationDashboard",
    "get_schema_optimization_dashboard",
    "set_schema_optimization_dashboard",
    "RetentionDashboard",
    "AdvancedAnalytics",
    "AnalyticsResult",
    "TrendAnalysis",
]
