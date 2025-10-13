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

from shared.influxdb_query_client import InfluxDBQueryClient as AdminAPIInfluxDBClient

logger = logging.getLogger(__name__)


class StatisticsResponse(BaseModel):
    """Statistics response model"""
    timestamp: datetime
    period: str
    metrics: Dict[str, Any]
    trends: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    source: str = "influxdb"  # Add source indicator


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
        
        # InfluxDB client for querying metrics
        self.influxdb_client = AdminAPIInfluxDBClient()
        self.use_influxdb = os.getenv("USE_INFLUXDB_STATS", "true").lower() == "true"
        
        # Keep service URLs for fallback
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002")
        }
        
        self._add_routes()
    
    async def initialize(self):
        """Initialize InfluxDB connection"""
        try:
            if self.use_influxdb:
                success = await self.influxdb_client.connect()
                if not success:
                    logger.warning("InfluxDB connection failed, will use fallback")
                    self.use_influxdb = False
                else:
                    logger.info("InfluxDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize InfluxDB: {e}")
            self.use_influxdb = False
    
    async def close(self):
        """Close InfluxDB connection"""
        try:
            await self.influxdb_client.close()
        except Exception as e:
            logger.error(f"Error closing InfluxDB client: {e}")
    
    def _add_routes(self):
        """Add statistics routes"""
        
        @self.router.get("/stats", response_model=StatisticsResponse)
        async def get_statistics(
            period: str = Query("1h", description="Time period for statistics"),
            service: Optional[str] = Query(None, description="Specific service to get stats for")
        ):
            """Get comprehensive statistics from InfluxDB"""
            try:
                # Try InfluxDB first
                if self.use_influxdb and self.influxdb_client.is_connected:
                    try:
                        stats = await self._get_stats_from_influxdb(period, service)
                        return StatisticsResponse(
                            timestamp=datetime.now(),
                            period=period,
                            metrics=stats["metrics"],
                            trends=stats["trends"],
                            alerts=stats["alerts"],
                            source="influxdb"
                        )
                    except Exception as influx_error:
                        logger.warning(f"InfluxDB query failed: {influx_error}, falling back to service calls")
                
                # Fallback to direct service calls
                logger.info("Using fallback: direct service HTTP calls")
                if service and service in self.service_urls:
                    stats = await self._get_service_stats(service, period)
                else:
                    stats = await self._get_all_stats(period)
                
                return StatisticsResponse(
                    timestamp=datetime.now(),
                    period=period,
                    metrics=stats["metrics"],
                    trends=stats["trends"],
                    alerts=stats["alerts"],
                    source="services-fallback"
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
    
    async def _get_stats_from_influxdb(self, period: str, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all statistics from InfluxDB
        
        Args:
            period: Time period for statistics
            service: Optional specific service to query
        
        Returns:
            Dictionary with metrics, trends, and alerts
        """
        # Get event statistics
        event_stats = await self.influxdb_client.get_event_statistics(period)
        
        # Get error rate
        error_stats = await self.influxdb_client.get_error_rate(period)
        
        # Get service metrics
        if service:
            service_metrics = {service: await self.influxdb_client.get_service_metrics(service, period)}
        else:
            service_stats = await self.influxdb_client.get_all_service_statistics(period)
            service_metrics = service_stats.get("services", {})
        
        # Get trends
        trends = await self.influxdb_client.get_event_trends(period, window="5m")
        
        # Calculate alerts from metrics
        alerts = self._calculate_alerts(service_metrics, error_stats)
        
        return {
            "metrics": {
                **event_stats,
                **error_stats,
                "services": service_metrics
            },
            "trends": trends.get("trends", []),
            "alerts": alerts
        }
    
    def _calculate_alerts(self, service_metrics: Dict[str, Any], error_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calculate alerts from metrics
        
        Args:
            service_metrics: Service metrics dictionary
            error_stats: Error statistics dictionary
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # High error rate alert
        error_rate = error_stats.get("error_rate_percent", 0)
        if error_rate > 5:
            alerts.append({
                "level": "error",
                "service": "system",
                "message": f"High error rate: {error_rate}%",
                "timestamp": datetime.now().isoformat()
            })
        elif error_rate > 2:
            alerts.append({
                "level": "warning",
                "service": "system",
                "message": f"Elevated error rate: {error_rate}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Service health alerts
        for service, metrics in service_metrics.items():
            if isinstance(metrics, dict):
                success_rate = metrics.get("success_rate", 100)
                if success_rate < 90:
                    alerts.append({
                        "level": "error",
                        "service": service,
                        "message": f"Critical: Low success rate: {success_rate}%",
                        "timestamp": datetime.now().isoformat()
                    })
                elif success_rate < 95:
                    alerts.append({
                        "level": "warning",
                        "service": service,
                        "message": f"Low success rate: {success_rate}%",
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Check processing time
                processing_time = metrics.get("processing_time_ms", 0)
                if processing_time > 1000:  # > 1 second
                    alerts.append({
                        "level": "warning",
                        "service": service,
                        "message": f"Slow processing: {processing_time}ms",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return alerts
    
    async def _get_all_stats(self, period: str) -> Dict[str, Any]:
        """Get statistics for all services (fallback method)"""
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
                # Use different endpoints based on service
                if service_name == "enrichment-pipeline":
                    # enrichment-pipeline has /api/v1/stats
                    stats_url = f"{service_url}/api/v1/stats"
                elif service_name == "websocket-ingestion":
                    # websocket-ingestion only has /health, extract stats from it
                    stats_url = f"{service_url}/health"
                else:
                    # Default to /stats
                    stats_url = f"{service_url}/stats"
                
                async with session.get(stats_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Transform service data to stats format
                        if service_name == "websocket-ingestion":
                            return self._transform_websocket_health_to_stats(data, period)
                        elif service_name == "enrichment-pipeline":
                            return self._transform_enrichment_stats_to_stats(data, period)
                        
                        return data
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error getting stats for {service_name}: {e}")
            return {
                "metrics": {"error": str(e)},
                "trends": {},
                "alerts": [{"service": service_name, "level": "error", "message": str(e)}]
            }
    
    def _transform_websocket_health_to_stats(self, health_data: Dict[str, Any], period: str) -> Dict[str, Any]:
        """Transform websocket-ingestion health data to stats format"""
        try:
            metrics = {
                "events_per_minute": 0,
                "error_rate": 0,
                "response_time_ms": 0,
                "connection_attempts": 0,
                "total_events_received": 0
            }
            
            # Extract metrics from health data
            if "subscription" in health_data:
                subscription = health_data["subscription"]
                metrics["events_per_minute"] = subscription.get("event_rate_per_minute", 0)
                metrics["total_events_received"] = subscription.get("total_events_received", 0)
            
            if "connection" in health_data:
                connection = health_data["connection"]
                metrics["connection_attempts"] = connection.get("connection_attempts", 0)
                
                # Calculate error rate based on failed connections
                total_attempts = connection.get("connection_attempts", 0)
                failed_connections = connection.get("failed_connections", 0)
                if total_attempts > 0:
                    metrics["error_rate"] = round((failed_connections / total_attempts) * 100, 2)
            
            if "weather_enrichment" in health_data:
                weather = health_data["weather_enrichment"]
                total_processed = weather.get("total_events_processed", 0)
                failed_enrichments = weather.get("failed_enrichments", 0)
                if total_processed > 0:
                    weather_error_rate = (failed_enrichments / total_processed) * 100
                    metrics["error_rate"] = max(metrics["error_rate"], weather_error_rate)
            
            return {
                "metrics": metrics,
                "trends": {
                    "events_per_minute": [{"timestamp": health_data.get("timestamp"), "value": metrics["events_per_minute"]}],
                    "error_rate": [{"timestamp": health_data.get("timestamp"), "value": metrics["error_rate"]}]
                },
                "alerts": []
            }
            
        except Exception as e:
            logger.error(f"Error transforming websocket health to stats: {e}")
            return {
                "service": "websocket-ingestion",
                "status": "error",
                "error": str(e),
                "timestamp": health_data.get("timestamp", "")
            }
    
    def _transform_enrichment_stats_to_stats(self, stats_data: Dict[str, Any], period: str) -> Dict[str, Any]:
        """Transform enrichment-pipeline stats data to admin-api stats format"""
        try:
            metrics = {
                "events_per_minute": 0,
                "error_rate": 0,
                "response_time_ms": 0,
                "connection_attempts": 0,
                "total_events_received": 0
            }
            
            # Extract metrics from enrichment-pipeline data
            quality_metrics = stats_data.get("quality_metrics", {})
            validation_stats = stats_data.get("validation_stats", {})
            influxdb_stats = stats_data.get("influxdb", {})
            
            # Calculate events per minute from quality metrics
            if quality_metrics.get("rates", {}).get("events_per_second", 0) > 0:
                metrics["events_per_minute"] = quality_metrics["rates"]["events_per_second"] * 60
            
            # Calculate error rate from validation stats
            if validation_stats.get("validation_count", 0) > 0:
                error_count = validation_stats.get("error_count", 0)
                total_count = validation_stats.get("validation_count", 0)
                metrics["error_rate"] = round((error_count / total_count) * 100, 2)
            
            # Use InfluxDB write errors as connection attempts metric
            metrics["connection_attempts"] = influxdb_stats.get("points_written", 0)
            
            # Total events from quality metrics
            metrics["total_events_received"] = quality_metrics.get("totals", {}).get("total_events", 0)
            
            # Response time from performance metrics
            metrics["response_time_ms"] = quality_metrics.get("performance", {}).get("avg_validation_time_ms", 0)
            
            return {
                "metrics": metrics,
                "trends": {
                    "events_per_minute": [{"timestamp": stats_data.get("timestamp"), "value": metrics["events_per_minute"]}],
                    "error_rate": [{"timestamp": stats_data.get("timestamp"), "value": metrics["error_rate"]}]
                },
                "alerts": []
            }
            
        except Exception as e:
            logger.error(f"Error transforming enrichment stats: {e}")
            return {
                "service": "enrichment-pipeline",
                "status": "error",
                "error": str(e),
                "timestamp": stats_data.get("timestamp", "")
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
