"""
Weather API Service Main Entry Point
"""

import asyncio
import logging
import os
from aiohttp import web
from dotenv import load_dotenv

from .health_check import HealthCheckHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_app():
    """Create the web application"""
    app = web.Application()
    
    # Add health check endpoint
    health_handler = HealthCheckHandler()
    app.router.add_get('/health', health_handler.handle)
    
    return app


async def main():
    """Main entry point"""
    logger.info("Starting Weather API Service...")
    
    # Create web application
    app = await create_app()
    
    # Start web server
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv('WEATHER_API_PORT', '8001'))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Weather API Service started on port {port}")
    
    # Keep the service running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down Weather API Service...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
