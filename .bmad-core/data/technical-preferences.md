<!-- Powered by BMAD™ Core -->

# User-Defined Preferred Patterns and Preferences

## Architecture Patterns (Last Updated: October 20, 2025)

### Event Ingestion Architecture (Epic 31)

**Current Pattern (as of Epic 31):**
```
Home Assistant WebSocket → websocket-ingestion → InfluxDB (DIRECT)
```

**Key Principles:**
- ❌ **Do NOT reference enrichment-pipeline** - Service was deprecated in Epic 31
- ✅ **websocket-ingestion writes DIRECTLY to InfluxDB** - No intermediate services
- ✅ **External services are standalone** - weather-api, sports-data, etc. are independent
- ✅ **External services consume FROM InfluxDB** - Not from websocket-ingestion

**DEPRECATED (Epic 31):**
- ~~enrichment-pipeline service~~ (Port 8002) - Removed
- ~~HTTP POST to enrichment-pipeline~~ - No longer exists
- ~~Dual write paths~~ - Single path only now

### Database Architecture (Epic 22)

**Hybrid Database Pattern:**
- **InfluxDB**: Time-series data (events, metrics, sports scores)
- **SQLite**: Relational metadata (devices, entities, webhooks)

**Benefits:**
- 5-10x faster device/entity queries (<10ms vs ~50ms)
- ACID transactions for critical data
- Proper foreign key relationships

### External API Pattern

**All external services follow this pattern:**
1. Fetch data from external API (ESPN, OpenWeatherMap, etc.)
2. Write directly to InfluxDB (time-series storage)
3. Dashboard queries via data-api
4. No direct service-to-service HTTP calls

**Services:**
- weather-api (Port 8009)
- sports-data (Port 8005)
- carbon-intensity (Port 8010)
- air-quality (Port 8012)
- calendar (Port 8013)

### Code Documentation Pattern

**When creating call tree documentation:**
- ✅ Validate against actual code (check for Epic 31 changes)
- ✅ Mark deprecated services clearly
- ✅ Include Epic numbers for context
- ✅ Add version numbers and change logs
- ✅ Cross-reference related documentation

**When updating architecture docs:**
- ✅ Check for deprecated services (enrichment-pipeline, etc.)
- ✅ Verify service ports and communication patterns
- ✅ Include Epic context for changes
- ✅ Update version history
