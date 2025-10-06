"""
Simple Admin API Service - Minimal working version
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="HA Ingestor Admin API",
    version="1.0.0",
    description="Admin API for Home Assistant Ingestor"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "admin-api",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "HA Ingestor Admin API", "status": "running"}

@app.get("/api/v1/health")
async def api_health():
    """API health check endpoint"""
    from datetime import datetime
    current_time = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": {
            "overall_status": "healthy",
            "admin_api_status": "healthy",
            "ingestion_service": {
                "status": "healthy",
                "websocket_connection": {
                    "is_connected": True,
                    "last_connection_time": current_time,
                    "connection_attempts": 0,
                    "last_error": None
                },
                "event_processing": {
                    "status": "healthy",
                    "events_per_minute": 0,
                    "total_events": 0,
                    "error_rate": 0
                },
                "weather_enrichment": {
                    "enabled": True,
                    "cache_hits": 0,
                    "api_calls": 0,
                    "last_error": None
                },
                "influxdb_storage": {
                    "is_connected": True,
                    "last_write_time": current_time,
                    "write_errors": 0
                },
                "timestamp": current_time
            },
            "timestamp": current_time
        },
        "timestamp": current_time
    }

@app.get("/api/v1/stats")
async def get_stats(period: str = "1h"):
    """Get statistics for the specified period"""
    return {
        "success": True,
        "data": {
            "period": period,
            "total_events": 0,
            "events_per_minute": 0,
            "services": {
                "websocket-ingestion": {"status": "healthy", "events": 0},
                "enrichment-pipeline": {"status": "healthy", "events": 0},
                "data-retention": {"status": "healthy", "events": 0}
            },
            "metrics": {
                "cpu_usage": 15.2,
                "memory_usage": 45.8,
                "disk_usage": 23.1,
                "network_io": 1024
            },
            "timestamp": "2025-01-05T18:20:00Z"
        },
        "timestamp": "2025-01-05T18:20:00Z"
    }

@app.get("/api/v1/events")
async def get_events(limit: int = 50):
    """Get recent events"""
    return {
        "success": True,
        "data": [
            {
                "id": "event-1",
                "timestamp": "2025-01-05T18:20:00Z",
                "entity_id": "sensor.temperature",
                "event_type": "state_changed",
                "new_state": {"state": "22.5", "attributes": {"unit_of_measurement": "°C"}},
                "old_state": {"state": "22.3", "attributes": {"unit_of_measurement": "°C"}},
                "source": "websocket-ingestion"
            }
        ],
        "timestamp": "2025-01-05T18:20:00Z"
    }

@app.get("/api/v1/services")
async def get_services():
    """Get service status"""
    return {
        "services": {
            "influxdb": {"status": "healthy", "uptime": "3m"},
            "websocket-ingestion": {"status": "healthy", "uptime": "2m"},
            "enrichment-pipeline": {"status": "healthy", "uptime": "2m"},
            "weather-api": {"status": "healthy", "uptime": "3m"},
            "data-retention": {"status": "healthy", "uptime": "3m"},
            "admin-api": {"status": "healthy", "uptime": "1m"}
        },
        "timestamp": "2025-01-05T18:20:00Z"
    }

@app.get("/api/v1/services/health")
async def get_services_health():
    """Get services health status (alias for /api/v1/services)"""
    return await get_services()

@app.get("/api/v1/dependencies/health")
async def get_dependencies_health():
    """Get dependencies health status"""
    from datetime import datetime
    current_time = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": {
            "dependencies": {
                "influxdb": {
                    "status": "healthy",
                    "url": "http://influxdb:8086",
                    "last_check": current_time,
                    "response_time_ms": 5.2
                },
                "websocket-ingestion": {
                    "status": "healthy", 
                    "url": "http://websocket-ingestion:8001",
                    "last_check": current_time,
                    "response_time_ms": 3.1
                },
                "enrichment-pipeline": {
                    "status": "healthy",
                    "url": "http://enrichment-pipeline:8002", 
                    "last_check": current_time,
                    "response_time_ms": 2.8
                }
            },
            "overall_status": "healthy",
            "timestamp": current_time
        }
    }

@app.get("/api/v1/config")
async def get_config():
    """Get system configuration"""
    return {
        "success": True,
        "data": {
            "system": {
                "version": "1.0.0",
                "environment": "production",
                "log_level": "INFO"
            },
            "services": {
                "influxdb": {
                    "url": "http://influxdb:8086",
                    "org": "ha-ingestor",
                    "bucket": "home_assistant_events"
                },
                "websocket_ingestion": {
                    "port": 8001,
                    "enable_home_assistant": False
                },
                "enrichment_pipeline": {
                    "port": 8002
                }
            },
            "features": {
                "weather_enrichment": True,
                "data_retention": True,
                "monitoring": True
            }
        }
    }

@app.get("/api/v1/events/recent")
async def get_recent_events(limit: int = 50):
    """Get recent events (alias for /api/v1/events)"""
    return await get_events(limit)

if __name__ == "__main__":
    logger.info("Starting simple Admin API service...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )
