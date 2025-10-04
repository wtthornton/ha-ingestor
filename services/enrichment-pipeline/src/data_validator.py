"""
Data Validation Service for Home Assistant Events
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    level: ValidationLevel
    message: str
    field: Optional[str] = None
    value: Optional[Any] = None
    expected: Optional[Any] = None


class DataValidator:
    """Comprehensive data validator for Home Assistant events"""
    
    def __init__(self):
        self.validation_stats = {
            "total_validations": 0,
            "valid_events": 0,
            "invalid_events": 0,
            "warnings": 0,
            "errors": 0
        }
        
        # Validation rules configuration
        self.required_fields = {
            "event_type": str,
            "timestamp": str
        }
        
        self.state_changed_required_fields = {
            "entity_id": str,
            "state": (str, int, float, bool)
        }
        
        # Value range validations
        self.temperature_range = (-50, 60)  # Celsius
        self.humidity_range = (0, 100)  # Percentage
        self.pressure_range = (800, 1200)  # hPa
        
        # Entity ID pattern validation
        self.entity_id_pattern = re.compile(r'^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$')
        
        # Timestamp format patterns
        self.timestamp_patterns = [
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$'),  # ISO with milliseconds
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'),  # ISO without milliseconds
            re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$'),  # ISO with timezone
        ]
    
    def validate_event(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate a single Home Assistant event
        
        Args:
            event: The event data to validate
            
        Returns:
            List of validation results
        """
        results = []
        
        try:
            # Update validation statistics
            self.validation_stats["total_validations"] += 1
            
            # Required fields validation
            results.extend(self._validate_required_fields(event))
            
            # Data type validation
            results.extend(self._validate_data_types(event))
            
            # Format validation
            results.extend(self._validate_formats(event))
            
            # Value range validation
            results.extend(self._validate_value_ranges(event))
            
            # Business logic validation
            results.extend(self._validate_business_logic(event))
            
            # Weather enrichment validation
            results.extend(self._validate_weather_enrichment(event))
            
            # Timestamp validation
            results.extend(self._validate_timestamps(event))
            
            # Update statistics based on results
            self._update_validation_stats(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error during event validation: {e}")
            self.validation_stats["errors"] += 1
            return [ValidationResult(
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Validation error: {str(e)}"
            )]
    
    def _validate_required_fields(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate required fields are present"""
        results = []
        
        # Check basic required fields
        for field, expected_type in self.required_fields.items():
            if field not in event or event[field] is None:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Missing required field: {field}",
                    field=field,
                    expected=expected_type.__name__
                ))
        
        # Check state_changed specific required fields
        if event.get("event_type") == "state_changed":
            if "new_state" not in event or not event["new_state"]:
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="Missing required field: new_state",
                    field="new_state"
                ))
            else:
                new_state = event["new_state"]
                for field, expected_type in self.state_changed_required_fields.items():
                    if field not in new_state or new_state[field] is None:
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.ERROR,
                            message=f"Missing required field in new_state: {field}",
                            field=f"new_state.{field}",
                            expected=expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
                        ))
        
        return results
    
    def _validate_data_types(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate data types"""
        results = []
        
        # Validate event_type
        if "event_type" in event:
            if not isinstance(event["event_type"], str):
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="event_type must be a string",
                    field="event_type",
                    value=type(event["event_type"]).__name__,
                    expected="str"
                ))
        
        # Validate timestamp
        if "timestamp" in event:
            if not isinstance(event["timestamp"], str):
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message="timestamp must be a string",
                    field="timestamp",
                    value=type(event["timestamp"]).__name__,
                    expected="str"
                ))
        
        # Validate state_changed specific fields
        if event.get("event_type") == "state_changed" and "new_state" in event:
            new_state = event["new_state"]
            
            # Validate entity_id
            if "entity_id" in new_state:
                if not isinstance(new_state["entity_id"], str):
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        message="entity_id must be a string",
                        field="new_state.entity_id",
                        value=type(new_state["entity_id"]).__name__,
                        expected="str"
                    ))
            
            # Validate state value
            if "state" in new_state:
                state_value = new_state["state"]
                if not isinstance(state_value, (str, int, float, bool)):
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        message="state must be a string, number, or boolean",
                        field="new_state.state",
                        value=type(state_value).__name__,
                        expected="str, int, float, or bool"
                    ))
        
        return results
    
    def _validate_formats(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate data formats"""
        results = []
        
        # Validate entity_id format
        if event.get("event_type") == "state_changed" and "new_state" in event:
            new_state = event["new_state"]
            if "entity_id" in new_state:
                entity_id = new_state["entity_id"]
                if isinstance(entity_id, str) and not self.entity_id_pattern.match(entity_id):
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        message=f"Invalid entity_id format: {entity_id}",
                        field="new_state.entity_id",
                        value=entity_id,
                        expected="domain.entity_name format"
                    ))
        
        # Validate timestamp format
        if "timestamp" in event:
            timestamp = event["timestamp"]
            if isinstance(timestamp, str) and not any(pattern.match(timestamp) for pattern in self.timestamp_patterns):
                results.append(ValidationResult(
                    is_valid=False,
                    level=ValidationLevel.ERROR,
                    message=f"Invalid timestamp format: {timestamp}",
                    field="timestamp",
                    value=timestamp,
                    expected="ISO 8601 UTC format"
                ))
        
        return results
    
    def _validate_value_ranges(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate value ranges"""
        results = []
        
        # Validate weather data ranges
        if "weather" in event:
            weather = event["weather"]
            
            # Temperature validation
            if "temperature" in weather:
                temp = weather["temperature"]
                if isinstance(temp, (int, float)):
                    if not (self.temperature_range[0] <= temp <= self.temperature_range[1]):
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message=f"Temperature out of reasonable range: {temp}°C",
                            field="weather.temperature",
                            value=temp,
                            expected=f"{self.temperature_range[0]} to {self.temperature_range[1]}°C"
                        ))
            
            # Humidity validation
            if "humidity" in weather:
                humidity = weather["humidity"]
                if isinstance(humidity, (int, float)):
                    if not (self.humidity_range[0] <= humidity <= self.humidity_range[1]):
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message=f"Humidity out of reasonable range: {humidity}%",
                            field="weather.humidity",
                            value=humidity,
                            expected=f"{self.humidity_range[0]} to {self.humidity_range[1]}%"
                        ))
            
            # Pressure validation
            if "pressure" in weather:
                pressure = weather["pressure"]
                if isinstance(pressure, (int, float)):
                    if not (self.pressure_range[0] <= pressure <= self.pressure_range[1]):
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message=f"Pressure out of reasonable range: {pressure}hPa",
                            field="weather.pressure",
                            value=pressure,
                            expected=f"{self.pressure_range[0]} to {self.pressure_range[1]}hPa"
                        ))
        
        return results
    
    def _validate_business_logic(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate business logic rules"""
        results = []
        
        # Validate state_changed event structure
        if event.get("event_type") == "state_changed":
            # Check if old_state and new_state are consistent
            if "old_state" in event and "new_state" in event:
                old_state = event["old_state"]
                new_state = event["new_state"]
                
                # Entity IDs should match
                if (old_state and new_state and 
                    old_state.get("entity_id") != new_state.get("entity_id")):
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.ERROR,
                        message="Entity ID mismatch between old_state and new_state",
                        field="entity_id_consistency"
                    ))
                
                # Timestamps should be logical
                if (old_state and new_state and 
                    "last_updated" in old_state and "last_updated" in new_state):
                    try:
                        old_time = datetime.fromisoformat(old_state["last_updated"].replace('Z', '+00:00'))
                        new_time = datetime.fromisoformat(new_state["last_updated"].replace('Z', '+00:00'))
                        
                        if new_time < old_time:
                            results.append(ValidationResult(
                                is_valid=False,
                                level=ValidationLevel.WARNING,
                                message="new_state timestamp is earlier than old_state timestamp",
                                field="timestamp_consistency"
                            ))
                    except (ValueError, TypeError):
                        # Timestamp parsing errors are handled elsewhere
                        pass
        
        return results
    
    def _validate_weather_enrichment(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate weather enrichment data"""
        results = []
        
        if "weather" in event:
            weather = event["weather"]
            
            # Check required weather fields
            required_weather_fields = ["temperature", "humidity", "pressure", "timestamp"]
            for field in required_weather_fields:
                if field not in weather:
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"Missing weather field: {field}",
                        field=f"weather.{field}"
                    ))
            
            # Validate weather timestamp
            if "timestamp" in weather:
                weather_timestamp = weather["timestamp"]
                if not any(pattern.match(weather_timestamp) for pattern in self.timestamp_patterns):
                    results.append(ValidationResult(
                        is_valid=False,
                        level=ValidationLevel.WARNING,
                        message=f"Invalid weather timestamp format: {weather_timestamp}",
                        field="weather.timestamp",
                        value=weather_timestamp,
                        expected="ISO 8601 UTC format"
                    ))
        
        return results
    
    def _validate_timestamps(self, event: Dict[str, Any]) -> List[ValidationResult]:
        """Validate timestamp consistency and logic"""
        results = []
        
        # Check if event timestamp is recent (not too far in the future)
        if "timestamp" in event and isinstance(event["timestamp"], str):
            try:
                event_time = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                
                # Allow up to 1 hour in the future for clock skew
                if event_time > current_time:
                    time_diff = (event_time - current_time).total_seconds()
                    if time_diff > 3600:  # 1 hour
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.WARNING,
                            message=f"Event timestamp is too far in the future: {time_diff/3600:.1f} hours",
                            field="timestamp",
                            value=event["timestamp"]
                        ))
                
                # Warn if event is very old (more than 24 hours)
                elif event_time < current_time:
                    time_diff = (current_time - event_time).total_seconds()
                    if time_diff > 86400:  # 24 hours
                        results.append(ValidationResult(
                            is_valid=False,
                            level=ValidationLevel.INFO,
                            message=f"Event timestamp is old: {time_diff/3600:.1f} hours ago",
                            field="timestamp",
                            value=event["timestamp"]
                        ))
                        
            except (ValueError, TypeError):
                # Format validation errors are handled elsewhere
                pass
        
        return results
    
    def _update_validation_stats(self, results: List[ValidationResult]):
        """Update validation statistics based on results"""
        has_errors = any(r.level == ValidationLevel.ERROR for r in results)
        has_warnings = any(r.level == ValidationLevel.WARNING for r in results)
        
        if has_errors:
            self.validation_stats["invalid_events"] += 1
            self.validation_stats["errors"] += len([r for r in results if r.level == ValidationLevel.ERROR])
        else:
            self.validation_stats["valid_events"] += 1
        
        if has_warnings:
            self.validation_stats["warnings"] += len([r for r in results if r.level == ValidationLevel.WARNING])
    
    def is_event_valid(self, event: Dict[str, Any]) -> bool:
        """
        Check if an event passes all validation checks
        
        Args:
            event: The event to validate
            
        Returns:
            True if event is valid, False otherwise
        """
        results = self.validate_event(event)
        return not any(r.level == ValidationLevel.ERROR for r in results)
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get validation statistics
        
        Returns:
            Dictionary with validation statistics
        """
        total = self.validation_stats["total_validations"]
        if total > 0:
            success_rate = (self.validation_stats["valid_events"] / total) * 100
            error_rate = (self.validation_stats["errors"] / total) * 100
            warning_rate = (self.validation_stats["warnings"] / total) * 100
        else:
            success_rate = error_rate = warning_rate = 0
        
        return {
            "total_validations": total,
            "valid_events": self.validation_stats["valid_events"],
            "invalid_events": self.validation_stats["invalid_events"],
            "success_rate": round(success_rate, 2),
            "error_rate": round(error_rate, 2),
            "warning_rate": round(warning_rate, 2),
            "total_errors": self.validation_stats["errors"],
            "total_warnings": self.validation_stats["warnings"]
        }
    
    def reset_statistics(self):
        """Reset validation statistics"""
        self.validation_stats = {
            "total_validations": 0,
            "valid_events": 0,
            "invalid_events": 0,
            "warnings": 0,
            "errors": 0
        }
        logger.info("Validation statistics reset")
