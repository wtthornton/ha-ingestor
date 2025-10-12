"""
Pydantic Data Models for Sports API
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================================================
# NFL Models
# ============================================================================

class NFLScore(BaseModel):
    """NFL game score model"""
    
    game_id: str = Field(..., description="Unique game identifier")
    date: datetime = Field(..., description="Game date and time")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    home_score: Optional[int] = Field(None, description="Home team score")
    away_score: Optional[int] = Field(None, description="Away team score")
    status: str = Field(..., description="Game status: scheduled, live, finished")
    quarter: Optional[str] = Field(None, description="Current quarter")
    time_remaining: Optional[str] = Field(None, description="Time remaining in quarter")
    season: int = Field(..., description="Season year")
    week: int = Field(..., description="Week number")
    
    # Optional enrichment fields
    home_conference: Optional[str] = Field(None, description="Home team conference (AFC/NFC)")
    away_conference: Optional[str] = Field(None, description="Away team conference")
    home_division: Optional[str] = Field(None, description="Home team division")
    away_division: Optional[str] = Field(None, description="Away team division")
    possession: Optional[str] = Field(None, description="Team with possession")
    down_distance: Optional[str] = Field(None, description="Down and distance (e.g., '3rd & 7')")
    field_position: Optional[str] = Field(None, description="Field position")
    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "12345",
                "date": "2025-10-11T18:00:00Z",
                "home_team": "Patriots",
                "away_team": "Chiefs",
                "home_score": 24,
                "away_score": 21,
                "status": "finished",
                "quarter": None,
                "time_remaining": None,
                "season": 2025,
                "week": 5
            }
        }


class NFLStanding(BaseModel):
    """NFL team standing model"""
    
    team: str = Field(..., description="Team name")
    conference: str = Field(..., description="Conference (AFC/NFC)")
    division: str = Field(..., description="Division (East/North/South/West)")
    wins: int = Field(..., ge=0, description="Number of wins")
    losses: int = Field(..., ge=0, description="Number of losses")
    ties: int = Field(0, ge=0, description="Number of ties")
    win_percentage: float = Field(..., ge=0.0, le=1.0, description="Win percentage")
    points_for: int = Field(0, ge=0, description="Total points scored")
    points_against: int = Field(0, ge=0, description="Total points allowed")
    season: int = Field(..., description="Season year")
    
    # Optional stats
    division_wins: Optional[int] = Field(None, ge=0, description="Division wins")
    conference_wins: Optional[int] = Field(None, ge=0, description="Conference wins")
    point_differential: Optional[int] = Field(None, description="Point differential")
    streak: Optional[str] = Field(None, description="Current streak (e.g., 'W3', 'L2')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "team": "Patriots",
                "conference": "AFC",
                "division": "East",
                "wins": 4,
                "losses": 1,
                "ties": 0,
                "win_percentage": 0.800,
                "points_for": 125,
                "points_against": 98,
                "season": 2025
            }
        }


class NFLPlayer(BaseModel):
    """NFL player model with statistics"""
    
    player_id: str = Field(..., description="Unique player identifier")
    name: str = Field(..., description="Player name")
    position: str = Field(..., description="Player position (QB, RB, WR, etc.)")
    team: str = Field(..., description="Team name")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Player statistics")
    
    # Optional fields
    number: Optional[int] = Field(None, description="Jersey number")
    age: Optional[int] = Field(None, description="Player age")
    height: Optional[str] = Field(None, description="Player height")
    weight: Optional[int] = Field(None, description="Player weight")
    
    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "abc123",
                "name": "Tom Brady",
                "position": "QB",
                "team": "Patriots",
                "stats": {
                    "passing_yards": 325,
                    "touchdowns": 3,
                    "interceptions": 1,
                    "qb_rating": 98.5
                }
            }
        }


class NFLInjury(BaseModel):
    """NFL injury report model"""
    
    player_id: str = Field(..., description="Unique player identifier")
    player_name: str = Field(..., description="Player name")
    team: str = Field(..., description="Team name")
    injury_type: str = Field(..., description="Type of injury (knee, ankle, etc.)")
    status: str = Field(..., description="Status: out, doubtful, questionable, probable")
    updated: datetime = Field(..., description="Last update timestamp")
    
    # Optional fields
    position: Optional[str] = Field(None, description="Player position")
    weeks_out: Optional[int] = Field(None, ge=0, description="Estimated weeks out")
    practice_participation: Optional[str] = Field(None, description="Practice participation level")
    season: Optional[int] = Field(None, description="Season year")
    
    class Config:
        json_schema_extra = {
            "example": {
                "player_id": "abc123",
                "player_name": "Tom Brady",
                "team": "Patriots",
                "injury_type": "knee",
                "status": "questionable",
                "updated": "2025-10-11T12:00:00Z"
            }
        }


class NFLFixture(BaseModel):
    """NFL fixture/game schedule model"""
    
    game_id: str = Field(..., description="Unique game identifier")
    date: datetime = Field(..., description="Scheduled date and time")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    season: int = Field(..., description="Season year")
    week: int = Field(..., description="Week number")
    venue: Optional[str] = Field(None, description="Venue name")
    city: Optional[str] = Field(None, description="City location")
    
    # Optional broadcast/TV info
    broadcast: Optional[str] = Field(None, description="TV network")
    status: str = Field("scheduled", description="Game status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "12345",
                "date": "2025-10-13T13:00:00Z",
                "home_team": "Patriots",
                "away_team": "Chiefs",
                "season": 2025,
                "week": 6,
                "venue": "Gillette Stadium",
                "city": "Foxborough"
            }
        }


# ============================================================================
# NHL Models
# ============================================================================

class NHLScore(BaseModel):
    """NHL game score model"""
    
    game_id: str = Field(..., description="Unique game identifier")
    date: datetime = Field(..., description="Game date and time")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    home_score: Optional[int] = Field(None, description="Home team score")
    away_score: Optional[int] = Field(None, description="Away team score")
    status: str = Field(..., description="Game status: scheduled, live, finished")
    period: Optional[str] = Field(None, description="Current period (1, 2, 3, OT, SO)")
    time_remaining: Optional[str] = Field(None, description="Time remaining in period")
    season: int = Field(..., description="Season year")
    
    # Hockey-specific fields
    home_shots: Optional[int] = Field(None, ge=0, description="Home team shots on goal")
    away_shots: Optional[int] = Field(None, ge=0, description="Away team shots on goal")
    home_power_play: Optional[bool] = Field(None, description="Home team on power play")
    away_power_play: Optional[bool] = Field(None, description="Away team on power play")
    
    # Optional enrichment fields
    home_conference: Optional[str] = Field(None, description="Home team conference")
    away_conference: Optional[str] = Field(None, description="Away team conference")
    home_division: Optional[str] = Field(None, description="Home team division")
    away_division: Optional[str] = Field(None, description="Away team division")
    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "67890",
                "date": "2025-10-11T19:00:00Z",
                "home_team": "Bruins",
                "away_team": "Canadiens",
                "home_score": 3,
                "away_score": 2,
                "status": "finished",
                "period": "3",
                "time_remaining": None,
                "season": 2025,
                "home_shots": 28,
                "away_shots": 22
            }
        }


class NHLStanding(BaseModel):
    """NHL team standing model"""
    
    team: str = Field(..., description="Team name")
    conference: str = Field(..., description="Conference (Eastern/Western)")
    division: str = Field(..., description="Division")
    wins: int = Field(..., ge=0, description="Number of wins")
    losses: int = Field(..., ge=0, description="Number of losses")
    overtime_losses: int = Field(0, ge=0, description="Overtime/Shootout losses")
    points: int = Field(..., ge=0, description="Total points")
    games_played: int = Field(..., ge=0, description="Games played")
    season: int = Field(..., description="Season year")
    
    # Optional stats
    goals_for: Optional[int] = Field(None, ge=0, description="Goals scored")
    goals_against: Optional[int] = Field(None, ge=0, description="Goals allowed")
    goal_differential: Optional[int] = Field(None, description="Goal differential")
    
    class Config:
        json_schema_extra = {
            "example": {
                "team": "Bruins",
                "conference": "Eastern",
                "division": "Atlantic",
                "wins": 8,
                "losses": 2,
                "overtime_losses": 1,
                "points": 17,
                "games_played": 11,
                "season": 2025
            }
        }


class NHLFixture(BaseModel):
    """NHL fixture/game schedule model"""
    
    game_id: str = Field(..., description="Unique game identifier")
    date: datetime = Field(..., description="Scheduled date and time")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    season: int = Field(..., description="Season year")
    venue: Optional[str] = Field(None, description="Venue name")
    city: Optional[str] = Field(None, description="City location")
    status: str = Field("scheduled", description="Game status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "67890",
                "date": "2025-10-13T19:00:00Z",
                "home_team": "Bruins",
                "away_team": "Canadiens",
                "season": 2025,
                "venue": "TD Garden",
                "city": "Boston"
            }
        }

