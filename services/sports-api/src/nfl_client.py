"""
NFL API Client for API-SPORTS
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from .api_client import APISportsClient
    from .models import NFLScore, NFLStanding, NFLPlayer, NFLInjury, NFLFixture
except ImportError:
    from api_client import APISportsClient
    from models import NFLScore, NFLStanding, NFLPlayer, NFLInjury, NFLFixture

logger = logging.getLogger(__name__)


class NFLClient(APISportsClient):
    """
    NFL-specific API client.
    
    Provides methods for fetching NFL scores, standings, fixtures,
    player statistics, and injury reports from API-SPORTS.
    """
    
    def __init__(self, api_key: str, rate_limiter=None):
        """
        Initialize NFL client.
        
        Args:
            api_key: API-SPORTS API key
            rate_limiter: Optional RateLimiter instance
        """
        super().__init__(api_key, "https://api-sports.io/nfl", rate_limiter)
        logger.info("NFL client initialized")
    
    async def get_scores(
        self, 
        date: Optional[str] = None
    ) -> List[NFLScore]:
        """
        Get NFL scores for a specific date or live scores.
        
        Args:
            date: Date in YYYY-MM-DD format, or None for live scores
            
        Returns:
            List of NFLScore objects
        """
        try:
            # Build parameters
            params = {'date': date} if date else {'live': 'all'}
            
            # Make API request
            data = await self._request('GET', '/scores', params=params)
            
            # Parse response
            scores = []
            for score_data in data.get('response', []):
                try:
                    score = NFLScore(**score_data)
                    scores.append(score)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse score data: {e}",
                        extra={"score_data": score_data}
                    )
            
            logger.info(
                f"Fetched {len(scores)} NFL scores",
                extra={
                    "date": date or "live",
                    "count": len(scores)
                }
            )
            
            return scores
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NFL scores: {e}",
                extra={"date": date}
            )
            return []  # Return empty list on error
    
    async def get_standings(
        self, 
        season: int
    ) -> List[NFLStanding]:
        """
        Get NFL standings for a season.
        
        Args:
            season: Season year (e.g., 2025)
            
        Returns:
            List of NFLStanding objects
        """
        try:
            # Make API request
            data = await self._request('GET', '/standings', params={'season': season})
            
            # Parse response
            standings = []
            for standing_data in data.get('response', []):
                try:
                    standing = NFLStanding(**standing_data)
                    standings.append(standing)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse standing data: {e}",
                        extra={"standing_data": standing_data}
                    )
            
            logger.info(
                f"Fetched {len(standings)} NFL standings",
                extra={
                    "season": season,
                    "count": len(standings)
                }
            )
            
            return standings
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NFL standings: {e}",
                extra={"season": season}
            )
            return []
    
    async def get_fixtures(
        self,
        season: int,
        week: Optional[int] = None
    ) -> List[NFLFixture]:
        """
        Get NFL fixtures/schedule for a season or specific week.
        
        Args:
            season: Season year
            week: Optional week number
            
        Returns:
            List of NFLFixture objects
        """
        try:
            # Build parameters
            params = {'season': season}
            if week is not None:
                params['week'] = week
            
            # Make API request
            data = await self._request('GET', '/fixtures', params=params)
            
            # Parse response
            fixtures = []
            for fixture_data in data.get('response', []):
                try:
                    fixture = NFLFixture(**fixture_data)
                    fixtures.append(fixture)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse fixture data: {e}",
                        extra={"fixture_data": fixture_data}
                    )
            
            logger.info(
                f"Fetched {len(fixtures)} NFL fixtures",
                extra={
                    "season": season,
                    "week": week,
                    "count": len(fixtures)
                }
            )
            
            return fixtures
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NFL fixtures: {e}",
                extra={"season": season, "week": week}
            )
            return []
    
    async def get_players(
        self,
        team: Optional[str] = None,
        player_id: Optional[str] = None
    ) -> List[NFLPlayer]:
        """
        Get NFL player statistics.
        
        Args:
            team: Team name filter
            player_id: Specific player ID filter
            
        Returns:
            List of NFLPlayer objects
        """
        try:
            # Build parameters
            params = {}
            if team:
                params['team'] = team
            if player_id:
                params['id'] = player_id
            
            # Make API request
            data = await self._request('GET', '/players', params=params)
            
            # Parse response
            players = []
            for player_data in data.get('response', []):
                try:
                    player = NFLPlayer(**player_data)
                    players.append(player)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse player data: {e}",
                        extra={"player_data": player_data}
                    )
            
            logger.info(
                f"Fetched {len(players)} NFL players",
                extra={
                    "team": team,
                    "player_id": player_id,
                    "count": len(players)
                }
            )
            
            return players
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NFL players: {e}",
                extra={"team": team, "player_id": player_id}
            )
            return []
    
    async def get_injuries(
        self,
        team: Optional[str] = None
    ) -> List[NFLInjury]:
        """
        Get NFL injury reports.
        
        Args:
            team: Team name filter (None for all teams)
            
        Returns:
            List of NFLInjury objects
        """
        try:
            # Build parameters
            params = {}
            if team:
                params['team'] = team
            
            # Make API request
            data = await self._request('GET', '/injuries', params=params)
            
            # Parse response
            injuries = []
            for injury_data in data.get('response', []):
                try:
                    injury = NFLInjury(**injury_data)
                    injuries.append(injury)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse injury data: {e}",
                        extra={"injury_data": injury_data}
                    )
            
            logger.info(
                f"Fetched {len(injuries)} NFL injuries",
                extra={
                    "team": team,
                    "count": len(injuries)
                }
            )
            
            return injuries
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NFL injuries: {e}",
                extra={"team": team}
            )
            return []

