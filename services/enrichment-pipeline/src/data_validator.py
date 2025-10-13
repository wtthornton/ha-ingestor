"""
Data Validation Engine
Epic 18.1: Complete Data Validation Engine

Comprehensive validation for Home Assistant events before storage.
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    entity_type: Optional[str] = None
    domain: Optional[str] = None
    validation_time_ms: float = 0.0
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'entity_type': self.entity_type,
            'domain': self.domain,
            'validation_time_ms': self.validation_time_ms
        }


class DataValidationEngine:
    """Validation engine for Home Assistant events"""
    
    # Entity ID pattern: domain.entity_name
    ENTITY_ID_PATTERN = re.compile(r'^[a-z_]+\.[a-z0-9_]+$')
    
    # Known Home Assistant domains
    KNOWN_DOMAINS = {
        'sensor', 'binary_sensor', 'light', 'switch', 'climate', 'cover',
        'fan', 'lock', 'media_player', 'camera', 'alarm_control_panel',
        'vacuum', 'water_heater', 'weather', 'device_tracker', 'person',
        'zone', 'automation', 'script', 'scene', 'input_boolean',
        'input_number', 'input_select', 'input_text', 'input_datetime',
        'timer', 'counter', 'sun', 'moon', 'calendar'
    }
    
    # Numeric sensor device classes (expect numeric state)
    NUMERIC_SENSOR_CLASSES = {
        'temperature', 'humidity', 'pressure', 'battery', 'power',
        'energy', 'voltage', 'current', 'frequency', 'illuminance',
        'signal_strength', 'pm25', 'pm10', 'co2', 'aqi'
    }
    
    def __init__(self):
        """Initialize validation engine"""
        self.validation_count = 0
        self.error_count = 0
        self.warning_count = 0
        self.start_time = time.time()
    
    def validate_event(self, event: Dict[str, Any]) -> ValidationResult:
        """
        Validate a Home Assistant event
        
        Args:
            event: Event dictionary from Home Assistant
            
        Returns:
            ValidationResult with validation status and details
        """
        start_time = time.time()
        result = ValidationResult(is_valid=True)
        
        try:
            # DEBUG: Log event structure
            logger.warning(f"[VALIDATOR] validate_event called")
            logger.warning(f"[VALIDATOR] Event keys: {list(event.keys())}")
            logger.warning(f"[VALIDATOR] Event type: {event.get('event_type')}")
            logger.warning(f"[VALIDATOR] Has entity_id: {'entity_id' in event}")
            logger.warning(f"[VALIDATOR] Has data: {'data' in event}")
            
            # Extract entity_id and state data from the event
            # The WebSocket service already extracts and flattens the structure,
            # so entity_id is at the top level, not in event['data']['entity_id']
            entity_id = event.get('entity_id', '')
            new_state = event.get('new_state', {})
            old_state = event.get('old_state', {})
            
            logger.warning(f"[VALIDATOR] Extracted entity_id: '{entity_id}' (type: {type(entity_id)})")
            logger.warning(f"[VALIDATOR] Has new_state: {new_state is not None}, Has old_state: {old_state is not None}")
            
            # Validate entity_id
            logger.warning(f"[VALIDATOR] Calling _validate_entity_id")
            if not self._validate_entity_id(entity_id, result):
                logger.warning(f"[VALIDATOR] _validate_entity_id FAILED - Errors: {result.errors}")
                return result
            logger.warning(f"[VALIDATOR] _validate_entity_id PASSED")
            
            # Extract domain from entity_id
            domain = entity_id.split('.')[0] if '.' in entity_id else ''
            result.domain = domain
            
            # Validate event structure
            self._validate_event_structure(event, result)
            
            # Validate state data
            if new_state:
                self._validate_state_data(new_state, domain, result)
            else:
                result.add_warning("Missing new_state in event data")
            
            # Domain-specific validation
            self._validate_domain_specific(new_state, domain, result)
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            result.add_error(f"Validation exception: {str(e)}")
        
        finally:
            # Record validation metrics
            validation_time_ms = (time.time() - start_time) * 1000
            result.validation_time_ms = validation_time_ms
            
            self.validation_count += 1
            if not result.is_valid:
                self.error_count += 1
            if result.warnings:
                self.warning_count += 1
        
        return result
    
    def _validate_entity_id(self, entity_id: str, result: ValidationResult) -> bool:
        """Validate entity_id format"""
        if not entity_id:
            result.add_error("Missing entity_id")
            return False
        
        if not isinstance(entity_id, str):
            result.add_error(f"entity_id must be string, got {type(entity_id).__name__}")
            return False
        
        if not self.ENTITY_ID_PATTERN.match(entity_id):
            result.add_error(f"Invalid entity_id format: {entity_id}")
            return False
        
        # Check domain
        domain = entity_id.split('.')[0]
        if domain not in self.KNOWN_DOMAINS:
            result.add_warning(f"Unknown domain: {domain}")
        
        return True
    
    def _validate_event_structure(self, event: Dict[str, Any], result: ValidationResult):
        """Validate event structure"""
        # The WebSocket service already extracts and flattens the event structure,
        # so we check for entity_id at the top level
        if 'entity_id' not in event:
            result.add_error("Missing 'entity_id' field in event")
        
        if 'event_type' not in event:
            result.add_warning("Missing 'event_type' field")
        
        # Validate event_type if present
        event_type = event.get('event_type')
        if event_type and event_type not in ['state_changed', 'call_service', 'automation_triggered']:
            result.add_warning(f"Unusual event_type: {event_type}")
    
    def _validate_state_data(self, state: Dict[str, Any], domain: str, result: ValidationResult):
        """Validate state data structure"""
        # Required fields in state object
        # Note: entity_id is at the event level, not in the state object
        # The WebSocket service's EventProcessor creates simplified state objects
        required_fields = ['state', 'last_changed', 'last_updated']
        
        for field in required_fields:
            if field not in state:
                result.add_error(f"Missing required field in state: {field}")
        
        # Validate state value
        state_value = state.get('state')
        if state_value is None:
            result.add_error("State value is None")
        elif state_value == '':
            result.add_warning("State value is empty string")
        
        # Validate timestamps
        for ts_field in ['last_changed', 'last_updated']:
            if ts_field in state:
                self._validate_timestamp(state[ts_field], ts_field, result)
        
        # Validate attributes
        attributes = state.get('attributes', {})
        if not isinstance(attributes, dict):
            result.add_error("attributes must be a dictionary")
    
    def _validate_timestamp(self, timestamp: Any, field_name: str, result: ValidationResult):
        """Validate timestamp format"""
        if not timestamp:
            result.add_warning(f"{field_name} is empty")
            return
        
        if not isinstance(timestamp, str):
            result.add_error(f"{field_name} must be string, got {type(timestamp).__name__}")
            return
        
        # Try to parse ISO 8601 timestamp
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            result.add_error(f"Invalid timestamp format for {field_name}: {timestamp}")
    
    def _validate_domain_specific(self, state: Dict[str, Any], domain: str, result: ValidationResult):
        """Domain-specific validation"""
        if not state:
            return
        
        state_value = state.get('state')
        attributes = state.get('attributes', {})
        
        if domain == 'sensor':
            self._validate_sensor(state_value, attributes, result)
        elif domain == 'binary_sensor':
            self._validate_binary_sensor(state_value, result)
        elif domain == 'light':
            self._validate_light(state_value, attributes, result)
        elif domain == 'switch':
            self._validate_switch(state_value, result)
        elif domain == 'climate':
            self._validate_climate(state_value, attributes, result)
        # Add more domain validations as needed
    
    def _validate_sensor(self, state: Any, attributes: Dict[str, Any], result: ValidationResult):
        """Validate sensor state"""
        # Check if unavailable
        if state in ['unavailable', 'unknown']:
            return  # Valid states
        
        device_class = attributes.get('device_class')
        
        # Numeric sensors should have numeric state
        if device_class in self.NUMERIC_SENSOR_CLASSES:
            try:
                float(state)
            except (ValueError, TypeError):
                result.add_error(f"Numeric sensor has non-numeric state: {state}")
        
        # Check for unit_of_measurement
        if device_class and 'unit_of_measurement' not in attributes:
            result.add_warning(f"Sensor with device_class {device_class} missing unit_of_measurement")
        
        # Validate temperature range
        if device_class == 'temperature':
            try:
                temp = float(state)
                if temp < -100 or temp > 100:
                    result.add_warning(f"Temperature value out of typical range: {temp}")
            except (ValueError, TypeError):
                pass
    
    def _validate_binary_sensor(self, state: Any, result: ValidationResult):
        """Validate binary sensor state"""
        valid_states = ['on', 'off', 'unavailable', 'unknown']
        
        if state not in valid_states:
            result.add_error(f"Binary sensor has invalid state: {state}")
    
    def _validate_light(self, state: Any, attributes: Dict[str, Any], result: ValidationResult):
        """Validate light state"""
        valid_states = ['on', 'off', 'unavailable', 'unknown']
        
        if state not in valid_states:
            result.add_error(f"Light has invalid state: {state}")
        
        # If on, check for brightness
        if state == 'on' and 'brightness' in attributes:
            brightness = attributes['brightness']
            try:
                b = int(brightness)
                if b < 0 or b > 255:
                    result.add_error(f"Brightness out of range (0-255): {b}")
            except (ValueError, TypeError):
                result.add_error(f"Invalid brightness value: {brightness}")
    
    def _validate_switch(self, state: Any, result: ValidationResult):
        """Validate switch state"""
        valid_states = ['on', 'off', 'unavailable', 'unknown']
        
        if state not in valid_states:
            result.add_error(f"Switch has invalid state: {state}")
    
    def _validate_climate(self, state: Any, attributes: Dict[str, Any], result: ValidationResult):
        """Validate climate/thermostat state"""
        valid_states = ['off', 'heat', 'cool', 'heat_cool', 'auto', 'dry', 'fan_only', 'unavailable', 'unknown']
        
        if state not in valid_states:
            result.add_warning(f"Unusual climate state: {state}")
        
        # Validate temperature settings
        for temp_attr in ['temperature', 'target_temp_high', 'target_temp_low', 'current_temperature']:
            if temp_attr in attributes:
                temp = attributes[temp_attr]
                try:
                    t = float(temp)
                    if t < -50 or t > 50:  # Celsius range
                        result.add_warning(f"{temp_attr} out of typical range: {t}")
                except (ValueError, TypeError):
                    result.add_error(f"Invalid {temp_attr} value: {temp}")
    
    def is_event_valid(self, event: Dict[str, Any]) -> bool:
        """
        Check if an event is valid (simple boolean check)
        
        Args:
            event: Event dictionary from Home Assistant
            
        Returns:
            True if event is valid, False otherwise
        """
        validation_result = self.validate_event(event)
        return validation_result.is_valid

    def get_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'validation_count': self.validation_count,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'error_rate': self.error_count / self.validation_count if self.validation_count > 0 else 0.0,
            'warning_rate': self.warning_count / self.validation_count if self.validation_count > 0 else 0.0
        }


# Global validator instance
_validator = None


def get_validator() -> DataValidationEngine:
    """Get or create global validator instance"""
    global _validator
    if _validator is None:
        _validator = DataValidationEngine()
    return _validator
