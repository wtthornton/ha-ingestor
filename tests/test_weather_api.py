#!/usr/bin/env python3
"""
Test script to verify Weather API functionality
"""
import asyncio
import sys
import os

# Add the websocket-ingestion src directory to path
sys.path.append('services/websocket-ingestion/src')

from weather_client import OpenWeatherMapClient

async def test_weather_api():
    """Test the Weather API directly"""
    print("Testing Weather API...")
    
    # Initialize client with API key
    api_key = "01342fef09a0a14c6a9bf6447d5934fd"
    client = OpenWeatherMapClient(api_key)
    
    try:
        # Test API call
        print("Making API call to OpenWeatherMap...")
        result = await client.get_current_weather("London,UK")
        
        if result:
            print(f"SUCCESS: API Test PASSED!")
            print(f"Weather data: {result.to_dict()}")
        else:
            print("FAILED: API Test - No data returned")
            
    except Exception as e:
        print(f"FAILED: API Test error: {e}")
    
    finally:
        if hasattr(client, 'close'):
            await client.close()

if __name__ == "__main__":
    asyncio.run(test_weather_api())
