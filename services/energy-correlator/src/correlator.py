"""
Energy-Event Correlation Engine
Analyzes relationships between HA events and power consumption changes
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from influxdb_client import Point

from .influxdb_wrapper import InfluxDBWrapper

logger = logging.getLogger(__name__)


class EnergyEventCorrelator:
    """
    Correlates Home Assistant events with power consumption changes
    Creates derived metrics in InfluxDB for analysis
    """
    
    def __init__(
        self,
        influxdb_url: str,
        influxdb_token: str,
        influxdb_org: str,
        influxdb_bucket: str
    ):
        self.influxdb_url = influxdb_url
        self.influxdb_token = influxdb_token
        self.influxdb_org = influxdb_org
        self.influxdb_bucket = influxdb_bucket
        self.client: Optional[InfluxDBWrapper] = None
        
        # Configuration
        self.correlation_window_seconds = 10  # Look +/- 10 seconds
        self.min_power_delta = 10.0  # Minimum 10W change to correlate
        
        # Statistics
        self.total_events_processed = 0
        self.correlations_found = 0
        self.correlations_written = 0
        self.errors = 0
    
    async def startup(self):
        """Initialize InfluxDB connection"""
        try:
            self.client = InfluxDBWrapper(
                self.influxdb_url,
                self.influxdb_token,
                self.influxdb_org,
                self.influxdb_bucket
            )
            
            self.client.connect()
            logger.info(f"Energy correlator connected to InfluxDB at {self.influxdb_url}")
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    async def shutdown(self):
        """Cleanup"""
        if self.client:
            try:
                self.client.close()
                logger.info("Energy correlator shut down")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
    
    async def process_recent_events(self, lookback_minutes: int = 5):
        """
        Process recent events and create correlations
        
        Args:
            lookback_minutes: How far back to process events (default: 5 minutes)
        """
        logger.info(f"Processing events from last {lookback_minutes} minutes")
        
        try:
            # Query recent events
            events = await self._query_recent_events(lookback_minutes)
            
            if not events:
                logger.debug("No events to process")
                return
            
            logger.info(f"Found {len(events)} events to process")
            
            # Process each event
            for event in events:
                await self._correlate_event_with_power(event)
            
            logger.info(
                f"Processed {self.total_events_processed} events, "
                f"found {self.correlations_found} correlations, "
                f"wrote {self.correlations_written} to InfluxDB"
            )
            
        except Exception as e:
            logger.error(f"Error processing events: {e}")
            self.errors += 1
    
    async def _query_recent_events(self, minutes: int) -> List[Dict]:
        """
        Query recent HA events that could affect power consumption
        
        Focuses on:
        - Switches (lights, plugs)
        - Climate devices (HVAC, thermostats)
        - Fans
        - Covers (blinds - affect heating/cooling)
        """
        
        # Calculate time range
        now = datetime.utcnow()
        start_time = now - timedelta(minutes=minutes)
        
        # Flux query for InfluxDB 2.x
        flux_query = f'''
        from(bucket: "{self.influxdb_bucket}")
          |> range(start: {start_time.isoformat()}Z, stop: {now.isoformat()}Z)
          |> filter(fn: (r) => r["_measurement"] == "home_assistant_events")
          |> filter(fn: (r) => 
              r["domain"] == "switch" or 
              r["domain"] == "light" or 
              r["domain"] == "climate" or 
              r["domain"] == "fan" or 
              r["domain"] == "cover"
          )
          |> filter(fn: (r) => r["_field"] == "state_value")
          |> sort(columns: ["_time"])
        '''
        
        try:
            logger.debug(f"Querying events since {start_time.isoformat()}")
            results = self.client.query(flux_query)
            
            # Convert to event format
            events = []
            for record in results:
                events.append({
                    'time': record['time'],
                    'entity_id': record.get('entity_id', ''),
                    'domain': record.get('domain', ''),
                    'state': record.get('_value', ''),
                    'previous_state': record.get('previous_state', '')
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    async def _correlate_event_with_power(self, event: Dict):
        """
        Correlate a single event with power changes
        
        Looks for power changes within ±10 seconds of the event
        
        Args:
            event: Event data with time, entity_id, state, previous_state
        """
        self.total_events_processed += 1
        
        event_time = event.get('time')
        entity_id = event.get('entity_id')
        domain = event.get('domain')
        state = event.get('state')
        previous_state = event.get('previous_state')
        
        # Get power before event (5 seconds before)
        time_before = event_time - timedelta(seconds=5)
        power_before = await self._get_power_at_time(time_before)
        
        # Get power after event (5 seconds after)
        time_after = event_time + timedelta(seconds=5)
        power_after = await self._get_power_at_time(time_after)
        
        if power_before is None or power_after is None:
            logger.debug(f"No power data found for event {entity_id} at {event_time}")
            return
        
        # Calculate delta
        power_delta = power_after - power_before
        
        # Check if significant change
        if abs(power_delta) < self.min_power_delta:
            logger.debug(
                f"Power change too small for {entity_id}: {power_delta:.1f}W "
                f"(threshold: {self.min_power_delta}W)"
            )
            return
        
        self.correlations_found += 1
        
        # Write correlation
        await self._write_correlation(
            event_time=event_time,
            entity_id=entity_id,
            domain=domain,
            state=state,
            previous_state=previous_state,
            power_before=power_before,
            power_after=power_after,
            power_delta=power_delta
        )
    
    async def _get_power_at_time(self, target_time: datetime) -> Optional[float]:
        """
        Get power reading closest to target time
        
        Looks within ±30 seconds of target time
        
        Args:
            target_time: Target timestamp
            
        Returns:
            Power reading in watts, or None if not found
        """
        
        start_time = target_time - timedelta(seconds=30)
        end_time = target_time + timedelta(seconds=30)
        
        # Flux query for smart_meter measurement
        flux_query = f'''
        from(bucket: "{self.influxdb_bucket}")
          |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
          |> filter(fn: (r) => r["_measurement"] == "smart_meter")
          |> filter(fn: (r) => r["_field"] == "total_power_w")
          |> sort(columns: ["_time"])
          |> limit(n: 1)
        '''
        
        try:
            results = self.client.query(flux_query)
            
            if results:
                power = results[0].get('_value')
                if power is not None:
                    return float(power)
            
            return None
            
        except Exception as e:
            logger.error(f"Error querying power: {e}")
            return None
    
    async def _write_correlation(
        self,
        event_time: datetime,
        entity_id: str,
        domain: str,
        state: str,
        previous_state: str,
        power_before: float,
        power_after: float,
        power_delta: float
    ):
        """Write correlation to InfluxDB"""
        
        try:
            # Calculate percentage change
            power_delta_pct = (
                (power_delta / power_before * 100) 
                if power_before > 0 else 0
            )
            
            point = Point("event_energy_correlation") \
                .tag("entity_id", entity_id) \
                .tag("domain", domain) \
                .tag("state", state) \
                .tag("previous_state", previous_state) \
                .field("power_before_w", float(power_before)) \
                .field("power_after_w", float(power_after)) \
                .field("power_delta_w", float(power_delta)) \
                .field("power_delta_pct", float(power_delta_pct)) \
                .time(event_time)
            
            self.client.write_point(point)
            self.correlations_written += 1
            
            logger.info(
                f"Correlation: {entity_id} [{previous_state}→{state}] "
                f"caused {power_delta:+.0f}W change "
                f"({power_delta_pct:+.1f}%)"
            )
            
        except Exception as e:
            logger.error(f"Error writing correlation: {e}")
            self.errors += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get correlator statistics"""
        
        correlation_rate = (
            (self.correlations_found / self.total_events_processed * 100)
            if self.total_events_processed > 0 else 0
        )
        
        write_success_rate = (
            (self.correlations_written / self.correlations_found * 100)
            if self.correlations_found > 0 else 100
        )
        
        return {
            "total_events_processed": self.total_events_processed,
            "correlations_found": self.correlations_found,
            "correlations_written": self.correlations_written,
            "correlation_rate_pct": round(correlation_rate, 2),
            "write_success_rate_pct": round(write_success_rate, 2),
            "errors": self.errors,
            "config": {
                "correlation_window_seconds": self.correlation_window_seconds,
                "min_power_delta_w": self.min_power_delta
            }
        }
    
    def reset_statistics(self):
        """Reset statistics counters"""
        self.total_events_processed = 0
        self.correlations_found = 0
        self.correlations_written = 0
        self.errors = 0
        logger.info("Statistics reset")

