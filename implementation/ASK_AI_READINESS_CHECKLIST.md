# Ask AI Tab - Readiness Checklist & Preparation
**Date:** October 19, 2025  
**Status:** Pre-Implementation (Waiting for Story AI1.24 completion)  
**Assumption:** Story AI1.24 will be completed by another developer first

---

## 📋 **Prerequisites from Story AI1.24**

### **Must-Have Completions (Blocking)**

Before starting Ask AI implementation, verify these are **100% complete**:

#### **1. Frontend Cleanup ✅**
- [ ] Old `Dashboard.tsx` deleted
- [ ] `ConversationalDashboard.tsx` is at root route (`/`)
- [ ] App.tsx routes updated
- [ ] Navigation component updated
- [ ] No references to old Dashboard anywhere

**Verification Command:**
```bash
# Search for any references to old Dashboard
grep -r "Dashboard" services/ai-automation-ui/src/ --exclude-dir=node_modules
# Should only find ConversationalDashboard references
```

#### **2. Backend Description-First Flow ✅**
- [ ] Daily analysis generates description-only (no YAML)
- [ ] `automation_yaml = NULL` for draft suggestions
- [ ] YAML only generated via `/approve` endpoint
- [ ] All suggestions created with `status='draft'`

**Verification:**
```bash
# Check a recent suggestion from database
# Should have: status='draft', automation_yaml=NULL, description_only populated
```

**SQL Query to Verify:**
```sql
-- Check recent suggestions have correct structure
SELECT id, status, 
       CASE WHEN automation_yaml IS NULL THEN 'NULL' ELSE 'HAS_YAML' END as yaml_status,
       CASE WHEN description_only IS NOT NULL THEN 'HAS_DESC' ELSE 'NULL' END as desc_status,
       created_at
FROM suggestions 
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC 
LIMIT 10;

-- Expected: status='draft', yaml_status='NULL', desc_status='HAS_DESC'
```

#### **3. Database Migration Complete ✅**
- [ ] Migration script created and applied
- [ ] All legacy `status='pending'` converted to `status='draft'`
- [ ] All draft suggestions have `automation_yaml=NULL`

**Verification:**
```sql
-- Should return 0 rows
SELECT COUNT(*) FROM suggestions WHERE status = 'pending';

-- Should return count of all suggestions that need cleanup
SELECT COUNT(*) FROM suggestions 
WHERE status = 'draft' AND automation_yaml IS NOT NULL;
-- Expected: 0
```

#### **4. API Endpoints Working ✅**
- [ ] POST `/api/v1/suggestions/generate` returns description-only
- [ ] POST `/api/v1/suggestions/{id}/refine` works
- [ ] POST `/api/v1/suggestions/{id}/approve` generates YAML
- [ ] GET `/api/v1/suggestions/devices/{id}/capabilities` works

**Verification:**
```bash
# Test suggestion generation (should return description, no YAML)
curl -X POST http://localhost:8018/api/v1/suggestions/generate \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": 1,
    "pattern_type": "time_of_day",
    "device_id": "light.office",
    "metadata": {"hour": 18, "confidence": 0.85}
  }'

# Expected response: automation_yaml should be null
```

#### **5. Component Availability ✅**
- [ ] `ConversationalSuggestionCard.tsx` exists and works
- [ ] `CustomToast.tsx` exists
- [ ] `api.ts` has methods: `refineSuggestion`, `approveAndGenerateYAML`, `getDeviceCapabilities`
- [ ] Zustand store (`store.ts`) exists

**Verification:**
```bash
# Check files exist
ls -la services/ai-automation-ui/src/components/ConversationalSuggestionCard.tsx
ls -la services/ai-automation-ui/src/components/CustomToast.tsx
ls -la services/ai-automation-ui/src/services/api.ts
ls -la services/ai-automation-ui/src/store.ts
```

---

## 🔍 **Pre-Implementation Checklist**

### **Phase 1: Verification (Before Starting)**

#### **Verify Story AI1.24 Completion**
- [ ] Ask other developer: "Is Story AI1.24 100% complete?"
- [ ] Review all completed tasks in story-ai1-24-conversational-ui-cleanup.md
- [ ] Run smoke tests on ConversationalDashboard
- [ ] Verify no failing tests in AI automation service

#### **Verify Running System**
- [ ] AI automation service running (http://localhost:8018)
- [ ] AI automation UI running (http://localhost:3001)
- [ ] ConversationalDashboard accessible at http://localhost:3001/
- [ ] Backend generating suggestions successfully
- [ ] No critical errors in logs

**Quick Test:**
```bash
# Check services are up
curl http://localhost:8018/health
curl http://localhost:3001/

# Check suggestions API
curl http://localhost:8018/api/v1/suggestions/list?limit=5
```

#### **Review Current Codebase**
- [ ] Read `ConversationalDashboard.tsx` (understand current implementation)
- [ ] Read `ConversationalSuggestionCard.tsx` (component we'll reuse)
- [ ] Read `api.ts` (API methods available)
- [ ] Read `conversational_router.py` (backend endpoints)
- [ ] Read `openai_client.py` (LLM integration)

**Files to Review:**
```
services/ai-automation-ui/src/
├── pages/ConversationalDashboard.tsx         (~300 lines)
├── components/ConversationalSuggestionCard.tsx (~440 lines)
├── services/api.ts                           (~370 lines)
└── store.ts                                  (~200 lines)

services/ai-automation-service/src/
├── api/conversational_router.py              (~673 lines)
├── llm/openai_client.py                      (~500 lines)
└── clients/ha_client.py                      (~304 lines)
```

---

## 📦 **Dependencies & Resources Needed**

### **1. Access to Home Assistant**
- [ ] Verify HA URL: `http://192.168.1.86:8123`
- [ ] Verify HA token is set in environment
- [ ] Test HA Conversation API access

**Test HA Conversation API:**
```bash
# Test if HA Conversation API is accessible
curl -X POST http://192.168.1.86:8123/api/conversation/process \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "turn on office lights", "language": "en"}'

# Expected: JSON response with conversation result
```

### **2. OpenAI API Key**
- [ ] Verify OpenAI API key is set (`OPENAI_API_KEY`)
- [ ] Check current usage/limits
- [ ] Confirm GPT-4o-mini model access

**Verify:**
```bash
# Check environment variable is set
echo $OPENAI_API_KEY  # Should output key (masked)

# Test OpenAI access (from ai-automation-service)
# Already working if Story AI1.24 is complete
```

### **3. Development Environment**
- [ ] Node.js 20+ installed
- [ ] Python 3.11+ installed
- [ ] Docker running (for services)
- [ ] Git configured

### **4. Documentation Access**
- [ ] Access to design specs:
  - `implementation/ASK_AI_TAB_DESIGN_SPECIFICATION.md`
  - `implementation/ASK_AI_ARCHITECTURE_REVIEW_AND_HA_INTEGRATION.md`
- [ ] Access to Hugging Face datasets documentation
- [ ] Context7 KB documentation cached

---

## 🛠️ **Preparation Tasks (Do These Before Starting)**

### **Task 1: Create Feature Branch**
```bash
# Don't run yet - just documenting
git checkout -b feature/ask-ai-tab
git push -u origin feature/ask-ai-tab
```

### **Task 2: Document Current API Surface**
**Create file:** `implementation/ASK_AI_CURRENT_API_REFERENCE.md`

**Content to document:**
- List all available endpoints from `conversational_router.py`
- List all available methods from `api.ts`
- Note any limitations or quirks
- Document request/response formats

### **Task 3: Create Mock Data for Testing**
**Create file:** `services/ai-automation-service/tests/fixtures/ask_ai_fixtures.py`

**Mock data needed:**
- Sample user queries
- Expected NLP parsing results
- Sample pattern search results
- Sample suggestion responses

### **Task 4: Set Up Test Environment**
**Checklist:**
- [ ] Create test database snapshot
- [ ] Prepare test devices/entities
- [ ] Create test patterns
- [ ] Document test scenarios

### **Task 5: Review Type Definitions**
**File to check:** `services/ai-automation-ui/src/types/index.ts`

**Verify types exist for:**
- `Suggestion` (with all new fields)
- `Pattern`
- `Device`
- Any conversational-specific types

**If missing, note what needs to be added:**
```typescript
// New types we'll need for Ask AI:
interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    suggestions?: Suggestion[];
    follow_up_prompts?: string[];
  };
}

interface UserContext {
  devices: {
    total: number;
    by_domain: { [domain: string]: number };
    recently_mentioned: string[];
  };
  integrations: {
    sports_tracking: string[];
    energy_pricing: boolean;
    weather: boolean;
  };
  automations: {
    total: number;
  };
  suggested_prompts: string[];
}

interface AskAIResponse {
  response_type: 'text' | 'suggestions' | 'clarification';
  message: string;
  suggestions?: Suggestion[];
  follow_up_prompts?: string[];
  context_used: {
    devices_detected: string[];
    triggers_detected: string[];
    conditions_detected: string[];
  };
  metadata: {
    query_id: string;
    processing_time_ms: number;
    confidence: number;
  };
}
```

---

## 📝 **Questions for Other Developer (Story AI1.24)**

### **Critical Questions:**

1. **Backend Behavior:**
   - Q: "Does daily analysis now generate description-only (no YAML)?"
   - Q: "Are all new suggestions created with `status='draft'`?"
   - Q: "Does `/approve` endpoint generate YAML correctly?"

2. **Database State:**
   - Q: "Did the migration run successfully?"
   - Q: "Are there any legacy `status='pending'` suggestions left?"
   - Q: "Can I see a sample suggestion from the database?"

3. **Frontend State:**
   - Q: "Is ConversationalDashboard working at root route `/`?"
   - Q: "Are there any known issues or bugs?"
   - Q: "Did you keep `SuggestionCard.tsx` or delete it?"

4. **Testing:**
   - Q: "What tests did you add/update?"
   - Q: "Are all tests passing?"
   - Q: "Any edge cases I should know about?"

5. **Breaking Changes:**
   - Q: "Did you change any API contracts?"
   - Q: "Did you modify the `Suggestion` type?"
   - Q: "Any new environment variables needed?"

---

## 🚨 **Potential Issues to Check**

### **Issue 1: API Contract Changes**
**Risk:** Story AI1.24 might have changed API responses

**Check:**
```bash
# Compare API responses before/after AI1.24
# Document any differences
```

**Mitigation:** Review API documentation, update our code accordingly

### **Issue 2: Zustand Store Changes**
**Risk:** Store structure might have changed

**Check:**
```typescript
// Review store.ts for any breaking changes
// Check if state shape changed
```

**Mitigation:** Align our new state additions with current structure

### **Issue 3: Component Prop Changes**
**Risk:** ConversationalSuggestionCard props might have changed

**Check:**
```typescript
// Review ConversationalSuggestionCard.tsx interface
interface Props {
  suggestion: ConversationalSuggestion;
  onRefine: (id: number, userInput: string) => Promise<void>;
  onApprove: (id: number) => Promise<void>;
  onReject: (id: number) => Promise<void>;
  darkMode?: boolean;
}
// Verify this matches our expectations
```

**Mitigation:** Update our design to match current props

### **Issue 4: Build/Deployment Changes**
**Risk:** Docker configs or build scripts might have changed

**Check:**
```bash
# Review docker-compose.yml
# Review package.json scripts
# Review environment variables
```

**Mitigation:** Update our deployment plan accordingly

---

## 📊 **Implementation Readiness Scorecard**

### **Before Starting, Verify All Are ✅:**

| Category | Item | Status | Blocker? |
|----------|------|--------|----------|
| **Story AI1.24** | Frontend cleanup complete | ⬜ | ✅ YES |
| **Story AI1.24** | Backend cleanup complete | ⬜ | ✅ YES |
| **Story AI1.24** | Database migration complete | ⬜ | ✅ YES |
| **Story AI1.24** | All tests passing | ⬜ | ✅ YES |
| **Environment** | HA Conversation API accessible | ⬜ | ⚠️ OPTIONAL |
| **Environment** | OpenAI API key configured | ⬜ | ✅ YES |
| **Environment** | All services running | ⬜ | ✅ YES |
| **Documentation** | Design specs reviewed | ⬜ | ⚠️ RECOMMENDED |
| **Documentation** | Current codebase reviewed | ⬜ | ⚠️ RECOMMENDED |
| **Preparation** | Feature branch created | ⬜ | ⚠️ RECOMMENDED |
| **Preparation** | Test fixtures prepared | ⬜ | ⚠️ OPTIONAL |

**Legend:**
- ✅ **YES** = Blocks implementation
- ⚠️ **RECOMMENDED** = Should do before starting
- ⚠️ **OPTIONAL** = Nice to have

**Ready to Start When:** All "✅ YES" items are checked ✅

---

## 🎯 **Implementation Order (After Ready)**

### **Phase 1: Backend Foundation (Day 1)**
1. Create `ask_ai_router.py` (stub endpoints)
2. Add HA Conversation API integration to `ha_client.py`
3. Wire router into `main.py`
4. Test endpoints with Postman/curl

### **Phase 2: NLP & RAG Integration (Day 2-3)**
1. Add NLP parsing (HA API + HF fallback)
2. Connect to existing pattern detection engine
3. Connect to existing suggestion generation
4. Test end-to-end query flow

### **Phase 3: Frontend Chat UI (Day 4-6)**
1. Create `AskAI.tsx` page
2. Create chat components (ChatContainer, ChatInput, MessageBubble)
3. Wire up to backend API
4. Reuse ConversationalSuggestionCard

### **Phase 4: Integration & Polish (Day 7-8)**
1. Add navigation route
2. Add context indicator
3. Add suggested prompts
4. Error handling
5. Loading states

### **Phase 5: Testing (Day 9-10)**
1. Unit tests
2. Integration tests
3. E2E tests
4. Manual QA

---

## 📚 **Reference Documents**

### **Design & Architecture:**
- `implementation/ASK_AI_TAB_DESIGN_SPECIFICATION.md` (Full design)
- `implementation/ASK_AI_ARCHITECTURE_REVIEW_AND_HA_INTEGRATION.md` (Code reuse analysis)
- `docs/stories/story-ai1-24-conversational-ui-cleanup.md` (Prerequisite story)

### **Existing Code to Study:**
- `services/ai-automation-ui/src/pages/ConversationalDashboard.tsx`
- `services/ai-automation-ui/src/components/ConversationalSuggestionCard.tsx`
- `services/ai-automation-service/src/api/conversational_router.py`
- `services/ai-automation-service/src/llm/openai_client.py`

### **Related Stories:**
- Story AI1.23: Conversational Suggestion Refinement
- Story AI1.21: Natural Language Generation
- Story AI1.11: Deployment Integration

---

## ✅ **Final Pre-Flight Checklist**

**Before saying "I'm ready to start":**

- [ ] Story AI1.24 confirmed 100% complete by other developer
- [ ] All services running and healthy
- [ ] ConversationalDashboard working at root route
- [ ] Backend generating description-only suggestions
- [ ] Database in clean state (no legacy statuses)
- [ ] All prerequisite APIs working and tested
- [ ] Feature branch created
- [ ] Design documents reviewed
- [ ] Current codebase studied
- [ ] Test environment prepared
- [ ] Questions to other developer asked and answered
- [ ] No blocking issues identified
- [ ] Ready to commit ~2 weeks of development time

---

## 🚀 **When Ready to Start**

**Notify user:** "Story AI1.24 verification complete. Ready to begin Ask AI implementation."

**First command will be:**
```bash
git checkout -b feature/ask-ai-tab
```

**First file to create:**
```
services/ai-automation-service/src/api/ask_ai_router.py
```

---

**Current Status:** ⏸️ **WAITING FOR STORY AI1.24 COMPLETION**  
**Estimated Start Date:** TBD (after AI1.24 done)  
**Estimated Duration:** 2 weeks (10 days)  
**Estimated Completion:** TBD + 2 weeks

---

**Prepared by:** BMad Master  
**Date:** October 19, 2025  
**Next Review:** After Story AI1.24 completion

