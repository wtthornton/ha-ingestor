"""
AI Automation Service - Main FastAPI Application
Phase 1 MVP - Pattern detection and suggestion generation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import logging
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Setup logging (use shared logging config)
try:
    from shared.logging_config import setup_logging
    logger = setup_logging("ai-automation-service")
except ImportError:
    # Fallback if shared logging not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ai-automation-service")

from .config import settings
from .database.models import init_db
from .api import health_router, data_router, pattern_router

# Create FastAPI application
app = FastAPI(
    title="AI Automation Service",
    description="AI-powered Home Assistant automation suggestion system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow frontend at port 3002)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3002",
        "http://127.0.0.1:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(data_router)
app.include_router(pattern_router)


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("=" * 60)
    logger.info("AI Automation Service Starting Up")
    logger.info("=" * 60)
    logger.info(f"Data API: {settings.data_api_url}")
    logger.info(f"Home Assistant: {settings.ha_url}")
    logger.info(f"MQTT Broker: {settings.mqtt_broker}:{settings.mqtt_port}")
    logger.info(f"Analysis Schedule: {settings.analysis_schedule}")
    logger.info("=" * 60)
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    logger.info("✅ AI Automation Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("AI Automation Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8018,
        log_level=settings.log_level.lower()
    )

