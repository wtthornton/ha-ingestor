"""Anomaly detection for performance metrics."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from ..utils.logging import get_logger


class AnomalyType(Enum):
    """Types of anomalies that can be detected."""

    SPIKE = "spike"  # Sudden increase in value
    DROP = "drop"  # Sudden decrease in value
    TREND_CHANGE = "trend_change"  # Change in trend direction
    LEVEL_SHIFT = "level_shift"  # Persistent change in baseline
    SEASONAL_ANOMALY = "seasonal_anomaly"  # Deviation from seasonal pattern
    VOLATILITY_CHANGE = "volatility_change"  # Change in variability


class AnomalySeverity(Enum):
    """Severity levels for detected anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyPoint:
    """Represents a detected anomaly point."""

    timestamp: datetime
    value: float
    expected_value: float
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    confidence: float  # 0.0 to 1.0
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection analysis."""

    metric_name: str
    anomalies_detected: list[AnomalyPoint]
    baseline_stats: dict[str, float]
    detection_config: dict[str, Any]
    analysis_time: datetime
    total_data_points: int
    anomaly_rate: float  # Percentage of data points that are anomalies


class AnomalyDetector:
    """Detects anomalies in performance metrics using various algorithms."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the anomaly detector."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Configuration
        self.z_score_threshold = self.config.get("z_score_threshold", 3.0)
        self.iqr_multiplier = self.config.get("iqr_multiplier", 1.5)
        self.min_data_points = self.config.get("min_data_points", 20)
        self.sensitivity = self.config.get("sensitivity", "medium")  # low, medium, high

        # Adjust thresholds based on sensitivity
        self._adjust_thresholds_for_sensitivity()

        # Detection history
        self.detection_history: dict[str, list[AnomalyPoint]] = {}
        self.baseline_cache: dict[str, dict[str, float]] = {}
        self.cache_ttl = timedelta(hours=1)

    def _adjust_thresholds_for_sensitivity(self) -> None:
        """Adjust detection thresholds based on sensitivity level."""
        if self.sensitivity == "low":
            self.z_score_threshold = 4.0
            self.iqr_multiplier = 2.0
        elif self.sensitivity == "high":
            self.z_score_threshold = 2.5
            self.iqr_multiplier = 1.2
        # medium uses default values

    def detect_anomalies(
        self,
        metric_name: str,
        data_points: list[tuple[datetime, float]],
        time_range: timedelta | None = None,
    ) -> AnomalyDetectionResult | None:
        """Detect anomalies in a metric's data points."""
        try:
            if len(data_points) < self.min_data_points:
                self.logger.debug(
                    f"Insufficient data points for anomaly detection: {len(data_points)} < {self.min_data_points}"
                )
                return None

            # Sort by timestamp
            sorted_data = sorted(data_points, key=lambda x: x[0])

            # Apply time range filter if specified
            if time_range:
                cutoff_time = datetime.utcnow() - time_range
                sorted_data = [
                    (ts, val) for ts, val in sorted_data if ts >= cutoff_time
                ]

                if len(sorted_data) < self.min_data_points:
                    return None

            # Extract values and timestamps
            timestamps = [ts for ts, _ in sorted_data]
            values = [val for _, val in sorted_data]

            # Calculate baseline statistics
            baseline_stats = self._calculate_baseline_statistics(values)

            # Detect anomalies using multiple methods
            anomalies = []

            # Z-score method
            z_score_anomalies = self._detect_z_score_anomalies(
                metric_name, timestamps, values, baseline_stats
            )
            anomalies.extend(z_score_anomalies)

            # IQR method
            iqr_anomalies = self._detect_iqr_anomalies(
                metric_name, timestamps, values, baseline_stats
            )
            anomalies.extend(iqr_anomalies)

            # Trend change detection
            trend_anomalies = self._detect_trend_changes(
                metric_name, timestamps, values, baseline_stats
            )
            anomalies.extend(trend_anomalies)

            # Level shift detection
            level_shift_anomalies = self._detect_level_shifts(
                metric_name, timestamps, values, baseline_stats
            )
            anomalies.extend(level_shift_anomalies)

            # Remove duplicate anomalies (same timestamp, similar type)
            unique_anomalies = self._deduplicate_anomalies(anomalies)

            # Calculate anomaly rate
            anomaly_rate = len(unique_anomalies) / len(values) * 100

            # Create result
            result = AnomalyDetectionResult(
                metric_name=metric_name,
                anomalies_detected=unique_anomalies,
                baseline_stats=baseline_stats,
                detection_config={
                    "z_score_threshold": self.z_score_threshold,
                    "iqr_multiplier": self.iqr_multiplier,
                    "sensitivity": self.sensitivity,
                },
                analysis_time=datetime.utcnow(),
                total_data_points=len(values),
                anomaly_rate=anomaly_rate,
            )

            # Update history and cache
            self.detection_history[metric_name] = unique_anomalies
            self.baseline_cache[metric_name] = baseline_stats

            return result

        except Exception as e:
            self.logger.error(f"Error detecting anomalies for {metric_name}: {e}")
            return None

    def _calculate_baseline_statistics(self, values: list[float]) -> dict[str, float]:
        """Calculate baseline statistics for anomaly detection."""
        try:
            if len(values) < 2:
                return {
                    "mean": values[0] if values else 0.0,
                    "std_dev": 0.0,
                    "median": values[0] if values else 0.0,
                }

            mean = statistics.mean(values)
            std_dev = statistics.stdev(values)
            median = statistics.median(values)

            # Calculate quartiles for IQR
            sorted_values = sorted(values)
            q1 = sorted_values[len(sorted_values) // 4]
            q3 = sorted_values[3 * len(sorted_values) // 4]
            iqr = q3 - q1

            # Calculate percentiles
            p95 = sorted_values[int(0.95 * len(sorted_values))]
            p5 = sorted_values[int(0.05 * len(sorted_values))]

            return {
                "mean": mean,
                "std_dev": std_dev,
                "median": median,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "p5": p5,
                "p95": p95,
                "min": min(values),
                "max": max(values),
            }

        except Exception as e:
            self.logger.error(f"Error calculating baseline statistics: {e}")
            return {"mean": 0.0, "std_dev": 0.0, "median": 0.0}

    def _detect_z_score_anomalies(
        self,
        metric_name: str,
        timestamps: list[datetime],
        values: list[float],
        baseline_stats: dict[str, float],
    ) -> list[AnomalyPoint]:
        """Detect anomalies using Z-score method."""
        anomalies: list[AnomalyPoint] = []
        mean = baseline_stats["mean"]
        std_dev = baseline_stats["std_dev"]

        if std_dev == 0:
            return anomalies

        for _i, (timestamp, value) in enumerate(zip(timestamps, values, strict=False)):
            z_score = abs(value - mean) / std_dev

            if z_score > self.z_score_threshold:
                # Determine anomaly type
                if value > mean:
                    anomaly_type = AnomalyType.SPIKE
                else:
                    anomaly_type = AnomalyType.DROP

                # Determine severity
                severity = self._determine_severity(z_score)

                # Calculate confidence
                confidence = min(1.0, z_score / (self.z_score_threshold * 2))

                anomaly = AnomalyPoint(
                    timestamp=timestamp,
                    value=value,
                    expected_value=mean,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    confidence=confidence,
                    description=f"Z-score anomaly: {z_score:.2f} (threshold: {self.z_score_threshold})",
                    metadata={"z_score": z_score, "method": "z_score"},
                )

                anomalies.append(anomaly)

        return anomalies

    def _detect_iqr_anomalies(
        self,
        metric_name: str,
        timestamps: list[datetime],
        values: list[float],
        baseline_stats: dict[str, float],
    ) -> list[AnomalyPoint]:
        """Detect anomalies using Interquartile Range (IQR) method."""
        anomalies: list[AnomalyPoint] = []
        q1 = baseline_stats["q1"]
        q3 = baseline_stats["q3"]
        iqr = baseline_stats["iqr"]

        lower_bound = q1 - (self.iqr_multiplier * iqr)
        upper_bound = q3 + (self.iqr_multiplier * iqr)

        for _i, (timestamp, value) in enumerate(zip(timestamps, values, strict=False)):
            if value < lower_bound or value > upper_bound:
                # Determine anomaly type
                if value > upper_bound:
                    anomaly_type = AnomalyType.SPIKE
                else:
                    anomaly_type = AnomalyType.DROP

                # Calculate distance from bounds
                if value > upper_bound:
                    distance = (value - upper_bound) / iqr
                else:
                    distance = (lower_bound - value) / iqr

                # Determine severity
                severity = self._determine_severity(distance * 2)  # Scale for IQR

                # Calculate confidence
                confidence = min(1.0, distance / 3.0)

                anomaly = AnomalyPoint(
                    timestamp=timestamp,
                    value=value,
                    expected_value=q3 if value > upper_bound else q1,
                    anomaly_type=anomaly_type,
                    severity=severity,
                    confidence=confidence,
                    description=f"IQR anomaly: {distance:.2f} IQR from bounds",
                    metadata={
                        "distance_iqr": distance,
                        "method": "iqr",
                        "bounds": [lower_bound, upper_bound],
                    },
                )

                anomalies.append(anomaly)

        return anomalies

    def _detect_trend_changes(
        self,
        metric_name: str,
        timestamps: list[datetime],
        values: list[float],
        baseline_stats: dict[str, float],
    ) -> list[AnomalyPoint]:
        """Detect trend changes and reversals."""
        anomalies: list[AnomalyPoint] = []

        if len(values) < 10:
            return anomalies

        # Use sliding window to detect trend changes
        window_size = min(10, len(values) // 4)

        for i in range(window_size, len(values) - window_size):
            # Calculate trend before and after the point
            before_values = values[i - window_size : i]
            after_values = values[i : i + window_size]

            before_trend = self._calculate_simple_trend(before_values)
            after_trend = self._calculate_simple_trend(after_values)

            # Check for trend change
            if abs(before_trend - after_trend) > 0.5:  # Significant change
                # Calculate confidence based on trend difference
                confidence = min(1.0, abs(before_trend - after_trend) / 2.0)

                anomaly = AnomalyPoint(
                    timestamp=timestamps[i],
                    value=values[i],
                    expected_value=baseline_stats["mean"],
                    anomaly_type=AnomalyType.TREND_CHANGE,
                    severity=AnomalySeverity.MEDIUM,
                    confidence=confidence,
                    description=f"Trend change: {before_trend:.2f} -> {after_trend:.2f}",
                    metadata={
                        "before_trend": before_trend,
                        "after_trend": after_trend,
                        "method": "trend_change",
                        "window_size": window_size,
                    },
                )

                anomalies.append(anomaly)

        return anomalies

    def _detect_level_shifts(
        self,
        metric_name: str,
        timestamps: list[datetime],
        values: list[float],
        baseline_stats: dict[str, float],
    ) -> list[AnomalyPoint]:
        """Detect persistent changes in baseline level."""
        anomalies = []

        if len(values) < 20:
            return anomalies

        # Use CUSUM-like approach to detect level shifts
        window_size = min(20, len(values) // 3)
        threshold = baseline_stats["std_dev"] * 2

        for i in range(window_size, len(values) - window_size):
            # Calculate mean before and after
            before_mean = statistics.mean(values[i - window_size : i])
            after_mean = statistics.mean(values[i : i + window_size])

            # Check for significant level shift
            shift_magnitude = abs(after_mean - before_mean)

            if shift_magnitude > threshold:
                # Calculate confidence
                confidence = min(1.0, shift_magnitude / (threshold * 2))

                anomaly = AnomalyPoint(
                    timestamp=timestamps[i],
                    value=values[i],
                    expected_value=before_mean,
                    anomaly_type=AnomalyType.LEVEL_SHIFT,
                    severity=AnomalySeverity.HIGH,
                    confidence=confidence,
                    description=f"Level shift: {shift_magnitude:.2f} (threshold: {threshold:.2f})",
                    metadata={
                        "shift_magnitude": shift_magnitude,
                        "before_mean": before_mean,
                        "after_mean": after_mean,
                        "method": "level_shift",
                        "window_size": window_size,
                    },
                )

                anomalies.append(anomaly)

        return anomalies

    def _calculate_simple_trend(self, values: list[float]) -> float:
        """Calculate simple trend direction for a list of values."""
        if len(values) < 2:
            return 0.0

        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * val for i, val in enumerate(values))
        x2_sum = sum(i * i for i in range(n))

        try:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            return slope
        except ZeroDivisionError:
            return 0.0

    def _determine_severity(self, score: float) -> AnomalySeverity:
        """Determine anomaly severity based on detection score."""
        if score > 5.0:
            return AnomalySeverity.CRITICAL
        elif score > 4.0:
            return AnomalySeverity.HIGH
        elif score > 3.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def _deduplicate_anomalies(
        self, anomalies: list[AnomalyPoint]
    ) -> list[AnomalyPoint]:
        """Remove duplicate anomalies based on timestamp and type."""
        if not anomalies:
            return []

        # Sort by timestamp
        sorted_anomalies = sorted(anomalies, key=lambda x: x.timestamp)
        unique_anomalies = []

        for anomaly in sorted_anomalies:
            # Check if we already have a similar anomaly at this timestamp
            is_duplicate = False

            for existing in unique_anomalies:
                time_diff = abs(
                    (anomaly.timestamp - existing.timestamp).total_seconds()
                )

                if (
                    time_diff < 60 and anomaly.anomaly_type == existing.anomaly_type
                ):  # Within 1 minute
                    # Keep the one with higher confidence
                    if anomaly.confidence > existing.confidence:
                        unique_anomalies.remove(existing)
                        unique_anomalies.append(anomaly)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_anomalies.append(anomaly)

        return unique_anomalies

    def get_anomaly_summary(
        self, metric_name: str, time_range: timedelta | None = None
    ) -> dict[str, Any]:
        """Get summary of anomalies for a specific metric."""
        if metric_name not in self.detection_history:
            return {"anomalies": [], "total_count": 0}

        anomalies = self.detection_history[metric_name]

        # Apply time range filter if specified
        if time_range:
            cutoff_time = datetime.utcnow() - time_range
            anomalies = [a for a in anomalies if a.timestamp >= cutoff_time]

        # Count by type and severity
        type_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}

        for anomaly in anomalies:
            # Count by type
            anomaly_type = anomaly.anomaly_type.value
            type_counts[anomaly_type] = type_counts.get(anomaly_type, 0) + 1

            # Count by severity
            severity = anomaly.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "anomalies": [self._anomaly_to_dict(a) for a in anomalies],
            "total_count": len(anomalies),
            "type_distribution": type_counts,
            "severity_distribution": severity_counts,
            "time_range": time_range.total_seconds() if time_range else None,
        }

    def _anomaly_to_dict(self, anomaly: AnomalyPoint) -> dict[str, Any]:
        """Convert anomaly point to dictionary for serialization."""
        return {
            "timestamp": anomaly.timestamp.isoformat(),
            "value": anomaly.value,
            "expected_value": anomaly.expected_value,
            "anomaly_type": anomaly.anomaly_type.value,
            "severity": anomaly.severity.value,
            "confidence": anomaly.confidence,
            "description": anomaly.description,
            "metadata": anomaly.metadata,
        }

    def get_detection_statistics(self) -> dict[str, Any]:
        """Get statistics about anomaly detection performance."""
        total_anomalies = sum(
            len(anomalies) for anomalies in self.detection_history.values()
        )

        return {
            "total_metrics_monitored": len(self.detection_history),
            "total_anomalies_detected": total_anomalies,
            "z_score_threshold": self.z_score_threshold,
            "iqr_multiplier": self.iqr_multiplier,
            "sensitivity": self.sensitivity,
            "min_data_points": self.min_data_points,
            "cache_size": len(self.baseline_cache),
        }

    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self.baseline_cache.clear()
        self.logger.info("Anomaly detection cache cleared")

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update detection configuration."""
        self.config.update(new_config)

        # Update specific parameters
        if "z_score_threshold" in new_config:
            self.z_score_threshold = new_config["z_score_threshold"]
        if "iqr_multiplier" in new_config:
            self.iqr_multiplier = new_config["iqr_multiplier"]
        if "sensitivity" in new_config:
            self.sensitivity = new_config["sensitivity"]
            self._adjust_thresholds_for_sensitivity()

        self.logger.info("Anomaly detection configuration updated")
