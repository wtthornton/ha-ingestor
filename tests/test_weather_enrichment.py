#!/usr/bin/env python3
"""
Test script to verify Weather Enrichment functionality
"""
import asyncio
import sys
import os

# Add the websocket-ingestion src directory to path
sys.path.append('/app/src')

from weather_enrichment import WeatherEnrichmentService

async def test_weather_enrichment():
    """Test the Weather Enrichment service directly"""
    print("Testing Weather Enrichment Service...")
    
    # Initialize service with API key
    api_key = "01342fef09a0a14c6a9bf6447d5934fd"
    service = WeatherEnrichmentService(api_key, "London,UK")
    
    try:
        # Start the service
        await service.start()
        print("Weather enrichment service started")
        
        # Test event enrichment
        test_event = {
            'event_type': 'state_changed',
            'entity_id': 'sensor.test_entity',
            'domain': 'sensor',
            'timestamp': '2025-10-10T22:00:00Z'
        }
        
        print("Testing event enrichment...")
        enriched_event = await service.enrich_event(test_event)
        
        print(f"Original event keys: {list(test_event.keys())}")
        print(f"Enriched event keys: {list(enriched_event.keys())}")
        
        if 'weather' in enriched_event:
            print("SUCCESS: Event was enriched with weather data!")
            print(f"Weather data: {enriched_event['weather']}")
        else:
            print("FAILED: Event was not enriched with weather data")
            print(f"Weather enriched flag: {enriched_event.get('weather_enriched', 'not set')}")
            print(f"Weather error: {enriched_event.get('weather_error', 'not set')}")
        
        # Check service statistics
        print(f"Total events processed: {service.total_events_processed}")
        print(f"Successful enrichments: {service.successful_enrichments}")
        print(f"Failed enrichments: {service.failed_enrichments}")
        print(f"Cache hits: {service.cache_hits}")
        print(f"Cache misses: {service.cache_misses}")
        
    except Exception as e:
        print(f"FAILED: Weather enrichment test error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(test_weather_enrichment())
