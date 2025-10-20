"""
Entity Validation Service for AI Automation

Validates that entities exist in Home Assistant before generating automations.
This prevents "Entity not found" errors by ensuring only real entities are used.
"""

import logging
from typing import Dict, List, Optional, Any
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EntityValidationResult:
    """Result of entity validation"""
    entity_id: str
    exists: bool
    suggested_alternatives: List[str]
    confidence_score: float


class EntityValidator:
    """
    Validates entities against real Home Assistant entities.
    
    This service ensures that automations use actual entities that exist
    in the Home Assistant instance, preventing "Entity not found" errors.
    """
    
    def __init__(self, data_api_client=None):
        self.data_api_client = data_api_client
        self.entity_cache = {}
        
    async def validate_entities(self, entity_ids: List[str]) -> Dict[str, EntityValidationResult]:
        """
        Validate a list of entity IDs against real Home Assistant entities.
        
        Args:
            entity_ids: List of entity IDs to validate
            
        Returns:
            Dictionary mapping entity_id to validation result
        """
        results = {}
        
        # Get all available entities from data-api
        available_entities = await self._get_available_entities()
        
        for entity_id in entity_ids:
            result = await self._validate_single_entity(entity_id, available_entities)
            results[entity_id] = result
            
        return results
    
    async def _get_available_entities(self) -> List[Dict[str, Any]]:
        """Get all available entities from data-api"""
        try:
            if self.data_api_client:
                entities = await self.data_api_client.get_all_entities()
                return entities
            else:
                logger.warning("Data API client not available, using empty entity list")
                return []
        except Exception as e:
            logger.error(f"Error fetching entities from data-api: {e}")
            return []
    
    async def _validate_single_entity(self, entity_id: str, available_entities: List[Dict[str, Any]]) -> EntityValidationResult:
        """
        Validate a single entity ID.
        
        Args:
            entity_id: Entity ID to validate
            available_entities: List of available entities
            
        Returns:
            EntityValidationResult with validation details
        """
        # Check if entity exists exactly
        exact_match = self._find_exact_match(entity_id, available_entities)
        if exact_match:
            return EntityValidationResult(
                entity_id=entity_id,
                exists=True,
                suggested_alternatives=[],
                confidence_score=1.0
            )
        
        # Find alternatives
        alternatives = self._find_alternatives(entity_id, available_entities)
        
        return EntityValidationResult(
            entity_id=entity_id,
            exists=False,
            suggested_alternatives=alternatives,
            confidence_score=0.0
        )
    
    def _find_exact_match(self, entity_id: str, available_entities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find exact match for entity ID"""
        for entity in available_entities:
            if entity.get('entity_id') == entity_id:
                return entity
        return None
    
    def _find_alternatives(self, entity_id: str, available_entities: List[Dict[str, Any]]) -> List[str]:
        """
        Find alternative entity IDs based on similarity.
        
        Args:
            entity_id: Entity ID to find alternatives for
            available_entities: List of available entities
            
        Returns:
            List of alternative entity IDs
        """
        alternatives = []
        
        # Extract domain and name parts
        if '.' in entity_id:
            domain, name = entity_id.split('.', 1)
        else:
            domain = 'unknown'
            name = entity_id
        
        # Find entities with same domain
        same_domain = [
            entity for entity in available_entities
            if entity.get('domain') == domain
        ]
        
        # Find entities with similar names
        name_words = set(re.findall(r'\w+', name.lower()))
        
        for entity in same_domain:
            entity_name = entity.get('entity_id', '').split('.', 1)[1] if '.' in entity.get('entity_id', '') else ''
            entity_words = set(re.findall(r'\w+', entity_name.lower()))
            
            # Calculate similarity
            common_words = name_words.intersection(entity_words)
            if common_words:
                similarity = len(common_words) / len(name_words.union(entity_words))
                if similarity > 0.3:  # 30% similarity threshold
                    alternatives.append(entity.get('entity_id'))
        
        # Limit to top 5 alternatives
        return alternatives[:5]
    
    async def map_query_to_entities(self, query: str, entities: List[str]) -> Dict[str, str]:
        """
        Map query terms to actual entity IDs.
        
        Args:
            query: Original user query
            entities: List of entities mentioned in query
            
        Returns:
            Dictionary mapping query terms to actual entity IDs
        """
        mapping = {}
        
        # Get available entities
        available_entities = await self._get_available_entities()
        
        for entity in entities:
            # Try to find best match
            best_match = self._find_best_match(entity, available_entities)
            if best_match:
                mapping[entity] = best_match['entity_id']
        
        return mapping
    
    def _find_best_match(self, query_term: str, available_entities: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find the best matching entity for a query term.
        
        Args:
            query_term: Term from user query (e.g., "office light")
            available_entities: List of available entities
            
        Returns:
            Best matching entity or None
        """
        query_words = set(re.findall(r'\w+', query_term.lower()))
        
        best_match = None
        best_score = 0
        
        for entity in available_entities:
            entity_id = entity.get('entity_id', '')
            entity_name = entity_id.split('.', 1)[1] if '.' in entity_id else entity_id
            entity_words = set(re.findall(r'\w+', entity_name.lower()))
            
            # Calculate word overlap score
            common_words = query_words.intersection(entity_words)
            if common_words:
                score = len(common_words) / len(query_words.union(entity_words))
                if score > best_score:
                    best_score = score
                    best_match = entity
        
        # Only return matches with at least 40% similarity
        return best_match if best_score >= 0.4 else None
    
    async def validate_automation_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """
        Validate all entities in an automation YAML.
        
        Args:
            yaml_content: Automation YAML content
            
        Returns:
            Validation result with entity status
        """
        import yaml
        
        try:
            automation_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return {
                "valid": False,
                "error": f"Invalid YAML: {e}",
                "entity_results": {}
            }
        
        # Extract entity IDs from YAML
        entity_ids = self._extract_entity_ids_from_yaml(automation_data)
        
        # Validate entities
        validation_results = await self.validate_entities(entity_ids)
        
        # Check if all entities are valid
        all_valid = all(result.exists for result in validation_results.values())
        
        return {
            "valid": all_valid,
            "entity_results": validation_results,
            "invalid_entities": [
                entity_id for entity_id, result in validation_results.items()
                if not result.exists
            ]
        }
    
    def _extract_entity_ids_from_yaml(self, automation_data: Dict[str, Any]) -> List[str]:
        """Extract all entity IDs from automation YAML data"""
        entity_ids = set()
        
        def extract_from_dict(data):
            if isinstance(data, dict):
                if 'entity_id' in data:
                    entity_id = data['entity_id']
                    if isinstance(entity_id, str):
                        entity_ids.add(entity_id)
                    elif isinstance(entity_id, list):
                        entity_ids.update(entity_id)
                
                for value in data.values():
                    extract_from_dict(value)
            elif isinstance(data, list):
                for item in data:
                    extract_from_dict(item)
        
        extract_from_dict(automation_data)
        return list(entity_ids)
