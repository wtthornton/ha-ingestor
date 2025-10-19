# Smart Meter & Energy Correlation Implementation Plan

**Date:** 2025-01-15  
**Author:** BMad Master  
**Status:** Design Complete - Ready for Implementation

---

## 📋 Executive Summary

This plan implements a new architecture for smart meter integration and energy-event correlation analysis, replacing the old "enrich at ingestion" approach with a proper time-series correlation pattern.

### Key Changes:
1. ✅ Smart meter remains a **separate service** (not integrated into event pipeline)
2. ✅ Energy data stored in **InfluxDB as separate measurement** (not enriched into events)
3. ✅ New **energy-event correlation service** (post-processing analysis)
4. ❌ Remove old enrichment code and unused SQLite tables
5. ✅ Add correlation queries to Data API
6. ✅ Update dashboard to show correlations

---

## 🎯 Architecture Decision

### OLD APPROACH (Weather-style enrichment) ❌
```python
# DON'T do this for energy data
event = {
    "entity_id": "switch.lamp",
    "state": "on",
    "weather_temp": 18.2,       # ✅ Good - weather is context
    "energy_power_w": 2450.0    # ❌ Bad - energy is consequence
}
```

### NEW APPROACH (Separate time-series correlation) ✅
```python
# Store separately in InfluxDB
Measurement: home_assistant_events
- timestamp: 15:30:00.000Z
- entity_id: switch.lamp
- state: on
- weather_temp: 18.2  # Still enriched

Measurement: smart_meter
- timestamp: 15:30:00.000Z
- total_power_w: 2450.0

Measurement: smart_meter_circuit
- timestamp: 15:30:00.000Z
- circuit_name: lighting
- power_w: 450.0

# Correlate via query or post-processing
Measurement: event_energy_correlation
- timestamp: 15:30:00.000Z
- entity_id: switch.lamp
- event_state: on
- power_before: 2450.0
- power_after: 2510.0
- power_delta: +60.0
```

---

## 📦 Phase 1: Cleanup Old Code

### 1.1 Remove Energy Enrichment from Events

**Files to Modify:**
- `services/enrichment-pipeline/src/main.py`
- `services/websocket-ingestion/src/main.py`
- `docs/architecture/data-models.md`
- `docs/architecture/database-schema.md`

**Actions:**
1. Remove `energy_consumption` field from `home_assistant_events` measurement
2. Remove any energy enrichment code from enrichment pipeline
3. Update documentation to reflect separate storage

**Code Locations:**
```python
# File: services/enrichment-pipeline/src/main.py
# REMOVE: Any energy enrichment logic (if exists)

# File: docs/architecture/database-schema.md
# Line 47: Remove energy_consumption field from Fields section
- `energy_consumption` - Energy usage in kWh if applicable (float)  # ❌ REMOVE
```

### 1.2 Clean Up SQLite (If Any Energy Tables Exist)

**Check for these tables:**
```sql
-- Check if these exist
SELECT name FROM sqlite_master 
WHERE type='table' 
AND name LIKE '%meter%' 
OR name LIKE '%energy%' 
OR name LIKE '%power%';
```

**Files to Check:**
- `services/data-api/src/database.py`
- `services/data-api/src/models/device.py`
- Any migration scripts in `services/data-api/migrations/`

**Action:** 
- If no energy-specific tables exist → Skip this step
- If tables exist → Create migration to drop them

### 1.3 Remove Test Scripts

**Search for test files:**
```bash
# Find all test files related to smart meter/energy
find . -name "*test*smart*meter*.py"
find . -name "*test*energy*.py"
find . -name "*test*power*.py"
```

**Root directory cleanup:**
```bash
# Remove these if they exist
test_smart_meter.py
test_energy_enrichment.py
test_power_monitoring.py
```

---

## 📦 Phase 2: Implement Smart Meter Service (Separate Pattern)

### 2.1 Smart Meter Service Architecture

**Service:** `services/smart-meter-service/` (Port: 8014)

**Current Status:** 
- ✅ Service structure exists
- ✅ Health check implemented
- ❌ Using mock data (lines 86-101 in `main.py`)
- ❌ No adapter implementations

**Keep As-Is:**
- Service separation ✅
- Port 8014 ✅
- InfluxDB storage ✅
- Health check endpoint ✅

**Implement:**
1. **Adapter Pattern** (already scaffolded)
   ```python
   # File: services/smart-meter-service/src/adapters/home_assistant.py
   class HomeAssistantAdapter(MeterAdapter):
       """Pull energy data from Home Assistant sensors"""
       
       async def fetch_consumption(self, session, api_token, device_id):
           # Query HA for sensor.power_* entities
           # Return standardized format
   ```

2. **InfluxDB Schema** (already correct)
   ```
   Measurement: smart_meter
   Tags:
     meter_type: "generic" | "emporia" | "sense" | "home_assistant"
     meter_source: "ha_integration" | "direct_api"
   Fields:
     total_power_w: float
     daily_kwh: float
   
   Measurement: smart_meter_circuit
   Tags:
     circuit_name: string
     meter_type: string
   Fields:
     power_w: float
     percentage: float
   ```

3. **Polling Frequency:** Every 5 minutes (already configured)

### 2.2 Home Assistant Integration Adapter

**New File:** `services/smart-meter-service/src/adapters/home_assistant.py`

```python
"""
Home Assistant Energy Sensor Adapter
Pulls energy data from HA's existing energy sensors
"""

import aiohttp
from typing import Dict, Any
from datetime import datetime
from .base import MeterAdapter


class HomeAssistantAdapter(MeterAdapter):
    """Adapter for Home Assistant energy monitoring sensors"""
    
    def __init__(self, ha_url: str, ha_token: str):
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json"
        }
    
    async def fetch_consumption(
        self, 
        session: aiohttp.ClientSession, 
        api_token: str, 
        device_id: str
    ) -> Dict[str, Any]:
        """
        Fetch power consumption from Home Assistant sensors
        
        Expected HA sensors:
        - sensor.total_power (whole-home power in watts)
        - sensor.daily_energy (daily energy in kWh)
        - sensor.power_* (individual circuit/device sensors)
        """
        
        # Get whole-home power
        total_power = await self._get_sensor_state(
            session, 
            "sensor.total_power"
        )
        
        # Get daily energy
        daily_kwh = await self._get_sensor_state(
            session,
            "sensor.daily_energy"
        )
        
        # Get circuit-level data (scan for sensor.power_* entities)
        circuits = await self._get_circuit_data(session)
        
        return {
            'total_power_w': float(total_power or 0),
            'daily_kwh': float(daily_kwh or 0),
            'circuits': circuits,
            'timestamp': datetime.now()
        }
    
    async def _get_sensor_state(
        self, 
        session: aiohttp.ClientSession, 
        entity_id: str
    ) -> str:
        """Get state of a single HA sensor"""
        url = f"{self.ha_url}/api/states/{entity_id}"
        
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('state', '0')
                else:
                    return '0'
        except Exception as e:
            logger.error(f"Error fetching {entity_id}: {e}")
            return '0'
    
    async def _get_circuit_data(
        self, 
        session: aiohttp.ClientSession
    ) -> list:
        """Get all power circuit sensors from HA"""
        url = f"{self.ha_url}/api/states"
        circuits = []
        
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    states = await response.json()
                    
                    # Filter for power sensors
                    for state in states:
                        entity_id = state.get('entity_id', '')
                        
                        # Look for energy/power sensors
                        if (entity_id.startswith('sensor.power_') or
                            'power' in state.get('attributes', {}).get('device_class', '')):
                            
                            circuits.append({
                                'name': state.get('attributes', {}).get('friendly_name', entity_id),
                                'entity_id': entity_id,
                                'power_w': float(state.get('state', 0) or 0)
                            })
            
            return circuits
            
        except Exception as e:
            logger.error(f"Error fetching circuit data: {e}")
            return []
```

### 2.3 Update main.py

**File:** `services/smart-meter-service/src/main.py`

**Changes:**
1. Import HA adapter
2. Replace mock data logic (lines 82-136)
3. Add adapter selection based on `METER_TYPE`

```python
# Add after imports
from adapters.home_assistant import HomeAssistantAdapter

class SmartMeterService:
    def __init__(self):
        self.meter_type = os.getenv('METER_TYPE', 'home_assistant')
        self.ha_url = os.getenv('HOME_ASSISTANT_URL')
        self.ha_token = os.getenv('HOME_ASSISTANT_TOKEN')
        # ... existing init code ...
        
        # Initialize adapter
        self.adapter = self._create_adapter()
    
    def _create_adapter(self):
        """Create adapter based on meter type"""
        if self.meter_type == 'home_assistant':
            return HomeAssistantAdapter(self.ha_url, self.ha_token)
        elif self.meter_type == 'emporia':
            # Future: from adapters.emporia import EmporiaAdapter
            # return EmporiaAdapter(...)
            raise NotImplementedError("Emporia adapter not yet implemented")
        elif self.meter_type == 'sense':
            # Future: from adapters.sense import SenseAdapter
            # return SenseAdapter(...)
            raise NotImplementedError("Sense adapter not yet implemented")
        else:
            logger.warning(f"Unknown meter type: {self.meter_type}, using mock data")
            return None
    
    async def fetch_consumption(self) -> Optional[Dict[str, Any]]:
        """Fetch power consumption from configured adapter"""
        
        if not self.adapter:
            # Return mock data if no adapter configured
            return self._get_mock_data()
        
        try:
            # Use adapter to fetch real data
            data = await self.adapter.fetch_consumption(
                self.session,
                self.api_token,
                self.device_id
            )
            
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now()
            
            # Calculate percentages
            for circuit in data.get('circuits', []):
                circuit['percentage'] = (
                    (circuit['power_w'] / data['total_power_w']) * 100 
                    if data['total_power_w'] > 0 else 0
                )
            
            # Update cache and stats
            self.cached_data = data
            self.last_fetch_time = datetime.now()
            self.health_handler.last_successful_fetch = datetime.now()
            self.health_handler.total_fetches += 1
            
            logger.info(
                f"Power: {data['total_power_w']:.0f}W, "
                f"Daily: {data.get('daily_kwh', 0):.1f}kWh"
            )
            
            return data
            
        except Exception as e:
            log_error_with_context(
                logger,
                f"Error fetching consumption: {e}",
                service="smart-meter-service",
                error=str(e)
            )
            self.health_handler.failed_fetches += 1
            return self.cached_data
    
    def _get_mock_data(self) -> Dict[str, Any]:
        """Return mock data for testing (keep existing code)"""
        # Keep lines 86-101 as fallback for testing
        return {
            'total_power_w': 2450.0,
            'daily_kwh': 18.5,
            'circuits': [
                {'name': 'HVAC', 'power_w': 1200.0},
                {'name': 'Kitchen', 'power_w': 450.0},
                # ... etc
            ],
            'timestamp': datetime.now()
        }
```

---

## 📦 Phase 3: Energy-Event Correlation Service

### 3.1 New Service: Energy Correlator

**Location:** `services/energy-correlator/`

**Purpose:** Post-process energy and event data to create correlations

**Port:** 8015

**Structure:**
```
services/energy-correlator/
├── Dockerfile
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── main.py
    ├── correlator.py
    ├── influxdb_client.py
    └── health_check.py
```

### 3.2 Correlator Implementation

**File:** `services/energy-correlator/src/correlator.py`

```python
"""
Energy-Event Correlation Engine
Analyzes relationships between HA events and power consumption changes
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from influxdb_client_3 import InfluxDBClient3, Point

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
        self.client: Optional[InfluxDBClient3] = None
        
        # Configuration
        self.correlation_window_seconds = 10  # Look +/- 10 seconds
        self.min_power_delta = 10.0  # Minimum 10W change to correlate
        
        # Statistics
        self.total_events_processed = 0
        self.correlations_found = 0
        self.correlations_written = 0
    
    async def startup(self):
        """Initialize InfluxDB connection"""
        self.client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_bucket,
            org=self.influxdb_org
        )
        logger.info("Energy correlator started")
    
    async def shutdown(self):
        """Cleanup"""
        if self.client:
            self.client.close()
    
    async def process_recent_events(self, lookback_minutes: int = 5):
        """
        Process recent events and create correlations
        
        Args:
            lookback_minutes: How far back to process events
        """
        logger.info(f"Processing events from last {lookback_minutes} minutes")
        
        # Query recent events
        events = await self._query_recent_events(lookback_minutes)
        
        logger.info(f"Found {len(events)} events to process")
        
        # Process each event
        for event in events:
            await self._correlate_event_with_power(event)
        
        logger.info(
            f"Processed {self.total_events_processed} events, "
            f"found {self.correlations_found} correlations"
        )
    
    async def _query_recent_events(self, minutes: int) -> List[Dict]:
        """Query recent HA events"""
        
        query = f"""
        SELECT 
            time,
            entity_id,
            domain,
            state_value as state,
            previous_state
        FROM home_assistant_events
        WHERE time >= now() - {minutes}m
        AND domain IN ('switch', 'light', 'climate', 'fan', 'cover')
        ORDER BY time
        """
        
        try:
            result = self.client.query(query)
            return list(result)
        except Exception as e:
            logger.error(f"Error querying events: {e}")
            return []
    
    async def _correlate_event_with_power(self, event: Dict):
        """
        Correlate a single event with power changes
        
        Args:
            event: Event data with time, entity_id, state
        """
        self.total_events_processed += 1
        
        event_time = event.get('time')
        entity_id = event.get('entity_id')
        state = event.get('state')
        previous_state = event.get('previous_state')
        
        # Get power before event
        power_before = await self._get_power_at_time(
            event_time - timedelta(seconds=self.correlation_window_seconds)
        )
        
        # Get power after event
        power_after = await self._get_power_at_time(
            event_time + timedelta(seconds=self.correlation_window_seconds)
        )
        
        if power_before is None or power_after is None:
            return
        
        # Calculate delta
        power_delta = power_after - power_before
        
        # Check if significant change
        if abs(power_delta) < self.min_power_delta:
            return
        
        self.correlations_found += 1
        
        # Write correlation
        await self._write_correlation(
            event_time=event_time,
            entity_id=entity_id,
            domain=event.get('domain'),
            state=state,
            previous_state=previous_state,
            power_before=power_before,
            power_after=power_after,
            power_delta=power_delta
        )
    
    async def _get_power_at_time(self, target_time: datetime) -> Optional[float]:
        """Get power reading closest to target time"""
        
        query = f"""
        SELECT 
            time,
            total_power_w
        FROM smart_meter
        WHERE time >= '{target_time - timedelta(seconds=30)}'
        AND time <= '{target_time + timedelta(seconds=30)}'
        ORDER BY time
        LIMIT 1
        """
        
        try:
            result = self.client.query(query)
            records = list(result)
            
            if records:
                return float(records[0].get('total_power_w', 0))
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
            point = Point("event_energy_correlation") \
                .tag("entity_id", entity_id) \
                .tag("domain", domain) \
                .tag("state", state) \
                .tag("previous_state", previous_state) \
                .field("power_before_w", float(power_before)) \
                .field("power_after_w", float(power_after)) \
                .field("power_delta_w", float(power_delta)) \
                .field("power_delta_pct", 
                       float((power_delta / power_before * 100) if power_before > 0 else 0)) \
                .time(event_time)
            
            self.client.write(point)
            self.correlations_written += 1
            
            logger.debug(
                f"Correlation: {entity_id} {previous_state}→{state} "
                f"caused {power_delta:+.0f}W change"
            )
            
        except Exception as e:
            logger.error(f"Error writing correlation: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get correlator statistics"""
        return {
            "total_events_processed": self.total_events_processed,
            "correlations_found": self.correlations_found,
            "correlations_written": self.correlations_written,
            "correlation_rate": (
                (self.correlations_found / self.total_events_processed * 100)
                if self.total_events_processed > 0 else 0
            )
        }
```

### 3.3 Correlator Main Service

**File:** `services/energy-correlator/src/main.py`

```python
"""
Energy-Event Correlation Service
"""

import asyncio
import logging
import os
from aiohttp import web
from dotenv import load_dotenv

from correlator import EnergyEventCorrelator
from health_check import HealthCheckHandler

load_dotenv()
logger = logging.getLogger(__name__)


class EnergyCorrelatorService:
    """Main service for energy-event correlation"""
    
    def __init__(self):
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home_assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'home_assistant_events')
        
        self.correlator = EnergyEventCorrelator(
            self.influxdb_url,
            self.influxdb_token,
            self.influxdb_org,
            self.influxdb_bucket
        )
        
        self.health_handler = HealthCheckHandler()
        self.processing_interval = int(os.getenv('PROCESSING_INTERVAL', '60'))  # 1 minute
    
    async def startup(self):
        """Initialize service"""
        await self.correlator.startup()
        logger.info("Energy Correlator Service started")
    
    async def shutdown(self):
        """Cleanup"""
        await self.correlator.shutdown()
    
    async def run_continuous(self):
        """Run continuous correlation processing"""
        logger.info(f"Starting correlation loop (every {self.processing_interval}s)")
        
        while True:
            try:
                # Process events from last 5 minutes
                await self.correlator.process_recent_events(lookback_minutes=5)
                
                # Update health check
                self.health_handler.last_successful_fetch = datetime.now()
                self.health_handler.total_fetches += 1
                
                # Wait for next interval
                await asyncio.sleep(self.processing_interval)
                
            except Exception as e:
                logger.error(f"Error in correlation loop: {e}")
                self.health_handler.failed_fetches += 1
                await asyncio.sleep(60)


async def create_app(service: EnergyCorrelatorService):
    """Create web application"""
    app = web.Application()
    
    # Health check endpoint
    app.router.add_get('/health', service.health_handler.handle)
    
    # Statistics endpoint
    async def get_statistics(request):
        stats = service.correlator.get_statistics()
        return web.json_response(stats)
    
    app.router.add_get('/statistics', get_statistics)
    
    return app


async def main():
    """Main entry point"""
    service = EnergyCorrelatorService()
    await service.startup()
    
    # Create web app
    app = await create_app(service)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Start HTTP server
    port = int(os.getenv('SERVICE_PORT', '8015'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Service running on port {port}")
    
    try:
        # Run correlation loop
        await service.run_continuous()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.shutdown()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
```

### 3.4 Dockerfile

**File:** `services/energy-correlator/Dockerfile`

```dockerfile
FROM python:3.11-alpine

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8015/health || exit 1

# Run service
CMD ["python", "-m", "src.main"]
```

### 3.5 Requirements

**File:** `services/energy-correlator/requirements.txt`

```
aiohttp==3.9.1
influxdb3-python==0.3.0
python-dotenv==1.0.0
```

---

## 📦 Phase 4: Update Data API

### 4.1 Add Energy Correlation Endpoints

**File:** `services/data-api/src/energy_endpoints.py` (NEW)

```python
"""
Energy Correlation API Endpoints
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from influxdb_client import InfluxDBClientWrapper

logger = logging.getLogger(__name__)
router = APIRouter()


class EnergyCorrelation(BaseModel):
    """Energy correlation data model"""
    timestamp: datetime
    entity_id: str
    domain: str
    state: str
    previous_state: str
    power_before_w: float
    power_after_w: float
    power_delta_w: float
    power_delta_pct: float


class CircuitPowerReading(BaseModel):
    """Circuit-level power reading"""
    timestamp: datetime
    circuit_name: str
    power_w: float
    percentage: float


class EnergyStatistics(BaseModel):
    """Energy usage statistics"""
    total_power_w: float
    daily_kwh: float
    peak_power_w: float
    peak_time: datetime
    average_power_w: float
    circuits: List[Dict[str, Any]]


@router.get("/energy/correlations", response_model=List[EnergyCorrelation])
async def get_energy_correlations(
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    hours: int = Query(24, description="Hours of history to return"),
    min_delta: float = Query(50.0, description="Minimum power delta (watts)")
):
    """
    Get event-energy correlations
    
    Shows which events caused significant power changes
    """
    
    try:
        # Build query
        filters = []
        if entity_id:
            filters.append(f"entity_id = '{entity_id}'")
        if domain:
            filters.append(f"domain = '{domain}'")
        
        filters.append(f"ABS(power_delta_w) >= {min_delta}")
        
        where_clause = " AND ".join(filters) if filters else "1=1"
        
        query = f"""
        SELECT 
            time,
            entity_id,
            domain,
            state,
            previous_state,
            power_before_w,
            power_after_w,
            power_delta_w,
            power_delta_pct
        FROM event_energy_correlation
        WHERE time >= now() - {hours}h
        AND {where_clause}
        ORDER BY time DESC
        LIMIT 1000
        """
        
        # Execute query (implement with your InfluxDB client)
        # results = await influxdb_client.query(query)
        
        return []  # Return parsed results
        
    except Exception as e:
        logger.error(f"Error getting energy correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/current", response_model=EnergyStatistics)
async def get_current_energy():
    """Get current energy consumption"""
    
    try:
        query = """
        SELECT 
            LAST(total_power_w) as current_power,
            LAST(daily_kwh) as daily_energy
        FROM smart_meter
        WHERE time >= now() - 5m
        """
        
        # Execute and return
        # Implement query execution
        
        return EnergyStatistics(
            total_power_w=0,
            daily_kwh=0,
            peak_power_w=0,
            peak_time=datetime.now(),
            average_power_w=0,
            circuits=[]
        )
        
    except Exception as e:
        logger.error(f"Error getting current energy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/circuits", response_model=List[CircuitPowerReading])
async def get_circuit_power(
    hours: int = Query(24, description="Hours of history")
):
    """Get circuit-level power readings"""
    
    try:
        query = f"""
        SELECT 
            time,
            circuit_name,
            power_w,
            percentage
        FROM smart_meter_circuit
        WHERE time >= now() - {hours}h
        ORDER BY time DESC
        """
        
        # Execute and return
        return []
        
    except Exception as e:
        logger.error(f"Error getting circuit power: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy/device-impact/{entity_id}")
async def get_device_energy_impact(
    entity_id: str,
    days: int = Query(7, description="Days of history")
):
    """
    Get energy impact analysis for a specific device
    
    Returns:
    - Average power change when device turns on/off
    - Total energy attributed to device
    - Usage patterns
    """
    
    try:
        query = f"""
        SELECT 
            state,
            AVG(power_delta_w) as avg_delta,
            COUNT(*) as event_count,
            SUM(power_delta_w) as total_delta
        FROM event_energy_correlation
        WHERE entity_id = '{entity_id}'
        AND time >= now() - {days}d
        GROUP BY state
        """
        
        # Execute and return analysis
        return {
            "entity_id": entity_id,
            "on_power_draw": 0,
            "daily_energy_kwh": 0,
            "usage_count": 0,
            "cost_estimate": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting device impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.2 Register Router in Main

**File:** `services/data-api/src/main.py`

```python
# Add import
from energy_endpoints import router as energy_router

# Register router
app.include_router(energy_router, prefix="/api/v1", tags=["energy"])
```

---

## 📦 Phase 5: Update Dashboard

### 5.1 Add Energy Correlation View

**File:** `services/health-dashboard/src/components/tabs/EnergyTab.tsx` (NEW)

```typescript
import React, { useState, useEffect } from 'react';
import { apiService } from '../../services/api';

interface EnergyCorrelation {
  timestamp: string;
  entity_id: string;
  domain: string;
  state: string;
  previous_state: string;
  power_before_w: number;
  power_after_w: number;
  power_delta_w: number;
  power_delta_pct: number;
}

export const EnergyTab: React.FC<{ darkMode: boolean }> = ({ darkMode }) => {
  const [correlations, setCorrelations] = useState<EnergyCorrelation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCorrelations();
  }, []);

  const fetchCorrelations = async () => {
    try {
      // Implement API call
      // const data = await apiService.getEnergyCorrelations();
      // setCorrelations(data);
    } catch (error) {
      console.error('Error fetching correlations:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Energy Correlations</h2>
      
      {/* Current Power */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-blue-100 dark:bg-blue-900">
          <p className="text-sm">Current Power</p>
          <p className="text-3xl font-bold">2,450W</p>
        </div>
        {/* More cards */}
      </div>

      {/* Correlations Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr>
              <th>Time</th>
              <th>Device</th>
              <th>State Change</th>
              <th>Power Delta</th>
            </tr>
          </thead>
          <tbody>
            {correlations.map((corr, idx) => (
              <tr key={idx}>
                <td>{new Date(corr.timestamp).toLocaleString()}</td>
                <td>{corr.entity_id}</td>
                <td>{corr.previous_state} → {corr.state}</td>
                <td className={corr.power_delta_w > 0 ? 'text-red-600' : 'text-green-600'}>
                  {corr.power_delta_w > 0 ? '+' : ''}{corr.power_delta_w.toFixed(0)}W
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

---

## 📦 Phase 6: Docker Compose Updates

### 6.1 Add Energy Correlator Service

**File:** `docker-compose.yml`

```yaml
services:
  # ... existing services ...

  energy-correlator:
    build:
      context: ./services/energy-correlator
      dockerfile: Dockerfile
    container_name: homeiq-energy-correlator
    ports:
      - "8015:8015"
    environment:
      - INFLUXDB_URL=http://influxdb:8086
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - INFLUXDB_ORG=home_assistant
      - INFLUXDB_BUCKET=home_assistant_events
      - PROCESSING_INTERVAL=60
      - LOG_LEVEL=INFO
    depends_on:
      - influxdb
      - smart-meter-service
    networks:
      - homeiq-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8015/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 6.2 Update Smart Meter Service Config

```yaml
  smart-meter-service:
    environment:
      - METER_TYPE=home_assistant
      - HOME_ASSISTANT_URL=${HOME_ASSISTANT_URL}
      - HOME_ASSISTANT_TOKEN=${HOME_ASSISTANT_TOKEN}
      # ... other env vars ...
```

---

## 📦 Phase 7: Testing & Validation

### 7.1 Test Scripts

**File:** `tests/test_energy_correlation.py`

```python
"""
Test energy correlation functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_smart_meter_polling():
    """Test smart meter polls and stores data"""
    # Test that smart meter service polls HA
    # Test data is written to InfluxDB
    pass


@pytest.mark.asyncio
async def test_energy_correlation():
    """Test correlation engine finds event-power relationships"""
    # Create test event
    # Create test power readings
    # Run correlator
    # Verify correlation is created
    pass


@pytest.mark.asyncio
async def test_correlation_api():
    """Test API endpoints return correlation data"""
    # Query correlation API
    # Verify response format
    pass
```

### 7.2 Validation Checklist

- [ ] Smart meter service polls HA sensors
- [ ] Power data written to `smart_meter` measurement
- [ ] Correlation service runs every minute
- [ ] Correlations written to `event_energy_correlation` measurement
- [ ] Data API returns correlation data
- [ ] Dashboard displays energy tab
- [ ] No energy enrichment in events (verified in InfluxDB)
- [ ] Old test scripts removed
- [ ] Documentation updated

---

## 📋 Implementation Order

### Week 1: Cleanup & Foundation
1. ✅ Phase 1: Clean up old code (1 day)
2. ✅ Phase 2: Implement smart meter HA adapter (2 days)
3. ✅ Test smart meter polling (1 day)

### Week 2: Correlation Service
4. ✅ Phase 3: Implement energy correlator (3 days)
5. ✅ Test correlation logic (1 day)

### Week 3: API & Dashboard
6. ✅ Phase 4: Add Data API endpoints (2 days)
7. ✅ Phase 5: Update dashboard (2 days)
8. ✅ Phase 7: Integration testing (1 day)

---

## 📊 Success Metrics

### Before (Old Approach)
- ❌ Energy data enriched into events (wrong pattern)
- ❌ Duplicate storage (events + smart meter)
- ❌ No temporal correlation analysis
- ❌ Mock data only

### After (New Approach)
- ✅ Energy stored separately (correct pattern)
- ✅ Single source of truth (smart_meter measurement)
- ✅ Temporal correlation analysis (post-processing)
- ✅ Real HA integration (live data)
- ✅ Queryable correlations via API
- ✅ Dashboard visualization

---

## 🚀 Deployment

### Environment Variables

```bash
# .env additions
METER_TYPE=home_assistant
HOME_ASSISTANT_URL=http://homeassistant:8123
HOME_ASSISTANT_TOKEN=your_ha_token

# Energy correlator
ENERGY_CORRELATION_ENABLED=true
PROCESSING_INTERVAL=60
```

### Deployment Commands

```bash
# Build new services
docker-compose build smart-meter-service energy-correlator

# Deploy
docker-compose up -d smart-meter-service energy-correlator

# Verify
docker-compose ps
docker-compose logs -f energy-correlator
```

---

## 📖 Documentation Updates

Files to update:
1. `docs/architecture.md` - Add energy correlator service
2. `docs/architecture/database-schema.md` - Document new measurements
3. `services/smart-meter-service/README.md` - Update with HA adapter
4. `services/energy-correlator/README.md` - New service docs
5. `docs/stories/` - Create new story for energy correlation

---

## ✅ Completion Checklist

- [ ] Phase 1: Cleanup complete
- [ ] Phase 2: Smart meter HA integration working
- [ ] Phase 3: Energy correlator deployed
- [ ] Phase 4: Data API endpoints tested
- [ ] Phase 5: Dashboard updated
- [ ] Phase 6: Docker compose updated
- [ ] Phase 7: All tests passing
- [ ] Documentation updated
- [ ] Deployed to production

---

**END OF PLAN**

