"""
Event Processor for Home Assistant Events
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class EventProcessor:
    """Processes and validates Home Assistant events"""
    
    def __init__(self):
        self.processed_events = 0
        self.validation_errors = 0
        self.last_processed_time: Optional[datetime] = None
        
        # Event validation rules
        self.required_fields = {
            "state_changed": ["event_type", "old_state", "new_state"],
            "call_service": ["event_type", "domain", "service", "service_data"],
            "service_registered": ["event_type", "domain", "service"],
            "service_removed": ["event_type", "domain", "service"]
        }
    
    def validate_event(self, event_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate Home Assistant event data
        
        Args:
            event_data: The event data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if event_data is a dictionary
            if not isinstance(event_data, dict):
                return False, "Event data must be a dictionary"
            
            # Check for required top-level fields
            if "event_type" not in event_data:
                return False, "Missing required field: event_type"
            
            event_type = event_data["event_type"]
            
            # Check for required fields based on event type
            if event_type in self.required_fields:
                required_fields = self.required_fields[event_type]
                for field in required_fields:
                    if field not in event_data:
                        return False, f"Missing required field for {event_type}: {field}"
            
            # Validate state_changed events specifically
            if event_type == "state_changed":
                return self._validate_state_changed_event(event_data)
            
            # Basic validation passed
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating event: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _validate_state_changed_event(self, event_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate state_changed event specifically
        
        Args:
            event_data: The state_changed event data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check old_state
            old_state = event_data.get("old_state")
            if old_state is not None and not isinstance(old_state, dict):
                return False, "old_state must be a dictionary or null"
            
            # Check new_state
            new_state = event_data.get("new_state")
            if new_state is None:
                return False, "new_state is required for state_changed events"
            
            if not isinstance(new_state, dict):
                return False, "new_state must be a dictionary"
            
            # Check required fields in new_state
            required_new_state_fields = ["entity_id", "state"]
            for field in required_new_state_fields:
                if field not in new_state:
                    return False, f"Missing required field in new_state: {field}"
            
            # Validate entity_id format
            entity_id = new_state.get("entity_id")
            if not isinstance(entity_id, str) or "." not in entity_id:
                return False, "entity_id must be a string in format 'domain.entity'"
            
            # Validate state value
            state_value = new_state.get("state")
            if not isinstance(state_value, str):
                return False, "state must be a string"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating state_changed event: {e}")
            return False, f"State validation error: {str(e)}"
    
    def extract_event_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from Home Assistant event
        
        Args:
            event_data: The raw event data
            
        Returns:
            Dictionary with extracted event data
        """
        try:
            extracted = {
                "event_type": event_data.get("event_type"),
                "timestamp": datetime.now().isoformat(),
                "raw_data": event_data.copy()
            }
            
            event_type = event_data.get("event_type")
            
            if event_type == "state_changed":
                extracted.update(self._extract_state_changed_data(event_data))
            elif event_type == "call_service":
                extracted.update(self._extract_call_service_data(event_data))
            else:
                # Generic extraction for other event types
                extracted["generic_data"] = event_data
            
            return extracted
            
        except Exception as e:
            logger.error(f"Error extracting event data: {e}")
            return {
                "event_type": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "raw_data": event_data
            }
    
    def _extract_state_changed_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from state_changed event
        
        Args:
            event_data: The state_changed event data
            
        Returns:
            Dictionary with extracted state_changed data
        """
        old_state = event_data.get("old_state", {})
        new_state = event_data.get("new_state", {})
        
        return {
            "entity_id": new_state.get("entity_id"),
            "domain": new_state.get("entity_id", "").split(".")[0] if new_state.get("entity_id") else None,
            "old_state": {
                "state": old_state.get("state") if old_state else None,
                "attributes": old_state.get("attributes", {}) if old_state else {},
                "last_changed": old_state.get("last_changed") if old_state else None,
                "last_updated": old_state.get("last_updated") if old_state else None
            },
            "new_state": {
                "state": new_state.get("state"),
                "attributes": new_state.get("attributes", {}),
                "last_changed": new_state.get("last_changed"),
                "last_updated": new_state.get("last_updated")
            },
            "state_change": {
                "from": old_state.get("state") if old_state else None,
                "to": new_state.get("state"),
                "changed": old_state.get("state") != new_state.get("state") if old_state else True
            }
        }
    
    def _extract_call_service_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from call_service event
        
        Args:
            event_data: The call_service event data
            
        Returns:
            Dictionary with extracted call_service data
        """
        return {
            "domain": event_data.get("domain"),
            "service": event_data.get("service"),
            "service_data": event_data.get("service_data", {}),
            "entity_id": event_data.get("entity_id")
        }
    
    def process_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and validate a Home Assistant event
        
        Args:
            event_data: The raw event data
            
        Returns:
            Processed event data if valid, None if invalid
        """
        try:
            # Validate event
            is_valid, error_msg = self.validate_event(event_data)
            
            if not is_valid:
                self.validation_errors += 1
                logger.warning(f"Event validation failed: {error_msg}")
                logger.debug(f"Invalid event data: {event_data}")
                return None
            
            # Extract structured data
            processed_data = self.extract_event_data(event_data)
            
            # Update statistics
            self.processed_events += 1
            self.last_processed_time = datetime.now()
            
            # Log processed event
            self._log_processed_event(processed_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            self.validation_errors += 1
            return None
    
    def _log_processed_event(self, processed_data: Dict[str, Any]):
        """
        Log processed event information
        
        Args:
            processed_data: The processed event data
        """
        try:
            event_type = processed_data.get("event_type")
            
            if event_type == "state_changed":
                entity_id = processed_data.get("entity_id")
                state_change = processed_data.get("state_change", {})
                from_state = state_change.get("from")
                to_state = state_change.get("to")
                
                logger.info(f"Processed state_changed: {entity_id} ({from_state} -> {to_state})")
            else:
                logger.info(f"Processed {event_type} event")
                
        except Exception as e:
            logger.error(f"Error logging processed event: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get event processing statistics
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            "processed_events": self.processed_events,
            "validation_errors": self.validation_errors,
            "success_rate": (self.processed_events / (self.processed_events + self.validation_errors) * 100) 
                           if (self.processed_events + self.validation_errors) > 0 else 0,
            "last_processed_time": self.last_processed_time.isoformat() if self.last_processed_time else None
        }
    
    def reset_statistics(self):
        """Reset processing statistics"""
        self.processed_events = 0
        self.validation_errors = 0
        self.last_processed_time = None
        logger.info("Event processing statistics reset")
