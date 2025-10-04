"""
Tests for Quality Reporting System
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quality_reporting import QualityReportingSystem, QualityReport


class TestQualityReportingSystem:
    """Test cases for QualityReportingSystem"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.quality_metrics = Mock()
        self.alert_manager = Mock()
        self.data_validator = Mock()
        
        self.reporting_system = QualityReportingSystem(
            self.quality_metrics,
            self.alert_manager,
            self.data_validator
        )
    
    @pytest.mark.asyncio
    async def test_start_stop_system(self):
        """Test starting and stopping the reporting system"""
        # Start system
        await self.reporting_system.start()
        assert self.reporting_system._is_running is True
        
        # Stop system
        await self.reporting_system.stop()
        assert self.reporting_system._is_running is False
    
    @pytest.mark.asyncio
    async def test_generate_daily_report(self):
        """Test generating daily report"""
        # Mock quality metrics data
        mock_current_metrics = {
            "total_events": 1000,
            "valid_events": 950,
            "quality_score": 95.0,
            "error_rate": 2.0,
            "processing_latency_avg": 150.0,
            "enrichment_coverage": 85.0
        }
        
        mock_quality_report = {
            "current_metrics": mock_current_metrics,
            "trend_metrics": {"quality_trend": "stable"},
            "entity_quality": {
                "sensor.temp": {"quality_score": 95.0},
                "sensor.humidity": {"quality_score": 90.0}
            },
            "problematic_entities": [{"entity_id": "sensor.humidity", "quality_score": 90.0}],
            "common_validation_errors": [
                {"error": "Missing timestamp", "count": 5},
                {"error": "Invalid format", "count": 3}
            ]
        }
        
        mock_alert_history = [
            {"alert_id": "alert_1", "severity": "warning", "timestamp": "2024-12-19T15:30:00Z"},
            {"alert_id": "alert_2", "severity": "critical", "timestamp": "2024-12-19T16:00:00Z"}
        ]
        
        mock_validation_stats = {
            "total_validations": 1000,
            "success_rate": 95.0,
            "error_rate": 2.0
        }
        
        mock_health_status = {
            "status": "healthy",
            "health_issues": [],
            "active_alerts": 1
        }
        
        # Setup mocks
        self.quality_metrics.get_current_metrics.return_value = mock_current_metrics
        self.quality_metrics.get_quality_report.return_value = mock_quality_report
        self.quality_metrics.get_health_status.return_value = mock_health_status
        self.alert_manager.get_alert_history.return_value = mock_alert_history
        self.data_validator.get_validation_statistics.return_value = mock_validation_stats
        
        # Generate daily report
        report = await self.reporting_system.generate_report("daily")
        
        # Check report structure
        assert isinstance(report, QualityReport)
        assert report.report_type == "daily"
        assert report.generated_by == "quality_reporting_system"
        assert "current_metrics" in report.data
        assert "quality_trends" in report.data
        assert "entity_quality_summary" in report.data
        assert "alerts_summary" in report.data
        assert "validation_summary" in report.data
        assert "system_health" in report.data
        
        # Check summary
        assert "overall_quality_score" in report.summary
        assert "total_events_processed" in report.summary
        assert "error_rate" in report.summary
        assert "active_alerts" in report.summary
        assert "system_status" in report.summary
        
        # Check recommendations
        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_generate_weekly_report(self):
        """Test generating weekly report"""
        # Mock data (same as daily for simplicity)
        mock_current_metrics = {"total_events": 7000, "quality_score": 94.0}
        mock_quality_report = {"current_metrics": mock_current_metrics}
        mock_alert_history = []
        mock_validation_stats = {"total_validations": 7000, "success_rate": 94.0}
        mock_health_status = {"status": "healthy", "health_issues": []}
        
        # Setup mocks
        self.quality_metrics.get_current_metrics.return_value = mock_current_metrics
        self.quality_metrics.get_quality_report.return_value = mock_quality_report
        self.quality_metrics.get_health_status.return_value = mock_health_status
        self.alert_manager.get_alert_history.return_value = mock_alert_history
        self.data_validator.get_validation_statistics.return_value = mock_validation_stats
        
        # Generate weekly report
        report = await self.reporting_system.generate_report("weekly")
        
        # Check report structure
        assert report.report_type == "weekly"
        assert "weekly_trends" in report.data
        assert "weekly_comparison" in report.data
        assert "weekly_recommendations" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_monthly_report(self):
        """Test generating monthly report"""
        # Mock data
        mock_current_metrics = {"total_events": 30000, "quality_score": 93.0}
        mock_quality_report = {"current_metrics": mock_current_metrics}
        mock_alert_history = []
        mock_validation_stats = {"total_validations": 30000, "success_rate": 93.0}
        mock_health_status = {"status": "healthy", "health_issues": []}
        
        # Setup mocks
        self.quality_metrics.get_current_metrics.return_value = mock_current_metrics
        self.quality_metrics.get_quality_report.return_value = mock_quality_report
        self.quality_metrics.get_health_status.return_value = mock_health_status
        self.alert_manager.get_alert_history.return_value = mock_alert_history
        self.data_validator.get_validation_statistics.return_value = mock_validation_stats
        
        # Generate monthly report
        report = await self.reporting_system.generate_report("monthly")
        
        # Check report structure
        assert report.report_type == "monthly"
        assert "monthly_trends" in report.data
        assert "monthly_comparison" in report.data
        assert "monthly_recommendations" in report.data
        assert "capacity_planning" in report.data
    
    @pytest.mark.asyncio
    async def test_generate_custom_report(self):
        """Test generating custom report"""
        # Mock data
        mock_current_metrics = {"total_events": 500, "quality_score": 96.0}
        mock_quality_report = {"current_metrics": mock_current_metrics}
        mock_alert_history = []
        mock_validation_stats = {"total_validations": 500, "success_rate": 96.0}
        mock_health_status = {"status": "healthy", "health_issues": []}
        
        # Setup mocks
        self.quality_metrics.get_current_metrics.return_value = mock_current_metrics
        self.quality_metrics.get_quality_report.return_value = mock_quality_report
        self.quality_metrics.get_health_status.return_value = mock_health_status
        self.alert_manager.get_alert_history.return_value = mock_alert_history
        self.data_validator.get_validation_statistics.return_value = mock_validation_stats
        
        # Generate custom report
        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc)
        
        report = await self.reporting_system.generate_report(
            "custom", 
            start_time=start_time, 
            end_time=end_time
        )
        
        # Check report structure
        assert report.report_type == "custom"
        assert report.start_time == start_time
        assert report.end_time == end_time
    
    def test_get_reports(self):
        """Test getting stored reports"""
        # Generate some reports
        mock_report_data = {
            "current_metrics": {"total_events": 100},
            "summary": {"overall_quality_score": 95.0}
        }
        
        # Manually add reports to simulate generated reports
        report1 = QualityReport(
            report_id="daily_1",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 95.0},
            recommendations=["Test recommendation"]
        )
        
        report2 = QualityReport(
            report_id="weekly_1",
            report_type="weekly",
            start_time=datetime.now(timezone.utc) - timedelta(weeks=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 94.0},
            recommendations=["Weekly recommendation"]
        )
        
        self.reporting_system.reports = [report1, report2]
        
        # Get all reports
        reports = self.reporting_system.get_reports()
        assert len(reports) == 2
        
        # Get reports by type
        daily_reports = self.reporting_system.get_reports(report_type="daily")
        assert len(daily_reports) == 1
        assert daily_reports[0]["report_type"] == "daily"
        
        # Get reports with limit
        limited_reports = self.reporting_system.get_reports(limit=1)
        assert len(limited_reports) == 1
    
    def test_get_report_by_id(self):
        """Test getting specific report by ID"""
        # Add a report
        mock_report_data = {"current_metrics": {"total_events": 100}}
        report = QualityReport(
            report_id="test_report_1",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 95.0},
            recommendations=["Test recommendation"]
        )
        
        self.reporting_system.reports = [report]
        
        # Get report by ID
        retrieved_report = self.reporting_system.get_report("test_report_1")
        assert retrieved_report is not None
        assert retrieved_report["report_id"] == "test_report_1"
        assert retrieved_report["report_type"] == "daily"
        
        # Get non-existent report
        nonexistent_report = self.reporting_system.get_report("nonexistent")
        assert nonexistent_report is None
    
    def test_export_report_json(self):
        """Test exporting report as JSON"""
        # Add a report
        mock_report_data = {"current_metrics": {"total_events": 100}}
        report = QualityReport(
            report_id="test_report_1",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 95.0},
            recommendations=["Test recommendation"]
        )
        
        self.reporting_system.reports = [report]
        
        # Export as JSON
        json_content = self.reporting_system.export_report("test_report_1", "json")
        assert json_content is not None
        
        # Parse JSON to verify structure
        import json
        parsed_content = json.loads(json_content)
        assert parsed_content["report_id"] == "test_report_1"
        assert parsed_content["report_type"] == "daily"
        assert "data" in parsed_content
        assert "summary" in parsed_content
        assert "recommendations" in parsed_content
    
    def test_export_report_csv(self):
        """Test exporting report as CSV"""
        # Add a report
        mock_report_data = {"current_metrics": {"total_events": 100}}
        report = QualityReport(
            report_id="test_report_1",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={
                "overall_quality_score": 95.0,
                "total_events_processed": 1000,
                "error_rate": 2.0,
                "active_alerts": 1,
                "system_status": "healthy",
                "performance_summary": {
                    "processing_latency": 150.0,
                    "enrichment_coverage": 85.0,
                    "capture_rate": 99.0
                }
            },
            recommendations=["Test recommendation"]
        )
        
        self.reporting_system.reports = [report]
        
        # Export as CSV
        csv_content = self.reporting_system.export_report("test_report_1", "csv")
        assert csv_content is not None
        
        # Check CSV structure
        lines = csv_content.strip().split('\n')
        assert len(lines) >= 2  # Header + at least one data row
        assert "Metric,Value" in lines[0]  # CSV header
        assert "Overall Quality Score,95.0" in csv_content
        assert "Total Events Processed,1000" in csv_content
    
    def test_export_report_html(self):
        """Test exporting report as HTML"""
        # Add a report
        mock_report_data = {"current_metrics": {"total_events": 100}}
        report = QualityReport(
            report_id="test_report_1",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={
                "overall_quality_score": 95.0,
                "total_events_processed": 1000,
                "error_rate": 2.0,
                "active_alerts": 1,
                "system_status": "healthy"
            },
            recommendations=["Test recommendation 1", "Test recommendation 2"]
        )
        
        self.reporting_system.reports = [report]
        
        # Export as HTML
        html_content = self.reporting_system.export_report("test_report_1", "html")
        assert html_content is not None
        
        # Check HTML structure
        assert "<!DOCTYPE html>" in html_content
        assert "<html>" in html_content
        assert "<head>" in html_content
        assert "<title>Quality Report" in html_content
        assert "<body>" in html_content
        assert "test_report_1" in html_content
        assert "daily" in html_content
        assert "95.0" in html_content
        assert "Test recommendation 1" in html_content
        assert "Test recommendation 2" in html_content
    
    def test_export_nonexistent_report(self):
        """Test exporting non-existent report"""
        # Try to export non-existent report
        content = self.reporting_system.export_report("nonexistent", "json")
        assert content is None
    
    def test_export_unsupported_format(self):
        """Test exporting with unsupported format"""
        # Add a report
        mock_report_data = {"current_metrics": {"total_events": 100}}
        report = QualityReport(
            report_id="test_report_1",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 95.0},
            recommendations=["Test recommendation"]
        )
        
        self.reporting_system.reports = [report]
        
        # Try to export with unsupported format
        with pytest.raises(ValueError, match="Unsupported export format"):
            self.reporting_system.export_report("test_report_1", "xml")
    
    def test_get_reporting_statistics(self):
        """Test getting reporting system statistics"""
        # Add some reports
        mock_report_data = {"current_metrics": {"total_events": 100}}
        
        for i in range(3):
            report = QualityReport(
                report_id=f"daily_{i}",
                report_type="daily",
                start_time=datetime.now(timezone.utc) - timedelta(days=i+1),
                end_time=datetime.now(timezone.utc) - timedelta(days=i),
                generated_at=datetime.now(timezone.utc) - timedelta(days=i),
                generated_by="test",
                data=mock_report_data,
                summary={"overall_quality_score": 95.0},
                recommendations=["Test recommendation"]
            )
            self.reporting_system.reports.append(report)
        
        # Add weekly report
        weekly_report = QualityReport(
            report_id="weekly_1",
            report_type="weekly",
            start_time=datetime.now(timezone.utc) - timedelta(weeks=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 94.0},
            recommendations=["Weekly recommendation"]
        )
        self.reporting_system.reports.append(weekly_report)
        
        # Get statistics
        stats = self.reporting_system.get_reporting_statistics()
        
        assert stats["total_reports"] == 4
        assert stats["reports_by_type"]["daily"] == 3
        assert stats["reports_by_type"]["weekly"] == 1
        assert stats["reports_by_type"]["monthly"] == 0
        assert stats["reports_by_type"]["custom"] == 0
        assert stats["auto_generation_enabled"] is True
        assert stats["system_running"] is False  # Not started in test
        assert stats["retention_days"] == 90
    
    def test_cleanup_old_reports(self):
        """Test cleaning up old reports"""
        # Add old and new reports
        mock_report_data = {"current_metrics": {"total_events": 100}}
        
        # Old report (should be cleaned up)
        old_report = QualityReport(
            report_id="old_report",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=100),
            end_time=datetime.now(timezone.utc) - timedelta(days=99),
            generated_at=datetime.now(timezone.utc) - timedelta(days=100),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 95.0},
            recommendations=["Old recommendation"]
        )
        
        # New report (should be kept)
        new_report = QualityReport(
            report_id="new_report",
            report_type="daily",
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc),
            generated_at=datetime.now(timezone.utc) - timedelta(days=1),
            generated_by="test",
            data=mock_report_data,
            summary={"overall_quality_score": 95.0},
            recommendations=["New recommendation"]
        )
        
        self.reporting_system.reports = [old_report, new_report]
        
        # Cleanup old reports
        self.reporting_system._cleanup_old_reports()
        
        # Check only new report remains
        remaining_reports = self.reporting_system.get_reports()
        assert len(remaining_reports) == 1
        assert remaining_reports[0]["report_id"] == "new_report"
    
    @pytest.mark.asyncio
    async def test_generate_report_error_handling(self):
        """Test error handling in report generation"""
        # Mock exception in quality metrics
        self.quality_metrics.get_current_metrics.side_effect = Exception("Test error")
        
        # Try to generate report
        with pytest.raises(Exception, match="Test error"):
            await self.reporting_system.generate_report("daily")
    
    def test_report_time_range_calculation(self):
        """Test report time range calculation"""
        # Test daily range
        start_time, end_time = self.reporting_system._get_report_time_range("daily")
        time_diff = end_time - start_time
        assert time_diff.days == 1
        
        # Test weekly range
        start_time, end_time = self.reporting_system._get_report_time_range("weekly")
        time_diff = end_time - start_time
        assert time_diff.days == 7
        
        # Test monthly range
        start_time, end_time = self.reporting_system._get_report_time_range("monthly")
        time_diff = end_time - start_time
        assert time_diff.days == 30
        
        # Test invalid report type
        with pytest.raises(ValueError, match="Unknown report type"):
            self.reporting_system._get_report_time_range("invalid")
