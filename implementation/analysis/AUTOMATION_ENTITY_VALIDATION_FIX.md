# Automation Entity Validation Fix

## Root Cause Analysis

**Problem:** The AI automation service is generating fake entity IDs like `light.office_light` and `binary_sensor.front_door` instead of using actual Home Assistant entities.

**Location:** `services/ai-automation-service/src/api/ask_ai_router.py` lines 103-236

**Issue:** The `generate_automation_yaml()` function uses a hardcoded prompt that instructs OpenAI to generate "realistic entity IDs based on device names (format: domain.name_with_underscores)" without actually validating that these entities exist.

## The Fix

### 1. Entity Validation Before YAML Generation

**Current Flow:**
```
User Query → Extract Entities (pattern matching) → Generate YAML → Create Automation → ERROR
```

**Fixed Flow:**
```
User Query → Extract Entities → Validate Against Real HA Entities → Generate YAML → Create Automation → SUCCESS
```

### 2. Implementation Changes

#### A. Add Entity Validation Service

Create a new service to validate entities against real Home Assistant entities:

```python
# services/ai-automation-service/src/services/entity_validator.py
class EntityValidator:
    async def validate_entities(self, entities: List[str]) -> Dict[str, bool]:
        """Validate that entities exist in Home Assistant"""
        
    async def get_entity_alternatives(self, entity_id: str) -> List[str]:
        """Get alternative entity names for suggestions"""
        
    async def suggest_entity_mapping(self, query: str) -> Dict[str, str]:
        """Map query terms to actual entity IDs"""
```

#### B. Update YAML Generation

Modify `generate_automation_yaml()` to:
1. Validate all entities before generating YAML
2. Use actual entity IDs from Home Assistant
3. Provide fallback suggestions if entities don't exist

#### C. Add Entity Discovery Integration

Connect to the existing entity discovery system in `websocket-ingestion` service:
- Use the discovered entities from `data-api`
- Query real entity registry from Home Assistant
- Cache entity mappings for performance

### 3. Specific Code Changes

#### Update `ask_ai_router.py`:

```python
async def generate_automation_yaml(suggestion: Dict[str, Any], original_query: str) -> str:
    """Generate automation YAML with validated entities"""
    
    # NEW: Validate entities first
    entity_validator = EntityValidator()
    validated_entities = await entity_validator.validate_and_map_entities(suggestion)
    
    if not validated_entities:
        raise ValueError("No valid entities found for automation")
    
    # Use validated entities in prompt
    prompt = f"""
    Generate YAML using these VALIDATED entities:
    {validated_entities}
    
    DO NOT create new entity IDs - use only the ones provided above.
    """
```

#### Add Entity Validation Service:

```python
class EntityValidator:
    def __init__(self, ha_client: HomeAssistantClient, data_api_client: DataAPIClient):
        self.ha_client = ha_client
        self.data_api_client = data_api_client
    
    async def validate_and_map_entities(self, suggestion: Dict) -> Dict[str, str]:
        """Validate entities and return mapping of query terms to real entity IDs"""
        
        # Get all available entities from data-api
        available_entities = await self.data_api_client.get_all_entities()
        
        # Map suggestion entities to real ones
        entity_mapping = {}
        for device_name in suggestion.get('devices_involved', []):
            real_entity = self._find_best_match(device_name, available_entities)
            if real_entity:
                entity_mapping[device_name] = real_entity['entity_id']
        
        return entity_mapping
```

### 4. Testing the Fix

#### Run Entity Verification:

```bash
# Test the entity verification script
python scripts/test-automation-entities.py

# Expected output:
# ✅ Found: light.office (actual entity)
# ✅ Found: binary_sensor.door_sensor (actual entity)
# ❌ Not Found: light.office_light (fake entity)
# ❌ Not Found: binary_sensor.front_door (fake entity)
```

#### Update Test Automation:

```yaml
# Use REAL entities from the verification script
alias: "Test Office Light Door Trigger"
trigger:
  - platform: state
    entity_id: binary_sensor.door_sensor  # REAL entity
    to: "on"
action:
  - service: light.turn_on
    target:
      entity_id: light.office  # REAL entity
    data:
      color_name: red
```

### 5. Prevention Measures

1. **Entity Validation Pipeline**: Always validate entities before automation creation
2. **Real Entity Discovery**: Use the existing entity discovery system
3. **Fallback Suggestions**: Provide alternative entities when requested ones don't exist
4. **User Education**: Show available entities in the UI

### 6. Files to Modify

1. `services/ai-automation-service/src/api/ask_ai_router.py` - Add entity validation
2. `services/ai-automation-service/src/services/entity_validator.py` - New service
3. `services/ai-automation-service/src/clients/data_api_client.py` - Add entity queries
4. `scripts/test-automation-entities.py` - Enhanced verification script

### 7. Testing Steps

1. Run entity verification script to see real entities
2. Update test automation with real entity IDs
3. Test automation creation with validated entities
4. Verify automation works without "Entity not found" errors

## Summary

The root cause is that the AI automation service generates fake entity IDs instead of using real Home Assistant entities. The fix involves:

1. **Validating entities** against the real Home Assistant registry
2. **Using actual entity IDs** in automation generation
3. **Providing fallback suggestions** for non-existent entities
4. **Integrating with existing entity discovery** system

This will eliminate the "Entity not found" errors and ensure automations use real, working entities.
