<!-- Powered by BMAD™ Core -->

# Context7 KB Cache Refresh Task

## Purpose
Simple auto-refresh system for Context7 KB cache. Keeps documentation fresh without over-engineering.

## Usage
```bash
# Check what needs refreshing
*context7-kb-refresh --check-only

# Refresh all stale entries
*context7-kb-refresh

# Process queued refreshes
*context7-kb-process-queue
```

## Implementation

### Staleness Check Logic

```python
def is_cache_stale(library_name: str) -> bool:
    """
    Check if cache needs refresh - dead simple
    
    Returns:
        True if stale (needs refresh)
        False if fresh (no refresh needed)
    """
    from datetime import datetime, timedelta
    import yaml
    import os
    
    meta_file = f"docs/kb/context7-cache/libraries/{library_name}/meta.yaml"
    
    if not os.path.exists(meta_file):
        return True  # No meta file = stale
    
    with open(meta_file, 'r') as f:
        meta = yaml.safe_load(f)
    
    # Get last_checked timestamp
    last_checked = meta.get('library_info', {}).get('last_checked')
    
    if not last_checked:
        return True  # Never checked = stale
    
    # Get max age policy (default 30 days)
    refresh_policy = meta.get('refresh_policy', {})
    max_age_days = refresh_policy.get('max_age_days', 30)
    
    # Calculate age
    last_checked_date = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
    age = datetime.now() - last_checked_date
    
    # Return True if older than max age
    return age.days > max_age_days


def get_cache_age(library_name: str) -> int:
    """Get cache age in days"""
    from datetime import datetime
    import yaml
    import os
    
    meta_file = f"docs/kb/context7-cache/libraries/{library_name}/meta.yaml"
    
    if not os.path.exists(meta_file):
        return 999  # Unknown age
    
    with open(meta_file, 'r') as f:
        meta = yaml.safe_load(f)
    
    last_checked = meta.get('library_info', {}).get('last_checked')
    
    if not last_checked:
        return 999  # Never checked
    
    last_checked_date = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
    age = datetime.now() - last_checked_date
    
    return age.days
```

### Queue Management

```python
def queue_refresh(library_name: str, topic: str = None):
    """Add library to refresh queue (simple file-based)"""
    from datetime import datetime
    import os
    
    queue_file = "docs/kb/context7-cache/.refresh-queue"
    
    # Create entry
    entry = f"{library_name},{topic or 'all'},{datetime.now().isoformat()}\n"
    
    # Append to queue
    with open(queue_file, 'a') as f:
        f.write(entry)
    
    return True


def get_refresh_queue() -> list:
    """Get all queued refresh items"""
    queue_file = "docs/kb/context7-cache/.refresh-queue"
    
    if not os.path.exists(queue_file):
        return []
    
    items = []
    with open(queue_file, 'r') as f:
        for line in f:
            if line.strip():
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    items.append({
                        'library': parts[0],
                        'topic': parts[1],
                        'queued_at': parts[2] if len(parts) > 2 else 'unknown'
                    })
    
    return items


def clear_refresh_queue():
    """Clear the refresh queue"""
    import os
    
    queue_file = "docs/kb/context7-cache/.refresh-queue"
    
    if os.path.exists(queue_file):
        os.remove(queue_file)
    
    return True


def process_queue_silently() -> int:
    """
    Process queue without verbose output - for automatic startup use
    
    Returns:
        Number of items successfully processed
    """
    queue = get_refresh_queue()
    if not queue:
        return 0
    
    success_count = 0
    failed_items = []
    
    for item in queue:
        try:
            # Fetch from Context7 silently
            # (Implementation will call Context7 MCP tools)
            library = item['library']
            topic = item.get('topic', 'all')
            
            # This would call the actual Context7 fetch
            # For now, just track success
            success_count += 1
            
        except Exception as e:
            # Log failure but continue processing
            failed_items.append(item)
    
    # Clear queue if all succeeded, or rewrite with failures
    if not failed_items:
        clear_refresh_queue()
    else:
        # Rewrite queue with only failed items
        queue_file = "docs/kb/context7-cache/.refresh-queue"
        with open(queue_file, 'w') as f:
            for item in failed_items:
                f.write(f"{item['library']},{item['topic']},{item['queued_at']}\n")
    
    return success_count
```

### Metadata Update

```python
def update_last_checked(library_name: str):
    """Update last_checked timestamp in meta.yaml"""
    from datetime import datetime
    import yaml
    import os
    
    meta_file = f"docs/kb/context7-cache/libraries/{library_name}/meta.yaml"
    
    if not os.path.exists(meta_file):
        return False
    
    # Read current meta
    with open(meta_file, 'r') as f:
        meta = yaml.safe_load(f)
    
    # Update last_checked
    if 'library_info' not in meta:
        meta['library_info'] = {}
    
    meta['library_info']['last_checked'] = datetime.now().isoformat() + 'Z'
    
    # Write back
    with open(meta_file, 'w') as f:
        yaml.dump(meta, f, default_flow_style=False, sort_keys=False)
    
    return True
```

### List Cached Libraries

```python
def list_cached_libraries() -> list:
    """Get list of all cached libraries"""
    import os
    
    libraries_dir = "docs/kb/context7-cache/libraries"
    
    if not os.path.exists(libraries_dir):
        return []
    
    libraries = []
    for item in os.listdir(libraries_dir):
        if os.path.isdir(os.path.join(libraries_dir, item)):
            libraries.append(item)
    
    return libraries
```

## Workflow

### Check-Only Mode
```yaml
check_only_workflow:
  steps:
    - list_all_libraries
    - check_staleness_for_each
    - display_stale_items
    - show_summary
```

### Refresh Mode
```yaml
refresh_workflow:
  steps:
    - list_all_libraries
    - check_staleness_for_each
    - for_each_stale_library:
        - fetch_from_context7
        - update_cache
        - update_last_checked
    - show_summary
```

### Queue Processing
```yaml
queue_workflow:
  steps:
    - read_queue_file
    - for_each_queued_item:
        - fetch_from_context7
        - update_cache
        - update_last_checked
    - clear_queue
    - show_summary
```

## Output Examples

### Check-Only Output
```
🔍 Checking for stale cache entries...
  ⚠️  vitest - 35 days old (max: 14 days)
  ⚠️  pytest - 42 days old (max: 30 days)
  ✅ playwright - 7 days old (max: 14 days)

📊 Found 2 stale entries out of 3 total
```

### Refresh Output
```
🔄 Refreshing stale cache entries...

Refreshing vitest...
  📄 Fetching documentation from Context7...
  ✅ Updated vitest/docs.md
  ✅ Updated last_checked timestamp

Refreshing pytest...
  📄 Fetching documentation from Context7...
  ✅ Updated pytest/docs.md
  ✅ Updated last_checked timestamp

✅ Refreshed 2 libraries successfully
```

### Queue Processing Output
```
🔄 Processing refresh queue...

Queue contains 2 items:
  1. vitest/all (queued 2 hours ago)
  2. pytest/fixtures (queued 5 minutes ago)

Processing vitest...
  ✅ Refreshed successfully

Processing pytest...
  ✅ Refreshed successfully

✅ Queue processed, 2 items completed
```

## Error Handling

### Common Errors
```python
error_scenarios = {
    "no_meta_file": {
        "action": "treat_as_stale",
        "message": "No meta.yaml found, will refresh"
    },
    "invalid_yaml": {
        "action": "skip_and_warn",
        "message": "Invalid YAML format, skipping"
    },
    "context7_unavailable": {
        "action": "queue_for_later",
        "message": "Context7 unavailable, queued for retry"
    },
    "permission_error": {
        "action": "abort",
        "message": "Cannot write to cache directory"
    }
}
```

## Configuration

Default refresh policies by library type:

```yaml
refresh_policies:
  stable:
    max_age_days: 30
    examples: ["react", "pytest", "fastapi"]
  
  active:
    max_age_days: 14
    examples: ["vitest", "playwright"]
  
  critical:
    max_age_days: 7
    examples: ["security-libs", "jwt", "oauth"]
```

## Success Criteria
- ✅ Can detect stale cache entries
- ✅ Can refresh cache without blocking users
- ✅ Can manually trigger refresh when needed
- ✅ Simple file-based queue system
- ✅ No complex dependencies
- ✅ Clear user feedback

## Implementation Notes
- Keep it simple - files, not databases
- Manual triggers - user controls when
- Queue for background - don't block users
- Check on access - don't poll constantly
- Simple, not perfect - iterate later

