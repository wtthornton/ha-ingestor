"""
Health Check Handler for Enrichment Pipeline Service
"""

import logging
from aiohttp import web
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthCheckHandler:
    """Handles health check requests for the enrichment pipeline service"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.service = None
    
    def set_service(self, service):
        """Set the service instance for health checks"""
        self.service = service
    
    async def health_check(self, request):
        """
        Handle health check requests
        
        Returns:
            JSON response with health status
        """
        try:
            health_data = {
                "status": "healthy",
                "service": "enrichment-pipeline",
                "uptime": str(datetime.now() - self.start_time),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add service status if available
            if self.service:
                service_status = self.service.get_service_status()
                health_data.update({
                    "is_running": service_status["is_running"],
                    "normalization": service_status["normalization"],
                    "influxdb": service_status["influxdb"]
                })
                
                # Determine overall health status
                if not service_status["is_running"]:
                    health_data["status"] = "unhealthy"
                    health_data["reason"] = "Service not running"
                elif not service_status["influxdb"]["connected"]:
                    health_data["status"] = "unhealthy"
                    health_data["reason"] = "InfluxDB not connected"
                else:
                    health_data["status"] = "healthy"
            
            return web.json_response(health_data)
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return web.json_response({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)


# Global health check handler instance
health_handler = HealthCheckHandler()


async def health_check_handler(request):
    """Handle health check requests"""
    return await health_handler.health_check(request)
