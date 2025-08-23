#!/usr/bin/env python3
"""
Automated Grafana Setup Script for ha-ingestor
This script automatically configures InfluxDB data source and imports the dashboard.
"""

import json
import sys
import time
from pathlib import Path

import requests


class GrafanaAutomation:
    def __init__(self):
        self.grafana_url = "http://localhost:3000"
        self.username = "admin"
        self.password = "Rom24aedslas!@"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

    def wait_for_grafana(self):
        """Wait for Grafana to be ready."""
        print("⏳ Waiting for Grafana to be ready...")
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = self.session.get(f"{self.grafana_url}/api/health")
                if response.status_code == 200:
                    print("✅ Grafana is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass

            print(f"   Attempt {attempt + 1}/{max_attempts}...")
            time.sleep(2)

        print("❌ Grafana is not responding. Please check if the service is running.")
        return False

    def create_influxdb_datasource(self):
        """Create InfluxDB data source."""
        print("🔧 Creating InfluxDB data source...")

        datasource_config = {
            "name": "InfluxDB",
            "type": "influxdb",
            "url": "http://influxdb:8086",
            "access": "proxy",
            "database": "ha_events",
            "user": "admin",
            "password": "Rom24aedslas!@",
            "jsonData": {
                "version": "Flux",
                "organization": "myorg",
                "defaultBucket": "ha_events",
                "tlsSkipVerify": True,
            },
            "secureJsonData": {"password": "Rom24aedslas!@"},
        }

        try:
            response = self.session.post(
                f"{self.grafana_url}/api/datasources",
                json=datasource_config,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                print("✅ InfluxDB data source created successfully!")
                return True
            elif response.status_code == 409:
                print("ℹ️  InfluxDB data source already exists.")
                return True
            else:
                print(
                    f"❌ Failed to create data source: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Error creating data source: {e}")
            return False

    def import_dashboard(self):
        """Import the Home Assistant dashboard."""
        print("📊 Importing Home Assistant dashboard...")

        # Read the dashboard JSON file
        dashboard_file = Path(
            "grafana/provisioning/dashboards/home_assistant_dashboard.json"
        )
        if not dashboard_file.exists():
            print("❌ Dashboard file not found!")
            return False

        try:
            with open(dashboard_file) as f:
                dashboard_data = json.load(f)

            # Prepare dashboard for import
            import_data = {
                "dashboard": dashboard_data["dashboard"],
                "overwrite": True,
                "inputs": [
                    {
                        "name": "DS_INFLUXDB",
                        "type": "datasource",
                        "pluginId": "influxdb",
                        "value": "InfluxDB",
                    }
                ],
            }

            response = self.session.post(
                f"{self.grafana_url}/api/dashboards/import",
                json=import_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                result = response.json()
                if "url" in result:
                    dashboard_url = f"{self.grafana_url}{result['url']}"
                    print("✅ Dashboard imported successfully!")
                    print(f"🌐 Dashboard URL: {dashboard_url}")
                else:
                    print("✅ Dashboard imported successfully!")
                    print("🌐 Check your Grafana dashboards list")
                return True
            else:
                print(
                    f"❌ Failed to import dashboard: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Error importing dashboard: {e}")
            return False

    def test_data_source(self):
        """Test the InfluxDB data source connection."""
        print("🧪 Testing InfluxDB connection...")

        try:
            response = self.session.post(
                f"{self.grafana_url}/api/datasources/proxy/1/query",
                json={"q": "SHOW MEASUREMENTS", "db": "ha_events"},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                print("✅ InfluxDB connection test successful!")
                return True
            else:
                print(f"⚠️  InfluxDB connection test returned: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error testing data source: {e}")
            return False

    def run_setup(self):
        """Run the complete setup process."""
        print("🚀 Starting automated Grafana setup...")
        print("=" * 50)

        # Step 1: Create data source (Grafana is already running)
        print("✅ Grafana is already running at localhost:3000")
        if not self.create_influxdb_datasource():
            return False

        # Step 2: Test data source
        if not self.test_data_source():
            print("⚠️  Data source test failed, but continuing...")

        # Step 3: Import dashboard
        if not self.import_dashboard():
            return False

        print("=" * 50)
        print("🎉 Setup completed successfully!")
        print(f"🌐 Grafana URL: {self.grafana_url}")
        print("👤 Username: admin")
        print("🔑 Password: Rom24aedslas!@")
        print("\n📊 Your Home Assistant dashboard should now be available!")
        print(
            "💡 Try publishing a test MQTT message from Home Assistant to see data flow."
        )

        return True


def main():
    """Main function."""
    print("🏠 ha-ingestor Grafana Automation Setup")
    print("=" * 50)

    # Check if required files exist
    required_files = [
        "grafana/provisioning/dashboards/home_assistant_dashboard.json",
        "docker-compose.monitoring.yml",
    ]

    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Required file not found: {file_path}")
            print(
                "Please ensure you're running this script from the ha-ingestor directory."
            )
            return 1

    # Run setup
    automation = GrafanaAutomation()
    success = automation.run_setup()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
