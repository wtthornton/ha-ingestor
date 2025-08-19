"""Attribute-based filter for Home Assistant events."""

from typing import Any, Dict, List, Optional, Union, Callable
from .base import Filter
from ..models.events import Event

class AttributeFilter(Filter):
    """Filter events based on attribute values and changes."""
    
    def __init__(self, 
                 attribute: str,
                 value: Any = None,
                 operator: str = "eq",
                 name: str = None):
        """Initialize attribute filter.
        
        Args:
            attribute: Name of the attribute to filter on
            value: Value to compare against (optional for some operators)
            operator: Comparison operator ("eq", "ne", "gt", "lt", "gte", "lte", "in", "nin", "contains", "regex", "custom")
            name: Optional name for the filter
        """
        super().__init__(name or f"attribute_filter_{attribute}_{operator}")
        
        self.attribute = attribute
        self.value = value
        self.operator = operator
        
        # Validate operator
        self._validate_operator()
        
        # Compile regex if needed
        self._compiled_regex = None
        if operator == "regex" and value:
            import re
            try:
                self._compiled_regex = re.compile(value, re.IGNORECASE)
            except re.error as e:
                self.logger.warning("Invalid regex pattern, using exact match", 
                                  pattern=value, error=str(e))
                self.operator = "eq"
        
        self.logger.info("Attribute filter initialized", 
                        attribute=attribute,
                        operator=operator,
                        value=value)
    
    def _validate_operator(self) -> None:
        """Validate the comparison operator."""
        valid_operators = ["eq", "ne", "gt", "lt", "gte", "lte", "in", "nin", "contains", "regex", "custom"]
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator '{self.operator}'. Must be one of: {valid_operators}")
    
    async def should_process(self, event: Event) -> bool:
        """Check if event attribute matches the filter criteria.
        
        Args:
            event: The event to check
            
        Returns:
            True if attribute matches criteria, False otherwise
        """
        if not event.attributes:
            self.logger.debug("Event has no attributes, filtering out", 
                            event_entity_id=event.entity_id)
            return False
        
        # Get attribute value
        attribute_value = event.attributes.get(self.attribute)
        
        if attribute_value is None:
            self.logger.debug("Attribute not found in event", 
                            attribute=self.attribute,
                            event_entity_id=event.entity_id)
            return False
        
        # Apply comparison
        try:
            should_process = self._compare_values(attribute_value, self.value)
            
            if should_process:
                self.logger.debug("Attribute matches filter criteria", 
                                attribute=self.attribute,
                                value=attribute_value,
                                operator=self.operator,
                                event_entity_id=event.entity_id)
            else:
                self.logger.debug("Attribute filtered out", 
                                attribute=self.attribute,
                                value=attribute_value,
                                operator=self.operator,
                                event_entity_id=event.entity_id)
            
            return should_process
            
        except Exception as e:
            self.logger.error("Error comparing attribute values", 
                            attribute=self.attribute,
                            value=attribute_value,
                            operator=self.operator,
                            error=str(e))
            # On error, allow the event to pass through
            return True
    
    def _compare_values(self, attribute_value: Any, filter_value: Any) -> bool:
        """Compare attribute value against filter value using the specified operator.
        
        Args:
            attribute_value: Value from the event attribute
            filter_value: Value to compare against
            
        Returns:
            True if comparison passes, False otherwise
        """
        if self.operator == "eq":
            return attribute_value == filter_value
        
        elif self.operator == "ne":
            return attribute_value != filter_value
        
        elif self.operator == "gt":
            return self._numeric_compare(attribute_value, filter_value, lambda a, b: a > b)
        
        elif self.operator == "lt":
            return self._numeric_compare(attribute_value, filter_value, lambda a, b: a < b)
        
        elif self.operator == "gte":
            return self._numeric_compare(attribute_value, filter_value, lambda a, b: a >= b)
        
        elif self.operator == "lte":
            return self._numeric_compare(attribute_value, filter_value, lambda a, b: a <= b)
        
        elif self.operator == "in":
            if not isinstance(filter_value, (list, tuple, set)):
                filter_value = [filter_value]
            return attribute_value in filter_value
        
        elif self.operator == "nin":
            if not isinstance(filter_value, (list, tuple, set)):
                filter_value = [filter_value]
            return attribute_value not in filter_value
        
        elif self.operator == "contains":
            if isinstance(attribute_value, str) and isinstance(filter_value, str):
                return filter_value.lower() in attribute_value.lower()
            elif isinstance(attribute_value, (list, tuple, set)):
                return filter_value in attribute_value
            return False
        
        elif self.operator == "regex":
            if self._compiled_regex and isinstance(attribute_value, str):
                return bool(self._compiled_regex.search(attribute_value))
            return False
        
        elif self.operator == "custom":
            # Custom comparison function
            if callable(filter_value):
                return bool(filter_value(attribute_value))
            return False
        
        return False
    
    def _numeric_compare(self, a: Any, b: Any, compare_func: Callable) -> bool:
        """Perform numeric comparison with type conversion.
        
        Args:
            a: First value
            b: Second value
            compare_func: Comparison function
            
        Returns:
            Result of comparison
        """
        try:
            # Convert to float for comparison
            a_float = float(a)
            b_float = float(b)
            return compare_func(a_float, b_float)
        except (ValueError, TypeError):
            return False
    
    def update_attribute(self, attribute: str) -> None:
        """Update the attribute to filter on.
        
        Args:
            attribute: New attribute name
        """
        self.attribute = attribute
        self.logger.info("Updated attribute filter", new_attribute=attribute)
    
    def update_value(self, value: Any) -> None:
        """Update the filter value.
        
        Args:
            value: New filter value
        """
        self.value = value
        self.logger.info("Updated filter value", new_value=value)
    
    def update_operator(self, operator: str) -> None:
        """Update the comparison operator.
        
        Args:
            operator: New operator
        """
        old_operator = self.operator
        self.operator = operator
        self._validate_operator()
        self.logger.info("Updated filter operator", 
                        old_operator=old_operator,
                        new_operator=operator)
    
    def get_filter_config(self) -> Dict[str, Any]:
        """Get current filter configuration.
        
        Returns:
            Dictionary with filter configuration
        """
        return {
            "attribute": self.attribute,
            "operator": self.operator,
            "value": self.value
        }
