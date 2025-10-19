# Device Validation Architecture

## Problem Statement
AI automation suggestions reference non-existent devices (e.g., "office window sensor" when no window sensors exist).

## Solution: Validation Layer

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐    ┌─────────────────┐
│ Pattern         │───▶│ Device           │───▶│ Suggestion          │───▶│ User Interface  │
│ Detection       │    │ Validation       │    │ Generation          │    │ (Ask AI Tab)    │
│                 │    │                  │    │                     │    │                 │
│ - Time patterns │    │ - Check entities │    │ - Generate only     │    │ - Show valid    │
│ - Co-occurrence │    │ - Validate       │    │   valid suggestions │    │   suggestions   │
│ - Anomalies     │    │   sensors        │    │ - Provide           │    │ - Suggest       │
│                 │    │ - Find           │    │   alternatives      │    │   alternatives  │
│                 │    │   alternatives   │    │                     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────────┘    └─────────────────┘
```

## Key Components

### 1. DeviceValidator Class
```python
class DeviceValidator:
    async def validate_automation_suggestion(
        self, 
        suggestion_text: str, 
        suggested_entities: List[str],
        trigger_conditions: List[str]
    ) -> ValidationResult
```

**Responsibilities:**
- Check if referenced entities exist in Home Assistant
- Validate trigger conditions against available sensors
- Find alternative devices when originals don't exist
- Cache device/entity data for performance

### 2. ValidationResult DataClass
```python
@dataclass
class ValidationResult:
    is_valid: bool
    missing_devices: List[str]
    missing_entities: List[str]
    missing_sensors: List[str]
    available_alternatives: Dict[str, List[str]]
    error_message: Optional[str]
```

**Purpose:**
- Structured response with validation status
- Lists what's missing and what alternatives exist
- Provides clear error messages for users

### 3. Integration Points

#### A. Suggestion Generation (suggestion_router.py)
```python
# BEFORE validation
description_data = await openai_client.generate_description_only(
    pattern_dict,
    device_context=device_context
)

# AFTER validation (new approach)
validation_result = await device_validator.validate_automation_suggestion(
    suggestion_text,
    suggested_entities,
    trigger_conditions
)

if not validation_result.is_valid:
    # Generate alternative suggestion or skip
    return generate_alternative_suggestion(validation_result)
else:
    # Proceed with original suggestion
    description_data = await openai_client.generate_description_only(...)
```

#### B. OpenAI Client (openai_client.py)
```python
def _build_description_prompt(self, pattern: Dict, device_context: Optional[Dict] = None) -> str:
    # NEW: Include validation context
    validation_context = self._build_validation_context(pattern, device_context)
    
    return f"""Create a Home Assistant automation for this detected usage pattern:

PATTERN DETECTED:
- Device: {device_name}
- Available Sensors: {validation_context['available_sensors']}
- Missing Sensors: {validation_context['missing_sensors']}

IMPORTANT: Only use devices and sensors that actually exist in the system.
If a required sensor doesn't exist, suggest an alternative approach.
"""
```

## Validation Logic

### 1. Entity Validation
```python
async def _entity_exists(self, entity_id: str) -> bool:
    """Check if an entity exists in Home Assistant"""
    return entity_id in self._entity_cache
```

### 2. Sensor Type Validation
```python
def _extract_required_sensors(self, condition: str) -> List[str]:
    """Extract required sensor types from trigger condition"""
    # "window open" → ['window']
    # "presence detected" → ['presence']
    # "temperature high" → ['temperature']
```

### 3. Alternative Finding
```python
async def _find_sensor_alternatives(self, sensor_type: str) -> List[str]:
    """Find alternative sensors of the requested type"""
    # If "window" sensor not found, suggest "presence" sensors
    # If "door" sensor not found, suggest "contact" sensors
```

## Example Flow

### Before Validation (Current)
```
Pattern: "Office lights turn on at 9 AM"
AI Suggestion: "When office window is open, flash lights blue/green"
❌ Problem: No window sensor exists
```

### After Validation (New)
```
Pattern: "Office lights turn on at 9 AM"
Validation: Check for window sensors → None found
Available: Presence sensors (ps_fp2_office, ps_fp2_desk)
AI Suggestion: "When presence is detected in office, flash lights blue/green"
✅ Solution: Uses actual available sensors
```

## Implementation Steps

1. **Create DeviceValidator** ✅ (Done)
2. **Integrate with suggestion generation** (Next)
3. **Update OpenAI prompts** (Next)
4. **Add validation to Ask AI endpoint** (Next)
5. **Test with real data** (Next)

## Benefits

- **Prevents invalid suggestions**: No more "window sensor" when none exists
- **Suggests alternatives**: "Use presence sensor instead of window sensor"
- **Improves user experience**: Only shows implementable automations
- **Reduces frustration**: No more suggestions that can't be created
- **Maintains accuracy**: AI suggestions match actual Home Assistant setup

## Performance Considerations

- **Caching**: Device/entity data cached to avoid repeated API calls
- **Async operations**: Non-blocking validation
- **Batch validation**: Validate multiple suggestions together
- **Error handling**: Graceful fallbacks when validation fails
