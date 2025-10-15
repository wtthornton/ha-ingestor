"""
CRUD operations for AI Automation Service database
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
import logging

from .models import Pattern, Suggestion, UserFeedback

logger = logging.getLogger(__name__)


# ============================================================================
# Pattern CRUD Operations
# ============================================================================

async def store_patterns(db: AsyncSession, patterns: List[Dict]) -> int:
    """
    Store detected patterns in database.
    
    Args:
        db: Database session
        patterns: List of pattern dictionaries from detector
    
    Returns:
        Number of patterns stored
    """
    if not patterns:
        logger.warning("No patterns to store")
        return 0
    
    try:
        stored_count = 0
        
        for pattern_data in patterns:
            pattern = Pattern(
                pattern_type=pattern_data['pattern_type'],
                device_id=pattern_data['device_id'],
                pattern_metadata=pattern_data.get('metadata', {}),
                confidence=pattern_data['confidence'],
                occurrences=pattern_data['occurrences'],
                created_at=datetime.now(timezone.utc)
            )
            db.add(pattern)
            stored_count += 1
        
        await db.commit()
        logger.info(f"✅ Stored {stored_count} patterns in database")
        return stored_count
        
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Failed to store patterns: {e}", exc_info=True)
        raise


async def get_patterns(
    db: AsyncSession,
    pattern_type: Optional[str] = None,
    device_id: Optional[str] = None,
    min_confidence: Optional[float] = None,
    limit: int = 100
) -> List[Pattern]:
    """
    Retrieve patterns from database with optional filters.
    
    Args:
        db: Database session
        pattern_type: Filter by pattern type (time_of_day, co_occurrence, anomaly)
        device_id: Filter by device ID
        min_confidence: Minimum confidence threshold
        limit: Maximum number of patterns to return
    
    Returns:
        List of Pattern objects
    """
    try:
        query = select(Pattern)
        
        if pattern_type:
            query = query.where(Pattern.pattern_type == pattern_type)
        
        if device_id:
            query = query.where(Pattern.device_id == device_id)
        
        if min_confidence is not None:
            query = query.where(Pattern.confidence >= min_confidence)
        
        query = query.order_by(Pattern.confidence.desc()).limit(limit)
        
        result = await db.execute(query)
        patterns = result.scalars().all()
        
        logger.info(f"Retrieved {len(patterns)} patterns from database")
        return list(patterns)
        
    except Exception as e:
        logger.error(f"Failed to retrieve patterns: {e}", exc_info=True)
        raise


async def delete_old_patterns(db: AsyncSession, days_old: int = 30) -> int:
    """
    Delete patterns older than specified days.
    
    Args:
        db: Database session
        days_old: Delete patterns older than this many days
    
    Returns:
        Number of patterns deleted
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        stmt = delete(Pattern).where(Pattern.created_at < cutoff_date)
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} patterns older than {days_old} days")
        return deleted_count
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete old patterns: {e}", exc_info=True)
        raise


async def get_pattern_stats(db: AsyncSession) -> Dict:
    """
    Get pattern statistics from database.
    
    Returns:
        Dictionary with pattern counts and statistics
    """
    try:
        # Total patterns
        total_result = await db.execute(select(func.count()).select_from(Pattern))
        total_patterns = total_result.scalar() or 0
        
        # Patterns by type
        type_result = await db.execute(
            select(Pattern.pattern_type, func.count())
            .group_by(Pattern.pattern_type)
        )
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        # Unique devices
        devices_result = await db.execute(
            select(func.count(func.distinct(Pattern.device_id))).select_from(Pattern)
        )
        unique_devices = devices_result.scalar() or 0
        
        # Average confidence
        avg_conf_result = await db.execute(
            select(func.avg(Pattern.confidence)).select_from(Pattern)
        )
        avg_confidence = avg_conf_result.scalar() or 0.0
        
        return {
            'total_patterns': total_patterns,
            'by_type': by_type,
            'unique_devices': unique_devices,
            'avg_confidence': float(avg_confidence)
        }
        
    except Exception as e:
        logger.error(f"Failed to get pattern stats: {e}", exc_info=True)
        raise


# ============================================================================
# Suggestion CRUD Operations
# ============================================================================

async def store_suggestion(db: AsyncSession, suggestion_data: Dict) -> Suggestion:
    """
    Store automation suggestion in database.
    
    Args:
        db: Database session
        suggestion_data: Suggestion dictionary
    
    Returns:
        Stored Suggestion object
    """
    try:
        suggestion = Suggestion(
            pattern_id=suggestion_data.get('pattern_id'),
            title=suggestion_data['title'],
            description=suggestion_data.get('description'),
            automation_yaml=suggestion_data['automation_yaml'],
            status='pending',
            confidence=suggestion_data['confidence'],
            category=suggestion_data.get('category'),
            priority=suggestion_data.get('priority'),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(suggestion)
        await db.commit()
        await db.refresh(suggestion)
        
        logger.info(f"✅ Stored suggestion: {suggestion.title}")
        return suggestion
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to store suggestion: {e}", exc_info=True)
        raise


async def get_suggestions(
    db: AsyncSession,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Suggestion]:
    """
    Retrieve automation suggestions from database.
    
    Args:
        db: Database session
        status: Filter by status (pending, approved, deployed, rejected)
        limit: Maximum number of suggestions to return
    
    Returns:
        List of Suggestion objects
    """
    try:
        query = select(Suggestion)
        
        if status:
            query = query.where(Suggestion.status == status)
        
        query = query.order_by(Suggestion.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        suggestions = result.scalars().all()
        
        logger.info(f"Retrieved {len(suggestions)} suggestions from database")
        return list(suggestions)
        
    except Exception as e:
        logger.error(f"Failed to retrieve suggestions: {e}", exc_info=True)
        raise


# ============================================================================
# User Feedback CRUD Operations
# ============================================================================

async def store_feedback(db: AsyncSession, feedback_data: Dict) -> UserFeedback:
    """
    Store user feedback on a suggestion.
    
    Args:
        db: Database session
        feedback_data: Feedback dictionary
    
    Returns:
        Stored UserFeedback object
    """
    try:
        feedback = UserFeedback(
            suggestion_id=feedback_data['suggestion_id'],
            action=feedback_data['action'],
            feedback_text=feedback_data.get('feedback_text'),
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        logger.info(f"✅ Stored feedback for suggestion {feedback.suggestion_id}: {feedback.action}")
        return feedback
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to store feedback: {e}", exc_info=True)
        raise

