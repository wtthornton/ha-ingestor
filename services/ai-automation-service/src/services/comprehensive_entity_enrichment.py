"""
Comprehensive Entity Enrichment Service

Combines ALL available data sources to provide complete entity context:
- Device Intelligence (capabilities, health scores, manufacturer, model, area)
- Entity Attributes (friendly_name, state, attributes, integration, supported_features)
- HA Client (entity states, device data, area data)
- Data API (device metadata, historical patterns)
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def enrich_entities_comprehensively(
    entity_ids: Set[str],
    ha_client: Optional[Any] = None,
    device_intelligence_client: Optional[Any] = None,
    data_api_client: Optional[Any] = None,
    include_historical: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Comprehensive entity enrichment using ALL available data sources.
    
    Args:
        entity_ids: Set of entity IDs to enrich
        ha_client: HomeAssistantClient for entity states and attributes
        device_intelligence_client: DeviceIntelligenceClient for device intelligence data
        data_api_client: DataAPIClient for historical data and metadata
        include_historical: Whether to include historical usage patterns
        
    Returns:
        Dictionary mapping entity_id to comprehensive enriched data
    """
    enriched: Dict[str, Dict[str, Any]] = {}
    
    if not entity_ids:
        logger.warning("No entity IDs provided for enrichment")
        return enriched
    
    logger.info(f"🔍 Starting comprehensive enrichment for {len(entity_ids)} entities")
    
    # Step 1: Get entity attributes from HA (fast, always available)
    # Use parallel enrichment to prevent timeout
    ha_enriched = {}
    if ha_client:
        try:
            from ..services.entity_attribute_service import EntityAttributeService
            import asyncio
            
            attribute_service = EntityAttributeService(ha_client)
            
            # Add timeout to HA enrichment to prevent gateway timeout
            try:
                ha_enriched = await asyncio.wait_for(
                    attribute_service.enrich_multiple_entities(list(entity_ids)),
                    timeout=10.0  # 10 second timeout for HA enrichment
                )
                logger.info(f"✅ HA enrichment: {len(ha_enriched)} entities")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ HA enrichment timed out after 10s for {len(entity_ids)} entities")
                ha_enriched = {}  # Continue with empty HA data rather than failing completely
        except Exception as e:
            logger.warning(f"⚠️ HA enrichment failed: {e}")
    
    # Step 2: Get device intelligence data (capabilities, health, manufacturer, model)
    device_intel_data = {}
    if device_intelligence_client:
        try:
            device_intel_data = await _get_device_intelligence_for_entities(
                entity_ids, ha_enriched, device_intelligence_client
            )
            logger.info(f"✅ Device Intelligence enrichment: {len(device_intel_data)} entities")
        except Exception as e:
            logger.warning(f"⚠️ Device Intelligence enrichment failed: {e}")
    
    # Step 3: Get historical usage patterns (optional)
    historical_data = {}
    if include_historical and data_api_client:
        try:
            historical_data = await _get_historical_patterns_for_entities(
                entity_ids, data_api_client
            )
            logger.info(f"✅ Historical data enrichment: {len(historical_data)} entities")
        except Exception as e:
            logger.warning(f"⚠️ Historical data enrichment failed: {e}")
    
    # Step 4: Combine all data sources for each entity
    for entity_id in entity_ids:
        combined = {
            'entity_id': entity_id,
            'domain': entity_id.split('.')[0] if '.' in entity_id else 'unknown',
            # HA Attributes data
            'friendly_name': None,
            'icon': None,
            'device_class': None,
            'unit_of_measurement': None,
            'state': 'unknown',
            'last_changed': None,
            'last_updated': None,
            'attributes': {},
            'is_group': False,
            'integration': 'unknown',
            'supported_features': None,
            'device_id': None,
            'area_id': None,
            # Device Intelligence data
            'device_name': None,
            'manufacturer': None,
            'model': None,
            'sw_version': None,
            'hw_version': None,
            'power_source': None,
            'area_name': None,
            'capabilities': [],
            'health_score': None,
            'last_seen': None,
            'device_class_from_intel': None,
            # Historical patterns (if requested)
            'usage_frequency': None,
            'common_states': [],
            'typical_usage_times': [],
            'recent_activity': None
        }
        
        # Merge HA enrichment data
        if entity_id in ha_enriched:
            ha_data = ha_enriched[entity_id]
            combined.update({
                'friendly_name': ha_data.get('friendly_name'),
                'icon': ha_data.get('icon'),
                'device_class': ha_data.get('device_class'),
                'unit_of_measurement': ha_data.get('unit_of_measurement'),
                'state': ha_data.get('state', 'unknown'),
                'last_changed': ha_data.get('last_changed'),
                'last_updated': ha_data.get('last_updated'),
                'attributes': ha_data.get('attributes', {}),
                'is_group': ha_data.get('is_group', False),
                'integration': ha_data.get('integration', 'unknown'),
                'supported_features': ha_data.get('supported_features'),
                'device_id': ha_data.get('device_id'),
                'area_id': ha_data.get('area_id')
            })
        
        # Merge Device Intelligence data
        if entity_id in device_intel_data:
            intel_data = device_intel_data[entity_id]
            combined.update({
                'device_name': intel_data.get('device_name'),
                'manufacturer': intel_data.get('manufacturer'),
                'model': intel_data.get('model'),
                'sw_version': intel_data.get('sw_version'),
                'hw_version': intel_data.get('hw_version'),
                'power_source': intel_data.get('power_source'),
                'area_name': intel_data.get('area_name'),
                'capabilities': intel_data.get('capabilities', []),
                'health_score': intel_data.get('health_score'),
                'last_seen': intel_data.get('last_seen'),
                'device_class_from_intel': intel_data.get('device_class')
            })
            # Use device intelligence area_name if HA area_id is missing
            if not combined.get('area_id') and intel_data.get('area_name'):
                combined['area_id'] = intel_data.get('area_id')
        
        # Merge historical patterns
        if entity_id in historical_data:
            hist_data = historical_data[entity_id]
            combined.update({
                'usage_frequency': hist_data.get('usage_frequency'),
                'common_states': hist_data.get('common_states', []),
                'typical_usage_times': hist_data.get('typical_usage_times', []),
                'recent_activity': hist_data.get('recent_activity')
            })
        
        enriched[entity_id] = combined
    
    logger.info(f"✅ Comprehensive enrichment complete: {len(enriched)}/{len(entity_ids)} entities")
    return enriched


async def _get_device_intelligence_for_entities(
    entity_ids: Set[str],
    ha_enriched: Dict[str, Dict[str, Any]],
    device_intelligence_client: Any
) -> Dict[str, Dict[str, Any]]:
    """
    Get device intelligence data for entities.
    
    Uses entity_id → device_id mapping from HA enrichment, then queries device intelligence.
    """
    device_intel_data = {}
    
    try:
        # Get all devices and build entity → device mapping (with timeout to prevent gateway timeout)
        import asyncio
        try:
            all_devices = await asyncio.wait_for(
                device_intelligence_client.get_all_devices(limit=200),  # Reduced from 500 to 200 for performance
                timeout=5.0  # 5 second timeout for get_all_devices
            )
        except asyncio.TimeoutError:
            logger.warning("⚠️ get_all_devices timed out after 5s, skipping device intelligence enrichment")
            return {}
        
        # Build mapping: entity_id → device
        entity_to_device = {}
        
        # Method 1: Use device_id from HA enrichment
        for entity_id, ha_data in ha_enriched.items():
            device_id = ha_data.get('device_id')
            if device_id:
                entity_to_device[entity_id] = device_id
        
        # Method 2: Search devices by entity ID
        for device in all_devices:
            if not isinstance(device, dict):
                continue
            
            device_entities = device.get('entities', []) or device.get('entity_ids', [])
            device_id = device.get('id') or device.get('device_id')
            
            if not device_id:
                continue
            
            for entity in device_entities:
                entity_id = entity if isinstance(entity, str) else entity.get('entity_id') if isinstance(entity, dict) else None
                if entity_id and entity_id in entity_ids and entity_id not in entity_to_device:
                    entity_to_device[entity_id] = device_id
        
        # Method 3: Query device details directly for each entity (fallback)
        for entity_id in entity_ids:
            if entity_id in entity_to_device:
                continue  # Already mapped
            
            # Try to find device by searching all devices
            for device in all_devices:
                if not isinstance(device, dict):
                    continue
                
                device_id = device.get('id') or device.get('device_id')
                device_name = device.get('name') or device.get('device_name') or ''
                device_entities = device.get('entities', []) or device.get('entity_ids', [])
                
                # Check if entity_id matches any device entity
                for ent in device_entities:
                    ent_id = ent if isinstance(ent, str) else ent.get('entity_id') if isinstance(ent, dict) else None
                    if ent_id == entity_id:
                        entity_to_device[entity_id] = device_id
                        break
                
                if entity_id in entity_to_device:
                    break
        
        # Get device details for mapped devices IN PARALLEL (performance fix for gateway timeout)
        import asyncio
        
        async def fetch_device_details(entity_id: str, device_id: str) -> tuple:
            """Fetch device details for a single entity"""
            try:
                device_details = await device_intelligence_client.get_device_details(device_id)
                if device_details:
                    # Extract entity-specific info if device has multiple entities
                    device_entities = device_details.get('entities', [])
                    entity_info = None
                    for ent in device_entities:
                        if isinstance(ent, dict) and ent.get('entity_id') == entity_id:
                            entity_info = ent
                            break
                        elif isinstance(ent, str) and ent == entity_id:
                            entity_info = {'entity_id': entity_id}
                            break
                    
                    return (entity_id, {
                        'device_name': device_details.get('name') or device_details.get('friendly_name'),
                        'manufacturer': device_details.get('manufacturer'),
                        'model': device_details.get('model'),
                        'sw_version': device_details.get('sw_version'),
                        'hw_version': device_details.get('hw_version'),
                        'power_source': device_details.get('power_source'),
                        'area_name': device_details.get('area_name'),
                        'area_id': device_details.get('area_id'),
                        'capabilities': device_details.get('capabilities', []),
                        'health_score': device_details.get('health_score'),
                        'last_seen': device_details.get('last_seen'),
                        'device_class': device_details.get('device_class'),
                        'integration': device_details.get('integration'),
                        'entity_state': entity_info.get('state') if entity_info else None,
                        'entity_attributes': entity_info.get('attributes', {}) if entity_info and isinstance(entity_info, dict) else {}
                    })
                return (entity_id, None)
            except Exception as e:
                logger.debug(f"Could not get device details for {device_id}: {e}")
                return (entity_id, None)
        
        # Fetch all device details in parallel (major performance improvement)
        if entity_to_device:
            logger.debug(f"📡 Fetching device details for {len(entity_to_device)} devices in parallel...")
            fetch_tasks = [
                fetch_device_details(entity_id, device_id)
                for entity_id, device_id in entity_to_device.items()
            ]
            
            # Execute all fetches in parallel with timeout
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*fetch_tasks, return_exceptions=True),
                    timeout=10.0  # 10 second timeout for all parallel fetches
                )
                
                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        logger.debug(f"Device details fetch error: {result}")
                        continue
                    entity_id, device_data = result
                    if device_data:
                        device_intel_data[entity_id] = device_data
                        logger.debug(f"📋 Device Intelligence for {entity_id}: manufacturer={device_data.get('manufacturer')}, health={device_data.get('health_score')}")
                
                logger.debug(f"✅ Fetched {len(device_intel_data)} device details in parallel")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ Device details fetch timed out after 10s (got {len(device_intel_data)}/{len(entity_to_device)} results)")
            except Exception as e:
                logger.warning(f"⚠️ Error in parallel device details fetch: {e}")
    
    except Exception as e:
        logger.error(f"Device Intelligence enrichment error: {e}", exc_info=True)
    
    return device_intel_data


async def _get_historical_patterns_for_entities(
    entity_ids: Set[str],
    data_api_client: Any
) -> Dict[str, Dict[str, Any]]:
    """
    Get historical usage patterns for entities (optional, for advanced context).
    
    This provides usage frequency, common states, typical usage times, etc.
    """
    historical_data = {}
    
    try:
        # Query recent events for each entity (last 7 days)
        # Note: This is optional as it may be slow for many entities
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        for entity_id in entity_ids:
            try:
                # Query events for this entity
                # This would require data_api_client to have an events query method
                # For now, we'll skip detailed historical analysis as it requires specific API endpoints
                # Future enhancement: Add historical pattern analysis
                pass
            except Exception as e:
                logger.debug(f"Historical data query failed for {entity_id}: {e}")
    
    except Exception as e:
        logger.warning(f"Historical pattern enrichment error: {e}")
    
    return historical_data


def format_comprehensive_enrichment_for_prompt(
    enriched_entities: Dict[str, Dict[str, Any]]
) -> str:
    """
    Format comprehensive enrichment data for LLM prompts.
    
    Creates a detailed, structured text representation of all entity data.
    """
    if not enriched_entities:
        return "No entity data available."
    
    sections = []
    
    for entity_id, data in enriched_entities.items():
        entity_section = []
        
        # Entity identification
        friendly_name = data.get('friendly_name') or data.get('device_name') or entity_id
        entity_section.append(f"**{friendly_name}** ({entity_id})")
        
        # Basic info
        if data.get('device_class'):
            entity_section.append(f"  Type: {data['device_class']}")
        if data.get('domain'):
            entity_section.append(f"  Domain: {data['domain']}")
        if data.get('state') and data.get('state') != 'unknown':
            entity_section.append(f"  Current State: {data['state']}")
        
        # Location
        area_info = []
        if data.get('area_name'):
            area_info.append(data['area_name'])
        elif data.get('area_id'):
            area_info.append(data['area_id'])
        if area_info:
            entity_section.append(f"  Location: {', '.join(area_info)}")
        
        # Device information
        device_info = []
        if data.get('manufacturer'):
            device_info.append(data['manufacturer'])
        if data.get('model'):
            device_info.append(data['model'])
        if device_info:
            entity_section.append(f"  Device: {' '.join(device_info)}")
        
        if data.get('integration') and data.get('integration') != 'unknown':
            entity_section.append(f"  Integration: {data['integration']}")
        
        # Health and status
        if data.get('health_score') is not None:
            health_status = "Excellent" if data['health_score'] > 80 else "Good" if data['health_score'] > 60 else "Fair"
            entity_section.append(f"  Health: {data['health_score']}/100 ({health_status})")
        
        # Capabilities (detailed)
        capabilities = data.get('capabilities', [])
        if capabilities:
            cap_list = []
            for cap in capabilities:
                if isinstance(cap, dict):
                    feature = cap.get('feature', 'unknown')
                    supported = cap.get('supported', False)
                    if supported:
                        cap_type = cap.get('type', '')
                        if cap_type:
                            cap_list.append(f"{feature} ({cap_type})")
                        else:
                            cap_list.append(feature)
                else:
                    cap_list.append(str(cap))
            if cap_list:
                entity_section.append(f"  Capabilities: {', '.join(cap_list[:5])}" + (f" (+{len(cap_list) - 5} more)" if len(cap_list) > 5 else ""))
        
        # Supported features (for lights, etc.)
        if data.get('supported_features'):
            entity_section.append(f"  Supported Features: {data['supported_features']}")
        
        # Group indicator
        if data.get('is_group'):
            entity_section.append(f"  ⚠️ This is a GROUP entity (controls multiple devices)")
        
        # Software version (if available)
        if data.get('sw_version'):
            entity_section.append(f"  Software Version: {data['sw_version']}")
        
        # Last seen (device intelligence)
        if data.get('last_seen'):
            entity_section.append(f"  Last Seen: {data['last_seen']}")
        
        sections.append("\n".join(entity_section))
    
    return "\n\n".join(sections)

