# Fixes and Troubleshooting

This directory contains detailed documentation of fixes, troubleshooting procedures, and lessons learned from production issues.

## Recent Fixes

### Event Validation Fix (October 13, 2025)
**Status:** ✅ Completed  
**Severity:** Critical  
**Impact:** System-wide event processing failure

**Files:**
- [Event Validation Fix Summary](./event-validation-fix-summary.md) - Complete fix details
- [Event Structure Alignment](./event-structure-alignment.md) - Design document
- [Documentation Updates](./DOCUMENTATION_UPDATES.md) - All documentation changes

**Quick Summary:**
The enrichment pipeline validator expected `entity_id` inside state objects, but the WebSocket service sends flattened events with `entity_id` at the top level. Fixed by updating validator to match the actual event structure.

**Result:**
- ✅ 251+ events processed successfully
- ✅ 100% validation success rate
- ✅ 100% InfluxDB write success rate
- ✅ Dashboard now showing live data

---

## Troubleshooting Guides

### Event Processing Issues

#### Dashboard Shows 0 Events
1. **Check Service Health**
   ```bash
   curl http://localhost:8002/health
   curl http://localhost:8001/health
   ```

2. **Check Validation Success Rate**
   ```bash
   docker logs homeiq-enrichment --tail 50 | grep "Validation passed"
   ```

3. **Check for Validation Errors**
   ```bash
   docker logs homeiq-enrichment | grep "validation failed"
   ```

4. **Verify InfluxDB Writes**
   ```bash
   docker logs homeiq-enrichment | grep "points_written"
   ```

#### Circuit Breaker Open
1. **Check enrichment service health**
   ```bash
   curl http://localhost:8002/health
   ```

2. **Check recent errors**
   ```bash
   docker logs homeiq-enrichment --tail 100 | grep "ERROR"
   ```

3. **Restart WebSocket service** to reset circuit breaker
   ```bash
   docker-compose restart websocket-ingestion
   ```

4. **Monitor for successful sends**
   ```bash
   docker logs homeiq-websocket --tail 50 | grep "Event sent successfully"
   ```

#### HTTP 500 Errors from Enrichment Service
1. **Check service logs for exceptions**
   ```bash
   docker logs homeiq-enrichment | grep -A 10 "ERROR"
   ```

2. **Verify event structure**
   - Ensure `entity_id` is at top level
   - Ensure state objects don't have `entity_id` field
   - Check state objects have: `state`, `last_changed`, `last_updated`

3. **Test with known-good event**
   ```bash
   curl -X POST http://localhost:8002/events \
     -H "Content-Type: application/json" \
     -d '{"event_type":"state_changed","entity_id":"sensor.test","domain":"sensor","new_state":{"state":"on","attributes":{},"last_changed":"2025-01-01T00:00:00Z","last_updated":"2025-01-01T00:00:00Z"}}'
   ```

### InfluxDB Issues

#### No Data in InfluxDB
1. **Check InfluxDB connection**
   ```bash
   curl http://localhost:8002/health | jq '.influxdb.connected'
   ```

2. **Check write success rate**
   ```bash
   curl http://localhost:8002/health | jq '.influxdb.success_rate'
   ```

3. **Query InfluxDB directly**
   ```bash
   docker exec homeiq-influxdb influx query \
     'from(bucket:"home_assistant_events") |> range(start: -1h) |> limit(n: 10)'
   ```

### Performance Issues

#### High CPU Usage
1. Check event processing rate
2. Monitor validation duration
3. Check for infinite loops in normalization
4. Verify batch processing is working

#### High Memory Usage
1. Check for memory leaks in event processing
2. Monitor queue sizes
3. Verify events are being cleared after processing
4. Check InfluxDB client memory usage

## Best Practices

### Debugging Event Processing
1. **Always check service health first**
2. **Enable WARNING level debug logs** (they bypass INFO filtering)
3. **Use structured logging** with correlation IDs
4. **Add debug logging at each stage** of processing
5. **Clear Docker cache** before rebuilding to ensure fresh code

### Event Structure Validation
1. **Verify entity_id is at top level** (not in state objects)
2. **Check state objects** have required fields only
3. **Use Context7** to verify against Home Assistant docs
4. **Test with real events** from Home Assistant

### Docker Development
1. **Always rebuild with `--no-cache`** when changing Python code
2. **Remove and recreate containers** after rebuild
3. **Clear builder cache** with `docker builder prune -af`
4. **Verify code changes** in container with `docker exec`

## Common Patterns

### Adding Debug Logging
```python
# Use WARNING level to bypass INFO filtering
logger.warning(f"[COMPONENT] Debug message: {data}")

# Include context
logger.warning(f"[VALIDATOR] Entity: {entity_id}, Valid: {is_valid}, Errors: {errors}")

# Log data structure
logger.warning(f"[HANDLER] Keys: {list(event.keys())}, Has field: {'field' in event}")
```

### Event Structure Checks
```python
# Check for flattened structure
assert 'entity_id' in event  # Should be at top level
assert 'data' not in event or 'entity_id' not in event.get('data', {})  # Should NOT be nested

# Check state objects
assert 'entity_id' not in event.get('new_state', {})  # Should NOT be in state
assert 'state' in event.get('new_state', {})  # Should have state field
```

### Validation Best Practices
```python
# Validate at the correct level
entity_id = event.get('entity_id', '')  # Top level, not event['data']['entity_id']

# State validation
required_state_fields = ['state', 'last_changed', 'last_updated']  # NOT entity_id
```

## Lessons Learned

### Technical Lessons
1. **Data contracts matter** - Mismatched expectations between services cause cascading failures
2. **Debug logging is critical** - Proper logging reveals exact issues quickly
3. **Docker cache can hide bugs** - Always clear cache when troubleshooting
4. **Design before implementing** - Reactive fixes waste time, design-first approach works
5. **Use external documentation** - Context7 helped understand Home Assistant structure

### Process Lessons
1. **Don't make assumptions** - Verify actual data structures with logging
2. **Be systematic** - Follow a clear debugging plan
3. **Document as you go** - Capture learnings immediately
4. **Test incrementally** - Verify each fix works before moving on
5. **Be truthful** - Don't claim fixes work until verified

### Tool Usage Lessons
1. **Context7 for external APIs** - Essential for understanding third-party systems
2. **Structured logging** - Makes debugging production issues much easier
3. **Health endpoints** - Critical for monitoring service state
4. **Circuit breakers** - Prevent cascade failures but need proper monitoring

## Related Documentation

- [API Documentation](../API_DOCUMENTATION.md) - Updated with correct event structure
- [Data Models](../architecture/data-models.md) - Updated with ProcessedEvent model
- [Event Flow Architecture](../architecture/event-flow-architecture.md) - Complete flow documentation
- [Event Validation Fix Summary](./event-validation-fix-summary.md) - Detailed fix documentation
- [Event Structure Alignment](./event-structure-alignment.md) - Design document

## Contact

For questions or issues related to these fixes, refer to the detailed documentation above or check the related architecture documentation.

