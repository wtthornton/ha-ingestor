"""
Pattern Detector Base Class

Week 2 Implementation - Pattern Detection Framework
Epic AI-1, Enhanced Implementation
"""

import pandas as pd
import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod

from .pattern_types import PatternResult, PatternType

logger = logging.getLogger(__name__)


class PatternDetector(ABC):
    """
    Abstract base class for all pattern detectors

    All detectors follow this interface for consistency
    """

    def __init__(
        self,
        min_occurrences: int = 3,
        min_confidence: float = 0.7
    ):
        """
        Initialize pattern detector

        Args:
            min_occurrences: Minimum number of occurrences to consider a pattern
            min_confidence: Minimum confidence score (0.0-1.0)
        """
        self.min_occurrences = min_occurrences
        self.min_confidence = min_confidence
        self.pattern_type = self._get_pattern_type()

    @abstractmethod
    def _get_pattern_type(self) -> PatternType:
        """Return the pattern type this detector finds"""
        pass

    @abstractmethod
    def detect(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """
        Detect patterns in the event data

        Args:
            events_df: DataFrame with Home Assistant events

        Returns:
            List of detected PatternResult objects
        """
        pass

    def _calculate_confidence(
        self,
        occurrences: int,
        total_possible: int,
        consistency_score: float = 1.0
    ) -> float:
        """
        Calculate confidence score for a pattern

        Args:
            occurrences: Number of times pattern occurred
            total_possible: Total number of opportunities for pattern
            consistency_score: Additional consistency metric (0.0-1.0)

        Returns:
            Confidence score (0.0-1.0)
        """
        if total_possible == 0:
            return 0.0

        # Base confidence from frequency
        frequency_score = min(occurrences / max(total_possible, 1), 1.0)

        # Weighted average of frequency and consistency
        confidence = (0.6 * frequency_score) + (0.4 * consistency_score)

        return min(max(confidence, 0.0), 1.0)

    def _filter_by_thresholds(
        self,
        patterns: List[PatternResult]
    ) -> List[PatternResult]:
        """
        Filter patterns by occurrence and confidence thresholds

        Args:
            patterns: List of detected patterns

        Returns:
            Filtered list meeting thresholds
        """
        filtered = [
            p for p in patterns
            if p.occurrences >= self.min_occurrences
            and p.confidence >= self.min_confidence
        ]

        logger.debug(
            f"{self.pattern_type.value}: {len(filtered)}/{len(patterns)} "
            f"patterns meet thresholds (min_occ={self.min_occurrences}, "
            f"min_conf={self.min_confidence})"
        )

        return filtered

    def detect_and_filter(self, events_df: pd.DataFrame) -> List[PatternResult]:
        """
        Detect patterns and apply threshold filtering

        Args:
            events_df: DataFrame with Home Assistant events

        Returns:
            Filtered list of high-quality patterns
        """
        try:
            patterns = self.detect(events_df)
            filtered_patterns = self._filter_by_thresholds(patterns)

            logger.info(
                f"{self.pattern_type.value} detector: Found {len(filtered_patterns)} patterns"
            )

            return filtered_patterns

        except Exception as e:
            logger.error(
                f"{self.pattern_type.value} detector failed: {e}",
                exc_info=True
            )
            return []
