"""WebSocket client for Home Assistant integration."""

import asyncio
import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed

from ..config import get_settings
from ..utils.logging import get_logger
from ..utils.retry import (
    websocket_circuit_breaker,
    websocket_retry,
    with_circuit_breaker,
)


class WebSocketClient:
    """WebSocket client for connecting to Home Assistant WebSocket API."""

    def __init__(self, config: Any = None) -> None:
        """Initialize WebSocket client.

        Args:
            config: Configuration settings. If None, uses global settings.
        """
        self.config = config or get_settings()
        self.logger = get_logger(__name__)

        # WebSocket connection
        self.websocket: Any | None = None

        # Connection state
        self._connected = False
        self._connecting = False
        self._disconnecting = False
        self._authenticated = False

        # Reconnection settings
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 1.0  # Start with 1 second

        # Event subscriptions
        self._subscribed_events: set[str] = set()

        # Message handler callback
        self._message_handler: Callable[[dict[str, Any], datetime], None] | None = None

        # Heartbeat management
        self._heartbeat_task: asyncio.Task | None = None
        self._heartbeat_interval = getattr(self.config, "ha_ws_heartbeat_interval", 30)

        # Message ID counter for requests
        self._message_id = 1

        # Event loop for async operations
        self._loop: asyncio.AbstractEventLoop | None = None

    @with_circuit_breaker(websocket_circuit_breaker)
    @websocket_retry
    async def connect(self) -> bool:
        """Connect to Home Assistant WebSocket API.

        Returns:
            True if connection successful, False otherwise.
        """
        if self._connected or self._connecting:
            self.logger.warning("Already connected or connecting")
            return self._connected

        self._connecting = True
        self.logger.info(
            "Connecting to Home Assistant WebSocket API", url=str(self.config.ha_ws_url)
        )

        try:
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                str(self.config.ha_ws_url),
                extra_headers={"Authorization": f"Bearer {self.config.ha_ws_token}"},
            )

            self._connected = True
            self.logger.info("WebSocket connection established")

            # Authenticate with Home Assistant
            if await self._authenticate():
                self.logger.info("Successfully authenticated with Home Assistant")
                self._authenticated = True

                # Start heartbeat
                self._start_heartbeat()

                # Start listening for messages
                asyncio.create_task(self._listen_for_messages())

                return True
            else:
                self.logger.error("Failed to authenticate with Home Assistant")
                await self.disconnect()
                return False

        except Exception as e:
            self.logger.error("Error connecting to WebSocket API", error=str(e))
            return False
        finally:
            self._connecting = False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket API."""
        if not self._connected or self._disconnecting:
            return

        self._disconnecting = True
        self.logger.info("Disconnecting from WebSocket API")

        try:
            # Stop heartbeat
            self._stop_heartbeat()

            # Close WebSocket connection
            if self.websocket:
                await self.websocket.close()
                self.websocket = None

        except Exception as e:
            self.logger.error("Error disconnecting from WebSocket API", error=str(e))
        finally:
            self._connected = False
            self._authenticated = False
            self._disconnecting = False
            self._subscribed_events.clear()

    async def subscribe_events(self, event_types: list[str]) -> bool:
        """Subscribe to Home Assistant events.

        Args:
            event_types: List of event types to subscribe to.

        Returns:
            True if subscription successful, False otherwise.
        """
        if not self._connected or not self._authenticated:
            self.logger.error("Cannot subscribe: not connected or not authenticated")
            return False

        try:
            for event_type in event_types:
                if event_type not in self._subscribed_events:
                    # Send subscription request
                    message = {
                        "id": self._get_message_id(),
                        "type": "subscribe_events",
                        "event_type": event_type,
                    }

                    await self._send_message(message)
                    self._subscribed_events.add(event_type)
                    self.logger.info("Subscribed to event type", event_type=event_type)
                else:
                    self.logger.debug(
                        "Already subscribed to event type", event_type=event_type
                    )

            return True

        except Exception as e:
            self.logger.error("Error subscribing to events", error=str(e))
            return False

    async def start_listening(self) -> None:
        """Start listening for WebSocket events."""
        if not self._connected or not self._authenticated:
            self.logger.error(
                "Cannot start listening: not connected or not authenticated"
            )
            return

        # Subscribe to default Home Assistant events
        default_events = [
            "state_changed",
            "automation_triggered",
            "service_called",
            "event",
        ]

        success = await self.subscribe_events(default_events)
        if success:
            self.logger.info("Started listening for WebSocket events")
        else:
            self.logger.error("Failed to start listening for WebSocket events")

    async def stop_listening(self) -> None:
        """Stop listening for WebSocket events."""
        if not self._connected:
            return

        try:
            # Unsubscribe from all events
            for event_type in list(self._subscribed_events):
                message = {
                    "id": self._get_message_id(),
                    "type": "unsubscribe_events",
                    "subscription": event_type,
                }

                try:
                    await self._send_message(message)
                    self._subscribed_events.discard(event_type)
                    self.logger.debug(
                        "Unsubscribed from event type", event_type=event_type
                    )
                except Exception as e:
                    self.logger.warning(
                        "Failed to unsubscribe from event type",
                        event_type=event_type,
                        error=str(e),
                    )

            self.logger.info("Stopped listening for WebSocket events")

        except Exception as e:
            self.logger.error("Error stopping WebSocket listener", error=str(e))

    def is_connected(self) -> bool:
        """Check if client is connected.

        Returns:
            True if connected, False otherwise.
        """
        return self._connected and self._authenticated

    def set_message_handler(
        self, handler: Callable[[dict[str, Any], datetime], None]
    ) -> None:
        """Set the message handler callback.

        Args:
            handler: Function to call when messages are received.
                    Signature: handler(message: Dict[str, Any], timestamp: datetime)
        """
        self._message_handler = handler
        self.logger.debug("Message handler set")

    async def _authenticate(self) -> bool:
        """Authenticate with Home Assistant WebSocket API."""
        try:
            # Wait for initial auth_required message
            initial_response = await self._receive_message()
            if not initial_response or initial_response.get("type") != "auth_required":
                self.logger.error(
                    "Expected auth_required message", response=initial_response
                )
                return False

            self.logger.info("Received auth_required, proceeding with authentication")

            # Send authentication message
            auth_message = {"type": "auth", "access_token": self.config.ha_ws_token}
            await self._send_message(auth_message)

            # Wait for authentication response
            response = await self._receive_message()

            if response and response.get("type") == "auth_ok":
                self.logger.info("Authentication successful")
                return True
            else:
                self.logger.error("Authentication failed", response=response)
                return False

        except Exception as e:
            self.logger.error("Error during authentication", error=str(e))
            return False

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send message to WebSocket.

        Args:
            message: Message to send.
        """
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")

        message_str = json.dumps(message)
        await self.websocket.send(message_str)
        self.logger.debug("Sent message", message=message)

    async def _receive_message(self) -> dict[str, Any] | None:
        """Receive message from WebSocket.

        Returns:
            Received message or None if connection closed.
        """
        if not self.websocket:
            return None

        try:
            message_str = await self.websocket.recv()
            message = json.loads(message_str)
            if isinstance(message, dict):
                self.logger.debug("Received message", message=message)
                return message
            else:
                self.logger.warning("Received non-dict message", message=message)
                return None
        except ConnectionClosed:
            self.logger.warning("WebSocket connection closed")
            return None
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse WebSocket message", error=str(e))
            return None

    async def _listen_for_messages(self) -> None:
        """Listen for incoming WebSocket messages."""
        self.logger.info("Started listening for WebSocket messages")

        try:
            while self._connected and not self._disconnecting:
                try:
                    message = await self._receive_message()
                    if message is None:
                        break

                    # Handle the message
                    await self._handle_message(message, datetime.utcnow())

                except Exception as e:
                    self.logger.error("Error handling WebSocket message", error=str(e))

        except Exception as e:
            self.logger.error("Error in WebSocket message listener", error=str(e))
        finally:
            self.logger.info("Stopped listening for WebSocket messages")

    async def _handle_message(
        self, message: dict[str, Any], timestamp: datetime
    ) -> None:
        """Handle incoming WebSocket message.

        Args:
            message: Received message
            timestamp: Message timestamp
        """
        try:
            message_type = message.get("type")

            if message_type == "event":
                # Handle event message
                if self._message_handler:
                    if asyncio.iscoroutinefunction(self._message_handler):
                        await self._message_handler(message, timestamp)
                    else:
                        self._message_handler(message, timestamp)
                else:
                    self.logger.debug("No message handler set", message=message)

            elif message_type == "pong":
                # Handle pong response
                self.logger.debug("Received pong response")

            elif message_type == "auth_ok":
                # Handle authentication success
                self.logger.debug("Authentication confirmed")

            elif message_type == "auth_invalid":
                # Handle authentication failure
                self.logger.error("Authentication invalid")
                self._authenticated = False

            else:
                # Handle other message types
                self.logger.debug(
                    "Received message", type=message_type, message=message
                )

        except Exception as e:
            self.logger.error(
                "Error handling WebSocket message", message=message, error=str(e)
            )

    def _start_heartbeat(self) -> None:
        """Start heartbeat monitoring."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self.logger.debug("Started heartbeat monitoring")

    def _stop_heartbeat(self) -> None:
        """Stop heartbeat monitoring."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
            self.logger.debug("Stopped heartbeat monitoring")

    async def _heartbeat_loop(self) -> None:
        """Heartbeat monitoring loop."""
        try:
            while self._connected and not self._disconnecting:
                await asyncio.sleep(self._heartbeat_interval)

                if self._connected and not self._disconnecting:
                    await self._send_ping()

        except asyncio.CancelledError:
            self.logger.debug("Heartbeat task cancelled")
        except Exception as e:
            self.logger.error("Error in heartbeat loop", error=str(e))

    async def _send_ping(self) -> None:
        """Send ping message to check connection health."""
        try:
            ping_message = {"id": self._get_message_id(), "type": "ping"}

            await self._send_message(ping_message)
            self.logger.debug("Sent ping")

        except Exception as e:
            self.logger.warning("Failed to send ping", error=str(e))
            # Connection might be stale, trigger reconnection
            await self._handle_connection_failure()

    async def _handle_connection_failure(self) -> None:
        """Handle connection failure and attempt reconnection."""
        if self._disconnecting:
            return

        self.logger.warning("WebSocket connection failure detected")
        self._connected = False
        self._authenticated = False

        # Attempt reconnection
        asyncio.create_task(self._reconnect())

    async def _reconnect(self) -> None:
        """Attempt to reconnect to WebSocket API."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self.logger.error("Max reconnection attempts reached")
            return

        self._reconnect_attempts += 1
        delay = min(self._reconnect_delay * (2 ** (self._reconnect_attempts - 1)), 60)

        self.logger.info(
            "Attempting to reconnect", attempt=self._reconnect_attempts, delay=delay
        )

        await asyncio.sleep(delay)

        try:
            if await self.connect():
                self.logger.info("Reconnection successful")
                # Resubscribe to events
                if self._subscribed_events:
                    await self.subscribe_events(list(self._subscribed_events))
            else:
                self.logger.warning("Reconnection failed, will retry")
                # Schedule next reconnection attempt
                asyncio.create_task(self._reconnect())

        except Exception as e:
            self.logger.error("Error during reconnection", error=str(e))
            # Schedule next reconnection attempt
            asyncio.create_task(self._reconnect())

    def _get_message_id(self) -> int:
        """Get next message ID.

        Returns:
            Next message ID.
        """
        message_id = self._message_id
        self._message_id += 1
        return message_id
