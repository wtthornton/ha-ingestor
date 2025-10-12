<!-- Powered by BMAD™ Core -->

# Implement Hybrid Auto-Refresh Task

## Task Overview
**Task:** Implement Hybrid Auto-Refresh (Level 1 + Level 2)  
**Effort:** 2 hours  
**Complexity:** LOW  
**Value:** HIGH  

## Objective
Implement automatic KB cache refresh using hybrid approach:
- Level 1: Auto-process queue on agent startup
- Level 2: Auto-check staleness on first KB access in session

## Prerequisites
- ✅ Manual refresh system implemented
- ✅ Task files created (context7-kb-refresh.md, etc.)
- ✅ All agents updated with refresh commands
- ✅ Configuration updated with refresh settings

## Tasks

### Task 1: Create Silent Queue Processor
**File:** `.bmad-core/tasks/context7-kb-refresh.md`  
**Action:** Add silent processing function  
**Estimated Time:** 15 minutes

```python
def process_queue_silently() -> int:
    """Process queue without verbose output - for startup use"""
    import os
    
    queue = get_refresh_queue()
    if not queue:
        return 0
    
    success_count = 0
    for item in queue:
        try:
            # Fetch and update silently
            docs = fetch_from_context7(item['library'], item['topic'])
            update_cache(item['library'], item['topic'], docs)
            update_last_checked(item['library'])
            success_count += 1
        except Exception:
            # Continue processing, don't fail entire queue
            pass
    
    clear_refresh_queue()
    return success_count
```

**Acceptance:**
- [ ] Function added to context7-kb-refresh.md
- [ ] Returns count of processed items
- [ ] No verbose output (silent)
- [ ] Clears queue after processing

---

### Task 2: Create Session Tracking
**File:** `.bmad-core/tasks/context7-kb-lookup.md`  
**Action:** Add session tracking and first-access check  
**Estimated Time:** 30 minutes

```python
# Add to top of KB lookup implementation
_SESSION_KB_CHECKED = False

def auto_check_and_queue_stale():
    """Check all libraries and queue stale ones - runs once per session"""
    stale_libs = []
    
    for lib in list_cached_libraries():
        if is_cache_stale(lib):
            stale_libs.append({
                'name': lib,
                'age_days': get_cache_age(lib)
            })
            queue_refresh(lib, 'all')
    
    return stale_libs

def kb_lookup_enhanced(library, topic):
    """Enhanced KB lookup with session checking"""
    global _SESSION_KB_CHECKED
    
    # First KB access in this session
    if not _SESSION_KB_CHECKED:
        _SESSION_KB_CHECKED = True
        
        stale_libs = auto_check_and_queue_stale()
        
        if stale_libs:
            print(f"📋 KB Status: {len(stale_libs)} libraries need refresh")
            for lib in stale_libs[:3]:  # Show max 3
                print(f"   ⚠️  {lib['name']} ({lib['age_days']} days old)")
            if len(stale_libs) > 3:
                print(f"   ... and {len(stale_libs) - 3} more")
            print(f"💡 Queued for refresh on next agent startup\n")
    
    # Normal KB lookup
    return standard_kb_lookup(library, topic)
```

**Acceptance:**
- [ ] Session tracking variable added
- [ ] auto_check_and_queue_stale() function created
- [ ] kb_lookup_enhanced() function created
- [ ] User notification implemented
- [ ] Only runs once per session

---

### Task 3: Update Agent Activations (All 9 Agents)
**Files:** `.bmad-core/agents/*.md` (9 files)  
**Action:** Add startup queue processing  
**Estimated Time:** 45 minutes

**For each agent, add to activation-instructions:**

```yaml
activation-instructions:
  - STEP 3c: Auto-process KB refresh queue (if enabled)
    ```
    config = load_core_config()
    if config.context7.knowledge_base.refresh.auto_process_on_startup:
        import os
        queue_file = 'docs/kb/context7-cache/.refresh-queue'
        if os.path.exists(queue_file):
            from tasks import process_queue_silently
            count = process_queue_silently()
            if count > 0:
                print(f"🔄 Processed {count} KB refresh(es)")
    ```
```

**Agents to update:**
1. [ ] bmad-master.md
2. [ ] dev.md
3. [ ] architect.md
4. [ ] qa.md
5. [ ] ux-expert.md
6. [ ] pm.md
7. [ ] analyst.md
8. [ ] po.md
9. [ ] sm.md

**Acceptance:**
- [ ] All 9 agents have startup queue processing
- [ ] Only runs if config.auto_process_on_startup: true
- [ ] Shows brief success message
- [ ] Silent if queue empty

---

### Task 4: Update KB Lookup Task
**File:** `.bmad-core/tasks/context7-kb-lookup.md`  
**Action:** Replace standard lookup with enhanced version  
**Estimated Time:** 15 minutes

**Update the main KB lookup workflow to use enhanced version:**

```yaml
kb_lookup:
  steps:
    - name: "session_check_and_queue"
      enabled_if: "config.auto_check_on_first_access"
      action: "run_session_check"
      function: "auto_check_and_queue_stale"
      timing: "first_access_only"
    
    - name: "check_kb_cache"
      action: "lookup_in_kb"
      # ... existing logic
```

**Acceptance:**
- [ ] KB lookup uses enhanced version
- [ ] Session check runs on first access
- [ ] Config flag checked before running
- [ ] Backward compatible with manual mode

---

### Task 5: Update Configuration Flags
**File:** `.bmad-core/core-config.yaml`  
**Action:** Already done! Just verify  
**Estimated Time:** 5 minutes

**Verify these settings exist:**
```yaml
context7:
  knowledge_base:
    refresh:
      enabled: true
      auto_process_on_startup: true
      auto_check_on_first_access: true
      notify_stale: true
```

**Acceptance:**
- [ ] Config flags present
- [ ] Flags default to true
- [ ] Can be disabled by user

---

### Task 6: Test Hybrid Behavior
**Action:** Test the complete hybrid workflow  
**Estimated Time:** 20 minutes

**Test Scenarios:**

1. **Test Startup Processing**
   - [ ] Create test queue file
   - [ ] Start agent
   - [ ] Verify queue processed
   - [ ] Verify success message shown

2. **Test First-Access Check**
   - [ ] Mark a library as stale (set old date)
   - [ ] Access KB for different library
   - [ ] Verify stale detection runs
   - [ ] Verify user notification shown
   - [ ] Verify stale item queued

3. **Test Second Access (No Re-Check)**
   - [ ] Access KB again in same session
   - [ ] Verify no re-check happens
   - [ ] Verify normal lookup behavior

4. **Test Next Startup**
   - [ ] Restart agent
   - [ ] Verify queued items processed
   - [ ] Verify cache updated

**Acceptance:**
- [ ] All test scenarios pass
- [ ] No blocking behavior (except startup)
- [ ] Clear user feedback
- [ ] No errors or warnings

---

### Task 7: Document Hybrid Behavior
**File:** `docs/kb/context7-cache/AUTO_REFRESH_QUICK_START.md`  
**Action:** Update with hybrid behavior  
**Estimated Time:** 10 minutes

**Add section:**
```markdown
## 🤖 Automatic Refresh (Hybrid Mode)

### How It Works Automatically

**On Agent Startup:**
- ✅ Auto-processes any queued refreshes (2-5s)
- ✅ Shows brief message: "🔄 Processed 2 KB refresh(es)"

**On First KB Access:**
- ✅ Auto-checks all cache for staleness (500ms)
- ✅ Auto-queues stale items
- ✅ Notifies you what's queued

**On Next Startup:**
- ✅ Processes the queue automatically
- ✅ Cache is now fresh!

### You Still Can Manually
- `*context7-kb-refresh --check-only` - Check anytime
- `*context7-kb-refresh` - Force refresh now
- `*context7-kb-process-queue` - Process queue now

### Disable Automation
Edit `.bmad-core/core-config.yaml`:
```yaml
auto_process_on_startup: false
auto_check_on_first_access: false
```
```

**Acceptance:**
- [ ] Documentation updated
- [ ] Hybrid behavior explained
- [ ] Manual override documented
- [ ] Disable instructions included

---

## Success Criteria

- [ ] Silent queue processor implemented
- [ ] Session tracking implemented
- [ ] All 9 agents updated with startup logic
- [ ] KB lookup enhanced with session check
- [ ] All tests pass
- [ ] Documentation complete
- [ ] No over-engineering
- [ ] User experience is smooth

## Rollback Plan

If hybrid approach causes issues:
```yaml
# Disable in core-config.yaml
auto_process_on_startup: false
auto_check_on_first_access: false
```

System falls back to manual mode immediately.

## Implementation Order

1. ✅ Create silent processor (15 min)
2. ✅ Add session tracking (30 min)
3. ✅ Update all 9 agents (45 min)
4. ✅ Enhance KB lookup (15 min)
5. ✅ Test all scenarios (20 min)
6. ✅ Update documentation (10 min)

**Total:** 2 hours 15 minutes

## Notes

- Keep it simple - no threads, no daemons
- Clear user notifications
- Non-blocking (except brief startup)
- Easy to disable
- Backward compatible

