"""
Weather API Service - Simple, single-file implementation
Following carbon-intensity and air-quality service patterns
Epic 31, Stories 31.1-31.3
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from influxdb_client_3 import InfluxDBClient3, Point

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from shared.logging_config import setup_logging
from .health_check import HealthCheckHandler

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logging("weather-api")


# Pydantic Models
class WeatherResponse(BaseModel):
    """Current weather response"""
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    condition: str
    description: str
    wind_speed: float
    cloudiness: int
    location: str
    timestamp: str


class WeatherService:
    """Simple weather service - fetch, cache, store"""
    
    def __init__(self):
        # OpenWeatherMap config
        self.api_key = os.getenv('WEATHER_API_KEY')
        self.location = os.getenv('WEATHER_LOCATION', 'Las Vegas')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # InfluxDB config
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home_assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'weather_data')
        
        # Cache (simple dict with timestamp)
        self.cached_weather: Optional[Dict[str, Any]] = None
        self.cache_time: Optional[datetime] = None
        self.cache_ttl = int(os.getenv('CACHE_TTL_SECONDS', '900'))  # 15 minutes
        
        # Components
        self.session: Optional[aiohttp.ClientSession] = None
        self.influxdb_client: Optional[InfluxDBClient3] = None
        self.health_handler = HealthCheckHandler()
        
        # Stats
        self.fetch_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        if not self.api_key:
            logger.warning("WEATHER_API_KEY not set - service will run in standby mode")
        if not self.influxdb_token:
            raise ValueError("INFLUXDB_TOKEN required")
    
    async def startup(self):
        """Initialize service"""
        logger.info("Initializing Weather API Service...")
        
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        
        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_bucket,
            org=self.influxdb_org
        )
        
        logger.info("Weather API Service initialized")
    
    async def shutdown(self):
        """Cleanup"""
        logger.info("Shutting down Weather API Service...")
        
        if self.session:
            await self.session.close()
        
        if self.influxdb_client:
            self.influxdb_client.close()
    
    async def fetch_weather(self) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeatherMap"""
        if not self.api_key:
            return self.cached_weather
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": self.location,
                "appid": self.api_key,
                "units": "metric"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    weather = {
                        'temperature': data.get("main", {}).get("temp", 0),
                        'feels_like': data.get("main", {}).get("feels_like", 0),
                        'humidity': data.get("main", {}).get("humidity", 0),
                        'pressure': data.get("main", {}).get("pressure", 0),
                        'condition': data.get("weather", [{}])[0].get("main", "Unknown"),
                        'description': data.get("weather", [{}])[0].get("description", ""),
                        'wind_speed': data.get("wind", {}).get("speed", 0),
                        'cloudiness': data.get("clouds", {}).get("all", 0),
                        'location': data.get("name", self.location),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    self.fetch_count += 1
                    logger.info(f"Fetched weather: {weather['temperature']}°C, {weather['condition']}")
                    return weather
                else:
                    logger.error(f"OpenWeatherMap API error: {response.status}")
                    return self.cached_weather
                    
        except Exception as e:
            logger.error(f"Error fetching weather: {e}")
            return self.cached_weather
    
    async def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """Get current weather (cache-first)"""
        # Check cache
        if self.cached_weather and self.cache_time:
            age = (datetime.utcnow() - self.cache_time).total_seconds()
            if age < self.cache_ttl:
                self.cache_hits += 1
                return self.cached_weather
        
        # Cache miss - fetch
        self.cache_misses += 1
        weather = await self.fetch_weather()
        
        if weather:
            self.cached_weather = weather
            self.cache_time = datetime.utcnow()
            
            # Write to InfluxDB
            await self.store_in_influxdb(weather)
        
        return weather
    
    async def store_in_influxdb(self, weather: Dict[str, Any]):
        """Store weather in InfluxDB"""
        if not weather:
            return
        
        try:
            point = Point("weather") \
                .tag("location", weather['location']) \
                .tag("condition", weather['condition']) \
                .field("temperature", float(weather['temperature'])) \
                .field("humidity", int(weather['humidity'])) \
                .field("pressure", int(weather['pressure'])) \
                .field("wind_speed", float(weather['wind_speed'])) \
                .field("cloudiness", int(weather['cloudiness'])) \
                .time(datetime.fromisoformat(weather['timestamp']))
            
            self.influxdb_client.write(point)
            logger.info("Weather data written to InfluxDB")
            
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
    
    async def run_continuous(self):
        """Background fetch loop"""
        logger.info(f"Starting continuous fetch (every {self.cache_ttl}s)")
        
        while True:
            try:
                await self.get_current_weather()
                await asyncio.sleep(self.cache_ttl)
            except Exception as e:
                logger.error(f"Error in continuous loop: {e}")
                await asyncio.sleep(300)


# Global service instance
weather_service = None


async def startup():
    """Startup handler"""
    global weather_service
    weather_service = WeatherService()
    await weather_service.startup()
    # Start background fetch
    asyncio.create_task(weather_service.run_continuous())


async def shutdown():
    """Shutdown handler"""
    if weather_service:
        await weather_service.shutdown()


# FastAPI app
app = FastAPI(
    title="Weather API Service",
    description="Standalone weather data service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lifecycle
app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "weather-api",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/health", "/current-weather", "/cache/stats"]
    }


@app.get("/health")
async def health():
    """Health check"""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return await weather_service.health_handler.handle()


@app.get("/current-weather", response_model=WeatherResponse)
async def get_current_weather():
    """Get current weather (Story 31.3)"""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    weather = await weather_service.get_current_weather()
    
    if not weather:
        raise HTTPException(status_code=503, detail="Weather data unavailable")
    
    return WeatherResponse(**weather)


@app.get("/cache/stats")
async def cache_stats():
    """Cache statistics"""
    if not weather_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    total = weather_service.cache_hits + weather_service.cache_misses
    hit_rate = (weather_service.cache_hits / total * 100) if total > 0 else 0
    
    return {
        "hits": weather_service.cache_hits,
        "misses": weather_service.cache_misses,
        "hit_rate": round(hit_rate, 2),
        "fetch_count": weather_service.fetch_count,
        "ttl_seconds": weather_service.cache_ttl,
        "last_cache_time": weather_service.cache_time.isoformat() if weather_service.cache_time else None
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('SERVICE_PORT', '8009'))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
