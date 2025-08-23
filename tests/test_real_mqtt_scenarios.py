"""Tests for real MQTT scenarios and validation."""

import json
import time
from datetime import datetime
from unittest.mock import Mock

import pytest

from ha_ingestor.mqtt.topic_patterns import (
    TopicPattern,
    TopicPatternManager,
)


class TestRealHomeAssistantScenarios:
    """Test with real Home Assistant MQTT scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()
        self.message_log = []

    def test_home_assistant_automation_workflow(self):
        """Test complete Home Assistant automation workflow."""
        # Set up typical HA automation patterns
        automation_patterns = [
            TopicPattern(
                "homeassistant/+/+/state",
                priority=1,
                description="General state changes",
            ),
            TopicPattern(
                "homeassistant/sensor/+/state",
                priority=2,
                description="Sensor state changes",
            ),
            TopicPattern(
                "homeassistant/binary_sensor/+/state",
                priority=2,
                description="Binary sensor changes",
            ),
            TopicPattern(
                "homeassistant/light/+/state",
                priority=2,
                description="Light state changes",
            ),
            TopicPattern(
                "homeassistant/switch/+/state",
                priority=2,
                description="Switch state changes",
            ),
            TopicPattern(
                "homeassistant/climate/+/state",
                priority=2,
                description="Climate control changes",
            ),
            TopicPattern(
                "homeassistant/+/+/attributes",
                priority=1,
                description="Entity attributes",
            ),
            TopicPattern(
                "homeassistant/+/+/+/config",
                priority=3,
                description="Entity configuration",
            ),
            TopicPattern(
                "homeassistant/+/+/+/+/availability",
                priority=2,
                description="Entity availability",
            ),
        ]

        for pattern in automation_patterns:
            self.manager.add_pattern(pattern)

        # Create realistic automation handlers
        def temperature_monitor(topic: str, payload: str, **kwargs):
            """Monitor temperature sensors and trigger alerts."""
            try:
                temp = float(payload)
                if temp > 30:
                    self.message_log.append(
                        f"ALERT: High temperature {temp}°C on {topic}"
                    )
                elif temp < 10:
                    self.message_log.append(
                        f"ALERT: Low temperature {temp}°C on {topic}"
                    )
                else:
                    self.message_log.append(
                        f"INFO: Normal temperature {temp}°C on {topic}"
                    )
            except ValueError:
                self.message_log.append(
                    f"ERROR: Invalid temperature value '{payload}' on {topic}"
                )

        def motion_detector(topic: str, payload: str, **kwargs):
            """Handle motion sensor events."""
            if payload == "on":
                self.message_log.append(f"MOTION: Motion detected on {topic}")
            else:
                self.message_log.append(f"MOTION: Motion cleared on {topic}")

        def light_controller(topic: str, payload: str, **kwargs):
            """Handle light state changes."""
            if payload == "on":
                self.message_log.append(f"LIGHT: Light turned on {topic}")
            else:
                self.message_log.append(f"LIGHT: Light turned off {topic}")

        def climate_monitor(topic: str, payload: str, **kwargs):
            """Monitor climate control systems."""
            self.message_log.append(f"CLIMATE: {topic} = {payload}")

        # Subscribe to patterns
        temp_sub = self.manager.subscribe_to_pattern(
            "homeassistant/sensor/+/state",
            callback=temperature_monitor,
            filters={"topic_regex": r".*temperature.*"},
        )

        motion_sub = self.manager.subscribe_to_pattern(
            "homeassistant/binary_sensor/+/state",
            callback=motion_detector,
            filters={"topic_regex": r".*motion.*"},
        )

        light_sub = self.manager.subscribe_to_pattern(
            "homeassistant/light/+/state", callback=light_controller
        )

        climate_sub = self.manager.subscribe_to_pattern(
            "homeassistant/climate/+/state", callback=climate_monitor
        )

        # Simulate realistic HA automation sequence
        automation_sequence = [
            # Morning routine
            ("homeassistant/sensor/living_room_temperature/state", "22.5"),
            ("homeassistant/binary_sensor/front_door_motion/state", "on"),
            ("homeassistant/light/living_room_ceiling/state", "on"),
            ("homeassistant/climate/thermostat/state", "heat"),
            # Midday
            ("homeassistant/sensor/outdoor_temperature/state", "28.3"),
            ("homeassistant/sensor/living_room_temperature/state", "24.1"),
            ("homeassistant/binary_sensor/front_door_motion/state", "off"),
            # Evening
            ("homeassistant/sensor/living_room_temperature/state", "21.8"),
            ("homeassistant/light/living_room_ceiling/state", "off"),
            ("homeassistant/light/table_lamp/state", "on"),
            ("homeassistant/climate/thermostat/state", "cool"),
            # Night
            ("homeassistant/sensor/bedroom_temperature/state", "20.2"),
            ("homeassistant/light/table_lamp/state", "off"),
            ("homeassistant/binary_sensor/bedroom_motion/state", "off"),
        ]

        # Process automation sequence
        for topic, payload in automation_sequence:
            routes = self.manager.route_message(topic, payload)

            # Execute callbacks
            for subscription_id, callback in routes:
                try:
                    callback(topic, payload)
                except Exception as e:
                    self.message_log.append(
                        f"ERROR: Callback failed for {subscription_id}: {e}"
                    )

        # Verify automation workflow
        assert len(self.message_log) > 0, "No automation messages were processed"

        # Check for specific automation events
        temp_alerts = [msg for msg in self.message_log if "ALERT:" in msg]
        motion_events = [msg for msg in self.message_log if "MOTION:" in msg]
        light_events = [msg for msg in self.message_log if "LIGHT:" in msg]
        climate_events = [msg for msg in self.message_log if "CLIMATE:" in msg]

        assert (
            len(temp_alerts) > 0
        ), "Temperature monitoring should have generated alerts"
        assert len(motion_events) > 0, "Motion detection should have generated events"
        assert len(light_events) > 0, "Light control should have generated events"
        assert len(climate_events) > 0, "Climate control should have generated events"

        # Verify metrics
        metrics = self.manager.get_metrics()
        assert metrics["total_patterns"] == 9
        assert metrics["total_subscriptions"] == 4
        assert metrics["pattern_matches"] >= len(automation_sequence)
        assert metrics["topic_routes"] >= len(automation_sequence)

    def test_home_assistant_device_discovery(self):
        """Test Home Assistant device discovery and configuration."""
        # Set up device discovery patterns
        discovery_patterns = [
            TopicPattern(
                "homeassistant/+/+/config",
                priority=3,
                description="Device configuration",
            ),
            TopicPattern(
                "homeassistant/+/+/+/config",
                priority=4,
                description="Extended device config",
            ),
            TopicPattern(
                "homeassistant/+/+/+/+/config",
                priority=5,
                description="Advanced device config",
            ),
        ]

        for pattern in discovery_patterns:
            self.manager.add_pattern(pattern)

        # Create device discovery handler
        discovered_devices = []

        def device_discovery_handler(topic: str, payload: str, **kwargs):
            """Handle device discovery messages."""
            try:
                config = json.loads(payload)
                device_info = {
                    "topic": topic,
                    "name": config.get("name", "Unknown"),
                    "type": config.get("type", "Unknown"),
                    "platform": config.get("platform", "Unknown"),
                    "discovered_at": datetime.now().isoformat(),
                }
                discovered_devices.append(device_info)
            except json.JSONDecodeError:
                discovered_devices.append(
                    {
                        "topic": topic,
                        "error": "Invalid JSON payload",
                        "discovered_at": datetime.now().isoformat(),
                    }
                )

        # Subscribe to discovery patterns
        discovery_sub = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/config", callback=device_discovery_handler
        )

        # Simulate device discovery messages
        discovery_messages = [
            (
                "homeassistant/sensor/living_room_temperature/config",
                json.dumps(
                    {
                        "name": "Living Room Temperature",
                        "type": "sensor",
                        "platform": "mqtt",
                        "unit_of_measurement": "°C",
                        "device_class": "temperature",
                    }
                ),
            ),
            (
                "homeassistant/light/living_room_ceiling/config",
                json.dumps(
                    {
                        "name": "Living Room Ceiling Light",
                        "type": "light",
                        "platform": "mqtt",
                        "brightness": True,
                        "color_temp": True,
                    }
                ),
            ),
            (
                "homeassistant/binary_sensor/front_door_motion/config",
                json.dumps(
                    {
                        "name": "Front Door Motion",
                        "type": "binary_sensor",
                        "platform": "mqtt",
                        "device_class": "motion",
                    }
                ),
            ),
            (
                "homeassistant/climate/thermostat/config",
                json.dumps(
                    {
                        "name": "Smart Thermostat",
                        "type": "climate",
                        "platform": "mqtt",
                        "modes": ["heat", "cool", "off"],
                        "temperature_unit": "C",
                    }
                ),
            ),
        ]

        # Process discovery messages
        for topic, payload in discovery_messages:
            routes = self.manager.route_message(topic, payload)

            for subscription_id, callback in routes:
                callback(topic, payload)

        # Verify device discovery
        assert (
            len(discovered_devices) == 4
        ), f"Expected 4 devices, got {len(discovered_devices)}"

        # Check specific device types
        sensor_devices = [d for d in discovered_devices if d.get("type") == "sensor"]
        light_devices = [d for d in discovered_devices if d.get("type") == "light"]
        binary_sensor_devices = [
            d for d in discovered_devices if d.get("type") == "binary_sensor"
        ]
        climate_devices = [d for d in discovered_devices if d.get("type") == "climate"]

        assert len(sensor_devices) == 1, "Should have discovered 1 sensor device"
        assert len(light_devices) == 1, "Should have discovered 1 light device"
        assert (
            len(binary_sensor_devices) == 1
        ), "Should have discovered 1 binary sensor device"
        assert len(climate_devices) == 1, "Should have discovered 1 climate device"

    def test_home_assistant_availability_monitoring(self):
        """Test Home Assistant device availability monitoring."""
        # Set up availability patterns
        availability_patterns = [
            TopicPattern(
                "homeassistant/+/+/+/availability",
                priority=2,
                description="Device availability",
            ),
            TopicPattern(
                "homeassistant/+/+/+/+/availability",
                priority=3,
                description="Extended availability",
            ),
        ]

        for pattern in availability_patterns:
            self.manager.add_pattern(pattern)

        # Create availability monitoring handler
        availability_status = {}

        def availability_handler(topic: str, payload: str, **kwargs):
            """Handle device availability updates."""
            device_id = topic.split("/")[2]  # Extract device ID from topic
            availability_status[device_id] = {
                "status": payload,
                "last_update": datetime.now().isoformat(),
                "topic": topic,
            }

        # Subscribe to availability patterns
        availability_sub = self.manager.subscribe_to_pattern(
            "homeassistant/+/+/+/availability", callback=availability_handler
        )

        # Simulate availability updates
        availability_messages = [
            ("homeassistant/sensor/living_room_temperature/availability", "online"),
            ("homeassistant/light/living_room_ceiling/availability", "online"),
            ("homeassistant/binary_sensor/front_door_motion/availability", "offline"),
            ("homeassistant/climate/thermostat/availability", "online"),
            ("homeassistant/sensor/living_room_temperature/availability", "offline"),
            ("homeassistant/binary_sensor/front_door_motion/availability", "online"),
        ]

        # Process availability messages
        for topic, payload in availability_messages:
            routes = self.manager.route_message(topic, payload)

            for subscription_id, callback in routes:
                callback(topic, payload)

        # Verify availability monitoring
        assert len(availability_status) > 0, "No availability updates were processed"

        # Check final availability states
        online_devices = [
            d for d in availability_status.values() if d["status"] == "online"
        ]
        offline_devices = [
            d for d in availability_status.values() if d["status"] == "offline"
        ]

        assert len(online_devices) > 0, "Should have some online devices"
        assert len(offline_devices) > 0, "Should have some offline devices"


class TestMultiTenantMQTTScenarios:
    """Test multi-tenant MQTT scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()
        self.tenant_messages = {"tenant1": [], "tenant2": [], "tenant3": []}

    def test_multi_tenant_isolation(self):
        """Test complete tenant isolation in MQTT patterns."""
        # Set up tenant-specific patterns
        tenant_patterns = [
            # Tenant 1 patterns
            TopicPattern(
                "tenant1/+/+/state", priority=1, description="Tenant 1 state changes"
            ),
            TopicPattern(
                "tenant1/sensor/+/state",
                priority=2,
                description="Tenant 1 sensor states",
            ),
            TopicPattern(
                "tenant1/light/+/state", priority=2, description="Tenant 1 light states"
            ),
            # Tenant 2 patterns
            TopicPattern(
                "tenant2/+/+/state", priority=1, description="Tenant 2 state changes"
            ),
            TopicPattern(
                "tenant2/sensor/+/state",
                priority=2,
                description="Tenant 2 sensor states",
            ),
            TopicPattern(
                "tenant2/switch/+/state",
                priority=2,
                description="Tenant 2 switch states",
            ),
            # Tenant 3 patterns
            TopicPattern(
                "tenant3/+/+/state", priority=1, description="Tenant 3 state changes"
            ),
            TopicPattern(
                "tenant3/climate/+/state",
                priority=2,
                description="Tenant 3 climate states",
            ),
        ]

        for pattern in tenant_patterns:
            self.manager.add_pattern(pattern)

        # Create tenant-specific handlers
        def tenant1_handler(topic: str, payload: str, **kwargs):
            """Handle Tenant 1 messages."""
            self.tenant_messages["tenant1"].append(
                {
                    "topic": topic,
                    "payload": payload,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        def tenant2_handler(topic: str, payload: str, **kwargs):
            """Handle Tenant 2 messages."""
            self.tenant_messages["tenant2"].append(
                {
                    "topic": topic,
                    "payload": payload,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        def tenant3_handler(topic: str, payload: str, **kwargs):
            """Handle Tenant 3 messages."""
            self.tenant_messages["tenant3"].append(
                {
                    "topic": topic,
                    "payload": payload,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Subscribe to tenant patterns
        t1_sub = self.manager.subscribe_to_pattern("tenant1/+/+/state", tenant1_handler)
        t2_sub = self.manager.subscribe_to_pattern("tenant2/+/+/state", tenant2_handler)
        t3_sub = self.manager.subscribe_to_pattern("tenant3/+/+/state", tenant3_handler)

        # Simulate multi-tenant message flow
        multi_tenant_messages = [
            # Tenant 1 messages
            ("tenant1/sensor/temperature/state", "25.5"),
            ("tenant1/light/living_room/state", "on"),
            ("tenant1/sensor/humidity/state", "60.0"),
            # Tenant 2 messages
            ("tenant2/sensor/temperature/state", "22.0"),
            ("tenant2/switch/garage/state", "off"),
            ("tenant2/sensor/pressure/state", "1013.25"),
            # Tenant 3 messages
            ("tenant3/climate/thermostat/state", "heat"),
            ("tenant3/climate/humidifier/state", "on"),
            # Mixed tenant messages
            ("tenant1/sensor/temperature/state", "26.1"),
            ("tenant2/switch/security/state", "armed"),
            ("tenant3/climate/thermostat/state", "cool"),
        ]

        # Process all messages
        for topic, payload in multi_tenant_messages:
            routes = self.manager.route_message(topic, payload)

            for subscription_id, callback in routes:
                callback(topic, payload)

        # Verify tenant isolation
        assert (
            len(self.tenant_messages["tenant1"]) > 0
        ), "Tenant 1 should have received messages"
        assert (
            len(self.tenant_messages["tenant2"]) > 0
        ), "Tenant 2 should have received messages"
        assert (
            len(self.tenant_messages["tenant3"]) > 0
        ), "Tenant 3 should have received messages"

        # Verify no cross-tenant message leakage
        for tenant, messages in self.tenant_messages.items():
            for message in messages:
                assert message["topic"].startswith(
                    tenant
                ), f"Message {message['topic']} leaked to {tenant} handler"

        # Verify message counts match expectations
        tenant1_expected = len(
            [m for m in multi_tenant_messages if m[0].startswith("tenant1")]
        )
        tenant2_expected = len(
            [m for m in multi_tenant_messages if m[0].startswith("tenant2")]
        )
        tenant3_expected = len(
            [m for m in multi_tenant_messages if m[0].startswith("tenant3")]
        )

        assert (
            len(self.tenant_messages["tenant1"]) == tenant1_expected
        ), f"Tenant 1 expected {tenant1_expected} messages, got {len(self.tenant_messages['tenant1'])}"
        assert (
            len(self.tenant_messages["tenant2"]) == tenant2_expected
        ), f"Tenant 2 expected {tenant2_expected} messages, got {len(self.tenant_messages['tenant2'])}"
        assert (
            len(self.tenant_messages["tenant3"]) == tenant3_expected
        ), f"Tenant 3 expected {tenant3_expected} messages, got {len(self.tenant_messages['tenant3'])}"


class TestPerformanceUnderRealLoad:
    """Test performance under realistic load conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TopicPatternManager()

    def test_high_volume_message_processing(self):
        """Test processing high volumes of messages efficiently."""
        # Create many patterns for a realistic scenario
        for i in range(100):
            pattern = TopicPattern(
                f"homeassistant/sensor{i}/+/state",
                priority=i % 10,
                description=f"Sensor {i} state pattern",
            )
            self.manager.add_pattern(pattern)

        # Create many subscriptions
        callbacks = []
        for i in range(200):
            callback = Mock()
            callbacks.append(callback)
            self.manager.subscribe_to_pattern(
                f"homeassistant/sensor{i % 100}/+/state", callback
            )

        # Generate high volume of messages
        message_count = 10000
        start_time = time.time()

        for i in range(message_count):
            topic = f"homeassistant/sensor{i % 100}/temperature/state"
            payload = f"value_{i}"

            routes = self.manager.route_message(topic, payload)

            # Execute callbacks
            for subscription_id, callback in routes:
                callback(topic, payload)

        end_time = time.time()
        processing_time = end_time - start_time

        # Performance assertions
        assert (
            processing_time < 10.0
        ), f"Processing {message_count} messages took too long: {processing_time:.2f}s"

        # Calculate throughput
        messages_per_second = message_count / processing_time
        assert (
            messages_per_second > 1000
        ), f"Throughput too low: {messages_per_second:.0f} msg/s"

        # Verify metrics
        metrics = self.manager.get_metrics()
        assert metrics["total_patterns"] == 100
        assert metrics["total_subscriptions"] == 200
        assert metrics["pattern_matches"] >= message_count
        assert metrics["topic_routes"] >= message_count

        # Check cache performance
        cache_hit_rate = metrics["cache_hit_rate"]
        assert cache_hit_rate > 0.1, f"Cache hit rate too low: {cache_hit_rate:.2%}"

        # Performance analysis
        performance_analysis = self.manager.get_performance_analysis()
        assert performance_analysis["total_messages_processed"] >= message_count

        # Optimization recommendations
        optimization_results = self.manager.optimize_performance()
        assert isinstance(optimization_results, dict)
        assert "recommendations" in optimization_results

    def test_memory_efficiency(self):
        """Test memory efficiency under load."""
        import os

        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create many patterns and subscriptions
        for i in range(500):
            pattern = TopicPattern(f"test/pattern{i}/+/state", priority=i % 5)
            self.manager.add_pattern(pattern)

            callback = Mock()
            self.manager.subscribe_to_pattern(f"test/pattern{i}/+/state", callback)

        # Process many messages
        for i in range(5000):
            topic = f"test/pattern{i % 500}/temperature/state"
            payload = f"value_{i}"
            self.manager.route_message(topic, payload)

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory efficiency assertions
        assert (
            memory_increase < 100
        ), f"Memory usage increased too much: {memory_increase:.1f} MB"

        # Check that caches are being managed properly
        metrics = self.manager.get_metrics()
        cache_size = metrics["pattern_match_cache_size"]
        assert cache_size <= 1000, f"Cache size too large: {cache_size}"

        # Force optimization
        optimization_results = self.manager.optimize_performance()
        assert (
            "cache_cleared" in optimization_results
            or "hierarchy_optimized" in optimization_results
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
