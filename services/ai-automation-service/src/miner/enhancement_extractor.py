"""
Enhancement Extractor

Extracts actionable enhancements from community automations.

Epic AI-4, Story AI4.2
"""
import logging
from typing import List, Dict, Any, Literal
from collections import Counter

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Enhancement(BaseModel):
    """Structured enhancement suggestion from community"""
    
    type: Literal['condition', 'timing', 'action']
    category: str  # 'weather', 'occupancy', 'offset', 'brightness', etc.
    description: str
    example: str  # Natural language example
    applicable_devices: List[str]  # Device types this applies to
    frequency: int  # How many community automations use this
    quality_score: float  # Average quality of automations using this
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "condition",
                "category": "weather",
                "description": "Only run if temperature > 20°C",
                "example": "Add weather condition to prevent running in cold weather",
                "applicable_devices": ["climate", "thermostat"],
                "frequency": 150,
                "quality_score": 0.87
            }
        }


class EnhancementExtractor:
    """Extract applicable enhancements from community automations"""
    
    # Known enhancement patterns
    CONDITION_KEYWORDS = {
        'weather': ['weather', 'temperature', 'humidity', 'rain', 'wind'],
        'occupancy': ['person', 'occupancy', 'home', 'away', 'presence'],
        'time': ['time', 'after', 'before', 'sunrise', 'sunset'],
        'state': ['state', 'is', 'for']
    }
    
    TIMING_KEYWORDS = {
        'offset': ['offset', 'before', 'after', 'minutes'],
        'delay': ['delay', 'wait']
    }
    
    ACTION_KEYWORDS = {
        'brightness': ['brightness', 'dim', 'level'],
        'color': ['color', 'temperature', 'kelvin', 'rgb'],
        'scene': ['scene', 'preset']
    }
    
    def extract_enhancements(
        self,
        community_automations: List[Dict[str, Any]],
        user_devices: List[str]
    ) -> List[Enhancement]:
        """
        Extract applicable enhancements from community automations
        
        Args:
            community_automations: List of automation dicts from Miner
            user_devices: List of device types user has
        
        Returns:
            List of Enhancement objects, ranked by frequency × quality
        """
        if not community_automations:
            return []
        
        enhancements = []
        
        for automation in community_automations:
            # Extract condition enhancements
            conditions = automation.get('conditions', [])
            for condition in conditions:
                if isinstance(condition, dict):
                    enhancement = self._extract_condition_enhancement(
                        condition,
                        automation,
                        user_devices
                    )
                    if enhancement:
                        enhancements.append(enhancement)
            
            # Extract timing enhancements
            triggers = automation.get('triggers', [])
            for trigger in triggers:
                if isinstance(trigger, dict):
                    enhancement = self._extract_timing_enhancement(
                        trigger,
                        automation,
                        user_devices
                    )
                    if enhancement:
                        enhancements.append(enhancement)
            
            # Extract action enhancements
            actions = automation.get('actions', [])
            for action in actions:
                if isinstance(action, dict):
                    enhancement = self._extract_action_enhancement(
                        action,
                        automation,
                        user_devices
                    )
                    if enhancement:
                        enhancements.append(enhancement)
        
        # Deduplicate and rank
        ranked = self._rank_enhancements(enhancements)
        
        logger.debug(f"Extracted {len(ranked)} enhancements from {len(community_automations)} automations")
        
        return ranked
    
    def _extract_condition_enhancement(
        self,
        condition: Dict[str, Any],
        automation: Dict[str, Any],
        user_devices: List[str]
    ) -> Optional[Enhancement]:
        """Extract condition enhancement"""
        
        condition_str = str(condition).lower()
        
        # Detect category
        category = None
        for cat, keywords in self.CONDITION_KEYWORDS.items():
            if any(kw in condition_str for kw in keywords):
                category = cat
                break
        
        if not category:
            return None
        
        # Check if applicable to user's devices
        auto_devices = automation.get('devices', [])
        if not self._is_applicable(auto_devices, user_devices):
            return None
        
        # Create enhancement
        description = self._generate_condition_description(condition, category)
        example = f"Add {category} condition to your automation"
        
        return Enhancement(
            type='condition',
            category=category,
            description=description,
            example=example,
            applicable_devices=auto_devices,
            frequency=1,  # Will aggregate later
            quality_score=automation.get('quality_score', 0.0)
        )
    
    def _extract_timing_enhancement(
        self,
        trigger: Dict[str, Any],
        automation: Dict[str, Any],
        user_devices: List[str]
    ) -> Optional[Enhancement]:
        """Extract timing enhancement"""
        
        trigger_str = str(trigger).lower()
        
        # Look for offset/delay patterns
        category = None
        for cat, keywords in self.TIMING_KEYWORDS.items():
            if any(kw in trigger_str for kw in keywords):
                category = cat
                break
        
        if not category:
            return None
        
        auto_devices = automation.get('devices', [])
        if not self._is_applicable(auto_devices, user_devices):
            return None
        
        description = self._generate_timing_description(trigger, category)
        example = f"Use {category} for better timing control"
        
        return Enhancement(
            type='timing',
            category=category,
            description=description,
            example=example,
            applicable_devices=auto_devices,
            frequency=1,
            quality_score=automation.get('quality_score', 0.0)
        )
    
    def _extract_action_enhancement(
        self,
        action: Dict[str, Any],
        automation: Dict[str, Any],
        user_devices: List[str]
    ) -> Optional[Enhancement]:
        """Extract action enhancement"""
        
        action_str = str(action).lower()
        
        # Look for brightness/color/scene
        category = None
        for cat, keywords in self.ACTION_KEYWORDS.items():
            if any(kw in action_str for kw in keywords):
                category = cat
                break
        
        if not category:
            return None
        
        auto_devices = automation.get('devices', [])
        if not self._is_applicable(auto_devices, user_devices):
            return None
        
        description = self._generate_action_description(action, category)
        example = f"Use {category} for better control"
        
        return Enhancement(
            type='action',
            category=category,
            description=description,
            example=example,
            applicable_devices=auto_devices,
            frequency=1,
            quality_score=automation.get('quality_score', 0.0)
        )
    
    def _is_applicable(
        self,
        automation_devices: List[str],
        user_devices: List[str]
    ) -> bool:
        """Check if enhancement applies to user's devices"""
        if not automation_devices:
            return True  # Generic enhancement
        
        # Check overlap
        return any(device in user_devices for device in automation_devices)
    
    def _generate_condition_description(
        self,
        condition: Dict[str, Any],
        category: str
    ) -> str:
        """Generate human-readable condition description"""
        # Simplified - would be more sophisticated in production
        if category == 'weather':
            return "Add weather condition (temperature, humidity, etc.)"
        elif category == 'occupancy':
            return "Only run when home is occupied"
        elif category == 'time':
            return "Add time constraint (after sunrise, before 10 PM, etc.)"
        else:
            return f"Add {category} condition"
    
    def _generate_timing_description(
        self,
        trigger: Dict[str, Any],
        category: str
    ) -> str:
        """Generate timing description"""
        if category == 'offset':
            return "Use offset (e.g., 30 minutes before sunset)"
        elif category == 'delay':
            return "Add delay to prevent false triggers"
        else:
            return f"Use {category} for timing"
    
    def _generate_action_description(
        self,
        action: Dict[str, Any],
        category: str
    ) -> str:
        """Generate action description"""
        if category == 'brightness':
            return "Set specific brightness level (e.g., 50% instead of 100%)"
        elif category == 'color':
            return "Set color temperature (e.g., 2700K for warm light)"
        elif category == 'scene':
            return "Use scene for coordinated device control"
        else:
            return f"Use {category} action"
    
    def _rank_enhancements(
        self,
        enhancements: List[Enhancement]
    ) -> List[Enhancement]:
        """
        Deduplicate and rank enhancements
        
        Ranking: frequency × quality_score
        """
        # Group by (type, category)
        grouped: Dict[tuple, List[Enhancement]] = {}
        
        for enh in enhancements:
            key = (enh.type, enh.category)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(enh)
        
        # Aggregate each group
        aggregated = []
        
        for (etype, category), group in grouped.items():
            # Combine frequency
            total_frequency = len(group)
            
            # Average quality
            avg_quality = sum(e.quality_score for e in group) / len(group)
            
            # Collect all applicable devices
            all_devices = set()
            for e in group:
                all_devices.update(e.applicable_devices)
            
            # Use first enhancement as template
            template = group[0]
            
            aggregated.append(Enhancement(
                type=etype,
                category=category,
                description=template.description,
                example=template.example,
                applicable_devices=sorted(list(all_devices)),
                frequency=total_frequency,
                quality_score=avg_quality
            ))
        
        # Sort by rank (frequency × quality)
        aggregated.sort(
            key=lambda e: e.frequency * e.quality_score,
            reverse=True
        )
        
        return aggregated

