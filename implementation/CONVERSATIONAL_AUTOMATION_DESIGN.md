# Conversational Automation Suggestion System - Design Document

**Status:** Design Phase  
**Date:** October 17, 2025  
**Goal:** Replace YAML-first with description-first conversational automation suggestions

---

## ⚠️ ALPHA DEPLOYMENT NOTICE

**This is an Alpha feature.** We will:
- ✅ **Delete all existing suggestions** (clean slate)
- ✅ **Drop and recreate database table** (no migrations)
- ✅ **Reprocess patterns** to generate fresh suggestions
- ✅ **No data preservation** (acceptable in Alpha)

**Why this is OK:**
- 🔬 We're in Alpha - no production users
- ⚡ Faster development - no migration complexity
- 🧪 Clean testing environment
- 🔄 Easy to iterate and refine

**Migration to Beta:** When we hit Beta, we'll add proper migrations.

---

## Executive Summary

Transform the automation suggestion system from "generate YAML → show to user" to "generate description → refine conversationally → generate YAML only on approval". This makes automations accessible to non-technical users while reducing errors and improving UX.

**Key Benefits:**
- ✅ No YAML intimidation for users
- ✅ Iterative refinement before implementation
- ✅ Capability discovery integrated into flow
- ✅ Natural language throughout
- ✅ Validation before YAML generation

**Cost Impact:** +$0.36/month for typical usage (negligible)

---

## Architecture Overview

### **Current Flow (YAML-First)**
```
Pattern Detection
    ↓
Generate YAML + Description (1 OpenAI call)
    ↓
Show to user (scary YAML visible)
    ↓
User approves/rejects (no editing)
    ↓
Deploy to HA
```

### **New Flow (Description-First)**
```
Pattern Detection
    ↓
Generate Description Only (1 OpenAI call)
    ↓
Show readable description + capabilities
    ↓
User edits with natural language (0-N OpenAI calls)
    ↓
User approves final description
    ↓
Generate YAML (1 OpenAI call)
    ↓
Validate YAML
    ↓
Deploy to HA
```

**Total OpenAI Calls:** 2-5 per automation (vs 1 currently)

---

## Database Schema Changes

### **⚠️ ALPHA APPROACH: Delete and Recreate**

Since we're in **Alpha**, we don't need migrations. We'll:
1. **Delete all existing suggestions** (`DELETE FROM automation_suggestions`)
2. **Drop and recreate the table** with new schema
3. **Reprocess patterns** to generate new suggestions

This is acceptable in Alpha because:
- ✅ No production users yet
- ✅ Faster than migrations
- ✅ Clean slate for testing
- ✅ Can iterate quickly

### **New `automation_suggestions` Table Schema**

```sql
-- Drop existing table (ALPHA ONLY!)
DROP TABLE IF EXISTS automation_suggestions CASCADE;

-- Create new table with conversational design
CREATE TABLE automation_suggestions (
    id VARCHAR(50) PRIMARY KEY,
    pattern_id VARCHAR(50) NOT NULL,
    
    -- Description-first fields (NEW)
    description_only TEXT NOT NULL,              -- Human-readable description
    conversation_history JSONB DEFAULT '[]',     -- Edit history
    device_capabilities JSONB DEFAULT '{}',      -- Cached capabilities
    refinement_count INTEGER DEFAULT 0,
    
    -- YAML generation (generated ONLY after approval)
    automation_yaml TEXT,                        -- NULL until approved
    yaml_generated_at TIMESTAMP,                 -- Track when YAML created
    
    -- Status tracking (NEW)
    status VARCHAR(50) DEFAULT 'draft',          -- draft | refining | yaml_generated | deployed | rejected
    
    -- Legacy fields (kept for compatibility)
    title VARCHAR(255),
    category VARCHAR(50),
    priority VARCHAR(50),
    confidence FLOAT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    deployed_at TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (pattern_id) REFERENCES patterns(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_suggestions_status ON automation_suggestions(status);
CREATE INDEX idx_suggestions_created ON automation_suggestions(created_at DESC);
CREATE INDEX idx_suggestions_pattern ON automation_suggestions(pattern_id);

-- Status values:
-- 'draft'           -> Initial suggestion, no YAML yet
-- 'refining'        -> User is editing
-- 'yaml_generated'  -> YAML created, ready to deploy
-- 'deployed'        -> Active in HA
-- 'rejected'        -> User rejected
```

### **Alpha Migration Script**

```sql
-- alpha_reset_suggestions.sql
-- Run this to clean slate for conversational system

BEGIN;

-- Delete all existing suggestions
DELETE FROM automation_suggestions;

-- Drop and recreate with new schema
DROP TABLE IF EXISTS automation_suggestions CASCADE;

-- Create new table (see schema above)
CREATE TABLE automation_suggestions (
    -- ... full schema ...
);

COMMIT;

-- Reprocess patterns to generate new suggestions
-- (Run via Python script: python scripts/reprocess_patterns.py)
```

### **Alpha Reset Checklist**

Before starting implementation, run this checklist:

```bash
# 1. Backup existing suggestions (optional, for reference)
pg_dump -d ai_automation -t automation_suggestions > backup_suggestions.sql

# 2. Stop the AI automation service
docker-compose stop ai-automation-service

# 3. Run reset script
psql -d ai_automation -f services/ai-automation-service/sql/alpha_reset_suggestions.sql

# 4. Verify table structure
psql -d ai_automation -c "\d automation_suggestions"

# 5. Deploy updated code (with new models)
docker-compose up -d --build ai-automation-service

# 6. Reprocess patterns to generate new suggestions
python services/ai-automation-service/scripts/reprocess_patterns.py

# 7. Verify new suggestions created
curl http://localhost:8018/api/v1/suggestions | jq '.suggestions[] | {id, status, description_only}'
```

**Expected Output:**
```json
[
  {
    "id": "suggestion-new-1",
    "status": "draft",
    "description_only": "When motion is detected in the Living Room after 6PM, turn on the Living Room Light to 50% brightness"
  },
  {
    "id": "suggestion-new-2",
    "status": "draft",
    "description_only": "Turn off the Coffee Maker automatically at 10 AM every weekday"
  }
]
```

---

### **Schema Example**
```json
{
  "id": "suggestion-123",
  "pattern_id": "pattern-456",
  "description_only": "When motion is detected in the Living Room after 6PM, turn on the Living Room Light to 50% brightness",
  "conversation_history": [
    {
      "timestamp": "2025-10-17T18:30:00Z",
      "user_input": "Make it blue",
      "updated_description": "When motion is detected in the Living Room after 6PM, turn on the Living Room Light to blue",
      "validation_result": {"ok": true, "message": "Device supports RGB colors"}
    },
    {
      "timestamp": "2025-10-17T18:31:00Z",
      "user_input": "Only on weekdays",
      "updated_description": "When motion is detected in the Living Room after 6PM on weekdays, turn on the Living Room Light to blue",
      "validation_result": {"ok": true}
    }
  ],
  "device_capabilities": {
    "light.living_room": {
      "supported_features": ["brightness", "rgb_color", "color_temp", "transition"],
      "friendly_capabilities": [
        "Adjust brightness (0-100%)",
        "Change color (RGB)",
        "Set color temperature (warm to cool)",
        "Smooth transitions (fade in/out)"
      ]
    }
  },
  "refinement_count": 2,
  "automation_yaml": null,  // Generated only after approval
  "yaml_generated_at": null,
  "status": "refining",
  "confidence": 0.89,
  "created_at": "2025-10-17T18:25:00Z",
  "approved_at": null
}
```

---

## API Contracts

### **1. Generate Initial Suggestion (Modified)**

**Endpoint:** `POST /api/v1/suggestions/generate`

**Request:**
```json
{
  "pattern_id": "pattern-456",
  "pattern_type": "time_of_day",
  "device_id": "light.living_room",
  "metadata": {
    "hour": 18,
    "minute": 0,
    "occurrences": 24,
    "confidence": 0.89
  }
}
```

**Response:**
```json
{
  "suggestion_id": "suggestion-123",
  "description": "When motion is detected in the Living Room after 6PM, turn on the Living Room Light to 50% brightness",
  "trigger_summary": "Motion detected after 6PM",
  "action_summary": "Turn on Living Room Light (50%)",
  "devices_involved": [
    {
      "entity_id": "light.living_room",
      "friendly_name": "Living Room Light",
      "domain": "light",
      "area": "Living Room",
      "capabilities": {
        "supported_features": ["brightness", "rgb_color", "color_temp", "transition"],
        "friendly_capabilities": [
          "Adjust brightness (0-100%)",
          "Change color (RGB colors)",
          "Set color temperature (2700K-6500K)",
          "Smooth transitions (fade in/out)"
        ]
      }
    }
  ],
  "confidence": 0.89,
  "status": "draft",
  "created_at": "2025-10-17T18:25:00Z"
}
```

---

### **2. Refine Suggestion (NEW)**

**Endpoint:** `POST /api/v1/suggestions/{suggestion_id}/refine`

**Request:**
```json
{
  "user_input": "Make the lights blue and only on weekdays",
  "conversation_context": true  // Include previous edits in OpenAI call
}
```

**Response:**
```json
{
  "suggestion_id": "suggestion-123",
  "updated_description": "When motion is detected in the Living Room after 6PM on weekdays, turn on the Living Room Light to blue",
  "changes_detected": [
    "Added color: blue (RGB supported ✓)",
    "Added condition: weekdays only"
  ],
  "validation": {
    "ok": true,
    "messages": [
      "✓ Device supports RGB color",
      "✓ Time condition valid"
    ],
    "warnings": []
  },
  "devices_involved": [
    {
      "entity_id": "light.living_room",
      "friendly_name": "Living Room Light",
      "capabilities_used": ["rgb_color", "brightness"],
      "capabilities_available": ["color_temp", "transition"]
    }
  ],
  "confidence": 0.92,  // May increase with refinement
  "refinement_count": 3,
  "status": "refining"
}
```

**Error Response (Invalid Request):**
```json
{
  "error": true,
  "validation": {
    "ok": false,
    "messages": [],
    "warnings": [
      "⚠️ 'Master Bedroom Light' does not support color changes (brightness only)",
      "⚠️ Suggested alternative: Use color temperature instead?"
    ]
  },
  "suggested_clarification": "This light doesn't support colors, but you can adjust brightness (0-100%) or color temperature (warm to cool). What would you like to do?",
  "keep_previous_description": true
}
```

---

### **3. Get Device Capabilities (NEW)**

**Endpoint:** `GET /api/v1/devices/{device_id}/capabilities`

**Response:**
```json
{
  "entity_id": "light.living_room",
  "friendly_name": "Living Room Light",
  "domain": "light",
  "manufacturer": "Philips",
  "model": "Hue Color Bulb",
  "area": "Living Room",
  "supported_features": {
    "brightness": {
      "available": true,
      "range": "0-100%",
      "description": "Adjust brightness level"
    },
    "rgb_color": {
      "available": true,
      "description": "Set any RGB color",
      "examples": ["blue", "red", "warm white", "cool white"]
    },
    "color_temp": {
      "available": true,
      "range": "2700K-6500K",
      "description": "Set color temperature (warm to cool)"
    },
    "transition": {
      "available": true,
      "description": "Fade in/out smoothly",
      "examples": ["fade in over 3 seconds", "instant"]
    },
    "effects": {
      "available": false
    }
  },
  "common_use_cases": [
    "Turn on to 50% brightness",
    "Set to warm white",
    "Change to blue",
    "Fade in over 2 seconds"
  ]
}
```

---

### **4. Approve and Generate YAML (NEW)**

**Endpoint:** `POST /api/v1/suggestions/{suggestion_id}/approve`

**Request:**
```json
{
  "final_description": "When motion is detected in the Living Room after 6PM on weekdays, turn on the Living Room Light to blue",
  "user_notes": "Perfect for evening movie time!"  // Optional
}
```

**Response:**
```json
{
  "suggestion_id": "suggestion-123",
  "status": "yaml_generated",
  "automation_yaml": "alias: Living Room Evening Lighting\ntrigger:\n  - platform: state\n    entity_id: binary_sensor.living_room_motion\n    to: 'on'\ncondition:\n  - condition: time\n    after: '18:00:00'\n  - condition: time\n    weekday:\n      - mon\n      - tue\n      - wed\n      - thu\n      - fri\naction:\n  - service: light.turn_on\n    target:\n      entity_id: light.living_room\n    data:\n      rgb_color: [0, 0, 255]\n      brightness_pct: 100",
  "yaml_validation": {
    "syntax_valid": true,
    "safety_score": 95,
    "issues": []
  },
  "ready_to_deploy": true,
  "preview_url": "/automation/preview/suggestion-123"
}
```

**Error Response (YAML Generation Failed):**
```json
{
  "error": true,
  "status": "yaml_generation_failed",
  "message": "Could not generate valid YAML automation",
  "details": "RGB color requires 3 values but device returned error",
  "suggestion": "Would you like to try a different color or brightness instead?",
  "rollback_to_refining": true
}
```

---

### **5. List Suggestions with Status (Updated)**

**Endpoint:** `GET /api/v1/suggestions?status=draft,refining`

**Response:**
```json
{
  "suggestions": [
    {
      "suggestion_id": "suggestion-123",
      "description": "When motion is detected in the Living Room after 6PM on weekdays, turn on the Living Room Light to blue",
      "status": "refining",
      "refinement_count": 3,
      "confidence": 0.92,
      "created_at": "2025-10-17T18:25:00Z",
      "last_edited_at": "2025-10-17T18:31:00Z",
      "has_yaml": false
    },
    {
      "suggestion_id": "suggestion-124",
      "description": "When the Front Door opens, turn on the Hallway Light for 5 minutes",
      "status": "draft",
      "refinement_count": 0,
      "confidence": 0.85,
      "created_at": "2025-10-17T17:15:00Z",
      "has_yaml": false
    },
    {
      "suggestion_id": "suggestion-125",
      "description": "Turn off the Coffee Maker automatically at 10 AM every day",
      "status": "yaml_generated",
      "refinement_count": 1,
      "confidence": 0.95,
      "created_at": "2025-10-17T16:00:00Z",
      "approved_at": "2025-10-17T16:05:00Z",
      "has_yaml": true
    }
  ],
  "total": 3,
  "by_status": {
    "draft": 1,
    "refining": 1,
    "yaml_generated": 1,
    "deployed": 0,
    "rejected": 0
  }
}
```

---

## OpenAI Prompt Templates

### **Prompt 1: Generate Initial Description (No YAML)**

```python
SYSTEM_PROMPT_DESCRIPTION_ONLY = """You are a home automation expert creating human-readable automation suggestions.

Your goal: Create a clear, conversational description of what the automation will do.
DO NOT generate YAML. Only describe the automation in plain English.

Guidelines:
- Use device friendly names, not entity IDs
- Be specific about triggers and actions
- Include timing and conditions naturally
- Write like you're explaining to a friend
- Keep it to 1-2 sentences maximum

Examples:
✓ "When motion is detected in the Kitchen after 6PM, turn on the Kitchen Light to 50% brightness"
✓ "Turn off the Coffee Maker automatically at 10 AM every weekday"
✓ "When the Front Door opens, turn on the Hallway Light for 5 minutes"

✗ "alias: Kitchen Motion Light\ntrigger:\n..." (NO YAML!)
✗ "light.kitchen turns on when binary_sensor.kitchen_motion..." (Use friendly names!)
"""

USER_PROMPT_DESCRIPTION = """Create a clear, conversational description for this detected pattern:

PATTERN DETECTED:
- Type: {pattern_type}
- Device: {device_friendly_name} ({device_id})
- Area: {area}
- Pattern Details: {pattern_details}
- Occurrences: {occurrences} times in last 30 days
- Confidence: {confidence:.0%}

DEVICE CAPABILITIES:
{capability_summary}

TASK:
Write a 1-2 sentence description of what automation this suggests.
Include WHEN it triggers and WHAT action it takes.
Use the device's friendly name: "{device_friendly_name}"

OUTPUT FORMAT:
Just the description, nothing else. No YAML, no formatting, just plain text.

Example: "When motion is detected in the Kitchen after 6PM, turn on the Kitchen Light to 50% brightness"
"""
```

---

### **Prompt 2: Refine Description with User Input**

```python
SYSTEM_PROMPT_REFINE = """You are a home automation expert helping users refine automation descriptions.

Your goal: Update the automation description based on the user's natural language edits.
DO NOT generate YAML yet. Only update the description.

Rules:
1. Preserve existing details unless user changes them
2. Add new requirements naturally into the description
3. Use device friendly names
4. Check if requested changes are possible given device capabilities
5. If something can't be done, explain why and suggest alternatives

Response format (JSON):
{
  "updated_description": "New description with user's changes",
  "changes_made": ["List of what changed"],
  "validation": {
    "ok": true/false,
    "warnings": ["Any issues with the request"],
    "alternatives": ["Suggestions if request isn't possible"]
  },
  "clarification_needed": null or "Question if request is ambiguous"
}
"""

USER_PROMPT_REFINE = """The user wants to modify this automation:

CURRENT DESCRIPTION:
"{current_description}"

USER'S REQUESTED CHANGES:
"{user_input}"

DEVICE CAPABILITIES:
{device_capabilities_json}

CONVERSATION HISTORY (previous edits):
{conversation_history}

TASK:
1. Check if the user's request is possible given device capabilities
2. If possible: Update the description to incorporate their changes
3. If not possible: Explain why and suggest alternatives
4. If ambiguous: Ask for clarification

OUTPUT (JSON only):
{
  "updated_description": "Updated description here",
  "changes_made": ["Added color: blue", "Added condition: weekdays only"],
  "validation": {
    "ok": true,
    "warnings": [],
    "alternatives": []
  },
  "clarification_needed": null
}
"""
```

---

### **Prompt 3: Generate YAML from Approved Description**

```python
SYSTEM_PROMPT_YAML_GENERATION = """You are a Home Assistant automation expert.

Your goal: Convert an approved human-readable description into valid Home Assistant YAML.

The description has been refined and approved by the user.
Now generate the precise YAML automation code.

Guidelines:
- Generate COMPLETE, VALID Home Assistant YAML
- Use exact entity IDs provided
- Include all conditions and details from description
- Use appropriate service calls for device types
- Add proper formatting and indentation
- Include helpful comments for complex logic

Response format (JSON):
{
  "yaml": "Complete YAML automation as string",
  "alias": "Automation name",
  "services_used": ["list of HA services called"],
  "confidence": 0.95
}
"""

USER_PROMPT_YAML = """Generate Home Assistant YAML for this approved automation:

APPROVED DESCRIPTION:
"{final_description}"

DEVICES INVOLVED:
{devices_metadata_json}

REFINEMENT HISTORY (for context):
{conversation_history}

DEVICE ENTITY IDS (use these exactly):
{entity_id_mapping}

TASK:
Generate a complete, valid Home Assistant automation in YAML format.
Include all triggers, conditions, and actions from the description.

OUTPUT (JSON only):
{
  "yaml": "alias: Automation Name\\ntrigger:\\n  - platform: state...",
  "alias": "Short automation name",
  "services_used": ["light.turn_on", "condition.time"],
  "confidence": 0.95
}
"""
```

---

## Implementation Strategy

### **Phase 1: Database & API Foundation (Week 1)**

**⚠️ ALPHA APPROACH: Clean Slate**

Since we're in Alpha, we'll take the fast path:

**Tasks:**
1. ✅ **Delete all existing suggestions** (run SQL script)
2. ✅ **Drop and recreate table** with new schema
3. ✅ **Update SQLAlchemy models** with new fields
4. ✅ **Add status state machine** validation
5. ✅ **Create new API endpoints** (stub implementations)
6. ✅ **Create reprocessing script** to regenerate suggestions

**Alpha Benefits:**
- No migration complexity
- Faster development
- Clean testing environment
- Easy to iterate

**SQL Script to Run:**
```bash
# Delete and recreate
psql -d ai_automation -f services/ai-automation-service/sql/alpha_reset_suggestions.sql

# Reprocess patterns
python services/ai-automation-service/scripts/reprocess_patterns.py
```

**Deliverables:**
- ✅ `alpha_reset_suggestions.sql` script
- ✅ Updated SQLAlchemy models
- ✅ API endpoint stubs (return mock data)
- ✅ `reprocess_patterns.py` script

---

### **Phase 2: Description-Only Generation (Week 2)**

**Tasks:**
1. Create new `DescriptionGenerator` class
2. Implement Prompt 1 (description-only generation)
3. Add device capability fetching from data-api
4. Update pattern detection to trigger description generation
5. Store suggestions in "draft" status (no YAML)

**Changes to `openai_client.py`:**
```python
class OpenAIClient:
    # ... existing code ...
    
    async def generate_description_only(
        self,
        pattern: Dict,
        device_context: Dict
    ) -> str:
        """Generate human-readable description without YAML"""
        prompt = self._build_description_prompt(pattern, device_context)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_DESCRIPTION_ONLY},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200  # Shorter, just description
        )
        
        return response.choices[0].message.content.strip()
```

**Deliverables:**
- ✅ `DescriptionGenerator` class
- ✅ Description-only prompt templates
- ✅ Capability fetching from data-api
- ✅ Store descriptions in DB

---

### **Phase 3: Conversational Refinement (Week 3)**

**Tasks:**
1. Create `SuggestionRefiner` class
2. Implement Prompt 2 (refinement with validation)
3. Add conversation history tracking
4. Implement capability validation
5. Add error handling for impossible requests
6. Create refinement API endpoint

**New Class:**
```python
class SuggestionRefiner:
    """Refine automation descriptions based on user input"""
    
    def __init__(self, openai_client, data_api_client):
        self.openai = openai_client
        self.data_api = data_api_client
    
    async def refine_description(
        self,
        suggestion_id: str,
        user_input: str,
        include_history: bool = True
    ) -> RefinementResult:
        """
        Refine automation description with user's natural language input.
        
        Returns:
            RefinementResult with updated description and validation
        """
        # Get current suggestion
        suggestion = await self._get_suggestion(suggestion_id)
        
        # Get device capabilities
        capabilities = await self._get_device_capabilities(suggestion.device_ids)
        
        # Build refinement prompt with history
        prompt = self._build_refinement_prompt(
            current_description=suggestion.description_only,
            user_input=user_input,
            capabilities=capabilities,
            history=suggestion.conversation_history if include_history else []
        )
        
        # Call OpenAI
        response = await self.openai.client.chat.completions.create(
            model=self.openai.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_REFINE},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # More consistent for refinement
            max_tokens=400,
            response_format={"type": "json_object"}
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        # Validate feasibility
        validation = await self._validate_feasibility(
            result['updated_description'],
            capabilities
        )
        
        # Update conversation history
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "updated_description": result['updated_description'],
            "validation_result": validation
        }
        
        return RefinementResult(
            updated_description=result['updated_description'],
            changes_made=result['changes_made'],
            validation=validation,
            clarification_needed=result.get('clarification_needed'),
            history_entry=history_entry
        )
```

**Deliverables:**
- ✅ `SuggestionRefiner` class
- ✅ Refinement prompt templates
- ✅ Conversation history tracking
- ✅ Feasibility validation
- ✅ Working `/refine` endpoint

---

### **Phase 4: YAML Generation on Approval (Week 4)**

**Tasks:**
1. Create `YAMLGenerator` class (separate from description generation)
2. Implement Prompt 3 (description → YAML)
3. Add YAML validation and safety checks
4. Implement approval workflow
5. Create `/approve` endpoint
6. Add rollback mechanism if YAML fails

**New Class:**
```python
class YAMLGenerator:
    """Generate YAML only after description is approved"""
    
    async def generate_yaml_from_description(
        self,
        suggestion_id: str,
        final_description: str
    ) -> YAMLGenerationResult:
        """
        Generate Home Assistant YAML from approved description.
        
        This is called ONLY after user approves the refined description.
        """
        # Get full context
        suggestion = await self._get_suggestion(suggestion_id)
        devices = await self._get_device_metadata(suggestion.device_ids)
        
        # Build YAML generation prompt
        prompt = self._build_yaml_prompt(
            description=final_description,
            devices=devices,
            conversation_history=suggestion.conversation_history
        )
        
        # Call OpenAI
        response = await self.openai.client.chat.completions.create(
            model=self.openai.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_YAML_GENERATION},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # Very consistent for YAML
            max_tokens=800,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate YAML syntax
        try:
            yaml.safe_load(result['yaml'])
            syntax_valid = True
        except yaml.YAMLError as e:
            syntax_valid = False
            error_message = str(e)
        
        # Safety validation
        safety_result = await self.safety_validator.validate(result['yaml'])
        
        return YAMLGenerationResult(
            yaml=result['yaml'],
            alias=result['alias'],
            syntax_valid=syntax_valid,
            safety_score=safety_result.safety_score,
            ready_to_deploy=(syntax_valid and safety_result.is_safe)
        )
```

**Deliverables:**
- ✅ `YAMLGenerator` class
- ✅ YAML generation prompt template
- ✅ Approval workflow with validation
- ✅ Rollback on YAML failure
- ✅ Working `/approve` endpoint

---

### **Phase 5: Frontend Integration (Week 5)**

**Tasks:**
1. Update `SuggestionsTab.tsx` to show descriptions first
2. Add inline editing UI with natural language input
3. Show device capabilities in expandable section
4. Add conversation history display
5. Implement approve/reject flow
6. Add loading states for OpenAI calls
7. Show YAML preview only after approval (optional)

**UI Mockup:**
```typescript
// SuggestionCard.tsx (NEW)
interface SuggestionCardProps {
  suggestion: AutomationSuggestion;
  onRefine: (input: string) => Promise<void>;
  onApprove: () => Promise<void>;
  onReject: () => Promise<void>;
}

export function SuggestionCard({ suggestion, onRefine, onApprove, onReject }: SuggestionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editInput, setEditInput] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  
  return (
    <Card className="p-6">
      {/* Title */}
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="w-5 h-5 text-yellow-500" />
        <h3 className="font-semibold">{suggestion.title}</h3>
        <Badge>{suggestion.confidence}% confident</Badge>
      </div>
      
      {/* Description */}
      <p className="text-gray-700 mb-4">
        {suggestion.description_only}
      </p>
      
      {/* Device Capabilities (Expandable) */}
      <Disclosure>
        <Disclosure.Button className="text-sm text-blue-600">
          💡 This device can also... (click to see options)
        </Disclosure.Button>
        <Disclosure.Panel className="mt-2 text-sm bg-blue-50 p-3 rounded">
          <ul className="space-y-1">
            {suggestion.device_capabilities.friendly_capabilities.map(cap => (
              <li key={cap}>• {cap}</li>
            ))}
          </ul>
          <p className="mt-2 text-gray-600 italic">
            Try saying: "Make it blue" or "Fade in slowly"
          </p>
        </Disclosure.Panel>
      </Disclosure>
      
      {/* Edit Mode */}
      {isEditing ? (
        <div className="mt-4 space-y-3">
          <textarea
            value={editInput}
            onChange={(e) => setEditInput(e.target.value)}
            placeholder="Describe your changes... (e.g., 'Make it blue and only on weekdays')"
            className="w-full p-3 border rounded"
            rows={3}
          />
          <div className="flex gap-2">
            <Button
              onClick={async () => {
                setIsRefining(true);
                await onRefine(editInput);
                setIsRefining(false);
                setEditInput('');
              }}
              disabled={isRefining}
            >
              {isRefining ? 'Updating...' : 'Update Description'}
            </Button>
            <Button variant="ghost" onClick={() => setIsEditing(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex gap-2">
          <Button onClick={onApprove} variant="primary">
            ✓ Approve & Create
          </Button>
          <Button onClick={() => setIsEditing(true)} variant="secondary">
            ✏️ Edit with natural language
          </Button>
          <Button onClick={onReject} variant="ghost">
            ✕ Not interested
          </Button>
        </div>
      )}
      
      {/* Conversation History */}
      {suggestion.refinement_count > 0 && (
        <Disclosure>
          <Disclosure.Button className="mt-4 text-sm text-gray-500">
            {suggestion.refinement_count} edit{suggestion.refinement_count > 1 ? 's' : ''} made
          </Disclosure.Button>
          <Disclosure.Panel className="mt-2 space-y-2">
            {suggestion.conversation_history.map((entry, i) => (
              <div key={i} className="text-sm bg-gray-50 p-2 rounded">
                <p className="font-medium">You said: "{entry.user_input}"</p>
                <p className="text-gray-600 mt-1">→ {entry.validation_result.message}</p>
              </div>
            ))}
          </Disclosure.Panel>
        </Disclosure>
      )}
    </Card>
  );
}
```

**Deliverables:**
- ✅ Updated `SuggestionsTab` component
- ✅ `SuggestionCard` with inline editing
- ✅ Device capabilities display
- ✅ Conversation history viewer
- ✅ Loading states and error handling

---

## Testing Strategy

### **Unit Tests**

```python
# test_description_generator.py
async def test_generate_description_only():
    """Test description generation without YAML"""
    pattern = {
        "pattern_type": "time_of_day",
        "device_id": "light.kitchen",
        "hour": 18,
        "occurrences": 24,
        "confidence": 0.89
    }
    
    description = await generator.generate_description_only(pattern, device_context)
    
    assert "kitchen" in description.lower()
    assert "6" in description or "18" in description
    assert "light" in description.lower()
    assert "alias:" not in description  # No YAML!


# test_suggestion_refiner.py
async def test_refine_with_valid_change():
    """Test refinement with valid capability"""
    result = await refiner.refine_description(
        suggestion_id="test-123",
        user_input="Make it blue"
    )
    
    assert result.validation.ok == True
    assert "blue" in result.updated_description.lower()
    assert "rgb" in result.changes_made[0].lower()


async def test_refine_with_invalid_capability():
    """Test refinement with unsupported feature"""
    result = await refiner.refine_description(
        suggestion_id="test-124",  # Device without RGB
        user_input="Make it blue"
    )
    
    assert result.validation.ok == False
    assert len(result.validation.warnings) > 0
    assert "alternative" in result.validation.warnings[0].lower()


# test_yaml_generator.py
async def test_generate_yaml_from_approved_description():
    """Test YAML generation after approval"""
    result = await yaml_gen.generate_yaml_from_description(
        suggestion_id="test-125",
        final_description="When motion detected in Kitchen after 6PM, turn on Kitchen Light to blue"
    )
    
    assert result.syntax_valid == True
    assert "alias:" in result.yaml
    assert "light.kitchen" in result.yaml
    assert "rgb_color" in result.yaml
```

### **Integration Tests**

```python
# test_full_conversation_flow.py
async def test_complete_refinement_workflow():
    """Test entire flow from detection to YAML"""
    
    # 1. Generate initial description
    suggestion = await create_suggestion_from_pattern(pattern)
    assert suggestion.status == "draft"
    assert suggestion.automation_yaml is None
    
    # 2. User refines
    refined = await refine_suggestion(suggestion.id, "Make it blue")
    assert refined.status == "refining"
    assert "blue" in refined.description_only
    
    # 3. User refines again
    refined2 = await refine_suggestion(suggestion.id, "Only on weekdays")
    assert refined2.refinement_count == 2
    assert "weekday" in refined2.description_only
    
    # 4. User approves
    approved = await approve_suggestion(suggestion.id)
    assert approved.status == "yaml_generated"
    assert approved.automation_yaml is not None
    
    # 5. Validate YAML
    yaml_obj = yaml.safe_load(approved.automation_yaml)
    assert yaml_obj['alias'] is not None
    assert "weekday" in str(yaml_obj['condition'])
    assert "rgb_color" in str(yaml_obj['action'])
```

### **E2E Tests (Playwright)**

```typescript
// test_conversational_suggestions.spec.ts
test('Complete refinement flow', async ({ page }) => {
  await page.goto('http://localhost:3001/suggestions');
  
  // Find suggestion card
  const card = page.locator('[data-testid="suggestion-card"]').first();
  
  // Check initial description visible
  await expect(card.locator('p')).toContainText('Living Room Light');
  
  // Click edit
  await card.locator('button:has-text("Edit with natural language")').click();
  
  // Type refinement
  await card.locator('textarea').fill('Make it blue and only on weekdays');
  await card.locator('button:has-text("Update Description")').click();
  
  // Wait for API call
  await page.waitForResponse(resp => resp.url().includes('/refine'));
  
  // Check updated description
  await expect(card.locator('p')).toContainText('blue');
  await expect(card.locator('p')).toContainText('weekday');
  
  // Approve
  await card.locator('button:has-text("Approve & Create")').click();
  
  // Check status changed
  await expect(card).toContainText('YAML Generated');
  await expect(card).toContainText('Ready to deploy');
});
```

---

## Cost Analysis

### **Current System (YAML-First)**
- Pattern detection: Free (local)
- Generate YAML + description: 1 OpenAI call
- **Average:** ~600 tokens = $0.0002 per suggestion

### **New System (Description-First)**
- Pattern detection: Free (local)
- Generate description: 1 OpenAI call (~300 tokens)
- Refinements: 0-3 OpenAI calls (~400 tokens each)
- Generate YAML: 1 OpenAI call (~600 tokens)
- **Average:** ~1800 tokens = $0.0006 per suggestion

### **Monthly Cost Projection**

| Usage Pattern | Current Cost | New Cost | Increase |
|--------------|-------------|----------|----------|
| 5 suggestions/day (150/month) | $0.03 | $0.09 | +$0.06 |
| 10 suggestions/day (300/month) | $0.06 | $0.18 | +$0.12 |
| 20 suggestions/day (600/month) | $0.12 | $0.36 | +$0.24 |

**Conclusion:** Cost increase is negligible (<$0.50/month even at high usage)

---

## Rollout Plan

### **Week 1-2: Backend Foundation**
- Database migrations
- API endpoints (stubs)
- Description-only generation

### **Week 3-4: Refinement System**
- Conversational refinement
- Capability validation
- YAML generation on approval

### **Week 5: Frontend**
- Updated UI components
- Inline editing
- Conversation history

### **Week 6: Testing & Polish**
- E2E tests
- Performance optimization
- Documentation

### **Week 7: Soft Launch**
- Enable for beta users
- Monitor metrics
- Gather feedback

### **Week 8: General Availability**
- Enable for all users
- Deprecate old YAML-first flow
- Monitor cost/usage

---

## Success Metrics

### **User Experience**
- ✅ **Approval rate:** >60% (vs ~40% current)
- ✅ **Refinement rate:** >50% of users edit at least once
- ✅ **Time to approve:** <2 minutes (vs ~5 minutes with YAML)
- ✅ **Rejection rate:** <20% (vs ~35% current)

### **Technical Metrics**
- ✅ **Average refinements:** 1-2 per suggestion
- ✅ **OpenAI calls:** 2-4 per suggestion
- ✅ **YAML generation success:** >95%
- ✅ **API latency:** <2s per refinement

### **Business Metrics**
- ✅ **Monthly cost:** <$1.00 for typical usage
- ✅ **User satisfaction:** >4.5/5 stars
- ✅ **Feature adoption:** >80% use refinement at least once

---

## Risk Mitigation

### **Risk 1: OpenAI Outage**
**Mitigation:** 
- Implement retry with exponential backoff
- Cache common device capabilities
- Allow users to save drafts and retry later

### **Risk 2: Ambiguous User Input**
**Mitigation:**
- Implement clarification questions in refinement
- Show device capabilities proactively
- Provide example edits

### **Risk 3: YAML Generation Failure**
**Mitigation:**
- Rollback to "refining" status
- Show error message with specific issue
- Allow user to rephrase or use fallback

### **Risk 4: Cost Overruns**
**Mitigation:**
- Rate limiting: Max 10 refinements per suggestion
- Budget alerts at $5, $10, $20 monthly spend
- Cache device capabilities aggressively

---

## Future Enhancements (Post-MVP)

1. **Voice Input:** "Hey AI, make it blue and only on weekdays"
2. **Multi-Device Suggestions:** "Also turn on the fan"
3. **Template Library:** "Make it like my other bedroom automation"
4. **A/B Testing:** Compare description-first vs YAML-first
5. **Smart Suggestions:** "Based on your edit, you might also want to..."
6. **Undo/Redo:** Roll back to previous versions
7. **Share Automations:** Export/import refined descriptions

---

## Conclusion

This conversational approach transforms automation suggestions from "scary technical YAML" to "friendly iterative conversation". The cost increase is negligible (~$0.36/month), but the UX improvement is substantial. Users can think in outcomes rather than syntax, making home automation accessible to everyone.

**Ready to implement Phase 1?**

