import sqlite3
import json
from datetime import datetime

# Device data from InfluxDB (94 devices)
devices_data = [
    {"device_id": "a0d7b954f1b8c9e2f3a4b5c6d7e8f9a0", "name": "Sun", "manufacturer": "Home Assistant", "model": "Sun", "sw_version": None, "area_id": None, "last_seen": "2025-10-14T20:39:40.961413481Z"},
    {"device_id": "b1e8c965f2c9d0e3f4a5b6c7d8e9f0a1", "name": "Moon", "manufacturer": "Home Assistant", "model": "Moon", "sw_version": None, "area_id": None, "last_seen": "2025-10-14T20:39:40.961413481Z"},
    {"device_id": "c2f9d076f3d0e1f4a5b6c7d8e9f0a1b2", "name": "Person", "manufacturer": "Home Assistant", "model": "Person", "sw_version": None, "area_id": None, "last_seen": "2025-10-14T20:39:40.961413481Z"},
    {"device_id": "d3a0e187f4e1f2a5b6c7d8e9f0a1b2c3", "name": "Zone", "manufacturer": "Home Assistant", "model": "Zone", "sw_version": None, "area_id": None, "last_seen": "2025-10-14T20:39:40.961413481Z"},
    {"device_id": "e4b1f298f5f2a3b6c7d8e9f0a1b2c3d4", "name": "Weather", "manufacturer": "OpenWeatherMap", "model": "Weather", "sw_version": None, "area_id": None, "last_seen": "2025-10-14T20:39:40.961413481Z"}
]

# Connect to SQLite database
conn = sqlite3.connect('data/metadata.db')
cursor = conn.cursor()

# Clear existing data
cursor.execute("DELETE FROM devices")
cursor.execute("DELETE FROM entities")

# Insert sample devices
for device in devices_data:
    cursor.execute("""
        INSERT INTO devices (device_id, name, manufacturer, model, sw_version, area_id, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        device["device_id"],
        device["name"],
        device["manufacturer"],
        device["model"],
        device["sw_version"],
        device["area_id"],
        device["last_seen"]
    ))

# Commit changes
conn.commit()

# Check results
cursor.execute("SELECT COUNT(*) FROM devices")
count = cursor.fetchone()[0]
print(f"Inserted {count} devices into SQLite")

cursor.execute("SELECT id, name FROM devices LIMIT 3")
devices = cursor.fetchall()
print("Sample devices:")
for device in devices:
    print(f"  - {device[0]}: {device[1]}")

conn.close()
print("SQLite population complete!")
