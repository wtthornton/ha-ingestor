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
        self.historical_counter = None
    
    def set_service(self, service):
        """Set the service instance for health checks"""
        self.service = service
    
    def set_historical_counter(self, historical_counter):
        """Set the historical counter for persistent totals"""
        self.historical_counter = historical_counter
    
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
    
    async def get_event_rate(self, request):
        """Get standardized event rate metrics for enrichment-pipeline service"""
        try:
            # Get current time for uptime calculation
            current_time = datetime.now()
            uptime_seconds = (current_time - self.start_time).total_seconds()
            
            # Simulate some realistic metrics for enrichment-pipeline
            # In production, these would come from actual request tracking
            import random
            events_per_second = random.uniform(0.2, 3.0)  # Simulate 0.2-3.0 req/sec
            events_per_hour = events_per_second * 3600
            
            # Simulate some processing statistics
            processed_events = int(events_per_second * uptime_seconds)
            failed_events = int(processed_events * 0.03)  # 3% failure rate
            success_rate = 97.0
            
            # Build response
            response_data = {
                "service": "enrichment-pipeline",
                "events_per_second": round(events_per_second, 2),
                "events_per_hour": round(events_per_hour, 2),
                "total_events_processed": processed_events,
                "uptime_seconds": round(uptime_seconds, 2),
                "processing_stats": {
                    "is_running": True,
                    "max_workers": 3,
                    "active_workers": 2,
                    "processed_events": processed_events,
                    "failed_events": failed_events,
                    "success_rate": success_rate,
                    "processing_rate_per_second": events_per_second,
                    "average_processing_time_ms": random.uniform(200, 800),  # 200-800ms processing time
                    "queue_size": random.randint(0, 15),
                    "queue_maxsize": 1500,
                    "uptime_seconds": uptime_seconds,
                    "last_processing_time": current_time.isoformat(),
                    "event_handlers_count": 6
                },
                "connection_stats": {
                    "is_connected": True,
                    "is_subscribed": False,
                    "total_events_received": processed_events,
                    "events_by_type": {
                        "data_normalization": int(processed_events * 0.4),
                        "influxdb_storage": int(processed_events * 0.3),
                        "data_validation": int(processed_events * 0.2),
                        "quality_alerts": int(processed_events * 0.1)
                    },
                    "last_event_time": current_time.isoformat()
                },
                "timestamp": current_time.isoformat()
            }
            
            return web.json_response(response_data, status=200)
            
        except Exception as e:
            logger.error(f"Error getting event rate: {e}")
            return web.json_response(
                {
                    "service": "enrichment-pipeline",
                    "error": str(e),
                    "events_per_second": 0,
                    "events_per_hour": 0,
                    "timestamp": datetime.now().isoformat()
                },
                status=500
            )


# Global health check handler instance
health_handler = HealthCheckHandler()


async def health_check_handler(request):
    """Handle health check requests"""
    return await health_handler.health_check(request)
