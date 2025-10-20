"""
Ask AI Router - Natural Language Query Interface
===============================================

New endpoints for natural language queries about Home Assistant devices and automations.

Flow:
1. POST /query - Parse natural language query and generate suggestions
2. POST /query/{query_id}/refine - Refine query results
3. GET /query/{query_id}/suggestions - Get all suggestions for a query
4. POST /query/{query_id}/suggestions/{suggestion_id}/approve - Approve specific suggestion

Integration:
- Uses Home Assistant Conversation API for entity extraction
- Leverages existing RAG suggestion engine
- Reuses ConversationalSuggestionCard components
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid
import json
import time
import yaml as yaml_lib

from ..database import get_db
from ..config import settings
from ..clients.ha_client import HomeAssistantClient
from ..llm.openai_client import OpenAIClient
from ..database.models import Suggestion as SuggestionModel, AskAIQuery as AskAIQueryModel
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ask-ai", tags=["Ask AI"])

# Initialize clients
ha_client = None
openai_client = None

if settings.ha_url and settings.ha_token:
    try:
        ha_client = HomeAssistantClient(settings.ha_url, settings.ha_token)
        logger.info("✅ Home Assistant client initialized for Ask AI")
    except Exception as e:
        logger.error(f"❌ Failed to initialize HA client: {e}")

if settings.openai_api_key:
    try:
        openai_client = OpenAIClient(api_key=settings.openai_api_key, model="gpt-4o-mini")
        logger.info("✅ OpenAI client initialized for Ask AI")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")


# ============================================================================
# Request/Response Models
# ============================================================================

class AskAIQueryRequest(BaseModel):
    """Request to process natural language query"""
    query: str = Field(..., description="Natural language question about devices/automations")
    user_id: str = Field(default="anonymous", description="User identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class AskAIQueryResponse(BaseModel):
    """Response from Ask AI query"""
    query_id: str
    original_query: str
    parsed_intent: str
    extracted_entities: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    confidence: float
    processing_time_ms: int
    created_at: str


class QueryRefinementRequest(BaseModel):
    """Request to refine query results"""
    refinement: str = Field(..., description="How to refine the results")
    include_context: bool = Field(default=True, description="Include original query context")


class QueryRefinementResponse(BaseModel):
    """Response from query refinement"""
    query_id: str
    refined_suggestions: List[Dict[str, Any]]
    changes_made: List[str]
    confidence: float
    refinement_count: int


# ============================================================================
# Helper Functions
# ============================================================================

async def generate_automation_yaml(suggestion: Dict[str, Any], original_query: str) -> str:
    """
    Generate Home Assistant automation YAML from a suggestion.
    
    Uses OpenAI to convert the natural language suggestion into valid HA YAML.
    Now includes entity validation to prevent "Entity not found" errors.
    
    Args:
        suggestion: Suggestion dictionary with description, trigger_summary, action_summary, devices_involved
        original_query: Original user query for context
    
    Returns:
        YAML string for the automation
    """
    if not openai_client:
        raise ValueError("OpenAI client not initialized - cannot generate YAML")
    
    # NEW: Validate entities before generating YAML
    from ..services.entity_validator import EntityValidator
    from ..clients.data_api_client import DataAPIClient
    
    try:
        # Initialize entity validator with data API client
        data_api_client = DataAPIClient()
        entity_validator = EntityValidator(data_api_client)
        
        # Map query devices to real entities
        devices_involved = suggestion.get('devices_involved', [])
        if devices_involved:
            entity_mapping = await entity_validator.map_query_to_entities(original_query, devices_involved)
            logger.info(f"Entity mapping: {entity_mapping}")
            
            # Update suggestion with validated entities
            if entity_mapping:
                suggestion['validated_entities'] = entity_mapping
            else:
                logger.warning("No valid entities found for devices in suggestion")
    except Exception as e:
        logger.error(f"Error validating entities: {e}")
        # Continue without validation if there's an error
    
    # Construct prompt for OpenAI to generate creative YAML
    validated_entities_text = ""
    if 'validated_entities' in suggestion:
        validated_entities_text = f"""
VALIDATED ENTITIES (use these exact entity IDs):
{chr(10).join([f"- {term}: {entity_id}" for term, entity_id in suggestion['validated_entities'].items()])}

CRITICAL: Use ONLY the entity IDs listed above. Do NOT create new entity IDs.
"""
    
    prompt = f"""
You are a Home Assistant automation YAML generator expert with deep knowledge of advanced HA features.

User's original request: "{original_query}"

Automation suggestion:
- Description: {suggestion.get('description', '')}
- Trigger: {suggestion.get('trigger_summary', '')}
- Action: {suggestion.get('action_summary', '')}
- Devices: {', '.join(suggestion.get('devices_involved', []))}

{validated_entities_text}

Generate a sophisticated Home Assistant automation YAML configuration that brings this creative suggestion to life.

Requirements:
1. Use YAML format (not JSON)
2. Include: id, alias, trigger, action
3. CRITICAL: Use ONLY the validated entity IDs provided above - do NOT create new entity IDs
4. Add appropriate conditions if needed
5. Include mode: single or restart
6. Add description field
7. Use advanced HA features for creative implementations:
   - `sequence` for multi-step actions
   - `choose` for conditional logic
   - `template` for dynamic values
   - `condition` for complex triggers
   - `delay` for timing
   - `repeat` for patterns
   - `parallel` for simultaneous actions

Advanced YAML Examples:
```yaml
# Sequential flashing pattern
id: office_lights_sequence
alias: "Office Lights Sequence on Door Open"
description: "Flash office lights in sequence when front door opens"
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.front_door
    to: 'on'
action:
  - repeat:
      sequence:
        - service: light.turn_on
          target:
            entity_id: light.office_left
          data:
            brightness_pct: 100
            color_name: red
        - delay: "00:00:01"
        - service: light.turn_off
          target:
            entity_id: light.office_left
        - service: light.turn_on
          target:
            entity_id: light.office_right
          data:
            brightness_pct: 100
            color_name: blue
        - delay: "00:00:01"
        - service: light.turn_off
          target:
            entity_id: light.office_right
      count: 3

# Color-coded door notifications
id: door_color_notifications
alias: "Color-Coded Door Notifications"
description: "Different colors for different doors"
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.front_door
    to: 'on'
  - platform: state
    entity_id: binary_sensor.back_door
    to: 'on'
condition:
  - condition: time
    after: "18:00:00"
    before: "06:00:00"
action:
  - choose:
      - conditions:
          - condition: trigger
            id: "0"
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.office_lights
            data:
              brightness_pct: 100
              color_name: red
              flash: long
      - conditions:
          - condition: trigger
            id: "1"
        sequence:
          - service: light.turn_on
            target:
              entity_id: light.office_lights
            data:
              brightness_pct: 100
              color_name: blue
              flash: long
    default:
      - service: light.turn_on
        target:
          entity_id: light.office_lights
        data:
          brightness_pct: 50
          color_name: white
```

Generate ONLY the YAML content, no explanations or markdown code blocks. Use advanced HA features to implement the creative suggestion properly.
"""

    try:
        # Call OpenAI to generate YAML
        response = await openai_client.client.chat.completions.create(
            model=openai_client.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a Home Assistant YAML expert. Generate valid automation YAML. Return ONLY the YAML content without markdown code blocks or explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent YAML
            max_tokens=1000
        )
        
        yaml_content = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if yaml_content.startswith('```yaml'):
            yaml_content = yaml_content[7:]  # Remove ```yaml
        elif yaml_content.startswith('```'):
            yaml_content = yaml_content[3:]  # Remove ```
        
        if yaml_content.endswith('```'):
            yaml_content = yaml_content[:-3]  # Remove closing ```
        
        yaml_content = yaml_content.strip()
        
        # Validate the YAML syntax
        try:
            yaml_lib.safe_load(yaml_content)
            logger.info(f"✅ Generated valid YAML for suggestion {suggestion.get('suggestion_id')}")
        except yaml_lib.YAMLError as e:
            logger.error(f"❌ Generated invalid YAML: {e}")
            raise ValueError(f"Generated YAML is invalid: {e}")
        
        return yaml_content
        
    except Exception as e:
        logger.error(f"Failed to generate automation YAML: {e}", exc_info=True)
        raise


def get_ha_client() -> HomeAssistantClient:
    """Dependency injection for Home Assistant client"""
    if not ha_client:
        raise HTTPException(status_code=500, detail="Home Assistant client not initialized")
    return ha_client


async def extract_entities_with_ha(query: str) -> List[Dict[str, Any]]:
    """
    Extract entities from query using pattern matching.
    
    CRITICAL: We DO NOT use HA Conversation API here because it EXECUTES commands immediately!
    Instead, we use regex patterns to extract entities without side effects.
    
    Example: "Turn on the office lights" extracts {"name": "office", "domain": "light"}
    without actually turning on the lights.
    """
    # ALWAYS use pattern matching instead of HA Conversation API
    # to avoid executing commands during entity extraction
    logger.info("🔍 Extracting entities using pattern matching (not HA Conversation API)")
    return extract_entities_from_query(query)


def extract_entities_from_query(query: str) -> List[Dict[str, Any]]:
    """
    Extract entities from query using regex patterns (PRIMARY method).
    
    This is the safe way to extract entities without triggering any actions in Home Assistant.
    Uses pattern matching to identify devices, rooms, and entity types from natural language.
    """
    import re
    
    entities = []
    query_lower = query.lower()
    
    # Extract common device patterns from the query - be more selective
    device_patterns = [
        r'(office|living room|bedroom|kitchen|garage|front|back)\s+(?:light|lights|sensor|sensors|switch|switches|door|doors|window|windows)',
        r'(?:turn on|turn off|flash|dim|control)\s+(office|living room|bedroom|kitchen|garage|front|back)\s+(?:light|lights)',
        r'(front|back|garage|office)\s+(?:door|doors)',
        r'(?:light|lights)\s+(?:in|of)\s+(office|living room|bedroom|kitchen|garage)'
    ]
    
    for pattern in device_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                # Handle multiple groups
                for group in match:
                    if group and len(group) > 1:  # Avoid single letters
                        entities.append({
                            'name': group,
                            'domain': 'unknown',
                            'state': 'unknown'
                        })
            elif match and len(match) > 1:  # Avoid single letters
                entities.append({
                    'name': match,
                    'domain': 'unknown',
                    'state': 'unknown'
                })
    
    # If still no entities, add some generic ones based on common terms
    if not entities:
        if 'office' in query_lower:
            entities.append({'name': 'office', 'domain': 'room', 'state': 'unknown'})
        if 'light' in query_lower or 'lights' in query_lower:
            entities.append({'name': 'lights', 'domain': 'light', 'state': 'unknown'})
        if 'door' in query_lower or 'doors' in query_lower:
            entities.append({'name': 'door', 'domain': 'binary_sensor', 'state': 'unknown'})
        if 'front' in query_lower:
            entities.append({'name': 'front door', 'domain': 'binary_sensor', 'state': 'unknown'})
        if 'garage' in query_lower:
            entities.append({'name': 'garage door', 'domain': 'binary_sensor', 'state': 'unknown'})
    
    logger.info(f"Extracted {len(entities)} entities from query using fallback method")
    return entities


async def generate_suggestions_from_query(
    query: str, 
    entities: List[Dict[str, Any]], 
    user_id: str
) -> List[Dict[str, Any]]:
    """Generate automation suggestions based on query and entities"""
    if not openai_client:
        raise ValueError("OpenAI client not available - cannot generate suggestions")
    
    try:
        # Build context for OpenAI
        entities_summary = "\n".join([
            f"- {entity['name']} ({entity['domain']}): {entity['state']}"
            for entity in entities[:5]  # Limit context
        ])
        
        prompt = f"""
You are a HIGHLY CREATIVE and experienced Home Assistant automation expert. Your goal is to generate 3-4 DISTINCT, DIVERSE, and IMAGINATIVE automation suggestions based on the user's query. Think beyond literal interpretations and propose creative scenarios, combining devices, varying actions, and considering different conditions.

Query: "{query}"

Available devices:
{entities_summary}

CREATIVE EXAMPLES TO INSPIRE YOU:
- Instead of just "flash lights when door opens", consider: "Flash all four office lights in sequence (left, right, back, front) when front door opens"
- Instead of simple on/off, think: "Flash red for front door opening and blue for back door opening"
- Combine multiple triggers: "Flash lights when BOTH front and garage doors open"
- Add conditions: "Flash lights when door opens, but only after sunset"
- Use different patterns: "Strobe lights rapidly for 3 seconds, then steady blue for 10 seconds"
- Consider device combinations: "Flash lights AND play door chime when front door opens"

Generate 3-4 CREATIVE and DISTINCT automation suggestions. Each suggestion must be UNIQUE and offer a different perspective. Be imaginative and think of creative ways to use the available devices.

Each suggestion should:
1. Have a creative, detailed description with specific details about patterns, colors, sequences
2. Specify the trigger (when it happens) - be specific about conditions
3. Specify the action (what it does) - include patterns, colors, timing details
4. List the devices involved - think of creative combinations
5. Have a confidence score (0.0-1.0)

Return as JSON array with this structure:
[
  {{
    "description": "Creative, detailed description with specific patterns/colors/sequences",
    "trigger_summary": "Specific trigger conditions",
    "action_summary": "Detailed action with patterns/colors/timing",
    "devices_involved": ["Device1", "Device2", "Device3"],
    "confidence": 0.85
  }},
  {{
    "description": "Another creative variation with different approach",
    "trigger_summary": "Different trigger conditions",
    "action_summary": "Different action pattern",
    "devices_involved": ["Device1", "Device4"],
    "confidence": 0.80
  }},
  {{
    "description": "Third creative suggestion with unique combination",
    "trigger_summary": "Unique trigger setup",
    "action_summary": "Unique action pattern",
    "devices_involved": ["Device2", "Device3", "Device5"],
    "confidence": 0.75
  }},
  {{
    "description": "Fourth creative suggestion with advanced features",
    "trigger_summary": "Advanced trigger conditions",
    "action_summary": "Advanced action with multiple steps",
    "devices_involved": ["Device1", "Device2", "Device3", "Device4"],
    "confidence": 0.70
  }}
]
"""

        # Call OpenAI API directly for Ask AI queries
        logger.info(f"Calling OpenAI with prompt length: {len(prompt)}")
        logger.info(f"OpenAI client available: {openai_client is not None}")
        logger.info(f"OpenAI model: {openai_client.model if openai_client else 'None'}")
        
        try:
            response = await openai_client.client.chat.completions.create(
                model=openai_client.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a HIGHLY CREATIVE Home Assistant automation expert. Generate 3-4 DISTINCT, DIVERSE, and IMAGINATIVE automation suggestions based on user queries. Think beyond literal interpretations and propose creative scenarios with patterns, colors, sequences, and device combinations. Return as JSON array with description, trigger_summary, action_summary, devices_involved, and confidence fields."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.9,
                max_tokens=1200
            )
            
            logger.info(f"OpenAI response received: {response}")
            logger.info(f"Response choices count: {len(response.choices) if response.choices else 0}")
            if response.choices:
                logger.info(f"First choice content length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
        
        # Parse OpenAI response
        suggestions = []
        try:
            import json
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response content: {content[:200]}...")
            
            if not content:
                logger.warning("OpenAI returned empty response")
                raise ValueError("Empty response from OpenAI")
            
            # Remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            elif content.startswith('```'):
                content = content[3:]  # Remove ```
            
            if content.endswith('```'):
                content = content[:-3]  # Remove closing ```
            
            content = content.strip()
            logger.info(f"Cleaned content: {content[:200]}...")
                
            parsed = json.loads(content)
            for i, suggestion in enumerate(parsed):
                suggestions.append({
                    'suggestion_id': f'ask-ai-{uuid.uuid4().hex[:8]}',
                    'description': suggestion['description'],
                    'trigger_summary': suggestion['trigger_summary'],
                    'action_summary': suggestion['action_summary'],
                    'devices_involved': suggestion['devices_involved'],
                    'confidence': suggestion['confidence'],
                    'status': 'draft',
                    'created_at': datetime.now().isoformat()
                })
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse OpenAI response: {e}")
            logger.warning(f"Raw content that failed to parse: '{content}'")
            # Fallback if JSON parsing fails
            suggestions = [{
                'suggestion_id': f'ask-ai-{uuid.uuid4().hex[:8]}',
                'description': f"Automation suggestion for: {query}",
                'trigger_summary': "Based on your query",
                'action_summary': "Device control",
                'devices_involved': [entity['name'] for entity in entities[:3]],
                'confidence': 0.7,
                'status': 'draft',
                'created_at': datetime.now().isoformat()
            }]
        
        logger.info(f"Generated {len(suggestions)} suggestions for query: {query}")
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}")
        raise


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/query", response_model=AskAIQueryResponse, status_code=status.HTTP_201_CREATED)
async def process_natural_language_query(
    request: AskAIQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> AskAIQueryResponse:
    """
    Process natural language query and generate automation suggestions.
    
    This is the main endpoint for the Ask AI tab.
    """
    start_time = datetime.now()
    query_id = f"query-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"🤖 Processing Ask AI query: {request.query}")
    
    try:
        # Step 1: Extract entities using Home Assistant
        entities = await extract_entities_with_ha(request.query)
        
        # Step 2: Generate suggestions using OpenAI + entities
        suggestions = await generate_suggestions_from_query(
            request.query, 
            entities, 
            request.user_id
        )
        
        # Step 3: Calculate confidence based on entity extraction and suggestion quality
        confidence = min(0.9, 0.5 + (len(entities) * 0.1) + (len(suggestions) * 0.1))
        
        # Step 4: Determine parsed intent
        intent_keywords = {
            'automation': ['automate', 'automatic', 'schedule', 'routine'],
            'control': ['turn on', 'turn off', 'switch', 'control'],
            'monitoring': ['monitor', 'alert', 'notify', 'watch'],
            'energy': ['energy', 'power', 'electricity', 'save']
        }
        
        parsed_intent = 'general'
        query_lower = request.query.lower()
        for intent, keywords in intent_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                parsed_intent = intent
                break
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Step 5: Save query to database
        query_record = AskAIQueryModel(
            query_id=query_id,
            original_query=request.query,
            user_id=request.user_id,
            parsed_intent=parsed_intent,
            extracted_entities=entities,
            suggestions=suggestions,
            confidence=confidence,
            processing_time_ms=int(processing_time)
        )
        
        db.add(query_record)
        await db.commit()
        await db.refresh(query_record)
        
        response = AskAIQueryResponse(
            query_id=query_id,
            original_query=request.query,
            parsed_intent=parsed_intent,
            extracted_entities=entities,
            suggestions=suggestions,
            confidence=confidence,
            processing_time_ms=int(processing_time),
            created_at=datetime.now().isoformat()
        )
        
        logger.info(f"✅ Ask AI query processed and saved: {len(suggestions)} suggestions, {confidence:.2f} confidence")
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to process Ask AI query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/query/{query_id}/refine", response_model=QueryRefinementResponse)
async def refine_query_results(
    query_id: str,
    request: QueryRefinementRequest,
    db: AsyncSession = Depends(get_db)
) -> QueryRefinementResponse:
    """
    Refine the results of a previous Ask AI query.
    """
    logger.info(f"🔧 Refining Ask AI query {query_id}: {request.refinement}")
    
    # For now, return mock refinement
    # TODO: Implement actual refinement logic
    refined_suggestions = [{
        'suggestion_id': f'refined-{uuid.uuid4().hex[:8]}',
        'description': f"Refined suggestion: {request.refinement}",
        'trigger_summary': "Refined trigger",
        'action_summary': "Refined action",
        'devices_involved': [],
        'confidence': 0.8,
        'status': 'draft',
        'created_at': datetime.now().isoformat()
    }]
    
    return QueryRefinementResponse(
        query_id=query_id,
        refined_suggestions=refined_suggestions,
        changes_made=[f"Applied refinement: {request.refinement}"],
        confidence=0.8,
        refinement_count=1
    )


@router.get("/query/{query_id}/suggestions")
async def get_query_suggestions(
    query_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all suggestions for a specific query.
    """
    # For now, return empty list
    # TODO: Store and retrieve suggestions from database
    return {
        "query_id": query_id,
        "suggestions": [],
        "total_count": 0
    }


@router.post("/query/{query_id}/suggestions/{suggestion_id}/test")
async def test_suggestion_from_query(
    query_id: str,
    suggestion_id: str,
    db: AsyncSession = Depends(get_db),
    ha_client: HomeAssistantClient = Depends(get_ha_client)
) -> Dict[str, Any]:
    """
    Test a suggestion by creating a temporary automation in HA and triggering it.
    
    This allows you to see the automation in action before approving it.
    
    Steps:
    1. Validate YAML syntax
    2. Create temporary automation in Home Assistant (with "test_" prefix)
    3. Trigger the automation immediately
    4. Return results (automation stays in HA as disabled for review)
    """
    logger.info(f"🧪 Testing suggestion {suggestion_id} from query {query_id}")
    
    try:
        # Get the query from database
        query = await db.get(AskAIQueryModel, query_id)
        if not query:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")
        
        # Find the specific suggestion
        suggestion = None
        for s in query.suggestions:
            if s.get('suggestion_id') == suggestion_id:
                suggestion = s
                break
        
        if not suggestion:
            raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")
        
        # Generate YAML for the suggestion
        automation_yaml = await generate_automation_yaml(suggestion, query.original_query)
        
        # Validate the YAML first
        if not ha_client:
            raise HTTPException(status_code=500, detail="Home Assistant client not initialized")
        
        validation_result = await ha_client.validate_automation(automation_yaml)
        
        if not validation_result.get('valid', False):
            return {
                "suggestion_id": suggestion_id,
                "query_id": query_id,
                "valid": False,
                "executed": False,
                "automation_yaml": automation_yaml,
                "validation_details": {
                    "error": validation_result.get('error'),
                    "warnings": validation_result.get('warnings', []),
                    "entity_count": validation_result.get('entity_count', 0)
                },
                "message": f"Validation failed: {validation_result.get('error')}"
            }
        
        # Parse YAML and add test prefix to ID
        automation_data = yaml_lib.safe_load(automation_yaml)
        original_id = automation_data.get('id', 'ai_test_automation')
        test_id = f"test_{original_id}_{suggestion_id.split('-')[-1]}"
        automation_data['id'] = test_id
        automation_data['alias'] = f"[TEST] {automation_data.get('alias', 'AI Test Automation')}"
        
        # Re-serialize to YAML
        test_automation_yaml = yaml_lib.dump(automation_data, default_flow_style=False, sort_keys=False)
        
        # Create temporary automation in Home Assistant
        logger.info(f"🚀 Creating test automation: {test_id}")
        creation_result = await ha_client.create_automation(test_automation_yaml)
        
        if not creation_result.get('success'):
            return {
                "suggestion_id": suggestion_id,
                "query_id": query_id,
                "valid": True,
                "executed": False,
                "automation_yaml": automation_yaml,
                "validation_details": validation_result,
                "error": creation_result.get('error'),
                "message": f"Failed to create test automation: {creation_result.get('error')}"
            }
        
        automation_id = creation_result.get('automation_id', f"automation.{test_id}")
        
        # Trigger the automation immediately
        logger.info(f"▶️ Triggering test automation: {automation_id}")
        trigger_success = await ha_client.trigger_automation(automation_id)
        
        # Disable the automation after triggering (so it doesn't run again)
        await ha_client.disable_automation(automation_id)
        
        return {
            "suggestion_id": suggestion_id,
            "query_id": query_id,
            "valid": True,
            "executed": trigger_success,
            "automation_id": automation_id,
            "automation_yaml": automation_yaml,
            "test_automation_yaml": test_automation_yaml,
            "validation_details": {
                "error": validation_result.get('error'),
                "warnings": validation_result.get('warnings', []),
                "entity_count": validation_result.get('entity_count', 0)
            },
            "message": (
                f"✅ Test automation executed successfully! Check your Home Assistant devices. "
                f"The test automation '{automation_id}' has been created and disabled. "
                f"You can delete it manually or approve this suggestion to replace it."
            ) if trigger_success else (
                f"⚠️ Test automation created but failed to trigger. "
                f"Check Home Assistant logs for details. Automation ID: {automation_id}"
            )
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing suggestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/{query_id}/suggestions/{suggestion_id}/approve")
async def approve_suggestion_from_query(
    query_id: str,
    suggestion_id: str,
    db: AsyncSession = Depends(get_db),
    ha_client: HomeAssistantClient = Depends(get_ha_client)
) -> Dict[str, Any]:
    """
    Approve a suggestion and create the automation in Home Assistant.
    """
    logger.info(f"✅ Approving suggestion {suggestion_id} from query {query_id}")
    
    try:
        # Get the query from database
        query = await db.get(AskAIQueryModel, query_id)
        if not query:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")
        
        # Find the specific suggestion
        suggestion = None
        for s in query.suggestions:
            if s.get('suggestion_id') == suggestion_id:
                suggestion = s
                break
        
        if not suggestion:
            raise HTTPException(status_code=404, detail=f"Suggestion {suggestion_id} not found")
        
        # Generate YAML for the suggestion
        automation_yaml = await generate_automation_yaml(suggestion, query.original_query)
        
        # Create automation in Home Assistant
        if ha_client:
            creation_result = await ha_client.create_automation(automation_yaml)
            
            if creation_result.get('success'):
                logger.info(f"✅ Automation created successfully: {creation_result.get('automation_id')}")
                
                return {
                    "suggestion_id": suggestion_id,
                    "query_id": query_id,
                    "status": "approved",
                    "automation_id": creation_result.get('automation_id'),
                    "automation_yaml": automation_yaml,
                    "ready_to_deploy": True,
                    "warnings": creation_result.get('warnings', []),
                    "message": creation_result.get('message', 'Automation created successfully')
                }
            else:
                logger.error(f"❌ Failed to create automation: {creation_result.get('error')}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create automation: {creation_result.get('error')}"
                )
        else:
            raise HTTPException(status_code=500, detail="Home Assistant client not initialized")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving suggestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
