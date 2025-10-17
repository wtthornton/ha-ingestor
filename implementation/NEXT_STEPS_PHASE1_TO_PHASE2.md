# Next Steps: Phase 1 → Phase 2 Transition

**Story:** AI1.23 - Conversational Suggestion Refinement  
**Current Status:** ✅ Phase 1 Complete  
**Next Phase:** Phase 2 - Description-Only Generation  
**Date:** October 17, 2025

---

## 🎯 Quick Start: Testing Phase 1

Before moving to Phase 2, let's verify Phase 1 is working:

### **1. Reset Database (3 minutes)**
```bash
cd ~/ha-ingestor

# Stop service
docker-compose stop ai-automation-service

# Run reset script
cd services/ai-automation-service
python scripts/alpha_reset_database.py
# Type: yes

# Expected output:
# ✅ Database deleted
# ✅ Database created successfully
# ✅ Schema validation passed

# Restart service
cd ~/ha-ingestor
docker-compose up -d ai-automation-service

# Watch startup
docker-compose logs -f ai-automation-service
# Wait for: "Starting server on 0.0.0.0:8018"
```

### **2. Test API Endpoints (2 minutes)**
```bash
# Health check
curl http://localhost:8018/api/v1/suggestions/health
# Expected: {"status":"healthy","message":"Conversational suggestion router (Phase 1: Stubs)","phase":"1-mock-data"}

# Test mock generate endpoint
curl -X POST http://localhost:8018/api/v1/suggestions/generate \
  -H "Content-Type: application/json" \
  -d '{"pattern_id":123,"pattern_type":"time_of_day","device_id":"light.living_room","metadata":{}}' | jq

# Test mock refine endpoint
curl -X POST http://localhost:8018/api/v1/suggestions/test-123/refine \
  -H "Content-Type: application/json" \
  -d '{"user_input":"Make it blue"}' | jq

# Test mock capabilities endpoint
curl http://localhost:8018/api/v1/suggestions/devices/light.living_room/capabilities | jq
```

### **3. View Swagger Docs (1 minute)**
Open in browser: http://localhost:8018/docs

**Expected:**
- ✅ Tag "Conversational Suggestions" visible
- ✅ 6 new endpoints listed
- ✅ Can test endpoints in browser
- ✅ Mock responses work

### **4. Run Reprocessing (Optional - 2 minutes)**
```bash
cd services/ai-automation-service

# Only if you have patterns detected
python scripts/reprocess_patterns.py

# Expected:
# ✅ Deleted N old suggestions
# ✅ Created M new suggestions  
# ✅ All in 'draft' status
```

**Total Testing Time: ~10 minutes**

---

## 📋 Phase 1 Completion Checklist

Before moving to Phase 2, verify:

- [ ] ✅ Database reset script runs without errors
- [ ] ✅ Service starts successfully after reset
- [ ] ✅ All 6 API endpoints return mock data
- [ ] ✅ Swagger docs show new "Conversational Suggestions" tag
- [ ] ✅ `Suggestion` model has all new fields (verify in logs or DB)
- [ ] ✅ Reprocessing script completes successfully
- [ ] ✅ No Python import errors in logs
- [ ] ✅ No TypeScript/lint errors in modified files

**If all checked:** ✅ **Ready for Phase 2**

---

## 🚀 Phase 2 Overview: Description-Only Generation

**Goal:** Replace placeholder descriptions with real OpenAI-generated descriptions

**Timeline:** 5 days (Week 2)

**What We'll Build:**
1. `DescriptionGenerator` class with OpenAI integration
2. Three separate prompt templates (description, refinement, YAML)
3. Device capability fetching from data-api
4. Real description generation in reprocessing script
5. Updated `/generate` endpoint (remove mock data)

---

## 📝 Phase 2 Implementation Plan

### **Day 1: Description Generator Class**

**File:** `services/ai-automation-service/src/llm/description_generator.py`

**Tasks:**
- [ ] Create `DescriptionGenerator` class
- [ ] Implement description-only prompt template
- [ ] Use temperature 0.7 for natural language
- [ ] Target ~200 tokens per description
- [ ] Track token usage
- [ ] Handle OpenAI errors gracefully

**Pseudocode:**
```python
class DescriptionGenerator:
    async def generate_description(self, pattern: Dict, device_context: Dict) -> str:
        """Generate human-readable description from pattern"""
        prompt = self._build_description_prompt(pattern, device_context)
        
        response = await openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_DESCRIPTION},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
```

**Acceptance:** Description generator returns readable text (no YAML)

---

### **Day 2: Device Capability Fetching**

**File:** `services/ai-automation-service/src/clients/data_api_client.py` (extend existing)

**Tasks:**
- [ ] Add method to fetch device metadata from data-api
- [ ] Parse supported features (brightness, RGB, etc.)
- [ ] Format as friendly capabilities list
- [ ] Cache capabilities (1 hour TTL)
- [ ] Handle data-api connection errors

**New Method:**
```python
async def fetch_device_capabilities(self, device_id: str) -> Dict:
    """Fetch device capabilities from data-api"""
    response = await self.http_client.get(f"/api/devices/{device_id}")
    
    # Parse supported features
    capabilities = {
        "brightness": device.get("attributes", {}).get("brightness") is not None,
        "rgb_color": device.get("attributes", {}).get("rgb_color") is not None,
        # ... more features
    }
    
    return capabilities
```

**Acceptance:** Can fetch and cache device capabilities

---

### **Day 3: Update Reprocessing Script**

**File:** `services/ai-automation-service/scripts/reprocess_patterns.py`

**Tasks:**
- [ ] Replace placeholder descriptions with OpenAI calls
- [ ] Fetch device capabilities for each pattern
- [ ] Cache capabilities in suggestion record
- [ ] Add retry logic for OpenAI failures
- [ ] Log token usage per suggestion
- [ ] Show progress bar for long runs

**Updated Logic:**
```python
async def create_suggestion_from_pattern(pattern: Pattern) -> Suggestion:
    # Fetch device capabilities
    capabilities = await data_api_client.fetch_device_capabilities(pattern.device_id)
    
    # Generate real description via OpenAI
    description = await description_generator.generate_description(
        pattern=pattern_dict,
        device_context={"capabilities": capabilities}
    )
    
    suggestion = Suggestion(
        description_only=description,  # Real OpenAI description!
        device_capabilities=capabilities,  # Cache for later
        # ... rest of fields
    )
    
    return suggestion
```

**Acceptance:** Reprocessing generates real OpenAI descriptions

---

### **Day 4: Update API Endpoint**

**File:** `services/ai-automation-service/src/api/conversational_router.py`

**Tasks:**
- [ ] Remove mock data from `/generate` endpoint
- [ ] Call `DescriptionGenerator` with real pattern
- [ ] Fetch device capabilities
- [ ] Store suggestion in database
- [ ] Return real data instead of mock
- [ ] Add error handling

**Updated Endpoint:**
```python
@router.post("/generate")
async def generate_description_only(request: GenerateRequest, db: AsyncSession):
    # Fetch device capabilities
    capabilities = await data_api_client.fetch_device_capabilities(request.device_id)
    
    # Generate description via OpenAI
    description = await description_generator.generate_description(
        pattern=request.dict(),
        device_context={"capabilities": capabilities}
    )
    
    # Store in database
    suggestion = Suggestion(
        description_only=description,
        device_capabilities=capabilities,
        status="draft",
        # ...
    )
    db.add(suggestion)
    await db.commit()
    
    return suggestion_response
```

**Acceptance:** `/generate` endpoint returns real OpenAI descriptions

---

### **Day 5: Testing & Documentation**

**Tasks:**
- [ ] Write unit tests for `DescriptionGenerator`
- [ ] Write integration tests for `/generate` endpoint
- [ ] Test capability caching
- [ ] Verify token usage tracking
- [ ] Update API documentation
- [ ] Create Phase 2 completion summary

**Test Cases:**
```python
async def test_generate_description_time_of_day():
    """Test description generation for time-of-day pattern"""
    pattern = {"pattern_type": "time_of_day", "hour": 18, "device_id": "light.living_room"}
    description = await generator.generate_description(pattern, {})
    
    assert "living room" in description.lower()
    assert "6" in description or "18" in description
    assert "alias:" not in description  # No YAML!

async def test_capability_caching():
    """Test device capabilities are cached"""
    caps1 = await client.fetch_device_capabilities("light.living_room")
    caps2 = await client.fetch_device_capabilities("light.living_room")
    # Second call should be cached (no API call)
    assert caps1 == caps2
```

**Acceptance:** All tests pass, Phase 2 complete

---

## 📊 Phase 2 Success Metrics

**Code Quality:**
- ✅ Unit test coverage > 80%
- ✅ All API endpoints tested
- ✅ Error handling for OpenAI failures
- ✅ Token usage tracked accurately

**Functionality:**
- ✅ Real OpenAI descriptions generated
- ✅ Device capabilities fetched and cached
- ✅ No placeholder descriptions in output
- ✅ `/generate` endpoint returns real data

**Performance:**
- ✅ Description generation < 2 seconds
- ✅ Capability caching reduces API calls
- ✅ Token usage within expectations (~200 tokens/description)

---

## 💰 Phase 2 Cost Estimates

**OpenAI Usage:**
- Description generation: ~200 tokens per suggestion
- Cost per description: ~$0.00006 (at gpt-4o-mini pricing)
- 100 suggestions: ~$0.006 (less than 1 cent!)

**Monthly Cost (10 new suggestions/day):**
- 300 descriptions/month
- ~$0.018/month ($0.02 rounded)

**Conclusion:** Phase 2 cost is negligible

---

## 🔧 Development Environment Setup

**Before starting Phase 2, ensure:**

```bash
# 1. OpenAI API key is set
echo $OPENAI_API_KEY
# Should output: sk-...

# 2. Data-api is running
curl http://localhost:8006/health
# Expected: {"status":"healthy"}

# 3. ai-automation-service is healthy
curl http://localhost:8018/health
# Expected: {"status":"healthy"}

# 4. Database is initialized
ls services/ai-automation-service/data/ai_automation.db
# Expected: file exists

# 5. Python environment is active
python --version
# Expected: Python 3.11+
```

---

## 📚 Reference Documents

**Phase 1 Completion:**
- `implementation/PHASE1_COMPLETE_CONVERSATIONAL_AUTOMATION.md`

**Full Design:**
- `implementation/CONVERSATIONAL_AUTOMATION_DESIGN.md` (see "Phase 2" section)

**API Contracts:**
- `implementation/CONVERSATIONAL_AUTOMATION_DESIGN.md` (see "API Contracts" section)

**OpenAI Prompts:**
- `implementation/CONVERSATIONAL_AUTOMATION_DESIGN.md` (see "OpenAI Prompt Templates")

**Story:**
- `docs/stories/story-ai1-23-conversational-suggestion-refinement.md`

---

## 🚦 Decision Points for Phase 2

### **Question 1: Fallback Strategy**
**What to do if OpenAI call fails?**

**Options:**
- A. Use placeholder description (current approach)
- B. Retry up to 3 times, then fail gracefully
- C. Queue for later retry

**Recommendation:** Option B (retry then placeholder)

---

### **Question 2: Capability Caching**
**How long to cache device capabilities?**

**Options:**
- A. 1 hour (frequently updated devices)
- B. 24 hours (rarely change)
- C. Per-session (until service restart)

**Recommendation:** Option A (1 hour with refresh)

---

### **Question 3: Token Limit**
**What if description exceeds 200 tokens?**

**Options:**
- A. Truncate at 200 tokens
- B. Use higher limit (300 tokens)
- C. Retry with more concise prompt

**Recommendation:** Option B (increase to 300 tokens)

---

## ✅ Phase 2 Readiness Checklist

Before starting implementation:

- [ ] Phase 1 tested and working
- [ ] OpenAI API key configured
- [ ] Data-api responding
- [ ] Design document reviewed
- [ ] Prompt templates drafted
- [ ] Test strategy defined
- [ ] Time allocated (5 days)

**When all checked:** ✅ **Start Phase 2!**

---

## 🎯 Phase 2 Deliverables

At the end of Phase 2, we will have:

1. ✅ `DescriptionGenerator` class with OpenAI integration
2. ✅ Device capability fetching and caching
3. ✅ Real OpenAI descriptions (no placeholders)
4. ✅ Updated reprocessing script with OpenAI
5. ✅ Updated `/generate` endpoint (real data)
6. ✅ Unit and integration tests
7. ✅ Phase 2 completion documentation

**Overall Progress:** 40% complete (2/5 phases)

---

## 🤝 Need Help?

**Phase 2 Questions:**
- Review design doc: `implementation/CONVERSATIONAL_AUTOMATION_DESIGN.md`
- Check story: `docs/stories/story-ai1-23-conversational-suggestion-refinement.md`
- Test checklist: `implementation/ALPHA_RESET_CHECKLIST.md`

**Ready to start Phase 2?** Follow the Day 1-5 plan above!

---

**Phase 1:** ✅ COMPLETE  
**Phase 2:** 🚀 READY TO START  
**Timeline:** 5 days  
**Let's build it!** 🎉

