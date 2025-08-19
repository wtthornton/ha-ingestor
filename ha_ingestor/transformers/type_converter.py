"""Type conversion transformer for converting data types and validating data integrity."""

from typing import Any, Dict, List, Optional, Union, Callable
import time
import structlog
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from .base import Transformer, TransformationResult


class TypeConverter(Transformer):
    """Transforms data by converting field types and validating data integrity."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        
        # Type conversion configuration
        self.type_mappings = self.config.get("type_mappings", {})
        self.default_values = self.config.get("default_values", {})
        self.validation_rules = self.config.get("validation_rules", {})
        self.strict_mode = self.config.get("strict_mode", False)
        self.handle_errors = self.config.get("handle_errors", "warn")  # warn, skip, fail
        
        # Built-in type converters
        self._type_converters = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "datetime": self._to_datetime,
            "date": self._to_date,
            "decimal": self._to_decimal,
            "list": list,
            "dict": dict,
            "json": self._to_json_string,
        }
        
        # Validation
        if not isinstance(self.type_mappings, dict):
            raise ValueError("type_mappings must be a dictionary")
        
        self.logger.info("TypeConverter initialized", 
                        type_mappings_count=len(self.type_mappings),
                        strict_mode=self.strict_mode,
                        handle_errors=self.handle_errors)
    
    def transform(self, data: Dict[str, Any]) -> TransformationResult:
        """Transform data by applying type conversions."""
        start_time = time.time()
        self.metrics["transformations_total"] += 1
        
        try:
            if not isinstance(data, dict):
                error_msg = f"Input data must be a dictionary, got {type(data).__name__}"
                self.metrics["transformations_failed"] += 1
                return TransformationResult(
                    success=False,
                    data=data,
                    errors=[error_msg],
                    processing_time_ms=(time.time() - start_time) * 1000
                )
            
            transformed_data = data.copy()
            errors = []
            warnings = []
            conversions_applied = 0
            
            # Apply type conversions
            for field_name, target_type in self.type_mappings.items():
                if field_name in transformed_data:
                    try:
                        original_value = transformed_data[field_name]
                        converted_value = self._convert_value(original_value, target_type, field_name)
                        
                        if converted_value is not None:
                            transformed_data[field_name] = converted_value
                            conversions_applied += 1
                            
                            self.logger.debug("Type conversion applied", 
                                            field=field_name,
                                            original_type=type(original_value).__name__,
                                            target_type=target_type,
                                            original_value=original_value,
                                            converted_value=converted_value)
                        
                        # Apply validation rules if specified
                        if field_name in self.validation_rules:
                            validation_result = self._validate_field(
                                field_name, converted_value, self.validation_rules[field_name]
                            )
                            if not validation_result["valid"]:
                                if self.strict_mode:
                                    errors.append(f"Validation failed for {field_name}: {validation_result['message']}")
                                else:
                                    warnings.append(f"Validation warning for {field_name}: {validation_result['message']}")
                    
                    except Exception as e:
                        error_msg = f"Type conversion failed for field '{field_name}': {str(e)}"
                        
                        if self.handle_errors == "fail":
                            errors.append(error_msg)
                        elif self.handle_errors == "warn":
                            warnings.append(error_msg)
                        elif self.handle_errors == "skip":
                            # Skip this field, keep original value
                            pass
                        
                        self.logger.warning("Type conversion failed", 
                                          field=field_name, 
                                          target_type=target_type,
                                          error=str(e))
                        
                        # Apply default value if available
                        if field_name in self.default_values:
                            transformed_data[field_name] = self.default_values[field_name]
                            self.logger.info("Applied default value", 
                                           field=field_name,
                                           default_value=self.default_values[field_name])
                
                else:
                    # Field not present, apply default if specified
                    if field_name in self.default_values:
                        transformed_data[field_name] = self.default_values[field_name]
                        conversions_applied += 1
                        self.logger.debug("Applied default value for missing field", 
                                        field=field_name,
                                        default_value=self.default_values[field_name])
            
            processing_time = (time.time() - start_time) * 1000
            self.metrics["total_processing_time_ms"] += processing_time
            
            if not errors:
                self.metrics["transformations_success"] += 1
                return TransformationResult(
                    success=True,
                    data=transformed_data,
                    warnings=warnings,
                    metadata={
                        "conversions_applied": conversions_applied,
                        "fields_processed": len(self.type_mappings),
                        "validation_rules_applied": len([f for f in self.type_mappings if f in self.validation_rules])
                    },
                    processing_time_ms=processing_time
                )
            else:
                self.metrics["transformations_failed"] += 1
                return TransformationResult(
                    success=False,
                    data=transformed_data,
                    errors=errors,
                    warnings=warnings,
                    metadata={
                        "conversions_applied": conversions_applied,
                        "fields_processed": len(self.type_mappings)
                    },
                    processing_time_ms=processing_time
                )
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.metrics["transformations_failed"] += 1
            self.metrics["total_processing_time_ms"] += processing_time
            
            error_msg = f"Type conversion transformation failed: {str(e)}"
            self.logger.error("Type conversion transformation failed", error=str(e))
            
            return TransformationResult(
                success=False,
                data=data,
                errors=[error_msg],
                processing_time_ms=processing_time
            )
    
    def _convert_value(self, value: Any, target_type: str, field_name: str) -> Any:
        """Convert a value to the specified type."""
        if target_type not in self._type_converters:
            raise ValueError(f"Unsupported target type: {target_type}")
        
        converter = self._type_converters[target_type]
        
        # Handle None values
        if value is None:
            return None
        
        # Handle empty strings for numeric types
        if target_type in ["int", "float", "decimal"] and value == "":
            return None
        
        # Handle boolean conversions
        if target_type == "bool":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            elif isinstance(value, (int, float)):
                return bool(value)
            else:
                return bool(value)
        
        # Handle list conversions
        if target_type == "list" and not isinstance(value, list):
            return [value]
        
        # Handle dict conversions
        if target_type == "dict" and not isinstance(value, dict):
            return {"value": value}
        
        # Use the converter function
        try:
            return converter(value)
        except (ValueError, TypeError, InvalidOperation) as e:
            raise ValueError(f"Cannot convert '{value}' to {target_type}: {str(e)}")
    
    def _to_datetime(self, value: Any) -> Optional[datetime]:
        """Convert value to datetime."""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        elif isinstance(value, (int, float)):
            # Assume Unix timestamp
            return datetime.fromtimestamp(value)
        elif isinstance(value, str):
            # Try common datetime formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d",
                "%H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            raise ValueError(f"Cannot parse datetime string: {value}")
        
        return None
    
    def _to_date(self, value: Any) -> Optional[date]:
        """Convert value to date."""
        if isinstance(value, date):
            return value
        elif isinstance(value, datetime):
            return value.date()
        elif isinstance(value, str):
            # Try common date formats
            formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            
            raise ValueError(f"Cannot parse date string: {value}")
        
        return None
    
    def _to_decimal(self, value: Any) -> Optional[Decimal]:
        """Convert value to Decimal."""
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, str):
            return Decimal(value)
        
        return None
    
    def _to_json_string(self, value: Any) -> str:
        """Convert value to JSON string representation."""
        import json
        return json.dumps(value)
    
    def _validate_field(self, field_name: str, value: Any, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a field according to validation rules."""
        for rule_type, rule_value in rules.items():
            if rule_type == "min_length" and isinstance(value, (str, list)):
                if len(value) < rule_value:
                    return {
                        "valid": False,
                        "message": f"Length {len(value)} is less than minimum {rule_value}"
                    }
            
            elif rule_type == "max_length" and isinstance(value, (str, list)):
                if len(value) > rule_value:
                    return {
                        "valid": False,
                        "message": f"Length {len(value)} exceeds maximum {rule_value}"
                    }
            
            elif rule_type == "min_value" and isinstance(value, (int, float, Decimal)):
                if value < rule_value:
                    return {
                        "valid": False,
                        "message": f"Value {value} is less than minimum {rule_value}"
                    }
            
            elif rule_type == "max_value" and isinstance(value, (int, float, Decimal)):
                if value > rule_value:
                    return {
                        "valid": False,
                        "message": f"Value {value} exceeds maximum {rule_value}"
                    }
            
            elif rule_type == "pattern" and isinstance(value, str):
                import re
                if not re.match(rule_value, value):
                    return {
                        "valid": False,
                        "message": f"Value does not match pattern {rule_value}"
                    }
            
            elif rule_type == "allowed_values" and value not in rule_value:
                return {
                    "valid": False,
                    "message": f"Value {value} is not in allowed values {rule_value}"
                }
        
        return {"valid": True, "message": "Validation passed"}
    
    def should_apply(self, data: Dict[str, Any]) -> bool:
        """Check if this transformer should be applied based on conditions."""
        if not self.config.get("conditions"):
            return True
        
        conditions = self.config["conditions"]
        
        # Check if any required fields exist
        if "required_fields" in conditions:
            required_fields = conditions["required_fields"]
            if not all(field in data for field in required_fields):
                return False
        
        # Check domain/entity conditions for Home Assistant events
        if "domain" in conditions:
            domain = conditions["domain"]
            if data.get("domain") != domain:
                return False
        
        return True
    
    def add_type_mapping(self, field_name: str, target_type: str) -> None:
        """Add a new type mapping."""
        if target_type not in self._type_converters:
            raise ValueError(f"Unsupported target type: {target_type}")
        
        self.type_mappings[field_name] = target_type
        self.logger.info("Added type mapping", field=field_name, target_type=target_type)
    
    def add_validation_rule(self, field_name: str, rule_type: str, rule_value: Any) -> None:
        """Add a validation rule for a field."""
        if field_name not in self.validation_rules:
            self.validation_rules[field_name] = {}
        
        self.validation_rules[field_name][rule_type] = rule_value
        self.logger.info("Added validation rule", field=field_name, rule_type=rule_type, rule_value=rule_value)
    
    def get_type_mappings(self) -> Dict[str, str]:
        """Get current type mappings."""
        return self.type_mappings.copy()
    
    def get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get current validation rules."""
        return self.validation_rules.copy()
