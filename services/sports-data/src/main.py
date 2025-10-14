"""
Sports Data Service - Main Application

FastAPI service for fetching and caching sports data with team-based filtering.
Story 12.1 - Added InfluxDB persistence with circuit breaker pattern.
"""

import os
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional

from src.models import Game, GameList, TeamList, HealthCheck, UserTeams, APIUsageStats
from src.models_history import (HistoricalGameResponse, TeamScheduleResponse, 
                                 GameTimelineResponse, PaginatedGamesResponse)
from src.sports_api_client import SportsAPIClient
from src.cache_service import CacheService
from src.circuit_breaker import CircuitBreaker
from src.influxdb_writer import create_influxdb_writer_from_env
from src.influxdb_query import create_influxdb_query_from_env
from src.stats_calculator import calculate_team_record
from src.webhook_manager import WebhookManager
from src.event_detector import GameEventDetector
from src.ha_endpoints import router as ha_router

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global services (initialized in lifespan)
cache = CacheService()
sports_client = None
circuit_breaker = None
influxdb_writer = None
influxdb_query = None
webhook_manager = None
event_detector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    global sports_client, circuit_breaker, influxdb_writer, influxdb_query, webhook_manager, event_detector
    
    logger.info("Starting Sports Data Service...")
    
    # Initialize circuit breaker
    circuit_breaker = CircuitBreaker(
        failure_threshold=int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '3')),
        timeout_seconds=int(os.getenv('CIRCUIT_BREAKER_TIMEOUT_SECONDS', '60'))
    )
    
    # Initialize InfluxDB writer & query client
    influxdb_writer = create_influxdb_writer_from_env(circuit_breaker)
    influxdb_query = create_influxdb_query_from_env()
    logger.info(f"InfluxDB: {'enabled' if influxdb_writer else 'disabled'}")
    logger.info(f"Historical queries: {'enabled' if influxdb_query else 'disabled'}")
    
    # Initialize API client
    sports_client = SportsAPIClient(cache=cache)
    
    # Initialize webhook manager (Story 12.3)
    webhook_manager = WebhookManager(storage_file="data/webhooks.json")
    await webhook_manager.startup()
    
    # Start event detector (Story 12.3)
    event_detector = GameEventDetector(
        sports_client=sports_client,
        webhook_manager=webhook_manager,
        check_interval=15  # Check every 15 seconds
    )
    await event_detector.start()
    logger.info("Event detector started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if event_detector:
        await event_detector.stop()
    if webhook_manager:
        await webhook_manager.shutdown()


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Sports Data Service",
    description="NFL & NHL Sports Data API with team-based filtering and InfluxDB persistence",
    version="2.0.0",  # Story 12.1
    lifespan=lifespan
)

# CORS middleware for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include HA automation endpoints (Story 12.3)
app.include_router(ha_router)

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
    """Health check endpoint with InfluxDB status"""
    api_status = await sports_client.test_connection()
    
    # Add InfluxDB stats to response
    health_data = HealthCheck(
        status="healthy" if api_status else "degraded",
        service="sports-data",
        timestamp=datetime.utcnow().isoformat(),
        cache_status=cache.is_connected(),
        api_status=api_status
    )
    
    # Add InfluxDB status as extra field
    if influxdb_writer:
        health_data.influxdb = influxdb_writer.get_stats()
    else:
        health_data.influxdb = {'enabled': False}
    
    return health_data


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
        
        # Write to InfluxDB (non-blocking, fire-and-forget)
        if influxdb_writer and games:
            sport = league.lower() if league else 'nfl'
            asyncio.create_task(influxdb_writer.write_games(games, sport))
        
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
        
        # Write to InfluxDB (non-blocking, fire-and-forget)
        if influxdb_writer and games:
            sport = league.lower() if league else 'nfl'
            asyncio.create_task(influxdb_writer.write_games(games, sport))
        
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


# ============================================================================
# Story 12.2: Historical Query Endpoints
# ============================================================================

@app.get("/api/v1/games/history", response_model=PaginatedGamesResponse, tags=["History"])
async def get_games_history(
    sport: str = Query("nfl", pattern="^(nfl|nhl)$", description="Sport type"),
    team: Optional[str] = Query(None, description="Team name filter"),
    season: Optional[str] = Query(None, description="Season (e.g., '2025')"),
    status: Optional[str] = Query(None, pattern="^(scheduled|live|finished)$", description="Game status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Results per page")
):
    """
    Query historical games with filters.
    
    Examples:
    - /api/v1/games/history?team=Patriots&season=2025
    - /api/v1/games/history?sport=nhl&status=finished&page=2
    """
    if not influxdb_query:
        raise HTTPException(status_code=503, detail="Historical queries not available")
    
    # Build cache key
    cache_key = f"history:{sport}:{team}:{season}:{status}:{page}:{page_size}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        # Query InfluxDB
        games = influxdb_query.query_games_history(sport, team, season, status, limit=10000)
        
        # Simple pagination
        total = len(games)
        start = (page - 1) * page_size
        end = start + page_size
        page_games = games[start:end]
        
        # Convert to response models
        game_responses = [HistoricalGameResponse(**g) for g in page_games]
        
        result = PaginatedGamesResponse(
            games=game_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
        # Cache for 5 minutes
        cache.set(cache_key, result, ttl=300)
        
        return result
        
    except Exception as e:
        logger.error(f"Error querying game history: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@app.get("/api/v1/games/timeline/{game_id}", response_model=GameTimelineResponse, tags=["History"])
async def get_game_timeline(
    game_id: str,
    sport: str = Query("nfl", pattern="^(nfl|nhl)$", description="Sport type")
):
    """Get score progression for a specific game"""
    if not influxdb_query:
        raise HTTPException(status_code=503, detail="Historical queries not available")
    
    cache_key = f"timeline:{sport}:{game_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        timeline_data = influxdb_query.query_game_timeline(game_id, sport)
        
        if not timeline_data:
            raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
        
        first = timeline_data[0]
        last = timeline_data[-1]
        
        result = GameTimelineResponse(
            game_id=game_id,
            home_team=first.get('home_team', 'Unknown'),
            away_team=first.get('away_team', 'Unknown'),
            timeline=[
                {
                    "time": row['time'].isoformat() if hasattr(row['time'], 'isoformat') else str(row['time']),
                    "home_score": int(row.get('home_score', 0)),
                    "away_score": int(row.get('away_score', 0)),
                    "quarter": row.get('quarter', ''),
                    "time_remaining": row.get('time_remaining', '')
                }
                for row in timeline_data
            ],
            final_score={"home": int(last.get('home_score', 0)), "away": int(last.get('away_score', 0))},
            duration_minutes=len(timeline_data) * 5  # Approximate
        )
        
        cache.set(cache_key, result, ttl=300)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying game timeline: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@app.get("/api/v1/games/schedule/{team}", response_model=TeamScheduleResponse, tags=["History"])
async def get_team_schedule(
    team: str,
    season: str = Query(..., description="Season (e.g., '2025')"),
    sport: str = Query("nfl", pattern="^(nfl|nhl)$", description="Sport type")
):
    """Get full season schedule for a team with statistics"""
    if not influxdb_query:
        raise HTTPException(status_code=503, detail="Historical queries not available")
    
    cache_key = f"schedule:{sport}:{team}:{season}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        games = influxdb_query.query_games_history(sport, team, season)
        
        if not games:
            raise HTTPException(status_code=404, detail=f"No games found for {team} in {season}")
        
        # Convert to response models
        game_responses = [HistoricalGameResponse(**g) for g in games]
        
        # Calculate statistics
        stats = calculate_team_record(games, team, season)
        
        result = TeamScheduleResponse(
            team=team,
            season=season,
            games=game_responses,
            statistics=stats
        )
        
        cache.set(cache_key, result, ttl=300)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying team schedule: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


# ============================================================================
# Story 12.3: Webhook Registration & Management
# ============================================================================

class WebhookRegistration(BaseModel):
    """Webhook registration request"""
    url: HttpUrl
    events: List[str] = Field(..., description="Events: game_started, score_changed, game_ended")
    secret: str = Field(..., min_length=16, description="HMAC secret (min 16 chars)")
    team: Optional[str] = Field(None, description="Team filter (optional)")
    sport: str = Field("nfl", pattern="^(nfl|nhl)$", description="Sport type")


@app.post("/api/v1/webhooks/register", tags=["Webhooks"], status_code=201)
async def register_webhook(registration: WebhookRegistration):
    """
    Register webhook for game events.
    
    Webhook will receive POST requests with:
    - JSON payload with event details
    - X-Webhook-Signature header (HMAC-SHA256)
    - X-Webhook-Event header
    - X-Webhook-Timestamp header
    
    Events:
    - game_started: When game goes live
    - score_changed: When score changes during live game
    - game_ended: When game becomes final
    """
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhooks not available")
    
    webhook_id = webhook_manager.register(
        url=str(registration.url),
        events=registration.events,
        secret=registration.secret,
        team=registration.team
    )
    
    return {
        "webhook_id": webhook_id,
        "url": str(registration.url),
        "events": registration.events,
        "team": registration.team,
        "message": "Webhook registered successfully"
    }


@app.get("/api/v1/webhooks/list", tags=["Webhooks"])
async def list_webhooks():
    """List all registered webhooks (secrets hidden)"""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhooks not available")
    
    return {"webhooks": webhook_manager.get_all()}


@app.delete("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"], status_code=204)
async def unregister_webhook(webhook_id: str):
    """Unregister a webhook"""
    if not webhook_manager:
        raise HTTPException(status_code=503, detail="Webhooks not available")
    
    success = webhook_manager.unregister(webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv('PORT', '8005')),
        log_level="info"
    )

