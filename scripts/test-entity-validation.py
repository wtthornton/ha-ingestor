#!/usr/bin/env python3
"""
Test Entity Validation Fix
Directly tests the entity validation functionality
"""

import asyncio
import sys
import os

# Add the service path
sys.path.append('/app/src')

async def test_entity_validation():
    """Test the entity validation functionality"""
    try:
        from services.entity_validator import EntityValidator
        from clients.data_api_client import DataAPIClient
        
        print("🔍 Testing Entity Validation...")
        
        # Initialize clients
        data_api_client = DataAPIClient()
        entity_validator = EntityValidator(data_api_client)
        
        # Test fetching entities
        print("📡 Fetching entities from data-api...")
        entities = await entity_validator._get_available_entities()
        print(f"✅ Found {len(entities)} entities")
        
        if entities:
            print("📋 Sample entities:")
            for i, entity in enumerate(entities[:5]):
                print(f"  {i+1}. {entity.get('entity_id', 'Unknown')}")
        
        # Test entity mapping
        print("\n🔍 Testing entity mapping...")
        test_query = "When the front door opens I want the office light to blink Red for 5 secs"
        test_devices = ["office", "light", "door", "front"]
        
        mapping = await entity_validator.map_query_to_entities(test_query, test_devices)
        print(f"✅ Entity mapping result: {mapping}")
        
        # Test validation
        print("\n🔍 Testing entity validation...")
        test_entities = ["light.office_light", "binary_sensor.front_door", "light.hue_color_downlight_1_7"]
        validation_results = await entity_validator.validate_entities(test_entities)
        
        for entity_id, result in validation_results.items():
            status = "✅ EXISTS" if result.exists else "❌ NOT FOUND"
            print(f"  {entity_id}: {status}")
            if result.suggested_alternatives:
                print(f"    Alternatives: {result.suggested_alternatives}")
        
        print("\n🎉 Entity validation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during entity validation test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_entity_validation())
