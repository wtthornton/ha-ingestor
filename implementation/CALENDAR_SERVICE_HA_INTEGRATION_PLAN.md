# Calendar Service - Home Assistant Integration Plan

**Date:** October 16, 2025  
**Status:** Planning  
**Epic:** Data Enhancement  
**Objective:** Refactor calendar service to use Home Assistant as master data source instead of Google Calendar

---

## Executive Summary

The current calendar service connects directly to Google Calendar using OAuth2 to fetch events and predict home occupancy. This plan refactors the service to connect to Home Assistant instead, allowing HA to manage all calendar integrations (Google, iCloud, CalDAV, etc.) centrally. The service will consume calendar data via HA's REST and WebSocket APIs.

**Key Benefits:**
- **Centralized Calendar Management**: Home Assistant handles all calendar integrations
- **Multi-Source Support**: Access multiple calendars (Google, iCloud, CalDAV, Outlook) through single interface
- **Simplified Authentication**: Use HA long-lived token instead of OAuth2 flow
- **Consistency**: Same authentication pattern as other services in the project
- **Enhanced Automation**: Direct access to HA calendar automation capabilities
- **Real-time Updates**: WebSocket support for calendar event changes

---

## Research Summary

### Home Assistant Calendar Integration

Based on research using Context7 KB, Home Assistant provides comprehensive calendar support:

#### 1. **REST API Endpoints**
- **GET /api/calendars/<calendar_entity_id>**: Retrieve calendar events within a time range
  - Query params: `start` (timestamp), `end` (timestamp)
  - Returns: Array of CalendarEvent objects with `summary`, `start`, `end`, `description`, `location`
  - Authentication: Bearer token in header

#### 2. **WebSocket API Support**
- **subscribe_trigger**: Subscribe to calendar event triggers (start/end)
- **subscribe_events**: Listen to state_changed events for calendar entities
- Event types: `start` (event begins), `end` (event ends)
- Supports offset triggers (fire before/after event)

#### 3. **Calendar Entity Model**
- **Entity ID Format**: `calendar.{calendar_name}`
- **State**: `on` (active event), `off` (no active event)
- **Event Properties**:
  - `summary`: Event title
  - `start`: Start time (dateTime or date for all-day)
  - `end`: End time (dateTime or date for all-day)
  - `description`: Event description
  - `location`: Event location
  - `all_day`: Boolean for all-day events

#### 4. **Supported Calendar Integrations**
Home Assistant natively supports:
- Google Calendar
- CalDAV (iCloud, Nextcloud, etc.)
- Office 365
- Todoist
- Local Calendar
- ICS file imports

---

## Current Implementation Analysis

### Current Architecture
```
Calendar Service
    ↓ (OAuth2)
Google Calendar API
    ↓
Store Predictions → InfluxDB
```

### Current Features
1. OAuth2 authentication with Google
2. Fetch events every 15 minutes
3. Predict occupancy based on:
   - Event locations (contains "HOME" or "WFH")
   - Work-from-home detection
   - Arrival time calculations
4. Store predictions in InfluxDB
5. Health check endpoint

### Current Dependencies
```python
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.110.0
```

---

## Proposed Architecture

### New Architecture
```
Calendar Service
    ↓ (WebSocket + REST API)
Home Assistant
    ↓ (Various integrations)
Multiple Calendar Sources (Google, iCloud, CalDAV, etc.)
    ↓
Store Predictions → InfluxDB
```

### Integration Patterns

#### Pattern 1: REST API (Polling - Simpler)
```python
# Fetch events every N minutes
GET /api/calendars/calendar.primary?start=2025-10-16T00:00:00Z&end=2025-10-17T00:00:00Z
Authorization: Bearer <HA_TOKEN>
```

#### Pattern 2: WebSocket (Real-time - Advanced)
```python
# Subscribe to calendar triggers
{
    "type": "subscribe_trigger",
    "trigger": {
        "platform": "calendar",
        "event": "start",
        "entity_id": "calendar.primary"
    }
}
```

#### Pattern 3: Hybrid (Recommended)
- Use REST API for periodic full refresh (every 15-30 minutes)
- Use WebSocket for real-time event start/end notifications
- Best of both worlds: completeness + real-time updates

---

## Detailed Implementation Plan

### Phase 1: Core Infrastructure (2-3 hours)

#### Task 1.1: Home Assistant Client Module
Create `src/ha_client.py` with:

```python
"""Home Assistant REST API Client"""
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime

class HomeAssistantCalendarClient:
    """Client for Home Assistant Calendar API"""
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def get_calendars(self) -> List[str]:
        """Get list of available calendar entities"""
        # GET /api/states?filter=calendar
        
    async def get_events(
        self, 
        calendar_id: str, 
        start: datetime, 
        end: datetime
    ) -> List[Dict[str, Any]]:
        """Get calendar events within time range"""
        # GET /api/calendars/{calendar_id}?start=...&end=...
    
    async def get_calendar_state(self, calendar_id: str) -> Dict[str, Any]:
        """Get current calendar entity state"""
        # GET /api/states/calendar.{calendar_id}
```

**Acceptance Criteria:**
- [ ] Client successfully connects to HA instance
- [ ] Retrieves list of calendar entities
- [ ] Fetches events within date range
- [ ] Proper error handling and retries
- [ ] Connection pooling via aiohttp session

#### Task 1.2: WebSocket Event Subscriber (Optional - Advanced)
Create `src/ha_websocket.py` with:

```python
"""Home Assistant WebSocket Client for Calendar Events"""
import asyncio
import json
from typing import Callable, Optional

class HomeAssistantWebSocketClient:
    """WebSocket client for real-time calendar updates"""
    
    async def subscribe_calendar_events(
        self, 
        calendar_id: str,
        event_callback: Callable
    ):
        """Subscribe to calendar event start/end triggers"""
        # Use websocket_client pattern from websocket-ingestion service
```

**Acceptance Criteria:**
- [ ] WebSocket connection to HA established
- [ ] Successfully subscribes to calendar triggers
- [ ] Receives event start/end notifications
- [ ] Auto-reconnect on connection loss
- [ ] Reuse connection_manager pattern from websocket-ingestion

#### Task 1.3: Event Parser
Create `src/event_parser.py` with:

```python
"""Parse Home Assistant calendar events"""
from datetime import datetime
from typing import Dict, Any, List

class CalendarEventParser:
    """Parse and enrich calendar events"""
    
    @staticmethod
    def parse_ha_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse HA calendar event to internal format"""
        # Extract summary, start, end, location
        # Handle both dateTime and date (all-day events)
        # Detect WFH/HOME patterns
    
    @staticmethod
    def detect_occupancy_indicators(event: Dict[str, Any]) -> Dict[str, bool]:
        """Detect home/WFH indicators in event"""
        # Check summary for WFH, Home Office, etc.
        # Check location for HOME, residence, etc.
        # Return: {is_wfh, is_home, is_away}
```

**Acceptance Criteria:**
- [ ] Correctly parses dateTime and date formats
- [ ] Handles timezone conversions
- [ ] Detects WFH patterns in summary/location
- [ ] Handles missing/optional fields gracefully

### Phase 2: Service Refactoring (3-4 hours)

#### Task 2.1: Refactor CalendarService Class
Update `src/main.py`:

```python
class CalendarService:
    """Home Assistant Calendar integration for occupancy prediction"""
    
    def __init__(self):
        # Remove Google OAuth configuration
        self.ha_url = os.getenv('HOME_ASSISTANT_URL')
        self.ha_token = os.getenv('HOME_ASSISTANT_TOKEN')
        self.calendar_entities = os.getenv('CALENDAR_ENTITIES', 'calendar.primary').split(',')
        
        # InfluxDB configuration (unchanged)
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        # ... rest of InfluxDB config
        
        # Components
        self.ha_client: Optional[HomeAssistantCalendarClient] = None
        self.event_parser = CalendarEventParser()
        self.health_handler = HealthCheckHandler()
        
        # Validate
        if not self.ha_url or not self.ha_token:
            raise ValueError("HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN required")
    
    async def startup(self):
        """Initialize service"""
        logger.info("Initializing Calendar Service (HA Integration)...")
        
        # Initialize HA client
        self.ha_client = HomeAssistantCalendarClient(
            base_url=self.ha_url,
            token=self.ha_token
        )
        
        # Test connection
        calendars = await self.ha_client.get_calendars()
        logger.info(f"Found {len(calendars)} calendar(s)")
        
        self.health_handler.ha_connected = True
        
        # Initialize InfluxDB client (unchanged)
        self.influxdb_client = InfluxDBClient3(...)
        
        logger.info("Calendar Service initialized")
    
    async def get_today_events(self) -> List[Dict[str, Any]]:
        """Fetch today's calendar events from Home Assistant"""
        try:
            now = datetime.now()
            end_of_day = now.replace(hour=23, minute=59, second=59)
            
            all_events = []
            for calendar_id in self.calendar_entities:
                events = await self.ha_client.get_events(
                    calendar_id=calendar_id,
                    start=now,
                    end=end_of_day
                )
                
                # Parse and enrich events
                for event in events:
                    parsed = self.event_parser.parse_ha_event(event)
                    occupancy = self.event_parser.detect_occupancy_indicators(parsed)
                    parsed.update(occupancy)
                    all_events.append(parsed)
            
            return all_events
            
        except Exception as e:
            logger.error(f"Error fetching calendar events: {e}")
            self.health_handler.ha_connected = False
            return []
```

**Acceptance Criteria:**
- [ ] Remove all Google Calendar dependencies
- [ ] Use HA client for event fetching
- [ ] Support multiple calendar entities
- [ ] Maintain existing occupancy prediction logic
- [ ] Proper error handling and logging

#### Task 2.2: Update Occupancy Prediction Logic
The `predict_home_status()` method can remain largely unchanged, as it operates on parsed events:

```python
async def predict_home_status(self) -> Dict[str, Any]:
    """Predict home occupancy based on calendar"""
    # This logic remains the same - operates on parsed events
    # No changes needed if event format is consistent
```

**Acceptance Criteria:**
- [ ] Prediction logic works with new event format
- [ ] Maintains same prediction accuracy
- [ ] All edge cases handled (no events, all-day events, etc.)

#### Task 2.3: Update Health Check
Update `src/health_check.py`:

```python
class HealthCheckHandler:
    """Health check for calendar service"""
    
    def __init__(self):
        self.ha_connected = False  # Changed from oauth_valid
        self.last_successful_fetch: Optional[datetime] = None
        self.total_fetches = 0
        self.failed_fetches = 0
        self.calendar_count = 0
    
    async def handle(self, request):
        """Health check endpoint"""
        health_status = {
            'status': 'healthy' if self.ha_connected else 'unhealthy',
            'ha_connection': 'connected' if self.ha_connected else 'disconnected',
            'last_fetch': self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            'total_fetches': self.total_fetches,
            'failed_fetches': self.failed_fetches,
            'calendar_count': self.calendar_count,
            'service': 'calendar-service'
        }
        
        status_code = 200 if self.ha_connected else 503
        return web.json_response(health_status, status=status_code)
```

**Acceptance Criteria:**
- [ ] Health check reflects HA connection status
- [ ] Returns appropriate status codes
- [ ] Includes relevant metrics

### Phase 3: Configuration & Deployment (1-2 hours)

#### Task 3.1: Update Requirements
Update `requirements.txt`:

```python
# Remove Google Calendar dependencies:
# google-auth==2.25.2
# google-auth-oauthlib==1.2.0
# google-auth-httplib2==0.2.0
# google-api-python-client==2.110.0

# Add/keep:
python-dotenv==1.0.0
influxdb3-python==0.3.0
aiohttp==3.9.1  # For HA client
```

**Acceptance Criteria:**
- [ ] All Google dependencies removed
- [ ] Required dependencies added
- [ ] No version conflicts

#### Task 3.2: Update Environment Variables
Create `infrastructure/env.calendar.template`:

```bash
# Calendar Service Configuration
SERVICE_PORT=8013

# Home Assistant Connection
HOME_ASSISTANT_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=your_long_lived_access_token_here

# Calendar Entities (comma-separated)
# List of calendar entity IDs to monitor
CALENDAR_ENTITIES=calendar.primary,calendar.work,calendar.personal

# Service Configuration
FETCH_INTERVAL=900  # 15 minutes

# InfluxDB Configuration
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your_influxdb_token
INFLUXDB_ORG=home_assistant
INFLUXDB_BUCKET=events

# Logging
LOG_LEVEL=INFO
```

**Update `.env.example`**:
```bash
# Calendar Service Configuration
CALENDAR_ENTITIES=calendar.primary,calendar.work
```

**Acceptance Criteria:**
- [ ] Template file created with all required variables
- [ ] .env.example updated
- [ ] Clear documentation for each variable

#### Task 3.3: Update Docker Configuration
No changes needed to Dockerfile, but update docker-compose.yml:

```yaml
calendar-service:
  build:
    context: ./services/calendar-service
    dockerfile: Dockerfile
  container_name: calendar-service
  environment:
    - SERVICE_PORT=8013
    - HOME_ASSISTANT_URL=${HOME_ASSISTANT_URL}
    - HOME_ASSISTANT_TOKEN=${HOME_ASSISTANT_TOKEN}
    - CALENDAR_ENTITIES=${CALENDAR_ENTITIES:-calendar.primary}
    - FETCH_INTERVAL=${CALENDAR_FETCH_INTERVAL:-900}
    - INFLUXDB_URL=${INFLUXDB_URL}
    - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
    - INFLUXDB_ORG=${INFLUXDB_ORG}
    - INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
  ports:
    - "8013:8013"
  depends_on:
    - influxdb
  networks:
    - ha-ingestor-network
  restart: unless-stopped
```

**Acceptance Criteria:**
- [ ] Environment variables properly mapped
- [ ] Dependencies correctly specified
- [ ] Network configuration correct

#### Task 3.4: Update Documentation
Update `services/calendar-service/README.md`:

```markdown
# Calendar Service - Home Assistant Integration

Home Assistant calendar integration for occupancy prediction and smart home preparation.

## Purpose

Enable predictive automation by analyzing calendar events from Home Assistant - prepare home before arrival, enable eco mode when away all day, optimize based on work-from-home schedules.

## Features

- Connects to Home Assistant calendar entities
- Supports multiple calendar sources (Google, iCloud, CalDAV, etc.)
- Fetches calendar events every 15 minutes
- Predicts home occupancy based on event locations
- Detects work-from-home days
- Calculates estimated arrival times
- Stores predictions in InfluxDB

## Prerequisites

### Home Assistant Calendar Setup

1. **Configure Calendar Integration in Home Assistant**
   - Go to Settings → Devices & Services → Add Integration
   - Choose your calendar provider (Google, CalDAV, etc.)
   - Follow setup wizard for authentication
   - Note the entity ID (e.g., `calendar.primary`)

2. **Create Long-Lived Access Token**
   - In Home Assistant: Profile → Security → Long-Lived Access Tokens
   - Create new token for "Calendar Service"
   - Copy token securely

## Environment Variables

Required:
- `HOME_ASSISTANT_URL` - Home Assistant instance URL
- `HOME_ASSISTANT_TOKEN` - Long-lived access token
- `CALENDAR_ENTITIES` - Comma-separated calendar entity IDs
- `INFLUXDB_TOKEN` - InfluxDB token

Optional:
- `FETCH_INTERVAL` - Fetch interval in seconds (default: 900 = 15 min)

## Configuration

### 1. Add to .env

```bash
HOME_ASSISTANT_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=your_long_lived_access_token
CALENDAR_ENTITIES=calendar.primary,calendar.work
```

### 2. Calendar Entity Discovery

List available calendars:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://homeassistant.local:8123/api/states | \
     jq '.[] | select(.entity_id | startswith("calendar."))'
```

## InfluxDB Schema

```
Measurement: occupancy_prediction
Tags:
  source: "calendar"
  user: "primary"
Fields:
  currently_home: boolean
  wfh_today: boolean
  confidence: float (0-1)
  hours_until_arrival: float
```

## Supported Calendar Platforms

The service works with any calendar integration supported by Home Assistant:
- Google Calendar
- CalDAV (iCloud, Nextcloud, etc.)
- Office 365 / Outlook
- Local Calendar
- ICS file imports
- Todoist

## Occupancy Detection

The service analyzes calendar events for occupancy indicators:

**Work From Home Detection:**
- Summary contains: "WFH", "Work From Home", "Home Office"
- Location contains: "Home", "Residence"

**Away Detection:**
- Location is outside home
- Event during business hours
- No home indicators

## API Endpoints

- `GET /health` - Health check and statistics

## Automation Examples

### Prepare Home Before Arrival
```yaml
automation:
  - alias: "Prepare Home Before Arrival"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('sensor.occupancy_prediction', 'hours_until_arrival') | float < 0.5 }}
    condition:
      - condition: template
        value_template: >
          {{ states('sensor.occupancy_prediction') == 'away' }}
    action:
      - service: climate.set_temperature
        data:
          entity_id: climate.living_room
          temperature: 72
      - service: light.turn_on
        entity_id: light.entry
```

## Troubleshooting

### Connection Issues
- Verify HOME_ASSISTANT_URL is accessible from container
- Check token has not expired
- Ensure calendar entities exist in HA

### No Events Returned
- Verify calendar entity IDs are correct
- Check calendar has upcoming events
- Review calendar integration status in HA

## License

MIT License
```

**Acceptance Criteria:**
- [ ] README completely updated with HA integration info
- [ ] Remove all Google Calendar references
- [ ] Add HA setup instructions
- [ ] Include troubleshooting section

### Phase 4: Testing & Validation (2-3 hours)

#### Task 4.1: Unit Tests
Create `tests/test_ha_client.py`:

```python
"""Unit tests for Home Assistant client"""
import pytest
from unittest.mock import AsyncMock, patch
from src.ha_client import HomeAssistantCalendarClient

@pytest.mark.asyncio
async def test_get_calendars():
    """Test fetching calendar list"""
    client = HomeAssistantCalendarClient(
        base_url="http://localhost:8123",
        token="test_token"
    )
    # Mock aiohttp response
    # Assert correct API call
    # Assert correct parsing

@pytest.mark.asyncio
async def test_get_events():
    """Test fetching calendar events"""
    # Test with various date ranges
    # Test with empty results
    # Test error handling
```

Create `tests/test_event_parser.py`:
```python
"""Unit tests for event parser"""
import pytest
from src.event_parser import CalendarEventParser
from datetime import datetime

def test_parse_datetime_event():
    """Test parsing event with dateTime"""
    event = {
        "summary": "Team Meeting",
        "start": {"dateTime": "2025-10-16T14:00:00-07:00"},
        "end": {"dateTime": "2025-10-16T15:00:00-07:00"},
        "location": "Conference Room"
    }
    result = CalendarEventParser.parse_ha_event(event)
    assert result['summary'] == "Team Meeting"
    # More assertions

def test_parse_all_day_event():
    """Test parsing all-day event"""
    event = {
        "summary": "Holiday",
        "start": {"date": "2025-10-16"},
        "end": {"date": "2025-10-17"}
    }
    result = CalendarEventParser.parse_ha_event(event)
    # Assert all-day handling

def test_detect_wfh():
    """Test WFH detection"""
    event = {"summary": "WFH Day", "location": ""}
    indicators = CalendarEventParser.detect_occupancy_indicators(event)
    assert indicators['is_wfh'] is True
```

**Acceptance Criteria:**
- [ ] 80%+ code coverage
- [ ] All edge cases tested
- [ ] Mock external dependencies
- [ ] Tests pass in CI/CD

#### Task 4.2: Integration Tests
Create `tests/test_integration.py`:

```python
"""Integration tests with live HA instance (optional)"""
import pytest
import os
from src.main import CalendarService

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('RUN_INTEGRATION_TESTS'), reason="Integration tests disabled")
async def test_full_service_flow():
    """Test complete service flow with live HA"""
    service = CalendarService()
    await service.startup()
    
    # Fetch events
    events = await service.get_today_events()
    assert isinstance(events, list)
    
    # Predict occupancy
    prediction = await service.predict_home_status()
    assert 'currently_home' in prediction
    
    await service.shutdown()
```

**Acceptance Criteria:**
- [ ] Integration tests with real HA instance
- [ ] Test with multiple calendar types
- [ ] Validate end-to-end flow

#### Task 4.3: Manual Testing Checklist

**Pre-deployment Testing:**
- [ ] Service starts successfully
- [ ] Connects to HA instance
- [ ] Discovers calendar entities
- [ ] Fetches events correctly
- [ ] Parses all event types (dateTime, date)
- [ ] Detects WFH indicators accurately
- [ ] Generates occupancy predictions
- [ ] Stores data in InfluxDB
- [ ] Health check returns correct status
- [ ] Handles HA connection loss gracefully
- [ ] Reconnects automatically after disruption
- [ ] Works with multiple calendars
- [ ] Proper logging at all levels

**Performance Testing:**
- [ ] Fetch time < 2 seconds for 50 events
- [ ] Memory usage stable over 24 hours
- [ ] No memory leaks
- [ ] CPU usage < 5% average

### Phase 5: Deployment & Migration (1 hour)

#### Task 5.1: Migration Guide
Create `implementation/CALENDAR_SERVICE_MIGRATION_GUIDE.md`:

```markdown
# Calendar Service Migration Guide

## Migration from Google Calendar to Home Assistant

### Step 1: Set Up Calendar in Home Assistant

1. Open Home Assistant → Settings → Devices & Services
2. Click "Add Integration"
3. Search for your calendar provider:
   - Google Calendar
   - CalDAV (for iCloud, Nextcloud)
   - Office 365
4. Follow authentication flow
5. Note the calendar entity ID (e.g., `calendar.primary`)

### Step 2: Create Long-Lived Access Token

1. Click your profile → Security
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Name: "Calendar Service"
5. Copy the token (you won't see it again!)

### Step 3: Update Environment Variables

Remove old variables:
```bash
# Remove these from .env:
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

Add new variables:
```bash
# Add these to .env:
HOME_ASSISTANT_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=eyJhbGc...
CALENDAR_ENTITIES=calendar.primary
```

### Step 4: Restart Calendar Service

```bash
docker-compose restart calendar-service
```

### Step 5: Verify Operation

Check logs:
```bash
docker-compose logs -f calendar-service
```

Look for:
- "Calendar Service initialized"
- "Found N calendar(s)"
- No connection errors

Check health endpoint:
```bash
curl http://localhost:8013/health
```

### Rollback Plan

If issues occur:
1. Stop new calendar service
2. Restore old environment variables
3. Redeploy previous version
4. Report issues with logs
```

**Acceptance Criteria:**
- [ ] Clear step-by-step migration instructions
- [ ] Rollback plan documented
- [ ] Verification steps included

#### Task 5.2: Deployment

```bash
# 1. Stop existing service
docker-compose stop calendar-service

# 2. Update environment variables
# Edit .env file with new variables

# 3. Rebuild service
docker-compose build calendar-service

# 4. Start service
docker-compose up -d calendar-service

# 5. Monitor logs
docker-compose logs -f calendar-service
```

**Acceptance Criteria:**
- [ ] Clean deployment without errors
- [ ] Service starts and connects to HA
- [ ] No data loss during migration
- [ ] All features working as expected

---

## Success Criteria

### Functional Requirements
- [ ] Service connects to Home Assistant successfully
- [ ] Retrieves calendar events from HA calendar entities
- [ ] Supports multiple calendar sources through HA
- [ ] Maintains existing occupancy prediction accuracy
- [ ] Stores predictions in InfluxDB with same schema
- [ ] Health check endpoint functional
- [ ] Handles connection failures gracefully

### Non-Functional Requirements
- [ ] Authentication simplified (no OAuth2 flow needed)
- [ ] Response time < 2 seconds for typical queries
- [ ] Memory footprint reduced by ~30% (no Google libraries)
- [ ] 99.9% uptime with auto-reconnect
- [ ] Comprehensive error logging
- [ ] 80%+ test coverage

### Documentation
- [ ] README updated with HA integration instructions
- [ ] Environment variable template created
- [ ] Migration guide completed
- [ ] Code comments added for new modules
- [ ] Architecture diagram updated

---

## Risk Assessment & Mitigation

### Risk 1: Breaking Change for Existing Users
**Impact:** High  
**Probability:** High  
**Mitigation:**
- Provide detailed migration guide
- Support gradual rollout
- Maintain backward compatibility during transition period
- Provide rollback instructions

### Risk 2: HA Calendar Integration Not Available
**Impact:** High  
**Probability:** Low  
**Mitigation:**
- Document HA setup requirements upfront
- Provide troubleshooting guide for calendar setup
- Support multiple calendar types

### Risk 3: Event Format Differences
**Impact:** Medium  
**Probability:** Medium  
**Mitigation:**
- Comprehensive event parser with format detection
- Extensive unit tests for various event formats
- Graceful handling of unexpected formats

### Risk 4: WebSocket Complexity
**Impact:** Low  
**Probability:** Medium  
**Mitigation:**
- Start with REST API only (Phase 1)
- Add WebSocket in Phase 2 if needed
- Reuse existing WebSocket patterns from websocket-ingestion

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Core Infrastructure | HA client, event parser | 2-3 hours |
| Phase 2: Service Refactoring | Update main service logic | 3-4 hours |
| Phase 3: Configuration & Deployment | Env vars, docs, Docker | 1-2 hours |
| Phase 4: Testing & Validation | Unit, integration, manual tests | 2-3 hours |
| Phase 5: Deployment & Migration | Deploy, migrate, verify | 1 hour |
| **Total** | | **9-13 hours** |

**Recommended Approach:**
- Complete Phases 1-3 in one session (6-9 hours)
- Complete Phase 4 in separate testing session (2-3 hours)
- Deploy Phase 5 after testing validation (1 hour)

---

## Next Steps

### Immediate Actions
1. **Review and approve this plan**
2. **Verify HA calendar integration is set up**
3. **Create feature branch**: `feature/calendar-ha-integration`
4. **Begin Phase 1 implementation**

### Before Starting
- [ ] Verify Home Assistant instance is accessible
- [ ] Confirm calendar integration is configured in HA
- [ ] Create long-lived access token
- [ ] Back up current calendar service configuration
- [ ] Set up testing calendar with known events

### Success Metrics
- Service connects to HA within 5 seconds
- Event retrieval < 2 seconds
- Occupancy prediction accuracy maintained
- Zero data loss during migration
- Health check passes continuously

---

## Open Questions

1. **Multiple Calendar Priority**: How should events from multiple calendars be prioritized if they conflict?
   - **Recommendation**: Process all calendars equally, use earliest WFH/home event
   
2. **Calendar Entity Discovery**: Should service auto-discover calendar entities or require explicit configuration?
   - **Recommendation**: Start with explicit configuration, add auto-discovery in future enhancement

3. **WebSocket vs REST**: Should we implement WebSocket real-time updates or stick with REST polling?
   - **Recommendation**: Start with REST (simpler), add WebSocket if real-time updates prove valuable

4. **Backward Compatibility**: Should we support both Google and HA modes during transition?
   - **Recommendation**: Clean break, provide migration guide. No dual-mode to avoid complexity.

---

## References

- [Home Assistant Calendar Integration](https://www.home-assistant.io/integrations/calendar/)
- [Home Assistant REST API](https://developers.home-assistant.io/docs/api/rest/)
- [Home Assistant WebSocket API](https://developers.home-assistant.io/docs/api/websocket/)
- [Context7 Research Results](docs/kb/context7-cache/) - Used for HA API research
- [Current Calendar Service](services/calendar-service/)
- [WebSocket Connection Manager](services/websocket-ingestion/src/connection_manager.py) - Reference implementation

---

**Plan Status:** Ready for Review  
**Next Review Date:** Before implementation start  
**Plan Owner:** Development Team  
**Stakeholders:** System Architecture, Operations

