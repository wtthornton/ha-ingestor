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
            # AFC East
            Team(id='buf', name='Buffalo Bills', abbreviation='BUF', logo='', colors={'primary': '#00338D', 'secondary': '#C60C30'}),
            Team(id='mia', name='Miami Dolphins', abbreviation='MIA', logo='', colors={'primary': '#008E97', 'secondary': '#FC4C02'}),
            Team(id='ne', name='New England Patriots', abbreviation='NE', logo='', colors={'primary': '#002244', 'secondary': '#C60C30'}),
            Team(id='nyj', name='New York Jets', abbreviation='NYJ', logo='', colors={'primary': '#125740', 'secondary': '#FFFFFF'}),
            # AFC North
            Team(id='bal', name='Baltimore Ravens', abbreviation='BAL', logo='', colors={'primary': '#241773', 'secondary': '#000000'}),
            Team(id='cin', name='Cincinnati Bengals', abbreviation='CIN', logo='', colors={'primary': '#FB4F14', 'secondary': '#000000'}),
            Team(id='cle', name='Cleveland Browns', abbreviation='CLE', logo='', colors={'primary': '#311D00', 'secondary': '#FF3C00'}),
            Team(id='pit', name='Pittsburgh Steelers', abbreviation='PIT', logo='', colors={'primary': '#FFB612', 'secondary': '#101820'}),
            # AFC South
            Team(id='hou', name='Houston Texans', abbreviation='HOU', logo='', colors={'primary': '#03202F', 'secondary': '#A71930'}),
            Team(id='ind', name='Indianapolis Colts', abbreviation='IND', logo='', colors={'primary': '#002C5F', 'secondary': '#A2AAAD'}),
            Team(id='jax', name='Jacksonville Jaguars', abbreviation='JAX', logo='', colors={'primary': '#006778', 'secondary': '#D7A22A'}),
            Team(id='ten', name='Tennessee Titans', abbreviation='TEN', logo='', colors={'primary': '#0C2340', 'secondary': '#4B92DB'}),
            # AFC West
            Team(id='den', name='Denver Broncos', abbreviation='DEN', logo='', colors={'primary': '#FB4F14', 'secondary': '#002244'}),
            Team(id='kc', name='Kansas City Chiefs', abbreviation='KC', logo='', colors={'primary': '#E31837', 'secondary': '#FFB81C'}),
            Team(id='lv', name='Las Vegas Raiders', abbreviation='LV', logo='', colors={'primary': '#000000', 'secondary': '#A5ACAF'}),
            Team(id='lac', name='Los Angeles Chargers', abbreviation='LAC', logo='', colors={'primary': '#0080C6', 'secondary': '#FFC20E'}),
            # NFC East
            Team(id='dal', name='Dallas Cowboys', abbreviation='DAL', logo='', colors={'primary': '#003594', 'secondary': '#869397'}),
            Team(id='nyg', name='New York Giants', abbreviation='NYG', logo='', colors={'primary': '#0B2265', 'secondary': '#A71930'}),
            Team(id='phi', name='Philadelphia Eagles', abbreviation='PHI', logo='', colors={'primary': '#004C54', 'secondary': '#A5ACAF'}),
            Team(id='wsh', name='Washington Commanders', abbreviation='WSH', logo='', colors={'primary': '#5A1414', 'secondary': '#FFB612'}),
            # NFC North
            Team(id='chi', name='Chicago Bears', abbreviation='CHI', logo='', colors={'primary': '#0B162A', 'secondary': '#C83803'}),
            Team(id='det', name='Detroit Lions', abbreviation='DET', logo='', colors={'primary': '#0076B6', 'secondary': '#B0B7BC'}),
            Team(id='gb', name='Green Bay Packers', abbreviation='GB', logo='', colors={'primary': '#203731', 'secondary': '#FFB612'}),
            Team(id='min', name='Minnesota Vikings', abbreviation='MIN', logo='', colors={'primary': '#4F2683', 'secondary': '#FFC62F'}),
            # NFC South
            Team(id='atl', name='Atlanta Falcons', abbreviation='ATL', logo='', colors={'primary': '#A71930', 'secondary': '#000000'}),
            Team(id='car', name='Carolina Panthers', abbreviation='CAR', logo='', colors={'primary': '#0085CA', 'secondary': '#101820'}),
            Team(id='no', name='New Orleans Saints', abbreviation='NO', logo='', colors={'primary': '#D3BC8D', 'secondary': '#101820'}),
            Team(id='tb', name='Tampa Bay Buccaneers', abbreviation='TB', logo='', colors={'primary': '#D50A0A', 'secondary': '#FF7900'}),
            # NFC West
            Team(id='ari', name='Arizona Cardinals', abbreviation='ARI', logo='', colors={'primary': '#97233F', 'secondary': '#000000'}),
            Team(id='lar', name='Los Angeles Rams', abbreviation='LAR', logo='', colors={'primary': '#003594', 'secondary': '#FFA300'}),
            Team(id='sf', name='San Francisco 49ers', abbreviation='SF', logo='', colors={'primary': '#AA0000', 'secondary': '#B3995D'}),
            Team(id='sea', name='Seattle Seahawks', abbreviation='SEA', logo='', colors={'primary': '#002244', 'secondary': '#69BE28'}),
        ]
    
    def _get_nhl_teams(self) -> List[Team]:
        """Return list of NHL teams (static for Phase 1)"""
        # TODO: Fetch from API in Phase 2
        return [
            # Atlantic Division
            Team(id='bos', name='Boston Bruins', abbreviation='BOS', logo='', colors={'primary': '#FCB514', 'secondary': '#000000'}),
            Team(id='buf', name='Buffalo Sabres', abbreviation='BUF', logo='', colors={'primary': '#002654', 'secondary': '#FCB514'}),
            Team(id='det', name='Detroit Red Wings', abbreviation='DET', logo='', colors={'primary': '#CE1126', 'secondary': '#FFFFFF'}),
            Team(id='fla', name='Florida Panthers', abbreviation='FLA', logo='', colors={'primary': '#041E42', 'secondary': '#C8102E'}),
            Team(id='mtl', name='Montreal Canadiens', abbreviation='MTL', logo='', colors={'primary': '#AF1E2D', 'secondary': '#192168'}),
            Team(id='ott', name='Ottawa Senators', abbreviation='OTT', logo='', colors={'primary': '#C52032', 'secondary': '#000000'}),
            Team(id='tbl', name='Tampa Bay Lightning', abbreviation='TBL', logo='', colors={'primary': '#002868', 'secondary': '#FFFFFF'}),
            Team(id='tor', name='Toronto Maple Leafs', abbreviation='TOR', logo='', colors={'primary': '#00205B', 'secondary': '#FFFFFF'}),
            # Metropolitan Division
            Team(id='car', name='Carolina Hurricanes', abbreviation='CAR', logo='', colors={'primary': '#CC0000', 'secondary': '#000000'}),
            Team(id='cbj', name='Columbus Blue Jackets', abbreviation='CBJ', logo='', colors={'primary': '#002654', 'secondary': '#CE1126'}),
            Team(id='njd', name='New Jersey Devils', abbreviation='NJD', logo='', colors={'primary': '#CE1126', 'secondary': '#000000'}),
            Team(id='nyi', name='New York Islanders', abbreviation='NYI', logo='', colors={'primary': '#00539B', 'secondary': '#F47D30'}),
            Team(id='nyr', name='New York Rangers', abbreviation='NYR', logo='', colors={'primary': '#0038A8', 'secondary': '#CE1126'}),
            Team(id='phi', name='Philadelphia Flyers', abbreviation='PHI', logo='', colors={'primary': '#F74902', 'secondary': '#000000'}),
            Team(id='pit', name='Pittsburgh Penguins', abbreviation='PIT', logo='', colors={'primary': '#000000', 'secondary': '#FCB514'}),
            Team(id='wsh', name='Washington Capitals', abbreviation='WSH', logo='', colors={'primary': '#041E42', 'secondary': '#C8102E'}),
            # Central Division
            Team(id='ari', name='Arizona Coyotes', abbreviation='ARI', logo='', colors={'primary': '#8C2633', 'secondary': '#E2D6B5'}),
            Team(id='chi', name='Chicago Blackhawks', abbreviation='CHI', logo='', colors={'primary': '#CF0A2C', 'secondary': '#000000'}),
            Team(id='col', name='Colorado Avalanche', abbreviation='COL', logo='', colors={'primary': '#6F263D', 'secondary': '#236192'}),
            Team(id='dal', name='Dallas Stars', abbreviation='DAL', logo='', colors={'primary': '#006847', 'secondary': '#8F8F8C'}),
            Team(id='min', name='Minnesota Wild', abbreviation='MIN', logo='', colors={'primary': '#154734', 'secondary': '#A6192E'}),
            Team(id='nsh', name='Nashville Predators', abbreviation='NSH', logo='', colors={'primary': '#FFB81C', 'secondary': '#041E42'}),
            Team(id='stl', name='St. Louis Blues', abbreviation='STL', logo='', colors={'primary': '#002F87', 'secondary': '#FCB514'}),
            Team(id='wpg', name='Winnipeg Jets', abbreviation='WPG', logo='', colors={'primary': '#041E42', 'secondary': '#004C97'}),
            # Pacific Division
            Team(id='ana', name='Anaheim Ducks', abbreviation='ANA', logo='', colors={'primary': '#F47A38', 'secondary': '#B9975B'}),
            Team(id='cgy', name='Calgary Flames', abbreviation='CGY', logo='', colors={'primary': '#C8102E', 'secondary': '#F1BE48'}),
            Team(id='edm', name='Edmonton Oilers', abbreviation='EDM', logo='', colors={'primary': '#041E42', 'secondary': '#FF4C00'}),
            Team(id='lak', name='Los Angeles Kings', abbreviation='LAK', logo='', colors={'primary': '#111111', 'secondary': '#A2AAAD'}),
            Team(id='sjs', name='San Jose Sharks', abbreviation='SJS', logo='', colors={'primary': '#006D75', 'secondary': '#EA7200'}),
            Team(id='sea', name='Seattle Kraken', abbreviation='SEA', logo='', colors={'primary': '#001628', 'secondary': '#99D9D9'}),
            Team(id='vgk', name='Vegas Golden Knights', abbreviation='VGK', logo='', colors={'primary': '#B4975A', 'secondary': '#333F42'}),
            Team(id='van', name='Vancouver Canucks', abbreviation='VAN', logo='', colors={'primary': '#00205B', 'secondary': '#00843D'}),
        ]

