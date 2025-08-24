R"""InfluxDB writer for Home Assistant data storage."""

import asyncio
import gzip
import time
import zlib
from datetime import datetime
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from ..config import get_settings
from ..metrics import get_metrics_collector
from ..models import InfluxDBPoint
from ..utils.logging import get_logger


class InfluxDBWriter:
    """InfluxDB writer for storing Home Assistant data points."""

    def __init__(self, config: Any = None) -> None:
        """Initialize InfluxDB writer.

        Args:
            config: Configuration settings. If None, uses global settings.
        """
        self.config = config or get_settings()
        self.logger = get_logger(__name__)

        # HTTP client session
        self.session: aiohttp.ClientSession | None = None

        # Connection state
        self._connected = False
        self._connecting = False

        # Batch processing
        self._batch_size = self.config.influxdb_batch_size
        self._batch_timeout = self.config.influxdb_batch_timeout
        self._pending_points: list[InfluxDBPoint] = []
        self._batch_task: asyncio.Task | None = None
        self._last_batch_time: datetime | None = None

        # Error handling and retry
        self._max_retries = self.config.influxdb_max_retries
        self._retry_delay = self.config.influxdb_retry_delay
        self._retry_backoff = self.config.influxdb_retry_backoff
        self._retry_jitter = self.config.influxdb_retry_jitter

        # Circuit breaker state
        self._circuit_breaker_state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._circuit_breaker_failure_count = 0
        self._circuit_breaker_failure_threshold = 5
        self._circuit_breaker_timeout = 60.0  # seconds
        self._circuit_breaker_last_failure_time: datetime | None = None

        # Retry tracking
        self._consecutive_failures = 0
        self._last_successful_write: datetime | None = None

        # Statistics
        self._points_written = 0
        self._points_failed = 0
        self._batches_processed = 0
        self._last_write_time: datetime | None = None
        self._total_write_time = 0.0
        self._total_batch_time = 0.0

        # Compression and optimization
        self._compression = self.config.influxdb_compression.lower()
        self._compression_level = self.config.influxdb_compression_level
        self._optimize_batches = self.config.influxdb_optimize_batches

        # HTTP timeout
        self._timeout = ClientTimeout(
            total=self.config.influxdb_write_timeout,
            connect=self.config.influxdb_connect_timeout,
        )

    async def connect(self) -> bool:
        """Connect to InfluxDB.

        Returns:
            True if connection successful, False otherwise.
        """
        if self._connected or self._connecting:
            self.logger.warning("Already connected or connecting")
            return self._connected

        self._connecting = True
        self.logger.info("Connecting to InfluxDB", url=str(self.config.influxdb_url))

        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession(timeout=self._timeout)

            # Test connection by checking database info
            if await self._test_connection():
                self._connected = True
                self.logger.info("Successfully connected to InfluxDB")

                # Start batch processing
                self._start_batch_processing()

                return True
            else:
                self.logger.error("Failed to connect to InfluxDB")
                await self.disconnect()
                return False

        except Exception as e:
            self.logger.error("Error connecting to InfluxDB", error=str(e))
            return False
        finally:
            self._connecting = False

    async def disconnect(self) -> None:
        """Disconnect from InfluxDB."""
        if not self._connected:
            return

        self.logger.info("Disconnecting from InfluxDB")

        try:
            # Stop batch processing
            self._stop_batch_processing()

            # Flush any pending points
            if self._pending_points:
                await self._flush_batch()

            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None

        except Exception as e:
            self.logger.error("Error disconnecting from InfluxDB", error=str(e))
        finally:
            self._connected = False

    async def write_point(self, point: InfluxDBPoint) -> bool:
        """Write a single data point to InfluxDB.

        Args:
            point: InfluxDBPoint to write

        Returns:
            True if write successful, False otherwise.
        """
        if not self._connected:
            self.logger.error("Cannot write point: not connected to InfluxDB")
            return False

        try:
            # Track batch start time if this is the first point
            if not self._pending_points:
                self._last_batch_time = datetime.now()

            # Add point to batch
            self._pending_points.append(point)

            # Check if batch is full
            if len(self._pending_points) >= self._batch_size:
                await self._flush_batch()

            return True

        except Exception as e:
            self.logger.error("Error adding point to batch", error=str(e))
            self._points_failed += 1
            return False

    async def write_points(self, points: list[InfluxDBPoint]) -> bool:
        """Write multiple data points to InfluxDB.

        Args:
            points: List of InfluxDBPoint objects to write

        Returns:
            True if all writes successful, False otherwise.
        """
        if not self._connected:
            self.logger.error("Cannot write points: not connected to InfluxDB")
            return False

        try:
            success_count = 0
            for point in points:
                if await self.write_point(point):
                    success_count += 1

            # Force flush if we have points
            if self._pending_points:
                await self._flush_batch()

            self.logger.info(
                "Wrote points to InfluxDB", total=len(points), successful=success_count
            )

            return success_count == len(points)

        except Exception as e:
            self.logger.error("Error writing points to InfluxDB", error=str(e))
            return False

    async def flush(self) -> bool:
        """Force flush of pending points.

        Returns:
            True if flush successful, False otherwise.
        """
        if not self._connected:
            return False

        if self._pending_points:
            return await self._flush_batch()

        return True

    def is_connected(self) -> bool:
        """Check if writer is connected to InfluxDB.

        Returns:
            True if connected, False otherwise.
        """
        return self._connected

    def update_batch_config(
        self,
        batch_size: int | None = None,
        batch_timeout: float | None = None,
        compression: str | None = None,
        compression_level: int | None = None,
        optimize_batches: bool | None = None,
    ) -> None:
        """Update batch processing configuration.

        Args:
            batch_size: New batch size (if provided)
            batch_timeout: New batch timeout in seconds (if provided)
            compression: New compression algorithm (if provided)
            compression_level: New compression level (if provided)
            optimize_batches: New optimization setting (if provided)
        """
        if batch_size is not None:
            if batch_size < 1 or batch_size > 10000:
                raise ValueError("batch_size must be between 1 and 10000")
            self._batch_size = batch_size
            self.logger.info("Updated batch size", new_batch_size=batch_size)

        if batch_timeout is not None:
            if batch_timeout < 0.1 or batch_timeout > 300.0:
                raise ValueError("batch_timeout must be between 0.1 and 300.0 seconds")
            self._batch_timeout = batch_timeout
            self.logger.info("Updated batch timeout", new_batch_timeout=batch_timeout)

        if compression is not None:
            if compression.lower() not in ["gzip", "deflate", "none"]:
                raise ValueError("compression must be one of: gzip, deflate, none")
            self._compression = compression.lower()
            self.logger.info("Updated compression", new_compression=self._compression)

        if compression_level is not None:
            if compression_level < 1 or compression_level > 9:
                raise ValueError("compression_level must be between 1 and 9")
            self._compression_level = compression_level
            self.logger.info(
                "Updated compression level", new_level=self._compression_level
            )

        if optimize_batches is not None:
            self._optimize_batches = optimize_batches
            self.logger.info(
                "Updated batch optimization", new_setting=self._optimize_batches
            )

    def get_batch_config(self) -> dict[str, Any]:
        """Get current batch configuration.

        Returns:
            Dictionary with current batch settings.
        """
        return {
            "batch_size": self._batch_size,
            "batch_timeout": self._batch_timeout,
            "max_retries": self._max_retries,
            "retry_delay": self._retry_delay,
            "retry_backoff": self._retry_backoff,
            "retry_jitter": self._retry_jitter,
            "compression": self._compression,
            "compression_level": self._compression_level,
            "optimize_batches": self._optimize_batches,
            "circuit_breaker_state": self._circuit_breaker_state,
            "circuit_breaker_failure_count": self._circuit_breaker_failure_count,
            "consecutive_failures": self._consecutive_failures,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get writer statistics.

        Returns:
            Dictionary with statistics.
        """
        # Calculate averages
        avg_batch_size = (
            self._points_written / self._batches_processed
            if self._batches_processed > 0
            else 0
        )
        avg_write_time = (
            self._total_write_time / self._batches_processed
            if self._batches_processed > 0
            else 0
        )
        avg_batch_time = (
            self._total_batch_time / self._batches_processed
            if self._batches_processed > 0
            else 0
        )

        return {
            "connected": self._connected,
            "points_written": self._points_written,
            "points_failed": self._points_failed,
            "batches_processed": self._batches_processed,
            "pending_points": len(self._pending_points),
            "last_write_time": (
                self._last_write_time.isoformat() if self._last_write_time else None
            ),
            "batch_size": self._batch_size,
            "batch_timeout": self._batch_timeout,
            "max_retries": self._max_retries,
            "retry_delay": self._retry_delay,
            "retry_backoff": self._retry_backoff,
            "retry_jitter": self._retry_jitter,
            "avg_batch_size": round(avg_batch_size, 2),
            "avg_write_time": round(avg_write_time, 3),
            "avg_batch_time": round(avg_batch_time, 3),
            "total_write_time": round(self._total_write_time, 3),
            "total_batch_time": round(self._total_batch_time, 3),
        }

    def get_batch_performance(self) -> dict[str, Any]:
        """Get batch performance metrics.

        Returns:
            Dictionary with performance metrics.
        """
        if self._batches_processed == 0:
            return {
                "throughput_points_per_second": 0.0,
                "throughput_batches_per_second": 0.0,
                "avg_batch_size": 0.0,
                "avg_write_time": 0.0,
                "avg_batch_time": 0.0,
                "efficiency_ratio": 0.0,
            }

        # Calculate throughput
        if self._last_write_time and self._last_batch_time:
            total_runtime = (
                self._last_write_time - self._last_batch_time
            ).total_seconds()
            if total_runtime > 0:
                throughput_points = self._points_written / total_runtime
                throughput_batches = self._batches_processed / total_runtime
            else:
                throughput_points = 0.0
                throughput_batches = 0.0
        else:
            throughput_points = 0.0
            throughput_batches = 0.0

        # Calculate efficiency (write time vs batch time)
        efficiency_ratio = (
            self._total_write_time / self._total_batch_time
            if self._total_batch_time > 0
            else 0.0
        )

        return {
            "throughput_points_per_second": round(throughput_points, 2),
            "throughput_batches_per_second": round(throughput_batches, 3),
            "avg_batch_size": round(self._points_written / self._batches_processed, 2),
            "avg_write_time": round(
                self._total_write_time / self._batches_processed, 3
            ),
            "avg_batch_time": round(
                self._total_batch_time / self._batches_processed, 3
            ),
            "efficiency_ratio": round(efficiency_ratio, 3),
        }

    def get_circuit_breaker_status(self) -> dict[str, Any]:
        """Get circuit breaker status and statistics.

        Returns:
            Dictionary with circuit breaker information.
        """
        return {
            "state": self._circuit_breaker_state,
            "failure_count": self._circuit_breaker_failure_count,
            "failure_threshold": self._circuit_breaker_failure_threshold,
            "timeout": self._circuit_breaker_timeout,
            "consecutive_failures": self._consecutive_failures,
            "last_failure_time": (
                self._circuit_breaker_last_failure_time.isoformat()
                if self._circuit_breaker_last_failure_time
                else None
            ),
            "last_successful_write": (
                self._last_successful_write.isoformat()
                if self._last_successful_write
                else None
            ),
            "is_open": self._is_circuit_breaker_open(),
        }

    def reset_statistics(self) -> None:
        """Reset all statistics counters."""
        self._points_written = 0
        self._points_failed = 0
        self._batches_processed = 0
        self._last_write_time = None
        self._last_batch_time = None
        self._total_write_time = 0.0
        self._total_batch_time = 0.0

        self.logger.info("Reset InfluxDB writer statistics")

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to CLOSED state."""
        self._circuit_breaker_state = "CLOSED"
        self._circuit_breaker_failure_count = 0
        self._circuit_breaker_last_failure_time = None
        self._consecutive_failures = 0

        self.logger.info("Circuit breaker reset to CLOSED state")

    def update_throughput_metrics(self) -> None:
        """Update throughput metrics based on current performance."""
        try:
            metrics_collector = get_metrics_collector()

            # Calculate current throughput
            if self._last_write_time and self._last_batch_time:
                runtime = (
                    self._last_write_time - self._last_batch_time
                ).total_seconds()
                if runtime > 0:
                    points_per_second = self._points_written / runtime
                    batches_per_second = self._batches_processed / runtime

                    # Record throughput metrics
                    metrics_collector.record_influxdb_throughput(
                        points_per_second, batches_per_second
                    )

                    # Update circuit breaker state metric
                    metrics_collector.record_influxdb_circuit_breaker_state(
                        self._circuit_breaker_state
                    )

        except Exception as e:
            self.logger.error("Error updating throughput metrics", error=str(e))

    def detect_workload_type(self, points: list[InfluxDBPoint]) -> dict[str, Any]:
        """Detect workload characteristics from a batch of points.

        Args:
            points: List of points to analyze

        Returns:
            Dictionary with workload characteristics
        """
        if not points:
            return {"type": "empty", "characteristics": {}}

        # Analyze point characteristics
        measurements = [p.measurement for p in points]
        unique_measurements = len(set(measurements))
        total_points = len(points)

        # Analyze tag patterns
        tag_counts = []
        field_counts = []
        timestamp_patterns = []

        for point in points:
            tag_counts.append(len(point.tags))
            field_counts.append(len(point.fields))

            # Analyze timestamp patterns (hourly, daily, etc.)
            if point.timestamp:
                hour = point.timestamp.hour
                timestamp_patterns.append(hour)

        # Calculate statistics
        avg_tag_count = sum(tag_counts) / len(tag_counts) if tag_counts else 0
        avg_field_count = sum(field_counts) / len(field_counts) if field_counts else 0

        # Determine workload type based on characteristics
        workload_type = "mixed"
        if unique_measurements == 1:
            if avg_tag_count > 5:
                workload_type = "high_cardinality"
            elif avg_field_count > 10:
                workload_type = "wide_metrics"
            else:
                workload_type = "simple_metrics"
        elif unique_measurements > 10:
            workload_type = "multi_source"

        # Check for time-series patterns
        if timestamp_patterns:
            unique_hours = len(set(timestamp_patterns))
            if unique_hours <= 2:
                time_pattern = "burst"
            elif unique_hours <= 6:
                time_pattern = "periodic"
            else:
                time_pattern = "continuous"
        else:
            time_pattern = "unknown"

        return {
            "type": workload_type,
            "characteristics": {
                "total_points": total_points,
                "unique_measurements": unique_measurements,
                "avg_tag_count": round(avg_tag_count, 2),
                "avg_field_count": round(avg_field_count, 2),
                "time_pattern": time_pattern,
                "data_density": (
                    total_points / unique_measurements if unique_measurements > 0 else 0
                ),
            },
        }

    def optimize_for_workload(
        self, points: list[InfluxDBPoint], workload_info: dict[str, Any]
    ) -> list[InfluxDBPoint]:
        """Apply workload-specific optimizations to a batch of points.

        Args:
            points: List of points to optimize
            workload_info: Workload characteristics from detect_workload_type

        Returns:
            Optimized list of points
        """
        if not points or not workload_info:
            return points

        workload_type = workload_info.get("type", "mixed")
        characteristics = workload_info.get("characteristics", {})

        self.logger.debug(
            "Applying workload-specific optimization",
            workload_type=workload_type,
            characteristics=characteristics,
        )

        # Apply type-specific optimizations
        if workload_type == "high_cardinality":
            # For high cardinality, focus on tag optimization and compression
            points = self._optimize_high_cardinality(points, characteristics)
        elif workload_type == "wide_metrics":
            # For wide metrics, focus on field optimization
            points = self._optimize_wide_metrics(points, characteristics)
        elif workload_type == "simple_metrics":
            # For simple metrics, focus on batch efficiency
            points = self._optimize_simple_metrics(points, characteristics)
        elif workload_type == "multi_source":
            # For multi-source, focus on measurement grouping
            points = self._optimize_multi_source(points, characteristics)
        elif workload_type == "burst":
            # For burst workloads, optimize for quick processing
            points = self._optimize_burst_workload(points, characteristics)

        return points

    def _optimize_high_cardinality(
        self, points: list[InfluxDBPoint], characteristics: dict[str, Any]
    ) -> list[InfluxDBPoint]:
        """Optimize high cardinality workloads by reducing tag overhead."""
        if not points:
            return points

        # Sort by measurement and tags for better compression
        points.sort(key=lambda p: (p.measurement, str(sorted(p.tags.items()))))

        # Remove redundant tags that don't add value
        optimized_points = []
        for point in points:
            # Keep only essential tags for high cardinality
            essential_tags = {}
            for key, value in point.tags.items():
                # Keep entity_id, location, device_class as essential
                if key in ["entity_id", "location", "device_class", "domain"]:
                    essential_tags[key] = value
                # Keep tags with high variability (likely important for cardinality)
                elif (
                    len(
                        {
                            p.tags.get(key, "")
                            for p in points
                            if p.measurement == point.measurement
                        }
                    )
                    > 1
                ):
                    essential_tags[key] = value

            # Create optimized point
            optimized_point = InfluxDBPoint(
                measurement=point.measurement,
                tags=essential_tags,
                fields=point.fields,
                timestamp=point.timestamp,
            )
            optimized_points.append(optimized_point)

        self.logger.debug(
            "Optimized high cardinality workload",
            original_tags=len(points[0].tags) if points else 0,
            optimized_tags=len(optimized_points[0].tags) if optimized_points else 0,
        )

        return optimized_points

    def _optimize_wide_metrics(
        self, points: list[InfluxDBPoint], characteristics: dict[str, Any]
    ) -> list[InfluxDBPoint]:
        """Optimize wide metrics workloads by grouping related fields."""
        if not points:
            return points

        # Group points by measurement and tags to combine fields
        grouped_points: dict[tuple[str, tuple], dict[str, Any]] = {}

        for point in points:
            # Create key for grouping (measurement + tags)
            group_key = (point.measurement, tuple(sorted(point.tags.items())))

            if group_key not in grouped_points:
                grouped_points[group_key] = {
                    "measurement": point.measurement,
                    "tags": point.tags,
                    "fields": {},
                    "timestamp": point.timestamp,
                }

            # Merge fields, keeping the most recent value for conflicts
            for field_name, field_value in point.fields.items():
                if (
                    field_name not in grouped_points[group_key]["fields"]
                    or point.timestamp > grouped_points[group_key]["timestamp"]
                ):
                    grouped_points[group_key]["fields"][field_name] = field_value

        # Convert grouped data back to points
        optimized_points = []
        for group_data in grouped_points.values():
            optimized_point = InfluxDBPoint(
                measurement=group_data["measurement"],
                tags=group_data["tags"],
                fields=group_data["fields"],
                timestamp=group_data["timestamp"],
            )
            optimized_points.append(optimized_point)

        self.logger.debug(
            "Optimized wide metrics workload",
            original_points=len(points),
            optimized_points=len(optimized_points),
            avg_fields_before=characteristics.get("avg_field_count", 0),
            avg_fields_after=(
                sum(len(p.fields) for p in optimized_points) / len(optimized_points)
                if optimized_points
                else 0
            ),
        )

        return optimized_points

    def _optimize_simple_metrics(
        self, points: list[InfluxDBPoint], characteristics: dict[str, Any]
    ) -> list[InfluxDBPoint]:
        """Optimize simple metrics workloads for maximum throughput."""
        if not points:
            return points

        # For simple metrics, focus on batch efficiency
        # Sort by timestamp for better compression
        points.sort(key=lambda p: p.timestamp)

        # Remove any duplicate measurements with same timestamp
        seen = set()
        optimized_points = []

        for point in points:
            # Create unique key for deduplication
            key = (
                point.measurement,
                point.timestamp,
                tuple(sorted(point.tags.items())),
            )

            if key not in seen:
                seen.add(key)
                optimized_points.append(point)

        self.logger.debug(
            "Optimized simple metrics workload",
            original_points=len(points),
            optimized_points=len(optimized_points),
            duplicates_removed=len(points) - len(optimized_points),
        )

        return optimized_points

    def _optimize_multi_source(
        self, points: list[InfluxDBPoint], characteristics: dict[str, Any]
    ) -> list[InfluxDBPoint]:
        """Optimize multi-source workloads by grouping by measurement."""
        if not points:
            return points

        # Group by measurement for better compression
        measurement_groups: dict[str, list[InfluxDBPoint]] = {}

        for point in points:
            measurement = point.measurement
            if measurement not in measurement_groups:
                measurement_groups[measurement] = []
            measurement_groups[measurement].append(point)

        # Sort each group by timestamp
        optimized_points = []
        for _measurement, group_points in measurement_groups.items():
            # Sort points within each measurement group
            group_points.sort(key=lambda p: p.timestamp)
            optimized_points.extend(group_points)

        self.logger.debug(
            "Optimized multi-source workload",
            measurements=len(measurement_groups),
            total_points=len(optimized_points),
        )

        return optimized_points

    def _optimize_burst_workload(
        self, points: list[InfluxDBPoint], characteristics: dict[str, Any]
    ) -> list[InfluxDBPoint]:
        """Optimize burst workloads for quick processing."""
        if not points:
            return points

        # For burst workloads, minimize processing overhead
        # Skip complex optimizations, focus on basic deduplication

        # Simple deduplication by measurement + timestamp + tags
        seen = set()
        optimized_points = []

        for point in points:
            key = (
                point.measurement,
                point.timestamp,
                tuple(sorted(point.tags.items())),
            )
            if key not in seen:
                seen.add(key)
                optimized_points.append(point)

        self.logger.debug(
            "Optimized burst workload",
            original_points=len(points),
            optimized_points=len(optimized_points),
            processing_overhead="minimal",
        )

        return optimized_points

    def get_workload_optimization_stats(self) -> dict[str, Any]:
        """Get statistics about workload optimization performance.

        Returns:
            Dictionary with optimization statistics
        """
        return {
            "workload_types_processed": {
                "high_cardinality": getattr(self, "_high_cardinality_count", 0),
                "wide_metrics": getattr(self, "_wide_metrics_count", 0),
                "simple_metrics": getattr(self, "_simple_metrics_count", 0),
                "multi_source": getattr(self, "_multi_source_count", 0),
                "burst": getattr(self, "_burst_count", 0),
                "mixed": getattr(self, "_mixed_count", 0),
            },
            "optimization_effectiveness": {
                "avg_points_reduced": getattr(self, "_avg_points_reduced", 0.0),
                "avg_compression_improvement": getattr(
                    self, "_avg_compression_improvement", 0.0
                ),
                "total_optimization_time": getattr(
                    self, "_total_optimization_time", 0.0
                ),
            },
        }

    def reset_workload_stats(self) -> None:
        """Reset workload optimization statistics."""
        self._high_cardinality_count = 0
        self._wide_metrics_count = 0
        self._simple_metrics_count = 0
        self._multi_source_count = 0
        self._burst_count = 0
        self._mixed_count = 0
        self._avg_points_reduced = 0.0
        self._avg_compression_improvement = 0.0
        self._total_optimization_time = 0.0

        self.logger.info("Reset workload optimization statistics")

    async def _test_connection(self) -> bool:
        """Test InfluxDB connection by checking database info.

        Returns:
            True if connection test successful, False otherwise.
        """
        try:
            # Test with a simple ping or health check
            if not self.session:
                self.logger.error("No HTTP session available for connection test")
                return False

            url = f"{self.config.influxdb_url}/health"

            async with self.session.get(url) as response:
                if response.status == 200:
                    self.logger.debug("InfluxDB health check successful")
                    return True
                else:
                    self.logger.warning(
                        "InfluxDB health check failed", status=response.status
                    )
                    return False

        except Exception as e:
            self.logger.error("Error testing InfluxDB connection", error=str(e))
            return False

    async def _flush_batch(self) -> bool:
        """Flush the current batch of points to InfluxDB.

        Returns:
            True if flush successful, False otherwise.
        """
        if not self._pending_points:
            return True

        points_to_write = self._pending_points.copy()
        self._pending_points.clear()

        # Calculate batch age
        batch_age = 0.0
        if self._last_batch_time:
            batch_age = (datetime.now() - self._last_batch_time).total_seconds()
            self._total_batch_time += batch_age

        try:
            # Record original batch size for metrics
            original_size = len(points_to_write)

            # Optimize batch if enabled
            if self._optimize_batches:
                points_to_write = self._optimize_batch(points_to_write)

            # Convert points to line protocol
            lines = []
            for point in points_to_write:
                try:
                    line = point.to_line_protocol()
                    lines.append(line)
                except Exception as e:
                    self.logger.error(
                        "Error converting point to line protocol",
                        point=point,
                        error=str(e),
                    )
                    self._points_failed += 1
                    continue

            if not lines:
                return True

            # Calculate original data size
            original_data_size = len("\n".join(lines).encode("utf-8"))

            # Record batch size metric
            metrics_collector = get_metrics_collector()
            metrics_collector.record_influxdb_batch_size(len(lines))

            # Write to InfluxDB with timing
            start_time = time.time()
            success = await self._write_lines(lines)
            duration = time.time() - start_time
            self._total_write_time += duration

            # Calculate compression ratio (approximate)
            compressed_data_size = original_data_size
            if success and self._compression != "none":
                # Estimate compression ratio based on algorithm
                if self._compression == "gzip":
                    compressed_data_size = int(
                        original_data_size * 0.7
                    )  # ~30% compression
                elif self._compression == "deflate":
                    compressed_data_size = int(
                        original_data_size * 0.75
                    )  # ~25% compression

            # Record comprehensive batch processing metrics
            metrics_collector.record_influxdb_batch_processed(
                success=success,
                processing_duration=duration,
                batch_age=batch_age,
                original_size=original_size,
                optimized_size=len(lines),
                original_data_size=original_data_size,
                compressed_data_size=compressed_data_size,
            )

            # Record write metrics
            metrics_collector.record_influxdb_write(len(lines), success, duration)

            if success:
                self._points_written += len(lines)
                self._batches_processed += 1
                self._last_write_time = datetime.now()

                self.logger.debug(
                    "Successfully wrote batch to InfluxDB",
                    points=len(lines),
                    batch_age=batch_age,
                    duration=duration,
                )
            else:
                # Return failed points to pending queue
                self._pending_points.extend(points_to_write)
                self.logger.warning("Failed to write batch to InfluxDB, retrying later")

            return success

        except Exception as e:
            self.logger.error("Error flushing batch to InfluxDB", error=str(e))
            # Return failed points to pending queue
            self._pending_points.extend(points_to_write)
            return False

    async def _write_lines(self, lines: list[str]) -> bool:
        """Write line protocol data to InfluxDB.

        Args:
            lines: List of line protocol strings

        Returns:
            True if write successful, False otherwise.
        """
        if not self.session:
            return False

        # Check circuit breaker
        if self._is_circuit_breaker_open():
            self.logger.warning("Circuit breaker is open, skipping write operation")
            return False

        # Retry logic with exponential backoff and jitter
        for attempt in range(self._max_retries + 1):
            # Record retry attempt if not first attempt
            if attempt > 0:
                metrics_collector = get_metrics_collector()
                metrics_collector.record_influxdb_retry_attempt(attempt)
            try:
                # Prepare write URL
                url = f"{self.config.influxdb_url}/api/v2/write"
                params = {
                    "org": self.config.influxdb_org,
                    "bucket": self.config.influxdb_bucket,
                    "precision": "ns",  # Nanosecond precision
                }

                # Prepare data
                data = "\n".join(lines)

                # Compress data if compression is enabled
                compressed_data, content_encoding = self._compress_data(data)

                # Update headers for compression
                headers = {
                    "Authorization": f"Token {self.config.influxdb_token}",
                    "Content-Type": "text/plain; charset=utf-8",
                }
                if content_encoding != "identity":
                    headers["Content-Encoding"] = content_encoding

                # Send write request
                assert self.session is not None  # Already checked above
                async with self.session.post(
                    url, params=params, data=compressed_data, headers=headers
                ) as response:
                    if response.status == 204:  # No content = success
                        # Record success and close circuit breaker if needed
                        self._record_circuit_breaker_success()
                        self._last_successful_write = datetime.now()
                        return True
                    elif response.status == 429:  # Rate limited
                        self.logger.warning(
                            "InfluxDB rate limited, retrying",
                            attempt=attempt + 1,
                            max_retries=self._max_retries,
                        )
                        if attempt < self._max_retries:
                            delay = self._calculate_retry_delay(attempt)
                            await asyncio.sleep(delay)
                            continue
                    else:
                        # Get error details
                        error_text = await response.text()
                        self.logger.error(
                            "InfluxDB write failed",
                            status=response.status,
                            attempt=attempt + 1,
                            error=error_text,
                        )

                        if attempt < self._max_retries:
                            delay = self._calculate_retry_delay(attempt)
                            await asyncio.sleep(delay)
                            continue

                        return False

            except TimeoutError:
                self.logger.warning(
                    "InfluxDB write timeout, retrying",
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                )
                if attempt < self._max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    self.logger.error("InfluxDB write failed after timeout retries")
                    return False

            except Exception as e:
                self.logger.error(
                    "Error writing to InfluxDB",
                    attempt=attempt + 1,
                    max_retries=self._max_retries,
                    error=str(e),
                )
                if attempt < self._max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    return False

        # All retry attempts failed, record circuit breaker failure
        self._record_circuit_breaker_failure()

        # Record circuit breaker metrics
        metrics_collector = get_metrics_collector()
        metrics_collector.record_influxdb_circuit_breaker_state(
            self._circuit_breaker_state
        )
        if self._circuit_breaker_state == "OPEN":
            metrics_collector.record_influxdb_circuit_breaker_opened()

        return False

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter.

        Args:
            attempt: Current retry attempt (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay * (multiplier ^ attempt)
        base_delay = self._retry_delay * (self._retry_backoff**attempt)

        # Add jitter (±jitter_percentage)
        import random

        jitter_factor = 1.0 + random.uniform(-self._retry_jitter, self._retry_jitter)

        final_delay = base_delay * jitter_factor

        self.logger.debug(
            "Calculated retry delay",
            attempt=attempt + 1,
            base_delay=base_delay,
            jitter_factor=jitter_factor,
            final_delay=final_delay,
        )

        return final_delay

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests).

        Returns:
            True if circuit breaker is open, False otherwise.
        """
        if self._circuit_breaker_state == "CLOSED":
            return False

        if self._circuit_breaker_state == "OPEN":
            # Check if timeout has passed
            if (
                self._circuit_breaker_last_failure_time
                and (
                    datetime.now() - self._circuit_breaker_last_failure_time
                ).total_seconds()
                > self._circuit_breaker_timeout
            ):
                # Move to half-open state
                self._circuit_breaker_state = "HALF_OPEN"
                self.logger.info("Circuit breaker moved to HALF_OPEN state")
                return False
            return True

        # HALF_OPEN state - allow one request to test
        return False

    def _record_circuit_breaker_success(self) -> None:
        """Record successful operation and close circuit breaker."""
        if self._circuit_breaker_state == "HALF_OPEN":
            self._circuit_breaker_state = "CLOSED"
            self._circuit_breaker_failure_count = 0
            self._circuit_breaker_last_failure_time = None
            self._consecutive_failures = 0
            self.logger.info("Circuit breaker closed after successful operation")

    def _record_circuit_breaker_failure(self) -> None:
        """Record failed operation and potentially open circuit breaker."""
        self._circuit_breaker_failure_count += 1
        self._consecutive_failures += 1
        self._circuit_breaker_last_failure_time = datetime.now()

        if (
            self._circuit_breaker_failure_count
            >= self._circuit_breaker_failure_threshold
        ):
            if self._circuit_breaker_state != "OPEN":
                self._circuit_breaker_state = "OPEN"
                self.logger.warning(
                    "Circuit breaker opened due to repeated failures",
                    failure_count=self._circuit_breaker_failure_count,
                    threshold=self._circuit_breaker_failure_threshold,
                )

    def _optimize_batch(self, points: list[InfluxDBPoint]) -> list[InfluxDBPoint]:
        """Optimize batch by deduplication, sorting, and other optimizations.

        Args:
            points: List of points to optimize

        Returns:
            Optimized list of points
        """
        if not self._optimize_batches or len(points) <= 1:
            return points

        optimized_points = []
        seen_measurements = set()

        # Sort by measurement name for better compression
        sorted_points = sorted(points, key=lambda p: p.measurement)

        for point in sorted_points:
            # Create a unique key for deduplication
            point_key = f"{point.measurement}:{point.tags.get('entity_id', '')}:{point.timestamp}"

            if point_key not in seen_measurements:
                seen_measurements.add(point_key)
                optimized_points.append(point)
            else:
                # Keep the most recent version if timestamps differ
                existing_point = next(
                    p
                    for p in optimized_points
                    if f"{p.measurement}:{p.tags.get('entity_id', '')}:{p.timestamp}"
                    == point_key
                )
                if point.timestamp > existing_point.timestamp:
                    # Replace with newer point
                    optimized_points.remove(existing_point)
                    optimized_points.append(point)

        # Sort by timestamp for better compression
        optimized_points.sort(key=lambda p: p.timestamp)

        removed_count = len(points) - len(optimized_points)
        if removed_count > 0:
            self.logger.debug(
                "Optimized batch",
                original_count=len(points),
                optimized_count=len(optimized_points),
                removed_duplicates=removed_count,
            )

        return optimized_points

    def _compress_data(self, data: str) -> tuple[bytes, str]:
        """Compress data using the configured compression algorithm.

        Args:
            data: String data to compress

        Returns:
            Tuple of (compressed_data, content_encoding)
        """
        if self._compression == "none":
            return data.encode("utf-8"), "identity"

        try:
            if self._compression == "gzip":
                compressed = gzip.compress(
                    data.encode("utf-8"), compresslevel=self._compression_level
                )
                return compressed, "gzip"
            elif self._compression == "deflate":
                compressed = zlib.compress(
                    data.encode("utf-8"), level=self._compression_level
                )
                return compressed, "deflate"
            else:
                self.logger.warning(
                    "Unknown compression algorithm, using none",
                    algorithm=self._compression,
                )
                return data.encode("utf-8"), "identity"

        except Exception as e:
            self.logger.error(
                "Compression failed, using uncompressed data",
                algorithm=self._compression,
                error=str(e),
            )
            return data.encode("utf-8"), "identity"

    def _start_batch_processing(self) -> None:
        """Start batch processing task."""
        if self._batch_task:
            self._batch_task.cancel()

        self._batch_task = asyncio.create_task(self._batch_loop())
        self.logger.debug("Started batch processing")

    def _stop_batch_processing(self) -> None:
        """Stop batch processing task."""
        if self._batch_task:
            self._batch_task.cancel()
            self._batch_task = None
            self.logger.debug("Stopped batch processing")

    async def _batch_loop(self) -> None:
        """Batch processing loop."""
        try:
            while self._connected:
                await asyncio.sleep(self._batch_timeout)

                if self._connected and self._pending_points:
                    await self._flush_batch()

        except asyncio.CancelledError:
            self.logger.debug("Batch processing task cancelled")
        except Exception as e:
            self.logger.error("Error in batch processing loop", error=str(e))

    async def create_bucket_if_not_exists(self) -> bool:
        """Create InfluxDB bucket if it doesn't exist.

        Returns:
            True if bucket exists or was created successfully, False otherwise.
        """
        if not self._connected:
            self.logger.error("Cannot create bucket: not connected to InfluxDB")
            return False

        if not self.session:
            self.logger.error("No HTTP session available for bucket creation")
            return False

        try:
            # Check if bucket exists
            url = f"{self.config.influxdb_url}/api/v2/buckets"
            params = {
                "org": self.config.influxdb_org,
                "name": self.config.influxdb_bucket,
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    buckets = await response.json()
                    if any(
                        bucket["name"] == self.config.influxdb_bucket
                        for bucket in buckets.get("buckets", [])
                    ):
                        self.logger.info(
                            "InfluxDB bucket already exists",
                            bucket=self.config.influxdb_bucket,
                        )
                        return True

                # Create bucket
                create_url = f"{self.config.influxdb_url}/api/v2/buckets"
                create_data = {
                    "name": self.config.influxdb_bucket,
                    "orgID": self.config.influxdb_org,
                    "retentionRules": [
                        {
                            "type": "expire",
                            "everySeconds": 0,  # No retention (keep forever)
                        }
                    ],
                }

                async with self.session.post(
                    create_url, json=create_data
                ) as create_response:
                    if create_response.status == 201:
                        self.logger.info(
                            "Successfully created InfluxDB bucket",
                            bucket=self.config.influxdb_bucket,
                        )
                        return True
                    else:
                        error_text = await create_response.text()
                        self.logger.error(
                            "Failed to create InfluxDB bucket",
                            status=create_response.status,
                            error=error_text,
                        )
                        return False

        except Exception as e:
            self.logger.error("Error creating InfluxDB bucket", error=str(e))
            return False
