"""MQTT client for Home Assistant integration."""

import asyncio
import queue
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from ..config import get_settings
from ..utils.logging import get_logger
from ..utils.retry import mqtt_circuit_breaker, mqtt_retry, with_circuit_breaker
from .topic_patterns import TopicPattern, TopicPatternManager, TopicSubscription


class MQTTClient:
    """MQTT client for connecting to Home Assistant MQTT broker."""

    def __init__(self, config: Any = None) -> None:
        """Initialize MQTT client.

        Args:
            config: Configuration settings. If None, uses global settings.
        """
        self.config = config or get_settings()
        self.logger = get_logger(__name__)

        # MQTT client instance
        self.client: mqtt.Client | None = None

        # Connection state
        self._connected = False
        self._connecting = False
        self._disconnecting = False

        # Reconnection settings
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = getattr(
            config, "mqtt_max_reconnect_attempts", 10
        )
        self._reconnect_delay = getattr(
            config, "mqtt_initial_reconnect_delay", 1.0
        )  # Start with 1 second
        self._max_reconnect_delay = getattr(
            config, "mqtt_max_reconnect_delay", 300.0
        )  # Max 5 minutes
        self._reconnect_backoff_multiplier = getattr(
            config, "mqtt_reconnect_backoff_multiplier", 2.0
        )
        self._reconnect_jitter = getattr(
            config, "mqtt_reconnect_jitter", 0.1
        )  # 10% jitter

        # Reconnection task
        self._reconnect_task: asyncio.Task | None = None
        self._reconnect_running = False

        # Topic subscriptions
        self._subscribed_topics: list[str] = []

        # Initialize advanced topic pattern features only if enabled
        if self.config.mqtt_enable_pattern_matching:
            self._topic_pattern_manager = TopicPatternManager(self.config)
            self.logger.info("Advanced MQTT topic pattern matching enabled")
            
            # Initialize advanced features if enabled
            if getattr(self.config, "mqtt_enable_advanced_wildcards", False):
                self._initialize_advanced_wildcards()
                self.logger.info("Advanced wildcard patterns enabled")
            
            if getattr(self.config, "mqtt_enable_regex_patterns", False):
                self.logger.info("Regex-based topic patterns enabled")
                
        else:
            self._topic_pattern_manager = None
            self.logger.info(
                "Advanced MQTT topic pattern matching disabled (deployment mode)"
            )
        self._dynamic_subscriptions: dict[str, TopicSubscription] = {}
        self._subscription_callbacks: dict[str, Callable] = {}

        # Message handler callback
        self._message_handler: Callable[[str, str, datetime], None] | None = None

        # Message queue for async processing
        self._message_queue: queue.Queue | None = None

        # Event loop for async operations
        self._loop: asyncio.AbstractEventLoop | None = None

        # Performance metrics
        self._metrics = {
            "messages_received": 0,
            "messages_processed": 0,
            "pattern_matches": 0,
            "subscription_creates": 0,
            "subscription_removes": 0,
        }

    def _initialize_advanced_wildcards(self) -> None:
        """Initialize advanced wildcard patterns for Home Assistant topics."""
        if not self._topic_pattern_manager:
            return
            
        try:
            # Add Home Assistant specific wildcards
            ha_wildcards = {
                "\\ha_domain": r"binary_sensor|sensor|switch|light|climate|cover|device_tracker|automation|script|scene|input_boolean|input_text|input_number|input_select|input_datetime|zone|person|group|sun|moon|weather|zone|device|entity",
                "\\ha_entity": r"[a-zA-Z_][a-zA-Z0-9_]*",
                "\\ha_room": r"living_room|bedroom|kitchen|bathroom|garage|basement|attic|office|den|family_room|dining_room|laundry|pantry|closet|hallway|entry|mudroom|sunroom|patio|deck|garden|shed|workshop",
                "\\ha_device": r"[a-zA-Z_][a-zA-Z0-9_-]*",
                "\\ha_attribute": r"state|status|value|battery|temperature|humidity|pressure|brightness|color|position|tilt|speed|power|energy|voltage|current|frequency|signal_strength|last_seen|last_updated|friendly_name|unit_of_measurement|icon|assumed_state|supported_features|device_class|state_class",
                "\\ha_numeric": r"-?\d+(?:\.\d+)?",
                "\\ha_boolean": r"true|false|on|off|yes|no|1|0",
                "\\ha_timestamp": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?",
            }
            
            for wildcard, pattern in ha_wildcards.items():
                self._topic_pattern_manager.add_custom_wildcard(wildcard, pattern)
                
            # Create common pattern groups
            self._create_pattern_groups()
            
            self.logger.info("Advanced wildcards initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize advanced wildcards: {e}")

    def _create_pattern_groups(self) -> None:
        """Create common pattern groups for Home Assistant topics."""
        if not self._topic_pattern_manager:
            return
            
        try:
            # Sensor patterns group
            sensor_patterns = [
                "homeassistant/sensor/+/+/state",
                "homeassistant/binary_sensor/+/+/state",
                "homeassistant/sensor/+/+/attributes",
                "homeassistant/binary_sensor/+/+/attributes",
            ]
            self._topic_pattern_manager.create_pattern_group("sensors", sensor_patterns)
            
            # Device patterns group
            device_patterns = [
                "homeassistant/+/+/+/state",
                "homeassistant/+/+/+/attributes",
                "homeassistant/+/+/+/config",
                "homeassistant/+/+/+/discovery",
            ]
            self._topic_pattern_manager.create_pattern_group("devices", device_patterns)
            
            # System patterns group
            system_patterns = [
                "homeassistant/status",
                "homeassistant/+/+/+/+/+",
                "homeassistant/+/+/+/+/+/+",
            ]
            self._topic_pattern_manager.create_pattern_group("system", system_patterns)
            
            self.logger.info("Pattern groups created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create pattern groups: {e}")

    def add_advanced_pattern(self, pattern: str, pattern_type: str = "mqtt", priority: int = 1, description: str = "") -> bool:
        """Add an advanced topic pattern with enhanced features.
        
        Args:
            pattern: The topic pattern string
            pattern_type: Type of pattern ("mqtt", "regex", "advanced")
            priority: Pattern priority (higher = more important)
            description: Description of the pattern
            
        Returns:
            True if pattern was added successfully, False otherwise
        """
        if not self._topic_pattern_manager:
            self.logger.warning("Advanced pattern matching is disabled")
            return False
            
        try:
            from .topic_patterns import TopicPattern
            
            # Create the pattern
            topic_pattern = TopicPattern(
                pattern=pattern,
                pattern_type=pattern_type,
                priority=priority,
                description=description,
                enabled=True
            )
            
            # For advanced patterns, set the custom wildcards before adding to manager
            if pattern_type == "advanced":
                self.logger.debug(f"Setting advanced wildcards for pattern: {pattern}")
                self.logger.debug(f"Available wildcards: {list(self._topic_pattern_manager.custom_wildcards.keys())}")
                topic_pattern.set_advanced_wildcards(self._topic_pattern_manager.custom_wildcards)
                self.logger.debug(f"Pattern wildcards after setting: {list(topic_pattern.advanced_wildcards.keys())}")
            
            # Add to the manager
            success = self._topic_pattern_manager.add_pattern(topic_pattern)
            if success:
                self.logger.info(f"Added {pattern_type} pattern: {pattern}")
                self._metrics["subscription_creates"] += 1
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to add advanced pattern {pattern}: {e}")
            return False

    def get_pattern_statistics(self) -> dict[str, Any]:
        """Get statistics about topic patterns and matching performance.
        
        Returns:
            Dictionary containing pattern statistics
        """
        if not self._topic_pattern_manager:
            return {"error": "Advanced pattern matching is disabled"}
            
        try:
            # Get pattern statistics (which already includes metrics)
            stats = self._topic_pattern_manager.get_pattern_statistics()
            
            # Add MQTT client specific metrics that don't conflict
            for key, value in self._metrics.items():
                if key not in stats:  # Only add if not already present
                    stats[key] = value
                    
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get pattern statistics: {e}")
            return {"error": str(e)}

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
        self.logger.info(
            "Connecting to MQTT broker",
            host=self.config.ha_mqtt_host,
            port=self.config.ha_mqtt_port,
        )

        success = False  # Initialize success variable
        try:
            # Create MQTT client
            self.client = mqtt.Client(
                callback_api_version=CallbackAPIVersion.VERSION2,
                client_id=self.config.ha_mqtt_client_id,
                clean_session=True,
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
                if auth_dict is not None:
                    self.client.username_pw_set(
                        auth_dict["username"], auth_dict["password"]
                    )

            # Connect to broker
            self.client.connect(
                self.config.ha_mqtt_host,
                self.config.ha_mqtt_port,
                keepalive=self.config.ha_mqtt_keepalive,
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
                success = True
            else:
                self.logger.error("Failed to connect to MQTT broker")
                success = False

        except Exception as e:
            self.logger.error("Error connecting to MQTT broker", error=str(e))
            success = False
        finally:
            self._connecting = False

        # If connection failed, start reconnection process
        if not success and not self._disconnecting:
            await self._start_reconnection()

        return success

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

    async def subscribe(self, topics: list[str]) -> bool:
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
                        self.logger.error(
                            "Failed to subscribe to topic", topic=topic, result=result
                        )
                        return False
                else:
                    self.logger.debug("Already subscribed to topic", topic=topic)

            return True

        except Exception as e:
            self.logger.error("Error subscribing to topics", error=str(e))
            return False

    async def subscribe_with_pattern(
        self,
        pattern: str,
        callback: Callable | None = None,
        qos: int = 1,
        filters: dict[str, Any] | None = None,
    ) -> str:
        """Subscribe to a topic pattern with enhanced filtering and routing.

        Args:
            pattern: The topic pattern to subscribe to (supports MQTT wildcards + and #)
            callback: Optional callback function for messages matching this pattern
            qos: Quality of service level
            filters: Optional message filters (topic_regex, payload_regex, etc.)

        Returns:
            Subscription ID for management
        """
        try:
            # Validate callback if provided
            if callback is not None and not callable(callback):
                raise ValueError("Callback must be callable")

            # Create topic pattern if it doesn't exist
            topic_pattern = TopicPattern(
                pattern=pattern,
                description=f"Dynamic subscription to {pattern}",
                priority=1,
                enabled=True,
                filters=filters or {},
            )

            # Add pattern to manager
            if self._topic_pattern_manager:
                if not self._topic_pattern_manager.add_pattern(topic_pattern):
                    # Pattern already exists, update it
                    existing_pattern = self._topic_pattern_manager.pattern_index.get(
                        pattern
                    )
                    if existing_pattern:
                        existing_pattern.filters.update(filters or {})
                else:
                    self.logger.warning(
                        "Pattern already exists, updating it", pattern=pattern
                    )

            # Create subscription
            subscription_id = self._topic_pattern_manager.subscribe_to_pattern(
                pattern, callback, qos, filters
            )

            # Store callback for message routing
            if callback:
                self._subscription_callbacks[subscription_id] = callback

            # Subscribe to the actual MQTT topic if not already subscribed
            if pattern not in self._subscribed_topics:
                await self.subscribe([pattern])

            self._metrics["subscription_creates"] += 1
            self.logger.info(
                "Created pattern subscription",
                subscription_id=subscription_id,
                pattern=pattern,
            )

            return subscription_id

        except Exception as e:
            self.logger.error(
                "Failed to create pattern subscription", pattern=pattern, error=str(e)
            )
            raise

    async def unsubscribe_from_pattern(self, subscription_id: str) -> bool:
        """Unsubscribe from a topic pattern.

        Args:
            subscription_id: The subscription ID to remove

        Returns:
            True if unsubscribed successfully, False otherwise
        """
        try:
            # Get the pattern before removing the subscription
            subscription = self._topic_pattern_manager.subscriptions.get(
                subscription_id
            )
            if not subscription:
                return False

            pattern = subscription.topic

            # Remove from pattern manager
            success = self._topic_pattern_manager.unsubscribe_from_pattern(
                subscription_id
            )

            if success:
                # Remove callback
                if subscription_id in self._subscription_callbacks:
                    del self._subscription_callbacks[subscription_id]

                # Check if this was the last subscription for this pattern
                # If no more subscriptions for this pattern, remove the pattern
                if pattern not in self._topic_pattern_manager.subscription_patterns:
                    self._topic_pattern_manager.remove_pattern(pattern)

                self._metrics["subscription_removes"] += 1
                self.logger.info(
                    "Removed pattern subscription", subscription_id=subscription_id
                )

            return success

        except Exception as e:
            self.logger.error(
                "Failed to remove pattern subscription",
                subscription_id=subscription_id,
                error=str(e),
            )
            return False

    def add_topic_pattern(self, pattern: TopicPattern) -> bool:
        """Add a custom topic pattern for advanced matching.

        Args:
            pattern: The topic pattern to add

        Returns:
            True if pattern was added successfully, False otherwise
        """
        if self._topic_pattern_manager:
            return self._topic_pattern_manager.add_pattern(pattern)
        return False

    def remove_topic_pattern(self, pattern_str: str) -> bool:
        """Remove a custom topic pattern.

        Args:
            pattern_str: The pattern string to remove

        Returns:
            True if pattern was removed successfully, False otherwise
        """
        if self._topic_pattern_manager:
            return self._topic_pattern_manager.remove_pattern(pattern_str)
        return False

    def get_topic_patterns(self) -> list[TopicPattern]:
        """Get all registered topic patterns.

        Returns:
            List of all topic patterns
        """
        if self._topic_pattern_manager:
            return self._topic_pattern_manager.patterns.copy()
        return []

    def get_optimized_subscriptions(self, topics: list[str]) -> list[str]:
        """Get optimized list of subscriptions for a set of topics.

        Args:
            topics: List of topics to optimize subscriptions for

        Returns:
            Optimized list of subscription patterns
        """
        if self._topic_pattern_manager:
            return self._topic_pattern_manager.get_optimized_subscriptions(topics)
        return []

    async def start_listening(self) -> None:
        """Start listening for MQTT messages."""
        if not self._connected:
            self.logger.error("Cannot start listening: not connected")
            return

        # Initialize message queue and start message processing
        self._message_queue = queue.Queue(maxsize=1000)
        self._message_processing_task = asyncio.create_task(
            self._process_message_queue()
        )

        # Subscribe to default Home Assistant topics
        default_topics = [
            "homeassistant/+/+/state",
            "homeassistant/sensor/+/state",
            "homeassistant/binary_sensor/+/state",
            "homeassistant/switch/+/state",
            "homeassistant/light/+/state",
            "homeassistant/climate/+/state",
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
            # Stop message processing task
            if (
                hasattr(self, "_message_processing_task")
                and self._message_processing_task
            ):
                self._message_processing_task.cancel()
                try:
                    await self._message_processing_task
                except asyncio.CancelledError:
                    pass
                self._message_processing_task = None

            # Clear message queue
            if self._message_queue:
                while not self._message_queue.empty():
                    try:
                        self._message_queue.get_nowait()
                    except queue.Empty:
                        break
                self._message_queue = None

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

    def set_message_handler(
        self, handler: Callable[[str, str, datetime], None]
    ) -> None:
        """Set the message handler callback.

        Args:
            handler: Function to call when messages are received.
                    Signature: handler(topic: str, payload: str, timestamp: datetime)
        """
        self._message_handler = handler
        self.logger.debug("Message handler set")

    async def _handle_message(
        self, topic: str, payload: str, timestamp: datetime
    ) -> None:
        """Handle incoming MQTT message.

        Args:
            topic: MQTT topic
            payload: Message payload
            timestamp: Message timestamp
        """
        try:
            self._metrics["messages_received"] += 1

            # Route message through pattern manager for dynamic subscriptions
            routes = []
            if self._topic_pattern_manager:
                routes = self._topic_pattern_manager.route_message(
                    topic, payload, timestamp=timestamp
                )

            # Execute callbacks for matching patterns
            for subscription_id, callback in routes:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(topic, payload, timestamp)
                    else:
                        callback(topic, payload, timestamp)

                    # Update subscription metrics
                    if (
                        self._topic_pattern_manager
                        and subscription_id in self._topic_pattern_manager.subscriptions
                    ):
                        sub = self._topic_pattern_manager.subscriptions[subscription_id]
                        sub.message_count += 1
                        sub.last_message_time = __import__("time").time()

                except Exception as e:
                    self.logger.error(
                        "Error in subscription callback",
                        subscription_id=subscription_id,
                        error=str(e),
                    )

            # Call the main message handler if set
            if self._message_handler:
                try:
                    if asyncio.iscoroutinefunction(self._message_handler):
                        await self._message_handler(topic, payload, timestamp)
                    else:
                        self._message_handler(topic, payload, timestamp)
                except Exception as e:
                    self.logger.error("Error in main message handler", error=str(e))

            self._metrics["messages_processed"] += 1
            self._metrics["pattern_matches"] += len(routes)

        except Exception as e:
            self.logger.error("Error handling MQTT message", topic=topic, error=str(e))

    async def _process_message_queue(self) -> None:
        """Process messages from the queue asynchronously."""
        while True:
            try:
                # Get message from queue with timeout
                message = await asyncio.get_event_loop().run_in_executor(
                    None, self._message_queue.get, 1.0
                )

                if message:
                    topic, payload, timestamp = message
                    await self._handle_message(topic, payload, timestamp)

            except queue.Empty:
                # No messages in queue, continue
                continue
            except asyncio.CancelledError:
                self.logger.debug("Message processing task cancelled")
                break
            except Exception as e:
                self.logger.error("Error processing message from queue", error=str(e))

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
            while (
                self._reconnect_running
                and not self._connected
                and not self._disconnecting
            ):
                if self._reconnect_attempts >= self._max_reconnect_attempts:
                    self.logger.error(
                        "Max reconnection attempts reached",
                        max_attempts=self._max_reconnect_attempts,
                    )
                    break

                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_reconnect_delay()

                self.logger.info(
                    "Attempting to reconnect",
                    attempt=self._reconnect_attempts + 1,
                    max_attempts=self._max_reconnect_attempts,
                    delay=delay,
                )

                # Wait for the calculated delay
                await asyncio.sleep(delay)

                # Attempt reconnection
                if await self._attempt_reconnection():
                    self.logger.info("Reconnection successful")
                    break
                else:
                    self._reconnect_attempts += 1
                    self.logger.warning(
                        "Reconnection failed",
                        attempt=self._reconnect_attempts,
                        max_attempts=self._max_reconnect_attempts,
                    )

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
        base_delay = self._reconnect_delay * (
            self._reconnect_backoff_multiplier**self._reconnect_attempts
        )

        # Cap at maximum delay
        capped_delay = min(base_delay, self._max_reconnect_delay)

        # Add jitter (±jitter_percentage)
        import random

        jitter_factor = 1.0 + random.uniform(
            -self._reconnect_jitter, self._reconnect_jitter
        )

        final_delay = capped_delay * jitter_factor

        self.logger.debug(
            "Calculated reconnection delay",
            base_delay=base_delay,
            capped_delay=capped_delay,
            jitter_factor=jitter_factor,
            final_delay=final_delay,
        )

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
                clean_session=True,
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
                if auth_dict is not None:
                    self.client.username_pw_set(
                        auth_dict["username"], auth_dict["password"]
                    )

            # Connect to broker
            self.client.connect(
                self.config.ha_mqtt_host,
                self.config.ha_mqtt_port,
                keepalive=self.config.ha_mqtt_keepalive,
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
                self._reconnect_delay = (
                    self._reconnect_delay
                )  # Keep current delay for next time

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
    def _on_connect(
        self,
        client: Any,
        userdata: Any,
        flags: Any,
        reason_code: int,
        properties: Any = None,
    ) -> None:
        """Called when connected to MQTT broker."""
        if reason_code == 0:
            self._connected = True
            self.logger.info("Connected to MQTT broker")
        else:
            self.logger.error(
                "Failed to connect to MQTT broker", reason_code=reason_code
            )

    def _on_disconnect(self, client: Any, userdata: Any, *args, **kwargs) -> None:
        """Called when disconnected from MQTT broker."""
        # Extract reason_code from args for compatibility with different paho-mqtt versions
        reason_code = args[0] if args else 0

        self._connected = False
        self.logger.info("Disconnected from MQTT broker", reason_code=reason_code)

        # Attempt reconnection if not intentionally disconnecting
        if not self._disconnecting and reason_code != 0:
            try:
                # Check if there's a running event loop
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._start_reconnection())
            except RuntimeError:
                # No running event loop, schedule the reconnection for later
                self.logger.debug("No running event loop, scheduling reconnection")

    def _on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        """Called when a message is received."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            timestamp = datetime.now(UTC)

            self.logger.debug(
                "Received MQTT message", topic=topic, payload=payload, qos=msg.qos
            )

            # Queue message for async processing
            if self._message_queue:
                try:
                    self._message_queue.put_nowait((topic, payload, timestamp))
                except queue.Full:
                    self.logger.warning(
                        "Message queue full, dropping message", topic=topic
                    )
            else:
                # Fallback: log the message
                self.logger.info(
                    "Message received (no handler)", topic=topic, payload=payload
                )

        except Exception as e:
            self.logger.error("Error processing MQTT message", error=str(e))

    def _on_subscribe(
        self,
        client: Any,
        userdata: Any,
        mid: int,
        granted_qos: int,
        properties: Any = None,
    ) -> None:
        """Called when a subscription is confirmed."""
        self.logger.debug("Subscription confirmed", mid=mid, qos=granted_qos)

    def _on_log(self, client: Any, userdata: Any, level: int, buf: str) -> None:
        """Called for MQTT client logging."""
        if level == mqtt.MQTT_LOG_ERR:
            self.logger.error("MQTT client error", message=buf)
        elif level == mqtt.MQTT_LOG_WARNING:
            self.logger.warning("MQTT client warning", message=buf)
        elif level == mqtt.MQTT_LOG_NOTICE:
            self.logger.info("MQTT client notice", message=buf)
        else:
            self.logger.debug("MQTT client log", message=buf)

    def get_metrics(self) -> dict[str, Any]:
        """Get performance metrics for the MQTT client.

        Returns:
            Dictionary of performance metrics
        """
        metrics_dict = {
            **self._metrics,
            "subscribed_topics": len(self._subscribed_topics),
            "total_patterns": 0,
            "total_subscriptions": 0,
            "dynamic_subscriptions": len(self._dynamic_subscriptions),
            "pattern_subscriptions": 0,
        }

        if self._topic_pattern_manager:
            pattern_metrics = self._topic_pattern_manager.get_metrics()
            metrics_dict.update(pattern_metrics)
            metrics_dict["total_patterns"] = pattern_metrics.get("total_patterns", 0)
            metrics_dict["total_subscriptions"] = pattern_metrics.get(
                "total_subscriptions", 0
            )
            metrics_dict["pattern_subscriptions"] = pattern_metrics.get(
                "total_subscriptions", 0
            )

        return metrics_dict

    def clear_metrics(self) -> None:
        """Clear performance metrics."""
        for key in self._metrics:
            self._metrics[key] = 0
        if self._topic_pattern_manager:
            self._topic_pattern_manager.clear_metrics()
