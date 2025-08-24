"""
Common Patterns Demo for ha-ingestor
AI ASSISTANT CONTEXT: This file demonstrates common implementation patterns used throughout the project.
Use these examples as templates when implementing new features.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ha_ingestor.filters.base import BaseFilter
from ha_ingestor.metrics.registry import MetricsRegistry

# Import project models and utilities
from ha_ingestor.models.events import BaseEvent
from ha_ingestor.models.influxdb_point import InfluxDBPoint
from ha_ingestor.transformers.base import BaseTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PATTERN 1: Async Event Processing Pipeline
# ============================================================================


class EventProcessor:
    """
    AI ASSISTANT CONTEXT: Demonstrates the async event processing pipeline pattern.
    This is the core pattern used throughout the project for handling events.
    """

    def __init__(self, filters: list[BaseFilter], transformers: list[BaseTransformer]):
        self.filters = filters
        self.transformers = transformers
        self.processed_count = 0
        self.filtered_count = 0

    async def process_event(self, event: BaseEvent) -> InfluxDBPoint | None:
        """Process a single event through the pipeline."""
        try:
            # Apply filters
            if not await self._apply_filters(event):
                self.filtered_count += 1
                return None

            # Apply transformations
            point = await self._apply_transformations(event)

            self.processed_count += 1
            return point

        except Exception as e:
            logger.error(f"Error processing event {event.entity_id}: {e}")
            return None

    async def _apply_filters(self, event: BaseEvent) -> bool:
        """Apply all filters to the event."""
        for filter_instance in self.filters:
            if not await filter_instance.filter(event):
                return False
        return True

    async def _apply_transformations(self, event: BaseEvent) -> InfluxDBPoint:
        """Apply all transformations to the event."""
        current_data = event

        for transformer in self.transformers:
            current_data = await transformer.transform(current_data)

        return current_data


# ============================================================================
# PATTERN 2: Configurable Filter Implementation
# ============================================================================


class ConfigurableFilter(BaseFilter):
    """
    AI ASSISTANT CONTEXT: Demonstrates how to implement configurable filters.
    Use this pattern when creating new filter types.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.enabled = config.get("enabled", True)
        self.include_values = config.get("include_values", [])
        self.exclude_values = config.get("exclude_values", [])
        self.case_sensitive = config.get("case_sensitive", True)

    async def filter(self, event: BaseEvent) -> bool:
        """Filter logic implementation."""
        if not self.enabled:
            return True

        # Get the value to filter on
        value = getattr(event, "value", None)
        if value is None:
            return False

        # Convert to string for comparison if needed
        if not isinstance(value, str):
            value = str(value)

        # Apply case sensitivity
        if not self.case_sensitive:
            value = value.lower()
            include_values = [v.lower() for v in self.include_values]
            exclude_values = [v.lower() for v in self.exclude_values]
        else:
            include_values = self.include_values
            exclude_values = self.exclude_values

        # Check exclusions first
        if exclude_values and value in exclude_values:
            return False

        # Check inclusions
        if include_values and value not in include_values:
            return False

        return True


# ============================================================================
# PATTERN 3: Data Transformation Pipeline
# ============================================================================


class DataTransformationPipeline:
    """
    AI ASSISTANT CONTEXT: Demonstrates the data transformation pipeline pattern.
    This pattern is used for converting events to InfluxDB points.
    """

    def __init__(self, transformations: list[dict[str, Any]]):
        self.transformations = transformations

    async def transform_event(self, event: BaseEvent) -> InfluxDBPoint:
        """Transform an event through the pipeline."""
        # Start with base event data
        measurement = self._get_measurement_name(event)
        tags = self._extract_tags(event)
        fields = self._extract_fields(event)
        timestamp = event.timestamp or datetime.utcnow()

        # Apply custom transformations
        for transform_config in self.transformations:
            if transform_config.get("enabled", True):
                tags, fields = await self._apply_transformation(
                    transform_config, event, tags, fields
                )

        return InfluxDBPoint(
            measurement=measurement, tags=tags, fields=fields, timestamp=timestamp
        )

    def _get_measurement_name(self, event: BaseEvent) -> str:
        """Determine the measurement name for the event."""
        domain = getattr(event, "domain", "unknown")
        return f"{domain}_data"

    def _extract_tags(self, event: BaseEvent) -> dict[str, str]:
        """Extract tags from the event."""
        tags = {
            "entity_id": event.entity_id,
            "domain": getattr(event, "domain", "unknown"),
        }

        # Add device class if available
        if hasattr(event, "device_class") and event.device_class:
            tags["device_class"] = event.device_class

        # Add friendly name if available
        if hasattr(event, "friendly_name") and event.friendly_name:
            tags["friendly_name"] = event.friendly_name

        return tags

    def _extract_fields(self, event: BaseEvent) -> dict[str, Any]:
        """Extract fields from the event."""
        fields = {}

        # Add primary value
        if hasattr(event, "value"):
            fields["value"] = event.value

        # Add unit of measurement if available
        if hasattr(event, "unit_of_measurement"):
            fields["unit_of_measurement"] = event.unit_of_measurement

        # Add additional attributes
        if hasattr(event, "attributes") and event.attributes:
            for key, value in event.attributes.items():
                if isinstance(value, str | int | float | bool):
                    fields[key] = value

        return fields

    async def _apply_transformation(
        self,
        config: dict[str, Any],
        event: BaseEvent,
        tags: dict[str, str],
        fields: dict[str, Any],
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Apply a specific transformation."""
        transform_type = config.get("type")

        if transform_type == "field_mapping":
            return self._apply_field_mapping(config, tags, fields)
        elif transform_type == "type_conversion":
            return self._apply_type_conversion(config, tags, fields)
        elif transform_type == "value_aggregation":
            return self._apply_value_aggregation(config, tags, fields)
        else:
            logger.warning(f"Unknown transformation type: {transform_type}")
            return tags, fields

    def _apply_field_mapping(
        self, config: dict[str, Any], tags: dict[str, str], fields: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Apply field mapping transformation."""
        mappings = config.get("mappings", {})

        for source_field, target_field in mappings.items():
            if source_field in fields:
                fields[target_field] = fields.pop(source_field)

        return tags, fields

    def _apply_type_conversion(
        self, config: dict[str, Any], tags: dict[str, str], fields: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Apply type conversion transformation."""
        conversions = config.get("conversions", {})

        for field_name, conversion_config in conversions.items():
            if field_name in fields:
                target_type = conversion_config.get("target_type")
                default_value = conversion_config.get("default_value")

                try:
                    if target_type == "float":
                        fields[field_name] = float(fields[field_name])
                    elif target_type == "int":
                        fields[field_name] = int(fields[field_name])
                    elif target_type == "bool":
                        fields[field_name] = bool(fields[field_name])
                    elif target_type == "string":
                        fields[field_name] = str(fields[field_name])
                except (ValueError, TypeError):
                    if default_value is not None:
                        fields[field_name] = default_value
                    else:
                        # Remove field if conversion fails and no default
                        fields.pop(field_name, None)

        return tags, fields

    def _apply_value_aggregation(
        self, config: dict[str, Any], tags: dict[str, str], fields: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Apply value aggregation transformation."""
        aggregations = config.get("aggregations", {})

        for field_name, agg_config in aggregations.items():
            if field_name in fields:
                agg_type = agg_config.get("type")
                window_size = agg_config.get("window_size", 60)  # seconds

                # This is a simplified example - in practice, you'd need
                # to maintain state across multiple events
                if agg_type == "rolling_average":
                    # Implementation would depend on your state management
                    pass

        return tags, fields


# ============================================================================
# PATTERN 4: Metrics Collection and Monitoring
# ============================================================================


class MetricsCollector:
    """
    AI ASSISTANT CONTEXT: Demonstrates the metrics collection pattern.
    Use this pattern when implementing monitoring and observability features.
    """

    def __init__(self):
        self.metrics = MetricsRegistry()
        self._setup_metrics()

    def _setup_metrics(self):
        """Setup Prometheus metrics."""
        # Event processing metrics
        self.events_processed = self.metrics.counter(
            "events_processed_total",
            "Total number of events processed",
            ["status", "domain"],
        )

        self.processing_duration = self.metrics.histogram(
            "event_processing_duration_seconds",
            "Time spent processing events",
            ["domain", "filter_type"],
        )

        self.filter_efficiency = self.metrics.gauge(
            "filter_efficiency_ratio", "Ratio of events passing through filters"
        )

        # Pipeline metrics
        self.pipeline_throughput = self.metrics.counter(
            "pipeline_throughput_total",
            "Total events processed by pipeline",
            ["pipeline_stage"],
        )

        self.pipeline_errors = self.metrics.counter(
            "pipeline_errors_total",
            "Total errors in pipeline",
            ["pipeline_stage", "error_type"],
        )

    def record_event_processed(self, status: str, domain: str):
        """Record a processed event."""
        self.events_processed.labels(status=status, domain=domain).inc()

    def record_processing_duration(
        self, duration: float, domain: str, filter_type: str
    ):
        """Record processing duration."""
        self.processing_duration.labels(domain=domain, filter_type=filter_type).observe(
            duration
        )

    def update_filter_efficiency(self, total_events: int, passed_events: int):
        """Update filter efficiency ratio."""
        if total_events > 0:
            efficiency = passed_events / total_events
            self.filter_efficiency.set(efficiency)

    def record_pipeline_throughput(self, stage: str):
        """Record pipeline throughput."""
        self.pipeline_throughput.labels(pipeline_stage=stage).inc()

    def record_pipeline_error(self, stage: str, error_type: str):
        """Record pipeline error."""
        self.pipeline_errors.labels(pipeline_stage=stage, error_type=error_type).inc()


# ============================================================================
# PATTERN 5: Configuration Management
# ============================================================================


@dataclass
class FilterConfiguration:
    """
    AI ASSISTANT CONTEXT: Demonstrates the configuration management pattern.
    Use this pattern when creating new configuration schemas.
    """

    enabled: bool = True
    filter_type: str = "default"
    priority: int = 100
    timeout: float | None = None
    retry_count: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "FilterConfiguration":
        """Create configuration from dictionary."""
        return cls(
            enabled=config.get("enabled", True),
            filter_type=config.get("filter_type", "default"),
            priority=config.get("priority", 100),
            timeout=config.get("timeout"),
            retry_count=config.get("retry_count", 3),
            retry_delay=config.get("retry_delay", 1.0),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if self.priority < 0 or self.priority > 1000:
            errors.append("Priority must be between 0 and 1000")

        if self.retry_count < 0:
            errors.append("Retry count must be non-negative")

        if self.retry_delay < 0:
            errors.append("Retry delay must be non-negative")

        if self.timeout is not None and self.timeout <= 0:
            errors.append("Timeout must be positive")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "enabled": self.enabled,
            "filter_type": self.filter_type,
            "priority": self.priority,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
        }


# ============================================================================
# PATTERN 6: Error Handling and Retry Logic
# ============================================================================


class RetryableOperation:
    """
    AI ASSISTANT CONTEXT: Demonstrates the retry logic pattern.
    Use this pattern when implementing operations that may fail temporarily.
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(self, operation: callable, *args, **kwargs) -> Any:
        """Execute an operation with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                return result

            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    delay = self.base_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Operation failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Operation failed after {self.max_retries + 1} attempts: {e}"
                    )

        raise last_exception


# ============================================================================
# PATTERN 7: Batch Processing
# ============================================================================


class BatchProcessor:
    """
    AI ASSISTANT CONTEXT: Demonstrates the batch processing pattern.
    Use this pattern when implementing operations that benefit from batching.
    """

    def __init__(self, batch_size: int = 100, batch_timeout: float = 5.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.current_batch: list[Any] = []
        self.last_batch_time = datetime.utcnow()

    async def add_item(self, item: Any) -> bool:
        """Add an item to the current batch. Returns True if batch is ready."""
        self.current_batch.append(item)

        # Check if batch is ready
        batch_ready = (
            len(self.current_batch) >= self.batch_size
            or (datetime.utcnow() - self.last_batch_time).total_seconds()
            >= self.batch_timeout
        )

        return batch_ready

    def get_batch(self) -> list[Any]:
        """Get the current batch and reset."""
        batch = self.current_batch.copy()
        self.current_batch.clear()
        self.last_batch_time = datetime.utcnow()
        return batch

    def get_batch_size(self) -> int:
        """Get the current batch size."""
        return len(self.current_batch)

    def is_batch_ready(self) -> bool:
        """Check if the current batch is ready for processing."""
        return (
            len(self.current_batch) >= self.batch_size
            or (datetime.utcnow() - self.last_batch_time).total_seconds()
            >= self.batch_timeout
        )


# ============================================================================
# PATTERN 8: Health Check Implementation
# ============================================================================


class HealthChecker:
    """
    AI ASSISTANT CONTEXT: Demonstrates the health check pattern.
    Use this pattern when implementing health monitoring for services.
    """

    def __init__(self):
        self.checks: list[dict[str, Any]] = []
        self.last_check_time: datetime | None = None

    def add_check(self, name: str, check_func: callable, timeout: float = 5.0):
        """Add a health check."""
        self.checks.append({"name": name, "check_func": check_func, "timeout": timeout})

    async def run_health_checks(self) -> dict[str, Any]:
        """Run all health checks."""
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "overall_status": "healthy",
        }

        for check in self.checks:
            try:
                # Run check with timeout
                if asyncio.iscoroutinefunction(check["check_func"]):
                    check_result = await asyncio.wait_for(
                        check["check_func"](), timeout=check["timeout"]
                    )
                else:
                    check_result = check["check_func"]()

                results["checks"][check["name"]] = {
                    "status": "healthy",
                    "result": check_result,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            except TimeoutError:
                results["checks"][check["name"]] = {
                    "status": "unhealthy",
                    "error": "Check timed out",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                results["overall_status"] = "unhealthy"

            except Exception as e:
                results["checks"][check["name"]] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                results["overall_status"] = "unhealthy"

        # Update overall status
        if results["overall_status"] == "unhealthy":
            results["status"] = "unhealthy"

        self.last_check_time = datetime.utcnow()
        return results


# ============================================================================
# Usage Examples
# ============================================================================


async def main():
    """Demonstrate the common patterns."""
    logger.info("Starting Common Patterns Demo")

    # Example 1: Event Processing Pipeline
    logger.info("=== Event Processing Pipeline ===")

    # Create sample filters and transformers
    filters = [
        ConfigurableFilter(
            {
                "enabled": True,
                "include_values": ["sensor", "binary_sensor"],
                "exclude_values": ["test"],
            }
        )
    ]

    transformers = []  # Add transformers as needed

    # Create processor for demonstration
    EventProcessor(filters, transformers)

    # Example 2: Metrics Collection
    logger.info("=== Metrics Collection ===")
    metrics = MetricsCollector()
    metrics.record_event_processed("success", "sensor")
    metrics.record_processing_duration(0.1, "sensor", "domain_filter")

    # Example 3: Configuration Management
    logger.info("=== Configuration Management ===")
    config = FilterConfiguration.from_dict(
        {"enabled": True, "priority": 200, "retry_count": 5}
    )

    errors = config.validate()
    if errors:
        logger.warning(f"Configuration validation errors: {errors}")

    # Example 4: Health Checks
    logger.info("=== Health Checks ===")
    health_checker = HealthChecker()

    # Add a simple health check
    def simple_check():
        return {"message": "Service is healthy"}

    health_checker.add_check("simple_check", simple_check)

    health_status = await health_checker.run_health_checks()
    logger.info(f"Health status: {health_status['overall_status']}")

    logger.info("Common Patterns Demo completed")


if __name__ == "__main__":
    asyncio.run(main())
