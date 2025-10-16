"""
Suggestion Generation Router

Endpoints for generating automation suggestions from detected patterns using LLM.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any, List
import logging
import time

from ..llm.openai_client import OpenAIClient
from ..database import get_db, get_patterns, store_suggestion, get_suggestions
from ..config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/suggestions", tags=["Suggestions"])

# Initialize OpenAI client
openai_client = OpenAIClient(api_key=settings.openai_api_key, model="gpt-4o-mini")


@router.post("/generate")
async def generate_suggestions(
    pattern_type: Optional[str] = Query(default=None, description="Generate suggestions for specific pattern type"),
    min_confidence: float = Query(default=0.7, ge=0.0, le=1.0, description="Minimum pattern confidence"),
    max_suggestions: int = Query(default=10, ge=1, le=50, description="Maximum suggestions to generate"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate automation suggestions from detected patterns using OpenAI.
    
    This endpoint:
    1. Retrieves patterns from database (filtered by type and confidence)
    2. For each pattern, calls OpenAI to generate automation suggestion
    3. Stores suggestions in database
    4. Returns summary with token usage and costs
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting suggestion generation: pattern_type={pattern_type}, min_confidence={min_confidence}")
        
        # Step 1: Retrieve patterns from database
        patterns = await get_patterns(
            db,
            pattern_type=pattern_type,
            min_confidence=min_confidence,
            limit=max_suggestions
        )
        
        if not patterns:
            return {
                "success": False,
                "message": f"No patterns found with confidence >= {min_confidence}",
                "data": {
                    "suggestions_generated": 0,
                    "patterns_processed": 0
                }
            }
        
        logger.info(f"✅ Retrieved {len(patterns)} patterns from database")
        
        # Step 2: Generate suggestions using OpenAI
        suggestions_generated = 0
        suggestions_stored = []
        errors = []
        
        for pattern in patterns:
            try:
                # Convert SQLAlchemy model to dict
                pattern_dict = {
                    'device_id': pattern.device_id,
                    'pattern_type': pattern.pattern_type,
                    'confidence': pattern.confidence,
                    'occurrences': pattern.occurrences,
                    'metadata': pattern.pattern_metadata or {}
                }
                
                # Extract hour/minute for time_of_day patterns
                if pattern.pattern_type == 'time_of_day' and pattern.pattern_metadata:
                    pattern_dict['hour'] = int(pattern.pattern_metadata.get('avg_time_decimal', 0))
                    pattern_dict['minute'] = int((pattern.pattern_metadata.get('avg_time_decimal', 0) % 1) * 60)
                
                # Extract device1/device2 for co_occurrence patterns
                if pattern.pattern_type == 'co_occurrence' and pattern.pattern_metadata:
                    # Device ID is stored as "device1+device2"
                    if '+' in pattern.device_id:
                        device1, device2 = pattern.device_id.split('+', 1)
                        pattern_dict['device1'] = device1
                        pattern_dict['device2'] = device2
                
                logger.info(f"Generating suggestion for pattern #{pattern.id}: {pattern.device_id}")
                
                # Call OpenAI to generate suggestion
                ai_suggestion = await openai_client.generate_automation_suggestion(pattern_dict)
                
                # Store in database
                suggestion_data = {
                    'pattern_id': pattern.id,
                    'title': ai_suggestion.alias,
                    'description': ai_suggestion.description,
                    'automation_yaml': ai_suggestion.automation_yaml,
                    'confidence': pattern.confidence,
                    'category': ai_suggestion.category,
                    'priority': ai_suggestion.priority
                }
                
                stored_suggestion = await store_suggestion(db, suggestion_data)
                suggestions_stored.append(stored_suggestion)
                suggestions_generated += 1
                
                logger.info(f"✅ Generated and stored suggestion: {ai_suggestion.alias}")
                
            except Exception as e:
                error_msg = f"Failed to generate suggestion for pattern #{pattern.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                # Continue with next pattern
        
        # Step 3: Get usage stats
        usage_stats = openai_client.get_usage_stats()
        
        # Calculate performance
        duration = time.time() - start_time
        
        logger.info(f"✅ Suggestion generation completed in {duration:.2f}s")
        logger.info(f"   Tokens used: {usage_stats['total_tokens']}, Cost: ${usage_stats['estimated_cost_usd']:.4f}")
        
        return {
            "success": True,
            "message": f"Generated {suggestions_generated} automation suggestions",
            "data": {
                "suggestions_generated": suggestions_generated,
                "suggestions_stored": len(suggestions_stored),
                "patterns_processed": len(patterns),
                "errors": errors,
                "openai_usage": usage_stats,
                "performance": {
                    "duration_seconds": round(duration, 2),
                    "avg_time_per_suggestion": round(duration / suggestions_generated, 2) if suggestions_generated > 0 else 0
                },
                "suggestions": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "category": s.category,
                        "priority": s.priority,
                        "confidence": s.confidence
                    }
                    for s in suggestions_stored[:5]  # Preview first 5
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Suggestion generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Suggestion generation failed: {str(e)}"
        )


@router.get("/list")
async def list_suggestions(
    status_filter: Optional[str] = Query(default=None, description="Filter by status (pending, approved, deployed, rejected)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum suggestions to return"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    List automation suggestions with optional filters.
    """
    try:
        suggestions = await get_suggestions(db, status=status_filter, limit=limit)
        
        # Convert to dictionaries
        suggestions_list = [
            {
                "id": s.id,
                "pattern_id": s.pattern_id,
                "title": s.title,
                "description": s.description,
                "automation_yaml": s.automation_yaml,
                "status": s.status,
                "confidence": s.confidence,
                "category": s.category,
                "priority": s.priority,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "deployed_at": s.deployed_at.isoformat() if s.deployed_at else None
            }
            for s in suggestions
        ]
        
        return {
            "success": True,
            "data": {
                "suggestions": suggestions_list,
                "count": len(suggestions_list)
            },
            "message": f"Retrieved {len(suggestions_list)} suggestions"
        }
        
    except Exception as e:
        logger.error(f"Failed to list suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list suggestions: {str(e)}"
        )


@router.get("/usage-stats")
async def get_usage_stats() -> Dict[str, Any]:
    """
    Get OpenAI API usage statistics and cost estimates.
    """
    try:
        stats = openai_client.get_usage_stats()
        
        # Add budget alert
        from ..llm.cost_tracker import CostTracker
        budget_alert = CostTracker.check_budget_alert(
            total_cost=stats['estimated_cost_usd'],
            budget=10.0  # $10/month default budget
        )
        
        return {
            "success": True,
            "data": {
                **stats,
                "budget_alert": budget_alert
            },
            "message": "Usage statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}"
        )


@router.post("/usage-stats/reset")
async def reset_usage_stats() -> Dict[str, Any]:
    """
    Reset OpenAI API usage statistics (for monthly reset).
    """
    try:
        openai_client.reset_usage_stats()
        
        return {
            "success": True,
            "message": "Usage statistics reset successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset usage stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset usage stats: {str(e)}"
        )

