"""
Pydantic Models for Historical Sports Data

Models for historical query endpoints.
Story 12.2 - Historical Query Endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HistoricalGameResponse(BaseModel):
    """Historical game data"""
    game_id: str
    sport: str
    season: str
    week: Optional[str] = None
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str
    time: datetime
    quarter: Optional[str] = None
    period: Optional[str] = None


class TeamStatistics(BaseModel):
    """Team season statistics"""
    team: str
    season: str
    games_played: int
    wins: int
    losses: int
    ties: int = 0
    win_percentage: float
    points_for: int
    points_against: int
    point_differential: int


class GameTimelineResponse(BaseModel):
    """Score timeline for a game"""
    game_id: str
    home_team: str
    away_team: str
    timeline: List[Dict[str, Any]]
    final_score: Dict[str, int]
    duration_minutes: int


class TeamScheduleResponse(BaseModel):
    """Team season schedule with stats"""
    team: str
    season: str
    games: List[HistoricalGameResponse]
    statistics: TeamStatistics


class PaginatedGamesResponse(BaseModel):
    """Paginated game results"""
    games: List[HistoricalGameResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

