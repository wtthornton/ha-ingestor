#!/usr/bin/env python3
"""
Import All Dashboards Script
Automatically imports all the production dashboards into Grafana.
"""

import json
import sys
import time
from pathlib import Path

import requests


class DashboardImporter:
    def __init__(self):
        self.grafana_url = "http://localhost:3000"
        self.username = "admin"
        self.password = "Rom24aedslas!@"
        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

        # Dashboard files to import
        self.dashboard_files = [
            "grafana/provisioning/dashboards/executive_overview.json",
            "grafana/provisioning/dashboards/technical_operations.json",
            "grafana/provisioning/dashboards/energy_environment.json",
            "grafana/provisioning/dashboards/security_automation.json",
            "grafana/provisioning/dashboards/realtime_monitor.json",
        ]

    def import_dashboard(self, dashboard_file):
        """Import a single dashboard."""
        print(f"📊 Importing {dashboard_file}...")

        if not Path(dashboard_file).exists():
            print(f"❌ Dashboard file not found: {dashboard_file}")
            return False

        try:
            with open(dashboard_file, encoding="utf-8") as f:
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
                dashboard_title = dashboard_data["dashboard"]["title"]
                print(f"✅ Successfully imported: {dashboard_title}")
                return True
            else:
                print(
                    f"❌ Failed to import {dashboard_file}: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            print(f"❌ Error importing {dashboard_file}: {e}")
            return False

    def import_all_dashboards(self):
        """Import all dashboards."""
        print("🚀 Starting dashboard import process...")
        print("=" * 60)

        success_count = 0
        total_count = len(self.dashboard_files)

        for dashboard_file in self.dashboard_files:
            if self.import_dashboard(dashboard_file):
                success_count += 1
            time.sleep(1)  # Small delay between imports

        print("=" * 60)
        print("📊 Import Summary:")
        print(f"   ✅ Successful: {success_count}/{total_count}")
        print(f"   ❌ Failed: {total_count - success_count}/{total_count}")

        if success_count == total_count:
            print("\n🎉 All dashboards imported successfully!")
            print(f"🌐 Access your dashboards at: {self.grafana_url}")
            print("👤 Username: admin")
            print("🔑 Password: Rom24aedslas!@")
            print("\n📊 Available Dashboards:")
            print("   🏠 Home Assistant Executive Overview")
            print("   🔧 Home Assistant Technical Operations")
            print("   🌱 Energy & Environment Monitoring")
            print("   🔒 Security & Automation Control")
            print("   ⚡ Real-Time System Monitor")
            return True
        else:
            print("\n⚠️  Some dashboards failed to import. Check the logs above.")
            return False


def main():
    """Main function."""
    print("📊 Grafana Dashboard Import Tool")
    print("=" * 60)

    importer = DashboardImporter()
    success = importer.import_all_dashboards()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
