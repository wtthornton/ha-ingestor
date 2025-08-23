"""WebSocket event models for Home Assistant integration."""

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import Field, field_validator

from .events import Event


class WebSocketEvent(Event):
    """Model for WebSocket events from Home Assistant."""

    data: dict[str, Any] = Field(..., description="Event data")
    attributes: dict[str, Any] | None = Field(None, description="Entity attributes")
    source: Literal["websocket"] = Field(
        default="websocket", description="Event source"
    )

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type."""
        if not v or not v.strip():
            raise ValueError("Event type cannot be empty")

        # Common Home Assistant event types
        common_event_types = {
            "state_changed",
            "automation_triggered",
            "service_called",
            "event",
            "call_service",
            "fire_event",
            "user_updated",
            "device_registry_updated",
            "area_registry_updated",
        }

        event_type = v.strip().lower()
        if event_type not in common_event_types:
            # Allow custom event types but log warning
            import logging

            logging.getLogger(__name__).warning(f"Unknown event type: {event_type}")

        return event_type

    @field_validator("entity_id")
    @classmethod
    def validate_entity_id(cls, v: str | None) -> str | None:
        """Validate entity ID format."""
        if v is None:
            return None

        if not v.strip():
            raise ValueError("Entity ID cannot be empty if provided")

        # Entity ID should be lowercase with underscores and dots (Home Assistant format)
        entity_id = v.strip().lower()
        if not re.match(r"^[a-z0-9_.]+$", entity_id):
            raise ValueError(
                "Entity ID must contain only lowercase letters, numbers, underscores, and dots"
            )

        return entity_id

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str | None) -> str | None:
        """Validate entity domain."""
        if v is None:
            return None

        if not v.strip():
            raise ValueError("Domain cannot be empty if provided")

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

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate event data."""
        if not isinstance(v, dict):
            raise ValueError("Event data must be a dictionary")

        # Ensure all data values are serializable
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Event data keys must be strings")

            # Check if value is JSON serializable
            try:
                import json

                json.dumps(value)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Event data value for '{key}' is not JSON serializable"
                )

        return v

    @classmethod
    def from_websocket_message(
        cls, message: dict[str, Any], timestamp: datetime | None = None
    ) -> "WebSocketEvent":
        """Create WebSocketEvent from WebSocket message.

        Args:
            message: WebSocket message
            timestamp: Event timestamp (defaults to current time)

        Returns:
            WebSocketEvent instance

        Raises:
            ValueError: If message format is invalid
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Extract event information from message
        event_type = message.get("event", {}).get("event_type")
        if not event_type:
            raise ValueError("Message does not contain event_type")

        event_data = message.get("event", {})

        # Extract entity information if available
        entity_id = None
        domain = None

        if event_type == "state_changed":
            # For state_changed events, extract entity info from data
            entity = event_data.get("data", {}).get("entity_id")
            if entity:
                entity_id = entity
                # Extract domain from entity_id (e.g., "sensor.temperature" -> "sensor")
                if "." in entity:
                    domain = entity.split(".")[0]

        # Extract attributes if available
        attributes = None
        if event_type == "state_changed":
            # For state_changed events, extract attributes from data
            new_state = event_data.get("data", {}).get("new_state", {})
            if new_state and isinstance(new_state, dict):
                attributes = new_state.get("attributes")

        return cls(
            event_type=event_type,
            entity_id=entity_id,
            domain=domain,
            data=event_data,
            timestamp=timestamp,
            attributes=attributes,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "domain": self.domain,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
        }

    def get_measurement_name(self) -> str:
        """Get InfluxDB measurement name for this event."""
        if self.domain:
            return f"ha_{self.domain}_events"
        else:
            return f"ha_{self.event_type}"

    def get_tags(self) -> dict[str, str | None]:
        """Get InfluxDB tags for this event."""
        tags: dict[str, str | None] = {
            "event_type": self.event_type,
            "source": self.source,
        }

        if self.entity_id:
            tags["entity_id"] = self.entity_id

        if self.domain:
            tags["domain"] = self.domain

        # Add additional tags from event data if they exist
        if self.data:
            # Add common data tags
            for key in ["service", "service_data", "context_id", "context_user_id"]:
                if key in self.data:
                    value = str(self.data[key])
                    if value and len(value) <= 64:  # InfluxDB tag length limit
                        tags[key] = value

        return tags

    def get_fields(self) -> dict[str, Any]:
        """Get InfluxDB fields for this event."""
        fields: dict[str, Any] = {"event_type": self.event_type}

        # Add numeric and string data as fields
        if self.data:
            for key, value in self.data.items():
                if isinstance(value, (int, float)):
                    fields[f"data_{key}"] = value
                elif isinstance(value, str) and len(value) <= 64:
                    # Add short string values as fields
                    fields[f"data_{key}"] = value
                elif isinstance(value, bool):
                    # Convert boolean to integer for InfluxDB
                    fields[f"data_{key}"] = int(value)

        return fields

    def get_state_change_info(self) -> dict[str, Any] | None:
        """Get state change information for state_changed events.

        Returns:
            Dictionary with old_state and new_state info, or None if not a state_changed event
        """
        if self.event_type != "state_changed":
            return None

        event_data = self.data.get("data", {})
        old_state = event_data.get("old_state", {})
        new_state = event_data.get("new_state", {})

        if not old_state or not new_state:
            return None

        return {
            "old_state": old_state.get("state"),
            "new_state": new_state.get("state"),
            "old_attributes": old_state.get("attributes", {}),
            "new_attributes": new_state.get("attributes", {}),
            "last_changed": old_state.get("last_changed"),
            "last_updated": new_state.get("last_updated"),
        }

    def get_service_call_info(self) -> dict[str, Any] | None:
        """Get service call information for call_service events.

        Returns:
            Dictionary with service call info, or None if not a call_service event
        """
        if self.event_type != "call_service":
            return None

        return {
            "service": self.data.get("service"),
            "service_data": self.data.get("service_data", {}),
            "domain": self.data.get("domain"),
        }

    def get_automation_info(self) -> dict[str, Any] | None:
        """Get automation information for automation_triggered events.

        Returns:
            Dictionary with automation info, or None if not an automation_triggered event
        """
        if self.event_type != "automation_triggered":
            return None

        return {
            "entity_id": self.data.get("entity_id"),
            "name": self.data.get("name"),
            "source": self.data.get("source"),
        }
