"""
FastAPI Application for Automation Miner

Provides REST API for querying the automation corpus.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from ..miner.database import get_database
from .routes import router
from .admin_routes import router as admin_router  # Story AI4.4
from .device_routes import router as device_router  # Story AI4.3

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown
    
    Creates database tables and starts weekly refresh scheduler.
    """
    logger.info("Starting Automation Miner API...")
    
    # Initialize database
    db = get_database()
    await db.create_tables()
    logger.info("Database initialized")
    
    # Start weekly refresh scheduler (Story AI4.4)
    scheduler = None
    if settings.enable_automation_miner:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from ..jobs.weekly_refresh import setup_weekly_refresh_job
            
            scheduler = AsyncIOScheduler()
            await setup_weekly_refresh_job(scheduler)
            scheduler.start()
            logger.info("✅ Weekly refresh scheduler started")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start weekly refresh scheduler: {e}")
            scheduler = None
    else:
        logger.info("ℹ️  Weekly refresh scheduler disabled (ENABLE_AUTOMATION_MINER=false)")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Automation Miner API...")
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("✅ Weekly refresh scheduler stopped")
    
    await db.close()


# Create FastAPI application
app = FastAPI(
    title="Automation Miner API",
    description="Community knowledge crawler for Home Assistant automations",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/automation-miner")
app.include_router(admin_router, prefix="/api/automation-miner")  # Story AI4.4: Admin endpoints
app.include_router(device_router, prefix="/api/automation-miner")  # Story AI4.3: Device discovery


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service status and corpus information.
    """
    from ..miner.database import get_db_session
    from ..miner.repository import CorpusRepository
    
    async for db in get_db_session():
        try:
            repo = CorpusRepository(db)
            stats = await repo.get_stats()
            last_crawl = await repo.get_last_crawl_timestamp()
            
            return {
                "status": "healthy",
                "service": "automation-miner",
                "version": "0.1.0",
                "corpus": {
                    "total_automations": stats['total'],
                    "avg_quality": stats['avg_quality'],
                    "last_crawl": last_crawl.isoformat() if last_crawl else None
                },
                "enabled": settings.enable_automation_miner
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "automation-miner",
                "error": str(e)
            }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Automation Miner API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8019)

