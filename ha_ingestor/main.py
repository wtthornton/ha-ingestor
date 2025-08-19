"""Main application entry point for Home Assistant Activity Ingestor."""

import asyncio
import sys
from typing import Union

# Import implemented components
from .config import get_settings
from .utils.logging import setup_default_logging, get_logger
from .utils.error_handling import error_handler, ErrorContext, handle_error_decorator
from .mqtt import MQTTClient
from .websocket import WebSocketClient
from .influxdb import InfluxDBWriter
from .pipeline import EventProcessor
from .models import MQTTEvent, WebSocketEvent, InfluxDBPoint
from .metrics import get_metrics_collector


@handle_error_decorator("mqtt_message_processing", "mqtt_handler", max_retries=2)
async def handle_mqtt_message(topic: str, payload: str, timestamp) -> None:
    """Handle incoming MQTT messages.
    
    Args:
        topic: MQTT topic
        payload: Message payload
        timestamp: Message timestamp
    """
    logger = get_logger(__name__)
    
    # Parse MQTT message into event model
    event = MQTTEvent.from_mqtt_message(topic, payload, timestamp)
    
    logger.info("Received MQTT event",
               domain=event.domain,
               entity_id=event.entity_id,
               state=event.state,
               topic=topic)
    
    # Process event through pipeline
    if pipeline and pipeline.is_running():
        await pipeline.process_event(event)
    else:
        logger.warning("Pipeline not running, cannot process event")
    
    # For now, just log the event details
    if event.attributes:
        logger.debug("Event attributes", attributes=event.attributes)


@handle_error_decorator("websocket_message_processing", "websocket_handler", max_retries=2)
async def handle_websocket_message(message: dict, timestamp) -> None:
    """Handle incoming WebSocket messages.
    
    Args:
        message: WebSocket message
        timestamp: Message timestamp
    """
    logger = get_logger(__name__)
    
    # Parse WebSocket message into event model
    event = WebSocketEvent.from_websocket_message(message, timestamp)
    
    logger.info("Received WebSocket event",
               event_type=event.event_type,
               entity_id=event.entity_id,
               domain=event.domain)
    
    # Process event through pipeline
    if pipeline and pipeline.is_running():
        await pipeline.process_event(event)
    else:
        logger.warning("Pipeline not running, cannot process event")
    
    # For now, just log the event details
    if event.data:
        logger.debug("Event data", data=event.data)


async def store_to_influxdb(event: Union[MQTTEvent, WebSocketEvent, InfluxDBPoint]) -> bool:
    """Storage handler for InfluxDB.
    
    Args:
        event: Event to store (MQTTEvent, WebSocketEvent, or InfluxDBPoint)
        
    Returns:
        True if storage successful, False otherwise.
    """
    try:
        if isinstance(event, InfluxDBPoint):
            # Event is already an InfluxDB point
            point = event
        else:
            # Convert event to InfluxDB point
            if isinstance(event, MQTTEvent):
                point = InfluxDBPoint(
                    measurement=event.get_measurement_name(),
                    tags=event.get_tags(),
                    fields=event.get_fields(),
                    timestamp=event.timestamp
                )
            elif isinstance(event, WebSocketEvent):
                point = InfluxDBPoint(
                    measurement=event.get_measurement_name(),
                    tags=event.get_tags(),
                    fields=event.get_fields(),
                    timestamp=event.timestamp
                )
            else:
                logger.warning("Unknown event type for storage", event_type=type(event))
                return False
        
        # Write to InfluxDB
        success = await influxdb_writer.write_point(point)
        if success:
            logger.debug("Successfully stored event in InfluxDB", 
                        measurement=point.measurement,
                        tags=point.tags)
        else:
            logger.warning("Failed to store event in InfluxDB")
        
        return success
        
    except Exception as e:
        logger.error("Error storing event in InfluxDB", error=str(e))
        return False


async def main() -> int:
    """Main application function."""
    global pipeline, influxdb_writer
    
    try:
        # Initialize logging
        setup_default_logging()
        logger = get_logger(__name__)
        
        logger.info("🚀 Home Assistant Activity Ingestor starting")
        logger.info("=" * 50)
        
        # Load configuration
        config = get_settings()
        logger.info("Configuration loaded successfully", 
                   mqtt_host=config.ha_mqtt_host,
                   websocket_url=str(config.ha_ws_url),
                   influxdb_url=str(config.influxdb_url))
        
        # Initialize components
        mqtt_client = MQTTClient(config)
        websocket_client = WebSocketClient(config)
        influxdb_writer = InfluxDBWriter(config)
        pipeline = EventProcessor(config)
        
        # Set message handlers
        mqtt_client.set_message_handler(handle_mqtt_message)
        websocket_client.set_message_handler(handle_websocket_message)
        
        # Add storage handler to pipeline
        pipeline.add_storage_handler(store_to_influxdb)
        
        # Connect to all services
        logger.info("Connecting to services...")
        
        # Connect to MQTT broker
        logger.info("Connecting to MQTT broker...")
        mqtt_connected = await mqtt_client.connect()
        
        # Connect to WebSocket API
        logger.info("Connecting to Home Assistant WebSocket API...")
        websocket_connected = await websocket_client.connect()
        
        # Connect to InfluxDB
        logger.info("Connecting to InfluxDB...")
        influxdb_connected = await influxdb_writer.connect()
        
        if mqtt_connected and websocket_connected and influxdb_connected:
            logger.info("✅ All services connected successfully")
            
            # Create InfluxDB bucket if it doesn't exist
            logger.info("Ensuring InfluxDB bucket exists...")
            if await influxdb_writer.create_bucket_if_not_exists():
                logger.info("✅ InfluxDB bucket ready")
            else:
                logger.warning("⚠️ InfluxDB bucket creation failed, continuing anyway")
            
            # Start event processing pipeline
            logger.info("Starting event processing pipeline...")
            await pipeline.start()
            
            # Start listening for messages
            await mqtt_client.start_listening()
            await websocket_client.start_listening()
            logger.info("📡 Listening for messages from both sources...")
            
            logger.info("✅ Service initialized successfully")
            logger.info("📡 Waiting for Home Assistant activity...")
            
            # Keep the service running
            try:
                while True:
                    await asyncio.sleep(1)
                    
                    # Check if clients are still connected
                    if not mqtt_client.is_connected():
                        logger.warning("MQTT client disconnected, attempting reconnection...")
                        try:
                            if await mqtt_client.connect():
                                await mqtt_client.start_listening()
                            else:
                                logger.error("Failed to reconnect to MQTT broker")
                        except Exception as e:
                            context = ErrorContext("mqtt_reconnection", "main")
                            error_handler.handle_error(e, context)
                    
                    if not websocket_client.is_connected():
                        logger.warning("WebSocket client disconnected, attempting reconnection...")
                        try:
                            if await websocket_client.connect():
                                await websocket_client.start_listening()
                            else:
                                logger.error("Failed to reconnect to WebSocket API")
                        except Exception as e:
                            context = ErrorContext("websocket_reconnection", "main")
                            error_handler.handle_error(e, context)
                    
                    if not influxdb_writer.is_connected():
                        logger.warning("InfluxDB writer disconnected, attempting reconnection...")
                        try:
                            if await influxdb_writer.connect():
                                logger.info("Reconnected to InfluxDB")
                            else:
                                logger.error("Failed to reconnect to InfluxDB")
                        except Exception as e:
                            context = ErrorContext("influxdb_reconnection", "main")
                            error_handler.handle_error(e, context)
                    
                    # Update connection status metrics
                    metrics_collector = get_metrics_collector()
                    metrics_collector.record_client_connection_status("mqtt", mqtt_client.is_connected())
                    metrics_collector.record_client_connection_status("websocket", websocket_client.is_connected())
                    metrics_collector.record_client_connection_status("influxdb", influxdb_writer.is_connected())
                    
                    # If all clients are disconnected, break
                    if (not mqtt_client.is_connected() and 
                        not websocket_client.is_connected() and 
                        not influxdb_writer.is_connected()):
                        logger.error("All services disconnected, stopping service")
                        break
                    
                    # Log statistics periodically
                    if pipeline.is_running():
                        stats = pipeline.get_stats()
                        if stats["stats"]["events_processed"] > 0:
                            logger.info("Pipeline statistics", 
                                      processed=stats["stats"]["events_processed"],
                                      stored=stats["stats"]["events_stored"],
                                      failed=stats["stats"]["events_failed"],
                                      queue_size=stats["queue_size"])
                        
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
            except Exception as e:
                logger.error("Unexpected error in main loop", error=str(e))
                context = ErrorContext("main_loop", "main")
                error_handler.handle_error(e, context)
            finally:
                # Cleanup
                logger.info("Shutting down services...")
                
                # Stop pipeline
                if pipeline.is_running():
                    await pipeline.stop()
                
                # Disconnect clients
                await mqtt_client.disconnect()
                await websocket_client.disconnect()
                await influxdb_writer.disconnect()
                
                logger.info("✅ All services disconnected")
        else:
            logger.error("❌ Failed to connect to one or more services")
            if not mqtt_connected:
                logger.error("MQTT connection failed")
            if not websocket_connected:
                logger.error("WebSocket connection failed")
            if not influxdb_connected:
                logger.error("InfluxDB connection failed")
            return 1
        
        logger.info("🛑 Service stopped")
        return 0
        
    except Exception as e:
        # Fallback to print if logging isn't working
        print(f"❌ Service failed to start: {e}")
        return 1


def cli() -> int:
    """CLI entry point."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Service interrupted by user")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(cli())
