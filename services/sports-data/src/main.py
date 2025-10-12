"""
Sports Data Service - Main Application

FastAPI service for fetching and caching sports data with team-based filtering.
"""

import os
import logging
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.models import Game, GameList, TeamList, HealthCheck, UserTeams, APIUsageStats
from src.sports_api_client import SportsAPIClient
from src.cache_service import CacheService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sports Data Service",
    description="NFL & NHL Sports Data API with team-based filtering",
    version="1.0.0"
)

# CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
cache = CacheService()
sports_client = SportsAPIClient(cache=cache)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "sports-data",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/api/v1/games/live",
            "/api/v1/games/upcoming",
            "/api/v1/teams",
            "/api/v1/metrics/api-usage"
        ]
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    api_status = await sports_client.test_connection()
    
    return HealthCheck(
        status="healthy" if api_status else "degraded",
        service="sports-data",
        timestamp=datetime.utcnow().isoformat(),
        cache_status=cache.is_connected(),
        api_status=api_status
    )


@app.get("/api/v1/games/live", response_model=GameList, tags=["Games"])
async def get_live_games(
    league: str = Query(None, description="Filter by league (NFL or NHL)"),
    team_ids: str = Query(None, description="Comma-separated team IDs (e.g., 'sf,dal,bos')")
):
    """
    Get live games for selected teams only
    
    Args:
        league: Filter by league ('NFL' or 'NHL')
        team_ids: Comma-separated team IDs (e.g., 'sf,dal,bos')
                 If not provided, returns empty list
    
    Returns:
        JSON with games list and count
    """
    # Parse team IDs
    teams = team_ids.split(',') if team_ids else []
    teams = [t.strip().lower() for t in teams if t.strip()]
    
    logger.info(f"Fetching live games for teams: {teams}")
    
    # Fetch games for selected teams only
    try:
        games = await sports_client.get_live_games(league, teams)
        
        return GameList(
            games=games,
            count=len(games),
            filtered_by_teams=teams
        )
    except Exception as e:
        logger.error(f"Error fetching live games: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching live games: {str(e)}")


@app.get("/api/v1/games/upcoming", response_model=GameList, tags=["Games"])
async def get_upcoming_games(
    league: str = Query(None, description="Filter by league (NFL or NHL)"),
    hours: int = Query(24, description="Number of hours to look ahead"),
    team_ids: str = Query(None, description="Comma-separated team IDs")
):
    """
    Get upcoming games for selected teams in next N hours
    
    Args:
        league: Filter by league ('NFL' or 'NHL')
        hours: Number of hours to look ahead
        team_ids: Comma-separated team IDs (e.g., 'sf,dal,bos')
    
    Returns:
        JSON with games list and count
    """
    # Parse team IDs
    teams = team_ids.split(',') if team_ids else []
    teams = [t.strip().lower() for t in teams if t.strip()]
    
    logger.info(f"Fetching upcoming games for teams: {teams}, hours: {hours}")
    
    try:
        games = await sports_client.get_upcoming_games(league, hours, teams)
        
        return GameList(
            games=games,
            count=len(games),
            filtered_by_teams=teams
        )
    except Exception as e:
        logger.error(f"Error fetching upcoming games: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching upcoming games: {str(e)}")


@app.get("/api/v1/teams", response_model=TeamList, tags=["Teams"])
async def get_available_teams(
    league: str = Query(None, description="Filter by league (NFL or NHL)")
):
    """
    Get list of all available teams for selection
    
    Args:
        league: Filter by league ('NFL' or 'NHL')
    
    Returns:
        JSON with teams list organized by league
    """
    try:
        teams = await sports_client.get_available_teams(league)
        return teams
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching teams: {str(e)}")


@app.get("/api/v1/user/teams", tags=["User Preferences"])
async def get_user_selected_teams(user_id: str = Query("default")):
    """Get user's selected teams from preferences"""
    # In production, fetch from database
    # For now, return from environment or default empty
    selected = os.getenv('SELECTED_TEAMS', '').split(',')
    selected = [t.strip().lower() for t in selected if t.strip()]
    
    # Split into NFL/NHL (basic logic, can be improved)
    nfl_teams = [t for t in selected if t in ['sf', 'dal', 'gb', 'ne', 'kc']]  # Example
    nhl_teams = [t for t in selected if t in ['bos', 'wsh', 'pit', 'chi']]  # Example
    
    return UserTeams(
        user_id=user_id,
        nfl_teams=nfl_teams,
        nhl_teams=nhl_teams
    )


@app.post("/api/v1/user/teams", tags=["User Preferences"])
async def save_user_selected_teams(teams: UserTeams):
    """
    Save user's selected teams
    
    Body example:
    {
        "nfl_teams": ["sf", "dal"],
        "nhl_teams": ["bos", "wsh"]
    }
    """
    # In production, save to database
    # For now, log and return success
    logger.info(f"User {teams.user_id} selected teams: NFL={teams.nfl_teams}, NHL={teams.nhl_teams}")
    
    # Calculate estimated API usage
    total_teams = len(teams.nfl_teams) + len(teams.nhl_teams)
    estimated_daily_calls = total_teams * 12  # ~12 calls per team per day
    
    return {
        "success": True,
        "user_id": teams.user_id,
        "teams_saved": {
            "nfl_teams": teams.nfl_teams,
            "nhl_teams": teams.nhl_teams
        },
        "estimated_daily_api_calls": estimated_daily_calls,
        "within_free_tier": estimated_daily_calls <= 100
    }


@app.get("/api/v1/metrics/api-usage", response_model=APIUsageStats, tags=["Metrics"])
async def get_api_usage():
    """Get API usage statistics"""
    cache_stats = cache.get_stats()
    
    total_teams = 0  # Would come from user preferences in production
    estimated_daily = total_teams * 12
    
    return APIUsageStats(
        total_calls_today=sports_client.api_calls_today,
        nfl_calls=sports_client.nfl_calls,
        nhl_calls=sports_client.nhl_calls,
        cache_hits=cache_stats['hits'],
        cache_misses=cache_stats['misses'],
        estimated_daily_calls=estimated_daily,
        within_free_tier=sports_client.api_calls_today < 100
    )


@app.get("/api/v1/cache/stats", tags=["Cache"])
async def get_cache_stats():
    """Get cache statistics"""
    return cache.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv('PORT', '8005')),
        log_level="info"
    )

