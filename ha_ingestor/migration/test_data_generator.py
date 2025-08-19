"""Test data generator for schema migration testing.

This module generates realistic Home Assistant data for testing the schema
migration process with production-like workloads and data patterns.
"""

import json
import logging
import random
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class DataPattern(Enum):
    """Data pattern types for test generation."""

    HIGH_FREQUENCY = "high_frequency"  # High-frequency sensor data
    PERIODIC = "periodic"  # Periodic automation events
    BURST = "burst"  # Burst traffic patterns
    SPARSE = "sparse"  # Sparse, irregular events
    MIXED = "mixed"  # Mixed pattern combination


@dataclass
class TestDataConfig:
    """Configuration for test data generation."""

    # Data volume
    total_events: int = 100000
    time_span_hours: int = 24

    # Entity configuration
    light_entities: int = 50
    sensor_entities: int = 100
    switch_entities: int = 30
    climate_entities: int = 10
    automation_entities: int = 20

    # Event distribution
    mqtt_percentage: float = 0.7  # 70% MQTT, 30% WebSocket
    state_change_percentage: float = 0.8  # 80% state changes
    service_call_percentage: float = 0.15  # 15% service calls
    automation_percentage: float = 0.05  # 5% automation events

    # Data patterns
    pattern: DataPattern = DataPattern.MIXED

    # Cardinality simulation
    high_cardinality_entities: int = 1000  # Entities with unique IDs
    dynamic_attributes: bool = True  # Enable dynamic attributes

    # Performance stress testing
    enable_stress_patterns: bool = False
    stress_multiplier: float = 10.0


class HomeAssistantDataGenerator:
    """Generates realistic Home Assistant data for testing."""

    def __init__(
        self,
        config: TestDataConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize data generator.

        Args:
            config: Test data configuration
            logger: Logger instance
        """
        self.config = config or TestDataConfig()
        self.logger = logger or logging.getLogger(__name__)

        # Entity pools
        self.entities = self._generate_entity_pools()

        # State tracking for realistic data
        self.entity_states: dict[str, Any] = {}

        # Pattern generators
        self.pattern_generators = {
            DataPattern.HIGH_FREQUENCY: self._generate_high_frequency_pattern,
            DataPattern.PERIODIC: self._generate_periodic_pattern,
            DataPattern.BURST: self._generate_burst_pattern,
            DataPattern.SPARSE: self._generate_sparse_pattern,
            DataPattern.MIXED: self._generate_mixed_pattern,
        }

    def _generate_entity_pools(self) -> dict[str, list[str]]:
        """Generate pools of entity IDs for different domains."""
        entities = {}

        # Light entities
        entities["light"] = [
            f"light.{room}_{fixture}"
            for room in [
                "living_room",
                "bedroom",
                "kitchen",
                "bathroom",
                "office",
                "hallway",
            ]
            for fixture in ["main", "accent", "desk", "ceiling"]
        ][: self.config.light_entities]

        # Sensor entities
        sensor_types = [
            "temperature",
            "humidity",
            "pressure",
            "motion",
            "door",
            "window",
            "battery",
        ]
        entities["sensor"] = [
            f"sensor.{room}_{sensor_type}"
            for room in [
                "living_room",
                "bedroom",
                "kitchen",
                "bathroom",
                "office",
                "garage",
                "basement",
            ]
            for sensor_type in sensor_types
        ][: self.config.sensor_entities]

        # Switch entities
        entities["switch"] = [
            f"switch.{device}"
            for device in [
                "fan",
                "heater",
                "humidifier",
                "air_purifier",
                "coffee_maker",
                "dishwasher",
            ]
            for room in ["living_room", "bedroom", "kitchen", "office"]
        ][: self.config.switch_entities]

        # Climate entities
        entities["climate"] = [
            f"climate.{zone}"
            for zone in ["main_floor", "upstairs", "basement", "garage"]
        ][: self.config.climate_entities]

        # Automation entities
        entities["automation"] = [
            f"automation.{name}"
            for name in [
                "morning_routine",
                "evening_routine",
                "security_lights",
                "energy_saving",
                "presence_detection",
                "night_mode",
                "vacation_mode",
                "emergency_response",
            ]
        ][: self.config.automation_entities]

        # High cardinality entities for stress testing
        if self.config.high_cardinality_entities > 0:
            entities["high_cardinality"] = [
                f"sensor.dynamic_entity_{i:06d}"
                for i in range(self.config.high_cardinality_entities)
            ]

        total_entities = sum(len(entity_list) for entity_list in entities.values())
        self.logger.info(
            f"Generated {total_entities} test entities across {len(entities)} domains"
        )

        return entities

    async def generate_test_dataset(self) -> list[dict[str, Any]]:
        """Generate complete test dataset.

        Returns:
            List of generated events
        """
        start_time = datetime.utcnow() - timedelta(hours=self.config.time_span_hours)
        events = []

        self.logger.info(
            f"Generating {self.config.total_events} events over {self.config.time_span_hours} hours"
        )

        # Generate events based on pattern
        pattern_generator = self.pattern_generators[self.config.pattern]
        event_times = pattern_generator(start_time)

        # Generate events for each timestamp
        for i, event_time in enumerate(event_times[: self.config.total_events]):
            event = await self._generate_event_at_time(event_time, i)
            events.append(event)

            if i % 10000 == 0 and i > 0:
                self.logger.info(f"Generated {i}/{self.config.total_events} events")

        self.logger.info(f"Generated {len(events)} total events")
        return events

    def _generate_high_frequency_pattern(
        self, start_time: datetime
    ) -> Iterator[datetime]:
        """Generate high-frequency event pattern."""
        current_time = start_time
        end_time = start_time + timedelta(hours=self.config.time_span_hours)

        while current_time < end_time:
            # High frequency: 10-100 events per minute
            interval = random.uniform(0.6, 6.0)  # 0.6-6 seconds between events
            current_time += timedelta(seconds=interval)
            yield current_time

    def _generate_periodic_pattern(self, start_time: datetime) -> Iterator[datetime]:
        """Generate periodic event pattern."""
        current_time = start_time
        end_time = start_time + timedelta(hours=self.config.time_span_hours)

        while current_time < end_time:
            # Periodic: regular intervals with some jitter
            base_interval = 300  # 5 minutes
            jitter = random.uniform(-60, 60)  # ±1 minute jitter
            interval = base_interval + jitter
            current_time += timedelta(seconds=interval)
            yield current_time

    def _generate_burst_pattern(self, start_time: datetime) -> Iterator[datetime]:
        """Generate burst event pattern."""
        current_time = start_time
        end_time = start_time + timedelta(hours=self.config.time_span_hours)

        while current_time < end_time:
            # Burst pattern: periods of high activity followed by quiet periods
            if random.random() < 0.3:  # 30% chance of burst
                # Burst: 50-200 events in quick succession
                burst_size = random.randint(50, 200)
                for _ in range(burst_size):
                    yield current_time
                    current_time += timedelta(seconds=random.uniform(0.1, 2.0))

                # Quiet period: 10-30 minutes
                quiet_duration = random.randint(600, 1800)
                current_time += timedelta(seconds=quiet_duration)
            else:
                # Normal activity
                current_time += timedelta(seconds=random.uniform(30, 120))
                yield current_time

    def _generate_sparse_pattern(self, start_time: datetime) -> Iterator[datetime]:
        """Generate sparse event pattern."""
        current_time = start_time
        end_time = start_time + timedelta(hours=self.config.time_span_hours)

        while current_time < end_time:
            # Sparse: irregular intervals, mostly quiet
            interval = random.uniform(600, 3600)  # 10 minutes to 1 hour
            current_time += timedelta(seconds=interval)
            yield current_time

    def _generate_mixed_pattern(self, start_time: datetime) -> Iterator[datetime]:
        """Generate mixed event pattern combining multiple patterns."""
        patterns = [
            self._generate_high_frequency_pattern,
            self._generate_periodic_pattern,
            self._generate_burst_pattern,
            self._generate_sparse_pattern,
        ]

        # Divide time into segments and use different patterns
        segment_duration = self.config.time_span_hours / len(patterns)

        for i, pattern_func in enumerate(patterns):
            segment_start = start_time + timedelta(hours=i * segment_duration)

            # Generate events for this pattern segment
            for event_time in pattern_func(segment_start):
                if event_time < start_time + timedelta(
                    hours=(i + 1) * segment_duration
                ):
                    yield event_time
                else:
                    break

    async def _generate_event_at_time(
        self, event_time: datetime, sequence: int
    ) -> dict[str, Any]:
        """Generate a single event at specified time.

        Args:
            event_time: Time for the event
            sequence: Sequence number for the event

        Returns:
            Generated event data
        """
        # Determine event type
        rand = random.random()

        if rand < self.config.mqtt_percentage:
            # Generate MQTT event
            if random.random() < self.config.state_change_percentage:
                return self._generate_mqtt_state_event(event_time, sequence)
            else:
                return self._generate_mqtt_sensor_event(event_time, sequence)
        else:
            # Generate WebSocket event
            if random.random() < self.config.service_call_percentage:
                return self._generate_websocket_service_event(event_time, sequence)
            else:
                return self._generate_websocket_state_event(event_time, sequence)

    def _generate_mqtt_state_event(
        self, timestamp: datetime, sequence: int
    ) -> dict[str, Any]:
        """Generate MQTT state change event."""
        # Choose random domain and entity
        domain = random.choice(["light", "switch", "climate"])
        entity_id = random.choice(self.entities[domain])

        # Generate realistic state based on domain
        if domain == "light":
            state = random.choice(["on", "off"])
            brightness = random.randint(1, 255) if state == "on" else 0
            color_temp = random.randint(153, 500) if state == "on" else None

            attributes = {
                "brightness": brightness,
                "friendly_name": entity_id.replace("_", " ").title(),
                "supported_features": 43,
            }
            if color_temp:
                attributes["color_temp"] = color_temp

        elif domain == "switch":
            state = random.choice(["on", "off"])
            attributes = {
                "friendly_name": entity_id.replace("_", " ").title(),
                "device_class": "outlet",
            }

        elif domain == "climate":
            state = random.choice(["heat", "cool", "auto", "off"])
            current_temp = random.uniform(18.0, 26.0)
            target_temp = random.uniform(19.0, 25.0)

            attributes = {
                "current_temperature": round(current_temp, 1),
                "temperature": round(target_temp, 1),
                "friendly_name": entity_id.replace("_", " ").title(),
                "hvac_modes": ["heat", "cool", "auto", "off"],
                "supported_features": 17,
            }

        # Add dynamic attributes for cardinality testing
        if self.config.dynamic_attributes:
            attributes["last_changed"] = timestamp.isoformat()
            attributes["context_id"] = (
                f"context_{sequence}_{random.randint(1000, 9999)}"
            )
            if random.random() < 0.1:  # 10% chance of user context
                attributes["context_user_id"] = f"user_{random.randint(1, 10)}"

        # Store state for consistency
        self.entity_states[entity_id] = state

        topic = f"homeassistant/{domain}/{entity_id.split('.')[1]}/state"
        payload = {"state": state, "attributes": attributes}

        return {
            "type": "mqtt",
            "topic": topic,
            "payload": json.dumps(payload),
            "timestamp": timestamp,
            "domain": domain,
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes,
        }

    def _generate_mqtt_sensor_event(
        self, timestamp: datetime, sequence: int
    ) -> dict[str, Any]:
        """Generate MQTT sensor event."""
        entity_id = random.choice(self.entities["sensor"])
        sensor_type = entity_id.split("_")[-1]

        # Generate realistic sensor values
        if sensor_type == "temperature":
            value = round(random.uniform(15.0, 30.0), 1)
            unit = "°C"
            device_class = "temperature"
        elif sensor_type == "humidity":
            value = round(random.uniform(30.0, 80.0), 1)
            unit = "%"
            device_class = "humidity"
        elif sensor_type == "pressure":
            value = round(random.uniform(990.0, 1030.0), 1)
            unit = "hPa"
            device_class = "pressure"
        elif sensor_type == "battery":
            value = random.randint(0, 100)
            unit = "%"
            device_class = "battery"
        elif sensor_type in ["motion", "door", "window"]:
            value = random.choice(["on", "off"])
            unit = None
            device_class = sensor_type
        else:
            value = round(random.uniform(0.0, 100.0), 2)
            unit = "units"
            device_class = "measurement"

        attributes = {
            "unit_of_measurement": unit,
            "device_class": device_class,
            "friendly_name": entity_id.replace("_", " ").title(),
        }

        if unit:
            attributes["unit_of_measurement"] = unit

        # Add dynamic attributes
        if self.config.dynamic_attributes:
            attributes["last_changed"] = timestamp.isoformat()
            if random.random() < 0.05:  # 5% chance of additional metadata
                attributes["source_timestamp"] = (
                    timestamp - timedelta(seconds=random.randint(1, 60))
                ).isoformat()
                attributes["accuracy"] = random.randint(1, 5)

        topic = f"homeassistant/sensor/{entity_id.split('.')[1]}/state"
        payload = {"state": value, "attributes": attributes}

        return {
            "type": "mqtt",
            "topic": topic,
            "payload": json.dumps(payload),
            "timestamp": timestamp,
            "domain": "sensor",
            "entity_id": entity_id,
            "state": value,
            "attributes": attributes,
        }

    def _generate_websocket_service_event(
        self, timestamp: datetime, sequence: int
    ) -> dict[str, Any]:
        """Generate WebSocket service call event."""
        # Choose service domain and action
        services = {
            "light": ["turn_on", "turn_off", "toggle"],
            "switch": ["turn_on", "turn_off", "toggle"],
            "climate": ["set_temperature", "set_hvac_mode"],
            "automation": ["trigger", "turn_on", "turn_off"],
        }

        domain = random.choice(list(services.keys()))
        service = random.choice(services[domain])

        # Generate service data
        service_data = {}
        target_entity = None

        if domain in self.entities:
            target_entity = random.choice(self.entities[domain])
            service_data["entity_id"] = target_entity

        if domain == "light" and service == "turn_on":
            service_data["brightness"] = random.randint(1, 255)
            if random.random() < 0.3:  # 30% chance of color
                service_data["color_temp"] = random.randint(153, 500)
        elif domain == "climate" and service == "set_temperature":
            service_data["temperature"] = random.randint(18, 26)

        data = {
            "domain": domain,
            "service": service,
            "service_data": service_data,
            "context": {
                "id": f"context_{sequence}_{random.randint(1000, 9999)}",
                "parent_id": None,
                "user_id": (
                    f"user_{random.randint(1, 10)}" if random.random() < 0.7 else None
                ),
            },
        }

        return {
            "type": "websocket",
            "event_type": "call_service",
            "timestamp": timestamp,
            "entity_id": target_entity,
            "domain": domain,
            "data": data,
        }

    def _generate_websocket_state_event(
        self, timestamp: datetime, sequence: int
    ) -> dict[str, Any]:
        """Generate WebSocket state change event."""
        # Choose random entity from any domain
        all_entities = []
        for domain, entities in self.entities.items():
            if domain != "high_cardinality":  # Skip high cardinality for regular events
                all_entities.extend([(domain, entity) for entity in entities])

        domain, entity_id = random.choice(all_entities)

        # Get current and new state
        old_state = self.entity_states.get(entity_id, "unknown")

        if domain == "light":
            new_state = random.choice(["on", "off"])
        elif domain == "switch":
            new_state = random.choice(["on", "off"])
        elif domain == "sensor":
            sensor_type = entity_id.split("_")[-1]
            if sensor_type == "temperature":
                new_state = str(round(random.uniform(15.0, 30.0), 1))
            elif sensor_type in ["motion", "door", "window"]:
                new_state = random.choice(["on", "off"])
            else:
                new_state = str(round(random.uniform(0.0, 100.0), 2))
        else:
            new_state = random.choice(["on", "off", "auto", "unknown"])

        # Update stored state
        self.entity_states[entity_id] = new_state

        data = {
            "entity_id": entity_id,
            "old_state": {
                "entity_id": entity_id,
                "state": old_state,
                "last_changed": (
                    timestamp - timedelta(minutes=random.randint(1, 60))
                ).isoformat(),
                "last_updated": (
                    timestamp - timedelta(seconds=random.randint(1, 300))
                ).isoformat(),
            },
            "new_state": {
                "entity_id": entity_id,
                "state": new_state,
                "last_changed": timestamp.isoformat(),
                "last_updated": timestamp.isoformat(),
            },
            "context": {
                "id": f"context_{sequence}_{random.randint(1000, 9999)}",
                "parent_id": None,
                "user_id": (
                    f"user_{random.randint(1, 10)}" if random.random() < 0.3 else None
                ),
            },
        }

        return {
            "type": "websocket",
            "event_type": "state_changed",
            "timestamp": timestamp,
            "entity_id": entity_id,
            "domain": domain,
            "data": data,
        }

    async def save_test_dataset(
        self, events: list[dict[str, Any]], filename: str
    ) -> None:
        """Save generated test dataset to file.

        Args:
            events: Generated events
            filename: Output filename
        """
        dataset = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "config": {
                    "total_events": self.config.total_events,
                    "time_span_hours": self.config.time_span_hours,
                    "pattern": self.config.pattern.value,
                    "entities": {
                        domain: len(entities)
                        for domain, entities in self.entities.items()
                    },
                },
                "statistics": self._calculate_dataset_statistics(events),
            },
            "events": events,
        }

        with open(filename, "w") as f:
            json.dump(dataset, f, indent=2, default=str)

        self.logger.info(f"Test dataset saved to {filename}")

    def _calculate_dataset_statistics(
        self, events: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Calculate statistics for the generated dataset.

        Args:
            events: Generated events

        Returns:
            Dataset statistics
        """
        stats = {
            "total_events": len(events),
            "event_types": {},
            "domains": {},
            "entity_count": len(
                set(
                    event.get("entity_id") for event in events if event.get("entity_id")
                )
            ),
            "time_range": {
                "start": (
                    min(event["timestamp"] for event in events).isoformat()
                    if events
                    else None
                ),
                "end": (
                    max(event["timestamp"] for event in events).isoformat()
                    if events
                    else None
                ),
            },
        }

        # Count event types and domains
        for event in events:
            event_type = event.get("type", "unknown")
            stats["event_types"][event_type] = (
                stats["event_types"].get(event_type, 0) + 1
            )

            domain = event.get("domain", "unknown")
            stats["domains"][domain] = stats["domains"].get(domain, 0) + 1

        return stats


async def generate_test_data_for_migration(
    config: TestDataConfig | None = None,
    output_file: str = "migration_test_data.json",
) -> str:
    """Generate test data for migration testing.

    Args:
        config: Test data configuration
        output_file: Output filename

    Returns:
        Path to generated test data file
    """
    logger = logging.getLogger(__name__)

    # Use default config if none provided
    if config is None:
        config = TestDataConfig()

    # Create generator
    generator = HomeAssistantDataGenerator(config, logger)

    # Generate dataset
    events = await generator.generate_test_dataset()

    # Save dataset
    await generator.save_test_dataset(events, output_file)

    return output_file
