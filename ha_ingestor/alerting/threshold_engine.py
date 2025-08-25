"""Threshold engine for advanced alerting conditions."""

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from ..utils.logging import get_logger


class ThresholdType(Enum):
    """Types of threshold conditions."""

    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    PERCENT_CHANGE = "percent_change"
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    VOLATILITY = "volatility"
    OUTLIER = "outlier"


@dataclass
class ThresholdCondition:
    """Definition of a threshold condition."""

    field_path: str
    threshold_type: ThresholdType
    threshold_value: float
    time_window_minutes: int = 5
    min_data_points: int = 3
    aggregation_method: str = "latest"  # latest, avg, min, max, sum
    trend_sensitivity: float = 0.1  # For trend detection
    volatility_threshold: float = 0.2  # For volatility detection
    outlier_std_dev: float = 2.0  # For outlier detection

    def __post_init__(self) -> None:
        """Validate threshold condition configuration."""
        if self.time_window_minutes < 1:
            raise ValueError("time_window_minutes must be at least 1")

        if self.min_data_points < 2:
            raise ValueError("min_data_points must be at least 2")

        if self.aggregation_method not in ["latest", "avg", "min", "max", "sum"]:
            raise ValueError(
                "aggregation_method must be one of: latest, avg, min, max, sum"
            )

        if self.trend_sensitivity <= 0:
            raise ValueError("trend_sensitivity must be positive")

        if self.volatility_threshold <= 0:
            raise ValueError("volatility_threshold must be positive")

        if self.outlier_std_dev <= 0:
            raise ValueError("outlier_std_dev must be positive")


@dataclass
class DataPoint:
    """A single data point with timestamp and value."""

    timestamp: datetime
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate data point."""
        if not isinstance(self.value, int | float):
            raise ValueError("value must be numeric")


class ThresholdEngine:
    """Engine for evaluating threshold-based alerting conditions."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the threshold engine."""
        self.config = config or {}
        self.logger = get_logger(__name__)
        self.data_history: dict[str, list[DataPoint]] = {}
        self.max_history_size = 10000  # Maximum data points to keep per field
        self.cleanup_interval = 100  # Cleanup every N operations

        # Performance tracking
        self.evaluation_count = 0
        self.cleanup_count = 0

    def add_data_point(
        self,
        field_path: str,
        value: float,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a data point for threshold evaluation."""
        if timestamp is None:
            timestamp = datetime.now(UTC)

        if metadata is None:
            metadata = {}

        data_point = DataPoint(timestamp=timestamp, value=value, metadata=metadata)

        if field_path not in self.data_history:
            self.data_history[field_path] = []

        self.data_history[field_path].append(data_point)

        # Cleanup old data points
        if len(self.data_history[field_path]) > self.max_history_size:
            self.data_history[field_path] = self.data_history[field_path][
                -self.max_history_size :
            ]

        # Periodic cleanup
        self.evaluation_count += 1
        if self.evaluation_count % self.cleanup_interval == 0:
            self._cleanup_old_data()

    def evaluate_threshold(
        self, condition: ThresholdCondition, current_data: dict[str, Any]
    ) -> bool:
        """Evaluate a threshold condition against current and historical data."""
        try:
            # Extract current value
            current_value = self._extract_field_value(
                current_data, condition.field_path
            )
            if current_value is None:
                return False

            # Get historical data for this field
            historical_data = self._get_relevant_data_points(
                condition.field_path, condition.time_window_minutes
            )

            if len(historical_data) < condition.min_data_points:
                return False

            # Evaluate based on threshold type
            if condition.threshold_type == ThresholdType.ABOVE:
                return current_value > condition.threshold_value

            elif condition.threshold_type == ThresholdType.BELOW:
                return current_value < condition.threshold_value

            elif condition.threshold_type == ThresholdType.EQUALS:
                return abs(current_value - condition.threshold_value) < 1e-9

            elif condition.threshold_type == ThresholdType.NOT_EQUALS:
                return abs(current_value - condition.threshold_value) >= 1e-9

            elif condition.threshold_type == ThresholdType.PERCENT_CHANGE:
                return self._evaluate_percent_change(
                    historical_data, current_value, condition
                )

            elif condition.threshold_type == ThresholdType.TREND_UP:
                return self._evaluate_trend(
                    historical_data, "up", condition.trend_sensitivity
                )

            elif condition.threshold_type == ThresholdType.TREND_DOWN:
                return self._evaluate_trend(
                    historical_data, "down", condition.trend_sensitivity
                )

            elif condition.threshold_type == ThresholdType.VOLATILITY:
                return self._evaluate_volatility(
                    historical_data, condition.volatility_threshold
                )

            elif condition.threshold_type == ThresholdType.OUTLIER:
                return self._evaluate_outlier(
                    historical_data, current_value, condition.outlier_std_dev
                )

            return False

        except Exception as e:
            self.logger.error(f"Error evaluating threshold condition: {e}")
            return False

    def _extract_field_value(
        self, data: dict[str, Any], field_path: str
    ) -> float | None:
        """Extract a numeric field value from nested data using dot notation."""
        keys = field_path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None

        # Convert to float if possible
        try:
            return float(current)
        except (ValueError, TypeError):
            return None

    def _get_relevant_data_points(
        self, field_path: str, time_window_minutes: int
    ) -> list[DataPoint]:
        """Get data points within the specified time window."""
        if field_path not in self.data_history:
            return []

        # Filter points within the time window
        cutoff_time = datetime.now(UTC) - timedelta(
            minutes=time_window_minutes
        )

        relevant_points = [
            point
            for point in self.data_history[field_path]
            if point.timestamp >= cutoff_time
        ]

        # Sort by timestamp (oldest first)
        relevant_points.sort(key=lambda x: x.timestamp)
        return relevant_points

    def _evaluate_percent_change(
        self,
        historical_data: list[DataPoint],
        current_value: float,
        condition: ThresholdCondition,
    ) -> bool:
        """Evaluate percentage change threshold."""
        if len(historical_data) < 2:
            return False

        # Get baseline value based on aggregation method
        baseline_value = self._aggregate_values(
            historical_data, condition.aggregation_method
        )

        if baseline_value == 0:
            return False

        percent_change = abs((current_value - baseline_value) / baseline_value) * 100
        return percent_change > condition.threshold_value

    def _evaluate_trend(
        self, historical_data: list[DataPoint], direction: str, sensitivity: float
    ) -> bool:
        """Evaluate trend direction threshold."""
        if len(historical_data) < 3:
            return False

        # Calculate linear regression slope
        x_values = [
            (point.timestamp - historical_data[0].timestamp).total_seconds()
            for point in historical_data
        ]
        y_values = [point.value for point in historical_data]

        slope = self._calculate_linear_regression_slope(x_values, y_values)

        if direction == "up":
            return slope > sensitivity
        else:  # down
            return slope < -sensitivity

    def _evaluate_volatility(
        self, historical_data: list[DataPoint], threshold: float
    ) -> bool:
        """Evaluate volatility threshold."""
        if len(historical_data) < 3:
            return False

        values = [point.value for point in historical_data]
        mean_value = statistics.mean(values)

        # Calculate coefficient of variation (std dev / mean)
        if mean_value == 0:
            return False

        std_dev = statistics.stdev(values)
        coefficient_of_variation = std_dev / abs(mean_value)

        return coefficient_of_variation > threshold

    def _evaluate_outlier(
        self,
        historical_data: list[DataPoint],
        current_value: float,
        std_dev_threshold: float,
    ) -> bool:
        """Evaluate outlier threshold using standard deviation."""
        if len(historical_data) < 3:
            return False

        values = [point.value for point in historical_data]
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values)

        if std_dev == 0:
            return False

        # Calculate z-score
        z_score = abs(current_value - mean_value) / std_dev
        return z_score > std_dev_threshold

    def _aggregate_values(self, data_points: list[DataPoint], method: str) -> float:
        """Aggregate values using the specified method."""
        values = [point.value for point in data_points]

        if method == "latest":
            return values[-1]
        elif method == "avg":
            return statistics.mean(values)
        elif method == "min":
            return min(values)
        elif method == "max":
            return max(values)
        elif method == "sum":
            return sum(values)
        else:
            return values[-1]  # Default to latest

    def _calculate_linear_regression_slope(
        self, x_values: list[float], y_values: list[float]
    ) -> float:
        """Calculate the slope of a linear regression line."""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0

        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values, strict=False))
        sum_x_squared = sum(x * x for x in x_values)

        # Calculate slope using least squares method
        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x_squared - sum_x * sum_x

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _cleanup_old_data(self) -> None:
        """Clean up old data points to prevent memory bloat."""
        cutoff_time = datetime.now(UTC) - timedelta(
            hours=24
        )  # Keep 24 hours of data

        for field_path in list(self.data_history.keys()):
            original_count = len(self.data_history[field_path])

            # Remove old data points
            self.data_history[field_path] = [
                point
                for point in self.data_history[field_path]
                if point.timestamp >= cutoff_time
            ]

            # Remove empty field paths
            if not self.data_history[field_path]:
                del self.data_history[field_path]

            cleaned_count = original_count - len(self.data_history.get(field_path, []))
            if cleaned_count > 0:
                self.cleanup_count += cleaned_count

        if self.cleanup_count > 0:
            self.logger.debug(f"Cleaned up {self.cleanup_count} old data points")

    def get_field_statistics(
        self, field_path: str, time_window_minutes: int = 60
    ) -> dict[str, Any]:
        """Get statistics for a specific field within a time window."""
        data_points = self._get_relevant_data_points(field_path, time_window_minutes)

        if not data_points:
            return {
                "field_path": field_path,
                "data_points": 0,
                "time_window_minutes": time_window_minutes,
                "statistics": {},
            }

        values = [point.value for point in data_points]

        stats = {
            "field_path": field_path,
            "data_points": len(data_points),
            "time_window_minutes": time_window_minutes,
            "statistics": {
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "latest": values[-1],
                "oldest": values[0],
                "range": max(values) - min(values),
            },
        }

        # Add trend information if enough data points
        if len(values) >= 3:
            x_values = [
                (point.timestamp - data_points[0].timestamp).total_seconds()
                for point in data_points
            ]
            slope = self._calculate_linear_regression_slope(x_values, values)
            stats["statistics"]["trend_slope"] = slope
            stats["statistics"]["trend_direction"] = (
                "up" if slope > 0 else "down" if slope < 0 else "stable"
            )

        return stats

    def get_engine_statistics(self) -> dict[str, Any]:
        """Get overall engine statistics."""
        total_data_points = sum(len(points) for points in self.data_history.values())

        return {
            "total_fields": len(self.data_history),
            "total_data_points": total_data_points,
            "evaluation_count": self.evaluation_count,
            "cleanup_count": self.cleanup_count,
            "max_history_size": self.max_history_size,
            "field_details": {
                field_path: {
                    "data_points": len(points),
                    "oldest_timestamp": (
                        min(point.timestamp for point in points).isoformat()
                        if points
                        else None
                    ),
                    "newest_timestamp": (
                        max(point.timestamp for point in points).isoformat()
                        if points
                        else None
                    ),
                }
                for field_path, points in self.data_history.items()
            },
        }
