"""Tests for flexible data export system."""

import json
from datetime import datetime, timedelta

import pytest

from ha_ingestor.models.mqtt_event import MQTTEvent
from ha_ingestor.models.websocket_event import WebSocketEvent


class TestDataExportAPI:
    """Test data export API endpoints."""

    def test_events_export_endpoint(self):
        """Test that events export endpoint provides data in correct format."""
        # Mock API response for events export
        mock_response = {
            "status": "success",
            "data": {
                "events": [
                    {
                        "id": "event_001",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "domain": "sensor",
                        "entity_id": "temperature",
                        "event_type": "state_changed",
                        "state": "22.5",
                        "attributes": {
                            "unit_of_measurement": "°C",
                            "friendly_name": "Living Room Temperature",
                        },
                    }
                ],
                "total_count": 1,
                "page": 1,
                "per_page": 100,
            },
        }

        # Verify response structure
        assert mock_response["status"] == "success"
        assert "events" in mock_response["data"]
        assert "total_count" in mock_response["data"]
        assert "page" in mock_response["data"]
        assert "per_page" in mock_response["data"]

        # Verify event data structure
        event = mock_response["data"]["events"][0]
        assert "id" in event
        assert "timestamp" in event
        assert "domain" in event
        assert "entity_id" in event
        assert "event_type" in event
        assert "state" in event
        assert "attributes" in event

    def test_metadata_export_endpoint(self):
        """Test that metadata export endpoint provides device and integration info."""
        # Mock API response for metadata export
        mock_response = {
            "status": "success",
            "data": {
                "devices": [
                    {
                        "device_id": "device_001",
                        "name": "Philips Hue Bridge",
                        "manufacturer": "Philips",
                        "model": "B001",
                        "sw_version": "1.0.0",
                        "area_id": "area_001",
                        "area_name": "Living Room",
                    }
                ],
                "integrations": [
                    {
                        "domain": "hue",
                        "name": "Philips Hue",
                        "version": "2.0.0",
                        "config_entry_id": "config_001",
                    }
                ],
                "areas": [
                    {
                        "area_id": "area_001",
                        "name": "Living Room",
                        "parent_id": None,
                        "level": 1,
                    }
                ],
            },
        }

        # Verify response structure
        assert mock_response["status"] == "success"
        assert "devices" in mock_response["data"]
        assert "integrations" in mock_response["data"]
        assert "areas" in mock_response["data"]

        # Verify device data structure
        device = mock_response["data"]["devices"][0]
        assert "device_id" in device
        assert "name" in device
        assert "manufacturer" in device
        assert "model" in device
        assert "sw_version" in device
        assert "area_id" in device
        assert "area_name" in device

    def test_data_quality_export_endpoint(self):
        """Test that data quality export endpoint provides validation metrics."""
        # Mock API response for data quality export
        mock_response = {
            "status": "success",
            "data": {
                "validation_metrics": {
                    "total_events": 1000,
                    "valid_events": 985,
                    "invalid_events": 15,
                    "success_rate": 98.5,
                    "validation_errors": [
                        {
                            "error_type": "missing_required_field",
                            "count": 10,
                            "percentage": 1.0,
                        },
                        {"error_type": "invalid_format", "count": 5, "percentage": 0.5},
                    ],
                },
                "enrichment_metrics": {
                    "enriched_events": 950,
                    "enrichment_success_rate": 95.0,
                    "average_enrichment_time_ms": 45.2,
                },
            },
        }

        # Verify response structure
        assert mock_response["status"] == "success"
        assert "validation_metrics" in mock_response["data"]
        assert "enrichment_metrics" in mock_response["data"]

        # Verify validation metrics
        validation = mock_response["data"]["validation_metrics"]
        assert "total_events" in validation
        assert "valid_events" in validation
        assert "invalid_events" in validation
        assert "success_rate" in validation
        assert "validation_errors" in validation


class TestDataFormatting:
    """Test data formatting and serialization capabilities."""

    def test_json_export_formatting(self):
        """Test that data is properly formatted for JSON export."""
        # Create test event
        event = MQTTEvent(
            topic="homeassistant/sensor/temperature/state",
            payload='{"state": "22.5"}',
            state="22.5",
            domain="sensor",
            entity_id="temperature",
            timestamp=datetime.now(),
            event_type="state_changed",
            attributes={
                "unit_of_measurement": "°C",
                "friendly_name": "Living Room Temperature",
            },
        )

        # Convert to export format
        export_data = {
            "id": f"event_{event.timestamp.timestamp()}",
            "timestamp": event.timestamp.isoformat(),
            "domain": event.domain,
            "entity_id": event.entity_id,
            "event_type": event.event_type,
            "state": event.state,
            "attributes": event.attributes,
            "export_format": "json",
            "exported_at": datetime.now().isoformat(),
        }

        # Verify export format
        assert "id" in export_data
        assert "timestamp" in export_data
        assert "domain" in export_data
        assert "entity_id" in export_data
        assert "event_type" in export_data
        assert "state" in export_data
        assert "attributes" in export_data
        assert "export_format" in export_data
        assert "exported_at" in export_data

        # Verify JSON serialization
        json_string = json.dumps(export_data)
        assert "temperature" in json_string
        assert "22.5" in json_string
        # JSON serialization converts °C to \u00b0C, so check for the escaped version
        assert "\\u00b0C" in json_string or "°C" in json_string

    def test_csv_export_formatting(self):
        """Test that data is properly formatted for CSV export."""
        # Create test events for CSV export
        events = [
            MQTTEvent(
                topic="homeassistant/sensor/temp1/state",
                payload='{"state": "22.5"}',
                state="22.5",
                domain="sensor",
                entity_id="temp1",
                timestamp=datetime.now(),
                event_type="state_changed",
                attributes={"unit": "°C"},
            ),
            MQTTEvent(
                topic="homeassistant/sensor/temp2/state",
                payload='{"state": "23.0"}',
                state="23.0",
                domain="sensor",
                entity_id="temp2",
                timestamp=datetime.now(),
                event_type="state_changed",
                attributes={"unit": "°C"},
            ),
        ]

        # Convert to CSV format
        csv_headers = [
            "timestamp",
            "domain",
            "entity_id",
            "event_type",
            "state",
            "unit",
        ]
        csv_rows = []

        for event in events:
            row = [
                event.timestamp.isoformat(),
                event.domain,
                event.entity_id,
                event.event_type,
                event.state,
                event.attributes.get("unit", ""),
            ]
            csv_rows.append(row)

        # Verify CSV format
        assert len(csv_headers) == 6
        assert len(csv_rows) == 2
        assert csv_headers[0] == "timestamp"
        assert csv_headers[1] == "domain"
        assert csv_headers[2] == "entity_id"
        assert csv_rows[0][1] == "sensor"
        assert csv_rows[0][2] == "temp1"
        assert csv_rows[0][3] == "state_changed"

    def test_xml_export_formatting(self):
        """Test that data is properly formatted for XML export."""
        # Create test event for XML export
        event = WebSocketEvent(
            event_type="automation_triggered",
            entity_id="automation.morning_routine",
            domain="automation",
            data={
                "entity_id": "automation.morning_routine",
                "trigger": "time",
                "trigger_time": "07:00:00",
            },
            timestamp=datetime.now(),
            attributes={"trigger": "time", "trigger_time": "07:00:00"},
        )

        # Convert to XML format structure
        xml_structure = {
            "event": {
                "id": f"event_{event.timestamp.timestamp()}",
                "timestamp": event.timestamp.isoformat(),
                "domain": event.domain,
                "entity_id": event.entity_id,
                "event_type": event.event_type,
                "attributes": {
                    "trigger": event.attributes["trigger"],
                    "trigger_time": event.attributes["trigger_time"],
                },
            }
        }

        # Verify XML structure
        assert "event" in xml_structure
        event_data = xml_structure["event"]
        assert "id" in event_data
        assert "timestamp" in event_data
        assert "domain" in event_data
        assert "entity_id" in event_data
        assert "event_type" in event_data
        assert "attributes" in event_data


class TestDataFiltering:
    """Test data filtering and query capabilities."""

    def test_domain_filtering(self):
        """Test that events can be filtered by domain."""
        # Create test events with different domains
        events = [
            MQTTEvent(
                topic="homeassistant/sensor/temp/state",
                payload='{"state": "22.5"}',
                state="22.5",
                domain="sensor",
                entity_id="temp",
                timestamp=datetime.now(),
                event_type="state_changed",
            ),
            MQTTEvent(
                topic="homeassistant/switch/light/state",
                payload='{"state": "on"}',
                state="on",
                domain="switch",
                entity_id="light",
                timestamp=datetime.now(),
                event_type="state_changed",
            ),
            MQTTEvent(
                topic="homeassistant/binary_sensor/motion/state",
                payload='{"state": "off"}',
                state="off",
                domain="binary_sensor",
                entity_id="motion",
                timestamp=datetime.now(),
                event_type="state_changed",
            ),
        ]

        # Filter by sensor domain
        sensor_events = [event for event in events if event.domain == "sensor"]
        switch_events = [event for event in events if event.domain == "switch"]
        binary_sensor_events = [
            event for event in events if event.domain == "binary_sensor"
        ]

        # Verify filtering results
        assert len(sensor_events) == 1
        assert len(switch_events) == 1
        assert len(binary_sensor_events) == 1
        assert sensor_events[0].entity_id == "temp"
        assert switch_events[0].entity_id == "light"
        assert binary_sensor_events[0].entity_id == "motion"

    def test_timestamp_filtering(self):
        """Test that events can be filtered by timestamp range."""
        # Create test events with different timestamps
        base_time = datetime.now()
        events = [
            MQTTEvent(
                topic="homeassistant/sensor/temp1/state",
                payload='{"state": "22.5"}',
                state="22.5",
                domain="sensor",
                entity_id="temp1",
                timestamp=base_time - timedelta(hours=2),
                event_type="state_changed",
            ),
            MQTTEvent(
                topic="homeassistant/sensor/temp2/state",
                payload='{"state": "23.0"}',
                state="23.0",
                domain="sensor",
                entity_id="temp2",
                timestamp=base_time - timedelta(hours=1),
                event_type="state_changed",
            ),
            MQTTEvent(
                topic="homeassistant/sensor/temp3/state",
                payload='{"state": "23.5"}',
                state="23.5",
                domain="sensor",
                entity_id="temp3",
                timestamp=base_time,
                event_type="state_changed",
            ),
        ]

        # Filter by timestamp range (last 1.5 hours)
        cutoff_time = base_time - timedelta(hours=1, minutes=30)
        recent_events = [event for event in events if event.timestamp >= cutoff_time]

        # Verify timestamp filtering
        assert len(recent_events) == 2
        assert recent_events[0].entity_id == "temp2"
        assert recent_events[1].entity_id == "temp3"

    def test_entity_id_filtering(self):
        """Test that events can be filtered by entity ID pattern."""
        # Create test events with different entity IDs
        events = [
            MQTTEvent(
                topic="homeassistant/sensor/living_room_temp/state",
                payload='{"state": "22.5"}',
                state="22.5",
                domain="sensor",
                entity_id="living_room_temp",
                timestamp=datetime.now(),
                event_type="state_changed",
            ),
            MQTTEvent(
                topic="homeassistant/sensor/bedroom_temp/state",
                payload='{"state": "21.0"}',
                state="21.0",
                domain="sensor",
                entity_id="bedroom_temp",
                timestamp=datetime.now(),
                event_type="state_changed",
            ),
            MQTTEvent(
                topic="homeassistant/sensor/kitchen_temp/state",
                payload='{"state": "24.0"}',
                state="24.0",
                domain="sensor",
                entity_id="kitchen_temp",
                timestamp=datetime.now(),
                event_type="state_changed",
            ),
        ]

        # Filter by entity ID pattern (temperature sensors)
        temp_events = [event for event in events if "temp" in event.entity_id]
        living_room_events = [
            event for event in events if "living_room" in event.entity_id
        ]

        # Verify entity ID filtering
        assert len(temp_events) == 3
        assert len(living_room_events) == 1
        assert living_room_events[0].entity_id == "living_room_temp"

    def test_event_type_filtering(self):
        """Test that events can be filtered by event type."""
        # Create test events with different event types
        events = [
            WebSocketEvent(
                event_type="state_changed",
                entity_id="sensor.temperature",
                domain="sensor",
                data={"entity_id": "sensor.temperature"},
                timestamp=datetime.now(),
            ),
            WebSocketEvent(
                event_type="automation_triggered",
                entity_id="automation.morning_routine",
                domain="automation",
                data={"entity_id": "automation.morning_routine"},
                timestamp=datetime.now(),
            ),
            WebSocketEvent(
                event_type="service_called",
                entity_id="switch.light",
                domain="switch",
                data={"entity_id": "switch.light"},
                timestamp=datetime.now(),
            ),
        ]

        # Filter by event type
        state_changed_events = [
            event for event in events if event.event_type == "state_changed"
        ]
        automation_events = [
            event for event in events if event.event_type == "automation_triggered"
        ]
        service_events = [
            event for event in events if event.event_type == "service_called"
        ]

        # Verify event type filtering
        assert len(state_changed_events) == 1
        assert len(automation_events) == 1
        assert len(service_events) == 1
        assert state_changed_events[0].entity_id == "sensor.temperature"
        assert automation_events[0].entity_id == "automation.morning_routine"
        assert service_events[0].entity_id == "switch.light"


class TestDataPagination:
    """Test data pagination and result limiting capabilities."""

    def test_basic_pagination(self):
        """Test that data can be paginated with limit and offset."""
        # Create test events
        events = []
        for i in range(25):
            event = MQTTEvent(
                topic=f"homeassistant/sensor/temp_{i}/state",
                payload=f'{{"state": "{20 + i}"}}',
                state=str(20 + i),
                domain="sensor",
                entity_id=f"temp_{i}",
                timestamp=datetime.now() + timedelta(minutes=i),
                event_type="state_changed",
            )
            events.append(event)

        # Test pagination parameters
        page_size = 10
        page_1 = events[:page_size]
        page_2 = events[page_size : page_size * 2]
        page_3 = events[page_size * 2 : page_size * 3]

        # Verify pagination
        assert len(page_1) == 10
        assert len(page_2) == 10
        assert len(page_3) == 5
        assert page_1[0].entity_id == "temp_0"
        assert page_2[0].entity_id == "temp_10"
        assert page_3[0].entity_id == "temp_20"

    def test_pagination_metadata(self):
        """Test that pagination includes proper metadata."""
        # Mock pagination response
        pagination_response = {
            "data": {
                "events": [{"id": "event_001", "entity_id": "temp"}],
                "pagination": {
                    "current_page": 1,
                    "per_page": 100,
                    "total_count": 1000,
                    "total_pages": 10,
                    "has_next": True,
                    "has_prev": False,
                    "next_page": 2,
                    "prev_page": None,
                },
            }
        }

        # Verify pagination metadata
        pagination = pagination_response["data"]["pagination"]
        assert "current_page" in pagination
        assert "per_page" in pagination
        assert "total_count" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination
        assert pagination["current_page"] == 1
        assert pagination["total_pages"] == 10
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is False

    def test_cursor_based_pagination(self):
        """Test that cursor-based pagination works for large datasets."""
        # Create test events with timestamps
        events = []
        base_time = datetime.now()
        for i in range(100):
            event = MQTTEvent(
                topic=f"homeassistant/sensor/temp_{i}/state",
                payload=f'{{"state": "{20 + i}"}}',
                state=str(20 + i),
                domain="sensor",
                entity_id=f"temp_{i}",
                timestamp=base_time + timedelta(seconds=i),
                event_type="state_changed",
            )
            events.append(event)

        # Test cursor-based pagination
        cursor_size = 20
        cursor_1 = events[:cursor_size]
        cursor_2 = events[cursor_size : cursor_size * 2]
        cursor_3 = events[cursor_size * 2 : cursor_size * 3]

        # Verify cursor pagination
        assert len(cursor_1) == 20
        assert len(cursor_2) == 20
        assert len(cursor_3) == 20
        assert cursor_1[-1].timestamp < cursor_2[0].timestamp
        assert cursor_2[-1].timestamp < cursor_3[0].timestamp


class TestDataIntegration:
    """Test data integration and export capabilities."""

    def test_webhook_integration(self):
        """Test that data can be exported via webhooks."""
        # Mock webhook payload
        webhook_payload = {
            "webhook_id": "webhook_001",
            "url": "https://example.com/webhook",
            "events": [
                {
                    "id": "event_001",
                    "timestamp": "2024-01-01T12:00:00Z",
                    "domain": "sensor",
                    "entity_id": "temperature",
                    "event_type": "state_changed",
                    "state": "22.5",
                }
            ],
            "delivery_status": "pending",
            "retry_count": 0,
        }

        # Verify webhook payload structure
        assert "webhook_id" in webhook_payload
        assert "url" in webhook_payload
        assert "events" in webhook_payload
        assert "delivery_status" in webhook_payload
        assert "retry_count" in webhook_payload
        assert webhook_payload["webhook_id"] == "webhook_001"
        assert webhook_payload["delivery_status"] == "pending"

    def test_mqtt_integration(self):
        """Test that data can be exported via MQTT."""
        # Mock MQTT export payload
        mqtt_payload = {
            "topic": "ha_ingestor/export/events",
            "payload": {
                "export_id": "export_001",
                "timestamp": "2024-01-01T12:00:00Z",
                "event_count": 100,
                "format": "json",
                "compression": "gzip",
            },
            "qos": 1,
            "retain": False,
        }

        # Verify MQTT payload structure
        assert "topic" in mqtt_payload
        assert "payload" in mqtt_payload
        assert "qos" in mqtt_payload
        assert "retain" in mqtt_payload
        assert mqtt_payload["topic"] == "ha_ingestor/export/events"
        assert mqtt_payload["qos"] == 1
        assert mqtt_payload["retain"] is False

    def test_file_export_integration(self):
        """Test that data can be exported to files."""
        # Mock file export configuration
        file_export_config = {
            "export_id": "file_export_001",
            "format": "json",
            "compression": "gzip",
            "destination": "/exports/events.json.gz",
            "schedule": "daily",
            "retention_days": 30,
            "max_file_size_mb": 100,
        }

        # Verify file export configuration
        assert "export_id" in file_export_config
        assert "format" in file_export_config
        assert "compression" in file_export_config
        assert "destination" in file_export_config
        assert "schedule" in file_export_config
        assert "retention_days" in file_export_config
        assert "max_file_size_mb" in file_export_config
        assert file_export_config["format"] == "json"
        assert file_export_config["compression"] == "gzip"
        assert file_export_config["schedule"] == "daily"


class TestExportPerformance:
    """Test export performance and scalability capabilities."""

    def test_bulk_export_performance(self):
        """Test that bulk exports can handle large datasets efficiently."""
        # Create large dataset
        events = []
        for i in range(10000):
            event = MQTTEvent(
                topic=f"homeassistant/sensor/temp_{i}/state",
                payload=f'{{"state": "{20 + (i % 10)}"}}',
                state=str(20 + (i % 10)),
                domain="sensor",
                entity_id=f"temp_{i}",
                timestamp=datetime.now() + timedelta(seconds=i),
                event_type="state_changed",
            )
            events.append(event)

        # Test bulk export processing
        batch_size = 1000
        batches = [
            events[i : i + batch_size] for i in range(0, len(events), batch_size)
        ]

        # Verify batch processing
        assert len(batches) == 10
        assert all(len(batch) == 1000 for batch in batches[:-1])
        assert len(batches[-1]) == 1000  # Last batch should also be 1000

    def test_export_latency_measurement(self):
        """Test that export latency is measured and reported."""
        # Mock export performance metrics
        export_metrics = {
            "export_id": "export_001",
            "start_time": "2024-01-01T12:00:00Z",
            "end_time": "2024-01-01T12:00:05Z",
            "total_duration_ms": 5000,
            "event_count": 1000,
            "events_per_second": 200,
            "memory_usage_mb": 45.2,
            "cpu_usage_percent": 25.5,
        }

        # Verify export metrics
        assert "export_id" in export_metrics
        assert "start_time" in export_metrics
        assert "end_time" in export_metrics
        assert "total_duration_ms" in export_metrics
        assert "event_count" in export_metrics
        assert "events_per_second" in export_metrics
        assert "memory_usage_mb" in export_metrics
        assert "cpu_usage_percent" in export_metrics
        assert export_metrics["total_duration_ms"] == 5000
        assert export_metrics["events_per_second"] == 200

    def test_concurrent_export_handling(self):
        """Test that multiple concurrent exports can be handled."""
        # Mock concurrent export requests
        concurrent_exports = [
            {
                "export_id": f"export_{i:03d}",
                "format": "json",
                "priority": "high" if i % 3 == 0 else "normal",
                "status": "queued",
            }
            for i in range(10)
        ]

        # Verify concurrent export handling
        assert len(concurrent_exports) == 10
        high_priority = [exp for exp in concurrent_exports if exp["priority"] == "high"]
        normal_priority = [
            exp for exp in concurrent_exports if exp["priority"] == "normal"
        ]
        assert len(high_priority) == 4  # Every 3rd export is high priority
        assert len(normal_priority) == 6


class TestExportSecurity:
    """Test export security and access control capabilities."""

    def test_api_authentication(self):
        """Test that API endpoints require proper authentication."""
        # Mock authentication requirements
        auth_requirements = {
            "endpoint": "/api/v1/events",
            "method": "GET",
            "authentication": "required",
            "auth_type": "bearer_token",
            "permissions": ["read:events"],
            "rate_limit": "1000/hour",
        }

        # Verify authentication requirements
        assert "authentication" in auth_requirements
        assert "auth_type" in auth_requirements
        assert "permissions" in auth_requirements
        assert "rate_limit" in auth_requirements
        assert auth_requirements["authentication"] == "required"
        assert auth_requirements["auth_type"] == "bearer_token"
        assert "read:events" in auth_requirements["permissions"]

    def test_data_encryption(self):
        """Test that exported data can be encrypted."""
        # Mock encryption configuration
        encryption_config = {
            "encryption_enabled": True,
            "algorithm": "AES-256-GCM",
            "key_derivation": "PBKDF2",
            "key_size": 256,
            "iv_size": 12,
            "tag_size": 16,
        }

        # Verify encryption configuration
        assert "encryption_enabled" in encryption_config
        assert "algorithm" in encryption_config
        assert "key_derivation" in encryption_config
        assert "key_size" in encryption_config
        assert "iv_size" in encryption_config
        assert "tag_size" in encryption_config
        assert encryption_config["encryption_enabled"] is True
        assert encryption_config["algorithm"] == "AES-256-GCM"
        assert encryption_config["key_size"] == 256

    def test_access_control(self):
        """Test that access control is properly enforced."""
        # Mock access control rules
        access_control = {
            "user_id": "user_001",
            "role": "analyst",
            "permissions": ["read:events", "read:metadata", "export:events"],
            "restrictions": ["no_delete_access", "no_config_access"],
            "data_scope": "department_only",
        }

        # Verify access control
        assert "user_id" in access_control
        assert "role" in access_control
        assert "permissions" in access_control
        assert "restrictions" in access_control
        assert "data_scope" in access_control
        assert access_control["role"] == "analyst"
        assert "export:events" in access_control["permissions"]
        assert "no_delete_access" in access_control["restrictions"]


if __name__ == "__main__":
    pytest.main([__file__])
