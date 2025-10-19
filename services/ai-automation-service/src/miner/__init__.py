"""
Automation Miner Integration

Client and enhancement extraction for community knowledge augmentation.

Epic AI-4, Story AI4.2
"""

from .miner_client import MinerClient
from .enhancement_extractor import EnhancementExtractor, Enhancement

__all__ = ["MinerClient", "EnhancementExtractor", "Enhancement"]

