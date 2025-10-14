"""
Simple InfluxDB Writer for Sports Data

Writes game data to InfluxDB with basic error handling and circuit breaker.
Story 12.1 - InfluxDB Persistence Layer
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from influxdb_client_3 import InfluxDBClient3
    INFLUXDB_AVAILABLE = True
except ImportError:
    InfluxDBClient3 = None
    INFLUXDB_AVAILABLE = False

from src.influxdb_schema import SportsDataSchema


logger = logging.getLogger(__name__)


class InfluxDBWriter:
    """
    Simple InfluxDB writer for sports data.
    
    - Writes game data to InfluxDB
    - Uses circuit breaker to prevent cascading failures
    - Tracks basic statistics
    """
    
    def __init__(self, url: str, token: str, database: str, circuit_breaker=None):
        """
        Initialize InfluxDB writer.
        
        Args:
            url: InfluxDB server URL
            token: Authentication token  
            database: Database name
            circuit_breaker: Optional circuit breaker instance
        """
        if not INFLUXDB_AVAILABLE:
            logger.warning("InfluxDB client not available")
            self.enabled = False
            return
        
        self.circuit_breaker = circuit_breaker
        self.enabled = True
        self.writes_success = 0
        self.writes_failed = 0
        self.last_error = None
        
        # Initialize client
        try:
            host = url.replace('http://', '').replace('https://', '')
            self.client = InfluxDBClient3(token=token, host=host, database=database)
            logger.info(f"InfluxDB writer ready: {database}")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            self.enabled = False
            self.client = None
    
    async def write_games(self, games: List[Dict[str, Any]], sport: str) -> bool:
        """
        Write games to InfluxDB.
        
        Args:
            games: List of game data
            sport: 'nfl' or 'nhl'
            
        Returns:
            True if successful
        """
        if not self.enabled or not games:
            return False
        
        # Check circuit breaker
        if self.circuit_breaker and self.circuit_breaker.is_open():
            return False
        
        try:
            # Create points
            points = [SportsDataSchema.create_point(g, sport) for g in games]
            
            # Write to InfluxDB
            self.client.write(points)
            
            # Update stats
            self.writes_success += len(points)
            if self.circuit_breaker:
                self.circuit_breaker.record_success()
            
            logger.debug(f"Wrote {len(points)} {sport} games to InfluxDB")
            return True
            
        except Exception as e:
            self.writes_failed += 1
            self.last_error = str(e)
            logger.error(f"InfluxDB write failed: {e}")
            
            if self.circuit_breaker:
                self.circuit_breaker.record_failure()
            
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get writer statistics"""
        return {
            'enabled': self.enabled,
            'writes_success': self.writes_success,
            'writes_failed': self.writes_failed,
            'last_error': self.last_error,
            'circuit_breaker': self.circuit_breaker.get_status() if self.circuit_breaker else 'none'
        }


def create_influxdb_writer_from_env(circuit_breaker=None) -> Optional[InfluxDBWriter]:
    """Create InfluxDB writer from environment variables"""
    if os.getenv('INFLUXDB_ENABLED', 'true').lower() != 'true':
        logger.info("InfluxDB disabled")
        return None
    
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
        writer = InfluxDBWriter(url, token, database, circuit_breaker)
        return writer if writer.enabled else None
    except Exception as e:
        logger.error(f"Failed to create InfluxDB writer: {e}")
        return None

