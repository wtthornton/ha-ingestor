"""Tests for schema optimization features.

This module tests the new optimized InfluxDB schema implementation,
including tag optimization, field optimization, and retention policies.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from ha_ingestor.influxdb.retention_policies import (
    CompressionLevel,
    RetentionPeriod,
    RetentionPolicy,
    RetentionPolicyManager,
)
from ha_ingestor.models.mqtt_event import MQTTEvent
from ha_ingestor.models.optimized_schema import (
    OptimizedFieldManager,
    OptimizedInfluxDBPoint,
    OptimizedTagManager,
    SchemaOptimizer,
)
from ha_ingestor.models.websocket_event import WebSocketEvent
from ha_ingestor.transformers.schema_transformer import SchemaTransformer


class TestOptimizedInfluxDBPoint:
    """Test the optimized InfluxDB point model."""

    def test_optimized_point_creation(self):
        """Test creating an optimized InfluxDB point."""
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"domain": "light", "entity_id": "living_room_light"},
            fields={"state": "on", "brightness": 255},
            metadata={"optimization_score": 95.0},
        )

        assert point.measurement == "ha_entities"
        assert len(point.tags) == 2
        assert len(point.fields) == 2
        assert point.metadata["optimization_score"] == 95.0

    def test_optimized_point_validation(self):
        """Test point validation rules."""
        # Test valid measurement
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"domain": "light"},
            fields={"state": "on"},
        )
        assert point.measurement == "ha_entities"

        # Test invalid measurement
        with pytest.raises(ValueError, match="Measurement name cannot be empty"):
            OptimizedInfluxDBPoint(
                measurement="",
                timestamp=datetime.utcnow(),
                tags={"domain": "light"},
                fields={"state": "on"},
            )

    def test_tag_validation(self):
        """Test tag validation rules."""
        # Test valid tags
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"domain": "light", "entity_id": "living_room_light"},
            fields={"state": "on"},
        )
        assert len(point.tags) == 2

        # Test invalid tag key - Pydantic will catch this before our validator
        with pytest.raises(Exception):  # Pydantic validation error
            OptimizedInfluxDBPoint(
                measurement="ha_entities",
                timestamp=datetime.utcnow(),
                tags={123: "light"},
                fields={"state": "on"},
            )

    def test_field_optimization(self):
        """Test field value optimization."""
        # Test string field truncation
        long_string = "x" * 300
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"domain": "light"},
            fields={"long_field": long_string},
        )

        # Long string should be hashed
        assert "hash_" in point.fields["long_field"]
        assert len(point.fields["long_field"]) < 300

    def test_optimization_score(self):
        """Test optimization score calculation."""
        # High cardinality tags should reduce score
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"entity_id": "very_long_entity_id_that_exceeds_normal_lengths"},
            fields={"state": "on"},
        )

        score = point.get_optimization_score()
        assert score < 100.0  # Should be penalized for long entity_id

    def test_line_protocol_conversion(self):
        """Test conversion to InfluxDB line protocol."""
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"domain": "light"},
            fields={"state": "on"},
        )

        line_protocol = point.to_line_protocol()
        assert "ha_entities" in line_protocol
        assert "domain=light" in line_protocol
        assert (
            'state="on"' in line_protocol
        )  # String fields are quoted in line protocol

    def test_size_estimation(self):
        """Test point size estimation."""
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"domain": "light"},
            fields={"state": "on"},
        )

        size = point.get_size_estimate()
        assert size > 0
        assert isinstance(size, int)


class TestOptimizedTagManager:
    """Test the tag optimization manager."""

    def test_tag_manager_initialization(self):
        """Test tag manager initialization."""
        manager = OptimizedTagManager(max_tag_cardinality=5000)
        assert manager.max_tag_cardinality == 5000

    def test_tag_optimization(self):
        """Test tag optimization logic."""
        manager = OptimizedTagManager(max_tag_cardinality=100)

        # Add tags multiple times to exceed cardinality
        for i in range(150):
            tags = {"entity_id": f"entity_{i}"}
            manager._track_tag_cardinality("entity_id", f"entity_{i}")

        # Now optimize tags - should hash high cardinality values
        optimized = manager.optimize_tags({"entity_id": "entity_0"})

        # Should have hashed some values
        assert any("_hash" in key for key in optimized.keys())

    def test_tag_cardinality_tracking(self):
        """Test tag cardinality tracking."""
        manager = OptimizedTagManager(max_tag_cardinality=100)

        # Track multiple tag values
        for i in range(50):
            manager._track_tag_cardinality("test_tag", f"value_{i}")

        stats = manager.get_tag_statistics()
        assert stats["tag_value_counts"]["test_tag"] == 50

    def test_high_cardinality_detection(self):
        """Test high cardinality tag detection."""
        manager = OptimizedTagManager(max_tag_cardinality=10)

        # Add more values than the limit
        for i in range(15):
            manager._track_tag_cardinality("test_tag", f"value_{i}")

        stats = manager.get_tag_statistics()
        assert len(stats["high_cardinality_tags"]) > 0
        assert stats["high_cardinality_tags"][0]["tag"] == "test_tag"


class TestOptimizedFieldManager:
    """Test the field optimization manager."""

    def test_field_manager_initialization(self):
        """Test field manager initialization."""
        manager = OptimizedFieldManager()
        assert manager.field_type_mappings == {}
        assert manager.field_compression_stats == {}

    def test_field_key_optimization(self):
        """Test field key optimization."""
        manager = OptimizedFieldManager()

        # Test key normalization
        optimized_key = manager._optimize_field_key("Attr_Device_Class")
        assert (
            optimized_key == "device_class"
        )  # Should remove attr_ prefix and normalize

        optimized_key = manager._optimize_field_key("data_event_type")
        assert optimized_key == "event_type"  # Should remove data_ prefix

    def test_field_value_optimization(self):
        """Test field value optimization."""
        manager = OptimizedFieldManager()

        # Test string compression
        long_string = "x" * 300
        optimized_value = manager._optimize_field_value(long_string)
        # String should be truncated, not hashed at this length
        assert len(optimized_value) < 300
        assert optimized_value.endswith("...")

        # Test numeric values (should remain unchanged)
        numeric_value = 42
        optimized_value = manager._optimize_field_value(numeric_value)
        assert optimized_value == 42

    def test_complex_type_handling(self):
        """Test handling of complex data types."""
        manager = OptimizedFieldManager()

        # Test list compression
        test_list = ["item1", "item2", "item3"] * 100  # Long list
        optimized_value = manager._optimize_field_value(test_list)
        assert "hash_" in optimized_value

        # Test dict compression
        test_dict = {"key": "value" * 200}  # Long string value
        optimized_value = manager._optimize_field_value(test_dict)
        assert "hash_" in optimized_value

    def test_field_statistics(self):
        """Test field statistics collection."""
        manager = OptimizedFieldManager()

        # Process some fields
        fields = {"string_field": "test", "numeric_field": 42, "long_field": "x" * 300}

        optimized_fields = manager.optimize_fields(fields)
        stats = manager.get_field_statistics()

        assert stats["total_fields"] == 3
        assert "string_compression" in stats["compression_stats"]


class TestSchemaOptimizer:
    """Test the main schema optimizer."""

    def test_schema_optimizer_initialization(self):
        """Test schema optimizer initialization."""
        config = {"max_tag_cardinality": 5000}
        optimizer = SchemaOptimizer(config)

        assert optimizer.config == config
        assert optimizer.tag_manager.max_tag_cardinality == 5000

    def test_point_optimization(self):
        """Test complete point optimization."""
        config = {"max_tag_cardinality": 100}
        optimizer = SchemaOptimizer(config)

        # Create a point with high cardinality tags
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"entity_id": "very_long_entity_id_that_exceeds_normal_lengths"},
            fields={"state": "on" * 100},  # Long field value
        )

        optimized_point = optimizer.optimize_point(point)

        # Should have optimization metadata
        assert "original_tags_count" in optimized_point.metadata
        assert "optimized_tags_count" in optimized_point.metadata
        assert "optimization_score" in optimized_point.metadata

    def test_optimization_statistics(self):
        """Test optimization statistics tracking."""
        config = {"max_tag_cardinality": 100}
        optimizer = SchemaOptimizer(config)

        # Process multiple points
        for i in range(5):
            point = OptimizedInfluxDBPoint(
                measurement="ha_entities",
                timestamp=datetime.utcnow(),
                tags={"entity_id": f"entity_{i}"},
                fields={"state": "on"},
            )
            optimizer.optimize_point(point)

        report = optimizer.get_optimization_report()
        assert report["optimization_stats"]["total_points_processed"] == 5

    def test_statistics_reset(self):
        """Test statistics reset functionality."""
        config = {"max_tag_cardinality": 100}
        optimizer = SchemaOptimizer(config)

        # Process a point
        point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=datetime.utcnow(),
            tags={"entity_id": "test"},
            fields={"state": "on"},
        )
        optimizer.optimize_point(point)

        # Reset statistics
        optimizer.reset_statistics()
        report = optimizer.get_optimization_report()
        # After reset, should have no processed points
        assert report["optimization_stats"]["total_points_processed"] == 0


class TestSchemaTransformer:
    """Test the schema transformer."""

    def test_transformer_initialization(self):
        """Test schema transformer initialization."""
        config = {"max_tag_cardinality": 1000}
        transformer = SchemaTransformer(
            name="test_transformer",
            config=config,
            measurement_consolidation=True,
            tag_optimization=True,
            field_optimization=True,
        )

        assert transformer.name == "test_transformer"
        assert transformer.measurement_consolidation is True
        assert transformer.tag_optimization is True
        assert transformer.field_optimization is True

    def test_mqtt_event_transformation(self):
        """Test MQTT event transformation."""
        transformer = SchemaTransformer("test_transformer")

        # Create a mock MQTT event
        mqtt_event = Mock(spec=MQTTEvent)
        mqtt_event.timestamp = datetime.utcnow()
        mqtt_event.domain = "light"
        mqtt_event.entity_id = "living_room_light"
        mqtt_event.state = "on"
        mqtt_event.attributes = {
            "brightness": 255,
            "friendly_name": "Living Room Light",
        }
        mqtt_event.payload = "test payload"
        mqtt_event.topic = "homeassistant/light/living_room_light/state"

        # Mock the get_tags and get_fields methods
        mqtt_event.get_tags.return_value = {
            "domain": "light",
            "entity_id": "living_room_light",
        }
        mqtt_event.get_fields.return_value = {"state": "on", "brightness": 255}

        result = transformer.transform(mqtt_event)

        assert result.success is True
        assert isinstance(result.data, OptimizedInfluxDBPoint)
        assert result.data.measurement == "ha_entities"  # Consolidated measurement

    def test_websocket_event_transformation(self):
        """Test WebSocket event transformation."""
        transformer = SchemaTransformer("test_transformer")

        # Create a mock WebSocket event
        websocket_event = Mock(spec=WebSocketEvent)
        websocket_event.timestamp = datetime.utcnow()
        websocket_event.event_type = "state_changed"
        websocket_event.entity_id = "living_room_light"
        websocket_event.domain = "light"
        websocket_event.data = {"context_id": "test_context"}

        # Mock the get_tags and get_fields methods
        websocket_event.get_tags.return_value = {
            "event_type": "state_changed",
            "entity_id": "living_room_light",
        }
        websocket_event.get_fields.return_value = {"event_type": "state_changed"}

        result = transformer.transform(websocket_event)

        assert result.success is True
        assert isinstance(result.data, OptimizedInfluxDBPoint)
        assert result.data.measurement == "ha_entities"  # Consolidated measurement

    def test_unsupported_data_type(self):
        """Test handling of unsupported data types."""
        transformer = SchemaTransformer("test_transformer")

        # Try to transform unsupported data
        result = transformer.transform("unsupported_string")

        assert result.success is False
        assert "Unsupported data type" in result.errors[0]

    def test_entity_group_extraction(self):
        """Test entity group extraction logic."""
        transformer = SchemaTransformer("test_transformer")

        # Test various entity ID patterns
        assert transformer._extract_entity_group("living_room_light") == "living_room"
        assert (
            transformer._extract_entity_group("sensor_kitchen_temperature")
            == "sensor_kitchen"
        )  # Pattern matches first underscore
        assert transformer._extract_entity_group("bedroom") == "bedroom"
        # "simple" is 6 characters, which is above the minimum threshold
        assert transformer._extract_entity_group("simple") == "simple"

    def test_event_categorization(self):
        """Test WebSocket event categorization."""
        transformer = SchemaTransformer("test_transformer")

        assert (
            transformer._categorize_websocket_event("state_changed") == "state_change"
        )
        assert transformer._categorize_websocket_event("call_service") == "service_call"
        assert (
            transformer._categorize_websocket_event("automation_triggered")
            == "automation"
        )
        assert transformer._categorize_websocket_event("unknown_event") == "other"


class TestRetentionPolicies:
    """Test retention policy management."""

    def test_retention_policy_creation(self):
        """Test retention policy creation."""
        policy = RetentionPolicy(
            name="test_policy",
            duration=RetentionPeriod.RECENT,
            compression_level=CompressionLevel.LIGHT,
        )

        assert policy.name == "test_policy"
        assert policy.duration == RetentionPeriod.RECENT
        assert policy.compression_level == CompressionLevel.LIGHT

    def test_policy_validation(self):
        """Test policy validation logic."""
        # Real-time policy should have no compression
        policy = RetentionPolicy(name="real_time", duration=RetentionPeriod.REAL_TIME)
        policy.__post_init__()

        assert policy.compression_level == CompressionLevel.NONE
        assert policy.aggregate_data is False

        # Historical policy should have balanced compression and aggregation
        policy = RetentionPolicy(name="historical", duration=RetentionPeriod.HISTORICAL)
        policy.__post_init__()

        assert policy.compression_level == CompressionLevel.BALANCED
        assert policy.aggregate_data is True

    def test_retention_policy_manager(self):
        """Test retention policy manager."""
        manager = RetentionPolicyManager()

        # Should have default policies
        assert "real_time" in manager.policies
        assert "recent" in manager.policies
        assert "historical" in manager.policies
        assert "long_term" in manager.policies
        assert "archive" in manager.policies

    def test_policy_selection(self):
        """Test policy selection logic."""
        manager = RetentionPolicyManager()

        # Create a test point
        point = OptimizedInfluxDBPoint(
            measurement="ha_metrics",
            timestamp=datetime.utcnow(),
            tags={"domain": "test"},
            fields={"value": 42},
        )

        # Metrics should get long-term policy
        policy = manager.get_policy_for_point(point)
        assert policy.name == "long_term"

        # System events should get archive policy
        point.measurement = "ha_system"
        policy = manager.get_policy_for_point(point)
        assert policy.name == "archive"

    def test_retention_violation_detection(self):
        """Test retention violation detection."""
        manager = RetentionPolicyManager()

        # Create old data points
        old_timestamp = datetime.utcnow() - timedelta(days=10)
        old_point = OptimizedInfluxDBPoint(
            measurement="ha_entities",
            timestamp=old_timestamp,
            tags={"domain": "test"},
            fields={"state": "old"},
        )

        violations = manager.check_retention_violations([old_point])

        # Should detect violations for data older than retention period
        assert len(violations) > 0
        assert violations[0]["violation_type"] == "retention_exceeded"

    def test_cleanup_operations(self):
        """Test cleanup operations."""
        manager = RetentionPolicyManager()

        # Test cleanup scheduling
        result = manager.cleanup_expired_data(force=False)

        # First call should not perform cleanup
        if not result["cleanup_performed"]:
            assert "cleanup_not_due" in result["reason"]

        # Force cleanup
        result = manager.cleanup_expired_data(force=True)
        assert result["cleanup_performed"] is True

    def test_policy_management(self):
        """Test policy management operations."""
        manager = RetentionPolicyManager()

        # Test policy update
        updates = {"compression_level": CompressionLevel.MAXIMUM}
        success = manager.update_policy("recent", updates)
        assert success is True

        # Test custom policy addition
        custom_policy = RetentionPolicy(
            name="custom_policy", duration=RetentionPeriod.LONG_TERM
        )
        success = manager.add_custom_policy(custom_policy)
        assert success is True
        assert "custom_policy" in manager.policies

        # Test policy removal
        success = manager.remove_policy("custom_policy")
        assert success is True
        assert "custom_policy" not in manager.policies


if __name__ == "__main__":
    pytest.main([__file__])
