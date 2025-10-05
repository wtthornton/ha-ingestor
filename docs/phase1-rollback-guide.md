# Phase 1 Context7 Integration Rollback Guide

## Overview
This guide provides step-by-step instructions for rolling back the Phase 1 Context7 integration changes if needed.

## Rollback Process

### Step 1: Remove Context7 Awareness from Agent Personas

#### Architect Agent (.cursor/rules/bmad/architect.mdc)
**Remove this line from core_principles:**
```yaml
- Context7 Integration Awareness - Leverage Context7 MCP tools for up-to-date technology documentation and best practices when making architectural decisions
```

#### Dev Agent (.cursor/rules/bmad/dev.mdc)
**Remove this line from core_principles:**
```yaml
- Context7 Integration Awareness - Leverage Context7 MCP tools for up-to-date library documentation and implementation best practices when working with external libraries or technologies
```

#### QA Agent (.cursor/rules/bmad/qa.mdc)
**Remove this line from core_principles:**
```yaml
- Context7 Integration Awareness - Leverage Context7 MCP tools for up-to-date testing and security documentation when assessing library-related risks and quality concerns
```

### Step 2: Revert Template Changes

#### Architecture Template (.bmad-core/templates/architecture-tmpl.yaml)
**Revert this line in architectural patterns section:**
```yaml
# FROM:
2. **Use Context7 MCP tools (mcp_Context7_resolve-library-id, mcp_Context7_get-library-docs) to get up-to-date documentation for technology decisions when making architectural choices**

# TO:
2. **Use Context7 MCP tools (mcp_Context7_resolve-library-id, mcp_Context7_get-library-docs) to get up-to-date documentation for technology decisions**
```

#### PRD Template (.bmad-core/templates/prd-tmpl.yaml)
**Revert this line in UI/UX goals section:**
```yaml
# FROM:
2. **Use Context7 MCP tools (mcp_Context7_resolve-library-id, mcp_Context7_get-library-docs) to get up-to-date documentation for UI/UX technology decisions when making framework and library choices**

# TO:
2. **Use Context7 MCP tools (mcp_Context7_resolve-library-id, mcp_Context7_get-library-docs) to get up-to-date documentation for UI/UX technology decisions**
```

#### Story Template (.bmad-core/templates/story-tmpl.yaml)
**Revert this line in story definition section:**
```yaml
# FROM:
instruction: Define the user story using the standard format with role, action, and benefit. **Use Context7 MCP tools (mcp_Context7_resolve-library-id, mcp_Context7_get-library-docs) to get up-to-date documentation when stories involve external libraries or technologies that require implementation guidance.**

# TO:
instruction: Define the user story using the standard format with role, action, and benefit. **Use Context7 MCP tools (mcp_Context7_resolve-library-id, mcp_Context7_get-library-docs) to get up-to-date documentation when stories involve external libraries or technologies.**
```

### Step 3: Remove Test Files
**Delete these files:**
- `docs/phase1-test-context7-awareness.md`
- `docs/phase1-rollback-guide.md`

## Rollback Validation

### Pre-Rollback Checklist
- [ ] Identify reason for rollback
- [ ] Document any issues encountered
- [ ] Backup current state if needed for analysis

### Post-Rollback Validation
- [ ] All agent personas reverted to original state
- [ ] All templates reverted to original state
- [ ] Test files removed
- [ ] No linting errors in reverted files
- [ ] BMAD functionality works as before Phase 1

### Rollback Commands
```bash
# Verify no linting errors after rollback
# (Run linting on modified files)

# Test agent activation
# (Test each agent to ensure they work normally)

# Test template functionality  
# (Test template creation to ensure no issues)
```

## Rollback Time Estimate
- **Total Time**: 5-10 minutes
- **Complexity**: Very Low
- **Risk**: Minimal (no system changes were made)

## Notes
- Rollback is trivial because Phase 1 made no system changes
- Only text additions were made to existing files
- No new commands, dependencies, or system modifications
- Original BMAD functionality remains completely intact
- Rollback can be performed by any team member with file edit access

## Alternative: Partial Rollback
If only specific agents or templates need to be reverted, you can roll back individual components rather than the entire Phase 1 implementation.

## Recovery
If rollback was performed in error, simply re-apply the Phase 1 changes using the same process that was originally used.
