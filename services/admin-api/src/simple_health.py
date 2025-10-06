"""
Simplified Health Endpoint for Dashboard Integration
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
import aiohttp
import os

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)


class SimpleHealthService:
    """Simplified health service for dashboard integration"""
    
    def __init__(self):
        self.router = APIRouter()
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://websocket-ingestion:8000"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://enrichment-pipeline:8002"),
            "influxdb": os.getenv("INFLUXDB_URL", "http://influxdb:8086"),
        }
        self._add_routes()
    
    def _add_routes(self):
        """Add simplified health routes"""
        
        @self.router.get("/health")
        async def get_health():
            """Get simplified health status for dashboard"""
            try:
                # Check basic service connectivity
                services_status = await self._check_services_simple()
                logger.info(f"Services status: {services_status}")
                
                # Determine overall status
                healthy_services = sum(1 for status in services_status.values() if status.get("status") == "healthy")
                total_services = len(services_status)
                
                if healthy_services == total_services:
                    overall_status = "healthy"
                elif healthy_services > 0:
                    overall_status = "degraded"
                else:
                    overall_status = "unhealthy"
                
                # Get WebSocket service data
                websocket_data = services_status.get("websocket-ingestion", {})
                websocket_health = websocket_data.get("health_data", {})
                
                # Return simplified response with real WebSocket data
                return {
                    "overall_status": overall_status,
                    "admin_api_status": "healthy",
                    "ingestion_service": {
                        "status": overall_status,
                        "websocket_connection": {
                            "is_connected": websocket_health.get("is_connected", False),
                            "last_connection_time": websocket_health.get("timestamp", datetime.now().isoformat()),
                            "connection_attempts": websocket_health.get("connection_attempts", 0),
                            "last_error": None
                        },
                        "event_processing": {
                            "status": "healthy" if websocket_health.get("event_count", 0) > 0 else "degraded",
                            "events_per_minute": self._calculate_events_per_minute(websocket_health),
                            "total_events": websocket_health.get("event_count", 0),
                            "error_rate": 0
                        },
                        "weather_enrichment": {
                            "enabled": True,
                            "cache_hits": 0,
                            "api_calls": 0,
                            "last_error": None
                        },
                        "influxdb_storage": {
                            "is_connected": services_status.get("influxdb", {}).get("status") == "healthy",
                            "last_write_time": datetime.now().isoformat(),
                            "write_errors": 0
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting health status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get health status"
                )
        
        @self.router.get("/stats")
        async def get_stats(period: str = "1h"):
            """Get simplified statistics for dashboard"""
            try:
                return {
                    "timestamp": datetime.now().isoformat(),
                    "period": period,
                    "metrics": {
                        "total_events": 0,
                        "events_per_minute": 0,
                        "processing_time_avg": 0,
                        "error_rate": 0
                    },
                    "trends": {},
                    "alerts": []
                }
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get statistics"
                )
    
    async def _check_services_simple(self) -> Dict[str, Dict[str, Any]]:
        """Check service health with simplified logic"""
        services_status = {}
        
        for service_name, service_url in self.service_urls.items():
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"{service_url}/health") as response:
                        if response.status == 200:
                            # Get detailed health data for WebSocket service
                            if service_name == "websocket-ingestion":
                                health_data = await response.json()
                                services_status[service_name] = {
                                    "status": "healthy", 
                                    "response_time": 0,
                                    "health_data": health_data
                                }
                            else:
                                services_status[service_name] = {"status": "healthy", "response_time": 0}
                        else:
                            services_status[service_name] = {"status": "unhealthy", "error": f"HTTP {response.status}"}
            except Exception as e:
                services_status[service_name] = {"status": "unhealthy", "error": str(e)}
        
        return services_status
    
    def _calculate_events_per_minute(self, websocket_health: Dict[str, Any]) -> float:
        """Calculate events per minute from event count and uptime"""
        try:
            event_count = websocket_health.get("event_count", 0)
            uptime_str = websocket_health.get("uptime", "0:00:00")
            
            if event_count == 0:
                return 0.0
            
            # Parse uptime string (format: "H:MM:SS.ffffff")
            uptime_parts = uptime_str.split(":")
            if len(uptime_parts) >= 3:
                hours = int(uptime_parts[0])
                minutes = int(uptime_parts[1])
                seconds = float(uptime_parts[2])
                
                total_minutes = hours * 60 + minutes + (seconds / 60)
                
                if total_minutes > 0:
                    return round(event_count / total_minutes, 1)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating events per minute: {e}")
            return 0.0


# Create router instance
simple_health_service = SimpleHealthService()
router = simple_health_service.router
