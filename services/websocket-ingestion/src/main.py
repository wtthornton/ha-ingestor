"""
WebSocket Ingestion Service Main Entry Point
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional
from aiohttp import web
import aiohttp
from dotenv import load_dotenv

# Add shared directory to path for imports
sys.path.append('/app/shared')

from shared.logging_config import (
    setup_logging, get_logger, log_with_context, log_performance, 
    log_error_with_context, performance_monitor, generate_correlation_id,
    set_correlation_id, get_correlation_id
)
from shared.correlation_middleware import create_correlation_middleware

from health_check import HealthCheckHandler
from connection_manager import ConnectionManager
from async_event_processor import AsyncEventProcessor
from event_queue import EventQueue
from batch_processor import BatchProcessor
from memory_manager import MemoryManager
from weather_enrichment import WeatherEnrichmentService
from http_client import SimpleHTTPClient

# Load environment variables
load_dotenv()

# Configure enhanced logging
logger = setup_logging('websocket-ingestion')


class WebSocketIngestionService:
    """Main service class for WebSocket ingestion"""
    
    def __init__(self):
        self.connection_manager: Optional[ConnectionManager] = None
        self.health_handler = HealthCheckHandler()
        # Pass self reference to health handler for weather statistics
        self.health_handler.websocket_service = self
        
        # High-volume processing components
        self.async_event_processor: Optional[AsyncEventProcessor] = None
        self.event_queue: Optional[EventQueue] = None
        self.batch_processor: Optional[BatchProcessor] = None
        self.memory_manager: Optional[MemoryManager] = None
        
        # Weather enrichment components
        self.weather_enrichment: Optional[WeatherEnrichmentService] = None
        
        # HTTP client for enrichment service
        self.http_client: Optional[SimpleHTTPClient] = None
        
        # Get configuration from environment
        self.home_assistant_url = os.getenv('HOME_ASSISTANT_URL')
        self.home_assistant_token = os.getenv('HOME_ASSISTANT_TOKEN')
        self.home_assistant_enabled = os.getenv('ENABLE_HOME_ASSISTANT', 'true').lower() == 'true'
        
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
        
        # Enrichment service configuration
        self.enrichment_service_url = os.getenv('ENRICHMENT_SERVICE_URL', 'http://enrichment-pipeline:8002')
        
        if self.home_assistant_enabled and (not self.home_assistant_url or not self.home_assistant_token):
            raise ValueError("HOME_ASSISTANT_URL and HOME_ASSISTANT_TOKEN must be set when ENABLE_HOME_ASSISTANT=true")
    
    @performance_monitor("service_startup")
    async def start(self):
        """Start the service"""
        corr_id = generate_correlation_id()
        set_correlation_id(corr_id)
        
        log_with_context(
            logger, "INFO", "Starting WebSocket Ingestion Service",
            operation="service_startup",
            correlation_id=corr_id,
            service="websocket-ingestion"
        )
        
        try:
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
            
            log_with_context(
                logger, "INFO", "High-volume processing components started",
                operation="component_startup",
                correlation_id=corr_id,
                components=["memory_manager", "event_queue", "batch_processor", "async_event_processor"]
            )
            
            # Initialize weather enrichment service
            if self.weather_api_key and self.weather_enrichment_enabled:
                self.weather_enrichment = WeatherEnrichmentService(
                    api_key=self.weather_api_key,
                    default_location=self.weather_default_location
                )
                await self.weather_enrichment.start()
                log_with_context(
                    logger, "INFO", "Weather enrichment service initialized",
                    operation="weather_service_startup",
                    correlation_id=corr_id,
                    location=self.weather_default_location
                )
            else:
                log_with_context(
                    logger, "INFO", "Weather enrichment service disabled",
                    operation="weather_service_startup",
                    correlation_id=corr_id,
                    reason="no_api_key_or_disabled"
                )
            
            # HTTP client is initialized in main() function
            log_with_context(
                logger, "INFO", "HTTP client will be initialized in main()",
                operation="http_client_startup",
                correlation_id=corr_id,
                enrichment_url=self.enrichment_service_url
            )
            
            # Set up batch processor handler
            self.batch_processor.add_batch_handler(self._process_batch)
            
            # Initialize connection manager (only if Home Assistant is enabled)
            if self.home_assistant_enabled:
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
                
                # Start connection manager
                await self.connection_manager.start()
                log_with_context(
                    logger, "INFO", "Home Assistant connection manager started",
                    operation="ha_connection_startup",
                    correlation_id=corr_id,
                    url=self.home_assistant_url
                )
            else:
                log_with_context(
                    logger, "INFO", "Home Assistant connection disabled - running in standalone mode",
                    operation="ha_connection_startup",
                    correlation_id=corr_id,
                    mode="standalone"
                )
            
            # Update health handler with connection manager
            self.health_handler.set_connection_manager(self.connection_manager)
            
            log_with_context(
                logger, "INFO", "WebSocket Ingestion Service started successfully",
                operation="service_startup_complete",
                correlation_id=corr_id,
                status="success"
            )
            
        except Exception as e:
            log_error_with_context(
                logger, "Failed to start WebSocket Ingestion Service", e,
                operation="service_startup",
                correlation_id=corr_id,
                error_type="startup_failure"
            )
            raise
    
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
        
        # HTTP client cleanup is handled by context manager in main()
        
        if self.connection_manager:
            await self.connection_manager.stop()
        
        logger.info("WebSocket Ingestion Service stopped")
    
    async def _on_connect(self):
        """Handle successful connection"""
        corr_id = get_correlation_id() or generate_correlation_id()
        log_with_context(
            logger, "INFO", "Successfully connected to Home Assistant",
            operation="ha_connection",
            correlation_id=corr_id,
            status="connected",
            url=self.home_assistant_url
        )
    
    async def _on_disconnect(self):
        """Handle disconnection"""
        corr_id = get_correlation_id() or generate_correlation_id()
        log_with_context(
            logger, "WARNING", "Disconnected from Home Assistant",
            operation="ha_disconnection",
            correlation_id=corr_id,
            status="disconnected",
            url=self.home_assistant_url
        )
    
    async def _on_message(self, message):
        """Handle incoming message"""
        corr_id = get_correlation_id() or generate_correlation_id()
        log_with_context(
            logger, "DEBUG", "Received message from Home Assistant",
            operation="message_received",
            correlation_id=corr_id,
            message_type=type(message).__name__,
            message_size=len(str(message)) if message else 0
        )
        # Message handling is now done in connection_manager
    
    @performance_monitor("event_processing")
    async def _on_event(self, processed_event):
        """Handle processed event"""
        corr_id = get_correlation_id() or generate_correlation_id()
        
        event_type = processed_event.get('event_type', 'unknown')
        entity_id = processed_event.get('entity_id', 'N/A')
        
        log_with_context(
            logger, "DEBUG", "Processing Home Assistant event",
            operation="event_processing",
            correlation_id=corr_id,
            event_type=event_type,
            entity_id=entity_id,
            domain=processed_event.get('domain', 'unknown')
        )
        
        try:
            # Enrich with weather data if available
            if self.weather_enrichment:
                processed_event = await self.weather_enrichment.enrich_event(processed_event)
                log_with_context(
                    logger, "DEBUG", "Event enriched with weather data",
                    operation="weather_enrichment",
                    correlation_id=corr_id,
                    event_type=event_type,
                    entity_id=entity_id
                )
            
            # Add to batch processor for high-volume processing
            if self.batch_processor:
                await self.batch_processor.add_event(processed_event)
                log_with_context(
                    logger, "DEBUG", "Event added to batch processor",
                    operation="batch_processing",
                    correlation_id=corr_id,
                    event_type=event_type,
                    entity_id=entity_id
                )
                
        except Exception as e:
            log_error_with_context(
                logger, "Error processing Home Assistant event", e,
                operation="event_processing",
                correlation_id=corr_id,
                event_type=event_type,
                entity_id=entity_id
            )
    
    @performance_monitor("batch_processing")
    async def _process_batch(self, batch):
        """Process a batch of events"""
        corr_id = get_correlation_id() or generate_correlation_id()
        batch_size = len(batch)
        
        log_with_context(
            logger, "DEBUG", "Processing batch of events",
            operation="batch_processing",
            correlation_id=corr_id,
            batch_size=batch_size
        )
        
        try:
            # Add batch to async event processor
            if self.async_event_processor:
                for event in batch:
                    await self.async_event_processor.process_event(event)
                
                log_with_context(
                    logger, "DEBUG", "Batch processed by async event processor",
                    operation="async_processing",
                    correlation_id=corr_id,
                    batch_size=batch_size
                )
            
            # Send batch to enrichment service via HTTP
            if self.http_client:
                for event in batch:
                    success = await self.http_client.send_event(event)
                    if not success:
                        log_with_context(
                            logger, "ERROR", "Failed to send event to enrichment service",
                            operation="http_send",
                            correlation_id=corr_id,
                            event_type=event.get('event_type', 'unknown')
                        )
                
                log_with_context(
                    logger, "DEBUG", "Batch sent to enrichment service",
                    operation="http_batch_send",
                    correlation_id=corr_id,
                    batch_size=batch_size
                )
                
        except Exception as e:
            log_error_with_context(
                logger, "Error processing batch", e,
                operation="batch_processing",
                correlation_id=corr_id,
                batch_size=batch_size
            )
    
    async def _on_error(self, error):
        """Handle error"""
        corr_id = get_correlation_id() or generate_correlation_id()
        log_error_with_context(
            logger, "Service error occurred", error,
            operation="service_error",
            correlation_id=corr_id,
            error_type="service_error"
        )


async def websocket_handler(request):
    """WebSocket handler for real-time data streaming"""
    # Generate correlation ID for this WebSocket connection
    corr_id = generate_correlation_id()
    set_correlation_id(corr_id)
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    log_with_context(
        logger, "INFO", "WebSocket client connected",
        operation="websocket_connection",
        correlation_id=corr_id,
        client_ip=request.remote,
        user_agent=request.headers.get('User-Agent', 'unknown')
    )
    
    try:
        # Send initial connection message
        await ws.send_json({
            "type": "connection",
            "status": "connected",
            "message": "Connected to HA Ingestor WebSocket",
            "correlation_id": corr_id
        })
        
        # Keep connection alive and handle messages
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    log_with_context(
                        logger, "DEBUG", "Received WebSocket message",
                        operation="websocket_message",
                        correlation_id=corr_id,
                        message_type=data.get("type", "unknown"),
                        message_size=len(msg.data)
                    )
                    
                    # Handle different message types
                    if data.get("type") == "ping":
                        await ws.send_json({
                            "type": "pong", 
                            "timestamp": datetime.now().isoformat(),
                            "correlation_id": corr_id
                        })
                    elif data.get("type") == "subscribe":
                        # Handle subscription requests
                        channels = data.get("channels", [])
                        await ws.send_json({
                            "type": "subscription",
                            "status": "subscribed",
                            "channels": channels,
                            "correlation_id": corr_id
                        })
                        log_with_context(
                            logger, "INFO", "WebSocket client subscribed to channels",
                            operation="websocket_subscription",
                            correlation_id=corr_id,
                            channels=channels
                        )
                    else:
                        # Echo back unknown messages
                        await ws.send_json({
                            "type": "echo",
                            "original": data,
                            "correlation_id": corr_id
                        })
                        
                except json.JSONDecodeError as e:
                    log_error_with_context(
                        logger, "Invalid JSON in WebSocket message", e,
                        operation="websocket_message_parse",
                        correlation_id=corr_id,
                        message_data=msg.data[:100]  # First 100 chars for debugging
                    )
                    await ws.send_json({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "correlation_id": corr_id
                    })
            elif msg.type == aiohttp.WSMsgType.ERROR:
                log_error_with_context(
                    logger, "WebSocket error occurred", ws.exception(),
                    operation="websocket_error",
                    correlation_id=corr_id
                )
                break
                
    except Exception as e:
        log_error_with_context(
            logger, "WebSocket handler error", e,
            operation="websocket_handler",
            correlation_id=corr_id
        )
    finally:
        log_with_context(
            logger, "INFO", "WebSocket client disconnected",
            operation="websocket_disconnection",
            correlation_id=corr_id
        )
    
    return ws


async def create_app():
    """Create the web application"""
    # Create web application with proper middleware factory
    correlation_middleware = create_correlation_middleware()
    app = web.Application(middlewares=[correlation_middleware])
    
    # Create service instance
    service = WebSocketIngestionService()
    
    # Add health check endpoint
    app.router.add_get('/health', service.health_handler.handle)
    
    # Add WebSocket endpoint
    app.router.add_get('/ws', websocket_handler)
    
    # Store service instance in app
    app['service'] = service
    
    return app


async def main():
    """Main entry point"""
    logger.info("Starting WebSocket Ingestion Service...")
    
    # Initialize HTTP client for enrichment service
    enrichment_url = os.getenv("ENRICHMENT_SERVICE_URL", "http://enrichment-pipeline:8002")
    
    async with SimpleHTTPClient(enrichment_url) as http_client:
        # Create web application
        app = await create_app()
        service = app['service']
        
        # Set the HTTP client in the service
        service.http_client = http_client
        
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
