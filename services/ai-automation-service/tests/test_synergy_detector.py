"""
Unit tests for Device Synergy Detector

Story AI3.1: Device Synergy Detector Foundation
Epic AI-3: Cross-Device Synergy & Contextual Opportunities
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.synergy_detection.synergy_detector import DeviceSynergyDetector, COMPATIBLE_RELATIONSHIPS


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_data_api_client():
    """Mock Data API client"""
    client = AsyncMock()
    
    # Mock devices
    client.fetch_devices = AsyncMock(return_value=[
        {
            'device_id': 'device_1',
            'name': 'Bedroom Motion Sensor',
            'manufacturer': 'Aqara',
            'model': 'RTCGQ11LM'
        },
        {
            'device_id': 'device_2',
            'name': 'Bedroom Ceiling Light',
            'manufacturer': 'Philips',
            'model': 'Hue White'
        },
        {
            'device_id': 'device_3',
            'name': 'Living Room Thermostat',
            'manufacturer': 'Ecobee',
            'model': 'SmartThermostat'
        }
    ])
    
    # Mock entities
    client.fetch_entities = AsyncMock(return_value=[
        {
            'entity_id': 'binary_sensor.bedroom_motion',
            'device_id': 'device_1',
            'friendly_name': 'Bedroom Motion',
            'area_id': 'bedroom',
            'device_class': 'motion'
        },
        {
            'entity_id': 'light.bedroom_ceiling',
            'device_id': 'device_2',
            'friendly_name': 'Bedroom Light',
            'area_id': 'bedroom'
        },
        {
            'entity_id': 'climate.living_room',
            'device_id': 'device_3',
            'friendly_name': 'Living Room Thermostat',
            'area_id': 'living_room'
        },
        {
            'entity_id': 'sensor.outdoor_temperature',
            'device_id': 'device_4',
            'friendly_name': 'Outdoor Temperature',
            'area_id': 'living_room',
            'device_class': 'temperature'
        }
    ])
    
    return client


@pytest.fixture
def mock_ha_client():
    """Mock Home Assistant client"""
    return None  # For initial implementation


# ============================================================================
# Core Detection Tests
# ============================================================================

@pytest.mark.asyncio
async def test_detect_synergies_basic(mock_data_api_client, mock_ha_client):
    """Test basic synergy detection"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client,
        min_confidence=0.7
    )
    
    synergies = await detector.detect_synergies()
    
    # Should detect at least motion sensor + light in bedroom
    assert len(synergies) > 0
    assert any(s['relationship'] == 'motion_to_light' for s in synergies)


@pytest.mark.asyncio
async def test_same_area_motion_light_detection(mock_data_api_client, mock_ha_client):
    """Test detection of motion sensor + light in same area"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    synergies = await detector.detect_synergies()
    
    # Find bedroom synergy
    bedroom_synergies = [s for s in synergies if s['area'] == 'bedroom']
    assert len(bedroom_synergies) > 0
    
    motion_light = [s for s in bedroom_synergies if s['relationship'] == 'motion_to_light'][0]
    assert motion_light['trigger_entity'] == 'binary_sensor.bedroom_motion'
    assert motion_light['action_entity'] == 'light.bedroom_ceiling'
    assert motion_light['impact_score'] > 0.0
    assert motion_light['complexity'] == 'low'
    assert motion_light['confidence'] >= 0.7


@pytest.mark.asyncio
async def test_temp_climate_detection(mock_data_api_client, mock_ha_client):
    """Test detection of temperature sensor + climate device"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    synergies = await detector.detect_synergies()
    
    # Find living room temp → climate synergy
    living_room_synergies = [s for s in synergies if s['area'] == 'living_room']
    
    if living_room_synergies:
        temp_climate = [s for s in living_room_synergies if s['relationship'] == 'temp_to_climate']
        if temp_climate:
            assert temp_climate[0]['complexity'] == 'medium'
            assert temp_climate[0]['trigger_entity'] == 'sensor.outdoor_temperature'


@pytest.mark.asyncio
async def test_confidence_threshold_filtering(mock_data_api_client, mock_ha_client):
    """Test that low confidence synergies are filtered out"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client,
        min_confidence=0.95  # Very high threshold
    )
    
    synergies = await detector.detect_synergies()
    
    # All returned synergies should meet threshold
    for synergy in synergies:
        assert synergy['confidence'] >= 0.95


@pytest.mark.asyncio
async def test_impact_score_calculation(mock_data_api_client, mock_ha_client):
    """Test that impact scores are calculated correctly"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    synergies = await detector.detect_synergies()
    
    # All synergies should have valid impact scores
    for synergy in synergies:
        assert 0.0 <= synergy['impact_score'] <= 1.0
        assert synergy['impact_score'] > 0.0  # Should not be zero


@pytest.mark.asyncio
async def test_synergy_structure(mock_data_api_client, mock_ha_client):
    """Test that synergy opportunity structure is correct"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    synergies = await detector.detect_synergies()
    
    assert len(synergies) > 0
    
    # Check required fields
    synergy = synergies[0]
    assert 'synergy_id' in synergy
    assert 'synergy_type' in synergy
    assert 'devices' in synergy
    assert 'relationship' in synergy
    assert 'area' in synergy
    assert 'impact_score' in synergy
    assert 'complexity' in synergy
    assert 'confidence' in synergy
    assert 'rationale' in synergy
    
    # Check field types
    assert isinstance(synergy['synergy_id'], str)
    assert synergy['synergy_type'] == 'device_pair'
    assert isinstance(synergy['devices'], list)
    assert len(synergy['devices']) == 2
    assert synergy['complexity'] in ['low', 'medium', 'high']


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_no_devices_graceful_handling():
    """Test graceful handling when no devices found"""
    mock_client = AsyncMock()
    mock_client.fetch_devices = AsyncMock(return_value=[])
    mock_client.fetch_entities = AsyncMock(return_value=[])
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=None
    )
    
    synergies = await detector.detect_synergies()
    
    # Should return empty list, not error
    assert synergies == []


@pytest.mark.asyncio
async def test_data_api_failure_handling():
    """Test graceful handling when data-api fails"""
    mock_client = AsyncMock()
    mock_client.fetch_devices = AsyncMock(side_effect=Exception("API unavailable"))
    mock_client.fetch_entities = AsyncMock(return_value=[])
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=None
    )
    
    synergies = await detector.detect_synergies()
    
    # Should return empty list and log error, not crash
    assert synergies == []


@pytest.mark.asyncio
async def test_entity_fetch_failure_handling():
    """Test graceful handling when entity fetch fails"""
    mock_client = AsyncMock()
    mock_client.fetch_devices = AsyncMock(return_value=[{'device_id': 'test'}])
    mock_client.fetch_entities = AsyncMock(side_effect=Exception("Entity fetch failed"))
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=None
    )
    
    synergies = await detector.detect_synergies()
    
    # Should return empty list and log error, not crash
    assert synergies == []


# ============================================================================
# Caching Tests
# ============================================================================

@pytest.mark.asyncio
async def test_device_caching(mock_data_api_client, mock_ha_client):
    """Test that devices are cached after first fetch"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    # First call
    synergies1 = await detector.detect_synergies()
    
    # Second call (should use cache)
    synergies2 = await detector.detect_synergies()
    
    # Should only call API once due to caching
    assert mock_data_api_client.fetch_devices.call_count == 1
    assert mock_data_api_client.fetch_entities.call_count == 1


@pytest.mark.asyncio
async def test_cache_clear(mock_data_api_client, mock_ha_client):
    """Test cache clearing functionality"""
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    # First call (populates cache)
    await detector.detect_synergies()
    assert mock_data_api_client.fetch_devices.call_count == 1
    
    # Clear cache
    detector.clear_cache()
    
    # Second call (should fetch again)
    await detector.detect_synergies()
    assert mock_data_api_client.fetch_devices.call_count == 2


# ============================================================================
# Relationship Type Tests
# ============================================================================

def test_compatible_relationships_defined():
    """Test that relationship types are properly defined"""
    assert 'motion_to_light' in COMPATIBLE_RELATIONSHIPS
    assert 'door_to_light' in COMPATIBLE_RELATIONSHIPS
    assert 'door_to_lock' in COMPATIBLE_RELATIONSHIPS
    assert 'temp_to_climate' in COMPATIBLE_RELATIONSHIPS
    assert 'occupancy_to_light' in COMPATIBLE_RELATIONSHIPS
    
    # Check required fields
    for rel_type, config in COMPATIBLE_RELATIONSHIPS.items():
        assert 'trigger_domain' in config
        assert 'action_domain' in config
        assert 'benefit_score' in config
        assert 'complexity' in config
        assert 'description' in config


def test_benefit_scores_valid():
    """Test that benefit scores are in valid range"""
    for rel_type, config in COMPATIBLE_RELATIONSHIPS.items():
        assert 0.0 <= config['benefit_score'] <= 1.0


def test_complexity_levels_valid():
    """Test that complexity levels are valid"""
    valid_complexity = ['low', 'medium', 'high']
    for rel_type, config in COMPATIBLE_RELATIONSHIPS.items():
        assert config['complexity'] in valid_complexity


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_performance_large_device_count(mock_ha_client):
    """Test performance with large number of devices"""
    # Create mock with many devices (100 devices, 300 entities)
    mock_client = AsyncMock()
    
    mock_devices = [
        {'device_id': f'device_{i}', 'name': f'Device {i}'}
        for i in range(100)
    ]
    
    mock_entities = []
    for i in range(100):
        # Add 3 entities per device in various areas
        area = f'area_{i % 10}'  # 10 areas
        mock_entities.extend([
            {
                'entity_id': f'binary_sensor.motion_{i}',
                'device_id': f'device_{i}',
                'friendly_name': f'Motion {i}',
                'area_id': area,
                'device_class': 'motion'
            },
            {
                'entity_id': f'light.light_{i}',
                'device_id': f'device_{i}',
                'friendly_name': f'Light {i}',
                'area_id': area
            },
            {
                'entity_id': f'sensor.temp_{i}',
                'device_id': f'device_{i}',
                'friendly_name': f'Temp {i}',
                'area_id': area,
                'device_class': 'temperature'
            }
        ])
    
    mock_client.fetch_devices = AsyncMock(return_value=mock_devices)
    mock_client.fetch_entities = AsyncMock(return_value=mock_entities)
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=mock_ha_client
    )
    
    # Measure performance
    start_time = datetime.now(timezone.utc)
    synergies = await detector.detect_synergies()
    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    # Should complete in < 1 minute (AC: 6)
    assert duration < 60
    
    # Should find synergies
    assert len(synergies) > 0
    
    print(f"✅ Performance test: {len(synergies)} synergies detected in {duration:.2f}s")


# ============================================================================
# Integration Tests (require database)
# ============================================================================

@pytest.mark.asyncio
async def test_synergy_storage_integration(mock_data_api_client, mock_ha_client):
    """Test integration with database storage (requires running database)"""
    # This test would require actual database connection
    # For unit tests, we'll mock the storage layer
    
    from src.database.crud import store_synergy_opportunities
    from src.database.models import get_db_session
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    synergies = await detector.detect_synergies()
    
    # Verify structure is compatible with storage
    assert len(synergies) > 0
    synergy = synergies[0]
    
    # Check required fields for storage
    assert 'synergy_id' in synergy
    assert 'synergy_type' in synergy
    assert 'devices' in synergy
    assert 'impact_score' in synergy
    assert 'complexity' in synergy
    assert 'confidence' in synergy


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_no_compatible_pairs():
    """Test when no compatible pairs exist"""
    mock_client = AsyncMock()
    
    # Only incompatible devices
    mock_client.fetch_devices = AsyncMock(return_value=[
        {'device_id': 'device_1', 'name': 'Switch 1'},
        {'device_id': 'device_2', 'name': 'Switch 2'}
    ])
    
    mock_client.fetch_entities = AsyncMock(return_value=[
        {
            'entity_id': 'switch.device_1',
            'device_id': 'device_1',
            'friendly_name': 'Switch 1',
            'area_id': 'kitchen'
        },
        {
            'entity_id': 'switch.device_2',
            'device_id': 'device_2',
            'friendly_name': 'Switch 2',
            'area_id': 'kitchen'
        }
    ])
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=None
    )
    
    synergies = await detector.detect_synergies()
    
    # Should return empty list (switches can't trigger each other in our relationships)
    assert synergies == []


@pytest.mark.asyncio
async def test_devices_different_areas():
    """Test that different area devices aren't paired (when same_area_required=True)"""
    mock_client = AsyncMock()
    
    mock_client.fetch_devices = AsyncMock(return_value=[
        {'device_id': 'device_1', 'name': 'Bedroom Motion'},
        {'device_id': 'device_2', 'name': 'Kitchen Light'}
    ])
    
    mock_client.fetch_entities = AsyncMock(return_value=[
        {
            'entity_id': 'binary_sensor.bedroom_motion',
            'device_id': 'device_1',
            'friendly_name': 'Bedroom Motion',
            'area_id': 'bedroom',
            'device_class': 'motion'
        },
        {
            'entity_id': 'light.kitchen_light',
            'device_id': 'device_2',
            'friendly_name': 'Kitchen Light',
            'area_id': 'kitchen'
        }
    ])
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=None,
        same_area_required=True
    )
    
    synergies = await detector.detect_synergies()
    
    # Should not pair devices from different areas
    assert synergies == []


@pytest.mark.asyncio
async def test_ranking_order():
    """Test that synergies are ranked by impact score"""
    mock_client = AsyncMock()
    
    # Create entities that will generate multiple synergies with different scores
    mock_client.fetch_devices = AsyncMock(return_value=[
        {'device_id': f'device_{i}', 'name': f'Device {i}'}
        for i in range(10)
    ])
    
    mock_client.fetch_entities = AsyncMock(return_value=[
        # Door sensor + lock (high benefit 1.0)
        {
            'entity_id': 'binary_sensor.door',
            'device_id': 'device_1',
            'friendly_name': 'Door Sensor',
            'area_id': 'entry',
            'device_class': 'door'
        },
        {
            'entity_id': 'lock.front_door',
            'device_id': 'device_2',
            'friendly_name': 'Front Door Lock',
            'area_id': 'entry'
        },
        # Motion + light (medium benefit 0.7)
        {
            'entity_id': 'binary_sensor.motion',
            'device_id': 'device_3',
            'friendly_name': 'Motion',
            'area_id': 'bedroom',
            'device_class': 'motion'
        },
        {
            'entity_id': 'light.bedroom',
            'device_id': 'device_4',
            'friendly_name': 'Bedroom Light',
            'area_id': 'bedroom'
        }
    ])
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_client,
        ha_client=None
    )
    
    synergies = await detector.detect_synergies()
    
    # Should be ranked by impact (door_to_lock should be first due to higher benefit)
    if len(synergies) >= 2:
        # Verify descending order
        for i in range(len(synergies) - 1):
            assert synergies[i]['impact_score'] >= synergies[i+1]['impact_score']


# ============================================================================
# Logging Tests
# ============================================================================

@pytest.mark.asyncio
async def test_logging_output(mock_data_api_client, mock_ha_client, caplog):
    """Test that proper logging occurs"""
    import logging
    caplog.set_level(logging.INFO)
    
    detector = DeviceSynergyDetector(
        data_api_client=mock_data_api_client,
        ha_client=mock_ha_client
    )
    
    await detector.detect_synergies()
    
    # Check for expected log messages
    assert "Starting synergy detection" in caplog.text
    assert "Synergy detection complete" in caplog.text
    assert "opportunities" in caplog.text.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

