<!-- Powered by BMAD™ Core -->

# Context7 KB Refresh Check Command

## Command
`*context7-kb-refresh` or `*context7-kb-refresh --check-only`

## Purpose
Check and refresh stale Context7 KB cache entries. Simple manual control over cache freshness.

## Usage

### Check Only (No Refresh)
```bash
*context7-kb-refresh --check-only
```

### Refresh All Stale Entries
```bash
*context7-kb-refresh
```

## Implementation Workflow

### Step 1: List All Cached Libraries
```
1. Read docs/kb/context7-cache/libraries/ directory
2. For each subdirectory, collect library name
3. Return list of libraries
```

### Step 2: Check Staleness for Each
```
For each library:
1. Read meta.yaml file
2. Check last_checked timestamp
3. Get max_age_days from refresh_policy
4. Calculate age in days
5. If age > max_age_days, mark as stale
```

### Step 3: Display Results
```
For check-only mode:
- Show all libraries with age
- Highlight stale entries
- Show summary count

For refresh mode:
- Show stale entries
- Fetch new docs from Context7
- Update cache files
- Update last_checked timestamp
- Show success/failure for each
```

## Output Format

### Check-Only Mode
```
🔍 Checking for stale cache entries...

📚 Cached Libraries Status:
  ✅ playwright - 7 days old (max: 14 days) - FRESH
  ⚠️  vitest - 35 days old (max: 14 days) - STALE
  ⚠️  pytest - 42 days old (max: 30 days) - STALE

📊 Summary:
  Total: 3 libraries
  Fresh: 1 (33%)
  Stale: 2 (67%)
  
💡 Run *context7-kb-refresh to update stale entries
```

### Refresh Mode
```
🔄 Refreshing stale cache entries...

Found 2 stale entries:
  ⚠️  vitest - 35 days old
  ⚠️  pytest - 42 days old

Refreshing vitest...
  📄 Calling Context7 API...
  ✅ Retrieved 1183 code snippets
  💾 Updated cache file (28.1 KB)
  🕒 Updated last_checked timestamp
  ✅ vitest refreshed successfully

Refreshing pytest...
  📄 Calling Context7 API...
  ✅ Retrieved 614 code snippets
  💾 Updated cache file (52.3 KB)
  🕒 Updated last_checked timestamp
  ✅ pytest refreshed successfully

✅ Refresh complete!
  Refreshed: 2 libraries
  Failed: 0
  Time: 5.2 seconds
```

## Error Handling

### Context7 API Unavailable
```
❌ Error refreshing vitest: Context7 API unavailable
💡 Library queued for later refresh
ℹ️  Run *context7-kb-process-queue when API is available
```

### Permission Error
```
❌ Error: Cannot write to cache directory
💡 Check file permissions for docs/kb/context7-cache/
```

### Invalid Meta File
```
⚠️  Warning: Invalid meta.yaml for library 'react'
💡 Skipping this library
```

## Dependencies
- context7-kb-refresh.md (helper functions)
- Context7 MCP tools (for fetching docs)
- File system access (read/write)

## Notes
- Manual command - user controls when to refresh
- Simple, non-blocking operation
- Clear feedback on what's happening
- Graceful error handling
- No complex background processing

