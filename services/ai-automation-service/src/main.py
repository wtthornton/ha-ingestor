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
from .api import health_router, data_router, pattern_router, suggestion_router, analysis_router, suggestion_management_router, deployment_router, nl_generation_router
from .api.analysis_router import set_scheduler
from .api.health import set_capability_listener
from .scheduler import DailyAnalysisScheduler

# Epic AI-2: Device Intelligence (Story AI2.1)
from .clients.mqtt_client import MQTTNotificationClient
from .device_intelligence import CapabilityParser, MQTTCapabilityListener

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
        "http://127.0.0.1:3002",
        "http://ai-automation-ui",  # Container network
        "http://ai-automation-ui:80",
        "http://ha-ingestor-dashboard",  # Health dashboard container
        "http://ha-ingestor-dashboard:80"
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
app.include_router(nl_generation_router)  # Story AI1.21: Natural Language

# Initialize scheduler
scheduler = DailyAnalysisScheduler()
set_scheduler(scheduler)  # Connect scheduler to analysis router

# Epic AI-2: Device Intelligence components (Story AI2.1)
mqtt_client = None
capability_parser = None
capability_listener = None


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    global mqtt_client, capability_parser, capability_listener
    
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
    
    # Initialize MQTT client (Epic AI-1 + AI-2)
    try:
        mqtt_client = MQTTNotificationClient(
            broker=settings.mqtt_broker,
            port=settings.mqtt_port,
            username=settings.mqtt_username,
            password=settings.mqtt_password
        )
        mqtt_client.connect()
        logger.info("✅ MQTT client connected")
    except Exception as e:
        logger.error(f"❌ MQTT client initialization failed: {e}")
        # Continue without MQTT - don't block service startup
    
    # Initialize Device Intelligence (Epic AI-2 - Story AI2.1)
    if mqtt_client and mqtt_client.is_connected:
        try:
            capability_parser = CapabilityParser()
            capability_listener = MQTTCapabilityListener(
                mqtt_client=mqtt_client,
                db_session=None,  # Story 2.2 will add database session
                parser=capability_parser
            )
            await capability_listener.start()
            set_capability_listener(capability_listener)  # Connect to health endpoint
            logger.info("✅ Device Intelligence capability listener started")
        except Exception as e:
            logger.error(f"❌ Device Intelligence initialization failed: {e}")
            # Continue without Device Intelligence - don't block service startup
    else:
        logger.warning("⚠️ Device Intelligence not started (MQTT unavailable)")
    
    # Start scheduler (Epic AI-1)
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
    
    # Disconnect MQTT
    if mqtt_client:
        try:
            mqtt_client.disconnect()
            logger.info("✅ MQTT client disconnected")
        except Exception as e:
            logger.error(f"❌ MQTT disconnect failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8018,
        log_level=settings.log_level.lower()
    )

