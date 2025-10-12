"""
Health Check Handler for Sports API Service
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any
from aiohttp import web

if TYPE_CHECKING:
    from main import SportsAPIService

logger = logging.getLogger(__name__)


class HealthCheckHandler:
    """Handler for /health endpoint"""
    
    def __init__(self, service: Any = None):
        """
        Initialize health check handler.
        
        Args:
            service: Reference to main service instance
        """
        self.service = service
    
    async def handle(self, request: web.Request) -> web.Response:
        """
        Handle health check request.
        
        Returns JSON with service status and component health.
        
        Args:
            request: aiohttp Request object
            
        Returns:
            JSON response with health status
        """
        # Build health status
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "sports-api",
            "version": "1.0.0",
            "components": {
                "nfl_client": "healthy" if self.service.nfl_client else "disabled",
                "nhl_client": "healthy" if self.service.nhl_client else "disabled",
                "cache": "healthy" if self.service.cache_manager else "disabled",
                "rate_limiter": "healthy" if self.service.rate_limiter else "disabled",
                "influxdb": "healthy" if self.service.influxdb_writer else "disabled"
            },
            "configuration": {
                "nfl_enabled": self.service.nfl_enabled,
                "nhl_enabled": self.service.nhl_enabled,
                "api_key_configured": bool(self.service.api_key)
            },
            "endpoints": {
                "nfl": ["/api/nfl/scores", "/api/nfl/standings", "/api/nfl/fixtures", "/api/nfl/injuries"] if self.service.nfl_enabled else [],
                "nhl": ["/api/nhl/scores", "/api/nhl/standings", "/api/nhl/fixtures"] if self.service.nhl_enabled else [],
                "admin": ["/api/sports/stats", "/api/sports/cache/clear"]
            }
        }
        
        # Determine overall status
        # For now, service is healthy if it's running
        # Future stories will add component health checks
        
        logger.debug(
            "Health check requested",
            extra={
                "status": health["status"],
                "components": len(health["components"])
            }
        )
        
        return web.json_response(health, status=200)

