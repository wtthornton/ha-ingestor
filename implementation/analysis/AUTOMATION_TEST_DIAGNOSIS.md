# Automation Test Diagnosis

## Problem Analysis

**Error Summary:**
- Automation validated successfully but failed during execution
- Missing entities: `light.office_light` and `binary_sensor.front_door`
- Test automation is disabled

## Local Test Plan

### Step 1: Entity Verification

**Check Entity Existence:**

1. **Open Home Assistant Developer Tools:**
   - Navigate to Developer Tools → States
   - Search for: `light.office_light`
   - Search for: `binary_sensor.front_door`

2. **Expected Results:**
   ```
   ✅ Found: light.office_light (state: on/off)
   ✅ Found: binary_sensor.front_door (state: on/off)
   ```

3. **If Not Found:**
   - Check spelling variations
   - Verify integrations are working
   - Check device connectivity

### Step 2: Create Test Automation

**Manual Automation Creation:**

```yaml
# Test Automation YAML
alias: "Test Office Light Door Trigger"
description: "Test automation for office light when front door opens"
trigger:
  - platform: state
    entity_id: binary_sensor.front_door
    from: "off"
    to: "on"
condition: []
action:
  - service: light.turn_on
    target:
      entity_id: light.office_light
    data:
      color_name: red
      brightness_pct: 100
  - delay: "00:00:02"
  - service: light.turn_on
    target:
      entity_id: light.office_light
    data:
      color_name: white
      brightness_pct: 100
      transition: 3
mode: single
```

### Step 3: Alternative Entity Discovery

**Find Correct Entity Names:**

```python
# Python script to list all entities
import requests
import json

# Home Assistant API call
url = "http://192.168.1.86:8123/api/states"
headers = {
    "Authorization": "Bearer YOUR_LONG_LIVED_ACCESS_TOKEN",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
entities = response.json()

# Filter for lights and binary sensors
lights = [e for e in entities if e['entity_id'].startswith('light.')]
door_sensors = [e for e in entities if 'door' in e['entity_id'].lower()]

print("Available Lights:")
for light in lights:
    print(f"  {light['entity_id']} - {light['attributes'].get('friendly_name', 'No name')}")

print("\nAvailable Door Sensors:")
for sensor in door_sensors:
    print(f"  {sensor['entity_id']} - {sensor['attributes'].get('friendly_name', 'No name')}")
```

### Step 4: Test Automation Creation

**Using Home Assistant UI:**

1. **Go to Settings → Automations & Scenes**
2. **Click "Create Automation"**
3. **Use "Start with an empty automation"**
4. **Configure:**
   - **Name:** "Test Office Light Door"
   - **Trigger:** State trigger for door sensor
   - **Action:** Light control with color and transition

### Step 5: Verification Steps

**Test Checklist:**

- [ ] Entities exist in Developer Tools
- [ ] Automation created successfully
- [ ] Automation enabled (not disabled)
- [ ] Trigger entity state changes correctly
- [ ] Action entity responds to commands
- [ ] Test automation executes without errors

## Common Issues and Solutions

### Issue 1: Entity Not Found
**Cause:** Incorrect entity ID or missing integration
**Solution:** 
- Verify entity ID in Developer Tools
- Check integration status
- Ensure device is online

### Issue 2: Automation Disabled
**Cause:** Test automation was automatically disabled
**Solution:**
- Re-enable automation in UI
- Or delete and recreate

### Issue 3: Permission Issues
**Cause:** Insufficient permissions for automation
**Solution:**
- Check user permissions
- Verify API token permissions

## Test Results Template

```
Test Date: ___________
Entity Verification:
- light.office_light: [ ] Found [ ] Not Found
- binary_sensor.front_door: [ ] Found [ ] Not Found

Actual Entity Names (if different):
- Light: ___________
- Door Sensor: ___________

Automation Test:
- [ ] Created successfully
- [ ] Enabled
- [ ] Executed without errors
- [ ] Light responded correctly

Notes:
___________
```

## Next Steps

1. Run entity verification first
2. Create test automation with correct entity names
3. Test execution
4. Document results
5. Fix any remaining issues
