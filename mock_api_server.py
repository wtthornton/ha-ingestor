#!/usr/bin/env python3
"""
Simple mock API server for HomeIQ Dashboard
Provides basic endpoints that the dashboard expects
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime, timedelta
import random

app = FastAPI(title="HomeIQ Mock API", version="1.0.0")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
def generate_mock_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "influxdb": "healthy",
            "websocket-ingestion": "healthy", 
            "enrichment-pipeline": "healthy",
            "data-api": "healthy",
            "admin-api": "healthy"
        },
        "uptime": "2h 34m",
        "version": "1.0.0"
    }

def generate_mock_statistics():
    return {
        "events_processed": random.randint(1000, 5000),
        "events_per_minute": random.randint(10, 100),
        "active_services": 5,
        "total_devices": random.randint(50, 200),
        "total_entities": random.randint(100, 500),
        "memory_usage_mb": random.randint(200, 800),
        "cpu_usage_percent": random.randint(5, 25),
        "timestamp": datetime.now().isoformat()
    }

def generate_mock_services():
    services = [
        {
            "name": "influxdb",
            "status": "running",
            "health": "healthy",
            "uptime": "2h 34m",
            "port": 8086,
            "memory_usage": random.randint(100, 300)
        },
        {
            "name": "websocket-ingestion", 
            "status": "running",
            "health": "healthy",
            "uptime": "2h 34m",
            "port": 8001,
            "memory_usage": random.randint(150, 400)
        },
        {
            "name": "enrichment-pipeline",
            "status": "running", 
            "health": "healthy",
            "uptime": "2h 34m",
            "port": 8002,
            "memory_usage": random.randint(100, 250)
        },
        {
            "name": "data-api",
            "status": "running",
            "health": "healthy", 
            "uptime": "2h 34m",
            "port": 8006,
            "memory_usage": random.randint(200, 400)
        },
        {
            "name": "admin-api",
            "status": "running",
            "health": "healthy",
            "uptime": "2h 34m", 
            "port": 8003,
            "memory_usage": random.randint(150, 300)
        }
    ]
    return {"services": services}

def generate_mock_devices():
    devices = []
    manufacturers = ["Philips", "Samsung", "Apple", "Google", "Amazon", "TP-Link", "Ubiquiti"]
    areas = ["Living Room", "Bedroom", "Kitchen", "Bathroom", "Garage", "Office"]
    
    for i in range(random.randint(20, 50)):
        devices.append({
            "id": f"device_{i:03d}",
            "name": f"Device {i+1}",
            "manufacturer": random.choice(manufacturers),
            "model": f"Model-{random.randint(100, 999)}",
            "area_id": random.choice(areas).lower().replace(" ", "_"),
            "area_name": random.choice(areas),
            "integration": random.choice(["homekit", "zha", "zwave", "wifi", "bluetooth"]),
            "disabled": False,
            "entities_count": random.randint(1, 5)
        })
    
    return {
        "devices": devices,
        "total": len(devices),
        "page": 1,
        "per_page": 50
    }

def generate_mock_events():
    events = []
    event_types = ["state_changed", "device_registered", "service_registered", "automation_triggered"]
    entities = ["light.living_room", "switch.kitchen", "sensor.temperature", "camera.front_door"]
    
    for i in range(random.randint(10, 50)):
        events.append({
            "id": f"event_{i:06d}",
            "event_type": random.choice(event_types),
            "entity_id": random.choice(entities),
            "state": random.choice(["on", "off", "unavailable", "unknown"]),
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat(),
            "attributes": {
                "friendly_name": f"Entity {i+1}",
                "unit_of_measurement": random.choice(["°C", "%", "W", "V", None])
            }
        })
    
    return {
        "events": events,
        "total": len(events),
        "page": 1,
        "per_page": 50
    }

# Health endpoints
@app.get("/health")
async def health():
    return generate_mock_health()

@app.get("/api/v1/health")
async def health_v1():
    return generate_mock_health()

# Statistics
@app.get("/api/v1/stats")
async def stats(period: str = "1h"):
    return generate_mock_statistics()

# Services
@app.get("/api/v1/services")
async def services():
    return generate_mock_services()

@app.get("/health/services")
async def health_services():
    return generate_mock_services()

# Devices
@app.get("/api/devices")
async def devices():
    return generate_mock_devices()

# Events  
@app.get("/api/v1/events")
async def events():
    return generate_mock_events()

# Real-time metrics
@app.get("/api/v1/real-time-metrics")
async def real_time_metrics():
    return {
        "services": generate_mock_services(),
        "events": generate_mock_statistics(),
        "performance": {
            "avg_response_time_ms": random.randint(10, 100),
            "requests_per_minute": random.randint(50, 200),
            "error_rate_percent": random.uniform(0, 5)
        },
        "health": generate_mock_health()
    }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "HomeIQ Mock API Server", "status": "running"}

if __name__ == "__main__":
    print("🚀 Starting HomeIQ Mock API Server...")
    print("📊 Dashboard should be available at: http://localhost:3001")
    print("🔧 API endpoints available at: http://localhost:8003")
    print("📚 API docs available at: http://localhost:8003/docs")
    
    uvicorn.run(
        "mock_api_server:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )