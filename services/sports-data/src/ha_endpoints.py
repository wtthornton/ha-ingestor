"""
Home Assistant Automation Endpoints

Fast endpoints for HA automation conditionals and context.
Story 12.3 - Adaptive Event Monitor + Webhooks
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Path, Query, HTTPException


logger = logging.getLogger(__name__)


# Response Models
class GameStatusResponse(BaseModel):
    """Simple game status for quick checks"""
    team: str
    status: str  # "playing", "upcoming", "none"
    game_id: Optional[str] = None
    opponent: Optional[str] = None
    start_time: Optional[str] = None


class GameContextResponse(BaseModel):
    """Full game context for automations"""
    team: str
    status: str
    current_game: Optional[Dict[str, Any]] = None
    next_game: Optional[Dict[str, Any]] = None


# Create router
router = APIRouter(prefix="/api/v1/ha", tags=["Home Assistant"])


@router.get("/game-status/{team}", response_model=GameStatusResponse)
async def get_game_status(
    team: str = Path(..., description="Team abbreviation (e.g., 'sf', 'ne')"),
    sport: str = Query("nfl", pattern="^(nfl|nhl)$", description="Sport type")
):
    """
    Quick game status check for HA automations.
    
    Optimized for <50ms response time.
    Returns: "playing", "upcoming", "none"
    """
    from src.main import cache
    
    # Check cache for live games (fast!)
    live_games = await cache.get(f"live_games_{sport}")
    if live_games:
        for game in live_games:
            home_abbr = game.get('home_team', {}).get('abbreviation', '').lower()
            away_abbr = game.get('away_team', {}).get('abbreviation', '').lower()
            
            if team.lower() in (home_abbr, away_abbr):
                opponent = away_abbr if home_abbr == team.lower() else home_abbr
                return GameStatusResponse(
                    team=team,
                    status="playing",
                    game_id=game.get('id'),
                    opponent=opponent,
                    start_time=game.get('start_time')
                )
    
    # Check upcoming games
    upcoming_games = await cache.get(f"upcoming_games_{sport}")
    if upcoming_games:
        for game in upcoming_games:
            home_abbr = game.get('home_team', {}).get('abbreviation', '').lower()
            away_abbr = game.get('away_team', {}).get('abbreviation', '').lower()
            
            if team.lower() in (home_abbr, away_abbr):
                # Check if within next 4 hours
                start_time = game.get('start_time')
                if start_time:
                    try:
                        game_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        hours_until = (game_time - datetime.utcnow()).total_seconds() / 3600
                        
                        if hours_until <= 4:
                            opponent = away_abbr if home_abbr == team.lower() else home_abbr
                            return GameStatusResponse(
                                team=team,
                                status="upcoming",
                                game_id=game.get('id'),
                                opponent=opponent,
                                start_time=start_time
                            )
                    except:
                        pass
    
    # No current or upcoming games
    return GameStatusResponse(team=team, status="none")


@router.get("/game-context/{team}", response_model=GameContextResponse)
async def get_game_context(
    team: str = Path(..., description="Team abbreviation"),
    sport: str = Query("nfl", pattern="^(nfl|nhl)$", description="Sport type")
):
    """
    Full game context for advanced automations.
    
    Includes current game, next game, and score details.
    """
    from src.main import cache
    
    current_game = None
    next_game = None
    
    # Get current game
    live_games = await cache.get(f"live_games_{sport}")
    if live_games:
        for game in live_games:
            home_abbr = game.get('home_team', {}).get('abbreviation', '').lower()
            away_abbr = game.get('away_team', {}).get('abbreviation', '').lower()
            
            if team.lower() in (home_abbr, away_abbr):
                current_game = game
                break
    
    # Get next game if not playing
    if not current_game:
        upcoming_games = await cache.get(f"upcoming_games_{sport}")
        if upcoming_games:
            team_games = [
                g for g in upcoming_games
                if team.lower() in (
                    g.get('home_team', {}).get('abbreviation', '').lower(),
                    g.get('away_team', {}).get('abbreviation', '').lower()
                )
            ]
            if team_games:
                # Get earliest upcoming game
                next_game = min(team_games, key=lambda g: g.get('start_time', 'Z'))
    
    status = "playing" if current_game else ("upcoming" if next_game else "none")
    
    return GameContextResponse(
        team=team,
        status=status,
        current_game=current_game,
        next_game=next_game
    )

