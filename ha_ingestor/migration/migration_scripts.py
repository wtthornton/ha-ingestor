"""Migration scripts for data transfer between schemas.

This module provides utilities for migrating data from the old schema to
the new optimized schema, including data extraction, transformation, and
validation scripts.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiofiles

from ..models.mqtt_event import MQTTEvent
from ..models.websocket_event import WebSocketEvent
from ..transformers.schema_transformer import SchemaTransformer


@dataclass
class MigrationBatch:
    """Batch of data for migration processing."""

    batch_id: str
    records: list[dict[str, Any]]
    source_measurement: str
    target_measurement: str
    batch_size: int
    created_at: datetime
    processed_at: datetime | None = None
    success_count: int = 0
    error_count: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class DataExtractor:
    """Extracts data from the existing InfluxDB schema."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize data extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    async def extract_measurements(
        self, time_range: tuple[datetime, datetime] | None = None
    ) -> list[str]:
        """Extract list of measurements from InfluxDB.

        Args:
            time_range: Optional time range for extraction

        Returns:
            List of measurement names
        """
        # This would query InfluxDB for measurement names
        # For now, return simulated measurements
        measurements = [
            "ha_light",
            "ha_switch",
            "ha_sensor",
            "ha_climate",
            "ha_state_changed",
            "ha_call_service",
            "ha_automation_triggered",
        ]

        self.logger.info(f"Extracted {len(measurements)} measurements")
        return measurements

    async def extract_data_batch(
        self,
        measurement: str,
        batch_size: int = 1000,
        offset: int = 0,
        time_range: tuple[datetime, datetime] | None = None,
    ) -> MigrationBatch:
        """Extract a batch of data from a measurement.

        Args:
            measurement: Measurement name to extract from
            batch_size: Size of data batch
            offset: Offset for pagination
            time_range: Optional time range for extraction

        Returns:
            Migration batch with extracted data
        """
        # Simulate data extraction
        batch_id = (
            f"{measurement}_{offset}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        # This would query InfluxDB for actual data
        records = []
        for i in range(batch_size):
            record = {
                "measurement": measurement,
                "tags": {
                    "domain": measurement.replace("ha_", ""),
                    "entity_id": f"entity_{offset + i}",
                    "source": (
                        "mqtt"
                        if not measurement.startswith("ha_state")
                        else "websocket"
                    ),
                },
                "fields": {"state": "on" if i % 2 == 0 else "off", "value": i * 10.5},
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
            }
            records.append(record)

        batch = MigrationBatch(
            batch_id=batch_id,
            records=records,
            source_measurement=measurement,
            target_measurement=self._get_target_measurement(measurement),
            batch_size=len(records),
            created_at=datetime.utcnow(),
        )

        self.logger.debug(f"Extracted batch {batch_id} with {len(records)} records")
        return batch

    def _get_target_measurement(self, source_measurement: str) -> str:
        """Get target measurement for source measurement.

        Args:
            source_measurement: Source measurement name

        Returns:
            Target measurement name
        """
        # Map source measurements to target measurements
        if source_measurement.startswith("ha_state"):
            return "ha_entities"
        elif source_measurement in ["ha_call_service", "ha_service_executed"]:
            return "ha_services"
        elif source_measurement in [
            "ha_automation_triggered",
            "ha_automation_executed",
        ]:
            return "ha_automations"
        elif source_measurement.startswith("ha_"):
            return "ha_entities"
        else:
            return "ha_events"

    async def get_data_statistics(self, measurement: str) -> dict[str, Any]:
        """Get statistics about data in a measurement.

        Args:
            measurement: Measurement name

        Returns:
            Statistics dictionary
        """
        # This would query InfluxDB for actual statistics
        stats = {
            "total_records": 50000 + hash(measurement) % 100000,
            "date_range": {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "tag_cardinality": {
                "entity_id": 1000 + hash(measurement) % 5000,
                "domain": 10,
                "source": 2,
            },
            "field_count": 5 + hash(measurement) % 10,
            "estimated_size_mb": (50000 + hash(measurement) % 100000) * 0.001,
        }

        self.logger.info(
            f"Statistics for {measurement}: {stats['total_records']} records"
        )
        return stats


class DataTransformer:
    """Transforms data from old schema to new optimized schema."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize data transformer.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.schema_transformer = SchemaTransformer("migration_transformer")
        self.transformation_stats = {
            "total_transformed": 0,
            "transformation_errors": 0,
            "optimization_scores": [],
        }

    async def transform_batch(self, batch: MigrationBatch) -> MigrationBatch:
        """Transform a batch of data to the new schema.

        Args:
            batch: Migration batch to transform

        Returns:
            Transformed migration batch
        """
        transformed_records = []
        success_count = 0
        error_count = 0
        errors = []

        for record in batch.records:
            try:
                # Convert record to event-like object for transformation
                event = self._create_event_from_record(record)

                # Transform to optimized schema
                result = self.schema_transformer.transform(event)

                if result.success:
                    optimized_point = result.data
                    transformed_record = {
                        "measurement": optimized_point.measurement,
                        "tags": optimized_point.tags,
                        "fields": optimized_point.fields,
                        "timestamp": optimized_point.timestamp,
                        "metadata": optimized_point.metadata,
                    }
                    transformed_records.append(transformed_record)
                    success_count += 1

                    # Track optimization score
                    if hasattr(optimized_point, "get_optimization_score"):
                        score = optimized_point.get_optimization_score()
                        self.transformation_stats["optimization_scores"].append(score)
                else:
                    error_count += 1
                    error_msg = f"Transformation failed: {'; '.join(result.errors)}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)

            except Exception as e:
                error_count += 1
                error_msg = f"Record transformation error: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        # Update batch with transformation results
        batch.records = transformed_records
        batch.target_measurement = batch.target_measurement
        batch.success_count = success_count
        batch.error_count = error_count
        batch.errors = errors
        batch.processed_at = datetime.utcnow()

        # Update global stats
        self.transformation_stats["total_transformed"] += success_count
        self.transformation_stats["transformation_errors"] += error_count

        self.logger.info(
            f"Transformed batch {batch.batch_id}: {success_count} success, {error_count} errors"
        )

        return batch

    def _create_event_from_record(
        self, record: dict[str, Any]
    ) -> MQTTEvent | WebSocketEvent:
        """Create an event object from a record for transformation.

        Args:
            record: Record dictionary

        Returns:
            Event object for transformation
        """
        tags = record.get("tags", {})
        fields = record.get("fields", {})
        timestamp = record.get("timestamp", datetime.utcnow())

        source = tags.get("source", "mqtt")

        if source == "mqtt":
            # Create MQTT event
            return MQTTEvent(
                topic=f"homeassistant/{tags.get('domain', 'unknown')}/{tags.get('entity_id', 'unknown')}/state",
                payload=json.dumps(fields),
                timestamp=timestamp,
                domain=tags.get("domain"),
                entity_id=tags.get("entity_id"),
                state=fields.get("state", "unknown"),
                attributes=fields,
                event_type="state_changed",
            )
        else:
            # Create WebSocket event
            return WebSocketEvent(
                event_type=tags.get("event_type", "state_changed"),
                timestamp=timestamp,
                entity_id=tags.get("entity_id"),
                domain=tags.get("domain"),
                data=fields,
            )

    def get_transformation_statistics(self) -> dict[str, Any]:
        """Get transformation statistics.

        Returns:
            Transformation statistics
        """
        avg_score = 0.0
        if self.transformation_stats["optimization_scores"]:
            avg_score = sum(self.transformation_stats["optimization_scores"]) / len(
                self.transformation_stats["optimization_scores"]
            )

        return {
            "total_transformed": self.transformation_stats["total_transformed"],
            "transformation_errors": self.transformation_stats["transformation_errors"],
            "error_rate": self.transformation_stats["transformation_errors"]
            / max(1, self.transformation_stats["total_transformed"]),
            "average_optimization_score": avg_score,
            "min_optimization_score": min(
                self.transformation_stats["optimization_scores"], default=0
            ),
            "max_optimization_score": max(
                self.transformation_stats["optimization_scores"], default=0
            ),
        }


class DataLoader:
    """Loads transformed data into the new optimized schema."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize data loader.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.loading_stats = {
            "total_loaded": 0,
            "loading_errors": 0,
            "batches_processed": 0,
        }

    async def load_batch(self, batch: MigrationBatch) -> bool:
        """Load a transformed batch into the new schema.

        Args:
            batch: Transformed migration batch

        Returns:
            True if batch loaded successfully
        """
        try:
            # This would write to InfluxDB with the new schema
            # For now, simulate the loading process

            success_count = 0
            error_count = 0

            for record in batch.records:
                try:
                    # Simulate writing to InfluxDB
                    await self._write_record_to_influxdb(record)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Failed to load record: {e}")

            # Update batch status
            batch.success_count = success_count
            batch.error_count += error_count

            # Update global stats
            self.loading_stats["total_loaded"] += success_count
            self.loading_stats["loading_errors"] += error_count
            self.loading_stats["batches_processed"] += 1

            self.logger.info(
                f"Loaded batch {batch.batch_id}: {success_count} success, {error_count} errors"
            )

            return error_count == 0

        except Exception as e:
            self.logger.error(f"Failed to load batch {batch.batch_id}: {e}")
            return False

    async def _write_record_to_influxdb(self, record: dict[str, Any]) -> None:
        """Write a single record to InfluxDB.

        Args:
            record: Record to write
        """
        # This would use the InfluxDB client to write the record
        # For now, just simulate success/failure
        import random

        if random.random() < 0.01:  # 1% failure rate for simulation
            raise Exception("Simulated write failure")

        # Simulate write delay
        await asyncio.sleep(0.001)

    def get_loading_statistics(self) -> dict[str, Any]:
        """Get loading statistics.

        Returns:
            Loading statistics
        """
        return {
            "total_loaded": self.loading_stats["total_loaded"],
            "loading_errors": self.loading_stats["loading_errors"],
            "batches_processed": self.loading_stats["batches_processed"],
            "error_rate": self.loading_stats["loading_errors"]
            / max(1, self.loading_stats["total_loaded"]),
            "average_batch_size": self.loading_stats["total_loaded"]
            / max(1, self.loading_stats["batches_processed"]),
        }


class DataValidator:
    """Validates data consistency between old and new schemas."""

    def __init__(self, logger: logging.Logger | None = None):
        """Initialize data validator.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.validation_stats = {
            "total_validated": 0,
            "validation_errors": 0,
            "consistency_checks": 0,
            "consistency_failures": 0,
        }

    async def validate_batch_migration(
        self, original_batch: MigrationBatch, migrated_batch: MigrationBatch
    ) -> dict[str, Any]:
        """Validate that a migrated batch matches the original data.

        Args:
            original_batch: Original data batch
            migrated_batch: Migrated data batch

        Returns:
            Validation results
        """
        validation_results = {
            "batch_id": original_batch.batch_id,
            "record_count_match": len(original_batch.records)
            == len(migrated_batch.records),
            "data_consistency": True,
            "validation_errors": [],
            "consistency_score": 0.0,
        }

        try:
            # Check record count
            if not validation_results["record_count_match"]:
                validation_results["validation_errors"].append(
                    f"Record count mismatch: {len(original_batch.records)} vs {len(migrated_batch.records)}"
                )

            # Validate individual records
            consistent_records = 0
            total_records = min(
                len(original_batch.records), len(migrated_batch.records)
            )

            for i in range(total_records):
                is_consistent = await self._validate_record_consistency(
                    original_batch.records[i], migrated_batch.records[i]
                )

                if is_consistent:
                    consistent_records += 1
                else:
                    validation_results["validation_errors"].append(
                        f"Record {i} consistency check failed"
                    )

            # Calculate consistency score
            if total_records > 0:
                validation_results["consistency_score"] = (
                    consistent_records / total_records
                )

            validation_results["data_consistency"] = (
                validation_results["consistency_score"] > 0.95
            )

            # Update stats
            self.validation_stats["total_validated"] += total_records
            self.validation_stats["consistency_checks"] += total_records
            self.validation_stats["consistency_failures"] += (
                total_records - consistent_records
            )

            if not validation_results["data_consistency"]:
                self.validation_stats["validation_errors"] += 1

            self.logger.info(
                f"Validated batch {original_batch.batch_id}: "
                f"consistency {validation_results['consistency_score']:.2%}"
            )

        except Exception as e:
            validation_results["validation_errors"].append(
                f"Validation failed: {str(e)}"
            )
            validation_results["data_consistency"] = False
            self.validation_stats["validation_errors"] += 1
            self.logger.error(f"Batch validation failed: {e}")

        return validation_results

    async def _validate_record_consistency(
        self, original_record: dict[str, Any], migrated_record: dict[str, Any]
    ) -> bool:
        """Validate consistency between original and migrated record.

        Args:
            original_record: Original record
            migrated_record: Migrated record

        Returns:
            True if records are consistent
        """
        try:
            # Check timestamp consistency
            orig_timestamp = original_record.get("timestamp")
            migr_timestamp = migrated_record.get("timestamp")

            if orig_timestamp != migr_timestamp:
                return False

            # Check essential field preservation
            orig_fields = original_record.get("fields", {})
            migr_fields = migrated_record.get("fields", {})

            # Check that essential fields are preserved
            essential_fields = ["state", "value"]
            for field in essential_fields:
                if field in orig_fields:
                    if field not in migr_fields:
                        return False
                    if orig_fields[field] != migr_fields[field]:
                        return False

            # Check tag consistency (allowing for optimization)
            orig_tags = original_record.get("tags", {})
            migr_tags = migrated_record.get("tags", {})

            # Essential tags should be preserved or mapped
            if "entity_id" in orig_tags:
                # Entity ID might be hashed, so check if it exists in some form
                if "entity_id" not in migr_tags and "entity_id_hash" not in migr_tags:
                    return False

            return True

        except Exception:
            return False

    def get_validation_statistics(self) -> dict[str, Any]:
        """Get validation statistics.

        Returns:
            Validation statistics
        """
        return {
            "total_validated": self.validation_stats["total_validated"],
            "validation_errors": self.validation_stats["validation_errors"],
            "consistency_checks": self.validation_stats["consistency_checks"],
            "consistency_failures": self.validation_stats["consistency_failures"],
            "overall_consistency_rate": (
                self.validation_stats["consistency_checks"]
                - self.validation_stats["consistency_failures"]
            )
            / max(1, self.validation_stats["consistency_checks"]),
            "validation_success_rate": 1
            - (
                self.validation_stats["validation_errors"]
                / max(1, self.validation_stats["total_validated"])
            ),
        }


class MigrationRunner:
    """Orchestrates the complete migration process."""

    def __init__(
        self,
        batch_size: int = 1000,
        concurrent_batches: int = 4,
        logger: logging.Logger | None = None,
    ):
        """Initialize migration runner.

        Args:
            batch_size: Size of migration batches
            concurrent_batches: Number of concurrent batch processes
            logger: Logger instance
        """
        self.batch_size = batch_size
        self.concurrent_batches = concurrent_batches
        self.logger = logger or logging.getLogger(__name__)

        # Components
        self.extractor = DataExtractor(logger)
        self.transformer = DataTransformer(logger)
        self.loader = DataLoader(logger)
        self.validator = DataValidator(logger)

        # State
        self.migration_id = f"migration_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.processed_batches: list[MigrationBatch] = []
        self.validation_results: list[dict[str, Any]] = []

    async def run_full_migration(
        self,
        measurements: list[str] | None = None,
        time_range: tuple[datetime, datetime] | None = None,
        validate_percentage: float = 0.1,
    ) -> dict[str, Any]:
        """Run complete migration process.

        Args:
            measurements: List of measurements to migrate (None for all)
            time_range: Time range for migration
            validate_percentage: Percentage of data to validate

        Returns:
            Migration results
        """
        start_time = datetime.utcnow()

        try:
            self.logger.info(f"Starting migration {self.migration_id}")

            # Get measurements to migrate
            if measurements is None:
                measurements = await self.extractor.extract_measurements(time_range)

            # Process each measurement
            total_batches = 0
            for measurement in measurements:
                self.logger.info(f"Migrating measurement: {measurement}")

                # Get data statistics
                stats = await self.extractor.get_data_statistics(measurement)
                total_records = stats["total_records"]

                # Process in batches
                offset = 0
                while offset < total_records:
                    # Extract batch
                    batch = await self.extractor.extract_data_batch(
                        measurement, self.batch_size, offset, time_range
                    )

                    # Transform batch
                    transformed_batch = await self.transformer.transform_batch(batch)

                    # Load batch
                    load_success = await self.loader.load_batch(transformed_batch)

                    if not load_success:
                        self.logger.warning(
                            f"Batch loading had errors: {batch.batch_id}"
                        )

                    # Validate sample of batches
                    if total_batches % int(1 / validate_percentage) == 0:
                        validation_result = (
                            await self.validator.validate_batch_migration(
                                batch, transformed_batch
                            )
                        )
                        self.validation_results.append(validation_result)

                    self.processed_batches.append(transformed_batch)
                    total_batches += 1
                    offset += self.batch_size

            # Generate migration report
            end_time = datetime.utcnow()
            duration = end_time - start_time

            report = {
                "migration_id": self.migration_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": str(duration),
                "measurements_migrated": len(measurements),
                "total_batches": total_batches,
                "extraction_stats": {"measurements": measurements},
                "transformation_stats": self.transformer.get_transformation_statistics(),
                "loading_stats": self.loader.get_loading_statistics(),
                "validation_stats": self.validator.get_validation_statistics(),
                "validation_results": self.validation_results,
                "success": True,
            }

            # Save migration report
            await self._save_migration_report(report)

            self.logger.info(f"Migration completed successfully: {self.migration_id}")
            return report

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return {
                "migration_id": self.migration_id,
                "error": str(e),
                "success": False,
            }

    async def _save_migration_report(self, report: dict[str, Any]) -> None:
        """Save migration report to file.

        Args:
            report: Migration report data
        """
        report_file = f"migration_report_{self.migration_id}.json"

        async with aiofiles.open(report_file, "w") as f:
            await f.write(json.dumps(report, indent=2, default=str))

        self.logger.info(f"Migration report saved: {report_file}")
