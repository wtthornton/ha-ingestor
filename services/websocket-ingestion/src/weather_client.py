"""
Weather API Client for OpenWeatherMap Integration
"""

import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class WeatherData:
    """Weather data model"""
    
    def __init__(self, data: Dict[str, Any], source: str = "openweathermap"):
        self.temperature = data.get("main", {}).get("temp")
        self.feels_like = data.get("main", {}).get("feels_like")
        self.humidity = data.get("main", {}).get("humidity")
        self.pressure = data.get("main", {}).get("pressure")
        self.weather_condition = data.get("weather", [{}])[0].get("main")
        self.weather_description = data.get("weather", [{}])[0].get("description")
        self.wind_speed = data.get("wind", {}).get("speed")
        self.wind_direction = data.get("wind", {}).get("deg")
        self.cloudiness = data.get("clouds", {}).get("all")
        self.visibility = data.get("visibility")
        self.timestamp = datetime.now().isoformat()
        self.source = source
        self.location = data.get("name")
        self.country = data.get("sys", {}).get("country")
        self.coordinates = {
            "lat": data.get("coord", {}).get("lat"),
            "lon": data.get("coord", {}).get("lon")
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert weather data to dictionary"""
        return {
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "weather_condition": self.weather_condition,
            "weather_description": self.weather_description,
            "wind_speed": self.wind_speed,
            "wind_direction": self.wind_direction,
            "cloudiness": self.cloudiness,
            "visibility": self.visibility,
            "timestamp": self.timestamp,
            "source": self.source,
            "location": self.location,
            "country": self.country,
            "coordinates": self.coordinates
        }


class OpenWeatherMapClient:
    """OpenWeatherMap API client"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openweathermap.org/data/2.5"):
        """
        Initialize OpenWeatherMap client
        
        Args:
            api_key: OpenWeatherMap API key
            base_url: Base URL for OpenWeatherMap API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.request_count = 0
        self.last_request_time: Optional[datetime] = None
        self.rate_limit_delay = 1.0  # seconds between requests
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_error: Optional[str] = None
    
    async def start(self):
        """Start the weather client"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            logger.info("Weather client started")
    
    async def stop(self):
        """Stop the weather client"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Weather client stopped")
    
    async def get_current_weather(self, location: str) -> Optional[WeatherData]:
        """
        Get current weather for a location
        
        Args:
            location: Location name or coordinates (lat,lon)
            
        Returns:
            WeatherData object or None if failed
        """
        if not self.session:
            await self.start()
        
        # Apply rate limiting
        await self._apply_rate_limit()
        
        try:
            # Build API URL
            url = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"  # Use metric units
            }
            
            # Make API request
            async with self.session.get(url, params=params) as response:
                self.total_requests += 1
                
                if response.status == 200:
                    data = await response.json()
                    self.successful_requests += 1
                    self.last_error = None
                    
                    logger.debug(f"Successfully fetched weather for {location}")
                    return WeatherData(data)
                    
                else:
                    error_text = await response.text()
                    self.failed_requests += 1
                    self.last_error = f"API error {response.status}: {error_text}"
                    
                    logger.error(f"Failed to fetch weather for {location}: {self.last_error}")
                    return None
                    
        except asyncio.TimeoutError:
            self.failed_requests += 1
            self.last_error = "Request timeout"
            logger.error(f"Timeout fetching weather for {location}")
            return None
            
        except Exception as e:
            self.failed_requests += 1
            self.last_error = str(e)
            logger.error(f"Error fetching weather for {location}: {e}")
            return None
    
    async def get_current_weather_by_coordinates(self, lat: float, lon: float) -> Optional[WeatherData]:
        """
        Get current weather by coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            WeatherData object or None if failed
        """
        location = f"{lat},{lon}"
        return await self.get_current_weather(location)
    
    async def _apply_rate_limit(self):
        """Apply rate limiting"""
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                await asyncio.sleep(sleep_time)
        
        self.last_request_time = datetime.now()
    
    def configure_rate_limit(self, delay: float):
        """Configure rate limit delay"""
        if delay < 0:
            raise ValueError("Rate limit delay must be non-negative")
        
        self.rate_limit_delay = delay
        logger.info(f"Updated rate limit delay to {delay}s")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        success_rate = 0
        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 2),
            "last_error": self.last_error,
            "rate_limit_delay": self.rate_limit_delay,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
        }
    
    def reset_statistics(self):
        """Reset client statistics"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_error = None
        self.last_request_time = None
        logger.info("Weather client statistics reset")
