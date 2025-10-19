# Device Validation Example

## How the Validation System Works

Let me show you exactly how the device validation prevents invalid suggestions and provides alternatives.

## Example 1: Window Sensor Validation

### Before Validation (Current System)
```
Pattern Detected: "Office lights turn on at 9 AM"
AI Suggestion: "When office window is open, flash lights blue/green every 5 minutes"

❌ PROBLEM: No window sensor exists in your Home Assistant system
❌ RESULT: User gets suggestion that can't be implemented
```

### After Validation (New System)
```
Pattern Detected: "Office lights turn on at 9 AM"

Step 1: Validation Check
- Check for window sensors: ❌ None found
- Check for door sensors: ❌ None found  
- Check for presence sensors: ✅ Found ps_fp2_office, ps_fp2_desk

Step 2: Generate Alternative
AI Suggestion: "When presence is detected in office, flash lights blue/green every 5 minutes"

✅ SOLUTION: Uses actual available sensors
✅ RESULT: User gets implementable suggestion
```

## Example 2: Code Flow

### 1. Pattern Detection
```python
pattern_dict = {
    'pattern_type': 'time_of_day',
    'device_id': 'light.office',
    'hour': 9,
    'minute': 0,
    'confidence': 0.85
}
```

### 2. Device Context Building
```python
device_context = {
    'device_id': 'light.office',
    'name': 'Office Lights',
    'domain': 'light',
    'area': 'office'
}
```

### 3. Validation Check
```python
# Extract trigger conditions from AI suggestion
trigger_conditions = ["window open", "presence detected"]

# Validate against available sensors
validation_result = await device_validator.validate_trigger_condition("window open")

# Result:
validation_result = ValidationResult(
    is_valid=False,
    missing_sensors=['window'],
    available_alternatives={
        'window': ['binary_sensor.ps_fp2_office', 'binary_sensor.ps_fp2_desk']
    }
)
```

### 4. Alternative Generation
```python
if not validation_result.is_valid:
    # Generate alternative using available sensors
    alternative_suggestion = {
        'title': 'Office Light Show with Presence Detection',
        'description': 'When presence is detected in office, flash lights blue/green every 5 minutes',
        'trigger_entity': 'binary_sensor.ps_fp2_office',
        'action_entity': 'light.office'
    }
```

## Example 3: Real Validation Logic

### DeviceValidator.validate_trigger_condition()
```python
async def validate_trigger_condition(self, condition: str) -> ValidationResult:
    # Extract required sensors from condition
    required_sensors = self._extract_required_sensors(condition)
    # "window open" → ['window']
    # "presence detected" → ['presence']
    
    missing_sensors = []
    alternatives = {}
    
    for sensor_type in required_sensors:
        if not await self._sensor_type_exists(sensor_type):
            missing_sensors.append(sensor_type)
            # Find alternatives
            alternatives[sensor_type] = await self._find_sensor_alternatives(sensor_type)
    
    return ValidationResult(
        is_valid=len(missing_sensors) == 0,
        missing_sensors=missing_sensors,
        available_alternatives=alternatives
    )
```

### Sensor Type Detection
```python
def _extract_required_sensors(self, condition: str) -> List[str]:
    condition_lower = condition.lower()
    required_sensors = []
    
    if 'window' in condition_lower:
        required_sensors.append('window')
    if 'presence' in condition_lower:
        required_sensors.append('presence')
    if 'motion' in condition_lower:
        required_sensors.append('motion')
    
    return required_sensors
```

### Alternative Finding
```python
async def _find_sensor_alternatives(self, sensor_type: str) -> List[str]:
    alternatives = []
    
    if sensor_type == 'window':
        # Look for presence sensors as alternatives
        for entity_id, entity_data in self._entity_cache.items():
            if 'presence' in entity_id and entity_data.get('domain') == 'binary_sensor':
                alternatives.append(entity_id)
    
    return alternatives
```

## Example 4: Integration in Suggestion Generation

### Modified suggestion_router.py
```python
# BEFORE: Direct generation
description_data = await openai_client.generate_description_only(
    pattern_dict,
    device_context=device_context
)

# AFTER: Validation first
validation_result = await _validate_pattern_feasibility(pattern_dict, device_context)

if not validation_result.is_valid:
    if validation_result.available_alternatives:
        # Generate alternative using available devices
        description_data = await _generate_alternative_suggestion(
            pattern_dict, 
            device_context, 
            validation_result
        )
    else:
        # Skip this pattern entirely
        continue
else:
    # Original pattern is valid
    description_data = await openai_client.generate_description_only(...)
```

## Example 5: User Experience

### Before (Invalid Suggestions)
```
User sees: "When office window is open, flash lights blue/green"
User tries to implement: ❌ No window sensor exists
User frustration: High - suggestion is useless
```

### After (Validated Suggestions)
```
User sees: "When presence is detected in office, flash lights blue/green"
User tries to implement: ✅ Uses ps_fp2_office sensor
User satisfaction: High - suggestion works immediately
```

## Benefits of This Design

1. **Prevents Invalid Suggestions**: No more suggestions for non-existent devices
2. **Provides Alternatives**: Suggests similar functionality with available devices
3. **Improves User Experience**: Only shows implementable automations
4. **Maintains Accuracy**: AI suggestions match actual Home Assistant setup
5. **Reduces Frustration**: No more "why doesn't this work?" moments

## Future Enhancements

1. **Smart Alternatives**: More sophisticated alternative suggestions
2. **Context Awareness**: Consider room/area when finding alternatives
3. **User Preferences**: Learn which alternatives users prefer
4. **Device Capabilities**: Check if devices support required actions
5. **Complex Triggers**: Validate multi-condition triggers

This validation system ensures that every automation suggestion is actually implementable with your real Home Assistant setup!
