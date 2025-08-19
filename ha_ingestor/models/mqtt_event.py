"""MQTT event models for Home Assistant integration."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .events import Event


class MQTTEvent(Event):
    """Model for MQTT events from Home Assistant."""

    topic: str = Field(..., description="MQTT topic")
    payload: str = Field(..., description="Message payload")
    state: str = Field(..., description="Entity state value")
    event_type: str = Field(default="state_changed", description="Type of event")
    source: Literal["mqtt"] = Field(default="mqtt", description="Event source")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate MQTT topic format."""
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")

        # Check if topic follows Home Assistant pattern
        if not re.match(r"^homeassistant/[^/]+/[^/]+/state$", v.strip()):
            raise ValueError(
                "Topic must follow pattern: homeassistant/domain/entity_id/state"
            )

        return v.strip()

    @field_validator("payload")
    @classmethod
    def validate_payload(cls, v: str) -> str:
        """Validate message payload."""
        if not v or not v.strip():
            raise ValueError("Payload cannot be empty")
        return v.strip()

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Validate entity domain."""
        if not v or not v.strip():
            raise ValueError("Domain cannot be empty")

        # Common Home Assistant domains
        common_domains = {
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
        }

        domain = v.strip().lower()
        if domain not in common_domains:
            # Allow custom domains but log warning
            import logging

            logging.getLogger(__name__).warning(f"Unknown domain: {domain}")

        return domain

    @field_validator("entity_id")
    @classmethod
    def validate_entity_id(cls, v: str) -> str:
        """Validate entity ID format."""
        if not v or not v.strip():
            raise ValueError("Entity ID cannot be empty")

        # Entity ID should be lowercase with underscores
        entity_id = v.strip().lower()
        if not re.match(r"^[a-z0-9_]+$", entity_id):
            raise ValueError(
                "Entity ID must contain only lowercase letters, numbers, and underscores"
            )

        return entity_id

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        """Validate entity state."""
        if not v or not v.strip():
            raise ValueError("State cannot be empty")
        return v.strip()

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate entity attributes."""
        if v is None:
            return None

        if not isinstance(v, dict):
            raise ValueError("Attributes must be a dictionary")

        # Ensure all attribute values are serializable
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Attribute keys must be strings")

            # Check if value is JSON serializable
            try:
                import json

                json.dumps(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Attribute value for '{key}' is not JSON serializable"
                )

        return v

    @classmethod
    def from_mqtt_message(
        cls, topic: str, payload: str, timestamp: datetime | None = None
    ) -> "MQTTEvent":
        """Create MQTTEvent from MQTT message.

        Args:
            topic: MQTT topic
            payload: Message payload
            timestamp: Event timestamp (defaults to current time)

        Returns:
            MQTTEvent instance

        Raises:
            ValueError: If topic format is invalid
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Parse topic to extract domain and entity_id
        # Expected format: homeassistant/domain/entity_id/state
        topic_parts = topic.split("/")
        if (
            len(topic_parts) != 4
            or topic_parts[0] != "homeassistant"
            or topic_parts[3] != "state"
        ):
            raise ValueError(f"Invalid topic format: {topic}")

        domain = topic_parts[1]
        entity_id = topic_parts[2]

        # Try to parse payload as JSON for attributes
        attributes = None
        try:
            import json

            parsed_payload = json.loads(payload)
            if isinstance(parsed_payload, dict):
                # Extract state and attributes from JSON payload
                state = parsed_payload.get("state", payload)
                attributes = parsed_payload.get("attributes")
            else:
                state = payload
        except (json.JSONDecodeError, TypeError):
            # If payload is not JSON, use as-is
            state = payload

        return cls(
            topic=topic,
            payload=payload,
            timestamp=timestamp,
            domain=domain,
            entity_id=entity_id,
            state=state,
            attributes=attributes,
            event_type="state_changed",
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "topic": self.topic,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "domain": self.domain,
            "entity_id": self.entity_id,
            "state": self.state,
            "attributes": self.attributes,
            "source": self.source,
        }

    def get_measurement_name(self) -> str:
        """Get InfluxDB measurement name for this event."""
        return f"ha_{self.domain}"

    def get_tags(self) -> dict[str, str | None]:
        """Get InfluxDB tags for this event."""
        tags = {
            "domain": self.domain,
            "entity_id": self.entity_id,
            "source": self.source,
        }

        # Add additional tags from attributes if they exist
        if self.attributes:
            # Add common attribute tags
            for attr_name in ["friendly_name", "unit_of_measurement", "device_class"]:
                if attr_name in self.attributes:
                    attr_value = str(self.attributes[attr_name])
                    if (
                        attr_value and len(attr_value) <= 64
                    ):  # InfluxDB tag length limit
                        tags[attr_name] = attr_value

        return tags

    def get_fields(self) -> dict[str, Any]:
        """Get InfluxDB fields for this event."""
        fields: dict[str, Any] = {"state": self.state, "payload": self.payload}

        # Add numeric attributes as fields
        if self.attributes:
            for attr_name, attr_value in self.attributes.items():
                if isinstance(attr_value, (int, float)):
                    fields[f"attr_{attr_name}"] = attr_value
                elif isinstance(attr_value, str) and len(attr_value) <= 64:
                    # Add short string attributes as fields
                    fields[f"attr_{attr_name}"] = attr_value

        return fields
