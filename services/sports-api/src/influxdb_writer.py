"""
Sports Data InfluxDB Writer
High-performance batch writer following Context7 KB best practices
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

try:
    from influxdb_client_3 import InfluxDBClient3, Point, WriteOptions, InfluxDBError
    from influxdb_client_3 import write_client_options
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False
    Point = None
    InfluxDBClient3 = None
    WriteOptions = None
    InfluxDBError = Exception

try:
    from .influxdb_schema import (
        MEASUREMENT_NFL_SCORES,
        MEASUREMENT_NHL_SCORES,
        MEASUREMENT_NFL_PLAYER_STATS,
        MEASUREMENT_NFL_INJURIES,
        MEASUREMENT_NFL_STANDINGS,
        MEASUREMENT_NHL_STANDINGS
    )
except ImportError:
    from influxdb_schema import (
        MEASUREMENT_NFL_SCORES,
        MEASUREMENT_NHL_SCORES,
        MEASUREMENT_NFL_PLAYER_STATS,
        MEASUREMENT_NFL_INJURIES,
        MEASUREMENT_NFL_STANDINGS,
        MEASUREMENT_NHL_STANDINGS
    )

logger = logging.getLogger(__name__)


class BatchingCallback:
    """
    Callback handler for batch write operations.
    
    Tracks success, error, and retry events for monitoring.
    """
    
    def __init__(self):
        self.write_count = 0
        self.error_count = 0
        self.retry_count = 0
    
    def success(self, conf, data: str):
        """Handle successful batch write"""
        self.write_count += 1
        logger.debug(f"Batch written successfully: {conf}")
    
    def error(self, conf, data: str, exception: Exception):
        """Handle batch write error"""
        self.error_count += 1
        logger.error(
            f"Batch write failed: {conf}",
            extra={"error": str(exception), "data_sample": data[:200] if data else ""}
        )
    
    def retry(self, conf, data: str, exception: Exception):
        """Handle batch write retry"""
        self.retry_count += 1
        logger.warning(
            f"Retrying batch write: {conf}",
            extra={"error": str(exception)}
        )


class SportsInfluxDBWriter:
    """
    High-performance batch writer for sports data.
    
    Implements Context7 KB best practices:
    - Batch writing (100 points)
    - 10-second flush interval
    - Exponential backoff retry
    - Success/error/retry callbacks
    """
    
    def __init__(
        self,
        host: str,
        token: str,
        database: str,
        org: str,
        batch_size: int = 100,
        flush_interval: int = 10_000,  # milliseconds
        max_retries: int = 5
    ):
        """
        Initialize InfluxDB writer.
        
        Args:
            host: InfluxDB host URL
            token: Authentication token
            database: Database name
            org: Organization name
            batch_size: Points per batch (default: 100)
            flush_interval: Milliseconds between flushes (default: 10000)
            max_retries: Maximum retry attempts (default: 5)
        """
        if not INFLUXDB_AVAILABLE:
            raise ImportError("influxdb-client-3 not available")
        
        self.host = host
        self.token = token
        self.database = database
        self.org = org
        
        # Batch configuration
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        
        # Statistics
        self.total_points_written = 0
        self.total_batches_written = 0
        self.total_points_failed = 0
        self.write_times: deque = deque(maxlen=100)
        
        # Callbacks for monitoring
        self.callback = BatchingCallback()
        
        # Write options (Context7 KB pattern)
        self.write_options = WriteOptions(
            batch_size=batch_size,
            flush_interval=flush_interval,
            jitter_interval=2_000,
            retry_interval=5_000,
            max_retries=max_retries,
            max_retry_delay=30_000,
            exponential_base=2
        )
        
        # Client (initialized in start())
        self.client: Optional[InfluxDBClient3] = None
    
    async def start(self):
        """Initialize InfluxDB client"""
        try:
            wco = write_client_options(
                success_callback=self.callback.success,
                error_callback=self.callback.error,
                retry_callback=self.callback.retry,
                write_options=self.write_options
            )
            
            self.client = InfluxDBClient3(
                host=self.host,
                token=self.token,
                database=self.database,
                org=self.org,
                write_client_options=wco
            )
            
            logger.info(
                "InfluxDB writer initialized",
                extra={
                    "host": self.host,
                    "database": self.database,
                    "batch_size": self.batch_size,
                    "flush_interval_ms": self.flush_interval
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB client: {e}")
            raise
    
    async def stop(self):
        """Close InfluxDB client"""
        if self.client:
            try:
                # Flush remaining points
                await asyncio.sleep(0.1)
                self.client.close()
                logger.info(
                    "InfluxDB writer stopped",
                    extra={
                        "points_written": self.total_points_written,
                        "batches_written": self.total_batches_written
                    }
                )
            except Exception as e:
                logger.error(f"Error stopping InfluxDB writer: {e}")
    
    async def write_nfl_score(self, score: Dict[str, Any]) -> bool:
        """
        Write NFL score to InfluxDB.
        
        Args:
            score: NFL score data dictionary
            
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.client:
            logger.error("InfluxDB client not initialized")
            return False
        
        try:
            point = Point(MEASUREMENT_NFL_SCORES) \
                .tag("game_id", str(score['game_id'])) \
                .tag("season", str(score['season'])) \
                .tag("week", str(score['week'])) \
                .tag("home_team", score['home_team']) \
                .tag("away_team", score['away_team']) \
                .tag("status", score['status'])
            
            # Optional tags
            if score.get('home_conference'):
                point.tag("home_conference", score['home_conference'])
            if score.get('away_conference'):
                point.tag("away_conference", score['away_conference'])
            if score.get('home_division'):
                point.tag("home_division", score['home_division'])
            if score.get('away_division'):
                point.tag("away_division", score['away_division'])
            
            # Fields
            if score.get('home_score') is not None:
                point.field("home_score", int(score['home_score']))
            if score.get('away_score') is not None:
                point.field("away_score", int(score['away_score']))
            if score.get('quarter'):
                point.field("quarter", str(score['quarter']))
            if score.get('time_remaining'):
                point.field("time_remaining", str(score['time_remaining']))
            if score.get('possession'):
                point.field("possession", str(score['possession']))
            
            # Set timestamp
            if score.get('date'):
                if isinstance(score['date'], str):
                    from dateutil.parser import parse
                    point.time(parse(score['date']))
                else:
                    point.time(score['date'])
            else:
                point.time(datetime.now())
            
            # Write to InfluxDB
            self.client.write(point)
            self.total_points_written += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing NFL score: {e}", extra={"score": score})
            self.total_points_failed += 1
            return False
    
    async def write_nhl_score(self, score: Dict[str, Any]) -> bool:
        """
        Write NHL score to InfluxDB.
        
        Args:
            score: NHL score data dictionary
            
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.client:
            logger.error("InfluxDB client not initialized")
            return False
        
        try:
            point = Point(MEASUREMENT_NHL_SCORES) \
                .tag("game_id", str(score['game_id'])) \
                .tag("season", str(score['season'])) \
                .tag("home_team", score['home_team']) \
                .tag("away_team", score['away_team']) \
                .tag("status", score['status'])
            
            # Optional tags
            if score.get('home_conference'):
                point.tag("home_conference", score['home_conference'])
            if score.get('away_conference'):
                point.tag("away_conference", score['away_conference'])
            if score.get('home_division'):
                point.tag("home_division", score['home_division'])
            if score.get('away_division'):
                point.tag("away_division", score['away_division'])
            
            # Fields
            if score.get('home_score') is not None:
                point.field("home_score", int(score['home_score']))
            if score.get('away_score') is not None:
                point.field("away_score", int(score['away_score']))
            if score.get('period'):
                point.field("period", str(score['period']))
            if score.get('time_remaining'):
                point.field("time_remaining", str(score['time_remaining']))
            if score.get('home_shots') is not None:
                point.field("home_shots", int(score['home_shots']))
            if score.get('away_shots') is not None:
                point.field("away_shots", int(score['away_shots']))
            
            # Set timestamp
            if score.get('date'):
                if isinstance(score['date'], str):
                    from dateutil.parser import parse
                    point.time(parse(score['date']))
                else:
                    point.time(score['date'])
            else:
                point.time(datetime.now())
            
            # Write to InfluxDB
            self.client.write(point)
            self.total_points_written += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing NHL score: {e}", extra={"score": score})
            self.total_points_failed += 1
            return False
    
    async def write_player_stats(
        self, 
        stats: Dict[str, Any],
        sport: str = "nfl"
    ) -> bool:
        """
        Write player statistics to InfluxDB.
        
        Args:
            stats: Player statistics dictionary
            sport: Sport type (nfl, nhl)
            
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.client:
            logger.error("InfluxDB client not initialized")
            return False
        
        try:
            measurement = f"{sport}_player_stats"
            
            point = Point(measurement) \
                .tag("player_id", str(stats['player_id'])) \
                .tag("player_name", stats['player_name']) \
                .tag("team", stats['team']) \
                .tag("position", stats['position']) \
                .tag("season", str(stats['season']))
            
            # Optional tags
            if stats.get('game_id'):
                point.tag("game_id", str(stats['game_id']))
            if stats.get('week'):
                point.tag("week", str(stats['week']))
            
            # Add stat fields dynamically
            for key, value in stats.get('stats', {}).items():
                if isinstance(value, (int, float)):
                    point.field(key, value)
                elif isinstance(value, str):
                    point.field(key, value)
            
            # Set timestamp
            if stats.get('date'):
                if isinstance(stats['date'], str):
                    from dateutil.parser import parse
                    point.time(parse(stats['date']))
                else:
                    point.time(stats['date'])
            else:
                point.time(datetime.now())
            
            # Write to InfluxDB
            self.client.write(point)
            self.total_points_written += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing player stats: {e}", extra={"stats": stats})
            self.total_points_failed += 1
            return False
    
    async def write_injury_report(self, injury: Dict[str, Any]) -> bool:
        """
        Write injury report to InfluxDB.
        
        Args:
            injury: Injury report dictionary
            
        Returns:
            True if write succeeded, False otherwise
        """
        if not self.client:
            logger.error("InfluxDB client not initialized")
            return False
        
        try:
            point = Point(MEASUREMENT_NFL_INJURIES) \
                .tag("player_id", str(injury['player_id'])) \
                .tag("player_name", injury['player_name']) \
                .tag("team", injury['team']) \
                .tag("status", injury['status']) \
                .tag("injury_type", injury.get('injury_type', 'unknown'))
            
            # Optional tags
            if injury.get('position'):
                point.tag("position", injury['position'])
            if injury.get('season'):
                point.tag("season", str(injury['season']))
            
            # Fields
            if injury.get('weeks_out') is not None:
                point.field("weeks_out", int(injury['weeks_out']))
            if injury.get('practice_participation'):
                point.field("practice_participation", str(injury['practice_participation']))
            
            # Set timestamp
            if injury.get('updated'):
                if isinstance(injury['updated'], str):
                    from dateutil.parser import parse
                    point.time(parse(injury['updated']))
                else:
                    point.time(injury['updated'])
            else:
                point.time(datetime.now())
            
            # Write to InfluxDB
            self.client.write(point)
            self.total_points_written += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing injury report: {e}", extra={"injury": injury})
            self.total_points_failed += 1
            return False
    
    async def write_standings(
        self, 
        standings: List[Dict[str, Any]],
        sport: str = "nfl"
    ) -> int:
        """
        Write standings to InfluxDB (batch).
        
        Args:
            standings: List of standing dictionaries
            sport: Sport type (nfl, nhl)
            
        Returns:
            Number of successful writes
        """
        if not self.client:
            logger.error("InfluxDB client not initialized")
            return 0
        
        successful = 0
        measurement = f"{sport}_standings"
        
        for standing in standings:
            try:
                point = Point(measurement) \
                    .tag("team", standing['team']) \
                    .tag("season", str(standing['season']))
                
                # Optional tags
                if standing.get('conference'):
                    point.tag("conference", standing['conference'])
                if standing.get('division'):
                    point.tag("division", standing['division'])
                
                # Fields
                point.field("wins", int(standing['wins']))
                point.field("losses", int(standing['losses']))
                
                if sport == "nfl":
                    point.field("ties", int(standing.get('ties', 0)))
                    point.field("win_percentage", float(standing['win_percentage']))
                    if standing.get('points_for') is not None:
                        point.field("points_for", int(standing['points_for']))
                    if standing.get('points_against') is not None:
                        point.field("points_against", int(standing['points_against']))
                elif sport == "nhl":
                    point.field("overtime_losses", int(standing.get('overtime_losses', 0)))
                    point.field("points", int(standing['points']))
                    point.field("games_played", int(standing['games_played']))
                
                # Set timestamp
                point.time(datetime.now())
                
                # Write to InfluxDB
                self.client.write(point)
                successful += 1
                
            except Exception as e:
                logger.error(f"Error writing standing for {standing.get('team')}: {e}")
                self.total_points_failed += 1
        
        self.total_points_written += successful
        logger.info(
            f"Wrote {successful}/{len(standings)} {sport.upper()} standings",
            extra={"sport": sport, "successful": successful, "total": len(standings)}
        )
        
        return successful
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get writer statistics.
        
        Returns:
            Dictionary with write statistics
        """
        total_attempts = self.total_points_written + self.total_points_failed
        
        return {
            "total_points_written": self.total_points_written,
            "total_batches_written": self.callback.write_count,
            "total_points_failed": self.total_points_failed,
            "total_errors": self.callback.error_count,
            "total_retries": self.callback.retry_count,
            "success_rate": (
                self.total_points_written / total_attempts
                if total_attempts > 0 else 1.0
            ),
            "avg_write_time_ms": (
                sum(self.write_times) / len(self.write_times)
                if self.write_times else 0.0
            )
        }

