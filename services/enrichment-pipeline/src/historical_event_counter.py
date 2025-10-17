"""
Historical Event Counter for Persistent Total Event Tracking
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from influxdb_wrapper import InfluxDBClientWrapper

logger = logging.getLogger(__name__)


class HistoricalEventCounter:
    """Manages persistent total event counts across service restarts"""
    
    def __init__(self, influxdb_client: InfluxDBClientWrapper):
        """
        Initialize historical event counter
        
        Args:
            influxdb_client: InfluxDB client wrapper
        """
        self.influxdb_client = influxdb_client
        self.historical_totals = {
            'total_events_processed': 0,
            'events_by_type': {},
            'last_updated': None
        }
        self._initialized = False
    
    async def initialize_historical_totals(self) -> Dict[str, Any]:
        """
        Query InfluxDB for historical event totals and initialize counters
        
        Returns:
            Dictionary with historical totals
        """
        if self._initialized:
            logger.info("Historical totals already initialized")
            return self.historical_totals
        
        try:
            logger.info("🔍 Querying InfluxDB for historical processed event totals...")
            
            # Query total processed events from InfluxDB - count all records
            total_events_query = '''
                from(bucket: "home_assistant_events")
                |> range(start: 0)
                |> filter(fn: (r) => r._measurement == "home_assistant_events")
                |> count()
                |> group()
                |> sum(column: "_value")
            '''
            
            # Query processed events by type
            events_by_type_query = '''
                from(bucket: "home_assistant_events")
                |> range(start: 0)
                |> filter(fn: (r) => r._measurement == "home_assistant_events")
                |> group(columns: ["event_type"])
                |> count()
            '''
            
            # Execute queries using the enrichment pipeline's InfluxDB client
            total_result = await self._execute_influx_query(total_events_query)
            type_result = await self._execute_influx_query(events_by_type_query)
            
            # Parse results
            total_events = self._parse_count_result(total_result)
            events_by_type = self._parse_grouped_count_result(type_result)
            
            # Update historical totals
            self.historical_totals = {
                'total_events_processed': total_events,
                'events_by_type': events_by_type,
                'last_updated': datetime.now()
            }
            
            self._initialized = True
            
            logger.info(f"✅ Historical processed totals initialized: {total_events:,} total events")
            logger.info(f"📊 Processed events by type: {events_by_type}")
            
            return self.historical_totals
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize historical processed totals: {e}")
            # Return zeros as fallback
            self.historical_totals = {
                'total_events_processed': 0,
                'events_by_type': {},
                'last_updated': datetime.now()
            }
            self._initialized = True
            return self.historical_totals
    
    async def _execute_influx_query(self, query: str) -> Optional[Any]:
        """Execute InfluxDB query safely"""
        try:
            if not self.influxdb_client.client:
                logger.warning("InfluxDB not connected, cannot query historical totals")
                return None
            
            result = await self.influxdb_client.query_events(query)
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute InfluxDB query: {e}")
            return None
    
    def _parse_count_result(self, result) -> int:
        """Parse InfluxDB count query result"""
        try:
            if not result:
                return 0
            
            total_count = 0
            for table in result:
                for record in table.records:
                    if record.get_field() == "_value":
                        total_count = int(record.get_value())
                        break
            
            return total_count
            
        except Exception as e:
            logger.error(f"Error parsing count result: {e}")
            return 0
    
    def _parse_grouped_count_result(self, result) -> Dict[str, int]:
        """Parse InfluxDB grouped count query result"""
        try:
            if not result:
                return {}
            
            events_by_type = {}
            for table in result:
                for record in table.records:
                    if record.get_field() == "_value":
                        event_type = record.get_field_by_key("event_type") or "unknown"
                        count = int(record.get_value())
                        events_by_type[event_type] = count
            
            return events_by_type
            
        except Exception as e:
            logger.error(f"Error parsing grouped count result: {e}")
            return {}
    
    def get_historical_totals(self) -> Dict[str, Any]:
        """Get current historical totals"""
        return self.historical_totals.copy()
    
    def add_to_totals(self, events_processed: int, events_by_type: Dict[str, int]):
        """Add new events to historical totals"""
        if not self._initialized:
            logger.warning("Historical totals not initialized, cannot add to totals")
            return
        
        self.historical_totals['total_events_processed'] += events_processed
        self.historical_totals['last_updated'] = datetime.now()
        
        # Update events by type
        for event_type, count in events_by_type.items():
            current_count = self.historical_totals['events_by_type'].get(event_type, 0)
            self.historical_totals['events_by_type'][event_type] = current_count + count
    
    def get_total_events_processed(self) -> int:
        """Get total events processed (historical + current session)"""
        return self.historical_totals.get('total_events_processed', 0)
    
    def is_initialized(self) -> bool:
        """Check if historical totals are initialized"""
        return self._initialized
