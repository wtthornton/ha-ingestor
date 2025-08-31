"""FastAPI-based health check server for Home Assistant Activity Ingestor."""

import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

import ha_ingestor

from ..models.api_models import (
    AggregationType,
    EventFilter,
    EventsResponse,
    ExportRequest,
    ExportResponse,
    MetricsFilter,
    MetricsResponse,
    QueryRequest,
    QueryResponse,
    TimeRange,
)
from ..utils.logging import add_log_context, get_logger, set_correlation_id
from .checks import HealthStatus, create_default_health_checker


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
        self.app: FastAPI | None = None
        self.server: uvicorn.Server | None = None
        self._start_time = time.time()

    def create_app(self) -> FastAPI:
        """Create FastAPI application with health endpoints.

        Returns:
            Configured FastAPI application
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI) -> AsyncIterator[None]:
            """Lifespan context manager for FastAPI app.

            Args:
                app: FastAPI application instance

            Yields:
                None
            """
            # Startup
            self.logger.info(
                "Health server starting up", host=self.host, port=self.port
            )
            yield
            # Shutdown
            self.logger.info("Health server shutting down")

        app = FastAPI(
            title="Home Assistant Activity Ingestor Health",
            description="Health check and monitoring endpoints",
            version=ha_ingestor.__version__,
            lifespan=lifespan,
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
        async def add_correlation_id(
            request: Request, call_next: Callable[[Request], Any]
        ) -> Any:
            """Add correlation ID to request context.

            Args:
                request: Incoming request
                call_next: Next middleware in chain

            Returns:
                Response with correlation ID header
            """
            # Generate correlation ID for each request
            correlation_id = set_correlation_id()
            add_log_context(
                endpoint=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown",
            )

            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

        # Health endpoint
        @app.get("/health")
        async def health_check() -> JSONResponse:
            """Basic health check endpoint.

            Returns:
                JSON response with health status
            """
            try:
                overall_status = self.health_checker.get_overall_status()

                response_data: dict[str, Any] = {
                    "status": overall_status.value,
                    "timestamp": time.time(),
                    "uptime_seconds": time.time() - self._start_time,
                    "service": "ha-ingestor",
                    "version": ha_ingestor.__version__,
                }

                # Add dependency health if available
                if self.health_checker.get_dependency_names():
                    response_data["dependencies"] = {
                        name: {
                            "status": check.status.value,
                            "message": check.message,
                            "last_check": check.last_check,
                            "response_time_ms": check.response_time_ms,
                        }
                        for name, check in self.health_checker._last_checks.items()
                    }

                status_code = 200 if overall_status == HealthStatus.HEALTHY else 503

                return JSONResponse(content=response_data, status_code=status_code)

            except Exception as e:
                self.logger.error("Health check failed", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Health check failed: {str(e)}"
                ) from e

        # Readiness endpoint
        @app.get("/ready")
        async def readiness_check() -> JSONResponse:
            """Readiness check endpoint.

            Returns:
                JSON response with readiness status
            """
            try:
                # Check if all critical dependencies are healthy
                dependencies = await self.health_checker.check_all_dependencies()

                ready = all(
                    dep.status == HealthStatus.HEALTHY for dep in dependencies.values()
                )

                response_data: dict[str, Any] = {
                    "ready": ready,
                    "timestamp": time.time(),
                    "dependencies": {
                        name: {
                            "status": dep.status.value,
                            "ready": dep.status == HealthStatus.HEALTHY,
                        }
                        for name, dep in dependencies.items()
                    },
                }

                status_code = 200 if ready else 503

                return JSONResponse(content=response_data, status_code=status_code)

            except Exception as e:
                self.logger.error("Readiness check failed", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Readiness check failed: {str(e)}"
                ) from e

        # Metrics endpoint
        @app.get("/metrics")
        async def metrics() -> PlainTextResponse:
            """Prometheus metrics endpoint.

            Returns:
                Plain text response with Prometheus metrics
            """
            try:
                from ..metrics import get_enhanced_metrics_collector

                metrics_collector = get_enhanced_metrics_collector()
                metrics_text = metrics_collector.export_prometheus_metrics()

                return PlainTextResponse(content=metrics_text, media_type="text/plain")

            except Exception as e:
                self.logger.error("Metrics collection failed", error=str(e))
                # Return basic metrics even if collection fails
                basic_metrics = f"""# HELP ha_ingestor_up Service is up
# TYPE ha_ingestor_up gauge
ha_ingestor_up 1
# HELP ha_ingestor_uptime_seconds Service uptime in seconds
# TYPE ha_ingestor_uptime_seconds gauge
ha_ingestor_uptime_seconds {time.time() - self._start_time}
"""
                return PlainTextResponse(content=basic_metrics, media_type="text/plain")

        # Dependency health endpoint
        @app.get("/health/dependencies")
        async def dependencies_health() -> JSONResponse:
            """Detailed dependency health information.

            Returns:
                JSON response with dependency health details
            """
            try:
                dependencies = await self.health_checker.check_all_dependencies()

                response_data: dict[str, Any] = {
                    "timestamp": time.time(),
                    "dependencies": {
                        name: {
                            "status": dep.status.value,
                            "message": dep.message,
                            "last_check": dep.last_check,
                            "response_time_ms": dep.response_time_ms,
                            "details": dep.details,
                        }
                        for name, dep in dependencies.items()
                    },
                }

                return JSONResponse(content=response_data)

            except Exception as e:
                self.logger.error("Dependencies health check failed", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Dependencies health failed: {str(e)}"
                ) from e

        # Individual dependency health endpoint
        @app.get("/health/dependencies/{dependency_name}")
        async def dependency_health(dependency_name: str) -> JSONResponse:
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
                    "timestamp": time.time(),
                }

                status_code = 200 if health.status == HealthStatus.HEALTHY else 503

                return JSONResponse(content=response_data, status_code=status_code)

            except Exception as e:
                self.logger.error(
                    "Dependency health check failed",
                    dependency=dependency_name,
                    error=str(e),
                )
                raise HTTPException(
                    status_code=500, detail=f"Health check failed: {str(e)}"
                ) from e

        # API Data Access Endpoints

        @app.get("/api/events", response_model=EventsResponse)
        async def get_events(
            time_range: TimeRange = TimeRange.ONE_DAY,
            domain: str | None = None,
            entity_id: str | None = None,
            event_type: str | None = None,
            limit: int = 100,
            offset: int = 0,
            sort_by: str = "_time",
            sort_order: str = "desc",
        ):
            """Get filtered Home Assistant events from InfluxDB."""
            try:
                from ..api.data_access import get_data_access

                filter_params = EventFilter(
                    time_range=time_range,
                    domain=domain,
                    entity_id=entity_id,
                    event_type=event_type,
                    limit=limit,
                    offset=offset,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )

                data_access = get_data_access()
                events, total_count = await data_access.get_events(filter_params)

                # Calculate pagination info
                page = (offset // limit) + 1
                has_next = total_count > (offset + limit)
                has_prev = offset > 0

                return EventsResponse(
                    data=events,
                    total_count=total_count,
                    page=page,
                    per_page=limit,
                    has_next=has_next,
                    has_prev=has_prev,
                    time_range=time_range,
                    filters_applied=filter_params.dict(),
                )

            except Exception as e:
                self.logger.error("Failed to get events", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Failed to get events: {str(e)}"
                )

        @app.get("/api/metrics", response_model=MetricsResponse)
        async def get_metrics(
            metric_type: str,
            time_range: TimeRange = TimeRange.ONE_DAY,
            aggregation: AggregationType = AggregationType.NONE,
            domain: str | None = None,
            entity_id: str | None = None,
        ):
            """Get aggregated metrics from InfluxDB."""
            try:
                from ..api.data_access import get_data_access

                filter_params = MetricsFilter(
                    metric_type=metric_type,
                    time_range=time_range,
                    aggregation=aggregation,
                    domain=domain,
                    entity_id=entity_id,
                )

                data_access = get_data_access()
                metrics_response = await data_access.get_metrics(filter_params)

                return metrics_response

            except Exception as e:
                self.logger.error("Failed to get metrics", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Failed to get metrics: {str(e)}"
                )

        @app.post("/api/export", response_model=ExportResponse)
        async def export_data(export_request: ExportRequest):
            """Export data in various formats."""
            try:
                from ..api.data_access import get_data_access

                data_access = get_data_access()
                export_response = await data_access.export_data(export_request)

                return export_response

            except Exception as e:
                self.logger.error("Failed to export data", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Failed to export data: {str(e)}"
                )

        @app.post("/api/query", response_model=QueryResponse)
        async def execute_custom_query(query_request: QueryRequest):
            """Execute a custom Flux query (read-only, sanitized)."""
            try:
                from ..api.data_access import get_data_access

                data_access = get_data_access()
                query_response = await data_access.execute_custom_query(query_request)

                return query_response

            except Exception as e:
                self.logger.error("Failed to execute custom query", error=str(e))
                raise HTTPException(
                    status_code=500, detail=f"Failed to execute custom query: {str(e)}"
                )

        # Root endpoint
        @app.get("/")
        async def root() -> dict[str, Any]:
            """Root endpoint with service information.

            Returns:
                Dictionary with service information
            """
            return {
                "service": "Home Assistant Activity Ingestor",
                "version": ha_ingestor.__version__,
                "status": "running",
                "endpoints": {
                    "health": "/health",
                    "ready": "/ready",
                    "metrics": "/metrics",
                    "dependencies": "/health/dependencies",
                    "api": {
                        "events": "/api/events",
                        "metrics": "/api/metrics",
                        "export": "/api/export",
                        "query": "/api/query",
                    },
                },
                "timestamp": time.time(),
            }

        self.app = app
        return app

    async def start(self) -> None:
        """Start the health server."""
        if not self.app:
            self.create_app()

        if self.app is None:
            raise RuntimeError("Failed to create FastAPI application")

        config = uvicorn.Config(
            app=self.app, host=self.host, port=self.port, log_level="info"
        )

        self.server = uvicorn.Server(config)
        self.logger.info("Starting health server", host=self.host, port=self.port)

        # Start server in background
        if self.server:
            await self.server.serve()

    def start_sync(self) -> None:
        """Start the health server synchronously."""
        if not self.app:
            self.create_app()

        if self.app is None:
            raise RuntimeError("Failed to create FastAPI application")

        uvicorn.run(app=self.app, host=self.host, port=self.port, log_level="info")

    def stop_sync(self) -> None:
        """Stop the health server synchronously."""
        # For uvicorn.run, we can't easily stop it from another thread
        # This is a limitation of the current implementation
        # The server will stop when the main process exits
        self.logger.info("Health server stop requested (will stop with main process)")

    async def stop(self) -> None:
        """Stop the health server."""
        if self.server:
            self.server.should_exit = True
            self.logger.info("Health server stopped")

    def add_dependency_check(self, name: str, check_func: Callable[..., Any]) -> None:
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
