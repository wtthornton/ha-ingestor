# DataAPIClient Missing Method Fix

## Problem
The AI automation service was failing with the error:
```
❌ Failed to fetch HA devices: 'DataAPIClient' object has no attribute 'get_all_devices'
```

## Root Cause
The `capability_batch.py` module was calling `data_api_client.get_all_devices()` but this method didn't exist in the `DataAPIClient` class.

## Solution
Added the missing `get_all_devices()` method to `services/ai-automation-service/src/clients/data_api_client.py`:

```python
async def get_all_devices(self) -> List[Dict[str, Any]]:
    """
    Get all devices from Data API (alias for fetch_devices with no filters).
    
    Returns:
        List of all device dictionaries
    """
    return await self.fetch_devices()
```

## Implementation Details
- **Location**: `services/ai-automation-service/src/clients/data_api_client.py` (lines 202-209)
- **Method**: Simple alias that calls the existing `fetch_devices()` method with no filters
- **Return Type**: `List[Dict[str, Any]]` - same as `fetch_devices()`

## Files Changed
- `services/ai-automation-service/src/clients/data_api_client.py`

## Deployment
- Rebuilt and restarted `ai-automation-service` container
- Error resolved immediately

## Verification
- ✅ Service starts without errors
- ✅ API endpoints respond correctly
- ✅ Device Intelligence capability listener starts successfully
- ✅ Daily analysis scheduler starts successfully

## Status
**FIXED** - The AI automation service is now running properly without the missing method error.
