# InfluxDB Schema Analysis and Optimization Design

**Created:** 2024-12-20
**Task:** 5.1 Schema Analysis and Design
**Status:** In Progress

## Current Schema Analysis

### 1. Existing Schema Structure

#### 1.1 Current Data Model
The current schema uses a flexible approach with the following structure:

**Measurement Naming Convention:**
- MQTT Events: `ha_{domain}` (e.g., `ha_light`, `ha_switch`, `ha_sensor`)
- WebSocket Events: `ha_{event_type}` (e.g., `ha_state_changed`, `ha_call_service`)

**Tag Structure:**
- **Common Tags:**
  - `domain`: Entity domain (e.g., "light", "switch", "sensor")
  - `entity_id`: Specific entity identifier (e.g., "living_room_light")
  - `source`: Data source ("mqtt" or "websocket")
  - `event_type`: Event type for WebSocket events

- **Dynamic Tags:**
  - `friendly_name`: Human-readable entity name
  - `unit_of_measurement`: Unit for numeric values
  - `device_class`: Device classification
  - `service`: Service name for service calls
  - `context_id`: Event context identifier

**Field Structure:**
- **Common Fields:**
  - `state`: Current entity state
  - `payload`: Raw payload data
  - `event_type`: Event type identifier

- **Dynamic Fields:**
  - `attr_{attribute_name}`: Entity attributes
  - `data_{key}`: Event-specific data

#### 1.2 Current Schema Limitations

1. **Tag Cardinality Issues:**
   - High cardinality tags like `entity_id` can cause performance problems
   - Dynamic tags from attributes may create unpredictable cardinality
   - No tag value length validation beyond 64 characters

2. **Field Type Inconsistencies:**
   - Mixed data types in fields (string, numeric, boolean)
   - No field type validation or optimization
   - Potential for field explosion with dynamic attributes

3. **Measurement Proliferation:**
   - Separate measurements for each domain/event type
   - No measurement consolidation strategy
   - Potential for too many measurements

4. **Timestamp Handling:**
   - Nanosecond precision may be excessive for some use cases
   - No time bucketing or aggregation strategy
   - No retention policy enforcement

### 2. Query Pattern Analysis

#### 2.1 Common Query Patterns

Based on the current schema, typical queries would include:

1. **Entity State Queries:**
   ```sql
   -- Get current state of specific entity
   SELECT last("state") FROM "ha_light" WHERE "entity_id" = 'living_room_light'

   -- Get state history for entity
   SELECT "state" FROM "ha_light" WHERE "entity_id" = 'living_room_light' AND time > now() - 1h
   ```

2. **Domain-wide Queries:**
   ```sql
   -- Get all light states
   SELECT last("state") FROM "ha_light"

   -- Get sensor readings for specific domain
   SELECT mean("attr_temperature") FROM "ha_sensor" WHERE time > now() - 24h
   ```

3. **Time-based Analysis:**
   ```sql
   -- Get hourly averages
   SELECT mean("attr_temperature") FROM "ha_sensor" WHERE time > now() - 7d GROUP BY time(1h)

   -- Get daily statistics
   SELECT count("state") FROM "ha_light" WHERE time > now() - 30d GROUP BY time(1d)
   ```

4. **Cross-entity Queries:**
   ```sql
   -- Get all entities with specific attribute
   SELECT "entity_id", "state" FROM /ha_.*/ WHERE "attr_device_class" = 'temperature'
   ```

#### 2.2 Query Performance Issues

1. **High Cardinality Impact:**
   - Queries with high-cardinality tags are slow
   - No tag cardinality limits or warnings
   - Potential for query timeouts

2. **Measurement Scans:**
   - Queries across multiple measurements require multiple scans
   - No measurement consolidation strategy
   - Inefficient for cross-domain analysis

3. **Field Access Patterns:**
   - Dynamic field names make queries unpredictable
   - No field indexing strategy
   - Potential for field explosion

### 3. Optimization Opportunities

#### 3.1 Tag Optimization

1. **Cardinality Management:**
   - Implement tag cardinality limits
   - Use tag value hashing for high-cardinality values
   - Implement tag value compression

2. **Tag Hierarchy:**
   - Create structured tag hierarchies
   - Use consistent tag naming conventions
   - Implement tag value validation

3. **Tag Consolidation:**
   - Merge related tags where possible
   - Use composite tags for complex identifiers
   - Implement tag value normalization

#### 3.2 Field Optimization

1. **Field Type Standardization:**
   - Standardize field types across measurements
   - Implement field type validation
   - Use appropriate numeric types (int, float)

2. **Field Consolidation:**
   - Group related fields into structured objects
   - Use consistent field naming conventions
   - Implement field value validation

3. **Field Compression:**
   - Use appropriate compression algorithms
   - Implement field value encoding
   - Optimize field storage formats

#### 3.3 Measurement Optimization

1. **Measurement Consolidation:**
   - Consolidate related measurements
   - Use measurement hierarchies
   - Implement measurement naming conventions

2. **Measurement Partitioning:**
   - Partition measurements by time
   - Use measurement sharding strategies
   - Implement measurement lifecycle management

#### 3.4 Data Retention and Compression

1. **Retention Policies:**
   - Implement configurable retention periods
   - Use different retention for different data types
   - Implement data archival strategies

2. **Compression Strategies:**
   - Use appropriate compression algorithms
   - Implement compression level optimization
   - Use time-based compression strategies

### 4. Proposed Schema Design

#### 4.1 Optimized Tag Structure

**Core Tags (Low Cardinality):**
- `domain`: Entity domain (e.g., "light", "switch", "sensor")
- `entity_type`: Entity classification (e.g., "device", "sensor", "automation")
- `source`: Data source ("mqtt" or "websocket")
- `event_category`: Event category ("state_change", "service_call", "automation")

**Entity Tags (Medium Cardinality):**
- `entity_group`: Logical grouping (e.g., "living_room", "kitchen", "bedroom")
- `device_class`: Device classification (e.g., "temperature", "light", "switch")
- `manufacturer`: Device manufacturer (if available)
- `model`: Device model (if available)

**Dynamic Tags (High Cardinality - Limited):**
- `entity_id_hash`: Hashed entity ID (for high-cardinality entities)
- `context_hash`: Hashed context identifier (for complex contexts)

#### 4.2 Optimized Field Structure

**Core Fields:**
- `state`: Current entity state
- `state_numeric`: Numeric representation of state (if applicable)
- `timestamp_original`: Original event timestamp
- `event_id`: Unique event identifier

**Attribute Fields (Structured):**
- `attributes`: JSON object containing all attributes
- `attributes_common`: Common attributes (friendly_name, unit_of_measurement)
- `attributes_custom`: Custom attributes (device-specific)

**Metadata Fields:**
- `payload_size`: Size of original payload
- `processing_time`: Time taken to process event
- `filter_results`: Results of applied filters
- `transformation_results`: Results of applied transformations

#### 4.3 Optimized Measurement Structure

**Primary Measurements:**
- `ha_entities`: All entity state changes
- `ha_events`: All event data
- `ha_metrics`: Performance and operational metrics

**Specialized Measurements:**
- `ha_sensors`: Sensor-specific data (with optimized field types)
- `ha_automations`: Automation execution data
- `ha_services`: Service call data

#### 4.4 Data Retention Strategy

**Retention Policies:**
- **Real-time Data (1 day):** High precision, no compression
- **Recent Data (7 days):** Medium precision, light compression
- **Historical Data (30 days):** Low precision, heavy compression
- **Long-term Data (1 year):** Aggregated data, maximum compression
- **Archive Data (1+ years):** Aggregated data, external storage

**Compression Levels:**
- **Level 1 (1-7 days):** GZIP level 1 (fast)
- **Level 2 (8-30 days):** GZIP level 6 (balanced)
- **Level 3 (30+ days):** GZIP level 9 (maximum)

### 5. Migration Strategy

#### 5.1 Phase 1: Schema Preparation
1. Create new optimized measurements
2. Implement data validation and transformation
3. Test with sample data

#### 5.2 Phase 2: Data Migration
1. Implement dual-write strategy
2. Migrate historical data
3. Validate data integrity

#### 5.3 Phase 3: Schema Switch
1. Switch to new schema
2. Monitor performance
3. Remove old measurements

### 6. Performance Expectations

#### 6.1 Query Performance Improvements
- **Tag-based queries:** 3-5x faster
- **Time-range queries:** 2-3x faster
- **Cross-measurement queries:** 5-10x faster
- **Aggregation queries:** 2-4x faster

#### 6.2 Storage Efficiency
- **Data compression:** 40-60% reduction
- **Tag storage:** 30-50% reduction
- **Field storage:** 20-40% reduction
- **Overall storage:** 35-55% reduction

#### 6.3 Write Performance
- **Batch writes:** 2-3x faster
- **Individual writes:** 1.5-2x faster
- **Compression overhead:** <5% impact

### 7. Implementation Plan

#### 7.1 Week 1: Schema Design and Validation
- [ ] Finalize tag structure design
- [ ] Design field optimization strategy
- [ ] Create measurement consolidation plan
- [ ] Validate design with sample queries

#### 7.2 Week 2: Implementation
- [ ] Implement new schema models
- [ ] Create data transformation logic
- [ ] Implement retention policies
- [ ] Add compression strategies

#### 7.3 Week 3: Testing and Migration
- [ ] Test with production-like data
- [ ] Implement migration scripts
- [ ] Validate performance improvements
- [ ] Plan production migration

### 8. Risk Mitigation

#### 8.1 Data Loss Prevention
- Implement dual-write strategy during migration
- Validate data integrity at each step
- Maintain backup of original data

#### 8.2 Performance Degradation Prevention
- Test with realistic data volumes
- Implement gradual migration strategy
- Monitor performance metrics during migration

#### 8.3 Compatibility Issues
- Maintain backward compatibility during transition
- Implement feature flags for new schema
- Provide rollback mechanisms

### 9. Success Metrics

#### 9.1 Performance Metrics
- Query response time improvement
- Storage efficiency improvement
- Write performance improvement

#### 9.2 Quality Metrics
- Data integrity validation
- Query result accuracy
- System stability during migration

#### 9.3 Operational Metrics
- Migration completion time
- System downtime during migration
- User impact during transition

## Next Steps

1. **Review and approve schema design**
2. **Implement new schema models**
3. **Create data transformation logic**
4. **Implement retention and compression policies**
5. **Begin testing and validation**

## Dependencies

- **Task 4 completion:** Code quality improvements must be complete
- **Performance testing environment:** Required for validation
- **Data migration tools:** Required for production migration
- **Monitoring infrastructure:** Required for performance tracking
