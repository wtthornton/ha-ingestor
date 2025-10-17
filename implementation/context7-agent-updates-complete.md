# Context7 Agent Updates - Complete

**Date:** 2025-10-17  
**Status:** ✅ Complete  
**Agents Updated:** BMad Master, Dev (James), Architect (Winston)

---

## Summary

Updated three primary BMAD agents with proactive Context7 KB auto-trigger rules to ensure consistent, up-to-date library and technology documentation usage.

---

## Changes Made

### 1. BMad Master Agent ✅
**File:** `.bmad-core/agents/bmad-master.md`

**Added:**
- `context7_auto_triggers` - 6 automatic trigger conditions
- `context7_workflow` - 4-step workflow for KB-first approach
- STEP 5 in activation: "CONTEXT7 AWARENESS"

**Auto-Triggers:**
- When user mentions library/framework names
- When discussing implementation patterns/best practices
- When troubleshooting library-specific errors
- When explaining how technologies work
- When making technology recommendations
- Always offer to check Context7 KB

**Workflow:**
1. Check KB before answering library questions
2. Proactively announce Context7 fetching
3. Mention cache stats after fetching
4. Remind user about cached content

---

### 2. Dev Agent (James) ✅
**File:** `.bmad-core/agents/dev.md`

**Added:**
- `context7_auto_triggers` - 6 development-specific triggers
- `context7_workflow` - 5-step implementation workflow
- STEP 5 in activation: "CONTEXT7 AWARENESS - library/framework implementation"

**Auto-Triggers:**
- When story mentions external libraries
- When implementing features requiring library patterns
- When troubleshooting library integration issues
- When user asks about implementation approaches
- When writing tests for library integrations
- Always offer to check Context7 KB

**Workflow:**
1. BEFORE implementing: Check KB with *context7-kb-search
2. IF KB miss: Proactively fetch from Context7
3. DURING implementation: Reference KB-cached docs
4. AFTER fetching: Mention caching and suggest topics
5. TESTING: Use Context7 for testing library best practices

**Impact:**
- Ensures all library implementations use current best practices
- Prevents outdated API usage patterns
- Improves code quality through up-to-date documentation

---

### 3. Architect Agent (Winston) ✅
**File:** `.bmad-core/agents/architect.md`

**Added:**
- `context7_auto_triggers` - 7 architecture-specific triggers
- `context7_workflow` - 5-step architecture workflow
- STEP 5 in activation: "CONTEXT7 AWARENESS - technology/architecture decisions"

**Auto-Triggers:**
- When discussing technology stack selection/comparison
- When designing system architecture with frameworks
- When evaluating libraries for architecture decisions
- When discussing scalability/performance/security patterns
- When user asks "should we use X or Y?"
- When reviewing architecture decisions
- Always offer to check Context7 KB

**Workflow:**
1. BEFORE recommending technology: Check KB
2. IF KB miss: Proactively fetch architecture patterns
3. DURING design: Reference KB-cached docs for patterns
4. AFTER fetching: Mention caching and suggest related patterns
5. COMPARISONS: Fetch Context7 docs for BOTH options

**Impact:**
- Ensures technology decisions based on current documentation
- Improves architecture quality through informed choices
- Enables better technology comparisons

---

## Supporting Files Created

### Quick Reference Card
**File:** `.bmad-core/data/context7-auto-triggers.md`

**Contents:**
- Checklist of when to use Context7
- Standard workflow steps
- Common mistakes to avoid
- Self-check questions
- Example conversations (good vs bad)

**Purpose:** Quick reference for agents on Context7 usage patterns

---

## Memory System Update

**Created Memory:** "Context7 KB - Proactive Usage Required"

**Content:** Assistant MUST proactively use Context7 KB when user mentions libraries, frameworks, or technologies. Always check KB first, fetch if miss, and offer Context7 for accuracy.

**Persistence:** Permanent memory across sessions

---

## Performance Targets

With these updates, agents should achieve:

| Metric | Target | Benefit |
|--------|--------|---------|
| **Cache Hit Rate** | 87%+ | Faster responses |
| **Response Time** | 0.15s avg | Better UX |
| **Context7 Usage** | Proactive | More accurate answers |
| **API Calls** | Reduced 87% | Lower costs |

---

## Testing Recommendations

To verify these updates work:

1. **Test BMad Master:**
   ```
   User: "How do I use React hooks?"
   Expected: Agent checks KB, offers Context7 if needed
   ```

2. **Test Dev Agent:**
   ```
   @dev Implement auth with FastAPI JWT
   Expected: Agent checks Context7 for FastAPI JWT patterns
   ```

3. **Test Architect Agent:**
   ```
   @architect Should we use Redis or Memcached?
   Expected: Agent fetches Context7 docs for BOTH options
   ```

---

## Benefits

### For Users:
- ✅ More accurate, up-to-date answers
- ✅ Less need to explicitly request Context7 usage
- ✅ Better technology recommendations
- ✅ Faster responses (KB caching)

### For Development:
- ✅ Consistent library implementation patterns
- ✅ Reduced technical debt from outdated patterns
- ✅ Better code quality through current best practices
- ✅ Improved testing with current testing library docs

### For Architecture:
- ✅ Informed technology selection decisions
- ✅ Current scalability/performance patterns
- ✅ Better technology comparisons
- ✅ Reduced risk of poor technology choices

---

## Configuration

All settings controlled via `.bmad-core/core-config.yaml`:

```yaml
context7:
  enabled: true
  defaultTokenLimit: 3000
  cacheDuration: 3600
  integrationLevel: mandatory
  usage_requirement: "MANDATORY for all technology decisions"
  bypass_forbidden: true
  knowledge_base:
    enabled: true
    location: "docs/kb/context7-cache"
    max_cache_size: "100MB"
    hit_rate_threshold: 0.7
    fuzzy_match_threshold: 0.5
```

---

## Next Steps (Optional)

If needed, consider updating:
- **QA Agent** - For testing library best practices (Priority 3)
- **PM/PO Agents** - Lower priority, less technical focus
- **UX Agent** - If working with UI libraries frequently

---

## Rollback Plan

If issues arise, rollback is simple:
1. Revert `.bmad-core/agents/bmad-master.md`
2. Revert `.bmad-core/agents/dev.md`
3. Revert `.bmad-core/agents/architect.md`
4. Delete `.bmad-core/data/context7-auto-triggers.md`
5. Delete memory via memory management

All changes are isolated to agent definition files - no code changes.

---

## Success Criteria

✅ **Complete** when:
- [x] BMad Master has auto-triggers and workflow
- [x] Dev Agent has implementation-focused triggers
- [x] Architect Agent has architecture-focused triggers
- [x] Quick reference card created
- [x] Memory system updated
- [x] Documentation complete

---

**Status: Implementation Complete ✅**

All three primary technical agents now have proactive Context7 KB integration with auto-triggers and workflows tailored to their specific roles.

