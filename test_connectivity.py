#!/usr/bin/env python3
"""
Quick connectivity test for Home Assistant Ingestor
Tests WebSocket and MQTT connectivity to your Home Assistant instance
"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("❌ websockets library not installed. Install with: pip install websockets")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("❌ paho-mqtt library not installed. Install with: pip install paho-mqtt")
    sys.exit(1)


# Your Home Assistant configuration
HA_WS_URL = "ws://192.168.1.86:8123/api/websocket"
HA_WS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI2ZTc1NDJjODllMDc0NGE3YjI1MWRmMDM0MGE4MzM1ZSIsImlhdCI6MTc1NTU1MzY4NywiZXhwIjoyMDcwOTEzNjg3fQ.vB5StATqW6sUsSIlx0C6MaaOtw3dAarrue9KGFrKVoo"
HA_MQTT_HOST = "192.168.1.86"
HA_MQTT_PORT = 1883


async def test_websocket_connection():
    """Test WebSocket connection to Home Assistant"""
    print("🔌 Testing WebSocket connection...")

    try:
        async with websockets.connect(HA_WS_URL) as websocket:
            print(f"✅ WebSocket connected to {HA_WS_URL}")

            # Authenticate
            auth_msg = {"type": "auth", "access_token": HA_WS_TOKEN}
            await websocket.send(json.dumps(auth_msg))
            response = await websocket.recv()
            auth_response = json.loads(response)

            if auth_response.get("type") == "auth_ok":
                print("✅ WebSocket authentication successful")

                # Subscribe to events
                subscribe_msg = {"id": 1, "type": "subscribe_events"}
                await websocket.send(json.dumps(subscribe_msg))
                response = await websocket.recv()
                subscribe_response = json.loads(response)

                if subscribe_response.get(
                    "type"
                ) == "result" and subscribe_response.get("success"):
                    print("✅ Event subscription successful")

                    # Listen for a few events
                    print("📡 Listening for events (10 seconds)...")
                    events_received = 0

                    try:
                        for _ in range(5):  # Try to get 5 events
                            event = await asyncio.wait_for(websocket.recv(), timeout=10)
                            events_received += 1
                            event_data = json.loads(event)
                            event_type = event_data.get("event", {}).get(
                                "event_type", "unknown"
                            )
                            print(f"📨 Event {events_received}: {event_type}")
                    except TimeoutError:
                        pass

                    print(f"📊 Received {events_received} events in 10 seconds")

                else:
                    print(f"❌ Event subscription failed: {subscribe_response}")

            else:
                print(f"❌ WebSocket authentication failed: {auth_response}")

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

    return True


async def test_mqtt_connection():
    """Test MQTT connection to Home Assistant"""
    print("\n📡 Testing MQTT connection...")

    connection_result = None

    def on_connect(client, userdata, flags, rc):
        nonlocal connection_result
        connection_result = rc
        if rc == 0:
            print(f"✅ MQTT connected to {HA_MQTT_HOST}:{HA_MQTT_PORT}")
        else:
            print(f"❌ MQTT connection failed with code {rc}")

    def on_message(client, userdata, msg):
        print(f"📨 MQTT message: {msg.topic} = {msg.payload.decode()}")

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        # Try to connect without credentials first
        print(f"🔌 Attempting MQTT connection to {HA_MQTT_HOST}:{HA_MQTT_PORT}")
        client.connect(HA_MQTT_HOST, HA_MQTT_PORT, 10)

        # Start the loop
        client.loop_start()

        # Wait for connection result
        timeout = 10
        while connection_result is None and timeout > 0:
            await asyncio.sleep(0.1)
            timeout -= 0.1

        if connection_result == 0:
            # Subscribe to a test topic
            client.subscribe("homeassistant/#", 1)
            print("✅ MQTT subscription successful")

            # Wait a bit for messages
            await asyncio.sleep(5)

            client.loop_stop()
            client.disconnect()
            return True
        else:
            print(f"❌ MQTT connection failed (RC: {connection_result})")
            client.loop_stop()
            return False

    except Exception as e:
        print(f"❌ MQTT connection error: {e}")
        return False


async def main():
    """Run all connectivity tests"""
    print("🚀 Home Assistant Ingestor - Connectivity Test")
    print("=" * 50)
    print(f"🏠 Home Assistant: {HA_WS_URL}")
    print(f"📡 MQTT Broker: {HA_MQTT_HOST}:{HA_MQTT_PORT}")
    print("=" * 50)

    # Test WebSocket
    ws_success = await test_websocket_connection()

    # Test MQTT
    mqtt_success = await test_mqtt_connection()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"WebSocket: {'✅ PASS' if ws_success else '❌ FAIL'}")
    print(f"MQTT:      {'✅ PASS' if mqtt_success else '❌ FAIL'}")

    if ws_success and mqtt_success:
        print("\n🎉 All tests passed! Your Home Assistant is ready for development.")
        print("Next step: Start implementing Phase 1 of the roadmap.")
    elif ws_success:
        print("\n⚠️  WebSocket working, but MQTT needs configuration.")
        print("Check your MQTT broker settings and credentials.")
    elif mqtt_success:
        print("\n⚠️  MQTT working, but WebSocket needs configuration.")
        print("Check your Home Assistant WebSocket API settings.")
    else:
        print("\n❌ Both connections failed. Check your network and configuration.")

    print("\n📚 See DEVELOPMENT.md for detailed setup instructions.")


if __name__ == "__main__":
    asyncio.run(main())
