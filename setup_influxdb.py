#!/usr/bin/env python3
"""
Setup script to configure InfluxDB for ha-ingestor.
"""


import requests


def setup_influxdb():
    """Setup InfluxDB for ha-ingestor."""
    print("🔧 Setting up InfluxDB for ha-ingestor...")

    base_url = "http://localhost:8086"

    # Check if InfluxDB is set up
    try:
        response = requests.get(f"{base_url}/api/v2/setup")
        setup_data = response.json()

        if setup_data.get("allowed", False):
            print("⚠️ InfluxDB is not set up yet. Let's set it up...")

            # Setup InfluxDB
            setup_payload = {
                "username": "admin",
                "password": "admin123456",
                "org": "home_assistant",
                "bucket": "home_assistant_events",
                "retentionPeriodSeconds": 0,  # Never expire
            }

            response = requests.post(f"{base_url}/api/v2/setup", json=setup_payload)

            if response.status_code == 201:
                result = response.json()
                token = result.get("auth", {}).get("token")
                org = result.get("org", {}).get("name")
                bucket = result.get("bucket", {}).get("name")

                print("✅ InfluxDB setup completed!")
                print(f"   Token: {token}")
                print(f"   Org: {org}")
                print(f"   Bucket: {bucket}")

                # Create .env configuration
                env_config = f"""# Home Assistant MQTT Configuration (using local Docker)
HA_MQTT_HOST=localhost
HA_MQTT_PORT=1883
HA_MQTT_USERNAME=
HA_MQTT_PASSWORD=
HA_MQTT_CLIENT_ID=ha-ingestor-local

# Home Assistant WebSocket Configuration (disabled for local testing)
HA_WS_URL=ws://localhost:8123/api/websocket
HA_WS_TOKEN=disabled_for_local_testing

# InfluxDB Configuration (using your existing instance)
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN={token}
INFLUXDB_ORG={org}
INFLUXDB_BUCKET={bucket}

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=console

# Performance (conservative for local testing)
INFLUXDB_BATCH_SIZE=10
INFLUXDB_FLUSH_INTERVAL=5

# Advanced Features (DISABLED for deployment)
MQTT_ENABLE_PATTERN_MATCHING=false
MQTT_ENABLE_DYNAMIC_SUBSCRIPTIONS=false
MQTT_ENABLE_TOPIC_OPTIMIZATION=false

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000"""

                with open(".env", "w") as f:
                    f.write(env_config)

                print("✅ Updated .env file with InfluxDB credentials")
                return True

            else:
                print(f"❌ Setup failed: {response.status_code} - {response.text}")
                return False
        else:
            print("✅ InfluxDB is already set up!")
            print("ℹ️  You'll need to use existing credentials or create a new token")

            # Try to get organizations
            try:
                # This will likely fail without auth, but let's try
                response = requests.get(f"{base_url}/api/v2/orgs")
                if response.status_code == 200:
                    orgs = response.json().get("orgs", [])
                    print(f"Available organizations: {[org['name'] for org in orgs]}")
            except:
                pass

            print("\n🔑 To get a valid token:")
            print("1. Open http://localhost:8086 in your browser")
            print("2. Log in to InfluxDB")
            print("3. Go to 'Load Data' -> 'API Tokens'")
            print("4. Create a new token with read/write access to your bucket")
            print("5. Update the .env file with the token")

            return False

    except Exception as e:
        print(f"❌ Error setting up InfluxDB: {e}")
        return False


if __name__ == "__main__":
    setup_influxdb()
