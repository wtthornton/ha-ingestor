"""
Devices and Entities Endpoints for Data API
Migrated from admin-api as part of Epic 13 Story 13.2
Story 22.2: Updated to use SQLite storage
"""

import logging
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from shared.influxdb_query_client import InfluxDBQueryClient

# Story 22.2: SQLite models and database
from .database import get_db
from .models import Device, Entity

logger = logging.getLogger(__name__)


# Response Models
class DeviceResponse(BaseModel):
    """Device response model"""
    device_id: str = Field(description="Unique device identifier")
    name: str = Field(description="Device name")
    manufacturer: str = Field(description="Device manufacturer")
    model: str = Field(description="Device model")
    sw_version: Optional[str] = Field(default=None, description="Software/firmware version")
    area_id: Optional[str] = Field(default=None, description="Area/room ID")
    entity_count: int = Field(default=0, description="Number of entities")
    timestamp: str = Field(description="Last update timestamp")


class EntityResponse(BaseModel):
    """Entity response model"""
    entity_id: str = Field(description="Unique entity identifier")
    device_id: Optional[str] = Field(default=None, description="Associated device ID")
    domain: str = Field(description="Entity domain (light, sensor, etc)")
    platform: str = Field(description="Integration platform")
    unique_id: Optional[str] = Field(default=None, description="Unique ID within platform")
    area_id: Optional[str] = Field(default=None, description="Area/room ID")
    disabled: bool = Field(default=False, description="Whether entity is disabled")
    timestamp: str = Field(description="Last update timestamp")


class IntegrationResponse(BaseModel):
    """Integration/Config Entry response model"""
    entry_id: str = Field(description="Config entry ID")
    domain: str = Field(description="Integration domain")
    title: str = Field(description="Integration title")
    state: str = Field(description="Setup state")
    version: int = Field(default=1, description="Config version")
    timestamp: str = Field(description="Last update timestamp")


class DevicesListResponse(BaseModel):
    """Devices list response"""
    devices: List[DeviceResponse]
    count: int
    limit: int


class EntitiesListResponse(BaseModel):
    """Entities list response"""
    entities: List[EntityResponse]
    count: int
    limit: int


class IntegrationsListResponse(BaseModel):
    """Integrations list response"""
    integrations: List[IntegrationResponse]
    count: int


# Create router
router = APIRouter(tags=["Devices & Entities"])


# InfluxDB client (initialized on first use to avoid circular imports)
influxdb_client = InfluxDBQueryClient()


@router.get("/api/devices", response_model=DevicesListResponse)
async def list_devices(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of devices to return"),
    manufacturer: Optional[str] = Query(default=None, description="Filter by manufacturer"),
    model: Optional[str] = Query(default=None, description="Filter by model"),
    area_id: Optional[str] = Query(default=None, description="Filter by area/room"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all discovered devices from Home Assistant (SQLite storage)
    
    Story 22.2: Simple, fast SQLite queries with JOIN for entity counts
    """
    try:
        # Build query with entity count
        query = select(Device, func.count(Entity.entity_id).label('entity_count'))\
            .outerjoin(Entity, Device.device_id == Entity.device_id)\
            .group_by(Device.device_id)
        
        # Apply filters (simple WHERE clauses)
        if manufacturer:
            query = query.where(Device.manufacturer == manufacturer)
        if model:
            query = query.where(Device.model == model)
        if area_id:
            query = query.where(Device.area_id == area_id)
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute
        result = await db.execute(query)
        rows = result.all()
        
        # Convert to response
        device_responses = [
            DeviceResponse(
                device_id=device.device_id,
                name=device.name,
                manufacturer=device.manufacturer or "Unknown",
                model=device.model or "Unknown",
                sw_version=device.sw_version,
                area_id=device.area_id,
                entity_count=entity_count,
                timestamp=device.last_seen.isoformat() if device.last_seen else datetime.now().isoformat()
            )
            for device, entity_count in rows
        ]
        
        return DevicesListResponse(
            devices=device_responses,
            count=len(device_responses),
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing devices from SQLite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve devices: {str(e)}"
        )


@router.get("/api/devices/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    """Get device by ID (SQLite) - Story 22.2"""
    try:
        # Simple SELECT with entity count
        query = select(Device, func.count(Entity.entity_id).label('entity_count'))\
            .outerjoin(Entity, Device.device_id == Entity.device_id)\
            .where(Device.device_id == device_id)\
            .group_by(Device.device_id)
        
        result = await db.execute(query)
        row = result.first()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
        
        device, entity_count = row
        return DeviceResponse(
            device_id=device.device_id,
            name=device.name,
            manufacturer=device.manufacturer or "Unknown",
            model=device.model or "Unknown",
            sw_version=device.sw_version,
            area_id=device.area_id,
            entity_count=entity_count,
            timestamp=device.last_seen.isoformat() if device.last_seen else datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve device: {str(e)}")


@router.get("/api/entities", response_model=EntitiesListResponse)
async def list_entities(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of entities to return"),
    domain: Optional[str] = Query(default=None, description="Filter by domain (light, sensor, etc)"),
    platform: Optional[str] = Query(default=None, description="Filter by platform"),
    device_id: Optional[str] = Query(default=None, description="Filter by device ID"),
    db: AsyncSession = Depends(get_db)
):
    """List entities (SQLite) - Story 22.2"""
    try:
        # Build query
        query = select(Entity)
        
        # Apply filters
        if domain:
            query = query.where(Entity.domain == domain)
        if platform:
            query = query.where(Entity.platform == platform)
        if device_id:
            query = query.where(Entity.device_id == device_id)
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute
        result = await db.execute(query)
        entities_data = result.scalars().all()
        
        # Convert to response
        entity_responses = [
            EntityResponse(
                entity_id=entity.entity_id,
                device_id=entity.device_id,
                domain=entity.domain,
                platform=entity.platform or "unknown",
                unique_id=entity.unique_id,
                area_id=entity.area_id,
                disabled=entity.disabled,
                timestamp=entity.created_at.isoformat() if entity.created_at else datetime.now().isoformat()
            )
            for entity in entities_data
        ]
        
        return EntitiesListResponse(
            entities=entity_responses,
            count=len(entity_responses),
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error listing entities from SQLite: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entities: {str(e)}")


@router.get("/api/entities/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str, db: AsyncSession = Depends(get_db)):
    """Get entity by ID (SQLite) - Story 22.2"""
    try:
        # Simple SELECT
        result = await db.execute(select(Entity).where(Entity.entity_id == entity_id))
        entity = result.scalar_one_or_none()
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
        
        return EntityResponse(
            entity_id=entity.entity_id,
            device_id=entity.device_id,
            domain=entity.domain,
            platform=entity.platform or "unknown",
            unique_id=entity.unique_id,
            area_id=entity.area_id,
            disabled=entity.disabled,
            timestamp=entity.created_at.isoformat() if entity.created_at else datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve entity: {str(e)}")


@router.get("/api/integrations", response_model=IntegrationsListResponse)
async def list_integrations(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of integrations to return")
):
    """
    List all Home Assistant integrations (config entries)
    
    Returns all discovered integrations with their setup status.
    """
    try:
        # Query config entries from InfluxDB
        # Ensure client is connected
        if not influxdb_client.is_connected:
            await influxdb_client.connect()
        
        query = f'''
            from(bucket: "home_assistant_events")
                |> range(start: -90d)
                |> filter(fn: (r) => r["_measurement"] == "config_entries")
                |> last()
                |> limit(n: {limit})
        '''
        
        results = await influxdb_client._execute_query(query)
        
        # Convert results to response models
        integrations = []
        for record in results:
            # Convert timestamp to string if needed
            timestamp = record.get("_time", datetime.now())
            if not isinstance(timestamp, str):
                timestamp = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)
            
            integration = IntegrationResponse(
                entry_id=record.get("entry_id", ""),
                domain=record.get("domain", "unknown"),
                title=record.get("title", "Unknown"),
                state=record.get("state", "unknown"),
                version=int(record.get("version", 1)),
                timestamp=timestamp
            )
            integrations.append(integration)
        
        return IntegrationsListResponse(
            integrations=integrations,
            count=len(integrations)
        )
        
    except Exception as e:
        logger.error(f"Error listing integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve integrations: {str(e)}"
        )


# Helper functions
def _build_devices_query(filters: Dict[str, str], limit: int) -> str:
    """Build Flux query for devices with filters"""
    query = f'''
        from(bucket: "home_assistant_events")
            |> range(start: -90d)
            |> filter(fn: (r) => r["_measurement"] == "devices")
    '''
    
    # Add filters
    if filters.get("manufacturer"):
        query += f'\n    |> filter(fn: (r) => r["manufacturer"] == "{filters["manufacturer"]}")'
    if filters.get("model"):
        query += f'\n    |> filter(fn: (r) => r["model"] == "{filters["model"]}")'
    if filters.get("area_id"):
        query += f'\n    |> filter(fn: (r) => r["area_id"] == "{filters["area_id"]}")'
    
    query += f'\n    |> last()\n    |> limit(n: {limit})'
    
    return query


def _build_entities_query(filters: Dict[str, str], limit: int) -> str:
    """Build Flux query for entities with filters"""
    query = f'''
        from(bucket: "home_assistant_events")
            |> range(start: -90d)
            |> filter(fn: (r) => r["_measurement"] == "entities")
    '''
    
    # Add filters
    if filters.get("domain"):
        query += f'\n    |> filter(fn: (r) => r["domain"] == "{filters["domain"]}")'
    if filters.get("platform"):
        query += f'\n    |> filter(fn: (r) => r["platform"] == "{filters["platform"]}")'
    if filters.get("device_id"):
        query += f'\n    |> filter(fn: (r) => r["device_id"] == "{filters["device_id"]}")'
    
    query += f'\n    |> last()\n    |> limit(n: {limit})'
    
    return query

