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
from .api import health_router, data_router, pattern_router, suggestion_router, analysis_router, suggestion_management_router, deployment_router
from .api.analysis_router import set_scheduler
from .scheduler import DailyAnalysisScheduler

# Create FastAPI application
app = FastAPI(
    title="AI Automation Service",
    description="AI-powered Home Assistant automation suggestion system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow frontend at ports 3000, 3001, 3002)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Health dashboard
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # AI Automation standalone UI
        "http://127.0.0.1:3001",
        "http://localhost:3002",  # Legacy
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
app.include_router(suggestion_router)
app.include_router(analysis_router)
app.include_router(suggestion_management_router)
app.include_router(deployment_router)

# Initialize scheduler
scheduler = DailyAnalysisScheduler()
set_scheduler(scheduler)  # Connect scheduler to analysis router


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
    
    # Start scheduler
    try:
        scheduler.start()
        logger.info("✅ Daily analysis scheduler started")
    except Exception as e:
        logger.error(f"❌ Scheduler startup failed: {e}")
        # Don't raise - service can still run without scheduler
    
    logger.info("✅ AI Automation Service ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("AI Automation Service shutting down")
    
    # Stop scheduler
    try:
        scheduler.stop()
        logger.info("✅ Scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Scheduler shutdown failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8018,
        log_level=settings.log_level.lower()
    )

