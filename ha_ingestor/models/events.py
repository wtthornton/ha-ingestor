"""Base event model for the filter system."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class Event(BaseModel, ABC):
    """Base event class for the filter system.
    
    This class provides the common interface needed by filters and transformers.
    Concrete event types (MQTTEvent, WebSocketEvent) should inherit from this.
    """
    
    domain: str = Field(..., description="Entity domain (e.g., sensor, switch)")
    entity_id: str = Field(..., description="Entity identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of event")
    attributes: Optional[Dict[str, Any]] = Field(None, description="Entity attributes")
    
    @abstractmethod
    def get_measurement_name(self) -> str:
        """Get the measurement name for InfluxDB storage."""
        pass
    
    @abstractmethod
    def get_tags(self) -> Dict[str, str]:
        """Get tags for InfluxDB storage."""
        pass
    
    @abstractmethod
    def get_fields(self) -> Dict[str, Any]:
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "domain": self.domain,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "attributes": self.attributes or {}
        }
    
    def __str__(self) -> str:
        """String representation of the event."""
        return f"{self.__class__.__name__}(domain={self.domain}, entity_id={self.entity_id}, type={self.event_type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the event."""
        return f"{self.__class__.__name__}(domain='{self.domain}', entity_id='{self.entity_id}', event_type='{self.event_type}', timestamp={self.timestamp}, attributes={self.attributes})"
