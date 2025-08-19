"""Metrics registry for Prometheus metrics collection."""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from ..utils.logging import get_logger


@dataclass
class MetricValue:
    """A single metric value with timestamp."""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Metric:
    """A metric with name, help text, and values."""
    name: str
    help_text: str
    type: str  # counter, gauge, histogram, summary
    values: List[MetricValue] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class MetricsRegistry:
    """Registry for storing and managing metrics."""
    
    def __init__(self):
        """Initialize metrics registry."""
        self.logger = get_logger(__name__)
        self._metrics: Dict[str, Metric] = {}
        self._start_time = time.time()
        
    def register_counter(self, name: str, help_text: str) -> None:
        """Register a counter metric.
        
        Args:
            name: Metric name
            help_text: Help text for the metric
        """
        if name in self._metrics:
            self.logger.warning("Metric already registered", metric_name=name)
            return
            
        self._metrics[name] = Metric(
            name=name,
            help_text=help_text,
            type="counter"
        )
        self.logger.debug("Registered counter metric", metric_name=name)
    
    def register_gauge(self, name: str, help_text: str) -> None:
        """Register a gauge metric.
        
        Args:
            name: Metric name
            help_text: Help text for the metric
        """
        if name in self._metrics:
            self.logger.warning("Metric already registered", metric_name=name)
            return
            
        self._metrics[name] = Metric(
            name=name,
            help_text=help_text,
            type="gauge"
        )
        self.logger.debug("Registered gauge metric", metric_name=name)
    
    def register_histogram(self, name: str, help_text: str, buckets: Optional[List[float]] = None) -> None:
        """Register a histogram metric.
        
        Args:
            name: Metric name
            help_text: Help text for the metric
            buckets: Histogram buckets
        """
        if name in self._metrics:
            self.logger.warning("Metric already registered", metric_name=name)
            return
            
        metric = Metric(
            name=name,
            help_text=help_text,
            type="histogram"
        )
        
        # Store buckets in metric details
        metric.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
        
        self._metrics[name] = metric
        self.logger.debug("Registered histogram metric", metric_name=name, buckets=buckets)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to increment by
            labels: Optional labels for the metric
        """
        if name not in self._metrics:
            self.logger.warning("Counter metric not registered", metric_name=name)
            return
            
        metric = self._metrics[name]
        if metric.type != "counter":
            self.logger.error("Metric is not a counter", metric_name=name, metric_type=metric.type)
            return
        
        metric.values.append(MetricValue(
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        ))
        
        self.logger.debug("Incremented counter", metric_name=name, value=value, labels=labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value.
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels for the metric
        """
        if name not in self._metrics:
            self.logger.warning("Gauge metric not registered", metric_name=name)
            return
            
        metric = self._metrics[name]
        if metric.type != "gauge":
            self.logger.error("Metric is not a gauge", metric_name=name, metric_type=metric.type)
            return
        
        metric.values.append(MetricValue(
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        ))
        
        self.logger.debug("Set gauge", metric_name=name, value=value, labels=labels)
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value in a histogram metric.
        
        Args:
            name: Metric name
            value: Value to observe
            labels: Optional labels for the metric
        """
        if name not in self._metrics:
            self.logger.warning("Histogram metric not registered", metric_name=name)
            return
            
        metric = self._metrics[name]
        if metric.type != "histogram":
            self.logger.error("Metric is not a histogram", metric_name=name, metric_type=metric.type)
            return
        
        metric.values.append(MetricValue(
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        ))
        
        self.logger.debug("Observed histogram", metric_name=name, value=value, labels=labels)
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name.
        
        Args:
            name: Metric name
            
        Returns:
            Metric object or None if not found
        """
        return self._metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all registered metrics.
        
        Returns:
            Dictionary of all metrics
        """
        return self._metrics.copy()
    
    def get_metric_names(self) -> List[str]:
        """Get list of all metric names.
        
        Returns:
            List of metric names
        """
        return list(self._metrics.keys())
    
    def clear_metric(self, name: str) -> None:
        """Clear all values for a metric.
        
        Args:
            name: Metric name
        """
        if name in self._metrics:
            self._metrics[name].values.clear()
            self.logger.debug("Cleared metric values", metric_name=name)
    
    def clear_all_metrics(self) -> None:
        """Clear all metric values."""
        for metric in self._metrics.values():
            metric.values.clear()
        self.logger.debug("Cleared all metric values")
    
    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return time.time() - self._start_time
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        
        # Add service info
        lines.append("# HELP ha_ingestor_uptime_seconds Service uptime in seconds")
        lines.append("# TYPE ha_ingestor_uptime_seconds gauge")
        lines.append(f"ha_ingestor_uptime_seconds {self.get_uptime_seconds()}")
        lines.append("")
        
        for metric in self._metrics.values():
            # Add metric help and type
            lines.append(f"# HELP {metric.name} {metric.help_text}")
            lines.append(f"# TYPE {metric.name} {metric.type}")
            
            # Add metric values
            for value in metric.values:
                if value.labels:
                    # Format labels
                    label_str = ",".join([f'{k}="{v}"' for k, v in value.labels.items()])
                    lines.append(f"{metric.name}{{{label_str}}} {value.value}")
                else:
                    lines.append(f"{metric.name} {value.value}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        summary = {
            "uptime_seconds": self.get_uptime_seconds(),
            "total_metrics": len(self._metrics),
            "metrics": {}
        }
        
        for name, metric in self._metrics.items():
            summary["metrics"][name] = {
                "type": metric.type,
                "help": metric.help_text,
                "value_count": len(metric.values),
                "latest_value": metric.values[-1].value if metric.values else None,
                "latest_timestamp": metric.values[-1].timestamp if metric.values else None
            }
        
        return summary
