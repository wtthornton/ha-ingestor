<!-- Powered by BMAD™ Core -->

# Context7 KB Process Queue Command

## Command
`*context7-kb-process-queue`

## Purpose
Process queued refresh requests that were deferred during normal operations (e.g., when cache was stale but user didn't want to wait).

## Usage
```bash
*context7-kb-process-queue
```

## How Queue Gets Populated

### Automatic Queuing
When user accesses stale cache during normal `*context7-docs` lookup:
```
1. User requests docs: *context7-docs vitest coverage
2. System checks cache: Found (but 35 days old)
3. System returns cached docs immediately (don't block user)
4. System adds to queue: vitest queued for refresh
5. User continues working with cached docs
```

### Manual Queuing
User can also explicitly queue items:
```bash
# View queue status
*context7-kb-queue-status

# Add to queue manually
*context7-kb-queue-add vitest
```

## Queue File Format

Simple text file: `docs/kb/context7-cache/.refresh-queue`

```
vitest,all,2025-10-12T14:30:00Z
pytest,fixtures,2025-10-12T14:45:00Z
react,hooks,2025-10-12T15:00:00Z
```

Format: `library,topic,queued_timestamp`

## Implementation Workflow

### Step 1: Read Queue
```
1. Check if .refresh-queue file exists
2. If not, display "Queue is empty" and exit
3. If exists, parse each line
4. Extract library, topic, timestamp
5. Return list of queued items
```

### Step 2: Process Each Item
```
For each queued item:
1. Display processing message
2. Call Context7 API to fetch docs
3. Update cache files
4. Update last_checked timestamp
5. Log success or failure
```

### Step 3: Clear Queue
```
1. If all items processed successfully:
   - Delete .refresh-queue file
   - Display success message
2. If some failed:
   - Rewrite queue with only failed items
   - Display partial success message
```

## Output Format

### Empty Queue
```
📭 Refresh queue is empty
ℹ️  No pending refresh requests
```

### Processing Queue
```
🔄 Processing refresh queue...

Queue contains 3 items:
  1. vitest/all (queued 2 hours ago)
  2. pytest/fixtures (queued 5 minutes ago)
  3. react/hooks (queued 10 minutes ago)

Processing vitest/all...
  📄 Fetching documentation...
  ✅ Retrieved 1183 code snippets
  💾 Updated cache
  ✅ Success (took 2.1s)

Processing pytest/fixtures...
  📄 Fetching documentation...
  ✅ Retrieved 614 code snippets
  💾 Updated cache
  ✅ Success (took 1.8s)

Processing react/hooks...
  📄 Fetching documentation...
  ❌ Failed: Context7 API timeout
  💡 Kept in queue for retry

✅ Queue processed!
  Completed: 2 items
  Failed: 1 item (still in queue)
  Total time: 4.2 seconds
  
💡 Run command again later to retry failed items
```

### All Failed
```
❌ Queue processing failed!
  All 3 items failed to process
  Common error: Context7 API unavailable
  
💡 Queue preserved for retry
💡 Try again later when API is available
```

## Error Handling

### Context7 API Unavailable
```
Action: Keep item in queue
Message: "Context7 API unavailable, will retry later"
```

### Invalid Queue Format
```
Action: Skip malformed line, continue processing
Message: "Warning: Invalid queue entry, skipping"
```

### Permission Error
```
Action: Abort processing
Message: "Cannot write to cache, check permissions"
```

## Queue Management Commands

### View Queue Status
```bash
*context7-kb-queue-status

Output:
📋 Refresh Queue Status
  Items in queue: 3
  Oldest item: 2 hours ago
  Newest item: 5 minutes ago
  
  Queue contents:
    1. vitest/all - queued 2 hours ago
    2. pytest/fixtures - queued 5 minutes ago
    3. react/hooks - queued 10 minutes ago
```

### Clear Queue
```bash
*context7-kb-queue-clear

Output:
🗑️  Clearing refresh queue...
  Removed 3 items
  ✅ Queue cleared
```

## Dependencies
- context7-kb-refresh.md (helper functions)
- Context7 MCP tools (for fetching docs)
- Queue file: docs/kb/context7-cache/.refresh-queue

## Notes
- Simple file-based queue (no database)
- Manual processing (user controls when)
- Graceful failure handling (preserve queue)
- No automatic retry (user initiated)
- Clear feedback on progress

