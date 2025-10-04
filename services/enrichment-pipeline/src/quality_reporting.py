"""
Data Quality Reporting System
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import json
import csv
import io

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Quality report data structure"""
    report_id: str
    report_type: str
    start_time: datetime
    end_time: datetime
    generated_at: datetime
    generated_by: str
    data: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[str]


class QualityReportingSystem:
    """Automated quality reporting system"""
    
    def __init__(self, quality_metrics_tracker, alert_manager, data_validator):
        self.quality_metrics = quality_metrics_tracker
        self.alert_manager = alert_manager
        self.data_validator = data_validator
        
        # Reporting configuration
        self.reporting_config = {
            "daily_report_time": "06:00",  # UTC
            "weekly_report_day": "monday",
            "monthly_report_day": 1,
            "report_retention_days": 90,
            "auto_generate_reports": True,
            "report_formats": ["json", "csv", "html"]
        }
        
        # Report storage
        self.reports: List[QualityReport] = []
        self.report_templates = {
            "daily": self._generate_daily_report,
            "weekly": self._generate_weekly_report,
            "monthly": self._generate_monthly_report,
            "custom": self._generate_custom_report
        }
        
        # Report generation task
        self._report_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self):
        """Start the quality reporting system"""
        if self._is_running:
            logger.warning("Quality reporting system already running")
            return
        
        self._is_running = True
        
        if self.reporting_config["auto_generate_reports"]:
            self._report_task = asyncio.create_task(self._report_generation_loop())
            logger.info("Quality reporting system started with auto-generation")
        else:
            logger.info("Quality reporting system started (manual mode)")
    
    async def stop(self):
        """Stop the quality reporting system"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        if self._report_task and not self._report_task.done():
            self._report_task.cancel()
            try:
                await self._report_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Quality reporting system stopped")
    
    async def _report_generation_loop(self):
        """Main loop for automatic report generation"""
        while self._is_running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # Check if it's time for daily report
                if self._should_generate_daily_report(current_time):
                    await self.generate_report("daily")
                
                # Check if it's time for weekly report
                if self._should_generate_weekly_report(current_time):
                    await self.generate_report("weekly")
                
                # Check if it's time for monthly report
                if self._should_generate_monthly_report(current_time):
                    await self.generate_report("monthly")
                
                # Clean up old reports
                self._cleanup_old_reports()
                
                # Wait 1 hour before checking again
                await asyncio.sleep(3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in report generation loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def _should_generate_daily_report(self, current_time: datetime) -> bool:
        """Check if daily report should be generated"""
        report_time = self.reporting_config["daily_report_time"]
        hour, minute = map(int, report_time.split(':'))
        
        # Check if current time matches report time (within 1 hour window)
        target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        time_diff = abs((current_time - target_time).total_seconds())
        
        return time_diff < 3600  # 1 hour window
    
    def _should_generate_weekly_report(self, current_time: datetime) -> bool:
        """Check if weekly report should be generated"""
        if current_time.weekday() != 0:  # Monday
            return False
        
        # Check if it's the right time (same as daily report time)
        return self._should_generate_daily_report(current_time)
    
    def _should_generate_monthly_report(self, current_time: datetime) -> bool:
        """Check if monthly report should be generated"""
        if current_time.day != self.reporting_config["monthly_report_day"]:
            return False
        
        # Check if it's the right time (same as daily report time)
        return self._should_generate_daily_report(current_time)
    
    async def generate_report(self, report_type: str, start_time: Optional[datetime] = None, 
                            end_time: Optional[datetime] = None) -> QualityReport:
        """
        Generate a quality report
        
        Args:
            report_type: Type of report (daily, weekly, monthly, custom)
            start_time: Start time for custom reports
            end_time: End time for custom reports
            
        Returns:
            Generated quality report
        """
        try:
            # Determine time range
            if report_type == "custom":
                if not start_time or not end_time:
                    raise ValueError("start_time and end_time required for custom reports")
                report_start = start_time
                report_end = end_time
            else:
                report_start, report_end = self._get_report_time_range(report_type)
            
            # Generate report data
            report_id = f"{report_type}_{int(datetime.now(timezone.utc).timestamp())}"
            
            if report_type in self.report_templates:
                report_data = await self.report_templates[report_type](report_start, report_end)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Create report
            report = QualityReport(
                report_id=report_id,
                report_type=report_type,
                start_time=report_start,
                end_time=report_end,
                generated_at=datetime.now(timezone.utc),
                generated_by="quality_reporting_system",
                data=report_data,
                summary=self._generate_report_summary(report_data),
                recommendations=self._generate_recommendations(report_data)
            )
            
            # Store report
            self.reports.append(report)
            
            # Log report generation
            logger.info(f"Generated {report_type} quality report: {report_id}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            raise
    
    def _get_report_time_range(self, report_type: str) -> tuple[datetime, datetime]:
        """Get time range for report type"""
        current_time = datetime.now(timezone.utc)
        
        if report_type == "daily":
            start_time = current_time - timedelta(days=1)
            end_time = current_time
        elif report_type == "weekly":
            start_time = current_time - timedelta(weeks=1)
            end_time = current_time
        elif report_type == "monthly":
            start_time = current_time - timedelta(days=30)
            end_time = current_time
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        return start_time, end_time
    
    async def _generate_daily_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate daily quality report"""
        # Get current quality metrics
        current_metrics = self.quality_metrics.get_current_metrics()
        quality_report = self.quality_metrics.get_quality_report()
        
        # Get alerts for the period
        alerts = self.alert_manager.get_alert_history(limit=100)
        period_alerts = [
            alert for alert in alerts
            if start_time <= datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')) <= end_time
        ]
        
        # Get validation statistics
        validation_stats = self.data_validator.get_validation_statistics()
        
        return {
            "report_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_hours": (end_time - start_time).total_seconds() / 3600
            },
            "current_metrics": current_metrics,
            "quality_trends": quality_report.get("trend_metrics", {}),
            "entity_quality_summary": {
                "total_entities": len(quality_report.get("entity_quality", {})),
                "problematic_entities": len(quality_report.get("problematic_entities", [])),
                "top_problematic_entities": quality_report.get("problematic_entities", [])[:5]
            },
            "alerts_summary": {
                "total_alerts": len(period_alerts),
                "critical_alerts": len([a for a in period_alerts if a.get('severity') == 'critical']),
                "warning_alerts": len([a for a in period_alerts if a.get('severity') == 'warning']),
                "recent_alerts": period_alerts[:10]
            },
            "validation_summary": validation_stats,
            "common_validation_errors": quality_report.get("common_validation_errors", [])[:10],
            "system_health": self.quality_metrics.get_health_status()
        }
    
    async def _generate_weekly_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate weekly quality report"""
        # Get daily report data as base
        daily_data = await self._generate_daily_report(start_time, end_time)
        
        # Add weekly-specific analysis
        weekly_analysis = {
            "weekly_trends": self._analyze_weekly_trends(start_time, end_time),
            "weekly_comparison": self._compare_with_previous_week(start_time, end_time),
            "weekly_recommendations": self._generate_weekly_recommendations(daily_data)
        }
        
        # Merge with daily data
        weekly_data = daily_data.copy()
        weekly_data.update(weekly_analysis)
        
        return weekly_data
    
    async def _generate_monthly_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate monthly quality report"""
        # Get weekly report data as base
        weekly_data = await self._generate_weekly_report(start_time, end_time)
        
        # Add monthly-specific analysis
        monthly_analysis = {
            "monthly_trends": self._analyze_monthly_trends(start_time, end_time),
            "monthly_comparison": self._compare_with_previous_month(start_time, end_time),
            "monthly_recommendations": self._generate_monthly_recommendations(weekly_data),
            "capacity_planning": self._generate_capacity_planning_analysis(weekly_data)
        }
        
        # Merge with weekly data
        monthly_data = weekly_data.copy()
        monthly_data.update(monthly_analysis)
        
        return monthly_data
    
    async def _generate_custom_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate custom quality report"""
        # For custom reports, use daily report as base
        return await self._generate_daily_report(start_time, end_time)
    
    def _generate_report_summary(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report summary"""
        current_metrics = report_data.get("current_metrics", {})
        alerts_summary = report_data.get("alerts_summary", {})
        system_health = report_data.get("system_health", {})
        
        return {
            "overall_quality_score": current_metrics.get("quality_score", 0),
            "total_events_processed": current_metrics.get("total_events", 0),
            "error_rate": current_metrics.get("error_rate", 0),
            "active_alerts": alerts_summary.get("total_alerts", 0),
            "system_status": system_health.get("status", "unknown"),
            "key_issues": self._identify_key_issues(report_data),
            "performance_summary": {
                "processing_latency": current_metrics.get("processing_latency_avg", 0),
                "enrichment_coverage": current_metrics.get("enrichment_coverage", 0),
                "capture_rate": current_metrics.get("capture_rate", 0)
            }
        }
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on report data"""
        recommendations = []
        
        current_metrics = report_data.get("current_metrics", {})
        alerts_summary = report_data.get("alerts_summary", {})
        system_health = report_data.get("system_health", {})
        
        # Quality score recommendations
        quality_score = current_metrics.get("quality_score", 0)
        if quality_score < 95:
            recommendations.append(f"Quality score is below target (95%): {quality_score:.2f}%. Investigate validation errors and data quality issues.")
        
        # Error rate recommendations
        error_rate = current_metrics.get("error_rate", 0)
        if error_rate > 1:
            recommendations.append(f"Error rate is above acceptable threshold (1%): {error_rate:.2f}%. Review validation rules and data sources.")
        
        # Alert recommendations
        critical_alerts = alerts_summary.get("critical_alerts", 0)
        if critical_alerts > 0:
            recommendations.append(f"{critical_alerts} critical alerts require immediate attention. Review alert details and take corrective action.")
        
        # Processing latency recommendations
        processing_latency = current_metrics.get("processing_latency_avg", 0)
        if processing_latency > 500:
            recommendations.append(f"Processing latency is high: {processing_latency:.2f}ms. Consider optimizing processing pipeline or scaling resources.")
        
        # Enrichment coverage recommendations
        enrichment_coverage = current_metrics.get("enrichment_coverage", 0)
        if enrichment_coverage < 90:
            recommendations.append(f"Enrichment coverage is low: {enrichment_coverage:.2f}%. Check weather API connectivity and configuration.")
        
        # System health recommendations
        if system_health.get("status") != "healthy":
            recommendations.append("System health is degraded. Review system status and address identified issues.")
        
        # Default recommendation if no issues
        if not recommendations:
            recommendations.append("System is performing well. Continue monitoring and consider proactive optimizations.")
        
        return recommendations
    
    def _identify_key_issues(self, report_data: Dict[str, Any]) -> List[str]:
        """Identify key issues from report data"""
        issues = []
        
        current_metrics = report_data.get("current_metrics", {})
        alerts_summary = report_data.get("alerts_summary", {})
        
        # Check for critical issues
        if current_metrics.get("quality_score", 0) < 80:
            issues.append("Critical: Quality score below 80%")
        
        if current_metrics.get("error_rate", 0) > 5:
            issues.append("Critical: Error rate above 5%")
        
        if alerts_summary.get("critical_alerts", 0) > 0:
            issues.append(f"Critical: {alerts_summary['critical_alerts']} critical alerts active")
        
        # Check for warning issues
        if current_metrics.get("quality_score", 0) < 95:
            issues.append("Warning: Quality score below 95%")
        
        if current_metrics.get("error_rate", 0) > 1:
            issues.append("Warning: Error rate above 1%")
        
        return issues
    
    def _analyze_weekly_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze weekly trends (mock implementation)"""
        return {
            "quality_score_trend": "stable",
            "error_rate_trend": "decreasing",
            "processing_latency_trend": "stable",
            "enrichment_coverage_trend": "improving"
        }
    
    def _compare_with_previous_week(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Compare with previous week (mock implementation)"""
        return {
            "quality_score_change": "+2.5%",
            "error_rate_change": "-0.3%",
            "processing_latency_change": "+5ms",
            "enrichment_coverage_change": "+1.2%"
        }
    
    def _analyze_monthly_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analyze monthly trends (mock implementation)"""
        return {
            "quality_score_trend": "improving",
            "error_rate_trend": "stable",
            "processing_latency_trend": "improving",
            "enrichment_coverage_trend": "stable"
        }
    
    def _compare_with_previous_month(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Compare with previous month (mock implementation)"""
        return {
            "quality_score_change": "+5.2%",
            "error_rate_change": "-0.8%",
            "processing_latency_change": "-15ms",
            "enrichment_coverage_change": "+2.1%"
        }
    
    def _generate_weekly_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate weekly-specific recommendations"""
        recommendations = []
        
        # Add weekly-specific analysis
        weekly_trends = report_data.get("weekly_trends", {})
        
        if weekly_trends.get("error_rate_trend") == "increasing":
            recommendations.append("Error rate is trending upward. Investigate recent changes and data sources.")
        
        if weekly_trends.get("processing_latency_trend") == "increasing":
            recommendations.append("Processing latency is increasing. Consider performance optimization.")
        
        return recommendations
    
    def _generate_monthly_recommendations(self, report_data: Dict[str, Any]) -> List[str]:
        """Generate monthly-specific recommendations"""
        recommendations = []
        
        # Add monthly-specific analysis
        monthly_trends = report_data.get("monthly_trends", {})
        capacity_planning = report_data.get("capacity_planning", {})
        
        if monthly_trends.get("quality_score_trend") == "degrading":
            recommendations.append("Quality score is degrading over time. Review data validation rules and sources.")
        
        if capacity_planning.get("storage_growth_rate", 0) > 10:
            recommendations.append("Storage growth rate is high. Consider data retention policy optimization.")
        
        return recommendations
    
    def _generate_capacity_planning_analysis(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate capacity planning analysis (mock implementation)"""
        return {
            "storage_growth_rate": 8.5,  # percentage per month
            "processing_capacity_utilization": 65.0,  # percentage
            "recommended_scaling": "monitor",
            "estimated_capacity_exhaustion": "6 months"
        }
    
    def _cleanup_old_reports(self):
        """Clean up old reports based on retention policy"""
        retention_days = self.reporting_config["report_retention_days"]
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Remove old reports
        initial_count = len(self.reports)
        self.reports = [
            report for report in self.reports
            if report.generated_at > cutoff_time
        ]
        
        removed_count = initial_count - len(self.reports)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old reports")
    
    def get_reports(self, report_type: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get stored reports
        
        Args:
            report_type: Filter by report type
            limit: Maximum number of reports to return
            
        Returns:
            List of report dictionaries
        """
        reports = self.reports
        
        # Filter by type if specified
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        
        # Sort by generation time (newest first)
        reports.sort(key=lambda r: r.generated_at, reverse=True)
        
        # Apply limit
        reports = reports[:limit]
        
        return [
            {
                "report_id": report.report_id,
                "report_type": report.report_type,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat(),
                "generated_at": report.generated_at.isoformat(),
                "generated_by": report.generated_by,
                "summary": report.summary,
                "recommendations": report.recommendations
            }
            for report in reports
        ]
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific report by ID
        
        Args:
            report_id: Report ID to retrieve
            
        Returns:
            Report dictionary or None if not found
        """
        for report in self.reports:
            if report.report_id == report_id:
                return {
                    "report_id": report.report_id,
                    "report_type": report.report_type,
                    "start_time": report.start_time.isoformat(),
                    "end_time": report.end_time.isoformat(),
                    "generated_at": report.generated_at.isoformat(),
                    "generated_by": report.generated_by,
                    "data": report.data,
                    "summary": report.summary,
                    "recommendations": report.recommendations
                }
        return None
    
    def export_report(self, report_id: str, format: str = "json") -> Optional[str]:
        """
        Export report in specified format
        
        Args:
            report_id: Report ID to export
            format: Export format (json, csv, html)
            
        Returns:
            Exported report content or None if not found
        """
        report = self.get_report(report_id)
        if not report:
            return None
        
        if format == "json":
            return json.dumps(report, indent=2)
        elif format == "csv":
            return self._export_report_csv(report)
        elif format == "html":
            return self._export_report_html(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_report_csv(self, report: Dict[str, Any]) -> str:
        """Export report as CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Metric", "Value"])
        
        # Write summary metrics
        summary = report.get("summary", {})
        writer.writerow(["Overall Quality Score", summary.get("overall_quality_score", 0)])
        writer.writerow(["Total Events Processed", summary.get("total_events_processed", 0)])
        writer.writerow(["Error Rate", summary.get("error_rate", 0)])
        writer.writerow(["Active Alerts", summary.get("active_alerts", 0)])
        writer.writerow(["System Status", summary.get("system_status", "unknown")])
        
        # Write performance summary
        performance = summary.get("performance_summary", {})
        writer.writerow(["Processing Latency", performance.get("processing_latency", 0)])
        writer.writerow(["Enrichment Coverage", performance.get("enrichment_coverage", 0)])
        writer.writerow(["Capture Rate", performance.get("capture_rate", 0)])
        
        return output.getvalue()
    
    def _export_report_html(self, report: Dict[str, Any]) -> str:
        """Export report as HTML"""
        summary = report.get("summary", {})
        recommendations = report.get("recommendations", [])
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Quality Report - {report['report_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .recommendations {{ margin: 20px 0; }}
                .metric {{ margin: 10px 0; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Quality Report</h1>
                <p><strong>Report ID:</strong> {report['report_id']}</p>
                <p><strong>Type:</strong> {report['report_type']}</p>
                <p><strong>Generated:</strong> {report['generated_at']}</p>
                <p><strong>Period:</strong> {report['start_time']} to {report['end_time']}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metric"><strong>Overall Quality Score:</strong> {summary.get('overall_quality_score', 0):.2f}%</div>
                <div class="metric"><strong>Total Events Processed:</strong> {summary.get('total_events_processed', 0):,}</div>
                <div class="metric"><strong>Error Rate:</strong> {summary.get('error_rate', 0):.2f}%</div>
                <div class="metric"><strong>Active Alerts:</strong> {summary.get('active_alerts', 0)}</div>
                <div class="metric"><strong>System Status:</strong> {summary.get('system_status', 'unknown')}</div>
            </div>
            
            <div class="recommendations">
                <h2>Recommendations</h2>
                <ul>
        """
        
        for recommendation in recommendations:
            html += f"<li>{recommendation}</li>"
        
        html += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def get_reporting_statistics(self) -> Dict[str, Any]:
        """Get reporting system statistics"""
        return {
            "total_reports": len(self.reports),
            "reports_by_type": {
                report_type: len([r for r in self.reports if r.report_type == report_type])
                for report_type in ["daily", "weekly", "monthly", "custom"]
            },
            "auto_generation_enabled": self.reporting_config["auto_generate_reports"],
            "system_running": self._is_running,
            "retention_days": self.reporting_config["report_retention_days"]
        }
