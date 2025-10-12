"""
Sports API Client

Handles fetching data from ESPN, NHL Official API, and other sports data providers.
Implements team-based filtering to optimize API usage.
"""

import aiohttp
import os
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from src.models import Game, Team, GameList, TeamList, Period
from src.cache_service import CacheService

logger = logging.getLogger(__name__)


class SportsAPIClient:
    """Client for sports data APIs (ESPN, NHL, etc.)"""
    
    def __init__(self, cache: CacheService):
        self.cache = cache
        self.api_key = os.getenv('SPORTS_API_KEY', '')
        self.provider = os.getenv('SPORTS_API_PROVIDER', 'espn')
        
        # API endpoints
        self.endpoints = {
            'espn': {
                'nfl_scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
                'nhl_scoreboard': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',
            },
            'nhl_official': {
                'scoreboard': 'https://statsapi.web.nhl.com/api/v1/schedule',
                'game': 'https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live',
            }
        }
        
        # Usage tracking
        self.api_calls_today = 0
        self.nfl_calls = 0
        self.nhl_calls = 0
    
    async def get_live_games(
        self, 
        league: Optional[str] = None,
        team_ids: Optional[List[str]] = None
    ) -> List[Game]:
        """
        Fetch live games, filtered by team IDs
        
        Args:
            league: Filter by league ('NFL' or 'NHL')
            team_ids: List of team IDs (e.g., ['sf', 'dal', 'bos'])
                     If None or empty, returns NO games (opt-in model)
        
        Returns:
            List of Game objects for selected teams
        """
        # CRITICAL: If no teams selected, return empty list
        if not team_ids:
            logger.info("No teams selected, returning empty list")
            return []
        
        cache_key = f"live_games_{league or 'all'}_{'_'.join(sorted(team_ids))}"
        
        # Check cache first
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        # Fetch from API
        games = []
        
        try:
            if not league or league.upper() == 'NFL':
                nfl_games = await self._fetch_nfl_scoreboard()
                games.extend(nfl_games)
            
            if not league or league.upper() == 'NHL':
                nhl_games = await self._fetch_nhl_scoreboard()
                games.extend(nhl_games)
        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            # Try to return cached data even if expired
            cached_fallback = await self._get_expired_cache(cache_key)
            if cached_fallback:
                return cached_fallback
            return []
        
        # Filter only live games involving selected teams
        live_games = [
            g for g in games 
            if g.status == 'live' and self._game_has_selected_team(g, team_ids)
        ]
        
        # Cache for 15 seconds (live data changes frequently)
        await self.cache.set(cache_key, live_games, ttl=15)
        
        return live_games
    
    async def get_upcoming_games(
        self,
        league: Optional[str] = None,
        hours: int = 24,
        team_ids: Optional[List[str]] = None
    ) -> List[Game]:
        """Fetch upcoming games in next N hours"""
        if not team_ids:
            return []
        
        cache_key = f"upcoming_games_{league or 'all'}_{hours}_{'_'.join(sorted(team_ids))}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        games = []
        
        try:
            if not league or league.upper() == 'NFL':
                nfl_games = await self._fetch_nfl_scoreboard()
                games.extend(nfl_games)
            
            if not league or league.upper() == 'NHL':
                nhl_games = await self._fetch_nhl_scoreboard()
                games.extend(nhl_games)
        except Exception as e:
            logger.error(f"Error fetching upcoming games: {e}")
            return []
        
        # Filter upcoming games within time window
        now = datetime.utcnow()
        future_limit = now + timedelta(hours=hours)
        
        upcoming_games = [
            g for g in games
            if g.status == 'scheduled' 
            and self._game_has_selected_team(g, team_ids)
            and now <= datetime.fromisoformat(g.start_time.replace('Z', '+00:00')) <= future_limit
        ]
        
        # Cache for 5 minutes (doesn't change frequently)
        await self.cache.set(cache_key, upcoming_games, ttl=300)
        
        return upcoming_games
    
    async def get_available_teams(self, league: Optional[str] = None) -> TeamList:
        """Get list of all available teams"""
        cache_key = f"teams_{league or 'all'}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        teams = []
        
        # For now, return static team list
        # TODO: Fetch from API in Phase 2
        if not league or league.upper() == 'NFL':
            teams.extend(self._get_nfl_teams())
        
        if not league or league.upper() == 'NHL':
            teams.extend(self._get_nhl_teams())
        
        result = TeamList(
            league=league or 'ALL',
            teams=teams,
            count=len(teams)
        )
        
        # Cache for 1 hour (static data)
        await self.cache.set(cache_key, result, ttl=3600)
        
        return result
    
    async def test_connection(self) -> bool:
        """Test API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                url = self.endpoints['espn']['nfl_scoreboard']
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    self.api_calls_today += 1
                    return response.status == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def _game_has_selected_team(self, game: Game, team_ids: List[str]) -> bool:
        """Check if game involves any of the selected teams"""
        if not team_ids:
            return False
        return game.home_team.id in team_ids or game.away_team.id in team_ids
    
    async def _fetch_nfl_scoreboard(self) -> List[Game]:
        """Fetch NFL scoreboard from ESPN"""
        url = self.endpoints['espn']['nfl_scoreboard']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    self.api_calls_today += 1
                    self.nfl_calls += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_espn_games(data, 'NFL')
                    else:
                        logger.error(f"NFL API returned {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching NFL data: {e}")
            return []
    
    async def _fetch_nhl_scoreboard(self) -> List[Game]:
        """Fetch NHL scoreboard"""
        if self.provider == 'nhl_official':
            url = self.endpoints['nhl_official']['scoreboard']
        else:
            url = self.endpoints['espn']['nhl_scoreboard']
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    self.api_calls_today += 1
                    self.nhl_calls += 1
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_espn_games(data, 'NHL')
                    else:
                        logger.error(f"NHL API returned {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching NHL data: {e}")
            return []
    
    def _parse_espn_games(self, data: dict, league: str) -> List[Game]:
        """Parse ESPN API response into Game objects"""
        games = []
        
        for event in data.get('events', []):
            try:
                competition = event['competitions'][0]
                competitors = competition['competitors']
                
                # Find home and away teams
                home_team = next(c for c in competitors if c['homeAway'] == 'home')
                away_team = next(c for c in competitors if c['homeAway'] == 'away')
                
                game = Game(
                    id=event['id'],
                    league=league,
                    status=self._map_status(competition['status']['type']['state']),
                    start_time=event['date'],
                    home_team=self._parse_team(home_team),
                    away_team=self._parse_team(away_team),
                    score={
                        'home': int(home_team.get('score', 0)),
                        'away': int(away_team.get('score', 0))
                    },
                    period=Period(
                        current=int(competition['status'].get('period', 1)),
                        total=4 if league == 'NFL' else 3,
                        time_remaining=competition['status'].get('displayClock', '0:00')
                    )
                )
                
                games.append(game)
            except Exception as e:
                logger.error(f"Error parsing game: {e}")
                continue
        
        return games
    
    def _parse_team(self, competitor: dict) -> Team:
        """Parse team data from API response"""
        team_data = competitor['team']
        records = competitor.get('records', [{}])
        
        return Team(
            id=team_data.get('abbreviation', '').lower(),
            name=team_data.get('displayName', ''),
            abbreviation=team_data.get('abbreviation', ''),
            logo=team_data.get('logo', ''),
            colors={
                'primary': f"#{team_data.get('color', '000000')}",
                'secondary': f"#{team_data.get('alternateColor', 'FFFFFF')}"
            },
            record={
                'wins': int(records[0].get('wins', 0)),
                'losses': int(records[0].get('losses', 0)),
                'ties': int(records[0].get('ties', 0)) if league == 'NFL' else None
            } if records else None
        )
    
    def _map_status(self, espn_status: str) -> str:
        """Map ESPN status to our status"""
        mapping = {
            'pre': 'scheduled',
            'in': 'live',
            'post': 'final'
        }
        return mapping.get(espn_status, 'scheduled')
    
    async def _get_expired_cache(self, key: str) -> Optional[List[Game]]:
        """Try to get even expired cache as fallback"""
        if key in self.cache.cache:
            value, _ = self.cache.cache[key]
            return value
        return None
    
    def _get_nfl_teams(self) -> List[Team]:
        """Return list of NFL teams (static for Phase 1)"""
        # TODO: Fetch from API in Phase 2
        return [
            Team(id='sf', name='San Francisco 49ers', abbreviation='SF', logo='', colors={'primary': '#AA0000', 'secondary': '#B3995D'}),
            Team(id='dal', name='Dallas Cowboys', abbreviation='DAL', logo='', colors={'primary': '#003594', 'secondary': '#869397'}),
            # Add all 32 teams...
        ]
    
    def _get_nhl_teams(self) -> List[Team]:
        """Return list of NHL teams (static for Phase 1)"""
        # TODO: Fetch from API in Phase 2
        return [
            Team(id='bos', name='Boston Bruins', abbreviation='BOS', logo='', colors={'primary': '#FCB514', 'secondary': '#000000'}),
            Team(id='wsh', name='Washington Capitals', abbreviation='WSH', logo='', colors={'primary': '#041E42', 'secondary': '#C8102E'}),
            # Add all 32 teams...
        ]

