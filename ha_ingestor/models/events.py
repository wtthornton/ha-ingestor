"""Base event model for the filter system."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Event(BaseModel, ABC):
    """Base event class for the filter system.

    This class provides the common interface needed by filters and transformers.
    Concrete event types (MQTTEvent, WebSocketEvent) should inherit from this.
    """

    domain: str | None = Field(None, description="Entity domain (e.g., sensor, switch)")
    entity_id: str | None = Field(None, description="Entity identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of event")
    attributes: dict[str, Any] | None = Field(None, description="Entity attributes")

    @abstractmethod
    def get_measurement_name(self) -> str:
        """Get the measurement name for InfluxDB storage."""
        pass

    @abstractmethod
    def get_tags(self) -> dict[str, str | None]:
        """Get tags for InfluxDB storage."""
        pass

    @abstractmethod
    def get_fields(self) -> dict[str, Any]:
        """Get fields for InfluxDB storage."""
        pass

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute value with optional default.

        Args:
            key: Attribute key
            default: Default value if key not found

        Returns:
            Attribute value or default
        """
        if self.attributes and key in self.attributes:
            return self.attributes[key]
        return default

    def has_attribute(self, key: str) -> bool:
        """Check if an attribute exists.

        Args:
            key: Attribute key to check

        Returns:
            True if attribute exists, False otherwise
        """
        return self.attributes is not None and key in self.attributes

    def get_attribute_keys(self) -> list[str]:
        """Get all attribute keys.

        Returns:
            List of attribute keys
        """
        if self.attributes:
            return list(self.attributes.keys())
        return []

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "domain": self.domain,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "attributes": self.attributes or {},
        }

    def __str__(self) -> str:
        """String representation of the event."""
        domain_str = self.domain or "unknown"
        entity_str = self.entity_id or "unknown"
        return f"{self.__class__.__name__}(domain={domain_str}, entity_id={entity_str}, type={self.event_type})"

    def __repr__(self) -> str:
        """Detailed string representation of the event."""
        domain_str = f"'{self.domain}'" if self.domain else "None"
        entity_str = f"'{self.entity_id}'" if self.entity_id else "None"
        return f"{self.__class__.__name__}(domain={domain_str}, entity_id={entity_str}, event_type='{self.event_type}', timestamp={self.timestamp}, attributes={self.attributes})"
