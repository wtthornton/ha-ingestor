# Phase 5: OpenAI Suggestion Generation
## AI-Powered Automation Creation with GPT-4o-mini

**Epic:** Combined AI-1 (Pattern-based) + AI-2 (Feature-based)  
**Duration:** 30-120 seconds  
**Cost:** ~$0.00137 per run (~10 suggestions)  
**Last Updated:** October 17, 2025  
**Last Validated:** October 19, 2025 ✅

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Phase 4 - Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md)
- [→ Next: Phase 5b - Suggestion Storage](AI_AUTOMATION_PHASE5B_STORAGE.md)

---

## 📋 Overview

**Purpose:** Generate natural language automation suggestions using OpenAI GPT-4o-mini

Phase 5 transforms analysis results into actionable automations:
1. **Pattern-Based Suggestions** (Epic AI-1) - From detected patterns in Phase 3
2. **Feature-Based Suggestions** (Epic AI-2) - From utilization opportunities in Phase 4
3. **Combined Ranking** - Merge and sort by confidence
4. **Top 10 Selection** - Keep highest-confidence suggestions
5. **Storage** - Persist to database for user review

---

## 🔄 Call Tree

```
run_daily_analysis() [line 282]
├── OpenAIClient.__init__() [line 285]
│   ├── api_key from settings.openai_api_key
│   ├── model = "gpt-4o-mini"
│   └── Initialize AsyncOpenAI client
│
├── Part A: Pattern-based Suggestions (Epic AI-1) [line 290]
│   ├── Sort patterns by confidence [line 295]
│   ├── Select top 10 patterns [line 296]
│   │
│   └── For each top_pattern:
│       ├── openai_client.generate_automation_suggestion(pattern) [line 302]
│       │   ├── _build_prompt(pattern) [llm/openai_client.py:121]
│       │   │   ├── IF time_of_day: _build_time_of_day_prompt()
│       │   │   └── IF co_occurrence: _build_co_occurrence_prompt()
│       │   │
│       │   ├── client.chat.completions.create() [openai_client.py:78]
│       │   │   ├── model = "gpt-4o-mini"
│       │   │   ├── temperature = 0.7
│       │   │   ├── max_tokens = 600
│       │   │   ├── system_prompt: "You are a home automation expert..."
│       │   │   └── user_prompt: Pattern-specific prompt
│       │   │
│       │   ├── Track token usage [openai_client.py:100]
│       │   │   ├── total_input_tokens += prompt_tokens
│       │   │   ├── total_output_tokens += completion_tokens
│       │   │   └── total_tokens_used += total_tokens
│       │   │
│       │   └── _parse_automation_response() [openai_client.py:112]
│       │       ├── Extract YAML automation block
│       │       ├── Validate Home Assistant YAML structure
│       │       └── Returns: AutomationSuggestion(
│       │           alias, description, automation_yaml,
│       │           rationale, category, priority, confidence
│       │       )
│       │
│       └── pattern_suggestions.append() [line 304]
│
├── Part B: Feature-based Suggestions (Epic AI-2) [line 330]
│   ├── IF opportunities found:
│   │   ├── FeatureSuggestionGenerator.__init__() [line 336]
│   │   │   ├── llm_client (OpenAIClient)
│   │   │   ├── feature_analyzer
│   │   │   └── db_session factory
│   │   │
│   │   └── feature_generator.generate_suggestions(max=10) [line 342]
│   │       ├── feature_intelligence/feature_suggestion_generator.py
│   │       │
│   │       ├── For each opportunity:
│   │       │   ├── Build feature-focused prompt:
│   │       │   │   - Device capabilities (unused features)
│   │       │   │   - Current utilization stats
│   │       │   │   - Underutilized feature descriptions
│   │       │   │
│   │       │   ├── llm_client.generate_automation_suggestion() [same as above]
│   │       │   └── feature_suggestions.append()
│   │       │
│   │       └── Returns: List[Dict] feature suggestions
│   │
│   └── ELSE: No opportunities, skip
│
├── Part C: Combine and Rank [line 353]
│   ├── all_suggestions = pattern_suggestions + feature_suggestions
│   ├── Sort by confidence (descending)
│   └── Keep top 10 suggestions total
│
└── Returns: all_suggestions (top 10)
```

**Key Files:**
- `llm/openai_client.py` - OpenAI API integration
- `device_intelligence/feature_suggestion_generator.py` - Feature-based prompts
- `database/crud.py` - Suggestion storage (see [Phase 5b](AI_AUTOMATION_PHASE5B_STORAGE.md))

---

## 🤖 OpenAI Model Configuration

**Model Used:** `gpt-4o-mini`

**Why GPT-4o-mini?**
- **Cost-effective**: ~80% cheaper than GPT-4
- **Fast**: Lower latency for batch processing
- **Sufficient capability**: YAML generation doesn't require GPT-4's full power
- **Good context window**: 128K tokens (more than enough for our prompts)

**API Configuration:**
```python
client = AsyncOpenAI(api_key=settings.openai_api_key)

response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[system_prompt, user_prompt],
    temperature=0.7,     # Creativity level (0.0 = deterministic, 1.0 = creative)
    max_tokens=600       # Limit response length
)
```

**Temperature Setting (0.7):**
- **Not too low**: Avoids repetitive/boring suggestions
- **Not too high**: Maintains YAML validity and consistency
- **Sweet spot**: Creative but practical automations

**Max Tokens (600):**
- Typical response: 400-500 tokens
- YAML automation: ~200 tokens
- Rationale + metadata: ~100-200 tokens
- Buffer: 100 tokens

---

## 📝 System Prompt (Fixed for All Patterns)

**The Expert Persona:**

```
You are a home automation expert creating Home Assistant automations.
Generate valid YAML automations based on detected usage patterns.
Keep automations simple, practical, and easy to understand.
Always include proper service calls and entity IDs.
```

**Why This Works:**
- Establishes expertise and authority
- Sets expectations (YAML output)
- Emphasizes simplicity (users can understand)
- Ensures technical correctness (proper service calls)

---

## 📋 Prompt Templates by Pattern Type

### Template 1: Time-of-Day Pattern

**When Used:** Device consistently activates at same time each day

**Example Pattern:**
```python
{
    'pattern_type': 'time_of_day',
    'device_id': 'light.living_room',
    'hour': 7,
    'minute': 15,
    'occurrences': 26,
    'confidence': 0.87
}
```

**Generated Prompt:**

```
Create a Home Assistant automation for this detected usage pattern:

PATTERN DETECTED:
- Device: Living Room Light in Living Room
- Entity ID: light.living_room
- Device Type: light
- Pattern: Device activates at 07:15 consistently
- Occurrences: 26 times in last 30 days
- Confidence: 87%

INSTRUCTIONS:
1. Create a valid Home Assistant automation in YAML format
2. Use a descriptive alias starting with "AI Suggested: " and include the DEVICE NAME (Living Room Light), not the entity ID
3. Use time trigger for 07:15:00
4. Determine appropriate service call based on device type (light.turn_on, light.turn_off, climate.set_temperature, etc.)
5. Provide a brief rationale (1-2 sentences) explaining why this automation makes sense
6. Categorize as: energy, comfort, security, or convenience
7. Assign priority: high, medium, or low

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Living Room Light at 07:15"
description: "Automatically control Living Room Light based on usage pattern"
trigger:
  - platform: time
    at: "07:15:00"
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
```

RATIONALE: [1-2 sentence explanation mentioning "Living Room Light" by name]
CATEGORY: [energy|comfort|security|convenience]
PRIORITY: [high|medium|low]
```

**Prompt Engineering Techniques:**
- ✅ **Structured format**: Clear sections (PATTERN, INSTRUCTIONS, OUTPUT)
- ✅ **Example output**: Shows exactly what we want
- ✅ **Specific constraints**: Device name vs entity ID, 1-2 sentences
- ✅ **Friendly names**: "Living Room Light" not "light.living_room"
- ✅ **Confidence indicator**: Shows pattern strength

---

### Template 2: Co-Occurrence Pattern

**When Used:** Two devices consistently activate together

**Example Pattern:**
```python
{
    'pattern_type': 'co_occurrence',
    'device1': 'light.kitchen',
    'device2': 'media_player.kitchen_speaker',
    'occurrences': 18,
    'confidence': 0.75,
    'metadata': {
        'avg_time_delta_seconds': 45
    }
}
```

**Generated Prompt:**

```
Create a Home Assistant automation for this device co-occurrence pattern:

PATTERN DETECTED:
- Trigger Device: Kitchen Light (entity: light.kitchen, type: light)
- Response Device: Kitchen Speaker (entity: media_player.kitchen_speaker, type: media_player)
- Co-occurrences: 18 times in last 30 days
- Confidence: 75%
- Average time between events: 45.0 seconds

USER BEHAVIOR INSIGHT:
When the user activates "Kitchen Light", they typically also activate "Kitchen Speaker" about 45 seconds later.

INSTRUCTIONS:
1. Create a valid Home Assistant automation in YAML format
2. Use light.kitchen state change as trigger
3. media_player.kitchen_speaker should be activated after approximately 45 seconds
4. Use descriptive alias starting with "AI Suggested: " and include BOTH DEVICE NAMES (Kitchen Light and Kitchen Speaker), NOT entity IDs
5. Provide rationale explaining the pattern using the device names
6. Categorize and prioritize appropriately

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Turn On Kitchen Speaker When Kitchen Light Activates"
description: "Automatically activate Kitchen Speaker when Kitchen Light is turned on"
trigger:
  - platform: state
    entity_id: light.kitchen
    to: 'on'
action:
  - delay: '00:00:45'
  - service: media_player.turn_on
    target:
      entity_id: media_player.kitchen_speaker
```

RATIONALE: [Explanation based on co-occurrence pattern, mentioning "Kitchen Light" and "Kitchen Speaker" by their friendly names]
CATEGORY: [energy|comfort|security|convenience]
PRIORITY: [high|medium|low]
```

**Unique Features:**
- ✅ **Two-device relationship**: Clear trigger → response
- ✅ **Timing information**: Includes delay between actions
- ✅ **Behavioral insight**: Explains "why" user does this
- ✅ **Context-aware**: Adjusts delay based on actual patterns

---

### Template 3: Anomaly Pattern (Future)

**When Used:** Unusual activity detected (future feature)

**Example Pattern:**
```python
{
    'pattern_type': 'anomaly',
    'device_id': 'binary_sensor.garage_door',
    'metadata': {
        'anomaly_score': 0.92
    }
}
```

**Generated Prompt:**

```
Create a Home Assistant notification automation for this anomaly:

ANOMALY DETECTED:
- Device: binary_sensor.garage_door
- Anomaly Score: 0.92
- Pattern: Unusual activity detected (outside normal usage patterns)

INSTRUCTIONS:
Create a notification automation that alerts the user when unusual behavior is detected.

OUTPUT FORMAT:
```yaml
alias: "AI Suggested: Garage Door Anomaly Alert"
description: "Notify when unusual activity detected"
trigger:
  - platform: state
    entity_id: binary_sensor.garage_door
condition:
  - condition: time
    after: "22:00:00"
    before: "06:00:00"
action:
  - service: notify.persistent_notification
    data:
      title: "Unusual Activity Detected"
      message: "{{ trigger.to_state.name }} activated at unusual time"
```

RATIONALE: [Explanation about anomaly detection]
CATEGORY: security
PRIORITY: [high|medium|low]
```

**Security Focus:**
- ✅ **Notification-based**: Alerts user instead of acting
- ✅ **Time-based condition**: Only during unusual hours
- ✅ **Always security category**: Anomalies are security concerns

---

## 🔄 Complete API Call Trace

Let's trace a real OpenAI API call from pattern to suggestion:

**Input Pattern:**
```python
pattern = {
    'pattern_type': 'time_of_day',
    'device_id': 'light.living_room',
    'hour': 7,
    'minute': 15,
    'occurrences': 26,
    'confidence': 0.87,
    'device_name': 'Living Room Light'
}
```

**Step 1: Build Prompt**
```python
prompt = _build_time_of_day_prompt(pattern, device_context)
# Returns ~250-word structured prompt (see template above)
```

**Step 2: OpenAI API Request**
```python
request = {
    "model": "gpt-4o-mini",
    "messages": [
        {
            "role": "system",
            "content": "You are a home automation expert creating Home Assistant automations..."
        },
        {
            "role": "user",
            "content": "[250-word structured prompt]"
        }
    ],
    "temperature": 0.7,
    "max_tokens": 600
}

# POST https://api.openai.com/v1/chat/completions
```

**Step 3: OpenAI API Response**
```python
response = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1729166400,
    "model": "gpt-4o-mini-2024-07-18",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": """```yaml
alias: "AI Suggested: Living Room Light at 07:15"
description: "Automatically turn on Living Room Light at 7:15 AM on weekdays"
trigger:
  - platform: time
    at: "07:15:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 80
mode: single
```

RATIONALE: Based on 26 consistent activations at 7:15 AM over the past 30 days (87% confidence), this automation will automatically turn on the Living Room Light during your weekday morning routine, providing convenient hands-free lighting at your preferred time.

CATEGORY: convenience
PRIORITY: medium"""
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 287,
        "completion_tokens": 156,
        "total_tokens": 443
    }
}
```

**Step 4: Parse Response**
```python
content = response.choices[0].message.content

suggestion = AutomationSuggestion(
    alias="AI Suggested: Living Room Light at 07:15",
    description="Automatically turn on Living Room Light at 7:15 AM on weekdays",
    automation_yaml="""alias: "AI Suggested: Living Room Light at 07:15"
description: "Automatically turn on Living Room Light at 7:15 AM on weekdays"
trigger:
  - platform: time
    at: "07:15:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      brightness_pct: 80
mode: single""",
    rationale="Based on 26 consistent activations at 7:15 AM over the past 30 days (87% confidence), this automation will automatically turn on the Living Room Light during your weekday morning routine, providing convenient hands-free lighting at your preferred time.",
    category="convenience",
    priority="medium",
    confidence=0.87
)
```

**Step 5: Token Usage Tracking**
```python
# Track for cost calculation
total_input_tokens += 287      # Prompt
total_output_tokens += 156     # Response
total_tokens_used += 443       # Total

# Cost calculation (GPT-4o-mini pricing)
cost = (287 * $0.00000015) + (156 * $0.00000060)
     = $0.000043 + $0.000094
     = $0.000137 per suggestion
```

---

## 🔍 Response Parsing

**Regex-Based Extraction:**

The system uses regex patterns to extract specific fields from the LLM's free-form response:

```python
def _extract_alias(text: str) -> str:
    # Extract: alias: "Living Room Light at 07:15"
    match = re.search(r'alias:\s*["\']?([^"\'\n]+)["\']?', text)
    return match.group(1).strip()  # "AI Suggested: Living Room Light at 07:15"

def _extract_yaml(text: str) -> str:
    # Extract YAML code block
    match = re.search(r'```(?:yaml)?\n(.*?)\n```', text, re.DOTALL)
    return match.group(1).strip()  # Full YAML content

def _extract_rationale(text: str) -> str:
    # Extract: RATIONALE: [text until CATEGORY:]
    match = re.search(r'RATIONALE:\s*(.+?)(?:CATEGORY:|PRIORITY:|$)', text, re.DOTALL)
    return match.group(1).strip()

def _extract_category(text: str) -> str:
    # Extract: CATEGORY: convenience
    match = re.search(r'CATEGORY:\s*(\w+)', text)
    category = match.group(1).lower()
    # Validate: must be one of [energy, comfort, security, convenience]
    return category if category in VALID_CATEGORIES else "convenience"

def _extract_priority(text: str) -> str:
    # Extract: PRIORITY: medium
    match = re.search(r'PRIORITY:\s*(\w+)', text)
    priority = match.group(1).lower()
    # Validate: must be one of [high, medium, low]
    return priority if priority in VALID_PRIORITIES else "medium"
```

**Fallback Strategies:**

If extraction fails, the system has intelligent fallbacks:

```python
# If YAML extraction fails, generate basic YAML
yaml_content = extract_yaml(response) or generate_fallback_yaml(pattern)

# If category extraction fails, infer from device type
category = extract_category(response) or infer_category(pattern)
# Inference: light → convenience, alarm → security, climate → comfort

# If priority fails, default to medium
priority = extract_priority(response) or "medium"
```

---

## 💰 Token Usage & Cost Analysis

**Typical API Call:**

| Component | Tokens | Cost (GPT-4o-mini) |
|-----------|--------|-------------------|
| System prompt | ~50 | $0.0000075 |
| User prompt (time-of-day) | ~237 | $0.0000356 |
| **Total Input** | **287** | **$0.0000431** |
| | | |
| YAML response | ~120 | $0.0000720 |
| Rationale | ~30 | $0.0000180 |
| Metadata | ~6 | $0.0000036 |
| **Total Output** | **156** | **$0.0000936** |
| | | |
| **Grand Total** | **443** | **$0.0001367** |

**Daily Run (10 suggestions):**
- Total tokens: ~4,430
- Total cost: ~$0.00137
- Monthly cost: ~$0.041 (~$0.50/year)

**Scaling:**
- 100 suggestions/day: ~$1.37/day = $41/month
- 1000 suggestions/day: ~$13.70/day = $411/month

**Why GPT-4o-mini is Perfect:**
- **80% cheaper than GPT-4**: (~$0.0001367 vs ~$0.0007)
- **Sufficient quality**: YAML generation doesn't need GPT-4
- **Fast**: Lower latency for batch processing
- **Scalable**: Cost-effective even at high volume

---

## ⚠️ Error Handling & Retry Logic

**3-Attempt Retry Strategy:**

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=True
)
async def generate_automation_suggestion(pattern):
    # API call here
```

**Retry Behavior:**
1. **Attempt 1**: Immediate
2. **Attempt 2**: Wait 2 seconds
3. **Attempt 3**: Wait 4 seconds
4. **Failure**: Raise exception, log error

**Common Errors:**

1. **Rate Limit (429)**
   - Wait and retry (exponential backoff)
   - Typically resolves on retry

2. **Timeout**
   - Network issue or OpenAI overload
   - Retry with fresh connection

3. **Invalid API Key (401)**
   - Configuration error
   - No retry (will fail immediately)

4. **Invalid Response**
   - LLM generated invalid JSON/YAML
   - Fallback YAML generation kicks in

**Logging:**
```python
logger.info(f"Generating suggestion for time_of_day pattern: light.living_room")
# ✅ OpenAI API call successful: 443 tokens (input: 287, output: 156)
# ✅ Generated suggestion: AI Suggested: Living Room Light at 07:15
```

---

## 📊 Token Usage Dashboard

**Real-time Tracking:**

```python
class OpenAIClient:
    def __init__(self):
        self.total_tokens_used = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    async def generate_automation_suggestion(self, pattern):
        response = await self.client.chat.completions.create(...)
        
        # Accumulate usage
        usage = response.usage
        self.total_input_tokens += usage.prompt_tokens
        self.total_output_tokens += usage.completion_tokens
        self.total_tokens_used += usage.total_tokens
        
        # Log per-call usage
        logger.info(
            f"✅ OpenAI API call: {usage.total_tokens} tokens "
            f"(input: {usage.prompt_tokens}, output: {usage.completion_tokens})"
        )
    
    def get_usage_stats(self):
        cost = (
            (self.total_input_tokens * 0.00000015) +
            (self.total_output_tokens * 0.00000060)
        )
        
        return {
            'total_tokens': self.total_tokens_used,
            'input_tokens': self.total_input_tokens,
            'output_tokens': self.total_output_tokens,
            'estimated_cost_usd': round(cost, 6),
            'model': 'gpt-4o-mini'
        }
```

**End-of-Run Report:**

```python
# After Phase 5 completes
stats = openai_client.get_usage_stats()

logger.info(f"  → OpenAI tokens: {stats['total_tokens']}")
logger.info(f"  → OpenAI cost: ${stats['estimated_cost_usd']:.6f}")

# Example output:
#   → OpenAI tokens: 4,430
#   → OpenAI cost: $0.001370
```

---

## 🎯 Prompt Engineering Best Practices

**What Makes These Prompts Effective:**

1. **Structured Format**
   - Clear sections (PATTERN, INSTRUCTIONS, OUTPUT)
   - Easy for LLM to parse and follow

2. **Example-Driven**
   - Shows exact YAML format expected
   - Reduces ambiguity

3. **Specific Constraints**
   - "Use device name, not entity ID"
   - "1-2 sentences for rationale"
   - Clear output format

4. **Context-Rich**
   - Includes occurrences, confidence
   - Provides behavioral insight
   - Explains "why" pattern exists

5. **Validation Hints**
   - "Valid Home Assistant automation"
   - Lists valid categories/priorities
   - Specifies service call format

6. **Friendly Language**
   - "Living Room Light" not "light.living_room"
   - Makes suggestions more user-friendly
   - Easier to read and understand

**What NOT to Do:**

❌ Vague prompts: "Create an automation"  
❌ No examples: "Output YAML"  
❌ No constraints: LLM might hallucinate  
❌ Technical jargon: "entity_id light.living_room"  

---

## 🚀 Future Enhancements

**Potential Improvements:**

1. **Structured Output (JSON Mode)**
   - Use OpenAI's JSON mode for guaranteed valid responses
   - Eliminates regex parsing
   - More reliable extraction

2. **Function Calling**
   - Define automation schema as OpenAI function
   - LLM returns structured data directly
   - No parsing needed

3. **Few-Shot Learning**
   - Include 2-3 example automations in prompt
   - Improves output consistency
   - Reduces hallucinations

4. **Context Window Optimization**
   - Compress prompts further
   - Use prompt caching (OpenAI beta feature)
   - Reduce cost by 50%

5. **Multi-Model Support**
   - Fallback to GPT-3.5-turbo if 4o-mini fails
   - Local LLM option (Llama, Mistral) for privacy
   - Cost optimization strategies

6. **Batch API**
   - OpenAI Batch API (50% cheaper)
   - Process 10 suggestions in single request
   - Trade latency for cost

---

## 🎯 Phase 5 Output

**Example Output:**
```python
{
    'pattern_suggestions': 6,  # From Epic AI-1
    'feature_suggestions': 4,  # From Epic AI-2
    'total_suggestions': 10,   # Top 10 kept
    'openai_tokens_used': 4430,
    'openai_cost_usd': 0.00137
}
```

**Suggestions List:**
```python
[
    {
        'type': 'pattern_automation',
        'source': 'Epic-AI-1',
        'title': 'Living Room Light Morning Routine',
        'description': 'Turn on living room lights at 7:15 AM based on weekday pattern',
        'automation_yaml': '...',  # Valid HA YAML
        'confidence': 0.87,
        'category': 'convenience',
        'priority': 'medium',
        'rationale': 'Detected consistent morning pattern...'
    },
    # ... 9 more suggestions
]
```

---

## 🔗 Next Steps

**Phase 5 Output Used By:**
- [Phase 5b: Suggestion Storage](AI_AUTOMATION_PHASE5B_STORAGE.md) - Stores suggestions in database
- [Phase 6: MQTT Notification](AI_AUTOMATION_PHASE6_MQTT.md) - Publishes completion metrics

**Related Phases:**
- [Phase 3: Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md) - Provides patterns for AI-1 suggestions
- [Phase 4: Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md) - Provides opportunities for AI-2 suggestions
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Epic:** AI-1 (Pattern-based) + AI-2 (Feature-based)

