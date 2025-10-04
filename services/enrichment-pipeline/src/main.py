"""
Main entry point for the Enrichment Pipeline Service
"""

import asyncio
import logging
import os
from aiohttp import web
from shared.logging_config import setup_logging
from data_normalizer import DataNormalizer
from influxdb_wrapper import InfluxDBClientWrapper
from health_check import health_check_handler
from data_validator import DataValidator
from quality_metrics import QualityMetricsTracker
from quality_alerts import QualityAlertManager, alert_manager
from quality_dashboard import QualityDashboardAPI
from quality_reporting import QualityReportingSystem

# Setup logging for the service
logger = setup_logging("enrichment-pipeline-service")


class EnrichmentPipelineService:
    """Main service class for the enrichment pipeline"""
    
    def __init__(self):
        # Configuration
        self.influxdb_url = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
        self.influxdb_token = os.getenv("INFLUXDB_TOKEN", "ha-ingestor-token")
        self.influxdb_org = os.getenv("INFLUXDB_ORG", "ha-ingestor")
        self.influxdb_bucket = os.getenv("INFLUXDB_BUCKET", "home_assistant_events")
        
        # Core Components
        self.data_normalizer = DataNormalizer()
        self.influxdb_client = InfluxDBClientWrapper(
            self.influxdb_url,
            self.influxdb_token,
            self.influxdb_org,
            self.influxdb_bucket
        )
        
        # Quality Monitoring Components
        self.data_validator = DataValidator()
        self.quality_metrics = QualityMetricsTracker()
        self.alert_manager = alert_manager
        self.quality_dashboard = QualityDashboardAPI(
            self.quality_metrics, 
            self.alert_manager, 
            self.data_validator
        )
        self.quality_reporting = QualityReportingSystem(
            self.quality_metrics,
            self.alert_manager,
            self.data_validator
        )
        
        # Service state
        self.is_running = False
        self.start_time = None
    
    async def start(self):
        """Start the enrichment pipeline service"""
        try:
            logger.info("Starting Enrichment Pipeline Service...")
            
            # Connect to InfluxDB
            if not await self.influxdb_client.connect():
                logger.error("Failed to connect to InfluxDB")
                return False
            
            # Start quality reporting system
            await self.quality_reporting.start()
            
            # Mark service as running
            self.is_running = True
            self.start_time = asyncio.get_event_loop().time()
            
            logger.info("Enrichment Pipeline Service started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting service: {e}")
            return False
    
    async def stop(self):
        """Stop the enrichment pipeline service"""
        try:
            logger.info("Stopping Enrichment Pipeline Service...")
            
            # Stop quality reporting system
            await self.quality_reporting.stop()
            
            # Close InfluxDB connection
            await self.influxdb_client.close()
            
            # Mark service as stopped
            self.is_running = False
            
            logger.info("Enrichment Pipeline Service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
    
    async def process_event(self, event_data: dict) -> bool:
        """
        Process a single event through the enrichment pipeline
        
        Args:
            event_data: The raw event data
            
        Returns:
            True if processing successful, False otherwise
        """
        import time
        start_time = time.time()
        
        try:
            # Validate event data
            validation_results = self.data_validator.validate_event(event_data)
            
            # Check if event is valid
            if not self.data_validator.is_event_valid(event_data):
                logger.warning(f"Event validation failed: {event_data.get('event_type', 'unknown')}")
                # Record validation failure in metrics
                processing_time_ms = (time.time() - start_time) * 1000
                self.quality_metrics.record_validation_result(event_data, validation_results, processing_time_ms)
                return False
            
            # Normalize event data
            normalized_event = self.data_normalizer.normalize_event(event_data)
            
            if not normalized_event:
                logger.warning("Event normalization failed")
                # Record normalization failure in metrics
                processing_time_ms = (time.time() - start_time) * 1000
                self.quality_metrics.record_validation_result(event_data, validation_results, processing_time_ms)
                return False
            
            # Write to InfluxDB
            success = await self.influxdb_client.write_event(normalized_event)
            
            # Record processing result in quality metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self.quality_metrics.record_validation_result(event_data, validation_results, processing_time_ms)
            
            if success:
                logger.debug(f"Successfully processed {event_data.get('event_type', 'unknown')} event")
            else:
                logger.warning("Failed to write event to InfluxDB")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            # Record error in quality metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self.quality_metrics.record_validation_result(event_data, [], processing_time_ms)
            return False
    
    async def process_events_batch(self, events: list) -> int:
        """
        Process multiple events through the enrichment pipeline
        
        Args:
            events: List of raw event data
            
        Returns:
            Number of events successfully processed
        """
        import time
        start_time = time.time()
        
        try:
            # Process events individually to track quality metrics
            processed_count = 0
            for event_data in events:
                success = await self.process_event(event_data)
                if success:
                    processed_count += 1
            
            processing_time_ms = (time.time() - start_time) * 1000
            logger.info(f"Successfully processed {processed_count}/{len(events)} events in {processing_time_ms:.2f}ms")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing events batch: {e}")
            return 0
    
    def get_service_status(self) -> dict:
        """
        Get service status information
        
        Returns:
            Dictionary with service status
        """
        return {
            "service": "enrichment-pipeline",
            "is_running": self.is_running,
            "uptime": asyncio.get_event_loop().time() - self.start_time if self.start_time else 0,
            "normalization": self.data_normalizer.get_normalization_statistics(),
            "influxdb": self.influxdb_client.get_statistics(),
            "quality_metrics": self.quality_metrics.get_current_metrics(),
            "quality_health": self.quality_metrics.get_health_status(),
            "validation_stats": self.data_validator.get_validation_statistics(),
            "alert_stats": self.alert_manager.get_alert_statistics(),
            "timestamp": asyncio.get_event_loop().time()
        }


# Global service instance
service = EnrichmentPipelineService()


async def main():
    """Main application entry point"""
    try:
        # Start the service
        if not await service.start():
            logger.error("Failed to start service")
            return
        
        # Create web application
        app = web.Application()
        
        # Set service instance for health checks
        from health_check import health_handler
        health_handler.set_service(service)
        
        # Add routes
        app.router.add_get('/health', health_check_handler)
        app.router.add_get('/api/v1/health', health_check_handler)
        app.router.add_post('/process-event', process_event_handler)
        app.router.add_post('/process-events', process_events_handler)
        app.router.add_get('/status', status_handler)
        app.router.add_get('/api/v1/stats', status_handler)
        
        # Add quality dashboard routes
        service.quality_dashboard.setup_routes(app)
        
        # Start web server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', 8002)
        await site.start()
        
        logger.info("Enrichment Pipeline Service web server started on port 8002")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await runner.cleanup()
            await service.stop()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")


async def process_event_handler(request):
    """Handle single event processing request"""
    try:
        event_data = await request.json()
        success = await service.process_event(event_data)
        
        return web.json_response({
            "success": success,
            "message": "Event processed" if success else "Event processing failed"
        })
        
    except Exception as e:
        logger.error(f"Error in process_event_handler: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def process_events_handler(request):
    """Handle batch event processing request"""
    try:
        data = await request.json()
        events = data.get("events", [])
        
        if not events:
            return web.json_response({
                "success": False,
                "error": "No events provided"
            }, status=400)
        
        processed_count = await service.process_events_batch(events)
        
        return web.json_response({
            "success": True,
            "processed_count": processed_count,
            "total_count": len(events)
        })
        
    except Exception as e:
        logger.error(f"Error in process_events_handler: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def status_handler(request):
    """Handle status request"""
    try:
        status = service.get_service_status()
        return web.json_response(status)
        
    except Exception as e:
        logger.error(f"Error in status_handler: {e}")
        return web.json_response({
            "error": str(e)
        }, status=500)


if __name__ == '__main__':
    asyncio.run(main())
