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
        """Handle health check request"""
        try:
            # Basic health check - service is running
            health_data = {
                "status": "healthy",
                "service": "websocket-ingestion",
                "uptime": str(datetime.now() - self.start_time),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add connection status if available
            if self.connection_manager:
                connection_status = self.connection_manager.get_status()
                health_data["connection"] = {
                    "is_running": connection_status["is_running"],
                    "is_connected": connection_status["client_status"].get("is_connected", False),
                    "is_authenticated": connection_status["client_status"].get("is_authenticated", False),
                    "connection_attempts": connection_status["connection_attempts"],
                    "successful_connections": connection_status["successful_connections"],
                    "failed_connections": connection_status["failed_connections"],
                    "last_error": connection_status["last_error"]
                }
                
                # Add event subscription status
                health_data["event_subscription"] = connection_status.get("event_subscription", {})
                
                # Add event processing statistics
                health_data["event_processing"] = connection_status.get("event_processing", {})
                
                # Add event rate statistics
                health_data["event_rates"] = connection_status.get("event_rates", {})
                
                # Determine overall health status
                if not connection_status["is_running"]:
                    health_data["status"] = "unhealthy"
                    health_data["reason"] = "Connection manager not running"
                elif connection_status["failed_connections"] > 5:
                    health_data["status"] = "degraded"
                    health_data["reason"] = "Multiple connection failures"
                elif not connection_status["client_status"].get("is_authenticated", False):
                    health_data["status"] = "degraded"
                    health_data["reason"] = "Not authenticated with Home Assistant"
            else:
                health_data["connection"] = {
                    "status": "not_initialized"
                }
                health_data["status"] = "degraded"
                health_data["reason"] = "Connection manager not initialized"
            
            # Determine HTTP status code
            status_code = 200
            if health_data["status"] == "unhealthy":
                status_code = 503
            elif health_data["status"] == "degraded":
                status_code = 200  # Still operational but with issues
            
            return web.json_response(health_data, status=status_code)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response(
                {
                    "status": "unhealthy", 
                    "service": "websocket-ingestion",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }, 
                status=500
            )
