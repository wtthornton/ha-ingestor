#!/usr/bin/env python3
"""
Test script to verify Nabu Casa Home Assistant connection
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import aiohttp
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NabuCasaConnectionTest:
    """Test connection to Nabu Casa Home Assistant instance"""
    
    def __init__(self):
        # Nabu Casa URL from the provided link
        self.nabu_casa_url = "https://lwzisze94hrpqde9typkwgu5pptxdkoh.ui.nabu.casa"
        self.ws_url = "wss://lwzisze94hrpqde9typkwgu5pptxdkoh.ui.nabu.casa/api/websocket"
        
        # You'll need to provide your Nabu Casa token
        self.ha_token = os.getenv("NABU_CASA_TOKEN")
        if not self.ha_token:
            logger.error("❌ NABU_CASA_TOKEN environment variable not set")
            logger.info("Please set your Nabu Casa long-lived access token:")
            logger.info("export NABU_CASA_TOKEN=your_long_lived_access_token_here")
            sys.exit(1)
        
        self.ws = None
        self.session = None
        self.is_connected = False
        self.is_authenticated = False
        
    async def test_http_connection(self):
        """Test basic HTTP connectivity to Nabu Casa"""
        try:
            logger.info(f"🌐 Testing HTTP connection to {self.nabu_casa_url}")
            
            async with aiohttp.ClientSession() as session:
                # Test basic connectivity
                async with session.get(f"{self.nabu_casa_url}/api/") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ HTTP connection successful")
                        logger.info(f"📊 Home Assistant version: {data.get('version', 'Unknown')}")
                        return True
                    else:
                        logger.error(f"❌ HTTP connection failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ HTTP connection error: {e}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection to Nabu Casa"""
        try:
            logger.info(f"🔗 Testing WebSocket connection to {self.ws_url}")
            
            # Connect to WebSocket
            self.ws = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            # Wait for auth_required message
            auth_required = await self.ws.recv()
            auth_data = json.loads(auth_required)
            logger.info(f"🔐 Auth required: {auth_data}")
            
            if auth_data.get('type') != 'auth_required':
                logger.error("❌ Expected auth_required message")
                return False
            
            # Send authentication
            auth_message = {
                "type": "auth",
                "access_token": self.ha_token
            }
            await self.ws.send(json.dumps(auth_message))
            
            # Wait for auth response
            auth_response = await self.ws.recv()
            auth_result = json.loads(auth_response)
            logger.info(f"🔑 Auth response: {auth_result}")
            
            if auth_result.get('type') == 'auth_ok':
                logger.info("✅ Authentication successful")
                self.is_authenticated = True
                return True
            else:
                logger.error(f"❌ Authentication failed: {auth_result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            return False
    
    async def test_event_subscription(self):
        """Test event subscription"""
        try:
            if not self.is_authenticated:
                logger.error("❌ Not authenticated, cannot test event subscription")
                return False
            
            logger.info("📡 Testing event subscription...")
            
            # Subscribe to all events
            subscribe_message = {
                "id": 1,
                "type": "subscribe_events"
            }
            await self.ws.send(json.dumps(subscribe_message))
            
            # Wait for subscription confirmation
            response = await self.ws.recv()
            result = json.loads(response)
            logger.info(f"📨 Subscription response: {result}")
            
            if result.get('type') == 'result' and result.get('success'):
                logger.info("✅ Event subscription successful")
                
                # Wait for a few events to confirm it's working
                logger.info("⏳ Waiting for events (10 seconds)...")
                event_count = 0
                start_time = datetime.now()
                
                while (datetime.now() - start_time).seconds < 10:
                    try:
                        event = await asyncio.wait_for(self.ws.recv(), timeout=1.0)
                        event_data = json.loads(event)
                        
                        if event_data.get('type') == 'event':
                            event_count += 1
                            logger.info(f"📨 Event {event_count}: {event_data.get('event', {}).get('event_type', 'unknown')}")
                            
                    except asyncio.TimeoutError:
                        continue
                
                logger.info(f"✅ Received {event_count} events in 10 seconds")
                return True
            else:
                logger.error(f"❌ Event subscription failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Event subscription error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up connections"""
        if self.ws:
            await self.ws.close()
            logger.info("🔌 WebSocket connection closed")
    
    async def run_test(self):
        """Run complete connection test"""
        logger.info("🚀 Starting Nabu Casa connection test...")
        
        try:
            # Test HTTP connection
            http_ok = await self.test_http_connection()
            if not http_ok:
                logger.error("❌ HTTP test failed, aborting")
                return False
            
            # Test WebSocket connection
            ws_ok = await self.test_websocket_connection()
            if not ws_ok:
                logger.error("❌ WebSocket test failed, aborting")
                return False
            
            # Test event subscription
            events_ok = await self.test_event_subscription()
            if not events_ok:
                logger.error("❌ Event subscription test failed")
                return False
            
            logger.info("🎉 All tests passed! Nabu Casa connection is working")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test function"""
    test = NabuCasaConnectionTest()
    success = await test.run_test()
    
    if success:
        logger.info("✅ Nabu Casa connection test completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Nabu Casa connection test failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
