"""
InfluxDB Client for storing normalized Home Assistant events
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)


class InfluxDBClientWrapper:
    """Wrapper for InfluxDB operations"""
    
    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client: Optional[InfluxDBClient] = None
        self.write_api = None
        self.query_api = None
        
        # Statistics
        self.points_written = 0
        self.write_errors = 0
        self.last_write_time: Optional[datetime] = None
    
    async def connect(self) -> bool:
        """
        Connect to InfluxDB
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org
            )
            
            # Test connection
            await self._test_connection()
            
            # Initialize APIs
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            
            logger.info(f"Connected to InfluxDB at {self.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            return False
    
    async def _test_connection(self):
        """Test InfluxDB connection"""
        try:
            # Try to query buckets to test connection
            buckets_api = self.client.buckets_api()
            buckets = buckets_api.find_buckets()
            
            # Check if our bucket exists
            bucket_found = any(bucket.name == self.bucket for bucket in buckets.buckets)
            if not bucket_found:
                logger.warning(f"Bucket '{self.bucket}' not found in InfluxDB")
            
        except Exception as e:
            logger.error(f"InfluxDB connection test failed: {e}")
            raise
    
    async def write_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Write a normalized event to InfluxDB
        
        Args:
            event_data: The normalized event data
            
        Returns:
            True if write successful, False otherwise
        """
        try:
            if not self.client or not self.write_api:
                logger.error("InfluxDB client not connected")
                return False
            
            # Create InfluxDB point
            point = self._create_point_from_event(event_data)
            
            if not point:
                logger.warning("Failed to create InfluxDB point from event")
                return False
            
            # Write point
            self.write_api.write(bucket=self.bucket, record=point)
            
            # Update statistics
            self.points_written += 1
            self.last_write_time = datetime.now()
            
            logger.debug(f"Successfully wrote event to InfluxDB: {event_data.get('event_type', 'unknown')}")
            return True
            
        except Exception as e:
            self.write_errors += 1
            error_msg = str(e)
            
            # Handle field type conflicts specifically
            if "field type conflict" in error_msg:
                logger.warning(f"InfluxDB field type conflict (dropping event): {error_msg}")
                # For field type conflicts, we'll drop the event to prevent data corruption
                # This is a temporary solution until we can clean up the existing data
                return False
            else:
                logger.error(f"Error writing event to InfluxDB: {e}")
                return False
    
    def _create_point_from_event(self, event_data: Dict[str, Any]) -> Optional[Point]:
        """
        Create InfluxDB point from event data
        
        Args:
            event_data: The normalized event data
            
        Returns:
            InfluxDB Point or None if creation fails
        """
        try:
            event_type = event_data.get("event_type")
            if not event_type:
                return None
            
            # Create base point
            point = Point("home_assistant_events")
            
            # Set timestamp
            timestamp = event_data.get("timestamp")
            if timestamp:
                point.time(timestamp)
            
            # Add tags
            point.tag("event_type", event_type)
            
            # Add entity metadata as tags
            entity_metadata = event_data.get("entity_metadata", {})
            if entity_metadata:
                if entity_metadata.get("domain"):
                    point.tag("domain", entity_metadata["domain"])
                if entity_metadata.get("device_class"):
                    point.tag("device_class", entity_metadata["device_class"])
                if entity_metadata.get("entity_category"):
                    point.tag("entity_category", entity_metadata["entity_category"])
            
            # Epic 23.2: Add device_id and area_id as tags for spatial analytics
            device_id = event_data.get("device_id")
            if device_id:
                point.tag("device_id", device_id)
            
            area_id = event_data.get("area_id")
            if area_id:
                point.tag("area_id", area_id)
            
            # Add integration source tag (where the entity comes from)
            integration = entity_metadata.get("platform") or entity_metadata.get("integration")
            if integration:
                point.tag("integration", integration)
            
            # Add time_of_day tag for temporal analytics
            if timestamp:
                try:
                    from datetime import datetime as dt
                    if isinstance(timestamp, str):
                        ts = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        ts = timestamp
                    
                    hour = ts.hour
                    if 5 <= hour < 12:
                        time_of_day = "morning"
                    elif 12 <= hour < 17:
                        time_of_day = "afternoon"
                    elif 17 <= hour < 21:
                        time_of_day = "evening"
                    else:
                        time_of_day = "night"
                    
                    point.tag("time_of_day", time_of_day)
                except Exception as e:
                    logger.debug(f"Could not determine time_of_day: {e}")
            
            # Add fields based on event type
            if event_type == "state_changed":
                point = self._add_state_changed_fields(point, event_data)
            else:
                # Generic event fields
                point.field("raw_data", str(event_data))
            
            return point
            
        except Exception as e:
            logger.error(f"Error creating InfluxDB point: {e}")
            return None
    
    def _add_state_changed_fields(self, point: Point, event_data: Dict[str, Any]) -> Point:
        """
        Add state_changed specific fields to InfluxDB point
        
        Args:
            point: The InfluxDB point
            event_data: The event data
            
        Returns:
            Updated InfluxDB point
        """
        try:
            # Add entity_id as tag (check both new_state and top-level for WebSocket service format)
            new_state = event_data.get("new_state", {})
            entity_id = new_state.get("entity_id") or event_data.get("entity_id")
            if entity_id:
                point.tag("entity_id", entity_id)
            
            # Add state fields (ensure consistent string type for InfluxDB)
            if "state" in new_state:
                point.field("state", str(new_state["state"]))
            
            # Add old state for comparison (ensure consistent string type for InfluxDB)
            old_state = event_data.get("old_state", {})
            if old_state and "state" in old_state:
                point.field("old_state", str(old_state["state"]))
            
            # Add attributes as fields - preserve normalized types from data_normalizer
            # Type normalization happens in data_normalizer.py, we just pass through the values
            attributes = new_state.get("attributes", {})
            for key, value in attributes.items():
                if self._is_valid_field_value(value):
                    # Keep the type as-is from normalization (boolean, float, or string)
                    # data_normalizer.py already handled type coercion
                    point.field(f"attr_{key}", value)
            
            # Add entity metadata fields
            entity_metadata = event_data.get("entity_metadata", {})
            if entity_metadata.get("friendly_name"):
                point.field("friendly_name", entity_metadata["friendly_name"])
            if entity_metadata.get("unit_of_measurement"):
                point.field("unit_of_measurement", entity_metadata["unit_of_measurement"])
            if entity_metadata.get("icon"):
                point.field("icon", entity_metadata["icon"])
            
            # Epic 23.1: Add context fields for automation causality tracking
            context_id = event_data.get("context_id")
            if context_id:
                point.field("context_id", context_id)
            
            context_parent_id = event_data.get("context_parent_id")
            if context_parent_id:
                point.field("context_parent_id", context_parent_id)
            
            context_user_id = event_data.get("context_user_id")
            if context_user_id:
                point.field("context_user_id", context_user_id)
            
            # Epic 23.3: Add duration_in_state for time-based analytics
            duration_in_state = event_data.get("duration_in_state")
            if duration_in_state is not None:
                point.field("duration_in_state_seconds", float(duration_in_state))
            
            # Epic 23.5: Add device metadata for reliability analysis
            device_metadata = event_data.get("device_metadata")
            if device_metadata:
                if device_metadata.get("manufacturer"):
                    point.field("manufacturer", str(device_metadata["manufacturer"]))
                if device_metadata.get("model"):
                    point.field("model", str(device_metadata["model"]))
                if device_metadata.get("sw_version"):
                    point.field("sw_version", str(device_metadata["sw_version"]))
            
            # Weather enrichment: Extract weather data added by websocket-ingestion
            # Weather data is attached to events by WeatherEnrichmentService in websocket-ingestion
            weather = event_data.get("weather", {})
            logger.warning(f"[WEATHER_EXTRACT] Weather data present: {weather is not None and len(weather) > 0}, Keys: {list(weather.keys()) if weather else 'None'}, Sample: {str(weather)[:200]}")
            if weather:
                # Add weather temperature
                if weather.get("temperature") is not None:
                    point.field("weather_temp", float(weather["temperature"]))
                
                # Add weather humidity
                if weather.get("humidity") is not None:
                    point.field("weather_humidity", int(weather["humidity"]))
                
                # Add weather pressure
                if weather.get("pressure") is not None:
                    point.field("weather_pressure", float(weather["pressure"]))
                
                # Add wind speed
                if weather.get("wind_speed") is not None:
                    point.field("wind_speed", float(weather["wind_speed"]))
                
                # Add weather description
                if weather.get("weather_description"):
                    point.field("weather_description", str(weather["weather_description"]))
                
                # Add weather condition as tag for efficient filtering
                if weather.get("weather_condition"):
                    point.tag("weather_condition", str(weather["weather_condition"]))
                
                logger.debug(f"Added weather enrichment fields: temp={weather.get('temperature')}, humidity={weather.get('humidity')}")
            
            return point
            
        except Exception as e:
            logger.error(f"Error adding state_changed fields: {e}")
            return point
    
    def _normalize_field_value(self, value: Any) -> str:
        """
        Normalize field value to string for consistent InfluxDB schema
        
        Args:
            value: The value to normalize
            
        Returns:
            Normalized string value
        """
        try:
            # Convert None to empty string
            if value is None:
                return ""
            
            # Convert booleans to lowercase string (true/false)
            if isinstance(value, bool):
                return str(value).lower()
            
            # Convert to string for all other types
            return str(value)
            
        except Exception as e:
            logger.warning(f"Failed to normalize field value {value}: {e}")
            return ""
    
    def _is_valid_field_value(self, value: Any) -> bool:
        """
        Check if a value is valid for InfluxDB field
        
        Args:
            value: The value to check
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # InfluxDB supports: string, float, integer, boolean
            if isinstance(value, (str, int, float, bool)):
                return True
            
            # Convert None to empty string
            if value is None:
                return True
            
            # Complex objects (dict, list) are not valid
            if isinstance(value, (dict, list)):
                return False
            
            # Try to convert to string for other types
            str(value)
            return True
            
        except Exception:
            return False
    
    async def write_events_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Write multiple events to InfluxDB in batch
        
        Args:
            events: List of normalized event data
            
        Returns:
            Number of events successfully written
        """
        try:
            if not self.client or not self.write_api:
                logger.error("InfluxDB client not connected")
                return 0
            
            # Create points
            points = []
            for event_data in events:
                point = self._create_point_from_event(event_data)
                if point:
                    points.append(point)
            
            if not points:
                logger.warning("No valid points to write")
                return 0
            
            # Write batch
            self.write_api.write(bucket=self.bucket, record=points)
            
            # Update statistics
            written_count = len(points)
            self.points_written += written_count
            self.last_write_time = datetime.now()
            
            logger.info(f"Successfully wrote {written_count} events to InfluxDB")
            return written_count
            
        except Exception as e:
            self.write_errors += 1
            logger.error(f"Error writing batch to InfluxDB: {e}")
            return 0
    
    async def query_events(self, query: str) -> List[Dict[str, Any]]:
        """
        Query events from InfluxDB
        
        Args:
            query: InfluxDB query string
            
        Returns:
            List of query results
        """
        try:
            if not self.client or not self.query_api:
                logger.error("InfluxDB client not connected")
                return []
            
            # Execute query
            result = self.query_api.query(query=query, org=self.org)
            
            # Convert to list of dictionaries
            events = []
            for table in result:
                for record in table.records:
                    # Handle time conversion properly
                    time_value = record.get_time()
                    if hasattr(time_value, 'isoformat'):
                        time_str = time_value.isoformat()
                    else:
                        time_str = str(time_value)
                    
                    event = {
                        "time": time_str,
                        "measurement": record.get_measurement(),
                        "fields": record.values,
                        "tags": record.tags
                    }
                    events.append(event)
            
            logger.debug(f"Query returned {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Error querying InfluxDB: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get InfluxDB client statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "points_written": self.points_written,
            "write_errors": self.write_errors,
            "success_rate": (self.points_written / (self.points_written + self.write_errors) * 100) 
                           if (self.points_written + self.write_errors) > 0 else 0,
            "last_write_time": self.last_write_time.isoformat() if self.last_write_time else None,
            "connected": self.client is not None,
            "bucket": self.bucket,
            "org": self.org
        }
    
    async def close(self):
        """Close InfluxDB connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("InfluxDB connection closed")
        except Exception as e:
            logger.error(f"Error closing InfluxDB connection: {e}")
        finally:
            # Always reset client references
            self.client = None
            self.write_api = None
            self.query_api = None
