"""
NHL API Client for API-SPORTS
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from .api_client import APISportsClient
    from .models import NHLScore, NHLStanding, NHLFixture
except ImportError:
    from api_client import APISportsClient
    from models import NHLScore, NHLStanding, NHLFixture

logger = logging.getLogger(__name__)


class NHLClient(APISportsClient):
    """
    NHL-specific API client.
    
    Provides methods for fetching NHL scores, standings, and fixtures
    from API-SPORTS. Reuses authentication and retry logic from base client.
    """
    
    def __init__(self, api_key: str, rate_limiter=None):
        """
        Initialize NHL client.
        
        Args:
            api_key: API-SPORTS API key (shared with NFL)
            rate_limiter: Optional RateLimiter instance
        """
        super().__init__(api_key, "https://api-sports.io/nhl", rate_limiter)
        logger.info("NHL client initialized")
    
    async def get_scores(
        self, 
        date: Optional[str] = None
    ) -> List[NHLScore]:
        """
        Get NHL scores for a specific date or live scores.
        
        Args:
            date: Date in YYYY-MM-DD format, or None for live scores
            
        Returns:
            List of NHLScore objects
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
                    score = NHLScore(**score_data)
                    scores.append(score)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse NHL score data: {e}",
                        extra={"score_data": score_data}
                    )
            
            logger.info(
                f"Fetched {len(scores)} NHL scores",
                extra={
                    "date": date or "live",
                    "count": len(scores)
                }
            )
            
            return scores
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NHL scores: {e}",
                extra={"date": date}
            )
            return []  # Return empty list on error
    
    async def get_standings(
        self, 
        season: int
    ) -> List[NHLStanding]:
        """
        Get NHL standings for a season.
        
        Args:
            season: Season year (e.g., 2025)
            
        Returns:
            List of NHLStanding objects
        """
        try:
            # Make API request
            data = await self._request('GET', '/standings', params={'season': season})
            
            # Parse response
            standings = []
            for standing_data in data.get('response', []):
                try:
                    standing = NHLStanding(**standing_data)
                    standings.append(standing)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse NHL standing data: {e}",
                        extra={"standing_data": standing_data}
                    )
            
            logger.info(
                f"Fetched {len(standings)} NHL standings",
                extra={
                    "season": season,
                    "count": len(standings)
                }
            )
            
            return standings
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NHL standings: {e}",
                extra={"season": season}
            )
            return []
    
    async def get_fixtures(
        self,
        season: int
    ) -> List[NHLFixture]:
        """
        Get NHL fixtures/schedule for a season.
        
        Args:
            season: Season year
            
        Returns:
            List of NHLFixture objects
        """
        try:
            # Make API request
            data = await self._request('GET', '/fixtures', params={'season': season})
            
            # Parse response
            fixtures = []
            for fixture_data in data.get('response', []):
                try:
                    fixture = NHLFixture(**fixture_data)
                    fixtures.append(fixture)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse NHL fixture data: {e}",
                        extra={"fixture_data": fixture_data}
                    )
            
            logger.info(
                f"Fetched {len(fixtures)} NHL fixtures",
                extra={
                    "season": season,
                    "count": len(fixtures)
                }
            )
            
            return fixtures
            
        except Exception as e:
            logger.error(
                f"Failed to fetch NHL fixtures: {e}",
                extra={"season": season}
            )
            return []

