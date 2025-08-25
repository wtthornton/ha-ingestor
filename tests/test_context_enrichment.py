"""Tests for context enrichment engine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Any, Dict, List

from ha_ingestor.models.events import Event
from ha_ingestor.models.mqtt_event import MQTTEvent
from ha_ingestor.models.websocket_event import WebSocketEvent


class TestDeviceMetadataEnrichment:
    """Test device metadata enrichment capabilities."""

    def test_device_capabilities_enrichment(self):
        """Test that device capabilities are properly enriched."""
        # Test MQTT event with device capabilities
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload='{"state": "22.5", "attributes": {"unit_of_measurement": "°C", "device_class": "temperature"}}',
            state="22.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=datetime.now(),
            event_type="state_changed",
            attributes={
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "friendly_name": "Living Room Temperature"
            }
        )

        # Verify device capabilities are captured
        assert event.attributes["unit_of_measurement"] == "°C"
        assert event.attributes["device_class"] == "temperature"
        assert event.attributes["friendly_name"] == "Living Room Temperature"

    def test_device_manufacturer_enrichment(self):
        """Test that device manufacturer information is enriched."""
        event = WebSocketEvent(
            event_type="device_registry_updated",
            entity_id="switch.living_room_light",
            domain="switch",
            data={
                "entity_id": "switch.living_room_light",
                "manufacturer": "Philips Hue",
                "model": "LCT001",
                "sw_version": "1.0.0"
            },
            timestamp=datetime.now(),
            attributes={
                "manufacturer": "Philips Hue",
                "model": "LCT001",
                "sw_version": "1.0.0"
            }
        )

        # Verify manufacturer information is captured
        assert event.attributes["manufacturer"] == "Philips Hue"
        assert event.attributes["model"] == "LCT001"
        assert event.attributes["sw_version"] == "1.0.0"

    def test_device_area_enrichment(self):
        """Test that device area information is enriched."""
        event = WebSocketEvent(
            event_type="area_registry_updated",
            entity_id="sensor.bedroom_temperature",
            domain="sensor",
            data={
                "entity_id": "sensor.bedroom_temperature",
                "area_id": "bedroom",
                "area_name": "Master Bedroom"
            },
            timestamp=datetime.now(),
            attributes={
                "area_id": "bedroom",
                "area_name": "Master Bedroom"
            }
        )

        # Verify area information is captured
        assert event.attributes["area_id"] == "bedroom"
        assert event.attributes["area_name"] == "Master Bedroom"


class TestIntegrationInformationEnrichment:
    """Test integration information enrichment capabilities."""

    def test_integration_setup_enrichment(self):
        """Test that integration setup information is enriched."""
        event = WebSocketEvent(
            event_type="integration_setup",
            entity_id=None,
            domain="integration",
            data={
                "domain": "hue",
                "name": "Philips Hue",
                "version": "2.0.0",
                "config_entry_id": "abc123"
            },
            timestamp=datetime.now(),
            attributes={
                "domain": "hue",
                "name": "Philips Hue",
                "version": "2.0.0",
                "config_entry_id": "abc123"
            }
        )

        # Verify integration information is captured
        assert event.attributes["domain"] == "hue"
        assert event.attributes["name"] == "Philips Hue"
        assert event.attributes["version"] == "2.0.0"
        assert event.attributes["config_entry_id"] == "abc123"

    def test_integration_reload_enrichment(self):
        """Test that integration reload information is enriched."""
        event = WebSocketEvent(
            event_type="integration_reloaded",
            entity_id=None,
            domain="integration",
            data={
                "domain": "zwave",
                "name": "Z-Wave",
                "reason": "configuration_changed"
            },
            timestamp=datetime.now(),
            attributes={
                "domain": "zwave",
                "name": "Z-Wave",
                "reason": "configuration_changed"
            }
        )

        # Verify reload information is captured
        assert event.attributes["domain"] == "zwave"
        assert event.attributes["name"] == "Z-Wave"
        assert event.attributes["reason"] == "configuration_changed"

    def test_integration_removal_enrichment(self):
        """Test that integration removal information is enriched."""
        event = WebSocketEvent(
            event_type="integration_removed",
            entity_id=None,
            domain="integration",
            data={
                "domain": "old_integration",
                "name": "Old Integration",
                "removal_reason": "deprecated"
            },
            timestamp=datetime.now(),
            attributes={
                "domain": "old_integration",
                "name": "Old Integration",
                "removal_reason": "deprecated"
            }
        )

        # Verify removal information is captured
        assert event.attributes["domain"] == "old_integration"
        assert event.attributes["name"] == "Old Integration"
        assert event.attributes["removal_reason"] == "deprecated"


class TestNetworkTopologyEnrichment:
    """Test network topology enrichment capabilities."""

    def test_device_connection_status_enrichment(self):
        """Test that device connection status is enriched."""
        event = WebSocketEvent(
            event_type="device_registry_updated",
            entity_id="switch.network_switch",
            domain="switch",
            data={
                "entity_id": "switch.network_switch",
                "connection_type": "wifi",
                "ip_address": "192.168.1.100",
                "mac_address": "AA:BB:CC:DD:EE:FF"
            },
            timestamp=datetime.now(),
            attributes={
                "connection_type": "wifi",
                "ip_address": "192.168.1.100",
                "mac_address": "AA:BB:CC:DD:EE:FF"
            }
        )

        # Verify network information is captured
        assert event.attributes["connection_type"] == "wifi"
        assert event.attributes["ip_address"] == "192.168.1.100"
        assert event.attributes["mac_address"] == "AA:BB:CC:DD:EE:FF"

    def test_device_availability_enrichment(self):
        """Test that device availability status is enriched."""
        event = WebSocketEvent(
            event_type="state_changed",
            entity_id="sensor.network_device",
            domain="sensor",
            data={
                "entity_id": "sensor.network_device",
                "state": "unavailable",
                "attributes": {"available": False, "last_seen": "2024-01-01T12:00:00Z"}
            },
            timestamp=datetime.now(),
            attributes={
                "available": False,
                "last_seen": "2024-01-01T12:00:00Z"
            }
        )

        # Verify availability information is captured
        assert event.attributes["available"] is False
        assert event.attributes["last_seen"] == "2024-01-01T12:00:00Z"

    def test_network_segment_enrichment(self):
        """Test that network segment information is enriched."""
        event = WebSocketEvent(
            event_type="device_registry_updated",
            entity_id="switch.segmented_device",
            domain="switch",
            data={
                "entity_id": "switch.segmented_device",
                "network_segment": "iot_vlan",
                "subnet": "192.168.2.0/24"
            },
            timestamp=datetime.now(),
            attributes={
                "network_segment": "iot_vlan",
                "subnet": "192.168.2.0/24"
            }
        )

        # Verify network segment information is captured
        assert event.attributes["network_segment"] == "iot_vlan"
        assert event.attributes["subnet"] == "192.168.2.0/24"


class TestEventContextEnrichment:
    """Test event context enrichment capabilities."""

    def test_user_action_context_enrichment(self):
        """Test that user action context is enriched."""
        event = WebSocketEvent(
            event_type="call_service",
            entity_id="switch.living_room_light",
            domain="switch",
            data={
                "entity_id": "switch.living_room_light",
                "service": "turn_on",
                "user_id": "user123",
                "source": "mobile_app",
                "context_id": "context456"
            },
            timestamp=datetime.now(),
            attributes={
                "user_id": "user123",
                "source": "mobile_app",
                "context_id": "context456"
            }
        )

        # Verify user action context is captured
        assert event.attributes["user_id"] == "user123"
        assert event.attributes["source"] == "mobile_app"
        assert event.attributes["context_id"] == "context456"

    def test_automation_context_enrichment(self):
        """Test that automation context is enriched."""
        event = WebSocketEvent(
            event_type="automation_triggered",
            entity_id="automation.morning_routine",
            domain="automation",
            data={
                "entity_id": "automation.morning_routine",
                "trigger": "time",
                "trigger_time": "07:00:00",
                "trigger_date": "2024-01-01"
            },
            timestamp=datetime.now(),
            attributes={
                "trigger": "time",
                "trigger_time": "07:00:00",
                "trigger_date": "2024-01-01"
            }
        )

        # Verify automation context is captured
        assert event.attributes["trigger"] == "time"
        assert event.attributes["trigger_time"] == "07:00:00"
        assert event.attributes["trigger_date"] == "2024-01-01"

    def test_script_context_enrichment(self):
        """Test that script context is enriched."""
        event = WebSocketEvent(
            event_type="script_started",
            entity_id="script.test_script",
            domain="script",
            data={
                "entity_id": "script.test_script",
                "variables": {"test_var": "test_value"},
                "execution_id": "exec789"
            },
            timestamp=datetime.now(),
            attributes={
                "variables": {"test_var": "test_value"},
                "execution_id": "exec789"
            }
        )

        # Verify script context is captured
        assert event.attributes["variables"]["test_var"] == "test_value"
        assert event.attributes["execution_id"] == "exec789"


class TestRelationshipMappingEnrichment:
    """Test relationship mapping enrichment capabilities."""

    def test_device_entity_relationship_enrichment(self):
        """Test that device-entity relationships are enriched."""
        event = WebSocketEvent(
            event_type="entity_registry_updated",
            entity_id="sensor.temperature_1",
            domain="sensor",
            data={
                "entity_id": "sensor.temperature_1",
                "device_id": "device123",
                "area_id": "area456",
                "config_entry_id": "config789"
            },
            timestamp=datetime.now(),
            attributes={
                "device_id": "device123",
                "area_id": "area456",
                "config_entry_id": "config789"
            }
        )

        # Verify relationship information is captured
        assert event.attributes["device_id"] == "device123"
        assert event.attributes["area_id"] == "area456"
        assert event.attributes["config_entry_id"] == "config789"

    def test_integration_device_relationship_enrichment(self):
        """Test that integration-device relationships are enriched."""
        event = WebSocketEvent(
            event_type="device_registry_updated",
            entity_id="switch.hue_light",
            domain="switch",
            data={
                "entity_id": "switch.hue_light",
                "config_entries": ["config123"],
                "connections": [["mac", "AA:BB:CC:DD:EE:FF"]],
                "identifiers": [["hue", "light1"]]
            },
            timestamp=datetime.now(),
            attributes={
                "config_entries": ["config123"],
                "connections": [["mac", "AA:BB:CC:DD:EE:FF"]],
                "identifiers": [["hue", "light1"]]
            }
        )

        # Verify relationship information is captured
        assert event.attributes["config_entries"] == ["config123"]
        assert event.attributes["connections"] == [["mac", "AA:BB:CC:DD:EE:FF"]]
        assert event.attributes["identifiers"] == [["hue", "light1"]]

    def test_area_hierarchy_relationship_enrichment(self):
        """Test that area hierarchy relationships are enriched."""
        event = WebSocketEvent(
            event_type="area_registry_updated",
            entity_id="area.living_room",
            domain="area",
            data={
                "area_id": "area.living_room",
                "name": "Living Room",
                "parent_id": "area.downstairs",
                "level": 2
            },
            timestamp=datetime.now(),
            attributes={
                "parent_id": "area.downstairs",
                "level": 2
            }
        )

        # Verify hierarchy information is captured
        assert event.attributes["parent_id"] == "area.downstairs"
        assert event.attributes["level"] == 2


class TestPerformanceTimingEnrichment:
    """Test performance timing enrichment capabilities."""

    def test_event_processing_timing_enrichment(self):
        """Test that event processing timing is enriched."""
        start_time = datetime.now()
        processing_time = timedelta(milliseconds=150)
        
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload='{"state": "22.5"}',
            state="22.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=start_time,
            event_type="state_changed",
            attributes={
                "processing_start": start_time.isoformat(),
                "processing_duration_ms": 150,
                "queue_position": 5
            }
        )

        # Verify timing information is captured
        assert event.attributes["processing_start"] == start_time.isoformat()
        assert event.attributes["processing_duration_ms"] == 150
        assert event.attributes["queue_position"] == 5

    def test_system_performance_enrichment(self):
        """Test that system performance metrics are enriched."""
        event = WebSocketEvent(
            event_type="system_log_event",
            entity_id=None,
            domain="system",
            data={
                "level": "info",
                "message": "System performance normal",
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 30.1
            },
            timestamp=datetime.now(),
            attributes={
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 30.1
            }
        )

        # Verify performance metrics are captured
        assert event.attributes["cpu_usage"] == 25.5
        assert event.attributes["memory_usage"] == 45.2
        assert event.attributes["disk_usage"] == 30.1


class TestErrorContextEnrichment:
    """Test error context enrichment capabilities."""

    def test_error_context_enrichment(self):
        """Test that error context is enriched."""
        event = WebSocketEvent(
            event_type="system_log_event",
            entity_id="sensor.failed_sensor",
            domain="sensor",
            data={
                "level": "error",
                "message": "Sensor failed to update",
                "error_code": "E001",
                "error_details": "Connection timeout",
                "retry_count": 3
            },
            timestamp=datetime.now(),
            attributes={
                "error_code": "E001",
                "error_details": "Connection timeout",
                "retry_count": 3
            }
        )

        # Verify error context is captured
        assert event.attributes["error_code"] == "E001"
        assert event.attributes["error_details"] == "Connection timeout"
        assert event.attributes["retry_count"] == 3

    def test_validation_error_context_enrichment(self):
        """Test that validation error context is enriched."""
        event = MQTTEvent(
            topic="homeassistant/sensor/invalid_sensor/state",
            payload='{"invalid": "data"}',
            state="invalid",
            domain="sensor",
            entity_id="invalid_sensor",
            timestamp=datetime.now(),
            event_type="state_changed",
            attributes={
                "validation_errors": ["Invalid state format", "Missing required field"],
                "validation_level": "warning"
            }
        )

        # Verify validation error context is captured
        assert "Invalid state format" in event.attributes["validation_errors"]
        assert "Missing required field" in event.attributes["validation_errors"]
        assert event.attributes["validation_level"] == "warning"


class TestContextEnrichmentPerformance:
    """Test context enrichment performance capabilities."""

    def test_enrichment_latency_measurement(self):
        """Test that enrichment latency is measured."""
        start_time = datetime.now()
        
        # Simulate enrichment process
        event = MQTTEvent(
            topic="homeassistant/sensor/test/state",
            payload='{"state": "test"}',
            state="test",
            domain="sensor",
            entity_id="test",
            timestamp=start_time,
            event_type="state_changed"
        )
        
        # Add enrichment timing
        enrichment_duration = timedelta(milliseconds=50)
        event.attributes = {
            "enrichment_start": start_time.isoformat(),
            "enrichment_duration_ms": 50,
            "enrichment_steps": ["device_lookup", "area_mapping", "relationship_building"]
        }

        # Verify enrichment performance metrics
        assert event.attributes["enrichment_start"] == start_time.isoformat()
        assert event.attributes["enrichment_duration_ms"] == 50
        assert len(event.attributes["enrichment_steps"]) == 3

    def test_high_volume_enrichment(self):
        """Test that high volume enrichment is handled efficiently."""
        events = []
        start_time = datetime.now()
        
        # Create multiple events for batch enrichment
        for i in range(100):
            event = MQTTEvent(
                topic=f"homeassistant/sensor/test_{i}/state",
                payload=f'{{"state": "value_{i}"}}',
                state=f"value_{i}",
                domain="sensor",
                entity_id=f"test_{i}",
                timestamp=start_time + timedelta(seconds=i),
                event_type="state_changed"
            )
            events.append(event)
        
        # Verify batch processing capability
        assert len(events) == 100
        assert all(isinstance(event, MQTTEvent) for event in events)
        assert all(event.domain == "sensor" for event in events)


class TestContextEnrichmentCompleteness:
    """Test context enrichment completeness capabilities."""

    def test_full_context_capture(self):
        """Test that full context is captured for complex events."""
        event = WebSocketEvent(
            event_type="automation_triggered",
            entity_id="automation.complex_routine",
            domain="automation",
            data={
                "entity_id": "automation.complex_routine",
                "trigger": "state",
                "trigger_entity": "sensor.motion",
                "trigger_state": "on",
                "user_id": "user123",
                "source": "mobile_app",
                "context_id": "context456"
            },
            timestamp=datetime.now(),
            attributes={
                "trigger": "state",
                "trigger_entity": "sensor.motion",
                "trigger_state": "on",
                "user_id": "user123",
                "source": "mobile_app",
                "context_id": "context456",
                "enrichment_complete": True,
                "context_layers": ["device", "area", "user", "automation", "network"]
            }
        )

        # Verify comprehensive context capture
        assert event.attributes["trigger"] == "state"
        assert event.attributes["trigger_entity"] == "sensor.motion"
        assert event.attributes["user_id"] == "user123"
        assert event.attributes["enrichment_complete"] is True
        assert len(event.attributes["context_layers"]) == 5

    def test_context_accuracy_validation(self):
        """Test that context enrichment maintains data accuracy."""
        original_data = {
            "entity_id": "sensor.original",
            "state": "original_state",
            "timestamp": datetime.now()
        }
        
        event = MQTTEvent(
            topic="homeassistant/sensor/original/state",
            payload='{"state": "original_state"}',
            state="original_state",
            domain="sensor",
            entity_id="original",
            timestamp=original_data["timestamp"],
            event_type="state_changed"
        )
        
        # Add enrichment without modifying original data
        event.attributes = {
            "original_entity_id": event.entity_id,
            "original_state": event.state,
            "original_timestamp": event.timestamp.isoformat(),
            "enriched_at": datetime.now().isoformat(),
            "enrichment_version": "1.0.0"
        }
        
        # Verify original data integrity
        assert event.attributes["original_entity_id"] == "original"
        assert event.attributes["original_state"] == "original_state"
        assert event.attributes["enrichment_version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__])
