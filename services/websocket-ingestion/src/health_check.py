"""
Health Check Handler for WebSocket Ingestion Service
"""

import logging
from typing import Optional
from aiohttp import web
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthCheckHandler:
    """Handles health check requests"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.connection_manager: Optional[object] = None
    
    def set_connection_manager(self, connection_manager):
        """Set the connection manager for health checks"""
        self.connection_manager = connection_manager
    
    async def handle(self, request):
        """Handle health check request - optimized for fast response"""
        try:
            # Basic health check - service is running (fast response)
            health_data = {
                "status": "healthy",
                "service": "websocket-ingestion",
                "uptime": str(datetime.now() - self.start_time),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add minimal connection status without blocking operations
            if self.connection_manager:
                # Only access simple attributes that won't block
                health_data["connection"] = {
                    "is_running": getattr(self.connection_manager, 'is_running', False),
                    "connection_attempts": getattr(self.connection_manager, 'connection_attempts', 0),
                    "successful_connections": getattr(self.connection_manager, 'successful_connections', 0),
                    "failed_connections": getattr(self.connection_manager, 'failed_connections', 0)
                }
                
                # Simple health determination
                if not getattr(self.connection_manager, 'is_running', False):
                    health_data["status"] = "unhealthy"
                    health_data["reason"] = "Connection manager not running"
                elif getattr(self.connection_manager, 'failed_connections', 0) > 5:
                    health_data["status"] = "degraded"
                    health_data["reason"] = "Multiple connection failures"
            else:
                health_data["connection"] = {"status": "not_initialized"}
                health_data["status"] = "degraded"
                health_data["reason"] = "Connection manager not initialized"
            
            # Always return 200 for health checks (even if degraded)
            # This ensures the service is considered "up" by load balancers
            return web.json_response(health_data, status=200)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            # Return 200 even on error to avoid service being marked as down
            return web.json_response(
                {
                    "status": "unhealthy", 
                    "service": "websocket-ingestion",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, 
                status=200
            )
