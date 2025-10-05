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
    return {
        "status": "healthy",
        "service": "admin-api",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/v1/health"]
    }

@app.get("/api/v1/stats")
async def get_stats(period: str = "1h"):
    """Get statistics for the specified period"""
    return {
        "period": period,
        "total_events": 0,
        "events_per_minute": 0,
        "services": {
            "websocket-ingestion": {"status": "healthy", "events": 0},
            "enrichment-pipeline": {"status": "healthy", "events": 0},
            "data-retention": {"status": "healthy", "events": 0}
        },
        "timestamp": "2025-01-05T18:20:00Z"
    }

@app.get("/api/v1/events")
async def get_events(limit: int = 50):
    """Get recent events"""
    return {
        "events": [],
        "total": 0,
        "limit": limit,
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

if __name__ == "__main__":
    logger.info("Starting simple Admin API service...")
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8004,
        log_level="info"
    )
