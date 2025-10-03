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
        
        # Components
        self.data_normalizer = DataNormalizer()
        self.influxdb_client = InfluxDBClientWrapper(
            self.influxdb_url,
            self.influxdb_token,
            self.influxdb_org,
            self.influxdb_bucket
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
        try:
            # Normalize event data
            normalized_event = self.data_normalizer.normalize_event(event_data)
            
            if not normalized_event:
                logger.warning("Event normalization failed")
                return False
            
            # Write to InfluxDB
            success = await self.influxdb_client.write_event(normalized_event)
            
            if success:
                logger.debug(f"Successfully processed {event_data.get('event_type', 'unknown')} event")
            else:
                logger.warning("Failed to write event to InfluxDB")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return False
    
    async def process_events_batch(self, events: list) -> int:
        """
        Process multiple events through the enrichment pipeline
        
        Args:
            events: List of raw event data
            
        Returns:
            Number of events successfully processed
        """
        try:
            # Normalize all events
            normalized_events = []
            for event_data in events:
                normalized_event = self.data_normalizer.normalize_event(event_data)
                if normalized_event:
                    normalized_events.append(normalized_event)
            
            if not normalized_events:
                logger.warning("No events were successfully normalized")
                return 0
            
            # Write batch to InfluxDB
            written_count = await self.influxdb_client.write_events_batch(normalized_events)
            
            logger.info(f"Successfully processed {written_count} events")
            return written_count
            
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
        
        # Add routes
        app.router.add_get('/health', health_check_handler)
        app.router.add_post('/process-event', process_event_handler)
        app.router.add_post('/process-events', process_events_handler)
        app.router.add_get('/status', status_handler)
        
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
