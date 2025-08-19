"""MQTT client for Home Assistant integration."""

import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from ..config import get_settings
from ..utils.logging import get_logger
from ..utils.retry import mqtt_retry, with_circuit_breaker, mqtt_circuit_breaker


class MQTTClient:
    """MQTT client for connecting to Home Assistant MQTT broker."""

    def __init__(self, config=None):
        """Initialize MQTT client.
        
        Args:
            config: Configuration settings. If None, uses global settings.
        """
        self.config = config or get_settings()
        self.logger = get_logger(__name__)
        
        # MQTT client instance
        self.client: Optional[mqtt.Client] = None
        
        # Connection state
        self._connected = False
        self._connecting = False
        self._disconnecting = False
        
        # Reconnection settings
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = getattr(config, 'mqtt_max_reconnect_attempts', 10)
        self._reconnect_delay = getattr(config, 'mqtt_initial_reconnect_delay', 1.0)  # Start with 1 second
        self._max_reconnect_delay = getattr(config, 'mqtt_max_reconnect_delay', 300.0)  # Max 5 minutes
        self._reconnect_backoff_multiplier = getattr(config, 'mqtt_reconnect_backoff_multiplier', 2.0)
        self._reconnect_jitter = getattr(config, 'mqtt_reconnect_jitter', 0.1)  # 10% jitter
        
        # Reconnection task
        self._reconnect_task: Optional[asyncio.Task] = None
        self._reconnect_running = False
        
        # Topic subscriptions
        self._subscribed_topics: List[str] = []
        
        # Message handler callback
        self._message_handler: Optional[Callable[[str, str, datetime], None]] = None
        
        # Event loop for async operations
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @with_circuit_breaker(mqtt_circuit_breaker)
    @mqtt_retry
    async def connect(self) -> bool:
        """Connect to MQTT broker.
        
        Returns:
            True if connection successful, False otherwise.
        """
        if self._connected or self._connecting:
            self.logger.warning("Already connected or connecting")
            return self._connected

        self._connecting = True
        self.logger.info("Connecting to MQTT broker", 
                        host=self.config.ha_mqtt_host,
                        port=self.config.ha_mqtt_port)

        try:
            # Create MQTT client
            self.client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION2,
                client_id=self.config.ha_mqtt_client_id,
                clean_session=True
            )

            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_log = self._on_log

            # Set authentication if configured
            if self.config.is_mqtt_authenticated():
                auth_dict = self.config.get_mqtt_auth_dict()
                self.client.username_pw_set(
                    auth_dict["username"], 
                    auth_dict["password"]
                )

            # Connect to broker
            self.client.connect(
                self.config.ha_mqtt_host,
                self.config.ha_mqtt_port,
                keepalive=self.config.ha_mqtt_keepalive
            )

            # Start the client loop
            self.client.loop_start()

            # Wait for connection
            timeout = 10  # 10 second timeout
            start_time = asyncio.get_event_loop().time()
            
            while not self._connected and not self._disconnecting:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    self.logger.error("Connection timeout")
                    break
                await asyncio.sleep(0.1)

            if self._connected:
                self.logger.info("Successfully connected to MQTT broker")
                self._reconnect_attempts = 0
                self._reconnect_delay = 1.0
                return True
            else:
                self.logger.error("Failed to connect to MQTT broker")
                return False

        except Exception as e:
            self.logger.error("Error connecting to MQTT broker", error=str(e))
            return False
        finally:
            self._connecting = False
            
        # If connection failed, start reconnection process
        if not self._connected and not self._disconnecting:
            await self._start_reconnection()
            
        return self._connected

    async def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if not self._connected or self._disconnecting:
            return

        self._disconnecting = True
        self.logger.info("Disconnecting from MQTT broker")

        try:
            # Stop reconnection process
            await self._stop_reconnection()
            
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
                self.client = None
        except Exception as e:
            self.logger.error("Error disconnecting from MQTT broker", error=str(e))
        finally:
            self._connected = False
            self._disconnecting = False
            self._subscribed_topics.clear()

    async def subscribe(self, topics: List[str]) -> bool:
        """Subscribe to MQTT topics.
        
        Args:
            topics: List of topics to subscribe to.
            
        Returns:
            True if subscription successful, False otherwise.
        """
        if not self._connected or not self.client:
            self.logger.error("Cannot subscribe: not connected")
            return False

        try:
            for topic in topics:
                if topic not in self._subscribed_topics:
                    result, mid = self.client.subscribe(topic, qos=1)
                    if result == mqtt.MQTT_ERR_SUCCESS:
                        self._subscribed_topics.append(topic)
                        self.logger.info("Subscribed to topic", topic=topic)
                    else:
                        self.logger.error("Failed to subscribe to topic", 
                                        topic=topic, result=result)
                        return False
                else:
                    self.logger.debug("Already subscribed to topic", topic=topic)

            return True

        except Exception as e:
            self.logger.error("Error subscribing to topics", error=str(e))
            return False

    async def start_listening(self) -> None:
        """Start listening for MQTT messages."""
        if not self._connected:
            self.logger.error("Cannot start listening: not connected")
            return

        # Subscribe to default Home Assistant topics
        default_topics = [
            "homeassistant/+/+/state",
            "homeassistant/sensor/+/state",
            "homeassistant/binary_sensor/+/state",
            "homeassistant/switch/+/state",
            "homeassistant/light/+/state",
            "homeassistant/climate/+/state"
        ]

        success = await self.subscribe(default_topics)
        if success:
            self.logger.info("Started listening for MQTT messages")
        else:
            self.logger.error("Failed to start listening for MQTT messages")

    async def stop_listening(self) -> None:
        """Stop listening for MQTT messages."""
        if not self._connected:
            return

        try:
            # Unsubscribe from all topics
            for topic in self._subscribed_topics:
                if self.client:
                    self.client.unsubscribe(topic)
                    self.logger.debug("Unsubscribed from topic", topic=topic)

            self._subscribed_topics.clear()
            self.logger.info("Stopped listening for MQTT messages")

        except Exception as e:
            self.logger.error("Error stopping MQTT listener", error=str(e))

    def is_connected(self) -> bool:
        """Check if client is connected.
        
        Returns:
            True if connected, False otherwise.
        """
        return self._connected

    def set_message_handler(self, handler: Callable[[str, str, datetime], None]) -> None:
        """Set the message handler callback.
        
        Args:
            handler: Function to call when messages are received.
                    Signature: handler(topic: str, payload: str, timestamp: datetime)
        """
        self._message_handler = handler
        self.logger.debug("Message handler set")

    async def _handle_message(self, topic: str, payload: str, timestamp: datetime) -> None:
        """Handle incoming MQTT message.
        
        Args:
            topic: MQTT topic
            payload: Message payload
            timestamp: Message timestamp
        """
        try:
            if self._message_handler:
                # Call the message handler
                if asyncio.iscoroutinefunction(self._message_handler):
                    await self._message_handler(topic, payload, timestamp)
                else:
                    self._message_handler(topic, payload, timestamp)
            else:
                self.logger.debug("No message handler set", topic=topic, payload=payload)

        except Exception as e:
            self.logger.error("Error handling MQTT message", 
                            topic=topic, error=str(e))

    async def _start_reconnection(self) -> None:
        """Start the reconnection process with backoff strategy."""
        if self._reconnect_running:
            return
        
        self._reconnect_running = True
        self._reconnect_task = asyncio.create_task(self._reconnection_loop())
        self.logger.info("Started reconnection process")
    
    async def _stop_reconnection(self) -> None:
        """Stop the reconnection process."""
        if not self._reconnect_running:
            return
        
        self._reconnect_running = False
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None
        
        self.logger.info("Stopped reconnection process")
    
    async def _reconnection_loop(self) -> None:
        """Main reconnection loop with exponential backoff and jitter."""
        try:
            while self._reconnect_running and not self._connected and not self._disconnecting:
                if self._reconnect_attempts >= self._max_reconnect_attempts:
                    self.logger.error("Max reconnection attempts reached", 
                                   max_attempts=self._max_reconnect_attempts)
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_reconnect_delay()
                
                self.logger.info("Attempting to reconnect", 
                               attempt=self._reconnect_attempts + 1,
                               max_attempts=self._max_reconnect_attempts,
                               delay=delay)
                
                # Wait for the calculated delay
                await asyncio.sleep(delay)
                
                # Attempt reconnection
                if await self._attempt_reconnection():
                    self.logger.info("Reconnection successful")
                    break
                else:
                    self._reconnect_attempts += 1
                    self.logger.warning("Reconnection failed", 
                                      attempt=self._reconnect_attempts,
                                      max_attempts=self._max_reconnect_attempts)
                    
        except asyncio.CancelledError:
            self.logger.debug("Reconnection loop cancelled")
        except Exception as e:
            self.logger.error("Error in reconnection loop", error=str(e))
        finally:
            self._reconnect_running = False
            self.logger.debug("Reconnection loop stopped")
    
    def _calculate_reconnect_delay(self) -> float:
        """Calculate reconnection delay with exponential backoff and jitter.
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay * (multiplier ^ attempts)
        base_delay = self._reconnect_delay * (self._reconnect_backoff_multiplier ** self._reconnect_attempts)
        
        # Cap at maximum delay
        capped_delay = min(base_delay, self._max_reconnect_delay)
        
        # Add jitter (±jitter_percentage)
        import random
        jitter_factor = 1.0 + random.uniform(-self._reconnect_jitter, self._reconnect_jitter)
        
        final_delay = capped_delay * jitter_factor
        
        self.logger.debug("Calculated reconnection delay", 
                         base_delay=base_delay,
                         capped_delay=capped_delay,
                         jitter_factor=jitter_factor,
                         final_delay=final_delay)
        
        return final_delay
    
    async def _attempt_reconnection(self) -> bool:
        """Attempt a single reconnection.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        try:
            # Reset connection state
            self._connected = False
            self._connecting = False
            
            # Create new MQTT client instance
            if self.client:
                self.client.loop_stop()
                self.client.disconnect()
            
            self.client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION2,
                client_id=self.config.ha_mqtt_client_id,
                clean_session=True
            )
            
            # Set up callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_log = self._on_log
            
            # Set authentication if configured
            if self.config.is_mqtt_authenticated():
                auth_dict = self.config.get_mqtt_auth_dict()
                self.client.username_pw_set(
                    auth_dict["username"], 
                    auth_dict["password"]
                )
            
            # Connect to broker
            self.client.connect(
                self.config.ha_mqtt_host,
                self.config.ha_mqtt_port,
                keepalive=self.config.ha_mqtt_keepalive
            )
            
            # Start the client loop
            self.client.loop_start()
            
            # Wait for connection with timeout
            timeout = 10  # 10 second timeout
            start_time = asyncio.get_event_loop().time()
            
            while not self._connected and not self._disconnecting:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    self.logger.warning("Reconnection timeout")
                    break
                await asyncio.sleep(0.1)
            
            if self._connected:
                # Reset reconnection state
                self._reconnect_attempts = 0
                self._reconnect_delay = self._reconnect_delay  # Keep current delay for next time
                
                # Resubscribe to topics
                if self._subscribed_topics:
                    await self.subscribe(self._subscribed_topics)
                
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error("Error during reconnection attempt", error=str(e))
            return False

    # MQTT callback methods
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Called when connected to MQTT broker."""
        if reason_code == 0:
            self._connected = True
            self.logger.info("Connected to MQTT broker")
        else:
            self.logger.error("Failed to connect to MQTT broker", 
                            reason_code=reason_code)

    def _on_disconnect(self, client, userdata, reason_code, properties=None):
        """Called when disconnected from MQTT broker."""
        self._connected = False
        self.logger.info("Disconnected from MQTT broker", reason_code=reason_code)

        # Attempt reconnection if not intentionally disconnecting
        if not self._disconnecting and reason_code != 0:
            asyncio.create_task(self._start_reconnection())

    def _on_message(self, client, userdata, msg):
        """Called when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            timestamp = datetime.utcnow()

            self.logger.debug("Received MQTT message", 
                            topic=topic, 
                            payload=payload,
                            qos=msg.qos)

            # Handle message asynchronously
            asyncio.create_task(self._handle_message(topic, payload, timestamp))

        except Exception as e:
            self.logger.error("Error processing MQTT message", error=str(e))

    def _on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        """Called when a subscription is confirmed."""
        self.logger.debug("Subscription confirmed", mid=mid, qos=granted_qos)

    def _on_log(self, client, userdata, level, buf):
        """Called for MQTT client logging."""
        if level == mqtt.MQTT_LOG_ERR:
            self.logger.error("MQTT client error", message=buf)
        elif level == mqtt.MQTT_LOG_WARNING:
            self.logger.warning("MQTT client warning", message=buf)
        elif level == mqtt.MQTT_LOG_NOTICE:
            self.logger.info("MQTT client notice", message=buf)
        else:
            self.logger.debug("MQTT client log", message=buf)
