"""
Smart Meter Service Main Entry Point
Generic smart meter integration with adapter pattern
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

logger = setup_logging("smart-meter-service")


class SmartMeterService:
    """Generic smart meter integration with adapter support"""
    
    def __init__(self):
        self.meter_type = os.getenv('METER_TYPE', 'generic')
        self.api_token = os.getenv('METER_API_TOKEN', '')
        self.device_id = os.getenv('METER_DEVICE_ID', '')
        
        # InfluxDB configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://influxdb:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'home_assistant')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'events')
        
        # Service configuration
        self.fetch_interval = 300  # 5 minutes
        
        # Cache
        self.cached_data: Optional[Dict[str, Any]] = None
        self.last_fetch_time: Optional[datetime] = None
        self.baseline_3am: Optional[float] = None
        
        # Components
        self.session: Optional[aiohttp.ClientSession] = None
        self.influxdb_client: Optional[InfluxDBClient3] = None
        self.health_handler = HealthCheckHandler()
        
        if not self.influxdb_token:
            raise ValueError("INFLUXDB_TOKEN required")
    
    async def startup(self):
        """Initialize service"""
        logger.info(f"Initializing Smart Meter Service (Type: {self.meter_type})...")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        
        self.influxdb_client = InfluxDBClient3(
            host=self.influxdb_url,
            token=self.influxdb_token,
            database=self.influxdb_bucket,
            org=self.influxdb_org
        )
        
        logger.info("Smart Meter Service initialized")
    
    async def shutdown(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        if self.influxdb_client:
            self.influxdb_client.close()
    
    async def fetch_consumption(self) -> Optional[Dict[str, Any]]:
        """Fetch power consumption (generic implementation)"""
        
        try:
            # Generic mock data for demonstration
            # In production, this would call actual meter API
            
            data = {
                'total_power_w': 2450.0,
                'daily_kwh': 18.5,
                'circuits': [
                    {'name': 'HVAC', 'power_w': 1200.0},
                    {'name': 'Kitchen', 'power_w': 450.0},
                    {'name': 'Living Room', 'power_w': 300.0},
                    {'name': 'Office', 'power_w': 250.0},
                    {'name': 'Bedrooms', 'power_w': 150.0},
                    {'name': 'Other', 'power_w': 100.0}
                ],
                'timestamp': datetime.now()
            }
            
            # Calculate percentages
            for circuit in data['circuits']:
                circuit['percentage'] = (circuit['power_w'] / data['total_power_w']) * 100 if data['total_power_w'] > 0 else 0
            
            # Detect phantom loads (high 3am baseline)
            current_hour = datetime.now().hour
            if current_hour == 3:
                self.baseline_3am = data['total_power_w']
                if self.baseline_3am > 200:
                    logger.warning(f"High phantom load detected: {self.baseline_3am:.0f}W at 3am")
            
            # Log high consumption
            if data['total_power_w'] > 10000:
                logger.warning(f"High power consumption: {data['total_power_w']:.0f}W")
            
            self.cached_data = data
            self.last_fetch_time = datetime.now()
            
            self.health_handler.last_successful_fetch = datetime.now()
            self.health_handler.total_fetches += 1
            
            logger.info(f"Power: {data['total_power_w']:.0f}W, Daily: {data['daily_kwh']:.1f}kWh")
            
            return data
            
        except Exception as e:
            log_error_with_context(
                logger,
                f"Error fetching consumption: {e}",
                service="smart-meter-service",
                error=str(e)
            )
            self.health_handler.failed_fetches += 1
            return self.cached_data
    
    async def store_in_influxdb(self, data: Dict[str, Any]):
        """Store consumption data in InfluxDB"""
        
        if not data:
            return
        
        try:
            # Store whole-home consumption
            point = Point("smart_meter") \
                .tag("meter_type", self.meter_type) \
                .field("total_power_w", float(data['total_power_w'])) \
                .field("daily_kwh", float(data['daily_kwh'])) \
                .time(data['timestamp'])
            
            self.influxdb_client.write(point)
            
            # Store circuit-level data
            for circuit in data.get('circuits', []):
                circuit_point = Point("smart_meter_circuit") \
                    .tag("circuit_name", circuit['name']) \
                    .field("power_w", float(circuit['power_w'])) \
                    .field("percentage", float(circuit['percentage'])) \
                    .time(data['timestamp'])
                
                self.influxdb_client.write(circuit_point)
            
            logger.info("Smart meter data written to InfluxDB")
            
        except Exception as e:
            log_error_with_context(
                logger,
                f"Error writing to InfluxDB: {e}",
                service="smart-meter-service",
                error=str(e)
            )
    
    async def run_continuous(self):
        """Run continuous data collection loop"""
        
        logger.info(f"Starting continuous power monitoring (every {self.fetch_interval}s)")
        
        while True:
            try:
                data = await self.fetch_consumption()
                
                if data:
                    await self.store_in_influxdb(data)
                
                await asyncio.sleep(self.fetch_interval)
                
            except Exception as e:
                log_error_with_context(
                    logger,
                    f"Error in continuous loop: {e}",
                    service="smart-meter-service",
                    error=str(e)
                )
                await asyncio.sleep(60)


async def create_app(service: SmartMeterService):
    """Create web application"""
    app = web.Application()
    app.router.add_get('/health', service.health_handler.handle)
    return app


async def main():
    """Main entry point"""
    logger.info("Starting Smart Meter Service...")
    
    service = SmartMeterService()
    await service.startup()
    
    app = await create_app(service)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('SERVICE_PORT', '8014'))
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

