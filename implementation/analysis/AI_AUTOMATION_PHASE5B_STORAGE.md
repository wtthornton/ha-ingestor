# Phase 5b: Suggestion Storage
## Database Schema and Lifecycle Management

**Epic:** Combined AI-1 + AI-2  
**Story:** AI1.23 - Conversational Suggestion Refinement  
**Duration:** ~500ms (10 suggestions)  
**Database:** SQLite (`suggestions` table)  
**Last Updated:** October 17, 2025

**🔗 Navigation:**
- [← Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)
- [← Previous: Phase 5 - OpenAI Suggestion Generation](AI_AUTOMATION_PHASE5_OPENAI.md)
- [→ Next: Phase 6 - MQTT Notification](AI_AUTOMATION_PHASE6_MQTT.md)

---

## 📋 Overview

**Purpose:** Persist AI-generated automation suggestions to database for user review

Phase 5b handles suggestion storage:
1. **Store Suggestions** - Persist to SQLite database
2. **Track Status** - Manage lifecycle (pending → deployed)
3. **Link to Patterns** - Connect suggestions to detected patterns
4. **Enable Queries** - Support UI retrieval and filtering
5. **Track Deployment** - Monitor which automations are active

---

## 🔄 Storage Process

```
store_suggestion(db, suggestion) [database/crud.py:180]
├── Create Suggestion object (Story AI1.23 - Conversational Flow):
│   ├── pattern_id = suggestion.get('pattern_id')  # Link to detected pattern
│   ├── title = suggestion['title']  # User-friendly name
│   │
│   ├── # NEW: Description-first fields (Story AI1.23)
│   ├── description_only = suggestion['description']  # Human-readable description (required)
│   ├── conversation_history = []  # Conversation edit history (JSON array)
│   ├── device_capabilities = suggestion.get('device_capabilities', {})  # Cached device features
│   ├── refinement_count = 0  # Number of user edits
│   │
│   ├── # YAML generation (nullable until approved in conversational flow)
│   ├── automation_yaml = suggestion.get('automation_yaml')  # NULL for draft, populated when approved
│   ├── yaml_generated_at = None  # Set when YAML is generated after approval
│   │
│   ├── # Status tracking (updated for conversational flow)
│   ├── status = 'pending'  # Legacy batch flow: pending → deployed/rejected
│   ├──                     # NEW conversational flow: draft → refining → yaml_generated → deployed
│   │
│   ├── # Metadata fields
│   ├── confidence = suggestion['confidence']  # Pattern confidence
│   ├── category = suggestion.get('category')  # energy/comfort/security/convenience
│   ├── priority = suggestion.get('priority')  # high/medium/low
│   │
│   ├── # Timestamps
│   ├── created_at = datetime.now(utc)
│   ├── updated_at = datetime.now(utc)
│   ├── approved_at = None  # NEW: Set when user approves
│   └── deployed_at = None  # Set when deployed to HA
│
├── db.add(suggestion) [line 205]
│   └── Add to SQLAlchemy session (not yet committed)
│
├── db.commit() [line 206]
│   └── Write to SQLite database (suggestions table)
│
├── db.refresh(suggestion) [line 207]
│   └── Reload from DB to get auto-generated ID
│
└── Returns: Suggestion object with id assigned
```

---

## 🗄️ Database Schema

**SQLite Table: `suggestions`** (Updated for Story AI1.23)

```sql
CREATE TABLE suggestions (
    -- Primary Key
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER,  -- Foreign key to patterns.id (nullable for feature-based)
    
    -- Core Fields
    title VARCHAR NOT NULL,
    
    -- NEW: Description-First Fields (Story AI1.23)
    description_only TEXT NOT NULL,  -- Human-readable description (REQUIRED)
    conversation_history JSON,  -- Array of edit history
    device_capabilities JSON,  -- Cached device features for context
    refinement_count INTEGER DEFAULT 0,  -- Number of user refinements
    
    -- YAML Generation (nullable until approved in conversational flow)
    automation_yaml TEXT,  -- NULL for draft, populated after approval (CHANGED: was NOT NULL)
    yaml_generated_at DATETIME,  -- NEW: When YAML was created
    
    -- Status Tracking (updated for conversational flow)
    status VARCHAR DEFAULT 'pending',  -- Legacy: pending → deployed/rejected
                                       -- NEW conversational: draft → refining → yaml_generated → deployed
    
    -- Metadata
    confidence FLOAT NOT NULL,
    category VARCHAR,  -- energy/comfort/security/convenience
    priority VARCHAR,  -- high/medium/low
    
    -- Timestamps
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    approved_at DATETIME,  -- NEW: When user approved
    deployed_at DATETIME,  -- When deployed to HA
    ha_automation_id VARCHAR,  -- HA's ID after deployment
    
    FOREIGN KEY(pattern_id) REFERENCES patterns(id)
);

CREATE INDEX idx_suggestions_status ON suggestions(status);
CREATE INDEX idx_suggestions_created_at ON suggestions(created_at DESC);
```

**Field Details (Updated for Story AI1.23):**

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `id` | INTEGER | Auto-increment primary key | 42 |
| `pattern_id` | INTEGER | Link to pattern (Epic AI-1) or NULL (Epic AI-2) | 17 |
| `title` | VARCHAR | User-friendly name | "Living Room Light Morning Routine" |
| **`description_only`** | **TEXT** | **Human-readable description (REQUIRED)** | "Turn on living room lights at 7:15 AM on weekdays..." |
| **`conversation_history`** | **JSON** | **Conversation edit history** | `[{"user": "make it 7:30", "timestamp": "..."}]` |
| **`device_capabilities`** | **JSON** | **Cached device features for context** | `{"light.living_room": {"brightness": true}}` |
| **`refinement_count`** | **INTEGER** | **Number of user refinements** | 3 |
| `automation_yaml` | TEXT | Deployable HA YAML (NULLABLE until approved) | `alias: "Morning Lights"\ntrigger:...` or NULL |
| **`yaml_generated_at`** | **DATETIME** | **When YAML was generated** | "2025-10-17T09:15:00Z" |
| `status` | VARCHAR | Lifecycle state (see updated flow below) | "draft" → "refining" → "yaml_generated" → "deployed" |
| `confidence` | FLOAT | Pattern confidence | 0.87 |
| `category` | VARCHAR | Suggestion type | "convenience" |
| `priority` | VARCHAR | Importance level | "medium" |
| `created_at` | DATETIME | When generated | "2025-10-17T03:05:23Z" |
| `updated_at` | DATETIME | Last modified | "2025-10-17T09:15:00Z" |
| **`approved_at`** | **DATETIME** | **When user approved** | "2025-10-17T09:10:00Z" |
| `deployed_at` | DATETIME | When deployed to HA | "2025-10-17T10:00:00Z" |
| `ha_automation_id` | VARCHAR | HA automation ID | "automation.morning_lights" |

**Bold fields** = NEW in Story AI1.23 (Conversational Suggestion Refinement)

---

## 🔄 Status Lifecycle

Suggestions now support **TWO flows**:

### Legacy Flow (Pattern-Based Daily Analysis)

```
       ┌─────────┐
       │ pending │  ← Created by AI (3 AM daily run) with full YAML
       └────┬────┘
            │
            ├──────────────┐
            ▼              ▼
       ┌─────────┐    ┌──────────┐
       │deployed │    │ rejected │  ← User decision (immediate)
       └─────────┘    └──────────┘
```

### NEW Conversational Flow (Story AI1.23)

```
       ┌───────┐
       │ draft │  ← Created from NL request (description only, NO YAML yet)
       └───┬───┘
           │
           ▼
       ┌──────────┐
       │ refining │  ← User iterates with natural language edits
       └─────┬────┘    (max 10 refinements, tracked in conversation_history)
             │
             ├─────────────┐
             ▼             ▼
    ┌────────────────┐  ┌──────────┐
    │ yaml_generated │  │ rejected │  ← User approves or rejects
    └────────┬───────┘  └──────────┘
             │
             ▼
        ┌─────────┐
        │deployed │  ← YAML generated and deployed to HA
        └─────────┘
```

### Status Definitions

1. **pending** (Legacy Flow Only)
   - Created during Phase 5 of daily analysis
   - Includes full automation_yaml from start
   - Ready for immediate deployment
   - Awaiting user review

2. **draft** (NEW - Conversational Flow Only)
   - Created from natural language request
   - `description_only` populated, `automation_yaml` is NULL
   - User can refine with natural language
   - First step in conversational refinement

3. **refining** (NEW - Conversational Flow Only)
   - User is actively editing with natural language
   - `refinement_count` increments with each edit
   - `conversation_history` tracks all changes
   - Max 10 refinements allowed
   - Still NO automation_yaml (only description)

4. **yaml_generated** (NEW - Conversational Flow Only)
   - User approved the description
   - System generates automation_yaml from final description
   - `yaml_generated_at` timestamp set
   - `approved_at` timestamp set
   - Ready for deployment

5. **deployed** (Both Flows)
   - Successfully deployed to Home Assistant
   - `deployed_at` timestamp set
   - `ha_automation_id` populated
   - Automation is now active

6. **rejected** (Both Flows)
   - User rejected the suggestion
   - Not shown in active suggestions
   - Kept for analytics/learning
   - Can occur at any stage

---

## 📝 Storage Examples

### Example 1: Pattern-Based Suggestion (Epic AI-1)

**Input Data:**
```python
suggestion_data = {
    'type': 'pattern_automation',
    'source': 'Epic-AI-1',
    'pattern_id': 42,  # Links to detected pattern
    'pattern_type': 'time_of_day',
    'title': 'Living Room Light Morning Routine',
    'description': 'Turn on living room lights at 7:15 AM on weekdays based on consistent usage pattern detected over 30 days',
    'automation_yaml': '''alias: "Living Room Light Morning Routine"
description: "Automatically turn on living room lights at 7:15 AM on weekdays"
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
mode: single''',
    'confidence': 0.87,
    'category': 'convenience',
    'priority': 'medium',
    'rationale': 'Detected consistent pattern: light.living_room turns on at 7:15 AM (±10 min) on weekdays with 87% regularity over the past 30 days. High confidence automation candidate.'
}
```

**Database Record:**
```json
{
  "id": 123,
  "pattern_id": 42,
  "title": "Living Room Light Morning Routine",
  "description": "Turn on living room lights at 7:15 AM on weekdays...",
  "automation_yaml": "alias: \"Living Room Light Morning Routine\"...",
  "status": "pending",
  "confidence": 0.87,
  "category": "convenience",
  "priority": "medium",
  "created_at": "2025-10-17T03:05:23Z",
  "updated_at": "2025-10-17T03:05:23Z",
  "deployed_at": null,
  "ha_automation_id": null
}
```

### Example 2: Feature-Based Suggestion (Epic AI-2)

**Input Data:**
```python
suggestion_data = {
    'type': 'feature_automation',
    'source': 'Epic-AI-2',
    'pattern_id': None,  # No pattern - based on capability analysis
    'device_id': 'light.kitchen_switch',
    'device_model': 'VZM31-SN',
    'feature_name': 'led_notifications',
    'title': 'Garage Door LED Notification',
    'description': 'Flash kitchen switch LED red when garage door is left open for 10 minutes',
    'automation_yaml': '''alias: "Garage Door LED Notification"
description: "Visual notification using kitchen switch LED"
trigger:
  - platform: state
    entity_id: cover.garage_door
    to: "open"
    for:
      minutes: 10
action:
  - service: mqtt.publish
    data:
      topic: "zigbee2mqtt/kitchen_switch/set"
      payload: '{"led_effect": "Fast Blink", "led_color": "Red"}'
mode: single''',
    'confidence': 0.75,  # Lower confidence (opportunity-based, not pattern)
    'category': 'security',
    'priority': 'high',
    'rationale': 'Device has unused LED notification capability (led_effect). Kitchen is high-traffic area. Garage security is important.'
}
```

**Database Record:**
```json
{
  "id": 124,
  "pattern_id": null,  // No pattern - feature-based
  "title": "Garage Door LED Notification",
  "status": "pending",
  "confidence": 0.75,
  "category": "security",
  "priority": "high",
  ...
}
```

---

## 🔍 Querying Suggestions

**Common Query Patterns:**

**1. Get Pending Suggestions for UI:**
```python
# GET /api/suggestions?status=pending
suggestions = await get_suggestions(db, status='pending', limit=50)
```

**2. Get Recent Suggestions:**
```python
# Ordered by created_at DESC (newest first)
recent = await get_suggestions(db, status=None, limit=10)
```

**3. Get High-Confidence Suggestions:**
```python
# Custom query in crud.py
query = select(Suggestion).where(
    Suggestion.confidence >= 0.8,
    Suggestion.status == 'pending'
).order_by(Suggestion.confidence.desc())
```

**4. Get Suggestions by Category:**
```python
# Energy-saving suggestions
energy_suggestions = await db.execute(
    select(Suggestion).where(
        Suggestion.category == 'energy',
        Suggestion.status == 'pending'
    )
)
```

---

## 🔗 Relationship to Patterns

**Pattern-Based Suggestions (Epic AI-1):**
```sql
-- Get suggestion with its pattern
SELECT 
    s.*,
    p.pattern_type,
    p.device_id,
    p.occurrences
FROM suggestions s
JOIN patterns p ON s.pattern_id = p.id
WHERE s.id = 123;
```

**Feature-Based Suggestions (Epic AI-2):**
```sql
-- Feature-based suggestions have no pattern
SELECT * FROM suggestions
WHERE pattern_id IS NULL;  -- Epic AI-2 suggestions
```

**Why `pattern_id` is Nullable:**
- Epic AI-1: Pattern-driven → `pattern_id` populated
- Epic AI-2: Capability-driven → `pattern_id` is NULL
- Allows unified suggestion storage for both approaches

---

## 📊 Batch Storage Performance

**Typical Daily Run:**

```python
# Phase 5 generates 10 suggestions (top ranked)
all_suggestions = [
    pattern_suggestion_1,  # confidence: 0.92
    pattern_suggestion_2,  # confidence: 0.87
    feature_suggestion_1,  # confidence: 0.81
    pattern_suggestion_3,  # confidence: 0.78
    feature_suggestion_2,  # confidence: 0.75
    ...  # 5 more
]

suggestions_stored = 0
for suggestion in all_suggestions:
    try:
        async with get_db_session() as db:
            await store_suggestion(db, suggestion)
        suggestions_stored += 1
    except Exception as e:
        logger.error(f"Failed to store suggestion: {e}")
        # Continue with next suggestion
```

**Performance:**
- ~50ms per suggestion (SQLite insert + commit)
- 10 suggestions: ~500ms total
- Parallel storage possible but not implemented (sequential is fast enough)

**Error Handling:**
- Individual suggestion failures don't block others
- Failed suggestions logged but job continues
- User sees partial results (e.g., 8/10 suggestions stored)

---

## 👤 User Feedback Integration

**Related Table: `user_feedback`**

When user approves/rejects a suggestion:

```python
# User clicks "Approve" in UI
feedback = await store_feedback(db, {
    'suggestion_id': 123,
    'action': 'approved',
    'feedback_text': 'Great suggestion! I always do this manually.'
})

# Update suggestion status
suggestion.status = 'approved'
suggestion.updated_at = datetime.now(timezone.utc)
await db.commit()
```

**Feedback Tracking:**
```sql
SELECT 
    s.title,
    s.confidence,
    uf.action,
    uf.feedback_text
FROM suggestions s
JOIN user_feedback uf ON s.id = uf.suggestion_id
WHERE uf.action = 'approved';
```

**Future Enhancement:**
- Use feedback for ML model training
- Learn which suggestions users prefer
- Adjust confidence thresholds based on acceptance rate

---

## 🚀 Deployment Tracking

**When Suggestion is Deployed:**

```python
# POST /api/suggestions/{id}/deploy
suggestion = await db.get(Suggestion, suggestion_id)

# Deploy to Home Assistant
ha_automation_id = await ha_client.create_automation(
    yaml=suggestion.automation_yaml
)

# Update database
suggestion.status = 'deployed'
suggestion.deployed_at = datetime.now(timezone.utc)
suggestion.ha_automation_id = ha_automation_id
suggestion.updated_at = datetime.now(timezone.utc)
await db.commit()
```

**Deployment Verification:**

```sql
-- All deployed automations
SELECT 
    id,
    title,
    ha_automation_id,
    deployed_at
FROM suggestions
WHERE status = 'deployed'
ORDER BY deployed_at DESC;
```

---

## 📈 Analytics & Reporting

**Suggestion Statistics:**

```python
# Get suggestion counts by status
stats = await db.execute(
    select(
        Suggestion.status,
        func.count().label('count')
    ).group_by(Suggestion.status)
)

# Example result:
# {
#   'pending': 15,
#   'approved': 8,
#   'deployed': 23,
#   'rejected': 12
# }
```

**Acceptance Rate:**
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed,
    CAST(SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as acceptance_rate
FROM suggestions;
```

**Category Performance:**
```sql
SELECT 
    category,
    COUNT(*) as total,
    AVG(confidence) as avg_confidence,
    SUM(CASE WHEN status = 'deployed' THEN 1 ELSE 0 END) as deployed_count
FROM suggestions
GROUP BY category
ORDER BY deployed_count DESC;
```

---

## 🧹 Database Maintenance

**Old Suggestions Cleanup:**

```python
# Delete rejected suggestions older than 90 days
async def cleanup_old_suggestions(db: AsyncSession, days: int = 90):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    stmt = delete(Suggestion).where(
        Suggestion.status == 'rejected',
        Suggestion.created_at < cutoff
    )
    result = await db.execute(stmt)
    await db.commit()
    
    logger.info(f"Deleted {result.rowcount} old rejected suggestions")
```

**Database Size Management:**
- Each suggestion: ~2-3 KB (YAML is largest field)
- 100 suggestions: ~250 KB
- SQLite handles 10K+ suggestions easily
- Periodic cleanup keeps database lean

---

## ⚠️ Error Scenarios

**Common Errors:**

1. **Duplicate Suggestion:**
```python
# Same automation generated twice
# Currently allowed (no unique constraint)
# Future: Add unique constraint on (title, automation_yaml hash)
```

2. **Invalid YAML:**
```python
# OpenAI generated invalid YAML
# Caught during validation (Story AI1.19: Safety Validation)
# Suggestion not stored if YAML is invalid
```

3. **Database Lock:**
```python
# SQLite locked by another process
# Retry with exponential backoff
# Log warning if persistent
```

4. **Transaction Rollback:**
```python
try:
    db.add(suggestion)
    await db.commit()
except Exception as e:
    await db.rollback()  # Undo changes
    logger.error(f"Failed to store: {e}")
    raise
```

---

## 🖥️ Integration with UI

**API Endpoints:**

```typescript
// GET /api/suggestions?status=pending&limit=10
const suggestions = await fetch('/api/suggestions?status=pending');

// POST /api/suggestions/{id}/approve
await fetch(`/api/suggestions/${id}/approve`, { method: 'POST' });

// POST /api/suggestions/{id}/deploy
await fetch(`/api/suggestions/${id}/deploy`, { method: 'POST' });

// POST /api/suggestions/{id}/reject
await fetch(`/api/suggestions/${id}/reject`, { 
  method: 'POST',
  body: JSON.stringify({ reason: 'Not useful' })
});
```

**UI Display:**

```tsx
// AI Automation UI component
<SuggestionCard
  id={suggestion.id}
  title={suggestion.title}
  description={suggestion.description}
  confidence={suggestion.confidence}
  category={suggestion.category}
  priority={suggestion.priority}
  yaml={suggestion.automation_yaml}
  onApprove={() => approveSuggestion(suggestion.id)}
  onReject={() => rejectSuggestion(suggestion.id)}
/>
```

---

## 🎯 Phase 5b Output

**Returns:**
```python
{
    'suggestions_stored': 10,
    'storage_time_ms': 485,
    'failed_stores': 0
}
```

**Database State:**
- 10 new records in `suggestions` table
- All with `status='pending'`
- Ready for user review in UI

---

## 🔗 Related Documentation

- [← Phase 5: OpenAI Suggestion Generation](AI_AUTOMATION_PHASE5_OPENAI.md) - Generates suggestions
- [→ Phase 6: MQTT Notification](AI_AUTOMATION_PHASE6_MQTT.md) - Publishes completion
- [Phase 3: Pattern Detection](AI_AUTOMATION_PHASE3_PATTERNS.md) - Provides patterns for AI-1
- [Phase 4: Feature Analysis](AI_AUTOMATION_PHASE4_FEATURES.md) - Provides opportunities for AI-2
- [Back to Index](AI_AUTOMATION_CALL_TREE_INDEX.md)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Story:** AI1.23 - Conversational Suggestion Refinement

