"""
Tests for Quality Dashboard API
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock
from aiohttp import web
from datetime import datetime, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quality_dashboard import QualityDashboardAPI


class TestQualityDashboardAPI:
    """Test cases for QualityDashboardAPI"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.quality_metrics = Mock()
        self.alert_manager = Mock()
        self.data_validator = Mock()
        
        self.dashboard_api = QualityDashboardAPI(
            self.quality_metrics,
            self.alert_manager,
            self.data_validator
        )
    
    def test_setup_routes(self):
        """Test setting up dashboard routes"""
        app = web.Application()
        
        # Should not raise exception
        self.dashboard_api.setup_routes(app)
        
        # Check that routes were added (basic check)
        assert len(app.router._resources) > 0
    
    @pytest.mark.asyncio
    async def test_get_current_metrics(self):
        """Test getting current metrics endpoint"""
        # Mock metrics data
        mock_metrics = {
            "total_events": 100,
            "valid_events": 95,
            "quality_score": 95.0
        }
        self.quality_metrics.get_current_metrics.return_value = mock_metrics
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_current_metrics(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert response_data["data"] == mock_metrics
        assert "timestamp" in response_data
    
    @pytest.mark.asyncio
    async def test_get_quality_report(self):
        """Test getting quality report endpoint"""
        # Mock report data
        mock_report = {
            "current_metrics": {"total_events": 100},
            "trend_metrics": {"quality_trend": "stable"},
            "entity_quality": {"sensor.temp": {"quality_score": 95.0}}
        }
        self.quality_metrics.get_quality_report.return_value = mock_report
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_quality_report(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert response_data["data"] == mock_report
    
    @pytest.mark.asyncio
    async def test_get_entity_quality(self):
        """Test getting entity quality endpoint"""
        # Mock entity quality data
        mock_entity_quality = {
            "sensor.temperature": {
                "entity_id": "sensor.temperature",
                "total_events": 50,
                "valid_events": 48,
                "quality_score": 96.0
            },
            "sensor.humidity": {
                "entity_id": "sensor.humidity",
                "total_events": 30,
                "valid_events": 29,
                "quality_score": 96.7
            }
        }
        
        mock_report = {
            "entity_quality": mock_entity_quality,
            "problematic_entities": []
        }
        self.quality_metrics.get_quality_report.return_value = mock_report
        
        # Create request
        request = Mock()
        request.query = {"limit": "10", "sort_by": "quality_score", "order": "desc"}
        
        # Call endpoint
        response = await self.dashboard_api.get_entity_quality(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "entities" in response_data["data"]
        assert response_data["data"]["total_entities"] == 2
    
    @pytest.mark.asyncio
    async def test_get_entity_details(self):
        """Test getting entity details endpoint"""
        # Mock entity metrics
        mock_entity_metrics = {
            "entity_id": "sensor.temperature",
            "total_events": 50,
            "valid_events": 48,
            "quality_score": 96.0
        }
        self.quality_metrics.get_entity_quality.return_value = mock_entity_metrics
        
        # Mock validation stats
        mock_validation_stats = {
            "total_validations": 100,
            "success_rate": 95.0
        }
        self.data_validator.get_validation_statistics.return_value = mock_validation_stats
        
        # Create request
        request = Mock()
        request.match_info = {"entity_id": "sensor.temperature"}
        
        # Call endpoint
        response = await self.dashboard_api.get_entity_details(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert response_data["data"]["entity_metrics"] == mock_entity_metrics
        assert response_data["data"]["validation_stats"] == mock_validation_stats
    
    @pytest.mark.asyncio
    async def test_get_entity_details_not_found(self):
        """Test getting entity details for non-existent entity"""
        # Mock entity not found
        self.quality_metrics.get_entity_quality.return_value = None
        
        # Create request
        request = Mock()
        request.match_info = {"entity_id": "nonexistent.sensor"}
        
        # Call endpoint
        response = await self.dashboard_api.get_entity_details(request)
        
        # Check response
        assert response.status == 404
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is False
        assert "not found" in response_data["error"]
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self):
        """Test getting active alerts endpoint"""
        # Mock active alerts
        mock_alerts = [
            {
                "alert_id": "alert_1",
                "alert_type": "low_quality_score",
                "severity": "warning",
                "message": "Quality score below threshold",
                "timestamp": "2024-12-19T15:30:00Z"
            },
            {
                "alert_id": "alert_2",
                "alert_type": "high_error_rate",
                "severity": "critical",
                "message": "Error rate above threshold",
                "timestamp": "2024-12-19T15:31:00Z"
            }
        ]
        self.alert_manager.get_active_alerts.return_value = mock_alerts
        
        # Create request
        request = Mock()
        request.query = {"limit": "5"}
        
        # Call endpoint
        response = await self.dashboard_api.get_active_alerts(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert response_data["data"]["alerts"] == mock_alerts
        assert response_data["data"]["total_alerts"] == 2
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self):
        """Test acknowledging an alert"""
        # Mock successful acknowledgment
        self.alert_manager.acknowledge_alert.return_value = True
        
        # Create request
        request = Mock()
        request.match_info = {"alert_id": "test_alert_id"}
        request.json = AsyncMock(return_value={"acknowledged_by": "test_user"})
        
        # Call endpoint
        response = await self.dashboard_api.acknowledge_alert(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "acknowledged" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self):
        """Test acknowledging non-existent alert"""
        # Mock failed acknowledgment
        self.alert_manager.acknowledge_alert.return_value = False
        
        # Create request
        request = Mock()
        request.match_info = {"alert_id": "nonexistent_alert"}
        request.json = AsyncMock(return_value={"acknowledged_by": "test_user"})
        
        # Call endpoint
        response = await self.dashboard_api.acknowledge_alert(request)
        
        # Check response
        assert response.status == 404
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is False
        assert "not found" in response_data["error"]
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self):
        """Test resolving an alert"""
        # Mock successful resolution
        self.alert_manager.resolve_alert.return_value = True
        
        # Create request
        request = Mock()
        request.match_info = {"alert_id": "test_alert_id"}
        
        # Call endpoint
        response = await self.dashboard_api.resolve_alert(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "resolved" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_suppress_alert(self):
        """Test suppressing an alert"""
        # Mock successful suppression
        self.alert_manager.suppress_alert.return_value = True
        
        # Create request
        request = Mock()
        request.match_info = {"alert_id": "test_alert_id"}
        request.json = AsyncMock(return_value={
            "suppress_until": "2024-12-19T16:30:00Z"
        })
        
        # Call endpoint
        response = await self.dashboard_api.suppress_alert(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "suppressed" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_suppress_alert_missing_timestamp(self):
        """Test suppressing alert without timestamp"""
        # Create request without suppress_until
        request = Mock()
        request.match_info = {"alert_id": "test_alert_id"}
        request.json = AsyncMock(return_value={})  # Missing suppress_until
        
        # Call endpoint
        response = await self.dashboard_api.suppress_alert(request)
        
        # Check response
        assert response.status == 400
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is False
        assert "suppress_until" in response_data["error"]
    
    @pytest.mark.asyncio
    async def test_get_quality_health(self):
        """Test getting quality health endpoint"""
        # Mock health status
        mock_health = {
            "status": "healthy",
            "health_issues": [],
            "active_alerts": 0,
            "total_entities": 10
        }
        self.quality_metrics.get_health_status.return_value = mock_health
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_quality_health(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert response_data["data"] == mock_health
    
    @pytest.mark.asyncio
    async def test_get_quality_status(self):
        """Test getting comprehensive quality status"""
        # Mock various status data
        mock_current_metrics = {"total_events": 100, "quality_score": 95.0}
        mock_health_status = {"status": "healthy", "health_issues": []}
        mock_active_alerts = [{"alert_id": "alert_1", "message": "Test alert"}]
        mock_validation_stats = {"total_validations": 100, "success_rate": 95.0}
        
        self.quality_metrics.get_current_metrics.return_value = mock_current_metrics
        self.quality_metrics.get_health_status.return_value = mock_health_status
        self.alert_manager.get_active_alerts.return_value = mock_active_alerts
        self.data_validator.get_validation_statistics.return_value = mock_validation_stats
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_quality_status(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "current_metrics" in response_data["data"]
        assert "health_status" in response_data["data"]
        assert "active_alerts_count" in response_data["data"]
        assert "validation_stats" in response_data["data"]
        assert "system_status" in response_data["data"]
    
    @pytest.mark.asyncio
    async def test_export_quality_report(self):
        """Test exporting quality report"""
        # Mock report data
        mock_report = {
            "current_metrics": {"total_events": 100},
            "summary": {"overall_quality_score": 95.0}
        }
        self.quality_metrics.get_quality_report.return_value = mock_report
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.export_quality_report(request)
        
        # Check response
        assert response.status == 200
        assert response.headers["Content-Type"] == "application/json"
        assert "attachment" in response.headers["Content-Disposition"]
        assert "quality_report_" in response.headers["Content-Disposition"]
    
    @pytest.mark.asyncio
    async def test_export_alert_history(self):
        """Test exporting alert history"""
        # Mock alert history
        mock_alerts = [
            {"alert_id": "alert_1", "message": "Test alert 1"},
            {"alert_id": "alert_2", "message": "Test alert 2"}
        ]
        self.alert_manager.get_alert_history.return_value = mock_alerts
        
        # Create request
        request = Mock()
        request.query = {"limit": "100"}
        
        # Call endpoint
        response = await self.dashboard_api.export_alert_history(request)
        
        # Check response
        assert response.status == 200
        assert response.headers["Content-Type"] == "application/json"
        assert "attachment" in response.headers["Content-Disposition"]
        assert "alert_history_" in response.headers["Content-Disposition"]
    
    @pytest.mark.asyncio
    async def test_get_dashboard_config(self):
        """Test getting dashboard configuration"""
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_dashboard_config(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "refresh_interval" in response_data["data"]
    
    @pytest.mark.asyncio
    async def test_update_dashboard_config(self):
        """Test updating dashboard configuration"""
        # Create request
        request = Mock()
        request.json = AsyncMock(return_value={
            "refresh_interval": 60,
            "max_entities_display": 200
        })
        
        # Call endpoint
        response = await self.dashboard_api.update_dashboard_config(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "updated" in response_data["message"]
    
    @pytest.mark.asyncio
    async def test_get_quality_thresholds(self):
        """Test getting quality thresholds"""
        # Mock thresholds
        mock_thresholds = {
            "min_quality_score": 95.0,
            "max_error_rate": 1.0
        }
        self.quality_metrics.quality_thresholds = mock_thresholds
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_quality_thresholds(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert response_data["data"] == mock_thresholds
    
    @pytest.mark.asyncio
    async def test_update_quality_thresholds(self):
        """Test updating quality thresholds"""
        # Create request
        request = Mock()
        request.json = AsyncMock(return_value={
            "min_quality_score": 90.0,
            "max_error_rate": 2.0
        })
        
        # Call endpoint
        response = await self.dashboard_api.update_quality_thresholds(request)
        
        # Check response
        assert response.status == 200
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is True
        assert "updated" in response_data["message"]
        
        # Verify thresholds were updated
        self.quality_metrics.set_quality_thresholds.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in endpoints"""
        # Mock exception in quality metrics
        self.quality_metrics.get_current_metrics.side_effect = Exception("Test error")
        
        # Create request
        request = Mock()
        
        # Call endpoint
        response = await self.dashboard_api.get_current_metrics(request)
        
        # Check response
        assert response.status == 500
        
        # Parse response body
        response_data = await response.json()
        assert response_data["success"] is False
        assert "error" in response_data
