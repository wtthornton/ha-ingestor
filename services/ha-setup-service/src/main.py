"""
HA Setup Service - Main FastAPI Application

Context7 Best Practices Applied:
- Lifespan context manager for initialization/cleanup
- Async dependency injection
- Response model validation
- Proper exception handling
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Dict

from .config import get_settings
from .database import get_db, init_db
from .health_service import HealthMonitoringService
from .integration_checker import IntegrationHealthChecker
from .monitoring_service import ContinuousHealthMonitor
from .setup_wizard import Zigbee2MQTTSetupWizard, MQTTSetupWizard
from .optimization_engine import PerformanceAnalysisEngine, RecommendationEngine
from .schemas import (
    EnvironmentHealthResponse,
    HealthCheckResponse,
    IntegrationHealthResponse,
    PerformanceMetricResponse,
    IntegrationStatus
)

settings = get_settings()

# Global service instances (initialized in lifespan)
health_services: Dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for service initialization and cleanup
    
    Context7 Pattern: Modern FastAPI lifespan management
    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown")
    """
    # Startup: Initialize services
    print("=" * 80)
    print("🚀 HA Setup Service Starting")
    print("=" * 80)
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize health monitoring service
    health_services["monitor"] = HealthMonitoringService()
    print("✅ Health monitoring service initialized")
    
    # Initialize integration health checker
    health_services["integration_checker"] = IntegrationHealthChecker()
    print("✅ Integration health checker initialized")
    
    # Initialize continuous monitoring
    continuous_monitor = ContinuousHealthMonitor(
        health_services["monitor"],
        health_services["integration_checker"]
    )
    health_services["continuous_monitor"] = continuous_monitor
    
    # Start background monitoring
    await continuous_monitor.start()
    print("✅ Continuous health monitoring started")
    
    # Initialize setup wizards
    health_services["zigbee2mqtt_wizard"] = Zigbee2MQTTSetupWizard()
    health_services["mqtt_wizard"] = MQTTSetupWizard()
    print("✅ Setup wizards initialized")
    
    # Initialize optimization engine
    health_services["performance_analyzer"] = PerformanceAnalysisEngine()
    health_services["recommendation_engine"] = RecommendationEngine()
    print("✅ Optimization engine initialized")
    
    print("=" * 80)
    print("✨ HA Setup Service Ready")
    print(f"📍 Listening on port {settings.service_port}")
    print("📊 Services: Health Monitoring, Integration Checking, Setup Wizards, Optimization")
    print("=" * 80)
    
    yield  # Application runs here
    
    # Shutdown: Stop monitoring before cleanup
    print("🛑 Stopping continuous monitoring...")
    await continuous_monitor.stop()
    
    # Shutdown: Clean up resources
    print("=" * 80)
    print("👋 HA Setup Service Shutting Down")
    print("=" * 80)
    
    # Clear service instances
    health_services.clear()
    print("✅ Services cleaned up")


# Create FastAPI app with lifespan
app = FastAPI(
    title="HA Setup & Recommendation Service",
    description="Automated setup, health monitoring, and optimization for Home Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health Check Endpoints

@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Simple health check"
)
async def health_check():
    """Simple health check endpoint for container orchestration"""
    return HealthCheckResponse(
        status="healthy",
        service=settings.service_name,
        timestamp=datetime.now(),
        version="1.0.0"
    )


@app.get(
    "/api/health/environment",
    response_model=EnvironmentHealthResponse,
    tags=["health"],
    summary="Get comprehensive environment health status"
)
async def get_environment_health(
    db: AsyncSession = Depends(get_db)
) -> EnvironmentHealthResponse:
    """
    Get comprehensive environment health status
    
    Returns:
        Complete health status including:
        - Overall health score (0-100)
        - Home Assistant core status
        - Integration statuses
        - Performance metrics
        - Detected issues
    """
    try:
        health_service = health_services.get("monitor")
        if not health_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Health monitoring service not initialized"
            )
        
        return await health_service.check_environment_health(db)
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking environment health: {str(e)}"
        )


@app.get(
    "/api/health/trends",
    tags=["health"],
    summary="Get health trends over time"
)
async def get_health_trends(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """
    Get health trends over specified time period
    
    Args:
        hours: Number of hours to analyze (default: 24)
        
    Returns:
        Trend analysis including average score, min/max, and trend direction
    """
    try:
        continuous_monitor = health_services.get("continuous_monitor")
        if not continuous_monitor:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Continuous monitoring not initialized"
            )
        
        trends = await continuous_monitor.get_health_trends(db, hours)
        return trends
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting health trends: {str(e)}"
        )


@app.get(
    "/api/health/integrations",
    tags=["health"],
    summary="Get detailed integration health status"
)
async def get_integrations_health(
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed health status for all integrations
    
    Checks:
    - Home Assistant authentication
    - MQTT broker connectivity
    - Zigbee2MQTT status
    - Device discovery
    - HA Ingestor services (Data API, Admin API)
    
    Returns:
        List of integration health results with detailed diagnostics
    """
    try:
        integration_checker = health_services.get("integration_checker")
        if not integration_checker:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Integration health checker not initialized"
            )
        
        # Run all integration checks
        check_results = await integration_checker.check_all_integrations()
        
        # Store results in database
        await _store_integration_health_results(db, check_results)
        
        # Return results
        return {
            "timestamp": datetime.now(),
            "total_integrations": len(check_results),
            "healthy_count": sum(1 for r in check_results if r.status == IntegrationStatus.HEALTHY),
            "warning_count": sum(1 for r in check_results if r.status == IntegrationStatus.WARNING),
            "error_count": sum(1 for r in check_results if r.status == IntegrationStatus.ERROR),
            "not_configured_count": sum(1 for r in check_results if r.status == IntegrationStatus.NOT_CONFIGURED),
            "integrations": [r.dict() for r in check_results]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking integrations: {str(e)}"
        )


async def _store_integration_health_results(
    db: AsyncSession,
    check_results: list
):
    """Store integration health check results in database"""
    try:
        from .models import IntegrationHealth
        
        for result in check_results:
            integration_health = IntegrationHealth(
                integration_name=result.integration_name,
                integration_type=result.integration_type,
                status=result.status.value,
                is_configured=result.is_configured,
                is_connected=result.is_connected,
                error_message=result.error_message,
                last_check=result.last_check,
                check_details=result.check_details
            )
            
            db.add(integration_health)
        
        await db.commit()
        
    except Exception as e:
        await db.rollback()
        # Log error but don't fail the health check
        print(f"Error storing integration health results: {e}")


# Root endpoint

# Setup Wizard Endpoints

@app.post(
    "/api/setup/wizard/{integration_type}/start",
    tags=["setup"],
    summary="Start setup wizard for integration"
)
async def start_setup_wizard(integration_type: str):
    """
    Start a setup wizard for specified integration type
    
    Supported types:
    - zigbee2mqtt
    - mqtt
    """
    try:
        if integration_type == "zigbee2mqtt":
            wizard = health_services.get("zigbee2mqtt_wizard")
            session_id = await wizard.start_zigbee2mqtt_setup()
        elif integration_type == "mqtt":
            wizard = health_services.get("mqtt_wizard")
            session_id = await wizard.start_mqtt_setup()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported integration type: {integration_type}"
            )
        
        return {
            "session_id": session_id,
            "integration_type": integration_type,
            "status": "started",
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting setup wizard: {str(e)}"
        )


@app.post(
    "/api/setup/wizard/{session_id}/step/{step_number}",
    tags=["setup"],
    summary="Execute setup wizard step"
)
async def execute_wizard_step(
    session_id: str,
    step_number: int,
    step_data: Dict = None
):
    """Execute a specific step in the setup wizard"""
    try:
        # Get wizard from session
        zigbee_wizard = health_services.get("zigbee2mqtt_wizard")
        mqtt_wizard = health_services.get("mqtt_wizard")
        
        # Check which wizard owns this session
        session = zigbee_wizard.get_session_status(session_id) or mqtt_wizard.get_session_status(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        
        # Get appropriate wizard
        wizard = zigbee_wizard if session["integration_type"] == "zigbee2mqtt" else mqtt_wizard
        
        result = await wizard.execute_step(session_id, step_number, step_data)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing wizard step: {str(e)}"
        )


# Performance Optimization Endpoints

@app.get(
    "/api/optimization/analyze",
    tags=["optimization"],
    summary="Analyze system performance"
)
async def analyze_performance():
    """
    Run comprehensive performance analysis
    
    Returns:
        Performance analysis with bottlenecks identified
    """
    try:
        analyzer = health_services.get("performance_analyzer")
        if not analyzer:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Performance analyzer not initialized"
            )
        
        analysis = await analyzer.analyze_performance()
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing performance: {str(e)}"
        )


@app.get(
    "/api/optimization/recommendations",
    tags=["optimization"],
    summary="Get optimization recommendations"
)
async def get_optimization_recommendations():
    """
    Generate optimization recommendations based on performance analysis
    
    Returns:
        Prioritized list of optimization recommendations
    """
    try:
        analyzer = health_services.get("performance_analyzer")
        rec_engine = health_services.get("recommendation_engine")
        
        if not analyzer or not rec_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Optimization engine not initialized"
            )
        
        # Run performance analysis
        analysis = await analyzer.analyze_performance()
        
        # Generate recommendations
        recommendations = await rec_engine.generate_recommendations(analysis)
        
        return {
            "timestamp": datetime.now(),
            "total_recommendations": len(recommendations),
            "recommendations": [r.dict() for r in recommendations]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


# Root endpoint

@app.get("/", tags=["info"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "HA Setup & Recommendation Service",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "health_monitoring": "Real-time environment health monitoring",
            "integration_checking": "Comprehensive integration health validation",
            "setup_wizards": "Guided setup for MQTT and Zigbee2MQTT",
            "performance_optimization": "Automated performance analysis and recommendations",
            "continuous_monitoring": "Background health monitoring with alerting"
        },
        "endpoints": {
            "health": "/health",
            "environment_health": "/api/health/environment",
            "health_trends": "/api/health/trends?hours=24",
            "integrations_health": "/api/health/integrations",
            "performance_analysis": "/api/optimization/analyze",
            "recommendations": "/api/optimization/recommendations",
            "start_wizard": "/api/setup/wizard/{integration_type}/start",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True
    )

