#!/usr/bin/env python3
"""
Test script to check weather cache and force API calls
"""
import asyncio
import sys
import os

# Add the websocket-ingestion src directory to path
sys.path.append('/app/src')

from weather_enrichment import WeatherEnrichmentService

async def test_weather_cache():
    """Test weather cache behavior"""
    print("Testing Weather Cache Behavior...")
    
    # Initialize service with API key
    api_key = "01342fef09a0a14c6a9bf6447d5934fd"
    service = WeatherEnrichmentService(api_key, "London,UK")
    
    try:
        # Start the service
        await service.start()
        print("Weather enrichment service started")
        
        # Test multiple enrichments to see cache behavior
        for i in range(3):
            test_event = {
                'event_type': 'state_changed',
                'entity_id': f'sensor.test_entity_{i}',
                'domain': 'sensor',
                'timestamp': f'2025-10-10T22:00:{i:02d}Z'
            }
            
            print(f"\nTest {i+1}: Enriching event...")
            enriched_event = await service.enrich_event(test_event)
            
            print(f"Event enriched: {'weather' in enriched_event}")
            print(f"Cache hits: {service.cache_hits}")
            print(f"Cache misses: {service.cache_misses}")
            print(f"Total events processed: {service.total_events_processed}")
            print(f"Successful enrichments: {service.successful_enrichments}")
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        print(f"\nFinal Statistics:")
        print(f"Total events processed: {service.total_events_processed}")
        print(f"Successful enrichments: {service.successful_enrichments}")
        print(f"Failed enrichments: {service.failed_enrichments}")
        print(f"Cache hits: {service.cache_hits}")
        print(f"Cache misses: {service.cache_misses}")
        
    except Exception as e:
        print(f"FAILED: Weather cache test error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(test_weather_cache())
