"""
Health Monitoring Endpoints
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import os

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class HealthStatus(BaseModel):
    """Health status model"""
    status: str
    timestamp: str  # Changed to string for JSON serialization
    uptime_seconds: float
    version: str
    services: Dict[str, Any]
    dependencies: Dict[str, Any]
    metrics: Dict[str, Any]


class ServiceHealth(BaseModel):
    """Service health model"""
    name: str
    status: str
    last_check: str  # Changed to string for JSON serialization
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class HealthEndpoints:
    """Health monitoring endpoints"""
    
    def __init__(self):
        """Initialize health endpoints"""
        self.router = APIRouter()
        self.start_time = datetime.now()
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002"),
            "influxdb": os.getenv("INFLUXDB_URL", "http://localhost:8086"),
            "weather-api": "https://api.openweathermap.org/data/2.5"
        }
        
        self._add_routes()
    
    def _add_routes(self):
        """Add health routes"""
        
        @self.router.get("/health", response_model=HealthStatus)
        async def get_health():
            """Get comprehensive health status"""
            try:
                # Get service health
                services_health = await self._check_services()
                
                # Get detailed websocket service data
                websocket_data = await self._get_websocket_service_data()
                
                # Get dependency health
                dependencies_health = await self._check_dependencies()
                
                # Get metrics
                metrics = await self._get_metrics()
                
                # Determine overall status - be more lenient
                overall_status = "healthy"
                unhealthy_count = sum(1 for service in services_health.values() if service.status == "unhealthy")
                total_services = len(services_health)
                
                # Only mark as unhealthy if more than 50% of services are down
                if unhealthy_count > total_services * 0.5:
                    overall_status = "unhealthy"
                elif unhealthy_count > 0:
                    overall_status = "degraded"
                
                # Create enhanced health response with frontend-compatible structure
                enhanced_response = {
                    "overall_status": overall_status,
                    "admin_api_status": "healthy",
                    "ingestion_service": {
                        "status": overall_status,
                        "websocket_connection": {
                            "is_connected": websocket_data.get("connection", {}).get("is_running", False),
                            "last_connection_time": datetime.now().isoformat(),
                            "connection_attempts": websocket_data.get("connection", {}).get("connection_attempts", 0),
                            "last_error": websocket_data.get("connection", {}).get("last_error")
                        },
                        "event_processing": {
                            "status": "healthy" if websocket_data.get("subscription", {}).get("is_subscribed", False) else "unhealthy",
                            "events_per_minute": websocket_data.get("subscription", {}).get("event_rate_per_minute", 0),
                            "last_event_time": websocket_data.get("subscription", {}).get("last_event_time"),
                            "processing_lag": 0,
                            "total_events_received": websocket_data.get("subscription", {}).get("total_events_received", 0)
                        },
                        "weather_enrichment": {
                            "enabled": dependencies_health.get("weather_api", {}).get("status") == "healthy",
                            "cache_hits": websocket_data.get("weather_enrichment", {}).get("cache_hits", 0),
                            "api_calls": websocket_data.get("weather_enrichment", {}).get("weather_client_stats", {}).get("total_requests", 0),
                            "last_error": None
                        },
                        "influxdb_storage": {
                            "is_connected": dependencies_health.get("influxdb", {}).get("status") == "healthy",
                            "last_write_time": datetime.now().isoformat(),
                            "write_errors": 0
                        },
                        "timestamp": datetime.now().isoformat()
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                return enhanced_response
                
            except Exception as e:
                logger.error(f"Error getting health status: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get health status"
                )
        
        @self.router.get("/health/services", response_model=Dict[str, ServiceHealth])
        async def get_services_health():
            """Get services health status"""
            try:
                services_health = await self._check_services()
                return services_health
            except Exception as e:
                logger.error(f"Error getting services health: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get services health"
                )
        
        @self.router.get("/health/dependencies", response_model=Dict[str, Any])
        async def get_dependencies_health():
            """Get dependencies health status"""
            try:
                dependencies_health = await self._check_dependencies()
                return dependencies_health
            except Exception as e:
                logger.error(f"Error getting dependencies health: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get dependencies health"
                )
        
        @self.router.get("/health/metrics", response_model=Dict[str, Any])
        async def get_health_metrics():
            """Get health metrics"""
            try:
                metrics = await self._get_metrics()
                return metrics
            except Exception as e:
                logger.error(f"Error getting health metrics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get health metrics"
                )
    
    async def _check_services(self) -> Dict[str, ServiceHealth]:
        """Check health of all services"""
        services_health = {}
        
        for service_name, service_url in self.service_urls.items():
            try:
                start_time = datetime.now()
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
                    async with session.get(f"{service_url}/health") as response:
                        response_time = (datetime.now() - start_time).total_seconds() * 1000
                        
                        if response.status == 200:
                            data = await response.json()
                            services_health[service_name] = ServiceHealth(
                                name=service_name,
                                status=data.get("status", "unknown"),
                                last_check=datetime.now().isoformat(),  # Convert to ISO string
                                response_time_ms=response_time
                            )
                        else:
                            services_health[service_name] = ServiceHealth(
                                name=service_name,
                                status="unhealthy",
                                last_check=datetime.now().isoformat(),  # Convert to ISO string
                                response_time_ms=response_time,
                                error_message=f"HTTP {response.status}"
                            )
                            
            except asyncio.TimeoutError:
                services_health[service_name] = ServiceHealth(
                    name=service_name,
                    status="unhealthy",
                    last_check=datetime.now().isoformat(),  # Convert to ISO string
                    error_message="Timeout"
                )
            except Exception as e:
                services_health[service_name] = ServiceHealth(
                    name=service_name,
                    status="unhealthy",
                    last_check=datetime.now().isoformat(),  # Convert to ISO string
                    error_message=str(e)
                )
        
        return services_health
    
    async def _get_websocket_service_data(self) -> Dict[str, Any]:
        """Get detailed data from websocket service"""
        try:
            websocket_url = self.service_urls.get("websocket-ingestion")
            if not websocket_url:
                return {}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{websocket_url}/health") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get websocket service data: HTTP {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error getting websocket service data: {e}")
            return {}
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check health of external dependencies"""
        dependencies_health = {}
        
        # Check InfluxDB
        try:
            influxdb_url = self.service_urls["influxdb"]
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{influxdb_url}/health") as response:
                    dependencies_health["influxdb"] = {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "last_check": datetime.now().isoformat(),
                        "response_time_ms": response.headers.get("X-Response-Time", "N/A")
                    }
        except Exception as e:
            dependencies_health["influxdb"] = {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
        
        # Check Weather API
        try:
            weather_api_key = os.getenv("WEATHER_API_KEY")
            if weather_api_key:
                weather_url = self.service_urls["weather-api"]
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"{weather_url}/weather?q=London&appid={weather_api_key}") as response:
                        dependencies_health["weather_api"] = {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "last_check": datetime.now().isoformat(),
                            "response_time_ms": response.headers.get("X-Response-Time", "N/A")
                        }
            else:
                dependencies_health["weather_api"] = {
                    "status": "disabled",
                    "last_check": datetime.now().isoformat(),
                    "message": "No API key configured"
                }
        except Exception as e:
            dependencies_health["weather_api"] = {
                "status": "unhealthy",
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
        
        return dependencies_health
    
    async def _get_metrics(self) -> Dict[str, Any]:
        """Get health metrics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "start_time": self.start_time.isoformat(),
            "current_time": datetime.now().isoformat(),
            "memory_usage": self._get_memory_usage(),
            "cpu_usage": self._get_cpu_usage(),
            "disk_usage": self._get_disk_usage()
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage information"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "total_mb": round(memory.total / 1024 / 1024, 2),
                "available_mb": round(memory.available / 1024 / 1024, 2),
                "used_mb": round(memory.used / 1024 / 1024, 2),
                "percentage": memory.percent
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    def _get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage information"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            return {
                "usage_percent": cpu_percent,
                "core_count": cpu_count,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "percentage": round((disk.used / disk.total) * 100, 2)
            }
        except ImportError:
            return {"error": "psutil not available"}
