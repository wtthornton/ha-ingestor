# BMAD Core Optimization - Testing Quick Start

## ✅ Implementation Complete - Ready for Testing

**Status**: All 16 files updated successfully  
**Date**: October 12, 2025

---

## Quick Test Commands

### Test 1: Agent Startup with Document Loading

```bash
# Test @bmad-master startup
@bmad-master

# Expected: Should load tech-stack.md, source-tree.md, coding-standards.md
# Look for: References to project structure in greeting/context
```

### Test 2: Architect Agent Context

```bash
# Test @architect startup
@architect

# Expected: Should load tech-stack.md, source-tree.md, coding-standards.md
# Look for: Technology knowledge in responses
```

### Test 3: Create Document Task

```bash
@bmad-master
*create-doc

# Select any template
# Expected: Should reference project context section
# Look for: Mentions of tech-stack.md, source-tree.md
```

### Test 4: Story Creation

```bash
@po (or @pm)
*create-story

# Expected: Should load architecture docs
# Look for: Accurate dev notes with project-specific context
```

---

## What Changed - Quick Reference

### Core Config (.bmad-core/core-config.yaml)
✅ Added `agentLoadAlwaysFiles` section  
✅ Configured 5 agents with startup documents

### Agents (4 files)
✅ architect.md - loads 3 docs on startup  
✅ pm.md - loads 2 docs on startup  
✅ qa.md - loads 3 docs on startup  
✅ bmad-master.md - loads 3 docs on startup

### Tasks (8 files)
✅ create-doc.md - project context references  
✅ document-project.md - doc location hints  
✅ brownfield-create-story.md - architecture refs  
✅ brownfield-create-epic.md - technical context  
✅ review-story.md - quality standards  
✅ test-design.md - testing framework refs  
✅ apply-qa-fixes.md - standards reference  
✅ validate-next-story.md - validation context

### Templates (3 files)
✅ story-tmpl.yaml - doc references in dev-notes  
✅ brownfield-prd-tmpl.yaml - tech-stack ref  
✅ brownfield-architecture-tmpl.yaml - existing docs

---

## Success Indicators

### ✅ Good Signs
- Agents reference project structure without asking
- Technology decisions align with tech-stack.md
- Fewer clarification questions about project layout
- Story dev-notes contain accurate tech context

### ❌ Problem Signs
- Agents still asking "What's your tech stack?"
- Generic technology recommendations
- Invented file paths that don't match source-tree.md
- Agents not loading documents on startup

---

## Quick Validation Checklist

- [ ] @bmad-master activates and shows project awareness
- [ ] @architect shows tech-stack knowledge
- [ ] @pm shows project structure knowledge  
- [ ] @qa shows testing standards knowledge
- [ ] *create-doc shows project context section
- [ ] Story creation includes accurate dev notes
- [ ] No performance degradation on startup

---

## Expected Performance

### Metrics to Track
1. **Startup Time**: Should be <5 seconds (vs 15-20s repeated loading)
2. **Clarification Requests**: 2-3 per session (vs 6-8 before)
3. **Context Awareness**: Agents should know tech stack immediately
4. **Accuracy**: Technology decisions match project standards

### How to Measure
1. **Time startup**: Note when agent greeting appears
2. **Count questions**: How many times agent asks about structure/tech
3. **Check accuracy**: Do recommendations match tech-stack.md?
4. **User experience**: Fewer "that's not right" corrections?

---

## If Something Breaks

### Rollback Instructions

```bash
# Option 1: Revert specific phase
git log --oneline | grep "Phase [1-4]"
git revert <commit-hash>

# Option 2: Full rollback
git revert HEAD~4..HEAD

# Option 3: Selective file revert
git checkout HEAD~4 -- .bmad-core/core-config.yaml
```

### Most Likely Issues

**Issue**: Agent doesn't load docs on startup  
**Fix**: Check core-config.yaml syntax (YAML formatting)

**Issue**: Agent loads wrong docs  
**Fix**: Verify agentLoadAlwaysFiles.{agent-id} matches agent name

**Issue**: Doc paths not found  
**Fix**: Verify docs/architecture/ folder exists with files

**Issue**: Performance degradation  
**Fix**: Reduce docs in agentLoadAlwaysFiles (remove source-tree.md)

---

## Next Steps After Testing

1. ✅ **If working well**: Monitor for 1 week, collect metrics
2. ⚠️ **If issues found**: Document issues, adjust configuration
3. 📊 **After 1 week**: Review metrics, compare to baseline
4. 🔄 **After 1 month**: Assess ROI, make final adjustments

---

## Files to Monitor

### Config Files
- `.bmad-core/core-config.yaml` - Agent doc loading config

### Agent Files
- `.bmad-core/agents/architect.md`
- `.bmad-core/agents/pm.md`
- `.bmad-core/agents/qa.md`
- `.bmad-core/agents/bmad-master.md`

### Key Task Files
- `.bmad-core/tasks/create-doc.md`
- `.bmad-core/tasks/brownfield-create-story.md`

### Template Files
- `.bmad-core/templates/story-tmpl.yaml`

---

## Support Resources

**Implementation Plan**: `implementation/bmad-core-document-links-optimization-plan.md`  
**Implementation Summary**: `implementation/bmad-core-optimization-implementation-summary.md`  
**This File**: `implementation/TESTING-QUICK-START.md`

---

**Quick Start Version**: 1.0  
**Last Updated**: 2025-10-12  
**Status**: Ready for Testing

