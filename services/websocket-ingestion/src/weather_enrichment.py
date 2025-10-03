"""
Weather Enrichment Service for Event Processing
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .weather_client import OpenWeatherMapClient, WeatherData
from .weather_cache import WeatherCache

logger = logging.getLogger(__name__)


class WeatherEnrichmentService:
    """Service for enriching events with weather data"""
    
    def __init__(self, api_key: str, default_location: str = "London,UK"):
        """
        Initialize weather enrichment service
        
        Args:
            api_key: OpenWeatherMap API key
            default_location: Default location for weather data
        """
        self.weather_client = OpenWeatherMapClient(api_key)
        self.weather_cache = WeatherCache(max_size=1000, default_ttl=300)  # 5 minutes TTL
        
        # Configuration
        self.default_location = default_location
        self.enrichment_enabled = True
        self.fallback_to_cache = True
        
        # Statistics
        self.total_events_processed = 0
        self.successful_enrichments = 0
        self.failed_enrichments = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Processing start time
        self.processing_start_time = datetime.now()
    
    async def start(self):
        """Start the weather enrichment service"""
        await self.weather_client.start()
        await self.weather_cache.start()
        logger.info("Weather enrichment service started")
    
    async def stop(self):
        """Stop the weather enrichment service"""
        await self.weather_cache.stop()
        await self.weather_client.stop()
        logger.info("Weather enrichment service stopped")
    
    async def enrich_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich an event with weather data
        
        Args:
            event_data: Event data to enrich
            
        Returns:
            Enriched event data
        """
        self.total_events_processed += 1
        
        if not self.enrichment_enabled:
            logger.debug("Weather enrichment is disabled")
            return event_data
        
        try:
            # Determine location for weather data
            location = self._determine_location(event_data)
            
            # Get weather data
            weather_data = await self._get_weather_data(location)
            
            if weather_data:
                # Add weather data to event
                enriched_event = event_data.copy()
                enriched_event["weather"] = weather_data.to_dict()
                enriched_event["weather_enriched"] = True
                enriched_event["weather_location"] = location
                
                self.successful_enrichments += 1
                logger.debug(f"Successfully enriched event with weather data for {location}")
                
                return enriched_event
            else:
                # Weather data unavailable
                enriched_event = event_data.copy()
                enriched_event["weather_enriched"] = False
                enriched_event["weather_error"] = "Weather data unavailable"
                
                self.failed_enrichments += 1
                logger.warning(f"Failed to enrich event with weather data for {location}")
                
                return enriched_event
                
        except Exception as e:
            logger.error(f"Error enriching event: {e}")
            
            # Return original event with error info
            enriched_event = event_data.copy()
            enriched_event["weather_enriched"] = False
            enriched_event["weather_error"] = str(e)
            
            self.failed_enrichments += 1
            return enriched_event
    
    def _determine_location(self, event_data: Dict[str, Any]) -> str:
        """
        Determine location for weather data based on event
        
        Args:
            event_data: Event data
            
        Returns:
            Location string for weather API
        """
        # Try to extract location from event data
        # This could be enhanced to use entity location data
        
        # For now, use default location
        # In a real implementation, you might:
        # - Extract location from entity_id patterns
        # - Use Home Assistant location data
        # - Use IP geolocation
        # - Use user-configured location mapping
        
        return self.default_location
    
    async def _get_weather_data(self, location: str) -> Optional[WeatherData]:
        """
        Get weather data for a location
        
        Args:
            location: Location string
            
        Returns:
            WeatherData object or None if unavailable
        """
        # Try cache first
        cached_data = await self.weather_cache.get(location)
        if cached_data:
            self.cache_hits += 1
            logger.debug(f"Using cached weather data for {location}")
            return WeatherData(cached_data, source="cache")
        
        self.cache_misses += 1
        
        # Fetch from API
        weather_data = await self.weather_client.get_current_weather(location)
        
        if weather_data:
            # Cache the data
            await self.weather_cache.put(location, weather_data.to_dict())
            logger.debug(f"Fetched and cached weather data for {location}")
            return weather_data
        else:
            # API failed, try fallback to cache if enabled
            if self.fallback_to_cache:
                # Try to get any cached data (even if expired)
                for key in self.weather_cache.get_cache_keys():
                    cached_data = await self.weather_cache.get(key)
                    if cached_data:
                        logger.warning(f"Using fallback cached weather data from {key} for {location}")
                        return WeatherData(cached_data, source="fallback_cache")
            
            logger.error(f"No weather data available for {location}")
            return None
    
    def configure_default_location(self, location: str):
        """Configure default location"""
        self.default_location = location
        logger.info(f"Updated default location to {location}")
    
    def configure_enrichment(self, enabled: bool, fallback_to_cache: bool = True):
        """Configure enrichment settings"""
        self.enrichment_enabled = enabled
        self.fallback_to_cache = fallback_to_cache
        logger.info(f"Updated enrichment settings: enabled={enabled}, fallback_to_cache={fallback_to_cache}")
    
    def configure_cache_settings(self, max_size: int, ttl: int):
        """Configure cache settings"""
        self.weather_cache.configure_max_size(max_size)
        self.weather_cache.configure_ttl(ttl)
        logger.info(f"Updated cache settings: max_size={max_size}, ttl={ttl}s")
    
    def configure_rate_limit(self, delay: float):
        """Configure API rate limit"""
        self.weather_client.configure_rate_limit(delay)
        logger.info(f"Updated API rate limit to {delay}s")
    
    def get_enrichment_statistics(self) -> Dict[str, Any]:
        """Get enrichment statistics"""
        uptime = (datetime.now() - self.processing_start_time).total_seconds()
        
        # Calculate success rate
        success_rate = 0
        if self.total_events_processed > 0:
            success_rate = (self.successful_enrichments / self.total_events_processed) * 100
        
        # Calculate cache hit rate
        cache_hit_rate = 0
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            cache_hit_rate = (self.cache_hits / total_cache_requests) * 100
        
        return {
            "is_running": self.enrichment_enabled,
            "default_location": self.default_location,
            "fallback_to_cache": self.fallback_to_cache,
            "total_events_processed": self.total_events_processed,
            "successful_enrichments": self.successful_enrichments,
            "failed_enrichments": self.failed_enrichments,
            "success_rate": round(success_rate, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "uptime_seconds": round(uptime, 2),
            "weather_client_stats": self.weather_client.get_statistics(),
            "weather_cache_stats": self.weather_cache.get_cache_statistics()
        }
    
    def reset_statistics(self):
        """Reset enrichment statistics"""
        self.total_events_processed = 0
        self.successful_enrichments = 0
        self.failed_enrichments = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.processing_start_time = datetime.now()
        
        # Reset component statistics
        self.weather_client.reset_statistics()
        self.weather_cache.reset_statistics()
        
        logger.info("Weather enrichment statistics reset")
