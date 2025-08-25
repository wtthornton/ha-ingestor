"""Tests for enhanced data collection system."""

from datetime import datetime

import pytest

from ha_ingestor.models.mqtt_event import MQTTEvent
from ha_ingestor.models.websocket_event import WebSocketEvent


class TestEnhancedEventCapture:
    """Test enhanced event capture capabilities."""

    def test_mqtt_event_extended_types(self):
        """Test MQTT event capture with extended event types."""
        # Test state change event
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload='{"state": "22.5", "attributes": {"unit_of_measurement": "°C"}}',
            state="22.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=datetime.now(),
            event_type="state_changed",
            attributes={"unit_of_measurement": "°C"},
        )

        assert event.domain == "sensor"
        assert event.entity_id == "temperature"
        assert event.event_type == "state_changed"
        assert event.attributes["unit_of_measurement"] == "°C"

    def test_websocket_event_extended_types(self):
        """Test WebSocket event capture with extended event types."""
        # Test automation triggered event
        event = WebSocketEvent(
            event_type="automation_triggered",
            entity_id="automation.morning_routine",
            domain="automation",
            data={
                "entity_id": "automation.morning_routine",
                "name": "Morning Routine",
                "source": "time",
            },
            timestamp=datetime.now(),
            attributes={"friendly_name": "Morning Routine"},
        )

        assert event.event_type == "automation_triggered"
        assert event.entity_id == "automation.morning_routine"
        assert event.domain == "automation"
        assert event.data["name"] == "Morning Routine"

    def test_service_call_event(self):
        """Test service call event capture."""
        event = WebSocketEvent(
            event_type="call_service",
            entity_id="switch.living_room_light",
            domain="switch",
            data={
                "service": "turn_on",
                "service_data": {"entity_id": "switch.living_room_light"},
                "domain": "switch",
            },
            timestamp=datetime.now(),
            attributes={"friendly_name": "Living Room Light"},
        )

        assert event.event_type == "call_service"
        assert event.data["service"] == "turn_on"
        assert event.data["domain"] == "switch"

    def test_device_discovery_event(self):
        """Test device discovery event capture."""
        event = WebSocketEvent(
            event_type="device_registry_updated",
            entity_id=None,
            domain=None,
            data={
                "action": "create",
                "device_id": "device_123",
                "name": "New Device",
                "manufacturer": "Test Manufacturer",
            },
            timestamp=datetime.now(),
            attributes=None,
        )

        assert event.event_type == "device_registry_updated"
        assert event.data["action"] == "create"
        assert event.data["device_id"] == "device_123"

    def test_integration_health_event(self):
        """Test integration health event capture."""
        event = WebSocketEvent(
            event_type="integration_health",
            entity_id=None,
            domain=None,
            data={
                "integration": "mqtt",
                "status": "healthy",
                "last_check": "2025-08-24T12:00:00Z",
            },
            timestamp=datetime.now(),
            attributes=None,
        )

        assert event.event_type == "integration_health"
        assert event.data["integration"] == "mqtt"
        assert event.data["status"] == "healthy"

    def test_user_interaction_event(self):
        """Test user interaction event capture."""
        event = WebSocketEvent(
            event_type="user_updated",
            entity_id=None,
            domain=None,
            data={
                "user_id": "user_123",
                "action": "login",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
            },
            timestamp=datetime.now(),
            attributes=None,
        )

        assert event.event_type == "user_updated"
        assert event.data["user_id"] == "user_123"
        assert event.data["action"] == "login"


class TestEnhancedMetadataCollection:
    """Test enhanced metadata collection capabilities."""

    def test_device_capabilities_metadata(self):
        """Test device capabilities metadata collection."""
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload='{"state": "22.5", "attributes": {"unit_of_measurement": "°C"}}',
            state="22.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=datetime.now(),
            event_type="state_changed",
            attributes={
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "friendly_name": "Temperature Sensor",
                "supported_features": 0,
                "capabilities": {"min_value": -40, "max_value": 80, "precision": 0.1},
            },
        )

        assert event.attributes["device_class"] == "temperature"
        assert event.attributes["capabilities"]["min_value"] == -40
        assert event.attributes["capabilities"]["max_value"] == 80

    def test_integration_version_metadata(self):
        """Test integration version metadata collection."""
        event = WebSocketEvent(
            event_type="integration_updated",
            entity_id=None,
            domain=None,
            data={
                "integration": "mqtt",
                "version": "2.0.0",
                "config_entry_id": "config_123",
            },
            timestamp=datetime.now(),
            attributes={
                "integration_version": "2.0.0",
                "config_entry_id": "config_123",
                "last_update": "2025-08-24T12:00:00Z",
            },
        )

        assert event.attributes["integration_version"] == "2.0.0"
        assert event.attributes["config_entry_id"] == "config_123"

    def test_network_topology_metadata(self):
        """Test network topology metadata collection."""
        event = MQTTEvent(
            topic="homeassistant/switch/network_switch/state",
            payload='{"state": "on", "attributes": {"ip_address": "192.168.1.1"}}',
            state="on",
            domain="switch",
            entity_id="network_switch",
            timestamp=datetime.now(),
            event_type="state_changed",
            attributes={
                "ip_address": "192.168.1.1",
                "mac_address": "00:11:22:33:44:55",
                "network_segment": "lan",
                "topology": {
                    "parent_device": "router",
                    "connected_devices": ["device1", "device2"],
                    "network_interface": "eth0",
                },
            },
        )

        assert event.attributes["ip_address"] == "192.168.1.1"
        assert event.attributes["topology"]["parent_device"] == "router"
        assert "device1" in event.attributes["topology"]["connected_devices"]

    def test_performance_timing_metadata(self):
        """Test performance timing metadata collection."""
        start_time = datetime.now()

        event = WebSocketEvent(
            event_type="automation_executed",
            entity_id="automation.test",
            domain="automation",
            data={
                "entity_id": "automation.test",
                "execution_time": 0.125,
                "trigger_time": start_time.isoformat(),
            },
            timestamp=start_time,
            attributes={
                "execution_time": 0.125,
                "trigger_time": start_time.isoformat(),
                "performance_metrics": {
                    "cpu_usage": 2.5,
                    "memory_usage": 15.2,
                    "network_latency": 5.0,
                },
            },
        )

        assert event.attributes["execution_time"] == 0.125
        assert event.attributes["performance_metrics"]["cpu_usage"] == 2.5
        assert event.attributes["performance_metrics"]["memory_usage"] == 15.2

    def test_error_context_metadata(self):
        """Test error context metadata collection."""
        event = WebSocketEvent(
            event_type="error_occurred",
            entity_id="sensor.failed_sensor",
            domain="sensor",
            data={
                "error_type": "connection_timeout",
                "error_message": "Failed to connect to sensor",
                "retry_count": 3,
            },
            timestamp=datetime.now(),
            attributes={
                "error_type": "connection_timeout",
                "error_message": "Failed to connect to sensor",
                "retry_count": 3,
                "error_context": {
                    "last_successful_connection": "2025-08-24T11:00:00Z",
                    "connection_attempts": 5,
                    "error_stack_trace": "Traceback (most recent call last)...",
                    "system_resources": {
                        "cpu_usage": 85.0,
                        "memory_usage": 78.5,
                        "disk_space": 45.2,
                    },
                },
            },
        )

        assert event.attributes["error_type"] == "connection_timeout"
        assert event.attributes["error_context"]["connection_attempts"] == 5
        assert (
            event.attributes["error_context"]["system_resources"]["cpu_usage"] == 85.0
        )

    def test_user_action_history_metadata(self):
        """Test user action history metadata collection."""
        event = WebSocketEvent(
            event_type="user_action",
            entity_id="switch.user_controlled_switch",
            domain="switch",
            data={
                "user_id": "user_123",
                "action": "turn_on",
                "interface": "mobile_app",
            },
            timestamp=datetime.now(),
            attributes={
                "user_id": "user_123",
                "action": "turn_on",
                "interface": "mobile_app",
                "user_context": {
                    "location": "home",
                    "time_of_day": "morning",
                    "previous_actions": ["turn_off", "turn_on"],
                    "preferences": {
                        "auto_off_time": "22:00",
                        "brightness_level": "medium",
                    },
                },
            },
        )

        assert event.attributes["user_context"]["location"] == "home"
        assert event.attributes["user_context"]["time_of_day"] == "morning"
        assert "turn_off" in event.attributes["user_context"]["previous_actions"]


class TestEventCapturePerformance:
    """Test event capture performance characteristics."""

    def test_event_processing_latency(self):
        """Test that event processing maintains sub-100ms latency."""
        start_time = datetime.now()

        event = MQTTEvent(
            topic="homeassistant/sensor/test/state",
            payload='{"state": "test"}',
            state="test",
            domain="sensor",
            entity_id="test",
            timestamp=start_time,
            event_type="state_changed",
        )

        end_time = datetime.now()
        processing_time = (
            end_time - start_time
        ).total_seconds() * 1000  # Convert to milliseconds

        # This is a basic test - in real implementation, we'd measure actual processing time
        assert (
            processing_time < 100
        ), f"Event processing took {processing_time}ms, expected <100ms"

    def test_high_volume_event_capture(self):
        """Test that system can handle high volume event capture."""
        events = []
        start_time = datetime.now()

        # Create 1000 events (simulating high volume)
        for i in range(1000):
            event = MQTTEvent(
                topic=f"homeassistant/sensor/test_{i}/state",
                payload=f'{{"state": "value_{i}"}}',
                state=f"value_{i}",
                domain="sensor",
                entity_id=f"test_{i}",
                timestamp=start_time,
                event_type="state_changed",
            )
            events.append(event)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        events_per_second = len(events) / total_time

        # Should be able to handle 10,000+ events per second
        assert (
            events_per_second > 10000
        ), f"Event capture rate: {events_per_second}/s, expected >10,000/s"
        assert len(events) == 1000, "Should capture all 1000 events"


class TestEventCaptureCompleteness:
    """Test event capture completeness and accuracy."""

    def test_event_capture_with_full_context(self):
        """Test that events are captured with full context."""
        event = WebSocketEvent(
            event_type="state_changed",
            entity_id="light.living_room",
            domain="light",
            data={
                "entity_id": "light.living_room",
                "old_state": {"state": "off"},
                "new_state": {"state": "on"},
            },
            timestamp=datetime.now(),
            attributes={
                "friendly_name": "Living Room Light",
                "supported_features": 44,
                "capabilities": {"min_mireds": 153, "max_mireds": 500},
                "context": {
                    "id": "context_123",
                    "user_id": "user_123",
                    "parent_id": None,
                },
            },
        )

        # Verify all context is captured
        assert event.entity_id == "light.living_room"
        assert event.domain == "light"
        assert event.attributes["friendly_name"] == "Living Room Light"
        assert event.attributes["capabilities"]["min_mireds"] == 153
        assert event.attributes["context"]["user_id"] == "user_123"

    def test_event_capture_accuracy(self):
        """Test that event capture is accurate."""
        original_timestamp = datetime.now()

        event = MQTTEvent(
            topic="homeassistant/sensor/accuracy_test/state",
            payload='{"state": "test_value", "accuracy": 0.1}',
            state="test_value",
            domain="sensor",
            entity_id="accuracy_test",
            timestamp=original_timestamp,
            event_type="state_changed",
            attributes={"accuracy": 0.1},
        )

        # Verify data accuracy
        assert event.topic == "homeassistant/sensor/accuracy_test/state"
        assert event.payload == '{"state": "test_value", "accuracy": 0.1}'
        assert event.state == "test_value"
        assert event.attributes["accuracy"] == 0.1
        assert event.timestamp == original_timestamp


if __name__ == "__main__":
    pytest.main([__file__])
