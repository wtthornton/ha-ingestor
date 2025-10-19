"""
OpenAI Client for Automation Suggestion Generation

Uses GPT-4o-mini to convert detected patterns into natural language
automation suggestions with valid Home Assistant YAML.

**Model:** GPT-4o-mini (cost-effective, sufficient for YAML generation)
**Temperature:** 0.7 (balanced creativity + consistency)
**Typical Cost:** $0.000137 per suggestion (~$0.50/year for daily runs)

**Complete Documentation:**
See implementation/analysis/AI_AUTOMATION_CALL_TREE_INDEX.md for:
- Complete prompt templates (time-of-day, co-occurrence, anomaly)
- API call flow and examples
- Token usage and cost analysis
- Response parsing strategies
- Error handling and retry logic

**Prompt Templates:**
- Time-of-Day: Device activates consistently at specific time
- Co-Occurrence: Two devices frequently used together
- Anomaly: Unusual activity detection (future)
"""

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Dict, Optional
import logging
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class AutomationSuggestion(BaseModel):
    """Structured output for automation suggestion"""
    alias: str = Field(description="Automation name/alias")
    description: str = Field(description="User-friendly description")
    automation_yaml: str = Field(description="Valid Home Assistant automation YAML")
    rationale: str = Field(description="Explanation of why this automation makes sense")
    category: str = Field(description="Category: energy, comfort, security, convenience")
    priority: str = Field(description="Priority: high, medium, low")
    confidence: float = Field(description="Pattern confidence score")


class OpenAIClient:
    """Client for generating automation suggestions via OpenAI API"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost savings)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        logger.info(f"OpenAI client initialized with model={model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def generate_automation_suggestion(
        self,
        pattern: Dict,
        device_context: Optional[Dict] = None,
        community_enhancements: Optional[list] = None  # NEW: Epic AI-4, Story AI4.2
    ) -> AutomationSuggestion:
        """
        Generate automation suggestion from detected pattern.
        
        Args:
            pattern: Detected pattern dict with type, device_id, metadata
            device_context: Optional device metadata (name, manufacturer, area)
        
        Returns:
            AutomationSuggestion with YAML and explanation
        
        Raises:
            Exception: If OpenAI API call fails after retries
        """
        try:
            # Build prompt based on pattern type
            prompt = self._build_prompt(pattern, device_context)
            
            # NEW: Add community enhancements if available (Epic AI-4, Story AI4.2)
            if community_enhancements:
                community_context = self._build_community_context(community_enhancements)
                prompt = f"{prompt}\n\n{community_context}"
                logger.info(f"Added {len(community_enhancements)} community enhancements to prompt")
            
            logger.info(f"Generating suggestion for {pattern['pattern_type']} pattern: {pattern.get('device_id', 'N/A')}")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a home automation expert creating Home Assistant automations. "
                            "Generate valid YAML automations based on detected usage patterns. "
                            "Keep automations simple, practical, and easy to understand. "
                            "Always include proper service calls and entity IDs."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=600
            )
            
            # Track token usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            self.total_tokens_used += usage.total_tokens
            
            logger.info(
                f"✅ OpenAI API call successful: {usage.total_tokens} tokens "
                f"(input: {usage.prompt_tokens}, output: {usage.completion_tokens})"
            )
            
            # Parse response into structured format
            content = response.choices[0].message.content
            suggestion = self._parse_automation_response(content, pattern)
            
            logger.info(f"✅ Generated suggestion: {suggestion.alias}")
            return suggestion
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error for pattern {pattern.get('pattern_type')}: {e}")
            raise
    
    def _build_prompt(self, pattern: Dict, device_context: Optional[Dict] = None) -> str:
        """
        Build prompt from pattern - KEEP IT SIMPLE.
        
        Args:
            pattern: Pattern dictionary
            device_context: Optional device metadata
        
        Returns:
            Prompt string for OpenAI
        """
        pattern_type = pattern.get('pattern_type', 'unknown')
        
        if pattern_type == 'time_of_day':
            return self._build_time_of_day_prompt(pattern, device_context)
        elif pattern_type == 'co_occurrence':
            return self._build_co_occurrence_prompt(pattern, device_context)
        elif pattern_type == 'anomaly':
            return self._build_anomaly_prompt(pattern, device_context)
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
    
    def _build_time_of_day_prompt(self, pattern: Dict, device_context: Optional[Dict] = None) -> str:
        """Build prompt for time-of-day pattern"""
        hour = pattern.get('hour', 0)
        minute = pattern.get('minute', 0)
        device_id = pattern.get('device_id', 'unknown')
        occurrences = pattern.get('occurrences', 0)
        confidence = pattern.get('confidence', 0.0)
        
        # Extract friendly name from device_context
        device_name = device_context.get('name', device_id) if device_context else device_id
        domain = device_context.get('domain', 'unknown') if device_context else 'unknown'
        area = device_context.get('area', '') if device_context else ''
        
        # Build device description
        device_desc = f"{device_name}"
        if area:
            device_desc += f" in {area}"
        
        return f"""Create a Home Assistant automation for this detected usage pattern:

PATTERN DETECTED:
- Device: {device_desc}
- Entity ID: {device_id}
- Device Type: {domain}
- Pattern: Device activates at {hour:02d}:{minute:02d} consistently
- Occurrences: {occurrences} times in last 30 days
- Confidence: {confidence:.0%}

INSTRUCTIONS:
1. Create a valid Home Assistant automation in YAML format
2. Use a descriptive alias starting with "AI Suggested: " and include the DEVICE NAME ({device_name}), not the entity ID
3. Use time trigger for {hour:02d}:{minute:02d}:00
4. Determine appropriate service call based on device type ({domain}.turn_on, {domain}.turn_off, climate.set_temperature, etc.)
5. Provide a brief rationale (1-2 sentences) explaining why this automation makes sense
6. Categorize as: energy, comfort, security, or convenience
7. Assign priority: high, medium, or low

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: {device_name} at {hour:02d}:{minute:02d}"
description: "Automatically control {device_name} based on usage pattern"
trigger:
  - platform: time
    at: "{hour:02d}:{minute:02d}:00"
action:
  - service: {domain}.turn_on
    target:
      entity_id: {device_id}
```

RATIONALE: [1-2 sentence explanation mentioning "{device_name}" by name]
CATEGORY: [energy|comfort|security|convenience]
PRIORITY: [high|medium|low]
"""
    
    def _build_co_occurrence_prompt(self, pattern: Dict, device_context: Optional[Dict] = None) -> str:
        """Build prompt for co-occurrence pattern"""
        device1 = pattern.get('device1', 'unknown')
        device2 = pattern.get('device2', 'unknown')
        occurrences = pattern.get('occurrences', 0)
        confidence = pattern.get('confidence', 0.0)
        avg_delta = pattern.get('metadata', {}).get('avg_time_delta_seconds', 0)
        
        # Extract friendly names from device_context
        if device_context and 'device1' in device_context:
            device1_name = device_context['device1'].get('name', device1)
            device1_domain = device_context['device1'].get('domain', 'unknown')
        else:
            device1_name = device1
            device1_domain = device1.split('.')[0] if '.' in device1 else 'unknown'
        
        if device_context and 'device2' in device_context:
            device2_name = device_context['device2'].get('name', device2)
            device2_domain = device_context['device2'].get('domain', 'unknown')
        else:
            device2_name = device2
            device2_domain = device2.split('.')[0] if '.' in device2 else 'unknown'
        
        return f"""Create a Home Assistant automation for this device co-occurrence pattern:

PATTERN DETECTED:
- Trigger Device: {device1_name} (entity: {device1}, type: {device1_domain})
- Response Device: {device2_name} (entity: {device2}, type: {device2_domain})
- Co-occurrences: {occurrences} times in last 30 days
- Confidence: {confidence:.0%}
- Average time between events: {avg_delta:.1f} seconds

USER BEHAVIOR INSIGHT:
When the user activates "{device1_name}", they typically also activate "{device2_name}" about {int(avg_delta)} seconds later.

INSTRUCTIONS:
1. Create a valid Home Assistant automation in YAML format
2. Use {device1} state change as trigger
3. {device2} should be activated after approximately {int(avg_delta)} seconds
4. Use descriptive alias starting with "AI Suggested: " and include BOTH DEVICE NAMES ({device1_name} and {device2_name}), NOT entity IDs
5. Provide rationale explaining the pattern using the device names
6. Categorize and prioritize appropriately

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Turn On {device2_name} When {device1_name} Activates"
description: "Automatically activate {device2_name} when {device1_name} is turned on"
trigger:
  - platform: state
    entity_id: {device1}
    to: 'on'
action:
  - delay: '00:00:{int(avg_delta):02d}'
  - service: {device2_domain}.turn_on
    target:
      entity_id: {device2}
```

RATIONALE: [Explanation based on co-occurrence pattern, mentioning "{device1_name}" and "{device2_name}" by their friendly names]
CATEGORY: [energy|comfort|security|convenience]
PRIORITY: [high|medium|low]
"""
    
    def _build_anomaly_prompt(self, pattern: Dict, device_context: Optional[Dict] = None) -> str:
        """Build prompt for anomaly pattern"""
        device_id = pattern.get('device_id', 'unknown')
        anomaly_score = pattern.get('metadata', {}).get('anomaly_score', 0)
        
        return f"""Create a Home Assistant notification automation for this anomaly:

ANOMALY DETECTED:
- Device: {device_id}
- Anomaly Score: {anomaly_score:.2f}
- Pattern: Unusual activity detected (outside normal usage patterns)

INSTRUCTIONS:
Create a notification automation that alerts the user when unusual behavior is detected.

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: [Device] Anomaly Alert"
description: "Notify when unusual activity detected"
trigger:
  - platform: state
    entity_id: {device_id}
condition:
  - condition: time
    after: "22:00:00"
    before: "06:00:00"
action:
  - service: notify.persistent_notification
    data:
      title: "Unusual Activity Detected"
      message: "{{{{ trigger.to_state.name }}}} activated at unusual time"
```

RATIONALE: [Explanation about anomaly detection]
CATEGORY: security
PRIORITY: [high|medium|low]
"""
    
    def _parse_automation_response(self, llm_response: str, pattern: Dict) -> AutomationSuggestion:
        """
        Parse LLM response into structured AutomationSuggestion.
        
        Args:
            llm_response: Raw text response from OpenAI
            pattern: Original pattern (for fallback values)
        
        Returns:
            AutomationSuggestion object
        """
        # Extract components from response
        alias = self._extract_alias(llm_response) or "AI Suggested Automation"
        description = self._extract_description(llm_response) or "Automation based on detected pattern"
        yaml_content = self._extract_yaml(llm_response) or self._generate_fallback_yaml(pattern)
        rationale = self._extract_rationale(llm_response) or "Based on observed usage patterns"
        category = self._extract_category(llm_response) or self._infer_category(pattern)
        priority = self._extract_priority(llm_response) or "medium"
        
        return AutomationSuggestion(
            alias=alias,
            description=description,
            automation_yaml=yaml_content,
            rationale=rationale,
            category=category,
            priority=priority,
            confidence=pattern.get('confidence', 0.0)
        )
    
    def _extract_alias(self, text: str) -> Optional[str]:
        """Extract alias from LLM response"""
        # Look for 'alias: "..."' in YAML block
        match = re.search(r'alias:\s*["\']?([^"\'\n]+)["\']?', text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_description(self, text: str) -> Optional[str]:
        """Extract description from LLM response"""
        match = re.search(r'description:\s*["\']?([^"\'\n]+)["\']?', text, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    def _extract_yaml(self, text: str) -> Optional[str]:
        """Extract YAML block from LLM response"""
        # Look for YAML code block
        match = re.search(r'```(?:yaml)?\n(.*?)\n```', text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Fallback: Look for alias: as start of YAML
        lines = text.split('\n')
        yaml_lines = []
        in_yaml = False
        
        for line in lines:
            if line.strip().startswith('alias:'):
                in_yaml = True
            
            if in_yaml:
                yaml_lines.append(line)
                
                # Stop at RATIONALE or CATEGORY markers
                if any(marker in line.upper() for marker in ['RATIONALE:', 'CATEGORY:', 'PRIORITY:']):
                    break
        
        return '\n'.join(yaml_lines).strip() if yaml_lines else None
    
    def _extract_rationale(self, text: str) -> Optional[str]:
        """Extract rationale explanation from LLM response"""
        match = re.search(r'RATIONALE:\s*(.+?)(?:CATEGORY:|PRIORITY:|$)', text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else None
    
    def _extract_category(self, text: str) -> Optional[str]:
        """Extract category from LLM response"""
        match = re.search(r'CATEGORY:\s*(\w+)', text, re.IGNORECASE)
        if match:
            category = match.group(1).lower()
            if category in ['energy', 'comfort', 'security', 'convenience']:
                return category
        return None
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority from LLM response"""
        match = re.search(r'PRIORITY:\s*(\w+)', text, re.IGNORECASE)
        if match:
            priority = match.group(1).lower()
            if priority in ['high', 'medium', 'low']:
                return priority
        return None
    
    def _infer_category(self, pattern: Dict) -> str:
        """
        Infer category from pattern and device type.
        
        Args:
            pattern: Pattern dictionary
        
        Returns:
            Category string
        """
        device_id = pattern.get('device_id', '').lower()
        
        # Simple heuristics based on device type
        if any(keyword in device_id for keyword in ['light', 'switch']):
            return 'convenience'
        elif any(keyword in device_id for keyword in ['climate', 'thermostat', 'temperature', 'hvac']):
            return 'comfort'
        elif any(keyword in device_id for keyword in ['alarm', 'lock', 'door', 'camera', 'motion']):
            return 'security'
        elif any(keyword in device_id for keyword in ['energy', 'power', 'electricity']):
            return 'energy'
        else:
            return 'convenience'
    
    def _generate_fallback_yaml(self, pattern: Dict) -> str:
        """
        Generate fallback YAML if LLM parsing fails.
        
        Args:
            pattern: Pattern dictionary
        
        Returns:
            Basic valid Home Assistant automation YAML
        """
        pattern_type = pattern.get('pattern_type', 'unknown')
        device_id = pattern.get('device_id', 'unknown.entity')
        
        if pattern_type == 'time_of_day':
            hour = pattern.get('hour', 0)
            minute = pattern.get('minute', 0)
            
            return f"""alias: "AI Suggested: {device_id} at {hour:02d}:{minute:02d}"
description: "Activate device at consistent time"
trigger:
  - platform: time
    at: "{hour:02d}:{minute:02d}:00"
action:
  - service: homeassistant.turn_on
    target:
      entity_id: {device_id}
"""
        
        elif pattern_type == 'co_occurrence':
            device1 = pattern.get('device1', 'unknown')
            device2 = pattern.get('device2', 'unknown')
            
            # Try to extract friendly names for fallback
            device1_name = device1.split('.')[-1].replace('_', ' ').title() if '.' in device1 else device1
            device2_name = device2.split('.')[-1].replace('_', ' ').title() if '.' in device2 else device2
            
            return f"""alias: "AI Suggested: Turn On {device2_name} When {device1_name} Activates"
description: "Activate {device2_name} when {device1_name} changes"
trigger:
  - platform: state
    entity_id: {device1}
    to: 'on'
action:
  - service: homeassistant.turn_on
    target:
      entity_id: {device2}
"""
        
        else:
            return f"""alias: "AI Suggested Automation"
description: "Pattern-based automation"
trigger:
  - platform: state
    entity_id: {device_id}
action:
  - service: homeassistant.turn_on
    target:
      entity_id: {device_id}
"""
    
    def get_usage_stats(self) -> Dict:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with token counts and estimated cost
        """
        from .cost_tracker import CostTracker
        
        cost = CostTracker.calculate_cost(
            self.total_input_tokens,
            self.total_output_tokens
        )
        
        return {
            'total_tokens': self.total_tokens_used,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'estimated_cost_usd': round(cost, 4),
            'model': self.model
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics (for testing or daily reset)"""
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        logger.info("Usage statistics reset")
    
    # ========================================================================
    # Phase 2: Conversational Automation (Story AI1.23)
    # ========================================================================
    
    async def generate_description_only(
        self,
        pattern: Dict,
        device_context: Optional[Dict] = None
    ) -> str:
        """
        Generate human-readable description WITHOUT YAML.
        
        Phase 2 of conversational flow: Show users plain English first,
        generate YAML only after approval.
        
        Args:
            pattern: Detected pattern dict
            device_context: Optional device metadata
        
        Returns:
            Plain English description (1-2 sentences)
        """
        try:
            # Build simplified prompt (description only)
            prompt = self._build_description_prompt(pattern, device_context)
            
            logger.info(f"Generating description for {pattern['pattern_type']} pattern")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a home automation expert creating simple, friendly descriptions. "
                            "Write clear 1-2 sentence descriptions of what the automation will do. "
                            "Use device friendly names, not entity IDs. "
                            "DO NOT generate YAML - only describe in plain English."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=150  # Shorter for description only
            )
            
            # Track usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            self.total_tokens_used += usage.total_tokens
            
            description = response.choices[0].message.content.strip()
            logger.info(f"✅ Description generated ({usage.total_tokens} tokens)")
            
            return description
            
        except Exception as e:
            logger.error(f"❌ Failed to generate description: {e}")
            # Fallback to simple description
            return self._generate_fallback_description(pattern, device_context)
    
    def _build_description_prompt(self, pattern: Dict, device_context: Optional[Dict]) -> str:
        """Build prompt for description-only generation"""
        pattern_type = pattern.get('pattern_type', 'unknown')
        device_id = pattern.get('device_id', 'unknown')
        device_name = device_context.get('name', device_id) if device_context else device_id
        
        if pattern_type == 'time_of_day':
            hour = pattern.get('hour', 0)
            minute = pattern.get('minute', 0)
            return (
                f"Describe this automation pattern in 1-2 simple sentences:\n"
                f"- Device: {device_name}\n"
                f"- Activates at: {hour:02d}:{minute:02d} daily\n"
                f"- Happens consistently {pattern.get('occurrences', 0)} times/month\n\n"
                f"Write like you're explaining to a friend. Use the device name '{device_name}'."
            )
        
        elif pattern_type == 'co_occurrence':
            device1 = pattern.get('device1', 'unknown')
            device2 = pattern.get('device2', 'unknown')
            device1_name = device_context.get('device1', {}).get('name', device1) if device_context else device1
            device2_name = device_context.get('device2', {}).get('name', device2) if device_context else device2
            
            return (
                f"Describe this automation pattern in 1-2 simple sentences:\n"
                f"- When '{device1_name}' turns on\n"
                f"- '{device2_name}' also turns on (within seconds)\n"
                f"- Happens consistently {pattern.get('occurrences', 0)} times/month\n\n"
                f"Write like you're explaining to a friend."
            )
        
        else:
            return f"Describe a simple automation for {device_name} in 1-2 sentences."
    
    def _generate_fallback_description(self, pattern: Dict, device_context: Optional[Dict]) -> str:
        """Generate simple fallback description if API fails"""
        pattern_type = pattern.get('pattern_type', 'unknown')
        device_id = pattern.get('device_id', 'unknown')
        device_name = device_context.get('name', device_id) if device_context else device_id
        
        if pattern_type == 'time_of_day':
            hour = pattern.get('hour', 0)
            minute = pattern.get('minute', 0)
            return f"Turn on {device_name} automatically at {hour:02d}:{minute:02d} every day"
        
        elif pattern_type == 'co_occurrence':
            device1_name = device_context.get('device1', {}).get('name', pattern.get('device1', 'Device 1')) if device_context else 'Device 1'
            device2_name = device_context.get('device2', {}).get('name', pattern.get('device2', 'Device 2')) if device_context else 'Device 2'
            return f"When {device1_name} turns on, automatically turn on {device2_name}"
        
        return f"Automate {device_name} based on usage patterns"
    
    async def refine_description(
        self,
        current_description: str,
        user_input: str,
        device_capabilities: Optional[Dict] = None
    ) -> Dict:
        """
        Refine automation description based on user's natural language input.
        
        Phase 3: User says "Make it blue" or "Only on weekdays"
        
        Args:
            current_description: Current description text
            user_input: User's requested changes
            device_capabilities: Optional device capabilities for validation
        
        Returns:
            Dict with updated_description, changes_made, validation
        """
        try:
            logger.info(f"Refining description with user input: '{user_input}'")
            
            # Build refinement prompt
            prompt = self._build_refinement_prompt(
                current_description,
                user_input,
                device_capabilities
            )
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are helping refine home automation descriptions. "
                            "Update the description based on the user's request. "
                            "Keep it simple and conversational. "
                            "If the request is unclear or impossible, explain why."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,  # More consistent for refinement
                max_tokens=200
            )
            
            # Track usage
            usage = response.usage
            self.total_input_tokens += usage.prompt_tokens
            self.total_output_tokens += usage.completion_tokens
            self.total_tokens_used += usage.total_tokens
            
            result = response.choices[0].message.content.strip()
            logger.info(f"✅ Refinement complete ({usage.total_tokens} tokens)")
            
            # Parse result (expecting simple format)
            return self._parse_refinement_result(result, current_description)
            
        except Exception as e:
            logger.error(f"❌ Refinement failed: {e}")
            return {
                'updated_description': current_description,
                'changes_made': [],
                'validation': {
                    'ok': False,
                    'error': f"Could not process refinement: {str(e)}"
                }
            }
    
    def _build_refinement_prompt(
        self,
        current_description: str,
        user_input: str,
        device_capabilities: Optional[Dict]
    ) -> str:
        """Build prompt for refinement"""
        prompt = f"""Current automation description:
"{current_description}"

User wants to change it:
"{user_input}"
"""
        
        if device_capabilities:
            prompt += f"\nDevice capabilities: {', '.join(device_capabilities.get('features', []))}"
        
        prompt += """

Update the description to incorporate the user's change.
Keep it simple (1-2 sentences).
If the change is impossible or unclear, explain why.

Respond in this format:
UPDATED: [new description here]
CHANGES: [what changed]
OK: [yes/no]
"""
        return prompt
    
    def _parse_refinement_result(self, result: str, fallback_description: str) -> Dict:
        """Parse refinement result into structured format"""
        lines = result.strip().split('\n')
        
        updated_description = fallback_description
        changes_made = []
        ok = True
        error = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('UPDATED:'):
                updated_description = line.replace('UPDATED:', '').strip()
            elif line.startswith('CHANGES:'):
                changes_text = line.replace('CHANGES:', '').strip()
                if changes_text:
                    changes_made.append(changes_text)
            elif line.startswith('OK:'):
                ok_text = line.replace('OK:', '').strip().lower()
                ok = ok_text in ['yes', 'true', 'ok']
                if not ok:
                    error = "Request could not be applied"
        
        return {
            'updated_description': updated_description,
            'changes_made': changes_made,
            'validation': {
                'ok': ok,
                'error': error
            }
        }
    
    def _build_community_context(self, enhancements: list) -> str:
        """
        Build community enhancement context for prompt augmentation
        
        Epic AI-4, Story AI4.2
        
        Args:
            enhancements: List of Enhancement objects from EnhancementExtractor
        
        Returns:
            Formatted community context string
        """
        if not enhancements:
            return ""
        
        # Group by type
        by_type = {
            'condition': [],
            'timing': [],
            'action': []
        }
        
        for enh in enhancements[:10]:  # Top 10 only to keep prompt concise
            if hasattr(enh, 'type'):
                by_type.get(enh.type, []).append(enh)
        
        context = "\n**COMMUNITY BEST PRACTICES** (80% weight YOUR patterns, 20% weight community insights):\n"
        
        if by_type['condition']:
            context += "\n**Optional Conditions** (used in high-quality community automations):\n"
            for enh in by_type['condition'][:3]:  # Top 3
                context += f"- {enh.description} (used by {enh.frequency} automations, avg quality {enh.quality_score:.2f})\n"
        
        if by_type['timing']:
            context += "\n**Optional Timing Improvements:**\n"
            for enh in by_type['timing'][:3]:
                context += f"- {enh.example}\n"
        
        if by_type['action']:
            context += "\n**Optional Action Variations:**\n"
            for enh in by_type['action'][:3]:
                context += f"- {enh.description}\n"
        
        context += "\n**IMPORTANT:** These are optional enhancements. Prioritize the user's detected patterns (PRIMARY). Community insights should augment, not replace, personal patterns.\n"
        
        return context

