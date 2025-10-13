"""
Data Quality Metrics Collector
Epic 18.2: Collect Comprehensive Data Quality Metrics

Collects and tracks data quality metrics from the validation engine.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class QualityMetricsCollector:
    """Collects data quality metrics from validation results"""
    
    def __init__(self, influxdb_client=None):
        """
        Initialize quality metrics collector
        
        Args:
            influxdb_client: Optional InfluxDB client for storing metrics
        """
        self.influxdb_client = influxdb_client
        self.start_time = time.time()
        
        # Quality metrics counters
        self.total_events = 0
        self.valid_events = 0
        self.invalid_events = 0
        
        # Error type counters
        self.error_types = defaultdict(int)
        
        # Warning type counters
        self.warning_types = defaultdict(int)
        
        # Domain-specific counters
        self.events_by_domain = defaultdict(int)
        self.invalid_by_domain = defaultdict(int)
        
        # Timing metrics
        self.total_validation_time_ms = 0.0
        self.min_validation_time_ms = float('inf')
        self.max_validation_time_ms = 0.0
        
        # Entity-specific metrics
        self.entity_metrics = defaultdict(lambda: {
            'total': 0, 'valid': 0, 'invalid': 0, 'warnings': 0
        })
        
        # Quality thresholds
        self._quality_thresholds = {
            'min_valid_rate': 95.0,
            'max_invalid_rate': 5.0,
            'max_warning_rate': 10.0
        }
    
    def record_validation_result(self, validation_result, event_data: Optional[Dict[str, Any]] = None):
        """
        Record a validation result
        
        Args:
            validation_result: ValidationResult from data validator
            event_data: Original event data (optional, for additional context)
        """
        self.total_events += 1
        
        # Track valid/invalid
        if validation_result.is_valid:
            self.valid_events += 1
        else:
            self.invalid_events += 1
            
            # Count error types
            for error in validation_result.errors:
                error_type = self._classify_error(error)
                self.error_types[error_type] += 1
        
        # Track warnings
        for warning in validation_result.warnings:
            warning_type = self._classify_warning(warning)
            self.warning_types[warning_type] += 1
        
        # Track by domain
        if validation_result.domain:
            self.events_by_domain[validation_result.domain] += 1
            if not validation_result.is_valid:
                self.invalid_by_domain[validation_result.domain] += 1
        
        # Track validation timing
        if validation_result.validation_time_ms:
            self.total_validation_time_ms += validation_result.validation_time_ms
            self.min_validation_time_ms = min(self.min_validation_time_ms, validation_result.validation_time_ms)
            self.max_validation_time_ms = max(self.max_validation_time_ms, validation_result.validation_time_ms)
    
    def _classify_error(self, error: str) -> str:
        """Classify error type from error message"""
        error_lower = error.lower()
        
        if 'missing' in error_lower:
            return 'missing_field'
        elif 'invalid' in error_lower and 'format' in error_lower:
            return 'invalid_format'
        elif 'invalid' in error_lower and 'type' in error_lower:
            return 'invalid_type'
        elif 'range' in error_lower or 'out of' in error_lower:
            return 'out_of_range'
        elif 'timestamp' in error_lower:
            return 'timestamp_error'
        elif 'state' in error_lower:
            return 'invalid_state'
        else:
            return 'other_error'
    
    def _classify_warning(self, warning: str) -> str:
        """Classify warning type from warning message"""
        warning_lower = warning.lower()
        
        if 'missing' in warning_lower:
            return 'missing_optional_field'
        elif 'unknown' in warning_lower and 'domain' in warning_lower:
            return 'unknown_domain'
        elif 'unusual' in warning_lower or 'unexpected' in warning_lower:
            return 'unusual_value'
        elif 'range' in warning_lower:
            return 'out_of_typical_range'
        else:
            return 'other_warning'
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current quality metrics
        
        Returns:
            Dictionary of quality metrics
        """
        uptime = time.time() - self.start_time
        
        # Calculate rates
        valid_rate = (self.valid_events / self.total_events * 100) if self.total_events > 0 else 0.0
        invalid_rate = (self.invalid_events / self.total_events * 100) if self.total_events > 0 else 0.0
        
        # Calculate average validation time
        avg_validation_time = (
            self.total_validation_time_ms / self.total_events 
            if self.total_events > 0 else 0.0
        )
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'uptime_seconds': uptime,
            'totals': {
                'total_events': self.total_events,
                'valid_events': self.valid_events,
                'invalid_events': self.invalid_events,
                'events_with_warnings': sum(self.warning_types.values())
            },
            'rates': {
                'valid_rate_percent': round(valid_rate, 2),
                'invalid_rate_percent': round(invalid_rate, 2),
                'events_per_second': round(self.total_events / uptime, 2) if uptime > 0 else 0.0
            },
            'error_types': dict(self.error_types),
            'warning_types': dict(self.warning_types),
            'by_domain': {
                'total': dict(self.events_by_domain),
                'invalid': dict(self.invalid_by_domain)
            },
            'performance': {
                'avg_validation_time_ms': round(avg_validation_time, 3),
                'min_validation_time_ms': round(self.min_validation_time_ms, 3) if self.min_validation_time_ms != float('inf') else 0.0,
                'max_validation_time_ms': round(self.max_validation_time_ms, 3)
            }
        }
    
    async def write_to_influxdb(self, measurement: str = "data_quality_metrics"):
        """
        Write quality metrics to InfluxDB
        
        Args:
            measurement: InfluxDB measurement name
        """
        if not self.influxdb_client:
            logger.debug("No InfluxDB client configured for quality metrics")
            return
        
        try:
            from influxdb_client import Point
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
            
            # Write totals
            point = Point(measurement) \
                .tag("service", "enrichment-pipeline") \
                .field("total_events", self.total_events) \
                .field("valid_events", self.valid_events) \
                .field("invalid_events", self.invalid_events) \
                .field("events_with_warnings", sum(self.warning_types.values()))
            
            write_api.write(bucket="home_assistant_events", record=point)
            
            # Write rates
            metrics = self.get_metrics()
            point = Point(measurement) \
                .tag("service", "enrichment-pipeline") \
                .tag("metric_type", "rates") \
                .field("valid_rate_percent", metrics['rates']['valid_rate_percent']) \
                .field("invalid_rate_percent", metrics['rates']['invalid_rate_percent']) \
                .field("events_per_second", metrics['rates']['events_per_second'])
            
            write_api.write(bucket="home_assistant_events", record=point)
            
            logger.debug("Wrote quality metrics to InfluxDB")
            
        except Exception as e:
            logger.error(f"Error writing quality metrics to InfluxDB: {e}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status based on current metrics
        
        Returns:
            Dictionary with health status information
        """
        metrics = self.get_metrics()
        valid_rate = metrics['rates']['valid_rate_percent']
        invalid_rate = metrics['rates']['invalid_rate_percent']
        
        # Determine health status
        if valid_rate >= self._quality_thresholds['min_valid_rate']:
            status = 'healthy'
        elif valid_rate >= 90.0:
            status = 'degraded'
        else:
            status = 'unhealthy'
        
        return {
            'status': status,
            'valid_rate': valid_rate,
            'invalid_rate': invalid_rate,
            'total_events': self.total_events,
            'thresholds': self._quality_thresholds
        }
    
    def get_quality_report(self) -> Dict[str, Any]:
        """
        Get comprehensive quality report
        
        Returns:
            Dictionary with detailed quality report
        """
        metrics = self.get_metrics()
        health = self.get_health_status()
        
        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'health': health,
            'metrics': metrics,
            'summary': {
                'total_events': self.total_events,
                'valid_events': self.valid_events,
                'invalid_events': self.invalid_events,
                'quality_score': round(health['valid_rate'], 2)
            }
        }
    
    def get_entity_quality(self, entity_id: str) -> Dict[str, Any]:
        """
        Get quality metrics for a specific entity
        
        Args:
            entity_id: Entity ID to get metrics for
            
        Returns:
            Dictionary with entity-specific quality metrics
        """
        entity_data = self.entity_metrics.get(entity_id, {
            'total': 0, 'valid': 0, 'invalid': 0, 'warnings': 0
        })
        
        total = entity_data['total']
        valid_rate = (entity_data['valid'] / total * 100) if total > 0 else 0.0
        
        return {
            'entity_id': entity_id,
            'total_events': total,
            'valid_events': entity_data['valid'],
            'invalid_events': entity_data['invalid'],
            'warnings': entity_data['warnings'],
            'valid_rate': round(valid_rate, 2)
        }
    
    @property
    def quality_thresholds(self) -> Dict[str, float]:
        """Get current quality thresholds"""
        return self._quality_thresholds.copy()
    
    def set_quality_thresholds(self, thresholds: Dict[str, float]):
        """
        Set quality thresholds
        
        Args:
            thresholds: Dictionary of threshold values
        """
        self._quality_thresholds.update(thresholds)
        logger.info(f"Updated quality thresholds: {self._quality_thresholds}")
    
    def reset_metrics(self):
        """Reset all metrics counters"""
        self.total_events = 0
        self.valid_events = 0
        self.invalid_events = 0
        self.error_types.clear()
        self.warning_types.clear()
        self.events_by_domain.clear()
        self.invalid_by_domain.clear()
        self.total_validation_time_ms = 0.0
        self.min_validation_time_ms = float('inf')
        self.max_validation_time_ms = 0.0


# Global quality metrics collector
_quality_metrics = None


def get_quality_metrics_collector(influxdb_client=None) -> QualityMetricsCollector:
    """Get or create global quality metrics collector"""
    global _quality_metrics
    if _quality_metrics is None:
        _quality_metrics = QualityMetricsCollector(influxdb_client)
    return _quality_metrics
