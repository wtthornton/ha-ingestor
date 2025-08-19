"""Tests for MQTT event models."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest

from ha_ingestor.models.mqtt_event import MQTTEvent


class TestMQTTEvent:
    """Test cases for MQTTEvent class."""

    def test_init_valid_event(self):
        """Test creating MQTTEvent with valid data."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
        )

        assert event.topic == "homeassistant/sensor/temperature/state"
        assert event.payload == "23.5"
        assert event.domain == "sensor"
        assert event.entity_id == "temperature"
        assert event.state == "23.5"
        assert event.source == "mqtt"
        assert event.attributes is None

    def test_init_with_attributes(self):
        """Test creating MQTTEvent with attributes."""
        attributes = {
            "friendly_name": "Temperature Sensor",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        }

        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
            attributes=attributes,
        )

        assert event.attributes == attributes

    def test_topic_validation_empty(self):
        """Test topic validation with empty topic."""
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            MQTTEvent(
                topic="",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="test",
            )

    def test_topic_validation_invalid_format(self):
        """Test topic validation with invalid format."""
        with pytest.raises(ValueError, match="Topic must follow pattern"):
            MQTTEvent(
                topic="invalid/topic/format",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="test",
            )

    def test_topic_validation_valid_format(self):
        """Test topic validation with valid format."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="test",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="test",
        )

        assert event.topic == "homeassistant/sensor/temperature/state"

    def test_payload_validation_empty(self):
        """Test payload validation with empty payload."""
        with pytest.raises(ValueError, match="Payload cannot be empty"):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="test",
            )

    def test_domain_validation_empty(self):
        """Test domain validation with empty domain."""
        with pytest.raises(ValueError, match="Domain cannot be empty"):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="",
                entity_id="test",
                state="test",
            )

    def test_domain_validation_common_domains(self):
        """Test domain validation with common Home Assistant domains."""
        common_domains = [
            "sensor",
            "binary_sensor",
            "switch",
            "light",
            "climate",
            "cover",
            "fan",
            "lock",
            "media_player",
            "camera",
            "device_tracker",
        ]

        for domain in common_domains:
            event = MQTTEvent(
                topic=f"homeassistant/{domain}/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain=domain,
                entity_id="test",
                state="test",
            )
            assert event.domain == domain

    def test_domain_validation_custom_domain(self):
        """Test domain validation with custom domain."""
        with patch("logging.getLogger") as mock_logger:
            event = MQTTEvent(
                topic="homeassistant/custom_domain/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="custom_domain",
                entity_id="test",
                state="test",
            )
            assert event.domain == "custom_domain"

    def test_entity_id_validation_empty(self):
        """Test entity ID validation with empty ID."""
        with pytest.raises(ValueError, match="Entity ID cannot be empty"):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="",
                state="test",
            )

    def test_entity_id_validation_invalid_chars(self):
        """Test entity ID validation with invalid characters."""
        with pytest.raises(
            ValueError, match="Entity ID must contain only lowercase letters"
        ):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="Test-Sensor",
                state="test",
            )

    def test_entity_id_validation_valid_format(self):
        """Test entity ID validation with valid format."""
        valid_ids = ["temperature_sensor", "light_1", "switch_2", "sensor123"]

        for entity_id in valid_ids:
            event = MQTTEvent(
                topic=f"homeassistant/sensor/{entity_id}/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id=entity_id,
                state="test",
            )
            assert event.entity_id == entity_id

    def test_state_validation_empty(self):
        """Test state validation with empty state."""
        with pytest.raises(ValueError, match="State cannot be empty"):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="",
            )

    def test_attributes_validation_not_dict(self):
        """Test attributes validation with non-dict value."""
        with pytest.raises(ValueError, match="Attributes must be a dictionary"):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="test",
                attributes="not_a_dict",
            )

    def test_attributes_validation_non_string_keys(self):
        """Test attributes validation with non-string keys."""
        with pytest.raises(ValueError, match="Attribute keys must be strings"):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="test",
                attributes={123: "value"},
            )

    def test_attributes_validation_non_serializable_values(self):
        """Test attributes validation with non-serializable values."""

        class NonSerializable:
            pass

        with pytest.raises(
            ValueError, match="Attribute value for 'test' is not JSON serializable"
        ):
            MQTTEvent(
                topic="homeassistant/sensor/test/state",
                payload="test",
                timestamp=datetime.utcnow(),
                domain="sensor",
                entity_id="test",
                state="test",
                attributes={"test": NonSerializable()},
            )

    def test_from_mqtt_message_simple_payload(self):
        """Test creating MQTTEvent from MQTT message with simple payload."""
        topic = "homeassistant/sensor/temperature/state"
        payload = "23.5"
        timestamp = datetime.utcnow()

        event = MQTTEvent.from_mqtt_message(topic, payload, timestamp)

        assert event.topic == topic
        assert event.payload == payload
        assert event.timestamp == timestamp
        assert event.domain == "sensor"
        assert event.entity_id == "temperature"
        assert event.state == "23.5"
        assert event.attributes is None

    def test_from_mqtt_message_json_payload(self):
        """Test creating MQTTEvent from MQTT message with JSON payload."""
        topic = "homeassistant/sensor/temperature/state"
        payload = json.dumps(
            {
                "state": "23.5",
                "attributes": {
                    "friendly_name": "Temperature Sensor",
                    "unit_of_measurement": "°C",
                },
            }
        )
        timestamp = datetime.utcnow()

        event = MQTTEvent.from_mqtt_message(topic, payload, timestamp)

        assert event.topic == topic
        assert event.payload == payload
        assert event.timestamp == timestamp
        assert event.domain == "sensor"
        assert event.entity_id == "temperature"
        assert event.state == "23.5"
        assert event.attributes == {
            "friendly_name": "Temperature Sensor",
            "unit_of_measurement": "°C",
        }

    def test_from_mqtt_message_invalid_topic_format(self):
        """Test creating MQTTEvent from MQTT message with invalid topic format."""
        topic = "invalid/topic/format"
        payload = "test"

        with pytest.raises(ValueError, match="Invalid topic format"):
            MQTTEvent.from_mqtt_message(topic, payload)

    def test_from_mqtt_message_default_timestamp(self):
        """Test creating MQTTEvent from MQTT message with default timestamp."""
        topic = "homeassistant/sensor/temperature/state"
        payload = "23.5"

        with patch("ha_ingestor.models.mqtt_event.datetime") as mock_datetime:
            mock_now = datetime.utcnow()
            mock_datetime.utcnow.return_value = mock_now

            event = MQTTEvent.from_mqtt_message(topic, payload)

            assert event.timestamp == mock_now

    def test_to_dict(self):
        """Test converting MQTTEvent to dictionary."""
        timestamp = datetime.utcnow()
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=timestamp,
            domain="sensor",
            entity_id="temperature",
            state="23.5",
            attributes={"friendly_name": "Temperature Sensor"},
        )

        result = event.to_dict()

        expected = {
            "topic": "homeassistant/sensor/temperature/state",
            "payload": "23.5",
            "timestamp": timestamp.isoformat(),
            "domain": "sensor",
            "entity_id": "temperature",
            "state": "23.5",
            "attributes": {"friendly_name": "Temperature Sensor"},
            "source": "mqtt",
        }

        assert result == expected

    def test_get_measurement_name(self):
        """Test getting InfluxDB measurement name."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
        )

        assert event.get_measurement_name() == "ha_sensor"

    def test_get_tags(self):
        """Test getting InfluxDB tags."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
            attributes={
                "friendly_name": "Temperature Sensor",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
            },
        )

        tags = event.get_tags()

        expected_tags = {
            "domain": "sensor",
            "entity_id": "temperature",
            "source": "mqtt",
            "friendly_name": "Temperature Sensor",
            "unit_of_measurement": "°C",
            "device_class": "temperature",
        }

        assert tags == expected_tags

    def test_get_tags_without_attributes(self):
        """Test getting InfluxDB tags without attributes."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
        )

        tags = event.get_tags()

        expected_tags = {
            "domain": "sensor",
            "entity_id": "temperature",
            "source": "mqtt",
        }

        assert tags == expected_tags

    def test_get_fields(self):
        """Test getting InfluxDB fields."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
            attributes={
                "friendly_name": "Temperature Sensor",
                "temperature": 23.5,
                "humidity": 45.2,
                "status": "online",
            },
        )

        fields = event.get_fields()

        expected_fields = {
            "state": "23.5",
            "payload": "23.5",
            "attr_temperature": 23.5,
            "attr_humidity": 45.2,
            "attr_status": "online",
        }

        assert fields == expected_fields

    def test_get_fields_without_attributes(self):
        """Test getting InfluxDB fields without attributes."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
        )

        fields = event.get_fields()

        expected_fields = {"state": "23.5", "payload": "23.5"}

        assert fields == expected_fields

    def test_get_fields_long_string_attribute(self):
        """Test getting InfluxDB fields with long string attribute."""
        long_string = "a" * 65  # Longer than InfluxDB field limit

        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload="23.5",
            timestamp=datetime.utcnow(),
            domain="sensor",
            entity_id="temperature",
            state="23.5",
            attributes={
                "friendly_name": "Temperature Sensor",
                "long_description": long_string,
            },
        )

        fields = event.get_fields()

        # Long string should not be included in fields
        assert "attr_long_description" not in fields
        assert "attr_friendly_name" in fields


if __name__ == "__main__":
    pytest.main([__file__])
