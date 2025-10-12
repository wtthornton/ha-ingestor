"""
Sports API REST Endpoints
Simple, pragmatic implementation with caching and error handling
"""

import logging
from datetime import datetime
from typing import Optional
from aiohttp import web

logger = logging.getLogger(__name__)


class SportsEndpoints:
    """REST API endpoints for sports data"""
    
    def __init__(self, service):
        """
        Initialize endpoints with service reference.
        
        Args:
            service: SportsAPIService instance with clients and components
        """
        self.service = service
    
    async def nfl_scores(self, request: web.Request) -> web.Response:
        """
        GET /api/nfl/scores?date=YYYY-MM-DD
        
        Fetch NFL scores (live or historical) with caching.
        """
        date = request.query.get('date')
        cache_key = f"nfl_scores_{date or 'live'}"
        
        try:
            # Check cache first
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(
                    cache_key, 
                    'scores_live' if not date else 'scores_recent'
                )
                if cached:
                    return web.json_response({
                        'status': 'success',
                        'data': cached,
                        'metadata': {
                            'source': 'cache',
                            'timestamp': datetime.now().isoformat()
                        }
                    })
            
            # Fetch from API
            if not self.service.nfl_client:
                return web.json_response({
                    'status': 'error',
                    'error': 'NFL client not initialized'
                }, status=503)
            
            scores = await self.service.nfl_client.get_scores(date)
            data = [s.dict() for s in scores]
            
            # Write to InfluxDB (async, don't wait)
            if self.service.influxdb_writer and scores:
                for score in scores:
                    await self.service.influxdb_writer.write_nfl_score(score.dict())
            
            # Cache result
            if self.service.cache_manager:
                await self.service.cache_manager.set(
                    cache_key, 
                    data, 
                    'scores_live' if not date else 'scores_recent'
                )
            
            return web.json_response({
                'status': 'success',
                'data': data,
                'metadata': {
                    'source': 'api',
                    'timestamp': datetime.now().isoformat(),
                    'count': len(data)
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching NFL scores: {e}")
            return web.json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    async def nfl_standings(self, request: web.Request) -> web.Response:
        """GET /api/nfl/standings?season=YYYY"""
        season = int(request.query.get('season', datetime.now().year))
        cache_key = f"nfl_standings_{season}"
        
        try:
            # Check cache
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(cache_key, 'standings')
                if cached:
                    return web.json_response({
                        'status': 'success',
                        'data': cached,
                        'metadata': {'source': 'cache'}
                    })
            
            # Fetch from API
            if not self.service.nfl_client:
                return web.json_response({'status': 'error', 'error': 'NFL client not initialized'}, status=503)
            
            standings = await self.service.nfl_client.get_standings(season)
            data = [s.dict() for s in standings]
            
            # Write to InfluxDB
            if self.service.influxdb_writer and standings:
                await self.service.influxdb_writer.write_standings(data, sport="nfl")
            
            # Cache
            if self.service.cache_manager:
                await self.service.cache_manager.set(cache_key, data, 'standings')
            
            return web.json_response({'status': 'success', 'data': data, 'metadata': {'source': 'api'}})
            
        except Exception as e:
            logger.error(f"Error fetching NFL standings: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    async def nfl_fixtures(self, request: web.Request) -> web.Response:
        """GET /api/nfl/fixtures?season=YYYY&week=N"""
        season = int(request.query.get('season', datetime.now().year))
        week = request.query.get('week')
        week_int = int(week) if week else None
        
        cache_key = f"nfl_fixtures_{season}_{week or 'all'}"
        
        try:
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(cache_key, 'fixtures')
                if cached:
                    return web.json_response({'status': 'success', 'data': cached, 'metadata': {'source': 'cache'}})
            
            if not self.service.nfl_client:
                return web.json_response({'status': 'error', 'error': 'NFL client not initialized'}, status=503)
            
            fixtures = await self.service.nfl_client.get_fixtures(season, week_int)
            data = [f.dict() for f in fixtures]
            
            if self.service.cache_manager:
                await self.service.cache_manager.set(cache_key, data, 'fixtures')
            
            return web.json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            logger.error(f"Error fetching NFL fixtures: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    async def nfl_injuries(self, request: web.Request) -> web.Response:
        """GET /api/nfl/injuries?team=TEAM_NAME"""
        team = request.query.get('team')
        cache_key = f"nfl_injuries_{team or 'all'}"
        
        try:
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(cache_key, 'injuries')
                if cached:
                    return web.json_response({'status': 'success', 'data': cached, 'metadata': {'source': 'cache'}})
            
            if not self.service.nfl_client:
                return web.json_response({'status': 'error', 'error': 'NFL client not initialized'}, status=503)
            
            injuries = await self.service.nfl_client.get_injuries(team)
            data = [i.dict() for i in injuries]
            
            # Write to InfluxDB
            if self.service.influxdb_writer and injuries:
                for injury in injuries:
                    await self.service.influxdb_writer.write_injury_report(injury.dict())
            
            if self.service.cache_manager:
                await self.service.cache_manager.set(cache_key, data, 'injuries')
            
            return web.json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            logger.error(f"Error fetching NFL injuries: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    # NHL Endpoints (simpler - reuse pattern)
    async def nhl_scores(self, request: web.Request) -> web.Response:
        """GET /api/nhl/scores?date=YYYY-MM-DD"""
        date = request.query.get('date')
        cache_key = f"nhl_scores_{date or 'live'}"
        
        try:
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(cache_key, 'scores_live' if not date else 'scores_recent')
                if cached:
                    return web.json_response({'status': 'success', 'data': cached, 'metadata': {'source': 'cache'}})
            
            if not self.service.nhl_client:
                return web.json_response({'status': 'error', 'error': 'NHL client not initialized'}, status=503)
            
            scores = await self.service.nhl_client.get_scores(date)
            data = [s.dict() for s in scores]
            
            if self.service.influxdb_writer and scores:
                for score in scores:
                    await self.service.influxdb_writer.write_nhl_score(score.dict())
            
            if self.service.cache_manager:
                await self.service.cache_manager.set(cache_key, data, 'scores_live' if not date else 'scores_recent')
            
            return web.json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            logger.error(f"Error fetching NHL scores: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    async def nhl_standings(self, request: web.Request) -> web.Response:
        """GET /api/nhl/standings?season=YYYY"""
        season = int(request.query.get('season', datetime.now().year))
        cache_key = f"nhl_standings_{season}"
        
        try:
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(cache_key, 'standings')
                if cached:
                    return web.json_response({'status': 'success', 'data': cached, 'metadata': {'source': 'cache'}})
            
            if not self.service.nhl_client:
                return web.json_response({'status': 'error', 'error': 'NHL client not initialized'}, status=503)
            
            standings = await self.service.nhl_client.get_standings(season)
            data = [s.dict() for s in standings]
            
            if self.service.influxdb_writer and standings:
                await self.service.influxdb_writer.write_standings(data, sport="nhl")
            
            if self.service.cache_manager:
                await self.service.cache_manager.set(cache_key, data, 'standings')
            
            return web.json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            logger.error(f"Error fetching NHL standings: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    async def nhl_fixtures(self, request: web.Request) -> web.Response:
        """GET /api/nhl/fixtures?season=YYYY"""
        season = int(request.query.get('season', datetime.now().year))
        cache_key = f"nhl_fixtures_{season}"
        
        try:
            if self.service.cache_manager:
                cached = await self.service.cache_manager.get(cache_key, 'fixtures')
                if cached:
                    return web.json_response({'status': 'success', 'data': cached})
            
            if not self.service.nhl_client:
                return web.json_response({'status': 'error', 'error': 'NHL client not initialized'}, status=503)
            
            fixtures = await self.service.nhl_client.get_fixtures(season)
            data = [f.dict() for f in fixtures]
            
            if self.service.cache_manager:
                await self.service.cache_manager.set(cache_key, data, 'fixtures')
            
            return web.json_response({'status': 'success', 'data': data})
            
        except Exception as e:
            logger.error(f"Error fetching NHL fixtures: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    # Admin endpoints
    async def get_stats(self, request: web.Request) -> web.Response:
        """GET /api/sports/stats - Service statistics"""
        try:
            stats = {
                'cache': self.service.cache_manager.get_statistics() if self.service.cache_manager else {},
                'rate_limiter': self.service.rate_limiter.get_statistics() if self.service.rate_limiter else {},
                'influxdb': self.service.influxdb_writer.get_statistics() if self.service.influxdb_writer else {},
                'nfl_client': self.service.nfl_client.get_statistics() if self.service.nfl_client else {},
                'nhl_client': self.service.nhl_client.get_statistics() if self.service.nhl_client else {}
            }
            
            return web.json_response({'status': 'success', 'stats': stats})
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)
    
    async def clear_cache(self, request: web.Request) -> web.Response:
        """POST /api/sports/cache/clear - Clear all cache"""
        try:
            if not self.service.cache_manager:
                return web.json_response({'status': 'error', 'error': 'Cache not initialized'}, status=503)
            
            count = await self.service.cache_manager.clear()
            
            return web.json_response({
                'status': 'success',
                'message': f'Cleared {count} cache entries'
            })
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return web.json_response({'status': 'error', 'error': str(e)}, status=500)

