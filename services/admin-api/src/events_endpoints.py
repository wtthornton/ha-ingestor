"""
Recent Events Endpoints
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import os

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EventData(BaseModel):
    """Event data model"""
    id: str
    timestamp: datetime
    entity_id: str
    event_type: str
    old_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    attributes: Dict[str, Any] = {}
    tags: Dict[str, str] = {}


class EventFilter(BaseModel):
    """Event filter model"""
    entity_id: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tags: Dict[str, str] = {}


class EventSearch(BaseModel):
    """Event search model"""
    query: str
    fields: List[str] = ["entity_id", "event_type", "attributes"]
    limit: int = 100


class EventsEndpoints:
    """Recent events endpoints"""
    
    def __init__(self):
        """Initialize events endpoints"""
        self.router = APIRouter()
        self.service_urls = {
            "websocket-ingestion": os.getenv("WEBSOCKET_INGESTION_URL", "http://localhost:8001"),
            "enrichment-pipeline": os.getenv("ENRICHMENT_PIPELINE_URL", "http://localhost:8002")
        }
        
        self._add_routes()
    
    def _add_routes(self):
        """Add events routes"""
        
        @self.router.get("/events", response_model=List[EventData])
        async def get_recent_events(
            limit: int = Query(100, description="Maximum number of events to return"),
            offset: int = Query(0, description="Number of events to skip"),
            entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
            event_type: Optional[str] = Query(None, description="Filter by event type"),
            start_time: Optional[datetime] = Query(None, description="Start time filter"),
            end_time: Optional[datetime] = Query(None, description="End time filter"),
            service: Optional[str] = Query(None, description="Specific service to query")
        ):
            """Get recent events with optional filtering"""
            try:
                # Build filter
                event_filter = EventFilter(
                    entity_id=entity_id,
                    event_type=event_type,
                    start_time=start_time,
                    end_time=end_time
                )
                
                if service and service in self.service_urls:
                    # Get events from specific service
                    events = await self._get_service_events(service, event_filter, limit, offset)
                else:
                    # Get events from all services
                    events = await self._get_all_events(event_filter, limit, offset)
                
                return events
                
            except Exception as e:
                logger.error(f"Error getting recent events: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get recent events"
                )
        
        @self.router.get("/events/{event_id}", response_model=EventData)
        async def get_event_by_id(event_id: str):
            """Get a specific event by ID"""
            try:
                event = await self._get_event_by_id(event_id)
                if not event:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Event {event_id} not found"
                    )
                
                return event
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting event {event_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get event"
                )
        
        @self.router.post("/events/search", response_model=List[EventData])
        async def search_events(
            search: EventSearch
        ):
            """Search events with text query"""
            try:
                events = await self._search_events(search)
                return events
                
            except Exception as e:
                logger.error(f"Error searching events: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to search events"
                )
        
        @self.router.get("/events/stats", response_model=Dict[str, Any])
        async def get_events_stats(
            period: str = Query("1h", description="Time period for statistics"),
            service: Optional[str] = Query(None, description="Specific service")
        ):
            """Get event statistics"""
            try:
                if service and service in self.service_urls:
                    stats = await self._get_service_events_stats(service, period)
                else:
                    stats = await self._get_all_events_stats(period)
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting events stats: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get events statistics"
                )
        
        @self.router.get("/events/entities", response_model=List[Dict[str, Any]])
        async def get_active_entities(
            limit: int = Query(100, description="Maximum number of entities to return"),
            service: Optional[str] = Query(None, description="Specific service")
        ):
            """Get list of active entities"""
            try:
                if service and service in self.service_urls:
                    entities = await self._get_service_active_entities(service, limit)
                else:
                    entities = await self._get_all_active_entities(limit)
                
                return entities
                
            except Exception as e:
                logger.error(f"Error getting active entities: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get active entities"
                )
        
        @self.router.get("/events/types", response_model=List[Dict[str, Any]])
        async def get_event_types(
            limit: int = Query(50, description="Maximum number of event types to return"),
            service: Optional[str] = Query(None, description="Specific service")
        ):
            """Get list of event types"""
            try:
                if service and service in self.service_urls:
                    event_types = await self._get_service_event_types(service, limit)
                else:
                    event_types = await self._get_all_event_types(limit)
                
                return event_types
                
            except Exception as e:
                logger.error(f"Error getting event types: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get event types"
                )
        
        @self.router.get("/events/stream", response_model=Dict[str, Any])
        async def get_events_stream(
            duration: int = Query(60, description="Stream duration in seconds"),
            entity_id: Optional[str] = Query(None, description="Filter by entity ID")
        ):
            """Get real-time event stream"""
            try:
                stream_data = await self._get_events_stream(duration, entity_id)
                return stream_data
                
            except Exception as e:
                logger.error(f"Error getting events stream: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get events stream"
                )
    
    async def _get_all_events(self, event_filter: EventFilter, limit: int, offset: int) -> List[EventData]:
        """Get events from all services"""
        all_events = []
        
        for service_name, service_url in self.service_urls.items():
            try:
                events = await self._get_service_events(service_name, event_filter, limit, offset)
                for event in events:
                    event.tags["service"] = service_name
                all_events.extend(events)
            except Exception as e:
                logger.warning(f"Failed to get events from {service_name}: {e}")
        
        # Sort by timestamp (newest first)
        all_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_events[:limit]
    
    async def _get_service_events(self, service: str, event_filter: EventFilter, limit: int, offset: int) -> List[EventData]:
        """Get events from a specific service"""
        service_url = self.service_urls[service]
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                params = {
                    "limit": limit,
                    "offset": offset
                }
                
                if event_filter.entity_id:
                    params["entity_id"] = event_filter.entity_id
                if event_filter.event_type:
                    params["event_type"] = event_filter.event_type
                if event_filter.start_time:
                    params["start_time"] = event_filter.start_time.isoformat()
                if event_filter.end_time:
                    params["end_time"] = event_filter.end_time.isoformat()
                
                async with session.get(f"{service_url}/events", params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [EventData(**event) for event in data]
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error getting events from {service}: {e}")
            return []
    
    async def _get_event_by_id(self, event_id: str) -> Optional[EventData]:
        """Get a specific event by ID"""
        for service_name, service_url in self.service_urls.items():
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(f"{service_url}/events/{event_id}") as response:
                        if response.status == 200:
                            data = await response.json()
                            event = EventData(**data)
                            event.tags["service"] = service_name
                            return event
                        elif response.status == 404:
                            continue  # Try next service
                        else:
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                logger.warning(f"Failed to get event {event_id} from {service_name}: {e}")
        
        return None
    
    async def _search_events(self, search: EventSearch) -> List[EventData]:
        """Search events with text query"""
        all_events = []
        
        for service_name, service_url in self.service_urls.items():
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.post(f"{service_url}/events/search", json=search.model_dump()) as response:
                        if response.status == 200:
                            data = await response.json()
                            events = [EventData(**event) for event in data]
                            for event in events:
                                event.tags["service"] = service_name
                            all_events.extend(events)
                        else:
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                logger.warning(f"Failed to search events in {service_name}: {e}")
        
        # Sort by timestamp (newest first)
        all_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return all_events[:search.limit]
    
    async def _get_all_events_stats(self, period: str) -> Dict[str, Any]:
        """Get event statistics for all services"""
        all_stats = {
            "total_events": 0,
            "events_per_minute": 0,
            "unique_entities": 0,
            "event_types": {},
            "services": {}
        }
        
        for service_name, service_url in self.service_urls.items():
            try:
                stats = await self._get_service_events_stats(service_name, period)
                all_stats["services"][service_name] = stats
                all_stats["total_events"] += stats.get("total_events", 0)
                all_stats["events_per_minute"] += stats.get("events_per_minute", 0)
                all_stats["unique_entities"] += stats.get("unique_entities", 0)
                
                # Merge event types
                for event_type, count in stats.get("event_types", {}).items():
                    all_stats["event_types"][event_type] = all_stats["event_types"].get(event_type, 0) + count
            except Exception as e:
                logger.warning(f"Failed to get stats from {service_name}: {e}")
                all_stats["services"][service_name] = {"error": str(e)}
        
        return all_stats
    
    async def _get_service_events_stats(self, service: str, period: str) -> Dict[str, Any]:
        """Get event statistics for a specific service"""
        service_url = self.service_urls[service]
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                params = {"period": period}
                async with session.get(f"{service_url}/events/stats", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error getting events stats from {service}: {e}")
            return {"error": str(e)}
    
    async def _get_all_active_entities(self, limit: int) -> List[Dict[str, Any]]:
        """Get active entities from all services"""
        all_entities = []
        
        for service_name, service_url in self.service_urls.items():
            try:
                entities = await self._get_service_active_entities(service_name, limit)
                for entity in entities:
                    entity["service"] = service_name
                all_entities.extend(entities)
            except Exception as e:
                logger.warning(f"Failed to get active entities from {service_name}: {e}")
        
        # Remove duplicates and sort by activity
        unique_entities = {}
        for entity in all_entities:
            entity_id = entity["entity_id"]
            if entity_id not in unique_entities or entity["last_activity"] > unique_entities[entity_id]["last_activity"]:
                unique_entities[entity_id] = entity
        
        # Sort by last activity (most recent first)
        sorted_entities = sorted(unique_entities.values(), key=lambda x: x["last_activity"], reverse=True)
        
        return sorted_entities[:limit]
    
    async def _get_service_active_entities(self, service: str, limit: int) -> List[Dict[str, Any]]:
        """Get active entities from a specific service"""
        service_url = self.service_urls[service]
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                params = {"limit": limit}
                async with session.get(f"{service_url}/events/entities", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error getting active entities from {service}: {e}")
            return []
    
    async def _get_all_event_types(self, limit: int) -> List[Dict[str, Any]]:
        """Get event types from all services"""
        all_event_types = {}
        
        for service_name, service_url in self.service_urls.items():
            try:
                event_types = await self._get_service_event_types(service_name, limit)
                for event_type in event_types:
                    event_type_name = event_type["event_type"]
                    if event_type_name not in all_event_types:
                        all_event_types[event_type_name] = {
                            "event_type": event_type_name,
                            "count": 0,
                            "services": []
                        }
                    all_event_types[event_type_name]["count"] += event_type["count"]
                    all_event_types[event_type_name]["services"].append(service_name)
            except Exception as e:
                logger.warning(f"Failed to get event types from {service_name}: {e}")
        
        # Sort by count (most frequent first)
        sorted_event_types = sorted(all_event_types.values(), key=lambda x: x["count"], reverse=True)
        
        return sorted_event_types[:limit]
    
    async def _get_service_event_types(self, service: str, limit: int) -> List[Dict[str, Any]]:
        """Get event types from a specific service"""
        service_url = self.service_urls[service]
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                params = {"limit": limit}
                async with session.get(f"{service_url}/events/types", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error getting event types from {service}: {e}")
            return []
    
    async def _get_events_stream(self, duration: int, entity_id: Optional[str]) -> Dict[str, Any]:
        """Get real-time event stream"""
        stream_data = {
            "duration": duration,
            "entity_id": entity_id,
            "events": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        # This would typically involve WebSocket connections or Server-Sent Events
        # For now, we'll simulate by getting recent events
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=duration)
        
        event_filter = EventFilter(
            entity_id=entity_id,
            start_time=start_time,
            end_time=end_time
        )
        
        events = await self._get_all_events(event_filter, limit=1000, offset=0)
        stream_data["events"] = [event.dict() for event in events]
        stream_data["end_time"] = end_time.isoformat()
        
        return stream_data
