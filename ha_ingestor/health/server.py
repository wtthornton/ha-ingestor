"""FastAPI-based health check server for Home Assistant Activity Ingestor."""

import asyncio
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..utils.logging import get_logger, set_correlation_id, add_log_context
from .checks import HealthChecker, HealthStatus, create_default_health_checker
from ..metrics import get_metrics_collector


class HealthServer:
    """Health check server for the service."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """Initialize health server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.logger = get_logger(__name__)
        self.health_checker = create_default_health_checker()
        self.app = None
        self.server = None
        self._start_time = time.time()
        
    def create_app(self) -> FastAPI:
        """Create FastAPI application with health endpoints.
        
        Returns:
            Configured FastAPI application
        """
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            self.logger.info("Health server starting up", host=self.host, port=self.port)
            yield
            # Shutdown
            self.logger.info("Health server shutting down")
        
        app = FastAPI(
            title="Home Assistant Activity Ingestor Health",
            description="Health check and monitoring endpoints",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add request correlation middleware
        @app.middleware("http")
        async def add_correlation_id(request: Request, call_next):
            # Generate correlation ID for each request
            correlation_id = set_correlation_id()
            add_log_context(
                endpoint=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown"
            )
            
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        
        # Health endpoint
        @app.get("/health")
        async def health_check():
            """Basic health check endpoint."""
            try:
                overall_status = self.health_checker.get_overall_status()
                
                response_data = {
                    "status": overall_status.value,
                    "timestamp": time.time(),
                    "uptime_seconds": time.time() - self._start_time,
                    "service": "ha-ingestor",
                    "version": "1.0.0"
                }
                
                # Add dependency health if available
                if self.health_checker.get_dependency_names():
                    response_data["dependencies"] = {
                        name: {
                            "status": check.status.value,
                            "message": check.message,
                            "last_check": check.last_check,
                            "response_time_ms": check.response_time_ms
                        }
                        for name, check in self.health_checker._last_checks.items()
                    }
                
                status_code = 200 if overall_status == HealthStatus.HEALTHY else 503
                
                return JSONResponse(
                    content=response_data,
                    status_code=status_code
                )
                
            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
        
        # Readiness endpoint
        @app.get("/ready")
        async def readiness_check():
            """Readiness check endpoint."""
            try:
                # Check if all critical dependencies are healthy
                dependencies = await self.health_checker.check_all_dependencies()
                
                ready = all(
                    dep.status == HealthStatus.HEALTHY 
                    for dep in dependencies.values()
                )
                
                response_data = {
                    "ready": ready,
                    "timestamp": time.time(),
                    "dependencies": {
                        name: {
                            "status": dep.status.value,
                            "ready": dep.status == HealthStatus.HEALTHY
                        }
                        for name, dep in dependencies.items()
                    }
                }
                
                status_code = 200 if ready else 503
                
                return JSONResponse(
                    content=response_data,
                    status_code=status_code
                )
                
            except Exception as e:
                self.logger.error("Readiness check failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Readiness check failed: {str(e)}")
        
        # Metrics endpoint for Prometheus metrics
        @app.get("/metrics")
        async def metrics():
            """Metrics endpoint for Prometheus."""
            try:
                # Get metrics from the global collector
                metrics_collector = get_metrics_collector()
                prometheus_metrics = metrics_collector.export_prometheus()
                
                return PlainTextResponse(
                    content=prometheus_metrics,
                    media_type="text/plain"
                )
                
            except Exception as e:
                self.logger.error("Metrics endpoint failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")
        
        # Dependency health endpoint
        @app.get("/health/dependencies")
        async def dependencies_health():
            """Detailed dependency health information."""
            try:
                dependencies = await self.health_checker.check_all_dependencies()
                
                response_data = {
                    "timestamp": time.time(),
                    "dependencies": {
                        name: {
                            "status": dep.status.value,
                            "message": dep.message,
                            "last_check": dep.last_check,
                            "response_time_ms": dep.response_time_ms,
                            "details": dep.details
                        }
                        for name, dep in dependencies.items()
                    }
                }
                
                return JSONResponse(content=response_data)
                
            except Exception as e:
                self.logger.error("Dependencies health check failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"Dependencies health failed: {str(e)}")
        
        # Individual dependency health endpoint
        @app.get("/health/dependencies/{dependency_name}")
        async def dependency_health(dependency_name: str):
            """Health check for a specific dependency."""
            try:
                health = await self.health_checker.check_dependency(dependency_name)
                
                response_data = {
                    "name": health.name,
                    "status": health.status.value,
                    "message": health.message,
                    "last_check": health.last_check,
                    "response_time_ms": health.response_time_ms,
                    "details": health.details,
                    "timestamp": time.time()
                }
                
                status_code = 200 if health.status == HealthStatus.HEALTHY else 503
                
                return JSONResponse(
                    content=response_data,
                    status_code=status_code
                )
                
            except Exception as e:
                self.logger.error("Dependency health check failed", 
                                dependency=dependency_name, error=str(e))
                raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
        
        # Root endpoint
        @app.get("/")
        async def root():
            """Root endpoint with service information."""
            return {
                "service": "Home Assistant Activity Ingestor",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "health": "/health",
                    "ready": "/ready",
                    "metrics": "/metrics",
                    "dependencies": "/health/dependencies"
                },
                "timestamp": time.time()
            }
        
        self.app = app
        return app
    
    async def start(self) -> None:
        """Start the health server."""
        if not self.app:
            self.create_app()
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        
        self.server = uvicorn.Server(config)
        self.logger.info("Starting health server", host=self.host, port=self.port)
        
        # Start server in background
        await self.server.serve()
    
    def start_sync(self) -> None:
        """Start the health server synchronously."""
        if not self.app:
            self.create_app()
        
        uvicorn.run(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
    
    async def stop(self) -> None:
        """Stop the health server."""
        if self.server:
            self.server.should_exit = True
            self.logger.info("Health server stopped")
    
    def add_dependency_check(self, name: str, check_func: callable) -> None:
        """Add a custom dependency health check.
        
        Args:
            name: Dependency name
            check_func: Health check function
        """
        self.health_checker.add_dependency(name, check_func)
        self.logger.info("Added custom dependency health check", dependency=name)


def create_health_app(host: str = "0.0.0.0", port: int = 8000) -> FastAPI:
    """Create a health check FastAPI application.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        
    Returns:
        Configured FastAPI application
    """
    server = HealthServer(host=host, port=port)
    return server.create_app()


# Convenience function for quick health server creation
def run_health_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run a health server with default configuration.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    server = HealthServer(host=host, port=port)
    server.start_sync()


if __name__ == "__main__":
    # Run health server when script is executed directly
    run_health_server()
