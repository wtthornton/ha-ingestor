# Alpha Reset Checklist - Conversational Automation System

**Date:** October 17, 2025  
**Status:** 🔬 **ALPHA** - Ready to Execute  
**Full Design:** [CONVERSATIONAL_AUTOMATION_DESIGN.md](./CONVERSATIONAL_AUTOMATION_DESIGN.md)

---

## ⚠️ CRITICAL: This Will Delete All Suggestions

This checklist will:
- ❌ **Delete ALL existing automation suggestions**
- ❌ **Drop the `automation_suggestions` table**
- ✅ **Recreate with new conversational schema**
- ✅ **Reprocess patterns to generate fresh suggestions**

**This is OK because we're in Alpha!**

---

## Pre-Flight Checklist

Before you start, verify:

- [ ] ✅ We're in **Alpha** (no production users)
- [ ] ✅ All developers are aware suggestions will be deleted
- [ ] ✅ No critical testing in progress on existing suggestions
- [ ] ✅ Code changes are committed to git
- [ ] ✅ You have database access (psql)
- [ ] ✅ You can rebuild Docker images

---

## Step-by-Step Execution

### **Step 1: Backup (Optional)**

```bash
# Optional: Backup existing suggestions for reference
cd ~/homeiq
pg_dump -h localhost -U postgres -d ai_automation -t automation_suggestions > backup/suggestions_pre_conversational_$(date +%Y%m%d).sql

# Verify backup created
ls -lh backup/suggestions_pre_conversational_*.sql
```

---

### **Step 2: Stop AI Automation Service**

```bash
# Stop the service to prevent conflicts
docker-compose stop ai-automation-service

# Verify it's stopped
docker-compose ps ai-automation-service
# Should show: State = Exit
```

---

### **Step 3: Run Alpha Reset SQL**

```bash
# Navigate to service directory
cd services/ai-automation-service

# Run the reset script (to be created in Phase 1)
psql -h localhost -U postgres -d ai_automation -f sql/alpha_reset_suggestions.sql

# Expected output:
# DELETE 15           (or however many suggestions existed)
# DROP TABLE
# CREATE TABLE
# CREATE INDEX
# CREATE INDEX
# CREATE INDEX
```

---

### **Step 4: Verify New Schema**

```bash
# Check table structure
psql -h localhost -U postgres -d ai_automation -c "\d automation_suggestions"

# Should show NEW columns:
# - description_only (text, not null)
# - conversation_history (jsonb)
# - device_capabilities (jsonb)
# - refinement_count (integer)
# - status (varchar)
# - yaml_generated_at (timestamp)
```

**Expected Schema:**
```
                                   Table "public.automation_suggestions"
        Column         |            Type             | Collation | Nullable |      Default      
-----------------------+-----------------------------+-----------+----------+-------------------
 id                    | character varying(50)       |           | not null | 
 pattern_id            | character varying(50)       |           | not null | 
 description_only      | text                        |           | not null | 
 conversation_history  | jsonb                       |           |          | '[]'::jsonb
 device_capabilities   | jsonb                       |           |          | '{}'::jsonb
 refinement_count      | integer                     |           |          | 0
 automation_yaml       | text                        |           |          | 
 yaml_generated_at     | timestamp without time zone |           |          | 
 status                | character varying(50)       |           |          | 'draft'::character varying
 title                 | character varying(255)      |           |          | 
 category              | character varying(50)       |           |          | 
 priority              | character varying(50)       |           |          | 
 confidence            | double precision            |           |          | 
 created_at            | timestamp without time zone |           |          | now()
 updated_at            | timestamp without time zone |           |          | now()
 approved_at           | timestamp without time zone |           |          | 
 deployed_at           | timestamp without time zone |           |          | 
Indexes:
    "automation_suggestions_pkey" PRIMARY KEY, btree (id)
    "idx_suggestions_created" btree (created_at DESC)
    "idx_suggestions_pattern" btree (pattern_id)
    "idx_suggestions_status" btree (status)
Foreign-key constraints:
    "automation_suggestions_pattern_id_fkey" FOREIGN KEY (pattern_id) REFERENCES patterns(id) ON DELETE CASCADE
```

---

### **Step 5: Deploy Updated Code**

```bash
# Navigate back to root
cd ~/homeiq

# Pull latest changes (if from git)
git pull origin feature/conversational-suggestions

# Rebuild AI automation service with new models
docker-compose build ai-automation-service

# Start the service
docker-compose up -d ai-automation-service

# Watch logs for startup
docker-compose logs -f ai-automation-service

# Expected in logs:
# ✅ Database connection established
# ✅ Models loaded successfully
# ✅ API server started on port 8018
```

---

### **Step 6: Verify Service Health**

```bash
# Check service health
curl http://localhost:8018/health

# Expected response:
# {"status": "healthy", "database": "connected"}

# Check API endpoints exist
curl http://localhost:8018/api/v1/suggestions

# Expected response (empty array):
# {"suggestions": [], "total": 0}
```

---

### **Step 7: Reprocess Patterns**

```bash
# Run reprocessing script (to be created in Phase 1)
docker-compose exec ai-automation-service python scripts/reprocess_patterns.py

# Expected output:
# 🔄 Reprocessing patterns...
# 📊 Found 8 patterns to process
# ✅ [1/8] Generated suggestion for pattern-123: "Living Room Motion Lighting"
# ✅ [2/8] Generated suggestion for pattern-124: "Coffee Maker Auto-Off"
# ...
# ✅ Successfully created 8 new suggestions in 12.3 seconds
```

---

### **Step 8: Verify New Suggestions**

```bash
# Check suggestions were created
curl http://localhost:8018/api/v1/suggestions | jq '.'

# Expected response (example):
{
  "suggestions": [
    {
      "id": "suggestion-new-1",
      "status": "draft",
      "description_only": "When motion is detected in the Living Room after 6PM, turn on the Living Room Light to 50% brightness",
      "refinement_count": 0,
      "confidence": 0.89,
      "automation_yaml": null,
      "created_at": "2025-10-17T20:15:00Z"
    },
    {
      "id": "suggestion-new-2",
      "status": "draft",
      "description_only": "Turn off the Coffee Maker automatically at 10 AM every weekday",
      "refinement_count": 0,
      "confidence": 0.92,
      "automation_yaml": null,
      "created_at": "2025-10-17T20:15:01Z"
    }
  ],
  "total": 2
}

# Verify status distribution
curl http://localhost:8018/api/v1/suggestions | jq '.suggestions | group_by(.status) | map({status: .[0].status, count: length})'

# Expected:
# [
#   {"status": "draft", "count": 8}
# ]
```

---

### **Step 9: Test Frontend**

```bash
# Open AI Automation UI
open http://localhost:3001/suggestions

# Expected to see:
# ✅ Suggestions tab shows new suggestions
# ✅ Descriptions are visible (no YAML shown)
# ✅ "Edit" button present
# ✅ "Approve" button present
# ✅ Device capabilities section exists
```

---

### **Step 10: Smoke Test Refinement API**

```bash
# Get first suggestion ID
SUGGESTION_ID=$(curl -s http://localhost:8018/api/v1/suggestions | jq -r '.suggestions[0].id')

echo "Testing with suggestion: $SUGGESTION_ID"

# Test refinement endpoint (this will make an OpenAI call)
curl -X POST http://localhost:8018/api/v1/suggestions/$SUGGESTION_ID/refine \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Make it blue"}' \
  | jq '.'

# Expected response:
{
  "suggestion_id": "suggestion-new-1",
  "updated_description": "When motion is detected in the Living Room after 6PM, turn on the Living Room Light to blue",
  "changes_detected": [
    "Added color: blue (RGB supported ✓)"
  ],
  "validation": {
    "ok": true,
    "messages": ["✓ Device supports RGB color"]
  },
  "confidence": 0.92,
  "refinement_count": 1,
  "status": "refining"
}
```

---

## Post-Reset Verification

Check all these are working:

- [ ] ✅ Service health endpoint returns 200
- [ ] ✅ Suggestions list endpoint returns new suggestions
- [ ] ✅ All suggestions have `status: "draft"`
- [ ] ✅ All suggestions have `description_only` field populated
- [ ] ✅ All suggestions have `automation_yaml: null`
- [ ] ✅ Device capabilities are cached in suggestions
- [ ] ✅ Refinement endpoint works (makes OpenAI call)
- [ ] ✅ Frontend shows new UI (no YAML visible by default)
- [ ] ✅ Edit mode opens with natural language input
- [ ] ✅ Approve button exists but doesn't deploy yet (Phase 4)

---

## Troubleshooting

### **Problem: SQL script fails with "table does not exist"**

**Solution:** Table might already be dropped. That's OK, just continue.

```bash
# Check if table exists
psql -h localhost -U postgres -d ai_automation -c "\dt automation_suggestions"

# If it doesn't exist, just run the CREATE TABLE part
psql -h localhost -U postgres -d ai_automation -c "CREATE TABLE automation_suggestions (...);"
```

---

### **Problem: Service won't start after deploy**

**Solution:** Check logs for model errors.

```bash
# Check logs
docker-compose logs ai-automation-service | tail -50

# Common issues:
# - Missing column in model -> Update SQLAlchemy model
# - Migration conflict -> Drop alembic_version table (Alpha only!)
# - Import error -> Rebuild image with --no-cache
```

---

### **Problem: Reprocessing script fails**

**Solution:** Check if patterns exist.

```bash
# Check patterns table
psql -h localhost -U postgres -d ai_automation -c "SELECT COUNT(*) FROM patterns;"

# If no patterns exist, run pattern detection first
docker-compose exec ai-automation-service python scripts/detect_patterns.py
```

---

### **Problem: Refinement API returns 500**

**Solution:** Check OpenAI API key and logs.

```bash
# Verify OpenAI key is set
docker-compose exec ai-automation-service env | grep OPENAI

# Check logs for OpenAI errors
docker-compose logs ai-automation-service | grep -i openai

# Test OpenAI directly (if key is valid)
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Rollback Plan (If Needed)

If something goes wrong, you can restore from backup:

```bash
# Stop service
docker-compose stop ai-automation-service

# Drop new table
psql -h localhost -U postgres -d ai_automation -c "DROP TABLE IF EXISTS automation_suggestions CASCADE;"

# Restore from backup
psql -h localhost -U postgres -d ai_automation < backup/suggestions_pre_conversational_*.sql

# Restart with old code
git checkout main
docker-compose up -d --build ai-automation-service
```

---

## Success Criteria

You're ready to proceed with development when:

- ✅ All 10 steps completed without errors
- ✅ New suggestions generated with `status: "draft"`
- ✅ Refinement API returns valid responses
- ✅ Frontend shows description-first UI
- ✅ No YAML visible until approval
- ✅ OpenAI integration working (refinement makes API calls)

---

## Next Steps After Reset

Once reset is complete, proceed with implementation:

1. **Phase 2:** Complete `DescriptionGenerator` class
2. **Phase 3:** Build `SuggestionRefiner` with validation
3. **Phase 4:** Implement `YAMLGenerator` on approval
4. **Phase 5:** Polish frontend UI

**Timeline:** 5 weeks to production-ready conversational system

---

## Questions?

- **Full design:** [CONVERSATIONAL_AUTOMATION_DESIGN.md](./CONVERSATIONAL_AUTOMATION_DESIGN.md)
- **Summary:** [CONVERSATIONAL_AUTOMATION_SUMMARY.md](./CONVERSATIONAL_AUTOMATION_SUMMARY.md)
- **Implementation phases:** See design doc Section "Implementation Strategy"

**Ready to execute? Follow steps 1-10 above!** ✅

