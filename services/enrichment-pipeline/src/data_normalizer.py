"""
Data Normalization Service for Home Assistant Events
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
import re
import json

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes Home Assistant event data to standardized formats"""
    
    def __init__(self):
        self.normalized_events = 0
        self.normalization_errors = 0
        self.last_normalized_time: Optional[datetime] = None
        
        # State value mappings
        self.boolean_states = {
            "on": True,
            "off": False,
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
            "enabled": True,
            "disabled": False,
            "active": True,
            "inactive": False
        }
        
        # Unit conversion mappings
        self.temperature_units = {
            "°C": "celsius",
            "°F": "fahrenheit",
            "celsius": "celsius",
            "fahrenheit": "fahrenheit"
        }
        
        self.pressure_units = {
            "hPa": "hectopascal",
            "mbar": "millibar",
            "mmHg": "millimeter_of_mercury",
            "inHg": "inch_of_mercury",
            "Pa": "pascal",
            "kPa": "kilopascal"
        }
    
    def normalize_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Normalize a Home Assistant event
        
        Args:
            event_data: The raw event data
            
        Returns:
            Normalized event data or None if normalization fails
        """
        try:
            # Start with a copy of the original data
            normalized = event_data.copy()
            
            # Add normalization metadata
            normalized["_normalized"] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0.0",
                "source": "enrichment-pipeline"
            }
            
            # Normalize timestamps
            normalized = self._normalize_timestamps(normalized)
            
            # Normalize state values
            normalized = self._normalize_state_values(normalized)
            
            # Normalize units
            normalized = self._normalize_units(normalized)
            
            # Extract entity metadata
            normalized = self._extract_entity_metadata(normalized)
            
            # Validate normalized data
            if not self._validate_normalized_data(normalized):
                self.normalization_errors += 1
                logger.warning(f"Normalized data validation failed for event: {event_data.get('event_type', 'unknown')}")
                return None
            
            # Update statistics
            self.normalized_events += 1
            self.last_normalized_time = datetime.now(timezone.utc)
            
            logger.debug(f"Successfully normalized {event_data.get('event_type', 'unknown')} event")
            return normalized
            
        except Exception as e:
            self.normalization_errors += 1
            logger.error(f"Error normalizing event: {e}")
            logger.debug(f"Event data: {event_data}")
            return None
    
    def _normalize_timestamps(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all timestamps to ISO 8601 UTC format
        
        Args:
            event_data: The event data
            
        Returns:
            Event data with normalized timestamps
        """
        try:
            # Normalize main timestamp
            if "timestamp" in event_data:
                event_data["timestamp"] = self._convert_to_iso_utc(event_data["timestamp"])
            
            # Normalize state timestamps
            if event_data.get("event_type") == "state_changed":
                # Normalize old_state timestamps
                if "old_state" in event_data and event_data["old_state"]:
                    old_state = event_data["old_state"]
                    if "last_changed" in old_state:
                        old_state["last_changed"] = self._convert_to_iso_utc(old_state["last_changed"])
                    if "last_updated" in old_state:
                        old_state["last_updated"] = self._convert_to_iso_utc(old_state["last_updated"])
                
                # Normalize new_state timestamps
                if "new_state" in event_data and event_data["new_state"]:
                    new_state = event_data["new_state"]
                    if "last_changed" in new_state:
                        new_state["last_changed"] = self._convert_to_iso_utc(new_state["last_changed"])
                    if "last_updated" in new_state:
                        new_state["last_updated"] = self._convert_to_iso_utc(new_state["last_updated"])
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error normalizing timestamps: {e}")
            return event_data
    
    def _convert_to_iso_utc(self, timestamp: Union[str, datetime]) -> str:
        """
        Convert timestamp to ISO 8601 UTC format
        
        Args:
            timestamp: The timestamp to convert
            
        Returns:
            ISO 8601 UTC timestamp string
        """
        try:
            if isinstance(timestamp, str):
                # Parse various timestamp formats
                if timestamp.endswith('Z'):
                    # Already UTC
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                elif '+' in timestamp or timestamp.endswith('00:00'):
                    # Has timezone info
                    dt = datetime.fromisoformat(timestamp)
                else:
                    # Assume UTC if no timezone info
                    dt = datetime.fromisoformat(timestamp).replace(tzinfo=timezone.utc)
            elif isinstance(timestamp, datetime):
                dt = timestamp
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            else:
                raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")
            
            # Convert to UTC
            if dt.tzinfo != timezone.utc:
                dt = dt.astimezone(timezone.utc)
            
            return dt.isoformat()
            
        except Exception as e:
            logger.error(f"Error converting timestamp {timestamp}: {e}")
            # Return current UTC time as fallback
            return datetime.now(timezone.utc).isoformat()
    
    def _normalize_state_values(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize state values to appropriate types
        
        Args:
            event_data: The event data
            
        Returns:
            Event data with normalized state values
        """
        try:
            if event_data.get("event_type") == "state_changed":
                # Normalize old_state
                if "old_state" in event_data and event_data["old_state"]:
                    old_state = event_data["old_state"]
                    if "state" in old_state:
                        old_state["state"] = self._normalize_state_value(old_state["state"])
                
                # Normalize new_state
                if "new_state" in event_data and event_data["new_state"]:
                    new_state = event_data["new_state"]
                    if "state" in new_state:
                        new_state["state"] = self._normalize_state_value(new_state["state"])
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error normalizing state values: {e}")
            return event_data
    
    def _normalize_state_value(self, state_value: Any) -> Union[bool, int, float, str]:
        """
        Normalize a single state value
        
        Args:
            state_value: The state value to normalize
            
        Returns:
            Normalized state value
        """
        try:
            if isinstance(state_value, (int, float)):
                return state_value
            
            if isinstance(state_value, str):
                state_str = state_value.lower().strip()
                
                # Check for boolean values
                if state_str in self.boolean_states:
                    return self.boolean_states[state_str]
                
                # Check for numeric values
                if self._is_numeric(state_str):
                    if '.' in state_str:
                        return float(state_str)
                    else:
                        return int(state_str)
                
                # Return as string if not numeric or boolean
                return state_value
            
            return state_value
            
        except Exception as e:
            logger.error(f"Error normalizing state value {state_value}: {e}")
            return state_value
    
    def _is_numeric(self, value: str) -> bool:
        """
        Check if a string represents a numeric value
        
        Args:
            value: The string to check
            
        Returns:
            True if numeric, False otherwise
        """
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _normalize_units(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize units in attributes
        
        Args:
            event_data: The event data
            
        Returns:
            Event data with normalized units
        """
        try:
            if event_data.get("event_type") == "state_changed":
                # Normalize units in new_state attributes
                if "new_state" in event_data and event_data["new_state"]:
                    new_state = event_data["new_state"]
                    if "attributes" in new_state:
                        new_state["attributes"] = self._normalize_attribute_units(new_state["attributes"])
                
                # Normalize units in old_state attributes
                if "old_state" in event_data and event_data["old_state"]:
                    old_state = event_data["old_state"]
                    if "attributes" in old_state:
                        old_state["attributes"] = self._normalize_attribute_units(old_state["attributes"])
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error normalizing units: {e}")
            return event_data
    
    def _normalize_attribute_units(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize units in entity attributes
        
        Args:
            attributes: The attributes dictionary
            
        Returns:
            Attributes with normalized units
        """
        try:
            normalized_attrs = attributes.copy()
            
            # Normalize temperature units
            if "unit_of_measurement" in normalized_attrs:
                unit = normalized_attrs["unit_of_measurement"]
                if unit in self.temperature_units:
                    normalized_attrs["unit_of_measurement"] = self.temperature_units[unit]
                elif unit in self.pressure_units:
                    normalized_attrs["unit_of_measurement"] = self.pressure_units[unit]
            
            return normalized_attrs
            
        except Exception as e:
            logger.error(f"Error normalizing attribute units: {e}")
            return attributes
    
    def _extract_entity_metadata(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize entity metadata
        
        Args:
            event_data: The event data
            
        Returns:
            Event data with extracted entity metadata
        """
        try:
            if event_data.get("event_type") == "state_changed":
                # Extract metadata from new_state
                if "new_state" in event_data and event_data["new_state"]:
                    new_state = event_data["new_state"]
                    entity_id = new_state.get("entity_id")
                    
                    if entity_id:
                        # Extract domain
                        domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
                        
                        # Extract attributes metadata
                        attributes = new_state.get("attributes", {})
                        
                        # Create normalized metadata
                        metadata = {
                            "entity_id": entity_id,
                            "domain": domain,
                            "device_class": attributes.get("device_class"),
                            "friendly_name": attributes.get("friendly_name"),
                            "unit_of_measurement": attributes.get("unit_of_measurement"),
                            "icon": attributes.get("icon"),
                            "entity_category": attributes.get("entity_category")
                        }
                        
                        # Add metadata to event
                        event_data["entity_metadata"] = metadata
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error extracting entity metadata: {e}")
            return event_data
    
    def _validate_normalized_data(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate normalized event data
        
        Args:
            event_data: The normalized event data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if "event_type" not in event_data:
                return False
            
            # Check timestamp format
            if "timestamp" in event_data:
                timestamp = event_data["timestamp"]
                if not isinstance(timestamp, str) or not timestamp.endswith('+00:00'):
                    logger.warning(f"Invalid timestamp format: {timestamp}")
                    return False
            
            # Check state_changed specific validation
            if event_data.get("event_type") == "state_changed":
                if "new_state" not in event_data or not event_data["new_state"]:
                    return False
                
                new_state = event_data["new_state"]
                if "entity_id" not in new_state or "state" not in new_state:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating normalized data: {e}")
            return False
    
    def get_normalization_statistics(self) -> Dict[str, Any]:
        """
        Get normalization statistics
        
        Returns:
            Dictionary with normalization statistics
        """
        return {
            "normalized_events": self.normalized_events,
            "normalization_errors": self.normalization_errors,
            "success_rate": (self.normalized_events / (self.normalized_events + self.normalization_errors) * 100) 
                           if (self.normalized_events + self.normalization_errors) > 0 else 0,
            "last_normalized_time": self.last_normalized_time.isoformat() if self.last_normalized_time else None
        }
    
    def reset_statistics(self):
        """Reset normalization statistics"""
        self.normalized_events = 0
        self.normalization_errors = 0
        self.last_normalized_time = None
        logger.info("Normalization statistics reset")
