#!/usr/bin/env python3
"""
Simple test script for HA Simulator

Tests the basic functionality of the HA Simulator WebSocket server.
"""

import asyncio
import json
import logging
import aiohttp
from aiohttp import WSMsgType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simulator():
    """Test the HA Simulator"""
    simulator_url = "ws://localhost:8123/api/websocket"
    auth_token = "dev_simulator_token"
    
    logger.info(f"Connecting to HA Simulator: {simulator_url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(simulator_url) as ws:
                logger.info("✅ Connected to HA Simulator")
                
                # Step 1: Receive auth_required
                msg = await ws.receive()
                if msg.type == WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    logger.info(f"📨 Received: {data}")
                    
                    if data.get("type") == "auth_required":
                        logger.info("🔐 Authentication required")
                        
                        # Step 2: Send authentication
                        auth_msg = {
                            "type": "auth",
                            "access_token": auth_token
                        }
                        await ws.send_str(json.dumps(auth_msg))
                        logger.info("🔑 Sent authentication")
                        
                        # Step 3: Receive auth_ok
                        msg = await ws.receive()
                        if msg.type == WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            logger.info(f"📨 Received: {data}")
                            
                            if data.get("type") == "auth_ok":
                                logger.info("✅ Authentication successful")
                                
                                # Step 4: Subscribe to events
                                subscribe_msg = {
                                    "id": 1,
                                    "type": "subscribe_events"
                                }
                                await ws.send_str(json.dumps(subscribe_msg))
                                logger.info("📡 Subscribed to events")
                                
                                # Step 5: Receive subscription confirmation
                                msg = await ws.receive()
                                if msg.type == WSMsgType.TEXT:
                                    data = json.loads(msg.data)
                                    logger.info(f"📨 Received: {data}")
                                    
                                    if data.get("type") == "result" and data.get("success"):
                                        logger.info("✅ Event subscription successful")
                                        
                                        # Step 6: Wait for events
                                        logger.info("⏳ Waiting for events...")
                                        event_count = 0
                                        
                                        for _ in range(10):  # Wait for up to 10 events
                                            try:
                                                msg = await asyncio.wait_for(ws.receive(), timeout=30.0)
                                                if msg.type == WSMsgType.TEXT:
                                                    data = json.loads(msg.data)
                                                    
                                                    if data.get("type") == "event":
                                                        event_count += 1
                                                        event_data = data.get("event", {})
                                                        entity_id = event_data.get("data", {}).get("entity_id", "unknown")
                                                        event_type = event_data.get("event_type", "unknown")
                                                        
                                                        logger.info(f"📨 Event #{event_count}: {event_type} - {entity_id}")
                                                        
                                                        if event_count >= 5:  # Stop after 5 events
                                                            break
                                            except asyncio.TimeoutError:
                                                logger.warning("⏰ Timeout waiting for events")
                                                break
                                        
                                        logger.info(f"🎉 Test completed! Received {event_count} events")
                                        
                                        if event_count > 0:
                                            logger.info("✅ HA Simulator is working correctly!")
                                            return True
                                        else:
                                            logger.error("❌ No events received")
                                            return False
                                    else:
                                        logger.error(f"❌ Subscription failed: {data}")
                                        return False
                                else:
                                    logger.error("❌ No subscription response received")
                                    return False
                            else:
                                logger.error(f"❌ Authentication failed: {data}")
                                return False
                        else:
                            logger.error("❌ No authentication response received")
                            return False
                    else:
                        logger.error(f"❌ Expected auth_required, got: {data}")
                        return False
                else:
                    logger.error("❌ No initial message received")
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

async def test_health_check():
    """Test the health check endpoint"""
    health_url = "http://localhost:8123/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Health check passed: {data}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting HA Simulator tests")
    
    # Test health check first
    logger.info("1️⃣ Testing health check...")
    health_ok = await test_health_check()
    
    if not health_ok:
        logger.error("❌ Health check failed. Is the simulator running?")
        logger.info("💡 Start the simulator with: docker-compose up ha-simulator")
        return False
    
    # Test WebSocket functionality
    logger.info("2️⃣ Testing WebSocket functionality...")
    websocket_ok = await test_simulator()
    
    if websocket_ok:
        logger.info("🎉 All tests passed!")
        return True
    else:
        logger.error("❌ WebSocket test failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
