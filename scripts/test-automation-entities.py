#!/usr/bin/env python3
"""
Home Assistant Entity Verification Script
Tests for the automation entities that are causing "Entity not found" errors.
"""

import requests
import json
import sys
import os
from typing import List, Dict, Optional
from pathlib import Path

# Load configuration from environment file
def load_env_config():
    """Load configuration from the ai-automation env file."""
    env_file = Path("infrastructure/env.ai-automation")
    if not env_file.exists():
        print(f"❌ Environment file not found: {env_file}")
        sys.exit(1)
    
    config = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                # Remove inline comments
                if '#' in line:
                    line = line.split('#')[0].strip()
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    return config

# Load configuration
config = load_env_config()
HA_BASE_URL = config.get('HA_URL', 'http://192.168.1.86:8123')
HA_TOKEN = config.get('HA_TOKEN')

def get_all_entities() -> List[Dict]:
    """Fetch all entities from Home Assistant."""
    url = f"{HA_BASE_URL}/api/states"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching entities: {e}")
        return []

def find_entities(entities: List[Dict], search_terms: List[str]) -> Dict[str, List[Dict]]:
    """Find entities matching search terms."""
    results = {}
    
    for term in search_terms:
        matches = []
        for entity in entities:
            entity_id = entity['entity_id'].lower()
            friendly_name = entity.get('attributes', {}).get('friendly_name', '').lower()
            
            if (term.lower() in entity_id or 
                term.lower() in friendly_name or
                any(word in entity_id for word in term.lower().split()) or
                any(word in friendly_name for word in term.lower().split())):
                matches.append(entity)
        
        results[term] = matches
    
    return results

def test_specific_entities(entities: List[Dict]) -> Dict[str, bool]:
    """Test for the specific entities mentioned in the error."""
    target_entities = [
        "light.office_light",
        "binary_sensor.front_door"
    ]
    
    results = {}
    for entity_id in target_entities:
        found = any(e['entity_id'] == entity_id for e in entities)
        results[entity_id] = found
    
    return results

def print_entity_info(entity: Dict):
    """Print formatted entity information."""
    entity_id = entity['entity_id']
    friendly_name = entity.get('attributes', {}).get('friendly_name', 'No name')
    state = entity['state']
    domain = entity_id.split('.')[0]
    
    print(f"  📍 {entity_id}")
    print(f"     Name: {friendly_name}")
    print(f"     State: {state}")
    print(f"     Domain: {domain}")
    print()

def main():
    """Main function to run entity verification."""
    print("🔍 Home Assistant Entity Verification")
    print("=" * 50)
    
    if not HA_TOKEN:
        print("❌ Error: HA_TOKEN not found in environment file")
        print("   Check infrastructure/env.ai-automation file")
        sys.exit(1)
    
    print("📡 Fetching entities from Home Assistant...")
    entities = get_all_entities()
    
    if not entities:
        print("❌ Failed to fetch entities. Check your connection and token.")
        sys.exit(1)
    
    print(f"✅ Found {len(entities)} total entities")
    print()
    
    # Test specific entities from error
    print("🎯 Testing Specific Entities (from error logs):")
    print("-" * 40)
    
    specific_results = test_specific_entities(entities)
    for entity_id, found in specific_results.items():
        status = "✅ Found" if found else "❌ Not Found"
        print(f"  {entity_id}: {status}")
    
    print()
    
    # Search for similar entities
    print("🔎 Searching for Similar Entities:")
    print("-" * 40)
    
    search_terms = ["office", "light", "door", "front"]
    search_results = find_entities(entities, search_terms)
    
    for term, matches in search_results.items():
        if matches:
            print(f"\n📋 Entities matching '{term}':")
            for entity in matches[:5]:  # Show first 5 matches
                print_entity_info(entity)
            if len(matches) > 5:
                print(f"  ... and {len(matches) - 5} more")
        else:
            print(f"\n❌ No entities found matching '{term}'")
    
    # Summary and recommendations
    print("\n📝 Summary and Recommendations:")
    print("=" * 50)
    
    missing_entities = [eid for eid, found in specific_results.items() if not found]
    
    if missing_entities:
        print("❌ Missing entities that need to be fixed:")
        for entity_id in missing_entities:
            print(f"  - {entity_id}")
        
        print("\n🔧 Possible solutions:")
        print("  1. Check if the device is connected and online")
        print("  2. Verify the integration is working")
        print("  3. Check for typos in entity names")
        print("  4. Look for similar entity names above")
        print("  5. Re-configure the integration if needed")
    else:
        print("✅ All target entities found!")
        print("   The automation should work if these entities are used correctly.")
    
    print(f"\n📊 Total entities checked: {len(entities)}")
    print("🏁 Entity verification complete!")

if __name__ == "__main__":
    main()
