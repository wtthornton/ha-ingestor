"""
Simple InfluxDB Query Module for Sports Data

Query historical game data from InfluxDB.
Story 12.2 - Historical Query Endpoints
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from influxdb_client_3 import InfluxDBClient3
    INFLUXDB_AVAILABLE = True
except ImportError:
    InfluxDBClient3 = None
    INFLUXDB_AVAILABLE = False


logger = logging.getLogger(__name__)


class InfluxDBQuery:
    """Simple InfluxDB query client for historical sports data"""
    
    def __init__(self, url: str, token: str, database: str):
        """
        Initialize query client.
        
        Args:
            url: InfluxDB server URL
            token: Authentication token
            database: Database name
        """
        if not INFLUXDB_AVAILABLE:
            logger.warning("InfluxDB client not available")
            self.enabled = False
            return
        
        self.enabled = True
        
        try:
            host = url.replace('http://', '').replace('https://', '')
            self.client = InfluxDBClient3(token=token, host=host, database=database)
            logger.info(f"InfluxDB query client ready: {database}")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB query client: {e}")
            self.enabled = False
            self.client = None
    
    def query_games_history(
        self,
        sport: str,
        team: Optional[str] = None,
        season: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query historical games.
        
        Args:
            sport: 'nfl' or 'nhl'
            team: Team name filter
            season: Season filter (e.g., '2025')
            status: Status filter ('scheduled', 'live', 'finished')
            limit: Max results (default 1000)
            
        Returns:
            List of game dictionaries
        """
        if not self.enabled:
            return []
        
        # Build query
        measurement = "nfl_scores" if sport.lower() == "nfl" else "nhl_scores"
        where_clauses = []
        
        if season:
            where_clauses.append(f"season = '{season}'")
        if team:
            where_clauses.append(f"(home_team = '{team}' OR away_team = '{team}')")
        if status:
            where_clauses.append(f"status = '{status}'")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
        SELECT *
        FROM {measurement}
        WHERE {where_sql}
        ORDER BY time DESC
        LIMIT {limit}
        """
        
        try:
            # Execute query and convert to list of dicts
            reader = self.client.query(query=query, language="sql")
            table = reader.read_all()
            df = table.to_pandas()
            
            if df.empty:
                return []
            
            # Convert to list of dicts
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
    
    def query_game_timeline(self, game_id: str, sport: str) -> List[Dict[str, Any]]:
        """
        Get score progression for specific game.
        
        Args:
            game_id: Game identifier
            sport: 'nfl' or 'nhl'
            
        Returns:
            List of score updates (chronological)
        """
        if not self.enabled:
            return []
        
        measurement = "nfl_scores" if sport.lower() == "nfl" else "nhl_scores"
        
        query = f"""
        SELECT 
            time,
            home_score,
            away_score,
            quarter,
            time_remaining,
            status
        FROM {measurement}
        WHERE game_id = '{game_id}'
        ORDER BY time ASC
        """
        
        try:
            reader = self.client.query(query=query, language="sql")
            table = reader.read_all()
            df = table.to_pandas()
            
            if df.empty:
                return []
            
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Timeline query error: {e}")
            return []


def create_influxdb_query_from_env() -> Optional[InfluxDBQuery]:
    """Create InfluxDB query client from environment variables"""
    import os
    
    if not INFLUXDB_AVAILABLE:
        logger.warning("InfluxDB client not available")
        return None
    
    url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
    token = os.getenv('INFLUXDB_TOKEN')
    database = os.getenv('INFLUXDB_DATABASE', 'sports_data')
    
    if not token:
        logger.error("INFLUXDB_TOKEN not set")
        return None
    
    try:
        query_client = InfluxDBQuery(url, token, database)
        return query_client if query_client.enabled else None
    except Exception as e:
        logger.error(f"Failed to create InfluxDB query client: {e}")
        return None

