"""
Statistics and Metrics Endpoints
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import os

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StatisticsResponse(BaseModel):
    """Statistics response model"""
    timestamp: datetime
    period: str
    metrics: Dict[str, Any]
    trends: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class MetricData(BaseModel):
    """Metric data model"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = {}


class StatsEndpoints:
    """Statistics and metrics endpoints"""
    
    def __init__(self):
        """Initialize stats endpoints"""
        self.router = APIRouter()
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002")
        }
        
        self._add_routes()
    
    def _add_routes(self):
        """Add statistics routes"""
        
        @self.router.get("/stats", response_model=StatisticsResponse)
        async def get_statistics(
            period: str = Query("1h", description="Time period for statistics"),
            service: Optional[str] = Query(None, description="Specific service to get stats for")
        ):
            """Get comprehensive statistics"""
            try:
                if service and service in self.service_urls:
                    # Get stats for specific service
                    stats = await self._get_service_stats(service, period)
                else:
                    # Get stats for all services
                    stats = await self._get_all_stats(period)
                
                return StatisticsResponse(
                    timestamp=datetime.now(),
                    period=period,
                    metrics=stats["metrics"],
                    trends=stats["trends"],
                    alerts=stats["alerts"]
                )
                
            except Exception as e:
                logger.error(f"Error getting statistics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get statistics"
                )
        
        @self.router.get("/stats/services", response_model=Dict[str, Any])
        async def get_services_stats():
            """Get statistics for all services"""
            try:
                all_stats = {}
                
                for service_name, service_url in self.service_urls.items():
                    try:
                        stats = await self._get_service_stats(service_name, "1h")
                        all_stats[service_name] = stats
                    except Exception as e:
                        logger.warning(f"Failed to get stats for {service_name}: {e}")
                        all_stats[service_name] = {"error": str(e)}
                
                return all_stats
                
            except Exception as e:
                logger.error(f"Error getting services statistics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get services statistics"
                )
        
        @self.router.get("/stats/metrics", response_model=List[MetricData])
        async def get_metrics(
            metric_name: Optional[str] = Query(None, description="Specific metric name"),
            service: Optional[str] = Query(None, description="Specific service"),
            limit: int = Query(100, description="Maximum number of metrics to return")
        ):
            """Get specific metrics"""
            try:
                metrics = await self._get_metrics(metric_name, service, limit)
                return metrics
                
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get metrics"
                )
        
        @self.router.get("/stats/performance", response_model=Dict[str, Any])
        async def get_performance_stats():
            """Get performance statistics"""
            try:
                performance_stats = await self._get_performance_stats()
                return performance_stats
                
            except Exception as e:
                logger.error(f"Error getting performance statistics: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get performance statistics"
                )
        
        @self.router.get("/stats/alerts", response_model=List[Dict[str, Any]])
        async def get_alerts():
            """Get active alerts"""
            try:
                alerts = await self._get_alerts()
                return alerts
                
            except Exception as e:
                logger.error(f"Error getting alerts: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get alerts"
                )
    
    async def _get_all_stats(self, period: str) -> Dict[str, Any]:
        """Get statistics for all services"""
        all_stats = {
            "metrics": {},
            "trends": {},
            "alerts": []
        }
        
        for service_name, service_url in self.service_urls.items():
            try:
                service_stats = await self._get_service_stats(service_name, period)
                all_stats["metrics"][service_name] = service_stats["metrics"]
                all_stats["trends"][service_name] = service_stats["trends"]
                all_stats["alerts"].extend(service_stats["alerts"])
            except Exception as e:
                logger.warning(f"Failed to get stats for {service_name}: {e}")
                all_stats["metrics"][service_name] = {"error": str(e)}
        
        return all_stats
    
    async def _get_service_stats(self, service_name: str, period: str) -> Dict[str, Any]:
        """Get statistics for a specific service"""
        service_url = self.service_urls[service_name]
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{service_url}/stats?period={period}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error getting stats for {service_name}: {e}")
            return {
                "metrics": {"error": str(e)},
                "trends": {},
                "alerts": [{"service": service_name, "level": "error", "message": str(e)}]
            }
    
    async def _get_metrics(self, metric_name: Optional[str], service: Optional[str], limit: int) -> List[MetricData]:
        """Get specific metrics"""
        metrics = []
        
        services_to_check = [service] if service else list(self.service_urls.keys())
        
        for service_name in services_to_check:
            if service_name not in self.service_urls:
                continue
                
            try:
                service_url = self.service_urls[service_name]
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    params = {"limit": limit}
                    if metric_name:
                        params["metric"] = metric_name
                    
                    async with session.get(f"{service_url}/metrics", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            for metric in data:
                                metrics.append(MetricData(
                                    name=metric["name"],
                                    value=metric["value"],
                                    unit=metric.get("unit", ""),
                                    timestamp=datetime.fromisoformat(metric["timestamp"]),
                                    tags={**metric.get("tags", {}), "service": service_name}
                                ))
            except Exception as e:
                logger.warning(f"Failed to get metrics for {service_name}: {e}")
        
        return metrics[:limit]
    
    async def _get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        performance_stats = {
            "overall": {},
            "services": {},
            "recommendations": []
        }
        
        for service_name, service_url in self.service_urls.items():
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{service_url}/stats/performance") as response:
                        if response.status == 200:
                            data = await response.json()
                            performance_stats["services"][service_name] = data
                        else:
                            performance_stats["services"][service_name] = {"error": f"HTTP {response.status}"}
            except Exception as e:
                logger.warning(f"Failed to get performance stats for {service_name}: {e}")
                performance_stats["services"][service_name] = {"error": str(e)}
        
        # Calculate overall performance metrics
        performance_stats["overall"] = self._calculate_overall_performance(performance_stats["services"])
        
        # Generate recommendations
        performance_stats["recommendations"] = self._generate_recommendations(performance_stats["services"])
        
        return performance_stats
    
    async def _get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        alerts = []
        
        for service_name, service_url in self.service_urls.items():
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{service_url}/alerts") as response:
                        if response.status == 200:
                            data = await response.json()
                            for alert in data:
                                alert["service"] = service_name
                                alerts.append(alert)
            except Exception as e:
                logger.warning(f"Failed to get alerts for {service_name}: {e}")
                alerts.append({
                    "service": service_name,
                    "level": "error",
                    "message": f"Failed to get alerts: {e}",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Sort alerts by severity and timestamp
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        alerts.sort(key=lambda x: (severity_order.get(x.get("level", "info"), 3), x.get("timestamp", "")))
        
        return alerts
    
    def _calculate_overall_performance(self, services_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall performance metrics"""
        overall = {
            "total_requests": 0,
            "total_errors": 0,
            "average_response_time": 0,
            "success_rate": 0,
            "throughput": 0
        }
        
        valid_services = 0
        
        for service_name, stats in services_stats.items():
            if "error" in stats:
                continue
                
            valid_services += 1
            
            # Aggregate metrics
            overall["total_requests"] += stats.get("total_requests", 0)
            overall["total_errors"] += stats.get("total_errors", 0)
            overall["average_response_time"] += stats.get("average_response_time", 0)
            overall["throughput"] += stats.get("throughput", 0)
        
        if valid_services > 0:
            overall["average_response_time"] /= valid_services
            
            if overall["total_requests"] > 0:
                overall["success_rate"] = ((overall["total_requests"] - overall["total_errors"]) / overall["total_requests"]) * 100
        
        return overall
    
    def _generate_recommendations(self, services_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance recommendations"""
        recommendations = []
        
        for service_name, stats in services_stats.items():
            if "error" in stats:
                continue
            
            # Check response time
            if stats.get("average_response_time", 0) > 1000:  # > 1 second
                recommendations.append({
                    "service": service_name,
                    "type": "performance",
                    "level": "warning",
                    "message": f"High response time: {stats.get('average_response_time', 0):.2f}ms",
                    "recommendation": "Consider optimizing database queries or increasing resources"
                })
            
            # Check error rate
            success_rate = stats.get("success_rate", 100)
            if success_rate < 95:
                recommendations.append({
                    "service": service_name,
                    "type": "reliability",
                    "level": "error",
                    "message": f"Low success rate: {success_rate:.2f}%",
                    "recommendation": "Investigate error causes and improve error handling"
                })
            
            # Check throughput
            throughput = stats.get("throughput", 0)
            if throughput < 10:  # < 10 requests per second
                recommendations.append({
                    "service": service_name,
                    "type": "capacity",
                    "level": "info",
                    "message": f"Low throughput: {throughput:.2f} req/s",
                    "recommendation": "Consider scaling up or optimizing processing"
                })
        
        return recommendations
