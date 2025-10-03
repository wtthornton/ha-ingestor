"""
WebSocket Ingestion Service Main Entry Point
"""

import asyncio
import logging
import os
from typing import Optional
from aiohttp import web
from dotenv import load_dotenv

from .health_check import HealthCheckHandler
from .connection_manager import ConnectionManager
from .async_event_processor import AsyncEventProcessor
from .event_queue import EventQueue
from .batch_processor import BatchProcessor
from .memory_manager import MemoryManager
from .weather_enrichment import WeatherEnrichmentService
from .influxdb_client import InfluxDBConnectionManager
from .influxdb_batch_writer import InfluxDBBatchWriter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketIngestionService:
    """Main service class for WebSocket ingestion"""
    
    def __init__(self):
        self.connection_manager: Optional[ConnectionManager] = None
        self.health_handler = HealthCheckHandler()
        
        # High-volume processing components
        self.async_event_processor: Optional[AsyncEventProcessor] = None
        self.event_queue: Optional[EventQueue] = None
        self.batch_processor: Optional[BatchProcessor] = None
        self.memory_manager: Optional[MemoryManager] = None
        
        # Weather enrichment components
        self.weather_enrichment: Optional[WeatherEnrichmentService] = None
        
        # InfluxDB components
        self.influxdb_connection: Optional[InfluxDBConnectionManager] = None
        self.influxdb_writer: Optional[InfluxDBBatchWriter] = None
        
        # Get configuration from environment
        self.home_assistant_url = os.getenv('HOME_ASSISTANT_URL')
        self.home_assistant_token = os.getenv('HOME_ASSISTANT_TOKEN')
        
        # High-volume processing configuration
        self.max_workers = int(os.getenv('MAX_WORKERS', '10'))
        self.processing_rate_limit = int(os.getenv('PROCESSING_RATE_LIMIT', '1000'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.batch_timeout = float(os.getenv('BATCH_TIMEOUT', '5.0'))
        self.max_memory_mb = int(os.getenv('MAX_MEMORY_MB', '1024'))
        
        # Weather enrichment configuration
        self.weather_api_key = os.getenv('WEATHER_API_KEY')
        self.weather_default_location = os.getenv('WEATHER_DEFAULT_LOCATION', 'London,UK')
        self.weather_enrichment_enabled = os.getenv('WEATHER_ENRICHMENT_ENABLED', 'true').lower() == 'true'
        
        # InfluxDB configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home-assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'home-assistant-events')
        self.influxdb_enabled = os.getenv('INFLUXDB_ENABLED', 'true').lower() == 'true'
        
        if not self.home_assistant_url or not self.home_assistant_token:
            raise ValueError("HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN must be set")
    
    async def start(self):
        """Start the service"""
        logger.info("Starting WebSocket Ingestion Service...")
        
        # Initialize high-volume processing components
        self.memory_manager = MemoryManager(max_memory_mb=self.max_memory_mb)
        self.event_queue = EventQueue(maxsize=10000)
        self.batch_processor = BatchProcessor(
            batch_size=self.batch_size,
            batch_timeout=self.batch_timeout
        )
        self.async_event_processor = AsyncEventProcessor(
            max_workers=self.max_workers,
            processing_rate_limit=self.processing_rate_limit
        )
        
        # Start high-volume processing components
        await self.memory_manager.start()
        await self.batch_processor.start()
        await self.async_event_processor.start()
        
        # Initialize weather enrichment service
        if self.weather_api_key and self.weather_enrichment_enabled:
            self.weather_enrichment = WeatherEnrichmentService(
                api_key=self.weather_api_key,
                default_location=self.weather_default_location
            )
            await self.weather_enrichment.start()
            logger.info("Weather enrichment service initialized")
        else:
            logger.info("Weather enrichment service disabled (no API key or disabled)")
        
        # Initialize InfluxDB components
        if self.influxdb_token and self.influxdb_enabled:
            self.influxdb_connection = InfluxDBConnectionManager(
                url=self.influxdb_url,
                token=self.influxdb_token,
                org=self.influxdb_org,
                bucket=self.influxdb_bucket
            )
            await self.influxdb_connection.start()
            
            self.influxdb_writer = InfluxDBBatchWriter(
                connection_manager=self.influxdb_connection,
                batch_size=self.batch_size,
                batch_timeout=self.batch_timeout
            )
            await self.influxdb_writer.start()
            logger.info("InfluxDB components initialized")
        else:
            logger.info("InfluxDB components disabled (no token or disabled)")
        
        # Set up batch processor handler
        self.batch_processor.add_batch_handler(self._process_batch)
        
        # Initialize connection manager
        self.connection_manager = ConnectionManager(
            self.home_assistant_url,
            self.home_assistant_token
        )
        
        # Set up event handlers
        self.connection_manager.on_connect = self._on_connect
        self.connection_manager.on_disconnect = self._on_disconnect
        self.connection_manager.on_message = self._on_message
        self.connection_manager.on_error = self._on_error
        self.connection_manager.on_event = self._on_event
        
        # Update health handler with connection manager
        self.health_handler.set_connection_manager(self.connection_manager)
        
        # Start connection manager
        await self.connection_manager.start()
        
        logger.info("WebSocket Ingestion Service started")
    
    async def stop(self):
        """Stop the service"""
        logger.info("Stopping WebSocket Ingestion Service...")
        
        # Stop high-volume processing components
        if self.async_event_processor:
            await self.async_event_processor.stop()
        if self.batch_processor:
            await self.batch_processor.stop()
        if self.memory_manager:
            await self.memory_manager.stop()
        
        # Stop weather enrichment service
        if self.weather_enrichment:
            await self.weather_enrichment.stop()
        
        # Stop InfluxDB components
        if self.influxdb_writer:
            await self.influxdb_writer.stop()
        if self.influxdb_connection:
            await self.influxdb_connection.stop()
        
        if self.connection_manager:
            await self.connection_manager.stop()
        
        logger.info("WebSocket Ingestion Service stopped")
    
    async def _on_connect(self):
        """Handle successful connection"""
        logger.info("Successfully connected to Home Assistant")
    
    async def _on_disconnect(self):
        """Handle disconnection"""
        logger.warning("Disconnected from Home Assistant")
    
    async def _on_message(self, message):
        """Handle incoming message"""
        logger.debug(f"Received message: {message}")
        # Message handling is now done in connection_manager
    
    async def _on_event(self, processed_event):
        """Handle processed event"""
        logger.debug(f"Processed event: {processed_event.get('event_type')} - {processed_event.get('entity_id', 'N/A')}")
        
        # Enrich with weather data if available
        if self.weather_enrichment:
            processed_event = await self.weather_enrichment.enrich_event(processed_event)
        
        # Add to batch processor for high-volume processing
        if self.batch_processor:
            await self.batch_processor.add_event(processed_event)
    
    async def _process_batch(self, batch):
        """Process a batch of events"""
        logger.debug(f"Processing batch of {len(batch)} events")
        
        # Add batch to async event processor
        if self.async_event_processor:
            for event in batch:
                await self.async_event_processor.process_event(event)
        
        # Store batch in InfluxDB
        if self.influxdb_writer:
            for event in batch:
                await self.influxdb_writer.write_event(event)
    
    async def _on_error(self, error):
        """Handle error"""
        logger.error(f"Service error: {error}")


async def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Create service instance
    service = WebSocketIngestionService()
    
    # Add health check endpoint
    app.router.add_get('/health', service.health_handler.handle)
    
    # Store service instance in app
    app['service'] = service
    
    return app


async def main():
    """Main entry point"""
    logger.info("Starting WebSocket Ingestion Service...")
    
    # Create web application
    app = await create_app()
    service = app['service']
    
    # Start web server
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('WEBSOCKET_INGESTION_PORT', '8000'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"WebSocket Ingestion Service started on port {port}")
    
    # Start the service
    await service.start()
    
    # Keep the service running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down WebSocket Ingestion Service...")
    finally:
        await service.stop()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
