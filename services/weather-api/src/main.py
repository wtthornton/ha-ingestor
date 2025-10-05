"""
Weather API Service Main Entry Point
"""

import asyncio
import logging
import os
import sys
from aiohttp import web
from dotenv import load_dotenv

# Add shared directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))

from shared.logging_config import (
    setup_logging, get_logger, log_with_context, log_performance, 
    log_error_with_context, performance_monitor, generate_correlation_id,
    set_correlation_id, get_correlation_id
)
from shared.correlation_middleware import create_correlation_middleware

from .health_check import HealthCheckHandler

# Load environment variables
load_dotenv()

# Configure enhanced logging
logger = setup_logging("weather-api")


async def create_app():
    """Create the web application"""
    # Create web application with proper middleware factory
    correlation_middleware = create_correlation_middleware()
    app = web.Application(middlewares=[correlation_middleware])
    
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
