"""
Air Quality Service Main Entry Point
Fetches AQI data from AirNow API
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import aiohttp
from aiohttp import web
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point

sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from shared.logging_config import setup_logging, log_with_context, log_error_with_context

from health_check import HealthCheckHandler

load_dotenv()

logger = setup_logging("air-quality-service")


class AirQualityService:
    """Fetch and store air quality data from AirNow API"""
    
    def __init__(self):
        self.api_key = os.getenv('AIRNOW_API_KEY')
        self.latitude = os.getenv('LATITUDE', '36.1699')  # Las Vegas default
        self.longitude = os.getenv('LONGITUDE', '-115.1398')
        self.base_url = "https://www.airnowapi.org/aq/observation/latLong/current/"
        
        # InfluxDB configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home_assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'events')
        
        # Service configuration
        self.fetch_interval = 3600  # 1 hour
        self.cache_duration = 60  # minutes
        
        # Cache
        self.cached_data: Optional[Dict[str, Any]] = None
        self.last_fetch_time: Optional[datetime] = None
        self.last_category: Optional[str] = None
        
        # Components
        self.session: Optional[aiohttp.ClientSession] = None
        self.influxdb_client: Optional[InfluxDBClient3] = None
        self.health_handler = HealthCheckHandler()
        
        if not self.api_key:
            raise ValueError("AIRNOW_API_KEY environment variable is required")
        if not self.influxdb_token:
            raise ValueError("INFLUXDB_TOKEN environment variable is required")
    
    async def startup(self):
        """Initialize service"""
        logger.info("Initializing Air Quality Service...")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        
        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_bucket,
            org=self.influxdb_org
        )
        
        logger.info("Air Quality Service initialized")
    
    async def shutdown(self):
        """Cleanup"""
        logger.info("Shutting down Air Quality Service...")
        
        if self.session:
            await self.session.close()
        
        if self.influxdb_client:
            self.influxdb_client.close()
    
    async def fetch_air_quality(self) -> Optional[Dict[str, Any]]:
        """Fetch AQI from AirNow API"""
        
        try:
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "format": "application/json",
                "API_KEY": self.api_key
            }
            
            log_with_context(
                logger, "INFO",
                f"Fetching AQI for location {self.latitude},{self.longitude}",
                service="air-quality-service"
            )
            
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    raw_data = await response.json()
                    
                    if not raw_data:
                        logger.warning("AirNow API returned empty data")
                        return self.cached_data
                    
                    # Parse response (multiple parameters returned)
                    data = {
                        'aqi': 0,
                        'category': 'Unknown',
                        'parameter': 'Combined',
                        'pm25': 0,
                        'pm10': 0,
                        'ozone': 0,
                        'timestamp': datetime.now()
                    }
                    
                    # Find highest AQI (worst parameter)
                    for param_data in raw_data:
                        aqi = param_data.get('AQI', 0)
                        if aqi > data['aqi']:
                            data['aqi'] = aqi
                            data['category'] = param_data.get('Category', {}).get('Name', 'Unknown')
                            data['parameter'] = param_data.get('ParameterName', 'Unknown')
                        
                        # Store individual parameters
                        param_name = param_data.get('ParameterName', '').lower()
                        if 'pm2.5' in param_name:
                            data['pm25'] = aqi
                        elif 'pm10' in param_name:
                            data['pm10'] = aqi
                        elif 'ozone' in param_name:
                            data['ozone'] = aqi
                    
                    # Log category changes
                    if self.last_category and self.last_category != data['category']:
                        logger.warning(f"AQI category changed: {self.last_category} → {data['category']}")
                    
                    self.last_category = data['category']
                    self.cached_data = data
                    self.last_fetch_time = datetime.now()
                    
                    self.health_handler.last_successful_fetch = datetime.now()
                    self.health_handler.total_fetches += 1
                    
                    logger.info(f"AQI: {data['aqi']} ({data['category']})")
                    
                    return data
                    
                else:
                    logger.error(f"AirNow API returned status {response.status}")
                    self.health_handler.failed_fetches += 1
                    return self.cached_data
                    
        except Exception as e:
            log_error_with_context(
                logger,
                f"Error fetching AQI: {e}",
                service="air-quality-service",
                error=str(e)
            )
            self.health_handler.failed_fetches += 1
            return self.cached_data
    
    async def store_in_influxdb(self, data: Dict[str, Any]):
        """Store AQI data in InfluxDB"""
        
        if not data:
            return
        
        try:
            point = Point("air_quality") \
                .tag("location", f"{self.latitude},{self.longitude}") \
                .tag("category", data['category']) \
                .tag("parameter", data['parameter']) \
                .field("aqi", int(data['aqi'])) \
                .field("pm25", int(data['pm25'])) \
                .field("pm10", int(data['pm10'])) \
                .field("ozone", int(data['ozone'])) \
                .time(data['timestamp'])
            
            self.influxdb_client.write(point)
            
            logger.info("AQI data written to InfluxDB")
            
        except Exception as e:
            log_error_with_context(
                logger,
                f"Error writing to InfluxDB: {e}",
                service="air-quality-service",
                error=str(e)
            )
    
    async def get_current_aqi(self, request):
        """API endpoint for current AQI"""
        
        if self.cached_data:
            return web.json_response({
                'aqi': self.cached_data['aqi'],
                'category': self.cached_data['category'],
                'timestamp': self.last_fetch_time.isoformat() if self.last_fetch_time else None
            })
        else:
            return web.json_response({'error': 'No data available'}, status=503)
    
    async def run_continuous(self):
        """Run continuous data collection loop"""
        
        logger.info(f"Starting continuous AQI monitoring (every {self.fetch_interval}s)")
        
        while True:
            try:
                data = await self.fetch_air_quality()
                
                if data:
                    await self.store_in_influxdb(data)
                
                await asyncio.sleep(self.fetch_interval)
                
            except Exception as e:
                log_error_with_context(
                    logger,
                    f"Error in continuous loop: {e}",
                    service="air-quality-service",
                    error=str(e)
                )
                await asyncio.sleep(300)


async def create_app(service: AirQualityService):
    """Create web application"""
    app = web.Application()
    
    app.router.add_get('/health', service.health_handler.handle)
    app.router.add_get('/current-aqi', service.get_current_aqi)
    
    return app


async def main():
    """Main entry point"""
    logger.info("Starting Air Quality Service...")
    
    service = AirQualityService()
    await service.startup()
    
    app = await create_app(service)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('SERVICE_PORT', '8012'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"API endpoints available on port {port}")
    
    try:
        await service.run_continuous()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.shutdown()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

