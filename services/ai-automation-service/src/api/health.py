"""Health check endpoint"""

from fastapi import APIRouter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

# Reference to global capability_listener (set in main.py)
_capability_listener = None

def set_capability_listener(listener):
    """Set capability listener reference for health checks"""
    global _capability_listener
    _capability_listener = listener


@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    
    Epic AI-1: Service health
    Epic AI-2: Device Intelligence stats (Story AI2.1)
    
    Returns:
        Service health status with Device Intelligence metrics
    """
    health = {
        "status": "healthy",
        "service": "ai-automation-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Add Device Intelligence stats (Epic AI-2 - Story AI2.1)
    if _capability_listener and _capability_listener.is_started():
        health["device_intelligence"] = _capability_listener.get_stats()
    
    return health


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Automation Service",
        "version": "1.0.0",
        "description": "AI-powered Home Assistant automation suggestion system",
        "docs": "/docs"
    }

