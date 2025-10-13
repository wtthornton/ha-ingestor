"""WebSocket endpoints for real-time dashboard updates."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState

from .auth import AuthManager
from .health_endpoints import HealthEndpoints
from .stats_endpoints import StatsEndpoints
from .events_endpoints import EventsEndpoints

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.active_connections: Set[WebSocket] = set()
        self.health_endpoints = HealthEndpoints()
        self.stats_endpoints = StatsEndpoints()
        self.events_endpoints = EventsEndpoints()
        self.broadcast_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send initial data
        await self.send_initial_data(websocket)
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_initial_data(self, websocket: WebSocket):
        """Send initial dashboard data to a new connection."""
        try:
            # Get health data
            health_data = {"status": "healthy"}  # Placeholder
            
            # Get statistics
            stats_data = {}  # Placeholder
            
            # Get recent events
            events_data = []  # Placeholder - will add later
            
            initial_data = {
                "type": "initial_data",
                "data": {
                    "health": health_data,
                    "statistics": stats_data,
                    "events": events_data
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(initial_data))
            
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            error_data = {
                "type": "error",
                "message": "Failed to load initial data",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(error_data))
    
    async def broadcast_update(self, update_type: str, data: Any):
        """Broadcast an update to all connected clients."""
        if not self.active_connections:
            return
        
        message = {
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        message_text = json.dumps(message)
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_text)
                else:
                    disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected websockets
        for websocket in disconnected:
            self.active_connections.discard(websocket)
    
    async def start_broadcast_loop(self):
        """Start the broadcast loop for periodic updates."""
        self.is_running = True
        while self.is_running:
            try:
                if self.active_connections:
                    # Get current health status
                    health_data = await self.health_endpoints.get_health()
                    await self.broadcast_update("health_update", health_data)
                    
                    # Get current statistics
                    stats_data = await self.stats_endpoints.get_statistics()
                    await self.broadcast_update("stats_update", stats_data)
                
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
    
    def stop_broadcast_loop(self):
        """Stop the broadcast loop."""
        self.is_running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()


class WebSocketEndpoints:
    """WebSocket endpoints for real-time dashboard updates."""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.websocket_manager = WebSocketManager(auth_manager)
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup WebSocket routes."""
        
        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, client_id: str = "anonymous"):
            """WebSocket endpoint for real-time dashboard updates."""
            await self.websocket_manager.connect(websocket, client_id)
            
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    try:
                        message = json.loads(data)
                        await self._handle_client_message(websocket, message)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON received from client {client_id}")
                    except Exception as e:
                        logger.error(f"Error handling client message: {e}")
                        
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket, client_id)
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                self.websocket_manager.disconnect(websocket, client_id)
    
    async def _handle_client_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming messages from WebSocket clients."""
        message_type = message.get("type")
        
        if message_type == "ping":
            # Respond to ping with pong
            pong_message = {
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_text(json.dumps(pong_message))
        
        elif message_type == "request_update":
            # Send specific data update
            data_type = message.get("data_type")
            if data_type == "health":
                health_data = await self.websocket_manager.health_endpoints.get_health()
                await self.websocket_manager.broadcast_update("health_update", health_data)
            elif data_type == "stats":
                stats_data = await self.websocket_manager.stats_endpoints.get_statistics()
                await self.websocket_manager.broadcast_update("stats_update", stats_data)
            elif data_type == "events":
                events_data = await self.websocket_manager.events_endpoints.get_events({"limit": 20})
                await self.websocket_manager.broadcast_update("events_update", events_data)
        
        elif message_type == "subscribe":
            # Handle subscription requests
            subscription_type = message.get("subscription_type")
            logger.info(f"Client subscribed to {subscription_type}")
        
        elif message_type == "unsubscribe":
            # Handle unsubscription requests
            subscription_type = message.get("subscription_type")
            logger.info(f"Client unsubscribed from {subscription_type}")
    
    async def start_broadcast_loop(self):
        """Start the broadcast loop."""
        if not self.websocket_manager.broadcast_task:
            self.websocket_manager.broadcast_task = asyncio.create_task(
                self.websocket_manager.start_broadcast_loop()
            )
    
    def stop_broadcast_loop(self):
        """Stop the broadcast loop."""
        self.websocket_manager.stop_broadcast_loop()
    
    async def broadcast_health_update(self, health_data: Dict[str, Any]):
        """Broadcast health update to all connected clients."""
        await self.websocket_manager.broadcast_update("health_update", health_data)
    
    async def broadcast_stats_update(self, stats_data: Dict[str, Any]):
        """Broadcast statistics update to all connected clients."""
        await self.websocket_manager.broadcast_update("stats_update", stats_data)
    
    async def broadcast_events_update(self, events_data: list):
        """Broadcast events update to all connected clients."""
        await self.websocket_manager.broadcast_update("events_update", events_data)
