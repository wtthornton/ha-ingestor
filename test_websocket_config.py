#!/usr/bin/env python3
"""
Test script to check WebSocket service weather configuration
"""
import sys
import os

# Add the websocket-ingestion src directory to path
sys.path.append('/app/src')

from main import WebSocketIngestionService

def test_websocket_config():
    """Test WebSocket service weather configuration"""
    print("Testing WebSocket service weather configuration...")
    
    # Create service instance
    service = WebSocketIngestionService()
    
    print(f"Weather API key present: {service.weather_api_key is not None}")
    print(f"Weather API key (first 10 chars): {service.weather_api_key[:10] if service.weather_api_key else 'None'}...")
    print(f"Weather enrichment enabled: {service.weather_enrichment_enabled}")
    print(f"Weather enrichment service initialized: {service.weather_enrichment is not None}")
    print(f"Default location: {service.weather_default_location}")
    
    # Check environment variables
    print("\nEnvironment variables:")
    print(f"WEATHER_API_KEY: {os.getenv('WEATHER_API_KEY', 'Not set')}")
    print(f"WEATHER_ENRICHMENT_ENABLED: {os.getenv('WEATHER_ENRICHMENT_ENABLED', 'Not set')}")
    print(f"WEATHER_DEFAULT_LOCATION: {os.getenv('WEATHER_DEFAULT_LOCATION', 'Not set')}")

if __name__ == "__main__":
    test_websocket_config()
