"""
Data Quality Dashboard Backend API
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from aiohttp import web
import json

logger = logging.getLogger(__name__)


class QualityDashboardAPI:
    """Quality dashboard backend API endpoints"""
    
    def __init__(self, quality_metrics_tracker, alert_manager, data_validator):
        self.quality_metrics = quality_metrics_tracker
        self.alert_manager = alert_manager
        self.data_validator = data_validator
        
        # Dashboard configuration
        self.dashboard_config = {
            "refresh_interval": 30,  # seconds
            "max_entities_display": 100,
            "max_alerts_display": 50,
            "trend_period_hours": 24
        }
    
    def setup_routes(self, app: web.Application):
        """Setup quality dashboard API routes"""
        
        # Quality metrics endpoints
        app.router.add_get('/api/quality/current', self.get_current_metrics)
        app.router.add_get('/api/quality/report', self.get_quality_report)
        app.router.add_get('/api/quality/trends', self.get_quality_trends)
        app.router.add_get('/api/quality/entities', self.get_entity_quality)
        app.router.add_get('/api/quality/entity/{entity_id}', self.get_entity_details)
        
        # Alert endpoints
        app.router.add_get('/api/quality/alerts', self.get_active_alerts)
        app.router.add_get('/api/quality/alerts/history', self.get_alert_history)
        app.router.add_get('/api/quality/alerts/statistics', self.get_alert_statistics)
        app.router.add_post('/api/quality/alerts/{alert_id}/acknowledge', self.acknowledge_alert)
        app.router.add_post('/api/quality/alerts/{alert_id}/resolve', self.resolve_alert)
        app.router.add_post('/api/quality/alerts/{alert_id}/suppress', self.suppress_alert)
        
        # Dashboard configuration endpoints
        app.router.add_get('/api/quality/config', self.get_dashboard_config)
        app.router.add_put('/api/quality/config', self.update_dashboard_config)
        app.router.add_get('/api/quality/thresholds', self.get_quality_thresholds)
        app.router.add_put('/api/quality/thresholds', self.update_quality_thresholds)
        
        # Health and status endpoints
        app.router.add_get('/api/quality/health', self.get_quality_health)
        app.router.add_get('/api/quality/status', self.get_quality_status)
        
        # Export endpoints
        app.router.add_get('/api/quality/export/report', self.export_quality_report)
        app.router.add_get('/api/quality/export/alerts', self.export_alert_history)
    
    async def get_current_metrics(self, request: web.Request) -> web.Response:
        """Get current quality metrics"""
        try:
            metrics = self.quality_metrics.get_metrics()
            return web.json_response({
                "success": True,
                "data": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_quality_report(self, request: web.Request) -> web.Response:
        """Get comprehensive quality report"""
        try:
            report = self.quality_metrics.get_quality_report()
            return web.json_response({
                "success": True,
                "data": report,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting quality report: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_quality_trends(self, request: web.Request) -> web.Response:
        """Get quality trends over time"""
        try:
            # Get trend period from query parameter
            hours = int(request.query.get('hours', self.dashboard_config['trend_period_hours']))
            
            # Get metrics history for trend analysis
            report = self.quality_metrics.get_quality_report()
            trend_metrics = report.get('trend_metrics', {})
            
            # Add additional trend data
            trends = {
                "period_hours": hours,
                "trend_metrics": trend_metrics,
                "current_metrics": report.get('current_metrics', {}),
                "quality_score_history": self._get_quality_score_history(hours),
                "error_rate_history": self._get_error_rate_history(hours),
                "processing_latency_history": self._get_processing_latency_history(hours)
            }
            
            return web.json_response({
                "success": True,
                "data": trends,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_entity_quality(self, request: web.Request) -> web.Response:
        """Get entity quality metrics"""
        try:
            # Get query parameters
            limit = int(request.query.get('limit', self.dashboard_config['max_entities_display']))
            sort_by = request.query.get('sort_by', 'quality_score')
            order = request.query.get('order', 'asc')
            
            report = self.quality_metrics.get_quality_report()
            entity_quality = report.get('entity_quality', {})
            
            # Convert to list and sort
            entities = [
                {
                    "entity_id": entity_id,
                    **metrics
                }
                for entity_id, metrics in entity_quality.items()
            ]
            
            # Sort entities
            reverse = order.lower() == 'desc'
            if sort_by == 'quality_score':
                entities.sort(key=lambda x: x.get('quality_score', 0), reverse=reverse)
            elif sort_by == 'total_events':
                entities.sort(key=lambda x: x.get('total_events', 0), reverse=reverse)
            elif sort_by == 'invalid_events':
                entities.sort(key=lambda x: x.get('invalid_events', 0), reverse=reverse)
            
            # Apply limit
            entities = entities[:limit]
            
            return web.json_response({
                "success": True,
                "data": {
                    "entities": entities,
                    "total_entities": len(entity_quality),
                    "displayed_entities": len(entities)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting entity quality: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_entity_details(self, request: web.Request) -> web.Response:
        """Get detailed quality metrics for a specific entity"""
        try:
            entity_id = request.match_info['entity_id']
            
            entity_metrics = self.quality_metrics.get_entity_quality(entity_id)
            if not entity_metrics:
                return web.json_response({
                    "success": False,
                    "error": f"Entity not found: {entity_id}"
                }, status=404)
            
            # Get validation statistics for this entity
            validation_stats = self.data_validator.get_validation_statistics()
            
            return web.json_response({
                "success": True,
                "data": {
                    "entity_metrics": entity_metrics,
                    "validation_stats": validation_stats
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_active_alerts(self, request: web.Request) -> web.Response:
        """Get active quality alerts"""
        try:
            alerts = self.alert_manager.get_active_alerts()
            
            # Apply limit
            limit = int(request.query.get('limit', self.dashboard_config['max_alerts_display']))
            alerts = alerts[:limit]
            
            return web.json_response({
                "success": True,
                "data": {
                    "alerts": alerts,
                    "total_alerts": len(alerts)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_alert_history(self, request: web.Request) -> web.Response:
        """Get alert history"""
        try:
            limit = int(request.query.get('limit', 100))
            alerts = self.alert_manager.get_alert_history(limit)
            
            return web.json_response({
                "success": True,
                "data": {
                    "alerts": alerts,
                    "total_alerts": len(alerts)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting alert history: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_alert_statistics(self, request: web.Request) -> web.Response:
        """Get alert statistics"""
        try:
            stats = self.alert_manager.get_alert_statistics()
            
            return web.json_response({
                "success": True,
                "data": stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def acknowledge_alert(self, request: web.Request) -> web.Response:
        """Acknowledge an alert"""
        try:
            alert_id = request.match_info['alert_id']
            data = await request.json()
            acknowledged_by = data.get('acknowledged_by', 'unknown')
            
            success = self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": f"Alert {alert_id} acknowledged"
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Alert not found: {alert_id}"
                }, status=404)
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def resolve_alert(self, request: web.Request) -> web.Response:
        """Resolve an alert"""
        try:
            alert_id = request.match_info['alert_id']
            
            success = self.alert_manager.resolve_alert(alert_id)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": f"Alert {alert_id} resolved"
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Alert not found: {alert_id}"
                }, status=404)
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def suppress_alert(self, request: web.Request) -> web.Response:
        """Suppress an alert"""
        try:
            alert_id = request.match_info['alert_id']
            data = await request.json()
            
            # Parse suppress_until timestamp
            suppress_until_str = data.get('suppress_until')
            if not suppress_until_str:
                return web.json_response({
                    "success": False,
                    "error": "suppress_until timestamp required"
                }, status=400)
            
            suppress_until = datetime.fromisoformat(suppress_until_str.replace('Z', '+00:00'))
            
            success = self.alert_manager.suppress_alert(alert_id, suppress_until)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": f"Alert {alert_id} suppressed until {suppress_until.isoformat()}"
                })
            else:
                return web.json_response({
                    "success": False,
                    "error": f"Alert not found: {alert_id}"
                }, status=404)
        except Exception as e:
            logger.error(f"Error suppressing alert: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_dashboard_config(self, request: web.Request) -> web.Response:
        """Get dashboard configuration"""
        try:
            return web.json_response({
                "success": True,
                "data": self.dashboard_config,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting dashboard config: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def update_dashboard_config(self, request: web.Request) -> web.Response:
        """Update dashboard configuration"""
        try:
            data = await request.json()
            
            # Validate and update configuration
            for key, value in data.items():
                if key in self.dashboard_config:
                    self.dashboard_config[key] = value
            
            return web.json_response({
                "success": True,
                "data": self.dashboard_config,
                "message": "Dashboard configuration updated"
            })
        except Exception as e:
            logger.error(f"Error updating dashboard config: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_quality_thresholds(self, request: web.Request) -> web.Response:
        """Get quality thresholds"""
        try:
            thresholds = self.quality_metrics.quality_thresholds
            
            return web.json_response({
                "success": True,
                "data": thresholds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting quality thresholds: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def update_quality_thresholds(self, request: web.Request) -> web.Response:
        """Update quality thresholds"""
        try:
            data = await request.json()
            
            # Update thresholds
            self.quality_metrics.set_quality_thresholds(data)
            
            return web.json_response({
                "success": True,
                "data": self.quality_metrics.quality_thresholds,
                "message": "Quality thresholds updated"
            })
        except Exception as e:
            logger.error(f"Error updating quality thresholds: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_quality_health(self, request: web.Request) -> web.Response:
        """Get quality system health status"""
        try:
            health_status = self.quality_metrics.get_health_status()
            
            return web.json_response({
                "success": True,
                "data": health_status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting quality health: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def get_quality_status(self, request: web.Request) -> web.Response:
        """Get comprehensive quality status"""
        try:
            # Get current metrics
            current_metrics = self.quality_metrics.get_metrics()
            
            # Get health status
            health_status = self.quality_metrics.get_health_status()
            
            # Get active alerts count
            active_alerts = self.alert_manager.get_active_alerts()
            
            # Get validation statistics
            validation_stats = self.data_validator.get_validation_statistics()
            
            status = {
                "current_metrics": current_metrics,
                "health_status": health_status,
                "active_alerts_count": len(active_alerts),
                "validation_stats": validation_stats,
                "system_status": "healthy" if health_status["status"] == "healthy" else "degraded"
            }
            
            return web.json_response({
                "success": True,
                "data": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting quality status: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def export_quality_report(self, request: web.Request) -> web.Response:
        """Export quality report as JSON"""
        try:
            report = self.quality_metrics.get_quality_report()
            
            # Create filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"quality_report_{timestamp}.json"
            
            # Set response headers for file download
            response = web.Response(
                body=json.dumps(report, indent=2),
                headers={
                    'Content-Type': 'application/json',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
            
            return response
        except Exception as e:
            logger.error(f"Error exporting quality report: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def export_alert_history(self, request: web.Request) -> web.Response:
        """Export alert history as JSON"""
        try:
            limit = int(request.query.get('limit', 1000))
            alerts = self.alert_manager.get_alert_history(limit)
            
            # Create filename with timestamp
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"alert_history_{timestamp}.json"
            
            # Set response headers for file download
            response = web.Response(
                body=json.dumps(alerts, indent=2),
                headers={
                    'Content-Type': 'application/json',
                    'Content-Disposition': f'attachment; filename="{filename}"'
                }
            )
            
            return response
        except Exception as e:
            logger.error(f"Error exporting alert history: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    def _get_quality_score_history(self, hours: int) -> List[Dict[str, Any]]:
        """Get quality score history (mock implementation)"""
        # This would typically query historical data
        # For now, return mock data
        return [
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                "quality_score": 95.0 + (i % 5) - 2.5  # Mock varying scores
            }
            for i in range(hours)
        ]
    
    def _get_error_rate_history(self, hours: int) -> List[Dict[str, Any]]:
        """Get error rate history (mock implementation)"""
        return [
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                "error_rate": 0.5 + (i % 3) * 0.2  # Mock varying error rates
            }
            for i in range(hours)
        ]
    
    def _get_processing_latency_history(self, hours: int) -> List[Dict[str, Any]]:
        """Get processing latency history (mock implementation)"""
        return [
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
                "processing_latency": 200 + (i % 4) * 50  # Mock varying latencies
            }
            for i in range(hours)
        ]
