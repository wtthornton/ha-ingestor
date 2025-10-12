"""
Sports API Service Main Entry Point
"""

import asyncio
import logging
import os
import sys
from aiohttp import web
from dotenv import load_dotenv

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

try:
    from shared.logging_config import setup_logging
    from shared.correlation_middleware import create_correlation_middleware
except ModuleNotFoundError:
    # Fallback for testing or when shared module not in path
    from unittest.mock import MagicMock
    setup_logging = lambda x: MagicMock()
    create_correlation_middleware = lambda: MagicMock()

try:
    from .health_check import HealthCheckHandler
    from .endpoints import SportsEndpoints
    from .nfl_client import NFLClient
    from .nhl_client import NHLClient
    from .rate_limiter import RateLimiter
    from .cache_manager import CacheManager
    from .influxdb_writer import SportsInfluxDBWriter
except ImportError:
    from health_check import HealthCheckHandler
    from endpoints import SportsEndpoints
    from nfl_client import NFLClient
    from nhl_client import NHLClient
    from rate_limiter import RateLimiter
    from cache_manager import CacheManager
    from influxdb_writer import SportsInfluxDBWriter

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logging("sports-api")


class SportsAPIService:
    """Main service class for Sports API"""
    
    def __init__(self):
        """Initialize service with configuration from environment"""
        # API Configuration
        self.api_key = os.getenv('API_SPORTS_KEY')
        if not self.api_key:
            logger.warning("API_SPORTS_KEY not set - service will not be able to fetch data")
        
        # Service Configuration
        self.port = int(os.getenv('SPORTS_API_PORT', '8015'))
        self.nfl_enabled = os.getenv('NFL_ENABLED', 'true').lower() == 'true'
        self.nhl_enabled = os.getenv('NHL_ENABLED', 'true').lower() == 'true'
        
        # Rate limiting
        rate_per_second = float(os.getenv('API_SPORTS_REQUESTS_PER_SECOND', '1'))
        burst_size = int(os.getenv('API_SPORTS_BURST_SIZE', '5'))
        self.rate_limiter = RateLimiter(rate_per_second, burst_size)
        
        # Caching
        self.cache_manager = CacheManager()
        
        # InfluxDB configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home_assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'sports_data')
        
        # Component instances (initialized in start())
        self.nfl_client = None
        self.nhl_client = None
        self.influxdb_writer = None
        
        logger.info(
            "Sports API Service configured",
            extra={
                "port": self.port,
                "nfl_enabled": self.nfl_enabled,
                "nhl_enabled": self.nhl_enabled,
                "api_key_present": bool(self.api_key)
            }
        )
    
    async def start(self):
        """Start service components"""
        logger.info("Starting Sports API Service...")
        
        # Initialize NFL client (if enabled and API key present)
        if self.nfl_enabled and self.api_key:
            self.nfl_client = NFLClient(self.api_key, rate_limiter=self.rate_limiter)
            await self.nfl_client.__aenter__()
            logger.info("NFL client initialized")
        
        # Initialize NHL client (if enabled and API key present)
        if self.nhl_enabled and self.api_key:
            self.nhl_client = NHLClient(self.api_key, rate_limiter=self.rate_limiter)
            await self.nhl_client.__aenter__()
            logger.info("NHL client initialized")
        
        # Initialize InfluxDB writer (if token present)
        if self.influxdb_token:
            try:
                self.influxdb_writer = SportsInfluxDBWriter(
                    host=self.influxdb_url,
                    token=self.influxdb_token,
                    database=self.influxdb_bucket,
                    org=self.influxdb_org
                )
                await self.influxdb_writer.start()
                logger.info("InfluxDB writer initialized")
            except Exception as e:
                logger.warning(f"InfluxDB writer initialization failed (optional): {e}")
        
        logger.info("Sports API Service components initialized")
    
    async def stop(self):
        """Stop service components and cleanup"""
        logger.info("Stopping Sports API Service...")
        
        # Cleanup NFL client
        if self.nfl_client:
            await self.nfl_client.__aexit__(None, None, None)
        
        # Cleanup NHL client
        if self.nhl_client:
            await self.nhl_client.__aexit__(None, None, None)
        
        # Cleanup InfluxDB writer
        if self.influxdb_writer:
            await self.influxdb_writer.stop()
        
        logger.info("Sports API Service stopped")
    
    def create_app(self) -> web.Application:
        """
        Create aiohttp web application.
        
        Returns:
            Configured aiohttp Application
        """
        # Create application with correlation middleware
        app = web.Application(
            middlewares=[create_correlation_middleware()]
        )
        
        # Health check endpoint
        health_handler = HealthCheckHandler(self)
        app.router.add_get('/health', health_handler.handle)
        
        # Sports endpoints
        endpoints = SportsEndpoints(self)
        
        # NFL endpoints
        if self.nfl_enabled:
            app.router.add_get('/api/nfl/scores', endpoints.nfl_scores)
            app.router.add_get('/api/nfl/standings', endpoints.nfl_standings)
            app.router.add_get('/api/nfl/fixtures', endpoints.nfl_fixtures)
            app.router.add_get('/api/nfl/injuries', endpoints.nfl_injuries)
        
        # NHL endpoints
        if self.nhl_enabled:
            app.router.add_get('/api/nhl/scores', endpoints.nhl_scores)
            app.router.add_get('/api/nhl/standings', endpoints.nhl_standings)
            app.router.add_get('/api/nhl/fixtures', endpoints.nhl_fixtures)
        
        # Admin endpoints
        app.router.add_get('/api/sports/stats', endpoints.get_stats)
        app.router.add_post('/api/sports/cache/clear', endpoints.clear_cache)
        
        logger.info(
            "Web application created",
            extra={
                "routes": len(app.router.routes()),
                "middlewares": len(app.middlewares)
            }
        )
        
        return app


async def main():
    """Main entry point"""
    try:
        # Create service
        service = SportsAPIService()
        await service.start()
        
        # Create web application
        app = service.create_app()
        
        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', service.port)
        await site.start()
        
        logger.info(
            f"Sports API Service started successfully",
            extra={
                "port": service.port,
                "host": "0.0.0.0",
                "health_check": f"http://localhost:{service.port}/health"
            }
        )
        
        # Run forever
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        
    except Exception as e:
        logger.error(f"Service startup failed: {e}", exc_info=True)
        raise
    
    finally:
        logger.info("Shutting down Sports API Service...")
        await service.stop()
        await runner.cleanup()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

