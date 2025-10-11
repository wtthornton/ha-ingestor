"""
Carbon Intensity Service Main Entry Point
Fetches grid carbon intensity from WattTime API
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

# Add shared directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from shared.logging_config import (
    setup_logging, log_with_context, log_error_with_context
)

from health_check import HealthCheckHandler

# Load environment variables
load_dotenv()

# Configure logging
logger = setup_logging("carbon-intensity-service")


class CarbonIntensityService:
    """Fetch and store carbon intensity data from WattTime API"""
    
    def __init__(self):
        self.api_token = os.getenv('WATTTIME_API_TOKEN')
        self.region = os.getenv('GRID_REGION', 'CAISO_NORTH')
        self.base_url = "https://api.watttime.org/v3"
        
        # InfluxDB configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home_assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'events')
        
        # Service configuration
        self.fetch_interval = 900  # 15 minutes in seconds
        self.cache_duration = 15  # minutes
        
        # Cache
        self.cached_data: Optional[Dict[str, Any]] = None
        self.last_fetch_time: Optional[datetime] = None
        
        # HTTP session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # InfluxDB client
        self.influxdb_client: Optional[InfluxDBClient3] = None
        
        # Health check handler
        self.health_handler = HealthCheckHandler()
        
        # Validate configuration
        if not self.api_token:
            raise ValueError("WATTTIME_API_TOKEN environment variable is required")
        if not self.influxdb_token:
            raise ValueError("INFLUXDB_TOKEN environment variable is required")
    
    async def startup(self):
        """Initialize service components"""
        logger.info("Initializing Carbon Intensity Service...")
        
        # Create HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        
        # Create InfluxDB client
        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_bucket,
            org=self.influxdb_org
        )
        
        logger.info("Carbon Intensity Service initialized successfully")
    
    async def shutdown(self):
        """Cleanup service components"""
        logger.info("Shutting down Carbon Intensity Service...")
        
        if self.session:
            await self.session.close()
        
        if self.influxdb_client:
            self.influxdb_client.close()
        
        logger.info("Carbon Intensity Service shut down successfully")
    
    async def fetch_carbon_intensity(self) -> Optional[Dict[str, Any]]:
        """Fetch carbon intensity from WattTime API"""
        
        try:
            url = f"{self.base_url}/forecast"
            headers = {"Authorization": f"Bearer {self.api_token}"}
            params = {"region": self.region}
            
            log_with_context(
                logger, "INFO",
                f"Fetching carbon intensity for region {self.region}",
                service="carbon-intensity-service",
                region=self.region
            )
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    raw_data = await response.json()
                    
                    # Parse WattTime response
                    data = {
                        'carbon_intensity': raw_data.get('moer', 0),  # Marginal emissions rate
                        'renewable_percentage': raw_data.get('renewable_pct', 0),
                        'fossil_percentage': 100 - raw_data.get('renewable_pct', 0),
                        'timestamp': datetime.now()
                    }
                    
                    # Extract forecasts if available
                    forecast = raw_data.get('forecast', [])
                    if forecast:
                        data['forecast_1h'] = forecast[0].get('value', 0) if len(forecast) > 0 else 0
                        data['forecast_24h'] = forecast[23].get('value', 0) if len(forecast) > 23 else 0
                    else:
                        data['forecast_1h'] = 0
                        data['forecast_24h'] = 0
                    
                    # Update cache
                    self.cached_data = data
                    self.last_fetch_time = datetime.now()
                    
                    # Update health check
                    self.health_handler.last_successful_fetch = datetime.now()
                    self.health_handler.total_fetches += 1
                    
                    logger.info(f"Carbon intensity: {data['carbon_intensity']:.1f} gCO2/kWh, Renewable: {data['renewable_percentage']:.1f}%")
                    
                    return data
                    
                else:
                    log_error_with_context(
                        logger,
                        f"WattTime API returned status {response.status}",
                        service="carbon-intensity-service",
                        status_code=response.status
                    )
                    self.health_handler.failed_fetches += 1
                    return self.cached_data
                    
        except aiohttp.ClientError as e:
            log_error_with_context(
                logger,
                f"Error fetching carbon intensity: {e}",
                service="carbon-intensity-service",
                error=str(e)
            )
            self.health_handler.failed_fetches += 1
            
            # Return cached data if available
            if self.cached_data:
                logger.warning("Using cached carbon intensity data")
                return self.cached_data
            
            return None
        
        except Exception as e:
            log_error_with_context(
                logger,
                f"Unexpected error: {e}",
                service="carbon-intensity-service",
                error=str(e)
            )
            self.health_handler.failed_fetches += 1
            return self.cached_data
    
    async def store_in_influxdb(self, data: Dict[str, Any]):
        """Store carbon intensity data in InfluxDB"""
        
        if not data:
            logger.warning("No data to store in InfluxDB")
            return
        
        try:
            point = Point("carbon_intensity") \
                .tag("region", self.region) \
                .tag("grid_operator", self.region.split('_')[0]) \
                .field("carbon_intensity_gco2_kwh", float(data['carbon_intensity'])) \
                .field("renewable_percentage", float(data['renewable_percentage'])) \
                .field("fossil_percentage", float(data['fossil_percentage'])) \
                .field("forecast_1h", float(data['forecast_1h'])) \
                .field("forecast_24h", float(data['forecast_24h'])) \
                .time(data['timestamp'])
            
            self.influxdb_client.write(point)
            
            logger.info("Carbon intensity data written to InfluxDB")
            
        except Exception as e:
            log_error_with_context(
                logger,
                f"Error writing to InfluxDB: {e}",
                service="carbon-intensity-service",
                error=str(e)
            )
    
    async def run_continuous(self):
        """Run continuous data collection loop"""
        
        logger.info(f"Starting continuous carbon intensity monitoring (every {self.fetch_interval}s)")
        
        while True:
            try:
                # Fetch data
                data = await self.fetch_carbon_intensity()
                
                # Store in InfluxDB
                if data:
                    await self.store_in_influxdb(data)
                
                # Wait for next interval
                await asyncio.sleep(self.fetch_interval)
                
            except Exception as e:
                log_error_with_context(
                    logger,
                    f"Error in continuous loop: {e}",
                    service="carbon-intensity-service",
                    error=str(e)
                )
                # Wait before retrying
                await asyncio.sleep(60)


async def create_app(service: CarbonIntensityService):
    """Create the web application"""
    app = web.Application()
    
    # Add health check endpoint
    app.router.add_get('/health', service.health_handler.handle)
    
    return app


async def main():
    """Main entry point"""
    logger.info("Starting Carbon Intensity Service...")
    
    # Create service
    service = CarbonIntensityService()
    await service.startup()
    
    # Create web application for health check
    app = await create_app(service)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Start health check server
    port = int(os.getenv('SERVICE_PORT', '8010'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Health check endpoint available on port {port}")
    
    try:
        # Run continuous data collection
        await service.run_continuous()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    
    finally:
        await service.shutdown()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

