"""
InfluxDB Schema Definitions for Sports Data

Defines measurement structures for NFL and NHL game data storage.
Story 12.1 - InfluxDB Persistence Layer
"""

from typing import Dict, Any, Optional
from datetime import datetime
from influxdb_client_3 import Point, WritePrecision


class SportsDataSchema:
    """
    Schema definitions for sports data measurements in InfluxDB.
    
    Measurements:
    - nfl_scores: NFL game data
    - nhl_scores: NHL game data
    
    Both measurements use tags for filtering and fields for measurements,
    following InfluxDB best practices.
    """
    
    # Measurement names
    NFL_MEASUREMENT = "nfl_scores"
    NHL_MEASUREMENT = "nhl_scores"
    
    @staticmethod
    def create_nfl_point(game_data: Dict[str, Any], timestamp: Optional[datetime] = None) -> Point:
        """
        Create an InfluxDB Point for NFL game data.
        
        Args:
            game_data: Game data dictionary from ESPN API
            timestamp: Optional timestamp (defaults to game start time or now)
            
        Returns:
            InfluxDB Point object ready for writing
            
        Tags (indexed for filtering):
        - game_id: Unique identifier
        - season: "2025"
        - week: "5" or "wild_card"
        - home_team: "Patriots"
        - away_team: "Chiefs"
        - status: "scheduled" | "live" | "finished"
        - home_conference: "AFC" | "NFC"
        - away_conference: "AFC" | "NFC"
        - home_division: "East", "West", "North", "South"
        - away_division: "East", "West", "North", "South"
        
        Fields (measurements):
        - home_score: Integer
        - away_score: Integer
        - quarter: String ("1", "2", "3", "4", "OT")
        - time_remaining: String ("14:32")
        """
        # Use provided timestamp or game start time or now
        point_time = timestamp or game_data.get('start_time') or datetime.utcnow()
        if isinstance(point_time, str):
            point_time = datetime.fromisoformat(point_time.replace('Z', '+00:00'))
        
        # Create point
        point = Point(SportsDataSchema.NFL_MEASUREMENT)
        
        # Add tags (indexed for filtering)
        point.tag("game_id", str(game_data.get('id', 'unknown')))
        point.tag("season", str(game_data.get('season', '2025')))
        point.tag("week", str(game_data.get('week', 'unknown')))
        point.tag("home_team", str(game_data.get('home_team', 'unknown')))
        point.tag("away_team", str(game_data.get('away_team', 'unknown')))
        point.tag("status", str(game_data.get('status', 'unknown')))
        
        # Add conference and division tags if available
        if 'home_conference' in game_data:
            point.tag("home_conference", str(game_data['home_conference']))
        if 'away_conference' in game_data:
            point.tag("away_conference", str(game_data['away_conference']))
        if 'home_division' in game_data:
            point.tag("home_division", str(game_data['home_division']))
        if 'away_division' in game_data:
            point.tag("away_division", str(game_data['away_division']))
        
        # Add fields (measurements)
        point.field("home_score", int(game_data.get('home_score', 0)))
        point.field("away_score", int(game_data.get('away_score', 0)))
        point.field("quarter", str(game_data.get('quarter', 'unknown')))
        point.field("time_remaining", str(game_data.get('time_remaining', '')))
        
        # Add venue if available
        if 'venue' in game_data:
            point.field("venue", str(game_data['venue']))
        
        # Set timestamp
        point.time(point_time, WritePrecision.S)
        
        return point
    
    @staticmethod
    def create_nhl_point(game_data: Dict[str, Any], timestamp: Optional[datetime] = None) -> Point:
        """
        Create an InfluxDB Point for NHL game data.
        
        Args:
            game_data: Game data dictionary from ESPN API
            timestamp: Optional timestamp (defaults to game start time or now)
            
        Returns:
            InfluxDB Point object ready for writing
            
        Tags (indexed for filtering):
        - game_id: Unique identifier
        - season: "2024-2025"
        - home_team: "Bruins"
        - away_team: "Capitals"
        - status: "scheduled" | "live" | "finished"
        - home_conference: "Eastern" | "Western"
        - away_conference: "Eastern" | "Western"
        - home_division: "Atlantic", "Metropolitan", "Central", "Pacific"
        - away_division: "Atlantic", "Metropolitan", "Central", "Pacific"
        
        Fields (measurements):
        - home_score: Integer
        - away_score: Integer
        - period: String ("1", "2", "3", "OT", "SO")
        - time_remaining: String ("14:32")
        """
        # Use provided timestamp or game start time or now
        point_time = timestamp or game_data.get('start_time') or datetime.utcnow()
        if isinstance(point_time, str):
            point_time = datetime.fromisoformat(point_time.replace('Z', '+00:00'))
        
        # Create point
        point = Point(SportsDataSchema.NHL_MEASUREMENT)
        
        # Add tags (indexed for filtering)
        point.tag("game_id", str(game_data.get('id', 'unknown')))
        point.tag("season", str(game_data.get('season', '2024-2025')))
        point.tag("home_team", str(game_data.get('home_team', 'unknown')))
        point.tag("away_team", str(game_data.get('away_team', 'unknown')))
        point.tag("status", str(game_data.get('status', 'unknown')))
        
        # Add conference and division tags if available
        if 'home_conference' in game_data:
            point.tag("home_conference", str(game_data['home_conference']))
        if 'away_conference' in game_data:
            point.tag("away_conference", str(game_data['away_conference']))
        if 'home_division' in game_data:
            point.tag("home_division", str(game_data['home_division']))
        if 'away_division' in game_data:
            point.tag("away_division", str(game_data['away_division']))
        
        # Add fields (measurements)
        point.field("home_score", int(game_data.get('home_score', 0)))
        point.field("away_score", int(game_data.get('away_score', 0)))
        point.field("period", str(game_data.get('period', 'unknown')))
        point.field("time_remaining", str(game_data.get('time_remaining', '')))
        
        # Add venue if available
        if 'venue' in game_data:
            point.field("venue", str(game_data['venue']))
        
        # Set timestamp
        point.time(point_time, WritePrecision.S)
        
        return point
    
    @staticmethod
    def create_point(game_data: Dict[str, Any], sport: str, timestamp: Optional[datetime] = None) -> Point:
        """
        Create an InfluxDB Point for game data based on sport type.
        
        Args:
            game_data: Game data dictionary
            sport: Sport type ('nfl' or 'nhl')
            timestamp: Optional timestamp
            
        Returns:
            InfluxDB Point object
            
        Raises:
            ValueError: If sport type is not supported
        """
        sport_lower = sport.lower()
        
        if sport_lower == 'nfl':
            return SportsDataSchema.create_nfl_point(game_data, timestamp)
        elif sport_lower == 'nhl':
            return SportsDataSchema.create_nhl_point(game_data, timestamp)
        else:
            raise ValueError(f"Unsupported sport type: {sport}")

