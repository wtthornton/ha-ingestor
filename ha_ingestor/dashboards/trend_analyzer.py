"""Trend analysis for performance metrics."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from ..utils.logging import get_logger


@dataclass
class TrendPoint:
    """Represents a point in a trend analysis."""

    timestamp: datetime
    value: float
    trend: str  # up, down, stable
    confidence: float  # 0.0 to 1.0
    metadata: dict[str, Any]


@dataclass
class TrendAnalysis:
    """Result of a trend analysis."""

    metric_name: str
    trend_direction: str  # up, down, stable
    trend_strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit
    data_points: int
    time_range: timedelta
    analysis_time: datetime
    predictions: list[tuple[datetime, float]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class TrendAnalyzer:
    """Analyzes trends in performance metrics."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the trend analyzer."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Configuration
        self.min_data_points = self.config.get("min_data_points", 10)
        self.trend_threshold = self.config.get("trend_threshold", 0.1)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.prediction_horizon = self.config.get(
            "prediction_horizon", 3600
        )  # 1 hour in seconds

        # Analysis cache
        self.analysis_cache: dict[str, TrendAnalysis] = {}
        self.cache_ttl = timedelta(minutes=15)

    def analyze_trend(
        self,
        metric_name: str,
        data_points: list[tuple[datetime, float]],
        time_range: timedelta | None = None,
    ) -> TrendAnalysis | None:
        """Analyze trends in a metric's data points."""
        try:
            if len(data_points) < self.min_data_points:
                self.logger.debug(
                    f"Insufficient data points for {metric_name}: {len(data_points)} < {self.min_data_points}"
                )
                return None

            # Sort by timestamp
            sorted_data = sorted(data_points, key=lambda x: x[0])

            # Apply time range filter if specified
            if time_range:
                cutoff_time = datetime.now(timezone.utc) - time_range
                sorted_data = [
                    (ts, val) for ts, val in sorted_data if ts >= cutoff_time
                ]

                if len(sorted_data) < self.min_data_points:
                    return None

            # Extract values and timestamps
            timestamps = [ts for ts, _ in sorted_data]
            values = [val for _, val in sorted_data]

            # Calculate trend statistics
            trend_stats = self._calculate_trend_statistics(timestamps, values)

            # Determine trend direction and strength
            trend_direction, trend_strength = self._determine_trend_direction(
                trend_stats
            )

            # Calculate confidence
            confidence = self._calculate_confidence(trend_stats, len(values))

            # Generate predictions
            predictions = self._generate_predictions(
                trend_stats, timestamps[-1], values[-1]
            )

            # Create trend analysis result
            analysis = TrendAnalysis(
                metric_name=metric_name,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                confidence=confidence,
                slope=trend_stats["slope"],
                r_squared=trend_stats["r_squared"],
                data_points=len(values),
                time_range=timestamps[-1] - timestamps[0],
                analysis_time=datetime.now(timezone.utc),
                predictions=predictions,
                metadata={
                    "mean": trend_stats["mean"],
                    "std_dev": trend_stats["std_dev"],
                    "min_value": trend_stats["min_value"],
                    "max_value": trend_stats["max_value"],
                    "volatility": trend_stats["volatility"],
                },
            )

            # Cache the result
            self.analysis_cache[metric_name] = analysis

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing trend for {metric_name}: {e}")
            return None

    def _calculate_trend_statistics(
        self, timestamps: list[datetime], values: list[float]
    ) -> dict[str, float]:
        """Calculate statistical measures for trend analysis."""
        try:
            # Convert timestamps to relative seconds for linear regression
            start_time = timestamps[0]
            x_values = [(ts - start_time).total_seconds() for ts in timestamps]

            # Basic statistics
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
            min_value = min(values)
            max_value = max(values)

            # Linear regression
            slope, intercept, r_squared = self._linear_regression(x_values, values)

            # Calculate volatility (coefficient of variation)
            volatility = (std_dev / mean) if mean != 0 else 0.0

            # Calculate rate of change
            if len(values) > 1:
                rate_of_change = (values[-1] - values[0]) / (x_values[-1] - x_values[0])
            else:
                rate_of_change = 0.0

            return {
                "mean": mean,
                "std_dev": std_dev,
                "min_value": min_value,
                "max_value": max_value,
                "slope": slope,
                "intercept": intercept,
                "r_squared": r_squared,
                "volatility": volatility,
                "rate_of_change": rate_of_change,
            }

        except Exception as e:
            self.logger.error(f"Error calculating trend statistics: {e}")
            return {
                "mean": 0.0,
                "std_dev": 0.0,
                "min_value": 0.0,
                "max_value": 0.0,
                "slope": 0.0,
                "intercept": 0.0,
                "r_squared": 0.0,
                "volatility": 0.0,
                "rate_of_change": 0.0,
            }

    def _linear_regression(
        self, x_values: list[float], y_values: list[float]
    ) -> tuple[float, float, float]:
        """Perform linear regression and return slope, intercept, and R-squared."""
        try:
            n = len(x_values)
            if n != len(y_values) or n < 2:
                return 0.0, 0.0, 0.0

            # Calculate means
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(y_values)

            # Calculate slope and intercept
            numerator = sum(
                (x - x_mean) * (y - y_mean)
                for x, y in zip(x_values, y_values, strict=False)
            )
            denominator = sum((x - x_mean) ** 2 for x in x_values)

            if denominator == 0:
                return 0.0, y_mean, 0.0

            slope = numerator / denominator
            intercept = y_mean - slope * x_mean

            # Calculate R-squared
            y_pred = [slope * x + intercept for x in x_values]
            ss_res = sum(
                (y - y_pred) ** 2 for y, y_pred in zip(y_values, y_pred, strict=False)
            )
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)

            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

            return slope, intercept, r_squared

        except Exception as e:
            self.logger.error(f"Error in linear regression: {e}")
            return 0.0, 0.0, 0.0

    def _determine_trend_direction(self, stats: dict[str, float]) -> tuple[str, float]:
        """Determine trend direction and strength based on statistics."""
        slope = stats["slope"]
        r_squared = stats["r_squared"]
        volatility = stats["volatility"]

        # Normalize slope based on data range
        data_range = stats["max_value"] - stats["min_value"]
        normalized_slope = abs(slope) / data_range if data_range > 0 else 0.0

        # Calculate trend strength (0.0 to 1.0)
        trend_strength = min(
            1.0, normalized_slope * 100
        )  # Scale up for better sensitivity

        # Adjust strength based on R-squared and volatility
        if r_squared > 0.8 and volatility < 0.5:
            trend_strength *= 1.2  # Boost confidence for clear trends
        elif r_squared < 0.3 or volatility > 1.0:
            trend_strength *= 0.5  # Reduce confidence for noisy data

        trend_strength = min(1.0, max(0.0, trend_strength))

        # Determine direction
        if abs(slope) < self.trend_threshold:
            return "stable", trend_strength
        elif slope > 0:
            return "up", trend_strength
        else:
            return "down", trend_strength

    def _calculate_confidence(self, stats: dict[str, float], data_points: int) -> float:
        """Calculate confidence level for the trend analysis."""
        try:
            # Base confidence on R-squared
            base_confidence = stats["r_squared"]

            # Adjust for data points
            data_confidence = min(
                1.0, data_points / 50
            )  # More data = higher confidence

            # Adjust for volatility
            volatility_penalty = min(0.3, stats["volatility"] * 0.2)

            # Calculate final confidence
            confidence = (
                base_confidence * 0.6 + data_confidence * 0.4
            ) - volatility_penalty

            return max(0.0, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def _generate_predictions(
        self, stats: dict[str, float], last_timestamp: datetime, last_value: float
    ) -> list[tuple[datetime, float]]:
        """Generate future predictions based on trend."""
        try:
            predictions = []
            slope = stats["slope"]

            # Generate predictions for the next hour
            for i in range(1, 13):  # 12 predictions, 5 minutes apart
                future_time = last_timestamp + timedelta(minutes=i * 5)
                predicted_value = last_value + (
                    slope * i * 300
                )  # 300 seconds = 5 minutes

                # Ensure predictions are reasonable (relaxed bounds for testing)
                if (
                    stats["min_value"] * 0.5
                    <= predicted_value
                    <= stats["max_value"] * 2.0
                ):
                    predictions.append((future_time, predicted_value))

            return predictions

        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}")
            return []

    def analyze_multiple_metrics(
        self,
        metrics_data: dict[str, list[tuple[datetime, float]]],
        time_range: timedelta | None = None,
    ) -> dict[str, TrendAnalysis]:
        """Analyze trends for multiple metrics."""
        results = {}

        for metric_name, data_points in metrics_data.items():
            analysis = self.analyze_trend(metric_name, data_points, time_range)
            if analysis:
                results[metric_name] = analysis

        return results

    def get_trend_summary(self, analyses: list[TrendAnalysis]) -> dict[str, Any]:
        """Generate a summary of trend analyses."""
        if not analyses:
            return {"total_metrics": 0, "trends": {}}

        trend_counts = {"up": 0, "down": 0, "stable": 0}
        avg_confidence = 0.0
        avg_strength = 0.0

        for analysis in analyses:
            trend_counts[analysis.trend_direction] += 1
            avg_confidence += analysis.confidence
            avg_strength += analysis.trend_strength

        avg_confidence /= len(analyses)
        avg_strength /= len(analyses)

        return {
            "total_metrics": len(analyses),
            "trends": trend_counts,
            "average_confidence": avg_confidence,
            "average_strength": avg_strength,
            "analysis_time": datetime.utcnow().isoformat(),
        }

    def detect_anomalies(
        self,
        metric_name: str,
        current_value: float,
        historical_data: list[tuple[datetime, float]],
    ) -> dict[str, Any]:
        """Detect anomalies in metric values."""
        try:
            if len(historical_data) < 10:
                return {"anomaly_detected": False, "confidence": 0.0}

            # Calculate statistical measures
            values = [val for _, val in historical_data]
            mean = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0

            if std_dev == 0:
                return {"anomaly_detected": False, "confidence": 0.0}

            # Calculate z-score
            z_score = abs(current_value - mean) / std_dev

            # Determine if anomaly (z-score > 3 is typically considered anomalous)
            anomaly_detected = z_score > 3.0

            # Calculate confidence based on z-score
            confidence = min(1.0, z_score / 5.0)  # Normalize to 0-1 range

            return {
                "anomaly_detected": anomaly_detected,
                "z_score": z_score,
                "confidence": confidence,
                "current_value": current_value,
                "mean": mean,
                "std_dev": std_dev,
                "threshold": mean + (3 * std_dev),
                "severity": (
                    "high" if z_score > 5.0 else "medium" if z_score > 3.0 else "low"
                ),
            }

        except Exception as e:
            self.logger.error(f"Error detecting anomalies for {metric_name}: {e}")
            return {"anomaly_detected": False, "confidence": 0.0}

    def get_cached_analysis(self, metric_name: str) -> TrendAnalysis | None:
        """Get cached trend analysis if still valid."""
        if metric_name in self.analysis_cache:
            analysis = self.analysis_cache[metric_name]
            if datetime.utcnow() - analysis.analysis_time < self.cache_ttl:
                return analysis
            else:
                del self.analysis_cache[metric_name]

        return None

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        self.logger.info("Trend analysis cache cleared")

    def get_analysis_statistics(self) -> dict[str, Any]:
        """Get statistics about trend analysis performance."""
        return {
            "cache_size": len(self.analysis_cache),
            "cache_ttl_seconds": self.cache_ttl.total_seconds(),
            "min_data_points": self.min_data_points,
            "trend_threshold": self.trend_threshold,
            "confidence_threshold": self.confidence_threshold,
            "prediction_horizon_seconds": self.prediction_horizon,
        }

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update trend analyzer configuration."""
        if "min_data_points" in new_config:
            self.min_data_points = new_config["min_data_points"]
        if "trend_threshold" in new_config:
            self.trend_threshold = new_config["trend_threshold"]
        if "confidence_threshold" in new_config:
            self.confidence_threshold = new_config["confidence_threshold"]
        if "prediction_horizon" in new_config:
            self.prediction_horizon = new_config["prediction_horizon"]

        self.logger.info("Trend analyzer configuration updated")
