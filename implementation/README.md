# Implementation Folder

## Purpose

This folder contains **implementation notes, status reports, and session artifacts** created during the development process. These are NOT permanent documentation.

## What Goes Here

### Status & Completion Reports
- `*_COMPLETE.md` - Epic/story completion reports
- `*_STATUS.md` - Current status updates
- `DEPLOYMENT_COMPLETE.md` - Deployment status
- `EPIC_*_COMPLETE.md` - Epic completion reports

### Session Summaries
- `SESSION_*.md` - Development session summaries
- `*_SUMMARY.md` - Implementation summaries
- Progress reports and session notes

### Implementation Plans & Reports
- `*_PLAN.md` - Implementation plans
- `*_IMPLEMENTATION_*.md` - Implementation details
- `*_FIX_*.md` - Fix reports
- `*_FIXES_SUMMARY.md` - Fix summaries

### Subdirectories

#### `analysis/`
Technical analysis and diagnosis reports:
- `*_ANALYSIS.md` - System/API analysis
- `*_DIAGNOSIS.md` - Problem diagnosis
- `*_CALL_TREE.md` - Code flow analysis

#### `verification/`
Test and verification results:
- `*_VERIFICATION_RESULTS.md` - Test results
- `*_VERIFICATION.md` - Verification reports

#### `archive/`
Old/superseded implementation notes:
- Organized by date or epic
- Moved here when no longer active

## What Does NOT Go Here

### Permanent Documentation → `docs/`
- Architecture documentation
- PRD and user stories
- User manuals and guides
- API documentation
- Deployment guides (how-to)
- Troubleshooting guides

### Configuration → Root
- README.md (project overview)
- package.json, docker-compose.yml
- Environment files (.env*)

## File Organization Rules

### Creating New Files

**BEFORE creating a file, ask:**
1. Is this a temporary status/progress report? → `implementation/`
2. Is this a technical analysis? → `implementation/analysis/`
3. Is this test/verification results? → `implementation/verification/`
4. Is this permanent reference documentation? → `docs/`
5. Is this project configuration? → Root

**When in doubt:** Place in `implementation/` rather than root or `docs/`

### Lifecycle Management

1. **Active Development**: Files in main `implementation/` folder
2. **Epic Complete**: Move epic-specific files to `archive/epic-X/`
3. **Project Complete**: Archive all or clean up old artifacts
4. **Duplicates**: Keep most recent, archive others

## Examples

### Correct Placement ✅
```
implementation/
├── EPIC_17_COMPLETE.md
├── DEPLOYMENT_COMPLETE.md
├── SESSION_COMPLETE_EPIC_14_AND_15.md
├── analysis/
│   ├── API_DATA_SOURCE_ANALYSIS.md
│   └── DATA_FLOW_CALL_TREE.md
└── verification/
    └── GUI_VERIFICATION_RESULTS.md
```

### Incorrect Placement ❌
```
# Don't put these at root!
API_DATA_SOURCE_ANALYSIS.md         # → implementation/analysis/
DEPLOYMENT_COMPLETE.md              # → implementation/
GUI_VERIFICATION_RESULTS.md         # → implementation/verification/

# Don't put these in docs/!
docs/DEPLOYMENT_COMPLETE.md         # → implementation/
docs/EPIC_17_COMPLETE.md            # → implementation/
docs/SESSION_SUMMARY.md             # → implementation/
```

## Maintenance

### Regular Cleanup
- **Weekly**: Review active files
- **After Epic**: Archive epic-specific files
- **Monthly**: Clean up duplicates
- **Quarterly**: Archive completed work

### Archiving Strategy
```bash
# Move completed epic files
mkdir -p archive/epic-17
mv EPIC_17_*.md archive/epic-17/

# Move old session notes
mkdir -p archive/2025-10
mv SESSION_COMPLETE_*.md archive/2025-10/
```

## Related Documentation

- [Project Structure Rules](../.cursor/rules/project-structure.mdc) - Complete file organization rules
- [Documentation Standards](../.cursor/rules/documentation-standards.mdc) - Documentation guidelines
- [Source Tree](../docs/architecture/source-tree.md) - Full project structure

## For AI Agents

**MANDATORY RULES:**
1. NEVER create .md files at project root (except README.md)
2. ALWAYS place status/summary files in `implementation/`
3. ALWAYS place analysis in `implementation/analysis/`
4. ALWAYS place verification in `implementation/verification/`
5. ONLY place permanent reference docs in `docs/`

**Decision Tree:**
```
Creating a new .md file?
├─ Is it README.md? → Root (ONLY exception)
├─ Is it a status/completion report? → implementation/
├─ Is it a session summary? → implementation/
├─ Is it a fix/enhancement report? → implementation/
├─ Is it analysis/diagnosis? → implementation/analysis/
├─ Is it verification results? → implementation/verification/
├─ Is it an implementation plan? → implementation/
├─ Is it a reference guide/manual? → docs/
└─ When in doubt → implementation/ (NOT root, NOT docs/)
```

---

**Last Updated**: October 13, 2025  
**Maintained By**: Development Team

