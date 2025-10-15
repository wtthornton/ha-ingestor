"""Health check endpoint"""

from fastapi import APIRouter
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint for service monitoring.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "ai-automation-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Automation Service",
        "version": "1.0.0",
        "description": "AI-powered Home Assistant automation suggestion system",
        "docs": "/docs"
    }

