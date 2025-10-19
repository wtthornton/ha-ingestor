"""
Admin Routes for Automation Miner

Manual job triggers and management endpoints.

Epic AI-4, Story AI4.4
"""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime

from ..jobs.weekly_refresh import WeeklyRefreshJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/refresh/trigger")
async def trigger_manual_refresh(background_tasks: BackgroundTasks):
    """
    Manually trigger corpus refresh
    
    Runs the weekly refresh job immediately in the background.
    Useful for testing or recovering from failed scheduled runs.
    """
    logger.info("Manual corpus refresh triggered via API")
    
    job = WeeklyRefreshJob()
    background_tasks.add_task(job.run)
    
    return {
        "status": "triggered",
        "message": "Weekly refresh job started in background",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/refresh/status")
async def get_refresh_status():
    """
    Get weekly refresh job status
    
    Returns information about the last refresh and next scheduled run.
    """
    from ..miner.database import get_db_session
    from ..miner.repository import CorpusRepository
    
    async for db in get_db_session():
        try:
            repo = CorpusRepository(db)
            last_crawl = await repo.get_last_crawl_timestamp()
            stats = await repo.get_stats()
            
            if last_crawl:
                days_since = (datetime.utcnow() - last_crawl).days
                next_refresh = "Sunday 2 AM"  # Static, could calculate actual next run
            else:
                days_since = None
                next_refresh = "Not scheduled (no initial crawl yet)"
            
            return {
                "last_refresh": last_crawl.isoformat() if last_crawl else None,
                "days_since_refresh": days_since,
                "next_refresh": next_refresh,
                "corpus_total": stats['total'],
                "corpus_quality": stats['avg_quality'],
                "status": "healthy" if (not last_crawl or days_since <= 7) else "stale"
            }
        
        except Exception as e:
            logger.error(f"Failed to get refresh status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

