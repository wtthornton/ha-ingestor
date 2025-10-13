"""
Sports Data Endpoints for Data API
Epic 12 Story 12.2: Historical Sports Data Queries
Epic 13 Story 13.4: Integration into data-api service
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from shared.influxdb_query_client import InfluxDBQueryClient

logger = logging.getLogger(__name__)


# Response Models
class GameResponse(BaseModel):
    """Game response model"""
    game_id: str
    league: str  # NFL or NHL
    season: int
    week: Optional[str] = None  # For NFL
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    status: str  # scheduled, live, finished
    quarter_period: Optional[str] = None  # Quarter (NFL) or Period (NHL)
    time_remaining: Optional[str] = None
    timestamp: str


class GameListResponse(BaseModel):
    """Game list response"""
    games: List[GameResponse]
    count: int
    team: Optional[str] = None
    season: Optional[int] = None


class TeamScheduleResponse(BaseModel):
    """Team schedule response"""
    team: str
    season: int
    games: List[GameResponse]
    total_games: int
    wins: int
    losses: int
    ties: int
    win_percentage: float


class ScoreTimelinePoint(BaseModel):
    """Score timeline point"""
    timestamp: str
    home_score: int
    away_score: int
    quarter_period: str
    time_remaining: str


class ScoreTimelineResponse(BaseModel):
    """Score timeline response"""
    game_id: str
    home_team: str
    away_team: str
    timeline: List[ScoreTimelinePoint]
    final_score: str


# Create router
router = APIRouter(tags=["Sports Data"])

# InfluxDB client (shared instance)
influxdb_client = InfluxDBQueryClient()


@router.get("/sports/games/history", response_model=GameListResponse)
async def get_game_history(
    team: str = Query(..., description="Team name or abbreviation"),
    season: Optional[int] = Query(None, description="Season year (default: current)"),
    league: Optional[str] = Query(None, description="NFL or NHL"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of games")
):
    """
    Get historical games for a team
    
    Epic 12 Story 12.2: Query sports data from InfluxDB
    
    Args:
        team: Team name (e.g., "Patriots", "Bruins")
        season: Season year (e.g., 2025)
        league: Filter by league (NFL or NHL)
        status_filter: Filter by game status (scheduled, live, finished)
        limit: Maximum results
        
    Returns:
        List of games with scores and details
    """
    try:
        # Build query
        current_year = datetime.now().year
        season = season or current_year
        
        # Determine measurement based on league
        measurements = []
        if league:
            measurements.append(f"{league.lower()}_scores")
        else:
            measurements.extend(["nfl_scores", "nhl_scores"])
        
        all_games = []
        
        for measurement in measurements:
            query = f'''
                from(bucket: "sports_data")
                    |> range(start: {season}-01-01T00:00:00Z, stop: {season+1}-01-01T00:00:00Z)
                    |> filter(fn: (r) => r._measurement == "{measurement}")
                    |> filter(fn: (r) => r.home_team == "{team}" or r.away_team == "{team}")
            '''
            
            if status_filter:
                query += f'|> filter(fn: (r) => r.status == "{status_filter}")'
            
            query += '|> sort(columns: ["_time"], desc: true)'
            query += f'|> limit(n: {limit})'
            
            try:
                results = await influxdb_client._execute_query(query)
                
                for record in results:
                    game = GameResponse(
                        game_id=record.get("game_id", ""),
                        league=measurement.split('_')[0].upper(),
                        season=int(record.get("season", season)),
                        week=record.get("week"),
                        home_team=record.get("home_team", ""),
                        away_team=record.get("away_team", ""),
                        home_score=record.get("home_score"),
                        away_score=record.get("away_score"),
                        status=record.get("status", "unknown"),
                        quarter_period=record.get("quarter") or record.get("period"),
                        time_remaining=record.get("time_remaining"),
                        timestamp=record.get("_time", datetime.now().isoformat())
                    )
                    all_games.append(game)
            
            except Exception as e:
                logger.warning(f"Error querying {measurement}: {e}")
        
        return GameListResponse(
            games=all_games,
            count=len(all_games),
            team=team,
            season=season
        )
    
    except Exception as e:
        logger.error(f"Error getting game history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game history: {str(e)}"
        )


@router.get("/sports/games/timeline/{game_id}", response_model=ScoreTimelineResponse)
async def get_game_timeline(
    game_id: str,
    league: Optional[str] = Query(None, description="NFL or NHL")
):
    """
    Get score progression timeline for a specific game
    
    Shows how the score changed throughout the game (useful for comeback visualizations)
    
    Args:
        game_id: Unique game identifier
        league: NFL or NHL (optional, will search both if not specified)
        
    Returns:
        Score timeline with timestamps
    """
    try:
        measurements = []
        if league:
            measurements.append(f"{league.lower()}_scores")
        else:
            measurements.extend(["nfl_scores", "nhl_scores"])
        
        for measurement in measurements:
            query = f'''
                from(bucket: "sports_data")
                    |> range(start: -7d)
                    |> filter(fn: (r) => r._measurement == "{measurement}")
                    |> filter(fn: (r) => r.game_id == "{game_id}")
                    |> sort(columns: ["_time"])
            '''
            
            try:
                results = await influxdb_client._execute_query(query)
                
                if not results:
                    continue
                
                # Build timeline
                timeline = []
                for record in results:
                    point = ScoreTimelinePoint(
                        timestamp=record.get("_time", ""),
                        home_score=record.get("home_score", 0),
                        away_score=record.get("away_score", 0),
                        quarter_period=record.get("quarter") or record.get("period", ""),
                        time_remaining=record.get("time_remaining", "")
                    )
                    timeline.append(point)
                
                if timeline:
                    first_record = results[0]
                    final_record = results[-1]
                    
                    return ScoreTimelineResponse(
                        game_id=game_id,
                        home_team=first_record.get("home_team", ""),
                        away_team=first_record.get("away_team", ""),
                        timeline=timeline,
                        final_score=f"{final_record.get('home_score', 0)}-{final_record.get('away_score', 0)}"
                    )
            
            except Exception as e:
                logger.warning(f"Error querying {measurement} for game {game_id}: {e}")
        
        # Game not found in any measurement
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Game {game_id} not found"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game timeline: {str(e)}"
        )


@router.get("/sports/schedule/{team}", response_model=TeamScheduleResponse)
async def get_team_schedule(
    team: str,
    season: Optional[int] = Query(None, description="Season year (default: current)"),
    league: Optional[str] = Query(None, description="NFL or NHL")
):
    """
    Get complete season schedule for a team with win/loss record
    
    Args:
        team: Team name
        season: Season year (default: current year)
        league: NFL or NHL
        
    Returns:
        Full schedule with stats
    """
    try:
        current_year = datetime.now().year
        season = season or current_year
        
        # Get all games for team
        response = await get_game_history(team=team, season=season, league=league, limit=200)
        games = response.games
        
        # Calculate record
        wins = 0
        losses = 0
        ties = 0
        
        for game in games:
            if game.status == "finished" and game.home_score is not None and game.away_score is not None:
                if game.home_team == team:
                    if game.home_score > game.away_score:
                        wins += 1
                    elif game.home_score < game.away_score:
                        losses += 1
                    else:
                        ties += 1
                else:  # away team
                    if game.away_score > game.home_score:
                        wins += 1
                    elif game.away_score < game.home_score:
                        losses += 1
                    else:
                        ties += 1
        
        total_games_played = wins + losses + ties
        win_percentage = (wins / total_games_played) if total_games_played > 0 else 0.0
        
        return TeamScheduleResponse(
            team=team,
            season=season,
            games=games,
            total_games=len(games),
            wins=wins,
            losses=losses,
            ties=ties,
            win_percentage=round(win_percentage, 3)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting team schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team schedule: {str(e)}"
        )

