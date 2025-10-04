"""
Data Quality Metrics Collection and Monitoring
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import asyncio
import json

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Data quality metrics snapshot"""
    timestamp: datetime
    total_events: int = 0
    valid_events: int = 0
    invalid_events: int = 0
    warnings: int = 0
    errors: int = 0
    quality_score: float = 0.0
    capture_rate: float = 0.0
    enrichment_coverage: float = 0.0
    validation_success_rate: float = 0.0
    processing_latency_avg: float = 0.0
    error_rate: float = 0.0


@dataclass
class EntityQualityMetrics:
    """Entity-specific quality metrics"""
    entity_id: str
    total_events: int = 0
    valid_events: int = 0
    invalid_events: int = 0
    quality_score: float = 0.0
    last_updated: datetime = None


class QualityMetricsTracker:
    """Tracks and aggregates data quality metrics over time"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=window_size)
        self.entity_metrics: Dict[str, EntityQualityMetrics] = {}
        self.validation_errors: Dict[str, int] = defaultdict(int)
        self.processing_times: deque = deque(maxlen=window_size)
        
        # Current metrics
        self.current_metrics = QualityMetrics(timestamp=datetime.now(timezone.utc))
        
        # Configuration
        self.quality_thresholds = {
            "min_quality_score": 95.0,
            "max_error_rate": 1.0,
            "min_capture_rate": 99.0,
            "min_enrichment_coverage": 90.0,
            "max_processing_latency": 500.0  # milliseconds
        }
        
        # Alert tracking
        self.active_alerts: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)
    
    def record_validation_result(self, 
                                event: Dict[str, Any], 
                                validation_results: List[Any],
                                processing_time_ms: float = 0.0):
        """
        Record validation results for an event
        
        Args:
            event: The event data
            validation_results: List of validation results
            processing_time_ms: Processing time in milliseconds
        """
        try:
            # Update current metrics
            self.current_metrics.total_events += 1
            self.current_metrics.timestamp = datetime.now(timezone.utc)
            
            # Process validation results
            has_errors = any(hasattr(r, 'level') and r.level.value == 'error' for r in validation_results)
            has_warnings = any(hasattr(r, 'level') and r.level.value == 'warning' for r in validation_results)
            
            if has_errors:
                self.current_metrics.invalid_events += 1
                self.current_metrics.errors += len([r for r in validation_results 
                                                  if hasattr(r, 'level') and r.level.value == 'error'])
            else:
                self.current_metrics.valid_events += 1
            
            if has_warnings:
                self.current_metrics.warnings += len([r for r in validation_results 
                                                    if hasattr(r, 'level') and r.level.value == 'warning'])
            
            # Track validation errors by type
            for result in validation_results:
                if hasattr(result, 'level') and result.level.value == 'error':
                    error_key = f"{result.field}:{result.message}" if hasattr(result, 'field') else result.message
                    self.validation_errors[error_key] += 1
            
            # Record processing time
            if processing_time_ms > 0:
                self.processing_times.append(processing_time_ms)
                self.current_metrics.processing_latency_avg = sum(self.processing_times) / len(self.processing_times)
            
            # Update entity-specific metrics
            entity_id = self._extract_entity_id(event)
            if entity_id:
                self._update_entity_metrics(entity_id, not has_errors)
            
            # Check for weather enrichment
            if "weather" in event:
                self.current_metrics.enrichment_coverage = (
                    (self.current_metrics.enrichment_coverage * (self.current_metrics.total_events - 1) + 100) /
                    self.current_metrics.total_events
                )
            else:
                self.current_metrics.enrichment_coverage = (
                    (self.current_metrics.enrichment_coverage * (self.current_metrics.total_events - 1)) /
                    self.current_metrics.total_events
                )
            
            # Calculate derived metrics
            self._calculate_derived_metrics()
            
            # Check for quality alerts
            self._check_quality_alerts()
            
        except Exception as e:
            logger.error(f"Error recording validation result: {e}")
    
    def _extract_entity_id(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract entity ID from event"""
        try:
            # Try direct entity_id first
            if "entity_id" in event:
                return event["entity_id"]
            
            # Try from new_state
            if event.get("event_type") == "state_changed" and "new_state" in event:
                new_state = event["new_state"]
                if isinstance(new_state, dict) and "entity_id" in new_state:
                    return new_state["entity_id"]
            
            return None
        except Exception:
            return None
    
    def _update_entity_metrics(self, entity_id: str, is_valid: bool):
        """Update entity-specific quality metrics"""
        if entity_id not in self.entity_metrics:
            self.entity_metrics[entity_id] = EntityQualityMetrics(
                entity_id=entity_id,
                last_updated=datetime.now(timezone.utc)
            )
        
        entity_metrics = self.entity_metrics[entity_id]
        entity_metrics.total_events += 1
        entity_metrics.last_updated = datetime.now(timezone.utc)
        
        if is_valid:
            entity_metrics.valid_events += 1
        else:
            entity_metrics.invalid_events += 1
        
        # Calculate entity quality score
        if entity_metrics.total_events > 0:
            entity_metrics.quality_score = (entity_metrics.valid_events / entity_metrics.total_events) * 100
    
    def _calculate_derived_metrics(self):
        """Calculate derived quality metrics"""
        metrics = self.current_metrics
        
        if metrics.total_events > 0:
            # Quality score (weighted by errors and warnings)
            valid_ratio = metrics.valid_events / metrics.total_events
            error_penalty = (metrics.errors / metrics.total_events) * 0.5
            warning_penalty = (metrics.warnings / metrics.total_events) * 0.1
            metrics.quality_score = max(0.0, (valid_ratio - error_penalty - warning_penalty) * 100)
            
            # Validation success rate
            metrics.validation_success_rate = (metrics.valid_events / metrics.total_events) * 100
            
            # Error rate
            metrics.error_rate = (metrics.errors / metrics.total_events) * 100
            
            # Capture rate (assume 100% for now, could be calculated based on expected vs actual events)
            metrics.capture_rate = 100.0
    
    def _check_quality_alerts(self):
        """Check for quality threshold violations and generate alerts"""
        metrics = self.current_metrics
        current_time = datetime.now(timezone.utc)
        
        # Check quality score threshold
        if metrics.quality_score < self.quality_thresholds["min_quality_score"]:
            alert_key = "low_quality_score"
            if self._should_trigger_alert(alert_key, current_time):
                self._trigger_alert(alert_key, f"Quality score below threshold: {metrics.quality_score:.2f}%")
        
        # Check error rate threshold
        if metrics.error_rate > self.quality_thresholds["max_error_rate"]:
            alert_key = "high_error_rate"
            if self._should_trigger_alert(alert_key, current_time):
                self._trigger_alert(alert_key, f"Error rate above threshold: {metrics.error_rate:.2f}%")
        
        # Check capture rate threshold
        if metrics.capture_rate < self.quality_thresholds["min_capture_rate"]:
            alert_key = "low_capture_rate"
            if self._should_trigger_alert(alert_key, current_time):
                self._trigger_alert(alert_key, f"Capture rate below threshold: {metrics.capture_rate:.2f}%")
        
        # Check enrichment coverage threshold
        if metrics.enrichment_coverage < self.quality_thresholds["min_enrichment_coverage"]:
            alert_key = "low_enrichment_coverage"
            if self._should_trigger_alert(alert_key, current_time):
                self._trigger_alert(alert_key, f"Enrichment coverage below threshold: {metrics.enrichment_coverage:.2f}%")
        
        # Check processing latency threshold
        if metrics.processing_latency_avg > self.quality_thresholds["max_processing_latency"]:
            alert_key = "high_processing_latency"
            if self._should_trigger_alert(alert_key, current_time):
                self._trigger_alert(alert_key, f"Processing latency above threshold: {metrics.processing_latency_avg:.2f}ms")
    
    def _should_trigger_alert(self, alert_key: str, current_time: datetime) -> bool:
        """Check if alert should be triggered (respecting cooldown)"""
        if alert_key not in self.active_alerts:
            return True
        
        last_alert_time = self.active_alerts[alert_key]
        return (current_time - last_alert_time) > self.alert_cooldown
    
    def _trigger_alert(self, alert_key: str, message: str):
        """Trigger a quality alert"""
        self.active_alerts[alert_key] = datetime.now(timezone.utc)
        logger.warning(f"QUALITY ALERT [{alert_key}]: {message}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """
        Get current quality metrics
        
        Returns:
            Dictionary with current quality metrics
        """
        return asdict(self.current_metrics)
    
    def get_quality_report(self) -> Dict[str, Any]:
        """
        Get comprehensive quality report
        
        Returns:
            Dictionary with comprehensive quality report
        """
        # Add current metrics to history
        self.metrics_history.append(self.current_metrics)
        
        # Calculate trend metrics
        trend_metrics = self._calculate_trend_metrics()
        
        # Get top problematic entities
        problematic_entities = self._get_problematic_entities()
        
        # Get most common validation errors
        common_errors = self._get_common_validation_errors()
        
        return {
            "current_metrics": asdict(self.current_metrics),
            "trend_metrics": trend_metrics,
            "entity_quality": {
                entity_id: asdict(metrics) for entity_id, metrics in self.entity_metrics.items()
            },
            "problematic_entities": problematic_entities,
            "common_validation_errors": common_errors,
            "active_alerts": {
                alert_key: alert_time.isoformat() 
                for alert_key, alert_time in self.active_alerts.items()
            },
            "quality_thresholds": self.quality_thresholds,
            "report_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_trend_metrics(self) -> Dict[str, Any]:
        """Calculate trend metrics from history"""
        if len(self.metrics_history) < 2:
            return {"message": "Insufficient data for trend analysis"}
        
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 snapshots
        
        # Calculate averages
        avg_quality_score = sum(m.quality_score for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        avg_processing_latency = sum(m.processing_latency_avg for m in recent_metrics) / len(recent_metrics)
        
        # Calculate trends (simple linear trend)
        if len(recent_metrics) >= 5:
            quality_trend = self._calculate_linear_trend([m.quality_score for m in recent_metrics])
            error_trend = self._calculate_linear_trend([m.error_rate for m in recent_metrics])
            latency_trend = self._calculate_linear_trend([m.processing_latency_avg for m in recent_metrics])
        else:
            quality_trend = error_trend = latency_trend = 0.0
        
        return {
            "avg_quality_score": round(avg_quality_score, 2),
            "avg_error_rate": round(avg_error_rate, 2),
            "avg_processing_latency": round(avg_processing_latency, 2),
            "quality_trend": round(quality_trend, 2),
            "error_trend": round(error_trend, 2),
            "latency_trend": round(latency_trend, 2),
            "trend_period": f"{len(recent_metrics)} snapshots"
        }
    
    def _calculate_linear_trend(self, values: List[float]) -> float:
        """Calculate simple linear trend (slope)"""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _get_problematic_entities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get entities with the lowest quality scores"""
        if not self.entity_metrics:
            return []
        
        # Sort entities by quality score (ascending)
        sorted_entities = sorted(
            self.entity_metrics.items(),
            key=lambda x: x[1].quality_score
        )
        
        problematic = []
        for entity_id, metrics in sorted_entities[:limit]:
            if metrics.quality_score < 95.0:  # Only include entities with quality issues
                problematic.append({
                    "entity_id": entity_id,
                    "quality_score": metrics.quality_score,
                    "total_events": metrics.total_events,
                    "invalid_events": metrics.invalid_events,
                    "last_updated": metrics.last_updated.isoformat() if metrics.last_updated else None
                })
        
        return problematic
    
    def _get_common_validation_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common validation errors"""
        if not self.validation_errors:
            return []
        
        # Sort errors by frequency (descending)
        sorted_errors = sorted(
            self.validation_errors.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {
                "error": error,
                "count": count,
                "percentage": round((count / self.current_metrics.total_events) * 100, 2)
            }
            for error, count in sorted_errors[:limit]
        ]
    
    def get_entity_quality(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get quality metrics for a specific entity
        
        Args:
            entity_id: The entity ID to get metrics for
            
        Returns:
            Entity quality metrics or None if not found
        """
        if entity_id in self.entity_metrics:
            return asdict(self.entity_metrics[entity_id])
        return None
    
    def reset_metrics(self):
        """Reset all quality metrics"""
        self.metrics_history.clear()
        self.entity_metrics.clear()
        self.validation_errors.clear()
        self.processing_times.clear()
        self.active_alerts.clear()
        self.current_metrics = QualityMetrics(timestamp=datetime.now(timezone.utc))
        logger.info("Quality metrics reset")
    
    def set_quality_thresholds(self, thresholds: Dict[str, float]):
        """
        Update quality thresholds
        
        Args:
            thresholds: Dictionary of threshold values
        """
        self.quality_thresholds.update(thresholds)
        logger.info(f"Quality thresholds updated: {thresholds}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get quality system health status
        
        Returns:
            Dictionary with health status
        """
        metrics = self.current_metrics
        
        # Determine overall health status
        health_issues = []
        
        if metrics.quality_score < self.quality_thresholds["min_quality_score"]:
            health_issues.append("low_quality_score")
        
        if metrics.error_rate > self.quality_thresholds["max_error_rate"]:
            health_issues.append("high_error_rate")
        
        if metrics.capture_rate < self.quality_thresholds["min_capture_rate"]:
            health_issues.append("low_capture_rate")
        
        if metrics.enrichment_coverage < self.quality_thresholds["min_enrichment_coverage"]:
            health_issues.append("low_enrichment_coverage")
        
        if metrics.processing_latency_avg > self.quality_thresholds["max_processing_latency"]:
            health_issues.append("high_processing_latency")
        
        # Determine status
        if not health_issues:
            status = "healthy"
        elif len(health_issues) <= 2:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_issues": health_issues,
            "active_alerts": len(self.active_alerts),
            "total_entities": len(self.entity_metrics),
            "metrics_age_seconds": (datetime.now(timezone.utc) - metrics.timestamp).total_seconds(),
            "last_updated": metrics.timestamp.isoformat()
        }
