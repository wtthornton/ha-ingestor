"""
YAML Generator - Story AI1.23 Phase 4
======================================

Generates Home Assistant YAML from approved descriptions.
This is the FINAL step before deployment.

Flow:
1. User sees description → 2. User refines → 3. User approves → 4. Generate YAML (HERE)

Key Principles:
- Generate YAML ONLY after user approves
- Use temperature 0.2 for precise, valid YAML
- Include full conversation history for context
- Validate YAML syntax
- Run safety checks
- Rollback if generation fails
"""

from openai import AsyncOpenAI
from typing import Dict, Optional
from dataclasses import dataclass
import logging
import json
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class YAMLGenerationResult:
    """Result of YAML generation"""
    yaml: str
    alias: str
    services_used: list
    syntax_valid: bool
    safety_score: Optional[int] = None
    safety_issues: Optional[list] = None
    confidence: float = 0.95


# ============================================================================
# Prompt Templates
# ============================================================================

SYSTEM_PROMPT_YAML = """You are a Home Assistant automation expert.

Your goal: Convert an approved human-readable description into valid Home Assistant YAML.

The description has been refined and approved by the user.
Now generate the precise YAML automation code.

Guidelines:
- Generate COMPLETE, VALID Home Assistant YAML
- Use exact entity IDs provided
- Include all conditions and details from description
- Use appropriate service calls for device types
- Add proper formatting and indentation (2 spaces)
- Follow Home Assistant best practices
- Be precise - this will be deployed directly

Response format: ONLY JSON, no other text:
{
  "yaml": "Complete YAML automation as string with \\n for newlines",
  "alias": "Automation name (descriptive)",
  "services_used": ["list of HA services called, e.g., light.turn_on"],
  "confidence": 0.95
}

Example:
{
  "yaml": "alias: Morning Kitchen Light\\ntrigger:\\n  - platform: time\\n    at: '07:00:00'\\naction:\\n  - service: light.turn_on\\n    target:\\n      entity_id: light.kitchen\\n    data:\\n      brightness_pct: 100",
  "alias": "Morning Kitchen Light",
  "services_used": ["light.turn_on"],
  "confidence": 0.98
}
"""


# ============================================================================
# YAMLGenerator Class
# ============================================================================

class YAMLGenerator:
    """
    Generates Home Assistant YAML from approved descriptions.
    
    Phase 4: YAML Generation on Approval
    Story AI1.23: Conversational Suggestion Refinement
    
    Usage:
        generator = YAMLGenerator(openai_client)
        result = await generator.generate_yaml(
            description="When motion detected after 6PM, turn on Living Room Light to blue",
            devices_metadata={...},
            conversation_history=[...]
        )
    """
    
    def __init__(self, openai_client: AsyncOpenAI, model: str = "gpt-4o-mini"):
        """
        Initialize YAML generator.
        
        Args:
            openai_client: AsyncOpenAI client instance
            model: Model to use (default: gpt-4o-mini)
        """
        self.client = openai_client
        self.model = model
        self.total_tokens = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        logger.info(f"YAMLGenerator initialized with model={model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def generate_yaml(
        self,
        final_description: str,
        devices_metadata: Dict,
        conversation_history: Optional[list] = None
    ) -> YAMLGenerationResult:
        """
        Generate Home Assistant YAML from approved description.
        
        Args:
            final_description: User-approved automation description
            devices_metadata: Full device metadata with entity IDs
            conversation_history: Conversation history for context
        
        Returns:
            YAMLGenerationResult with YAML and validation info
        
        Raises:
            Exception: If OpenAI API call fails after retries
        """
        try:
            # Build YAML generation prompt
            prompt = self._build_yaml_prompt(
                final_description,
                devices_metadata,
                conversation_history or []
            )
            
            logger.info(f"🔨 Generating YAML from approved description: {final_description[:60]}...")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT_YAML
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Very precise for YAML generation
                max_tokens=800,   # Longer for complete automations
                response_format={"type": "json_object"}  # Force JSON
            )
            
            # Track token usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            self.total_tokens += usage.total_tokens
            
            logger.info(
                f"✅ YAML generated: {usage.total_tokens} tokens "
                f"(input: {usage.prompt_tokens}, output: {usage.completion_tokens})"
            )
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            yaml_data = json.loads(content)
            
            # Validate required fields
            if 'yaml' not in yaml_data or 'alias' not in yaml_data:
                raise ValueError("OpenAI response missing required fields (yaml, alias)")
            
            # Validate YAML syntax
            try:
                yaml.safe_load(yaml_data['yaml'])
                syntax_valid = True
                logger.info("✅ YAML syntax validation passed")
            except yaml.YAMLError as e:
                syntax_valid = False
                logger.error(f"❌ YAML syntax validation failed: {e}")
            
            # Build result
            result = YAMLGenerationResult(
                yaml=yaml_data['yaml'],
                alias=yaml_data['alias'],
                services_used=yaml_data.get('services_used', []),
                syntax_valid=syntax_valid,
                confidence=yaml_data.get('confidence', 0.95)
            )
            
            logger.info(f"✅ YAML generation complete: {result.alias}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse OpenAI JSON response: {e}")
            raise ValueError(f"OpenAI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"❌ OpenAI API error during YAML generation: {e}")
            raise
    
    def _build_yaml_prompt(
        self,
        final_description: str,
        devices_metadata: Dict,
        conversation_history: list
    ) -> str:
        """
        Build YAML generation prompt.
        
        Args:
            final_description: User-approved description
            devices_metadata: Device metadata with entity IDs
            conversation_history: Refinement history
        
        Returns:
            Formatted prompt for OpenAI
        """
        # Extract entity ID mapping
        entity_mapping = self._extract_entity_mapping(devices_metadata)
        
        # Format conversation history for context
        history_context = ""
        if conversation_history:
            history_context = "\n\nREFINEMENT HISTORY (for context):\n"
            for i, entry in enumerate(conversation_history, 1):
                history_context += f"{i}. User requested: \"{entry.get('user_input', 'N/A')}\"\n"
                history_context += f"   Result: {entry.get('updated_description', 'N/A')[:60]}...\n"
        
        prompt = f"""Generate Home Assistant YAML for this approved automation:

APPROVED DESCRIPTION:
"{final_description}"

DEVICES INVOLVED:
{json.dumps(devices_metadata, indent=2)}

ENTITY ID MAPPING (use these exactly):
{entity_mapping}
{history_context}

TASK:
Generate a complete, valid Home Assistant automation in YAML format.
- Include all triggers, conditions, and actions from the description
- Use exact entity IDs from the mapping above
- Follow Home Assistant YAML syntax precisely
- Add appropriate service calls based on device types
- Include any time constraints or conditions mentioned
- Use 2-space indentation

IMPORTANT:
- The description mentions specific details - include ALL of them
- If description says "blue", use rgb_color: [0, 0, 255]
- If description says "weekdays", add weekday condition
- If description says "fade in", add transition parameter
- Be precise and complete

OUTPUT (JSON only, no markdown):"""
        
        return prompt
    
    def _extract_entity_mapping(self, devices_metadata: Dict) -> str:
        """
        Extract entity ID mapping from devices metadata.
        
        Args:
            devices_metadata: Device metadata dictionary
        
        Returns:
            Formatted entity ID mapping string
        """
        mapping = []
        
        # Handle different metadata formats
        if isinstance(devices_metadata, dict):
            if 'entity_id' in devices_metadata:
                # Single device
                entity_id = devices_metadata['entity_id']
                friendly_name = devices_metadata.get('friendly_name', entity_id)
                domain = devices_metadata.get('domain', 'unknown')
                mapping.append(f"- {friendly_name}: {entity_id} (domain: {domain})")
            
            elif 'devices_involved' in devices_metadata:
                # Multiple devices
                for device in devices_metadata['devices_involved']:
                    entity_id = device.get('entity_id', 'unknown')
                    friendly_name = device.get('friendly_name', entity_id)
                    domain = device.get('domain', 'unknown')
                    mapping.append(f"- {friendly_name}: {entity_id} (domain: {domain})")
        
        return '\n'.join(mapping) if mapping else "No entity mapping available"
    
    def validate_yaml_syntax(self, yaml_string: str) -> tuple[bool, Optional[str]]:
        """
        Validate YAML syntax.
        
        Args:
            yaml_string: YAML string to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            yaml.safe_load(yaml_string)
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)
    
    def get_usage_stats(self) -> Dict:
        """
        Get token usage statistics.
        
        Returns:
            Dictionary with token counts and estimated cost
        """
        # Calculate cost (gpt-4o-mini pricing)
        INPUT_COST_PER_1M = 0.150   # $0.15 per 1M input tokens
        OUTPUT_COST_PER_1M = 0.600  # $0.60 per 1M output tokens
        
        input_cost = (self.total_input_tokens / 1_000_000) * INPUT_COST_PER_1M
        output_cost = (self.total_output_tokens / 1_000_000) * OUTPUT_COST_PER_1M
        total_cost = input_cost + output_cost
        
        return {
            'total_tokens': self.total_tokens,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'estimated_cost_usd': round(total_cost, 6),
            'model': self.model
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics"""
        self.total_tokens = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        logger.info("Usage statistics reset")

