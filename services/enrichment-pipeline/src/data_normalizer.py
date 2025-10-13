"""
Data Normalization Service for Home Assistant Events
Epic 18.1: Integrated with Data Validation Engine
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
import re
import json

from data_validator import get_validator, ValidationResult
# TEMPORARILY DISABLED: from quality_metrics import get_quality_metrics_collector

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes Home Assistant event data to standardized formats"""
    
    def __init__(self):
        self.normalized_events = 0
        self.normalization_errors = 0
        self.last_normalized_time: Optional[datetime] = None
        self.validator = get_validator()  # Epic 18.1: Data validation engine
        # TEMPORARILY DISABLED: self.quality_metrics = get_quality_metrics_collector()  # Epic 18.2: Quality metrics
        
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
            Normalized event data or None if normalization fails or validation fails
        """
        try:
            # TEMPORARILY DISABLED: Epic 18.1: Validate event data FIRST
            # TODO: Re-enable validation after fixing validation issues
            validation_result = self.validator.validate_event(event_data)
            
            # TEMPORARILY DISABLED: Epic 18.2: Record quality metrics
            # self.quality_metrics.record_validation_result(validation_result, event_data)
            
            # Log validation results if there are issues
            if not validation_result.is_valid:
                entity_id = event_data.get('entity_id', 'unknown')
                event_type = event_data.get('event_type', 'unknown')
                logger.warning(
                    f"[NORMALIZER] VALIDATION FAILED - Entity: {entity_id}, Event Type: {event_type}, "
                    f"Errors: {', '.join(validation_result.errors)}, "
                    f"Full Event: {str(event_data)[:200]}..."
                )
                self.normalization_errors += 1
                # Continue processing despite validation errors
            
            if validation_result.warnings:
                logger.warning(
                    f"[NORMALIZER] Event validation warnings for {event_data.get('entity_id', 'unknown')}: "
                    f"{', '.join(validation_result.warnings)}"
                )
            
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
            
            # Normalize numeric attribute fields to prevent InfluxDB type conflicts
            normalized_attrs = self._normalize_numeric_attributes(normalized_attrs)
            
            return normalized_attrs
            
        except Exception as e:
            logger.error(f"Error normalizing attribute units: {e}")
            return attributes
    
    def _normalize_numeric_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize ALL attribute field types to prevent InfluxDB type conflicts.
        
        InfluxDB enforces strict field typing - once a field is defined with a type,
        it cannot accept different types. This method ensures consistent typing for:
        - Boolean fields (true/false strings → boolean)
        - Numeric fields (string numbers → float)
        - String fields (keep as strings)
        - Null/empty values (remove)
        
        Args:
            attributes: The attributes dictionary
            
        Returns:
            Attributes with normalized field types
        """
        try:
            # Known boolean attribute fields that may arrive as strings from Home Assistant
            boolean_fields = [
                'dynamic_eq', 'aux_heat', 'away_mode', 'is_volume_muted', 
                'shuffle', 'repeat', 'is_locked', 'motion_detected', 
                'tamper_detected', 'battery_low', 'door_open', 'window_open',
                'occupancy', 'presence', 'charging', 'auto', 'eco_mode'
            ]
            
            # Known numeric attribute fields that may arrive as strings from Home Assistant
            numeric_fields = [
                'azimuth', 'elevation', 'brightness', 'temperature', 'humidity',
                'pressure', 'battery', 'battery_level', 'power', 'energy', 
                'voltage', 'current', 'frequency', 'speed', 'distance',
                'wind_speed', 'wind_bearing', 'visibility', 'precipitation',
                'uv_index', 'pm25', 'pm10', 'co2', 'voc', 'latitude', 'longitude',
                'volume_level', 'media_position', 'media_duration', 'supported_features',
                'hvac_modes', 'swing_modes', 'fan_modes', 'preset_modes', 'options',
                'min_temp', 'max_temp', 'min_humidity', 'max_humidity', 'step'
            ]
            
            normalized_attrs = attributes.copy()
            type_conversions = {'boolean': 0, 'numeric': 0, 'removed': 0}
            
            for key, value in list(normalized_attrs.items()):
                # Skip None values
                if value is None:
                    del normalized_attrs[key]
                    type_conversions['removed'] += 1
                    continue
                
                # Remove attr_ prefix for matching
                attr_name = key.replace('attr_', '')
                
                # Handle Boolean Fields
                if attr_name in boolean_fields:
                    try:
                        if isinstance(value, bool):
                            # Already boolean, keep as-is
                            pass
                        elif isinstance(value, str):
                            # Convert string to boolean
                            value_lower = value.lower().strip()
                            if value_lower in ('true', '1', 'on', 'yes', 'enabled'):
                                normalized_attrs[key] = True
                                type_conversions['boolean'] += 1
                            elif value_lower in ('false', '0', 'off', 'no', 'disabled'):
                                normalized_attrs[key] = False
                                type_conversions['boolean'] += 1
                            elif value_lower == '':
                                # Empty string - remove field
                                del normalized_attrs[key]
                                type_conversions['removed'] += 1
                            else:
                                # Invalid boolean value - remove to prevent conflict
                                logger.warning(f"Invalid boolean value for {key}: '{value}' - removing field")
                                del normalized_attrs[key]
                                type_conversions['removed'] += 1
                        elif isinstance(value, (int, float)):
                            # Convert 0/1 to boolean
                            normalized_attrs[key] = bool(value)
                            type_conversions['boolean'] += 1
                        else:
                            # Unknown type - remove
                            logger.warning(f"Removing boolean field {key} with invalid type {type(value)}: {value}")
                            del normalized_attrs[key]
                            type_conversions['removed'] += 1
                    except Exception as e:
                        logger.warning(f"Failed to convert {key} to boolean: {value} ({e}) - removing field")
                        del normalized_attrs[key]
                        type_conversions['removed'] += 1
                
                # Handle Numeric Fields
                elif attr_name in numeric_fields:
                    try:
                        if isinstance(value, str):
                            # Handle empty strings
                            if value.strip() == '':
                                del normalized_attrs[key]
                                type_conversions['removed'] += 1
                                continue
                            
                            # Attempt float conversion
                            normalized_attrs[key] = float(value)
                            type_conversions['numeric'] += 1
                        
                        elif isinstance(value, (int, float)):
                            # Already numeric, ensure it's float for consistency
                            normalized_attrs[key] = float(value)
                        
                        elif isinstance(value, bool):
                            # Boolean shouldn't be in numeric field - convert to 0/1
                            normalized_attrs[key] = float(1 if value else 0)
                            type_conversions['numeric'] += 1
                        
                        else:
                            # Non-numeric value - remove to prevent conflict
                            logger.warning(f"Removing numeric field {key} with non-numeric type {type(value)}: {value}")
                            del normalized_attrs[key]
                            type_conversions['removed'] += 1
                    
                    except (ValueError, TypeError) as e:
                        # Conversion failed - remove field rather than cause InfluxDB conflict
                        logger.warning(f"Failed to convert {key} to float: {value} ({e}) - removing field")
                        del normalized_attrs[key]
                        type_conversions['removed'] += 1
                
                # Handle String Fields (keep as-is, just ensure they're strings)
                else:
                    if isinstance(value, str):
                        # Already string, keep as-is
                        pass
                    elif isinstance(value, (int, float, bool)):
                        # Convert primitives to strings to maintain consistency
                        normalized_attrs[key] = str(value)
                    elif value == '':
                        # Empty string - remove
                        del normalized_attrs[key]
                        type_conversions['removed'] += 1
                    # Lists, dicts, etc. keep as-is (InfluxDB will handle as JSON)
            
            # Log type conversions summary if any occurred
            if sum(type_conversions.values()) > 0:
                logger.info(f"Type normalization applied: {type_conversions['boolean']} boolean, "
                           f"{type_conversions['numeric']} numeric, "
                           f"{type_conversions['removed']} removed fields")
            
            return normalized_attrs
            
        except Exception as e:
            logger.error(f"Error normalizing attribute types: {e}")
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
                if not isinstance(timestamp, str):
                    logger.warning(f"Invalid timestamp format: {timestamp}")
                    return False
                # Accept various timestamp formats (with or without timezone)
                if not (timestamp.endswith('+00:00') or timestamp.endswith('Z') or 
                       re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$', timestamp)):
                    logger.warning(f"Invalid timestamp format: {timestamp}")
                    return False
            
            # Check state_changed specific validation
            if event_data.get("event_type") == "state_changed":
                if "new_state" not in event_data or not event_data["new_state"]:
                    return False
                
                new_state = event_data["new_state"]
                # Check entity_id in both new_state and top-level (WebSocket service format)
                entity_id = new_state.get("entity_id") or event_data.get("entity_id")
                if not entity_id or "state" not in new_state:
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
