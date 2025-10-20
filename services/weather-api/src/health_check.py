"""
Health Check Handler for Weather API Service
Epic 31, Story 31.1
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class HealthCheckHandler:
    """Handles health check requests with component status"""
    
    def __init__(self):
        """Initialize health check handler"""
        self.start_time = datetime.utcnow()
        self.last_check_time = None
        
    async def handle(self) -> Dict[str, Any]:
        """
        Handle health check request
        
        Returns:
            Dict with service health status
        """
        try:
            self.last_check_time = datetime.utcnow()
            uptime = datetime.utcnow() - self.start_time
            
            health_data = {
                "status": "healthy",
                "service": "weather-api",
                "version": "1.0.0",
                "uptime": str(uptime),
                "uptime_seconds": int(uptime.total_seconds()),
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "api": "healthy",
                    "weather_client": "not_initialized",  # Will be updated in Story 31.2
                    "cache": "not_initialized",  # Will be updated in Story 31.2
                    "influxdb": "not_initialized"  # Will be updated in Story 31.2
                }
            }
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "weather-api",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_uptime_seconds(self) -> int:
        """Get service uptime in seconds"""
        uptime = datetime.utcnow() - self.start_time
        return int(uptime.total_seconds())
