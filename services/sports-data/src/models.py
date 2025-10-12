"""
Data models for Sports Data Service

Pydantic models for API responses and internal data structures.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any
from datetime import datetime


class Team(BaseModel):
    """Team information"""
    id: str = Field(..., description="Team ID (e.g., 'sf', 'dal')")
    name: str = Field(..., description="Full team name")
    abbreviation: str = Field(..., description="Team abbreviation")
    logo: str = Field(default="", description="Team logo URL")
    colors: Dict[str, str] = Field(
        default_factory=dict, 
        description="Team colors (primary, secondary)"
    )
    record: Optional[Dict[str, int]] = Field(
        None, 
        description="Team record (wins, losses, ties)"
    )


class Period(BaseModel):
    """Period/Quarter information"""
    current: int
    total: int
    time_remaining: Optional[str] = None


class Game(BaseModel):
    """Game information"""
    model_config = {'arbitrary_types_allowed': True}
    
    id: str = Field(..., description="Unique game ID")
    league: Literal['NFL', 'NHL'] = Field(..., description="League")
    status: Literal['scheduled', 'live', 'final'] = Field(
        ..., 
        description="Game status"
    )
    start_time: str = Field(..., description="Game start time (ISO format)")
    home_team: Team = Field(..., description="Home team")
    away_team: Team = Field(..., description="Away team")
    score: Dict[str, int] = Field(
        ..., 
        description="Current score (home, away)"
    )
    period: Period = Field(
        ..., 
        description="Period info (current, total, time_remaining)"
    )
    is_favorite: bool = Field(
        default=False, 
        description="User favorite indicator"
    )


class GameStats(BaseModel):
    """Game statistics"""
    game_id: str
    stats: Dict[str, Dict[str, int]] = Field(
        ..., 
        description="Statistics by category"
    )


class TeamList(BaseModel):
    """List of teams"""
    league: str
    teams: list[Team]
    count: int


class GameList(BaseModel):
    """List of games"""
    games: list[Game]
    count: int
    filtered_by_teams: list[str] = Field(default_factory=list)


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: str
    cache_status: bool
    api_status: bool


class UserTeams(BaseModel):
    """User's selected teams"""
    user_id: str = "default"
    nfl_teams: list[str] = Field(default_factory=list)
    nhl_teams: list[str] = Field(default_factory=list)
    

class APIUsageStats(BaseModel):
    """API usage statistics"""
    total_calls_today: int
    nfl_calls: int
    nhl_calls: int
    cache_hits: int
    cache_misses: int
    estimated_daily_calls: int
    within_free_tier: bool = True

