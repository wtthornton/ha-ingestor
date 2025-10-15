"""
Data API Client for AI Automation Service

Provides access to historical Home Assistant data via the Data API service.
"""

import httpx
import pandas as pd
from typing import List, Dict, Optional, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class DataAPIClient:
    """Client for fetching historical data from Data API"""
    
    def __init__(self, base_url: str = "http://data-api:8006"):
        """
        Initialize Data API client.
        
        Args:
            base_url: Base URL for Data API (default: http://data-api:8006)
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        logger.info(f"Data API client initialized with base_url={self.base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fetch_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        entity_id: Optional[str] = None,
        device_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 10000
    ) -> pd.DataFrame:
        """
        Fetch historical events from Data API.
        
        Args:
            start_time: Start datetime (default: 30 days ago)
            end_time: End datetime (default: now)
            entity_id: Optional filter for specific entity
            device_id: Optional filter for specific device
            event_type: Optional filter for event type (e.g., 'state_changed')
            limit: Maximum number of events to return
        
        Returns:
            pandas DataFrame with columns: timestamp, entity_id, event_type, old_state, new_state, attributes, tags
        
        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            # Default to last 30 days
            if start_time is None:
                start_time = datetime.now(timezone.utc) - timedelta(days=30)
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            
            # Build query parameters
            params: Dict[str, Any] = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "limit": limit
            }
            
            if entity_id:
                params["entity_id"] = entity_id
            if device_id:
                params["device_id"] = device_id
            if event_type:
                params["event_type"] = event_type
            
            logger.info(f"Fetching events from Data API: start={start_time}, end={end_time}, limit={limit}")
            
            response = await self.client.get(
                f"{self.base_url}/api/v1/events",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                if "events" in data:
                    events = data["events"]
                elif "data" in data:
                    events = data["data"]
                else:
                    events = []
            elif isinstance(data, list):
                events = data
            else:
                logger.warning(f"Unexpected response format from Data API: {type(data)}")
                events = []
            
            # Convert to pandas DataFrame
            if not events:
                logger.warning(f"No events returned from Data API for period {start_time} to {end_time}")
                return pd.DataFrame()
            
            df = pd.DataFrame(events)
            
            # Ensure timestamp column exists and parse it
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            else:
                logger.warning("No timestamp column in events data")
            
            logger.info(f"✅ Fetched {len(df)} events from Data API")
            return df
            
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to fetch events from Data API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching events: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fetch_devices(
        self,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        area_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch all devices from Data API.
        
        Args:
            manufacturer: Optional filter by manufacturer
            model: Optional filter by model
            area_id: Optional filter by area/room
            limit: Maximum number of devices to return
        
        Returns:
            List of device dictionaries with keys: device_id, name, manufacturer, model, area_id, entity_count
        
        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            params: Dict[str, Any] = {"limit": limit}
            
            if manufacturer:
                params["manufacturer"] = manufacturer
            if model:
                params["model"] = model
            if area_id:
                params["area_id"] = area_id
            
            logger.info(f"Fetching devices from Data API (limit={limit})")
            
            response = await self.client.get(
                f"{self.base_url}/api/devices",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle response format
            if isinstance(data, dict) and "devices" in data:
                devices = data["devices"]
            elif isinstance(data, list):
                devices = data
            else:
                logger.warning(f"Unexpected devices response format: {type(data)}")
                devices = []
            
            logger.info(f"✅ Fetched {len(devices)} devices from Data API")
            return devices
            
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to fetch devices from Data API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching devices: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def fetch_entities(
        self,
        device_id: Optional[str] = None,
        domain: Optional[str] = None,
        platform: Optional[str] = None,
        area_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetch all entities from Data API.
        
        Args:
            device_id: Optional filter by device ID
            domain: Optional filter by domain (light, sensor, switch, etc)
            platform: Optional filter by integration platform
            area_id: Optional filter by area/room
            limit: Maximum number of entities to return
        
        Returns:
            List of entity dictionaries with keys: entity_id, device_id, domain, platform, area_id, disabled
        
        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            params: Dict[str, Any] = {"limit": limit}
            
            if device_id:
                params["device_id"] = device_id
            if domain:
                params["domain"] = domain
            if platform:
                params["platform"] = platform
            if area_id:
                params["area_id"] = area_id
            
            logger.info(f"Fetching entities from Data API (limit={limit})")
            
            response = await self.client.get(
                f"{self.base_url}/api/entities",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Handle response format
            if isinstance(data, dict) and "entities" in data:
                entities = data["entities"]
            elif isinstance(data, list):
                entities = data
            else:
                logger.warning(f"Unexpected entities response format: {type(data)}")
                entities = []
            
            logger.info(f"✅ Fetched {len(entities)} entities from Data API")
            return entities
            
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to fetch entities from Data API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching entities: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Data API health status.
        
        Returns:
            Health status dictionary
        
        Raises:
            httpx.HTTPError: If API request fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"❌ Data API health check failed: {e}")
            raise
    
    async def close(self):
        """Close HTTP client connection pool"""
        await self.client.aclose()
        logger.info("Data API client closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

