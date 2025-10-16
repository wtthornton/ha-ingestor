import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('data/metadata.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if devices table exists and has data
if any('devices' in str(table).lower() for table in tables):
    cursor.execute("SELECT COUNT(*) FROM devices")
    count = cursor.fetchone()[0]
    print(f"\nDevices table has {count} records")
    
    if count > 0:
        cursor.execute("SELECT id, name FROM devices LIMIT 3")
        devices = cursor.fetchall()
        print("Sample devices:")
        for device in devices:
            print(f"  - {device[0]}: {device[1]}")

# Check entities table
if any('entities' in str(table).lower() for table in tables):
    cursor.execute("SELECT COUNT(*) FROM entities")
    count = cursor.fetchone()[0]
    print(f"\nEntities table has {count} records")

conn.close()
