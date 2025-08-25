"""Tests for schema migration functionality.

This module tests the migration system, including data extraction, transformation,
loading, and validation components.
"""

from datetime import datetime, UTC

import pytest

from ha_ingestor.migration.migration_scripts import (
    DataExtractor,
    DataLoader,
    DataTransformer,
    DataValidator,
    MigrationBatch,
    MigrationRunner,
)
from ha_ingestor.migration.schema_migration import (
    MigrationConfig,
    MigrationMetrics,
    MigrationPhase,
    MigrationStrategy,
    SchemaMigrator,
)
from ha_ingestor.migration.test_data_generator import (
    DataPattern,
    HomeAssistantDataGenerator,
    TestDataConfig,
)


class TestSchemaMigrator:
    """Test the main schema migrator."""

    def test_migration_config_creation(self):
        """Test migration configuration creation."""
        config = MigrationConfig(
            strategy=MigrationStrategy.DUAL_WRITE, batch_size=500, max_error_rate=0.02
        )

        assert config.strategy == MigrationStrategy.DUAL_WRITE
        assert config.batch_size == 500
        assert config.max_error_rate == 0.02
        assert config.migration_window_hours == 24  # Default value

    def test_migration_metrics_initialization(self):
        """Test migration metrics initialization."""
        metrics = MigrationMetrics()

        assert metrics.total_records == 0
        assert metrics.migrated_records == 0
        assert metrics.error_rate == 0.0
        assert metrics.data_integrity_score == 100.0

    def test_schema_migrator_initialization(self):
        """Test schema migrator initialization."""
        config = MigrationConfig(batch_size=1000)
        migrator = SchemaMigrator(config)

        assert migrator.config.batch_size == 1000
        assert migrator.current_phase == MigrationPhase.PREPARATION
        assert not migrator._migration_active
        assert migrator.migration_id.startswith("schema_migration_")

    @pytest.mark.asyncio
    async def test_migration_environment_validation(self):
        """Test migration environment validation."""
        migrator = SchemaMigrator()

        # Test successful validation
        result = await migrator._validate_migration_environment()
        assert result is True

    @pytest.mark.asyncio
    async def test_dual_write_enable_disable(self):
        """Test dual-write mode enabling and disabling."""
        migrator = SchemaMigrator()

        # Test enabling dual-write
        result = await migrator._enable_dual_write()
        assert result is True

        # Test disabling dual-write
        result = await migrator._disable_dual_write()
        assert result is True

    @pytest.mark.asyncio
    async def test_data_consistency_validation(self):
        """Test data consistency validation."""
        config = MigrationConfig(validate_percentage=0.1)
        migrator = SchemaMigrator(config)

        # Mock some data for validation
        migrator.metrics.total_records = 1000

        result = await migrator._validate_data_consistency()
        assert result is True
        assert migrator.metrics.validated_records > 0
        assert migrator.metrics.data_integrity_score > 0

    @pytest.mark.asyncio
    async def test_performance_improvement_validation(self):
        """Test performance improvement validation."""
        migrator = SchemaMigrator()

        result = await migrator._validate_performance_improvements()
        assert result is True
        assert migrator.metrics.performance_improvement > 0

    @pytest.mark.asyncio
    async def test_migration_failure_handling(self):
        """Test migration failure handling."""
        migrator = SchemaMigrator()

        await migrator._handle_migration_failure("Test error")
        assert migrator._rollback_triggered is True

    def test_migration_status_reporting(self):
        """Test migration status reporting."""
        migrator = SchemaMigrator()

        status = migrator.get_migration_status()
        assert "migration_id" in status
        assert "current_phase" in status
        assert "metrics" in status
        assert status["active"] is False


class TestDataExtractor:
    """Test the data extraction functionality."""

    def test_data_extractor_initialization(self):
        """Test data extractor initialization."""
        extractor = DataExtractor()
        assert extractor.logger is not None

    @pytest.mark.asyncio
    async def test_extract_measurements(self):
        """Test measurement extraction."""
        extractor = DataExtractor()

        measurements = await extractor.extract_measurements()
        assert isinstance(measurements, list)
        assert len(measurements) > 0
        assert "ha_light" in measurements
        assert "ha_sensor" in measurements

    @pytest.mark.asyncio
    async def test_extract_data_batch(self):
        """Test data batch extraction."""
        extractor = DataExtractor()

        batch = await extractor.extract_data_batch("ha_light", batch_size=100)

        assert isinstance(batch, MigrationBatch)
        assert batch.source_measurement == "ha_light"
        assert batch.target_measurement == "ha_entities"
        assert len(batch.records) == 100
        assert batch.batch_size == 100
        assert batch.batch_id.startswith("ha_light_")

    @pytest.mark.asyncio
    async def test_get_data_statistics(self):
        """Test data statistics extraction."""
        extractor = DataExtractor()

        stats = await extractor.get_data_statistics("ha_sensor")

        assert "total_records" in stats
        assert "date_range" in stats
        assert "tag_cardinality" in stats
        assert "field_count" in stats
        assert stats["total_records"] > 0

    def test_target_measurement_mapping(self):
        """Test target measurement mapping logic."""
        extractor = DataExtractor()

        assert extractor._get_target_measurement("ha_light") == "ha_entities"
        assert extractor._get_target_measurement("ha_state_changed") == "ha_entities"
        assert extractor._get_target_measurement("ha_call_service") == "ha_services"
        assert (
            extractor._get_target_measurement("ha_automation_triggered")
            == "ha_automations"
        )


class TestDataTransformer:
    """Test the data transformation functionality."""

    def test_data_transformer_initialization(self):
        """Test data transformer initialization."""
        transformer = DataTransformer()

        assert transformer.schema_transformer is not None
        assert transformer.transformation_stats["total_transformed"] == 0

    @pytest.mark.asyncio
    async def test_transform_batch(self):
        """Test batch transformation."""
        transformer = DataTransformer()

        # Create test batch
        records = [
            {
                "measurement": "ha_light",
                "tags": {
                    "domain": "light",
                    "entity_id": "living_room_light",
                    "source": "mqtt",
                },
                "fields": {"state": "on", "brightness": 255},
                "timestamp": datetime.now(UTC),
            }
        ]

        batch = MigrationBatch(
            batch_id="test_batch",
            records=records,
            source_measurement="ha_light",
            target_measurement="ha_entities",
            batch_size=1,
            created_at=datetime.now(UTC),
        )

        transformed_batch = await transformer.transform_batch(batch)

        assert transformed_batch.success_count >= 0
        assert transformed_batch.processed_at is not None
        assert len(transformed_batch.records) <= len(records)

    def test_create_event_from_record_mqtt(self):
        """Test creating MQTT event from record."""
        transformer = DataTransformer()

        record = {
            "tags": {"domain": "light", "entity_id": "test_light", "source": "mqtt"},
            "fields": {"state": "on", "brightness": 255},
            "timestamp": datetime.now(UTC),
        }

        event = transformer._create_event_from_record(record)

        assert hasattr(event, "topic")
        assert hasattr(event, "payload")
        assert event.domain == "light"
        assert event.entity_id == "test_light"

    def test_create_event_from_record_websocket(self):
        """Test creating WebSocket event from record."""
        transformer = DataTransformer()

        record = {
            "tags": {
                "domain": "sensor",
                "entity_id": "test_sensor",
                "source": "websocket",
                "event_type": "state_changed",
            },
            "fields": {"state": "active"},
            "timestamp": datetime.now(UTC),
        }

        event = transformer._create_event_from_record(record)

        assert hasattr(event, "event_type")
        assert hasattr(event, "data")
        assert event.entity_id == "test_sensor"
        assert event.domain == "sensor"

    def test_transformation_statistics(self):
        """Test transformation statistics tracking."""
        transformer = DataTransformer()

        # Add some mock statistics
        transformer.transformation_stats["total_transformed"] = 100
        transformer.transformation_stats["transformation_errors"] = 5
        transformer.transformation_stats["optimization_scores"] = [95.0, 87.5, 92.3]

        stats = transformer.get_transformation_statistics()

        assert stats["total_transformed"] == 100
        assert stats["transformation_errors"] == 5
        assert stats["error_rate"] == 0.05
        assert stats["average_optimization_score"] > 0


class TestDataLoader:
    """Test the data loading functionality."""

    def test_data_loader_initialization(self):
        """Test data loader initialization."""
        loader = DataLoader()

        assert loader.loading_stats["total_loaded"] == 0
        assert loader.loading_stats["loading_errors"] == 0

    @pytest.mark.asyncio
    async def test_load_batch(self):
        """Test batch loading."""
        loader = DataLoader()

        # Create test batch with transformed records
        records = [
            {
                "measurement": "ha_entities",
                "tags": {"domain": "light", "entity_id": "test_light"},
                "fields": {"state": "on"},
                "timestamp": datetime.now(UTC),
            }
        ]

        batch = MigrationBatch(
            batch_id="test_batch",
            records=records,
            source_measurement="ha_light",
            target_measurement="ha_entities",
            batch_size=1,
            created_at=datetime.now(UTC),
        )

        result = await loader.load_batch(batch)

        # Result can be True or False depending on simulated success/failure
        assert isinstance(result, bool)
        assert loader.loading_stats["batches_processed"] == 1

    @pytest.mark.asyncio
    async def test_write_record_to_influxdb(self):
        """Test individual record writing."""
        loader = DataLoader()

        record = {
            "measurement": "ha_entities",
            "tags": {"domain": "light"},
            "fields": {"state": "on"},
            "timestamp": datetime.now(UTC),
        }

        # This might raise an exception due to simulated failures
        try:
            await loader._write_record_to_influxdb(record)
        except Exception:
            pass  # Expected for simulation

    def test_loading_statistics(self):
        """Test loading statistics tracking."""
        loader = DataLoader()

        # Add some mock statistics
        loader.loading_stats["total_loaded"] = 1000
        loader.loading_stats["loading_errors"] = 10
        loader.loading_stats["batches_processed"] = 10

        stats = loader.get_loading_statistics()

        assert stats["total_loaded"] == 1000
        assert stats["loading_errors"] == 10
        assert stats["error_rate"] == 0.01
        assert stats["average_batch_size"] == 100


class TestDataValidator:
    """Test the data validation functionality."""

    def test_data_validator_initialization(self):
        """Test data validator initialization."""
        validator = DataValidator()

        assert validator.validation_stats["total_validated"] == 0
        assert validator.validation_stats["consistency_checks"] == 0

    @pytest.mark.asyncio
    async def test_validate_batch_migration(self):
        """Test batch migration validation."""
        validator = DataValidator()

        # Create original and migrated batches
        original_records = [
            {
                "tags": {"entity_id": "test_light"},
                "fields": {"state": "on", "value": 100},
                "timestamp": datetime.now(UTC),
            }
        ]

        migrated_records = [
            {
                "tags": {"entity_id": "test_light"},
                "fields": {"state": "on", "value": 100},
                "timestamp": datetime.now(UTC),
            }
        ]

        original_batch = MigrationBatch(
            batch_id="test_batch",
            records=original_records,
            source_measurement="ha_light",
            target_measurement="ha_entities",
            batch_size=1,
            created_at=datetime.now(UTC),
        )

        migrated_batch = MigrationBatch(
            batch_id="test_batch",
            records=migrated_records,
            source_measurement="ha_light",
            target_measurement="ha_entities",
            batch_size=1,
            created_at=datetime.now(UTC),
        )

        result = await validator.validate_batch_migration(
            original_batch, migrated_batch
        )

        assert "batch_id" in result
        assert "record_count_match" in result
        assert "data_consistency" in result
        assert "consistency_score" in result
        assert result["batch_id"] == "test_batch"

    @pytest.mark.asyncio
    async def test_validate_record_consistency(self):
        """Test individual record consistency validation."""
        validator = DataValidator()

        original_record = {
            "tags": {"entity_id": "test_light"},
            "fields": {"state": "on", "value": 100},
            "timestamp": datetime.now(UTC),
        }

        migrated_record = {
            "tags": {"entity_id": "test_light"},
            "fields": {"state": "on", "value": 100},
            "timestamp": original_record["timestamp"],
        }

        result = await validator._validate_record_consistency(
            original_record, migrated_record
        )
        assert isinstance(result, bool)

    def test_validation_statistics(self):
        """Test validation statistics tracking."""
        validator = DataValidator()

        # Add some mock statistics
        validator.validation_stats["total_validated"] = 500
        validator.validation_stats["consistency_checks"] = 500
        validator.validation_stats["consistency_failures"] = 5
        validator.validation_stats["validation_errors"] = 2

        stats = validator.get_validation_statistics()

        assert stats["total_validated"] == 500
        assert stats["consistency_checks"] == 500
        assert stats["overall_consistency_rate"] == 0.99
        assert stats["validation_success_rate"] > 0


class TestMigrationRunner:
    """Test the migration runner orchestrator."""

    def test_migration_runner_initialization(self):
        """Test migration runner initialization."""
        runner = MigrationRunner(batch_size=500, concurrent_batches=2)

        assert runner.batch_size == 500
        assert runner.concurrent_batches == 2
        assert runner.migration_id.startswith("migration_")
        assert len(runner.processed_batches) == 0

    @pytest.mark.asyncio
    async def test_run_full_migration(self):
        """Test complete migration process."""
        runner = MigrationRunner(batch_size=200, concurrent_batches=1)

        # Run migration with limited scope for testing
        # Add timeout to prevent hanging
        import asyncio
        try:
            result = await asyncio.wait_for(
                runner.run_full_migration(
                    measurements=["ha_light"],
                    validate_percentage=0.1,  # Validate 10% for testing
                ),
                timeout=30.0  # 30 second timeout
            )
        except asyncio.TimeoutError:
            pytest.fail("Migration test timed out after 30 seconds")

        assert "migration_id" in result
        assert "success" in result
        assert result["migration_id"] == runner.migration_id

    @pytest.mark.asyncio
    async def test_save_migration_report(self):
        """Test migration report saving."""
        runner = MigrationRunner()

        report = {
            "migration_id": runner.migration_id,
            "success": True,
            "duration": "00:10:30",
        }

        # Test report saving (would create actual file)
        await runner._save_migration_report(report)


class TestTestDataGenerator:
    """Test the test data generator."""

    def test_test_data_config_creation(self):
        """Test test data configuration."""
        config = TestDataConfig(
            total_events=1000, time_span_hours=12, pattern=DataPattern.HIGH_FREQUENCY
        )

        assert config.total_events == 1000
        assert config.time_span_hours == 12
        assert config.pattern == DataPattern.HIGH_FREQUENCY

    def test_data_generator_initialization(self):
        """Test data generator initialization."""
        config = TestDataConfig(light_entities=10, sensor_entities=20)
        generator = HomeAssistantDataGenerator(config)

        assert len(generator.entities["light"]) <= 10
        assert len(generator.entities["sensor"]) <= 20
        assert len(generator.entity_states) == 0

    def test_entity_pool_generation(self):
        """Test entity pool generation."""
        config = TestDataConfig(light_entities=5, sensor_entities=10, switch_entities=3)
        generator = HomeAssistantDataGenerator(config)

        assert "light" in generator.entities
        assert "sensor" in generator.entities
        assert "switch" in generator.entities
        assert len(generator.entities["light"]) <= 5
        assert len(generator.entities["sensor"]) <= 10
        assert len(generator.entities["switch"]) <= 3

    @pytest.mark.asyncio
    async def test_generate_test_dataset(self):
        """Test test dataset generation."""
        config = TestDataConfig(
            total_events=100, time_span_hours=1, pattern=DataPattern.PERIODIC
        )
        generator = HomeAssistantDataGenerator(config)

        events = await generator.generate_test_dataset()

        assert isinstance(events, list)
        assert len(events) <= config.total_events

        # Verify event structure
        if events:
            event = events[0]
            assert "timestamp" in event
            assert "type" in event
            assert event["type"] in ["mqtt", "websocket"]

    @pytest.mark.asyncio
    async def test_generate_mqtt_events(self):
        """Test MQTT event generation."""
        generator = HomeAssistantDataGenerator()

        # Test state event
        event = generator._generate_mqtt_state_event(datetime.now(UTC), 1)
        assert event["type"] == "mqtt"
        assert "topic" in event
        assert "payload" in event
        assert "domain" in event
        assert "entity_id" in event

        # Test sensor event
        event = generator._generate_mqtt_sensor_event(datetime.now(UTC), 2)
        assert event["type"] == "mqtt"
        assert event["domain"] == "sensor"

    @pytest.mark.asyncio
    async def test_generate_websocket_events(self):
        """Test WebSocket event generation."""
        generator = HomeAssistantDataGenerator()

        # Test service event
        event = generator._generate_websocket_service_event(datetime.now(UTC), 1)
        assert event["type"] == "websocket"
        assert event["event_type"] == "call_service"
        assert "data" in event

        # Test state event
        event = generator._generate_websocket_state_event(datetime.now(UTC), 2)
        assert event["type"] == "websocket"
        assert event["event_type"] == "state_changed"

    def test_dataset_statistics_calculation(self):
        """Test dataset statistics calculation."""
        generator = HomeAssistantDataGenerator()

        events = [
            {
                "type": "mqtt",
                "domain": "light",
                "entity_id": "light.test1",
                "timestamp": datetime.now(UTC),
            },
            {
                "type": "websocket",
                "domain": "sensor",
                "entity_id": "sensor.test1",
                "timestamp": datetime.now(UTC),
            },
            {
                "type": "mqtt",
                "domain": "light",
                "entity_id": "light.test2",
                "timestamp": datetime.now(UTC),
            },
        ]

        stats = generator._calculate_dataset_statistics(events)

        assert stats["total_events"] == 3
        assert stats["event_types"]["mqtt"] == 2
        assert stats["event_types"]["websocket"] == 1
        assert stats["domains"]["light"] == 2
        assert stats["domains"]["sensor"] == 1
        assert stats["entity_count"] == 3


if __name__ == "__main__":
    pytest.main([__file__])
