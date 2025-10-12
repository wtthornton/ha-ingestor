<!-- Powered by BMAD™ Core -->

# Context7 KB Lookup Implementation Task

## Purpose
MANDATORY: Implement the actual KB-first lookup system that checks local cache before calling Context7 API. FAILURE to use KB-first approach is FORBIDDEN.

## Session Tracking (Hybrid Auto-Refresh)
```python
# Global session state - tracks if staleness check has run
_SESSION_KB_CHECKED = False
```

## MANDATORY Usage
When user types `*context7-docs {library} {topic}`, you MUST execute this KB-first workflow. FAILURE to use KB-first approach is FORBIDDEN.

## Auto-Refresh Functions (Hybrid Mode)

### Auto Check and Queue Stale
```python
def auto_check_and_queue_stale():
    """
    Check all cached libraries for staleness and queue stale ones.
    Runs once per session on first KB access (if enabled).
    
    Returns:
        List of stale libraries with metadata
    """
    from .context7_kb_refresh import is_cache_stale, get_cache_age, list_cached_libraries, queue_refresh
    
    stale_libs = []
    
    for lib in list_cached_libraries():
        if is_cache_stale(lib):
            stale_libs.append({
                'name': lib,
                'age_days': get_cache_age(lib)
            })
            queue_refresh(lib, 'all')
    
    return stale_libs


def notify_stale_libraries(stale_libs):
    """Display user-friendly notification about stale libraries"""
    if not stale_libs:
        return
    
    print(f"📋 KB Status: {len(stale_libs)} libraries need refresh")
    
    # Show up to 3 stale libraries
    for lib in stale_libs[:3]:
        print(f"   ⚠️  {lib['name']} ({lib['age_days']} days old)")
    
    if len(stale_libs) > 3:
        print(f"   ... and {len(stale_libs) - 3} more")
    
    print(f"💡 Queued for refresh on next agent startup\n")
```

## Implementation Steps

### Step 0: Session Check (Hybrid Auto-Refresh)
```yaml
session_check:
  enabled_if: "config.auto_check_on_first_access == true"
  runs: "once_per_session"
  action: "check_and_queue_stale"
  
  workflow:
    - check_session_flag: "_SESSION_KB_CHECKED"
    - if_not_checked:
        - set_flag: "_SESSION_KB_CHECKED = True"
        - run: "auto_check_and_queue_stale()"
        - notify: "notify_stale_libraries()"
    - continue_to_step_1
```

### Step 1: Check KB Cache
```yaml
kb_cache_check:
  action: "read_kb_file"
  path: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
  success_action: "return_cached_content"
  failure_action: "fuzzy_match_lookup"
  
  on_success:
    - update_hit_count: "{library}:{topic}"
    - update_last_accessed: "{current_timestamp}"
    - return_content: "{cached_docs}"
```

### Step 2: Fuzzy Match Lookup
```yaml
fuzzy_match_lookup:
  action: "search_kb_index"
  parameters:
    library: "{library}"
    topic: "{topic}"
    confidence_threshold: 0.7
  success_action: "return_fuzzy_match"
  failure_action: "context7_api_call"
  
  search_strategy:
    - exact_library_match: true
    - topic_similarity: true
    - cross_reference_lookup: true
```

### Step 3: Context7 API Call
```yaml
context7_api_call:
  action: "mcp_Context7_get-library-docs"
  parameters:
    context7CompatibleLibraryID: "{resolved_library_id}"
    topic: "{topic}"
    tokens: "{token_limit}"
  success_action: "store_in_kb"
  failure_action: "return_error"
```

### Step 4: Store in KB Cache
```yaml
store_in_kb:
  steps:
    - create_directory: "docs/kb/context7-cache/libraries/{library}"
    - write_content: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
    - update_metadata: "docs/kb/context7-cache/libraries/{library}/meta.yaml"
    - update_topic_index: "docs/kb/context7-cache/topics/{topic}/index.yaml"
    - update_master_index: "docs/kb/context7-cache/index.yaml"
  success_action: "return_content"
```

## KB File Operations

### Read KB Cache File
```yaml
read_kb_cache:
  file_path: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
  format: "markdown_with_metadata"
  metadata_fields:
    - library: string
    - topic: string
    - context7_id: string
    - trust_score: number
    - snippet_count: number
    - last_updated: timestamp
    - cache_hits: number
    - token_count: number
```

### Update KB Metadata
```yaml
update_kb_metadata:
  library_meta: "docs/kb/context7-cache/libraries/{library}/meta.yaml"
  topic_index: "docs/kb/context7-cache/topics/{topic}/index.yaml"
  master_index: "docs/kb/context7-cache/index.yaml"
  
  updates:
    hit_count: "increment"
    last_accessed: "{current_timestamp}"
    total_hits: "increment"
    hit_rate: "recalculate"
```

### Write KB Cache File
```yaml
write_kb_cache:
  content_format: |
    # {library} - {topic}
    
    **Source**: {context7_id} (Trust Score: {trust_score})
    **Snippets**: {snippet_count} | **Tokens**: {token_count}
    **Last Updated**: {last_updated} | **Cache Hits**: {cache_hits}
    
    ---
    
    {context7_content}
    
    ---
    
    <!-- KB Metadata -->
    <!-- Library: {library} -->
    <!-- Topic: {topic} -->
    <!-- Context7 ID: {context7_id} -->
    <!-- Trust Score: {trust_score} -->
    <!-- Snippet Count: {snippet_count} -->
    <!-- Last Updated: {last_updated} -->
    <!-- Cache Hits: {cache_hits} -->
    <!-- Token Count: {token_count} -->
```

## Performance Metrics

### Track KB Performance
```yaml
performance_tracking:
  metrics:
    - cache_hits: number
    - cache_misses: number
    - hit_rate: percentage
    - avg_response_time: seconds
    - kb_size: bytes
    - total_entries: number
  
  update_triggers:
    - on_cache_hit: "increment_hits"
    - on_cache_miss: "increment_misses"
    - on_kb_store: "update_size_and_entries"
    - on_kb_cleanup: "recalculate_metrics"
```

## Error Handling

### Common Error Scenarios
```yaml
error_handling:
  kb_file_not_found:
    action: "fuzzy_match_lookup"
    message: "KB cache miss, trying fuzzy match"
  
  invalid_yaml_format:
    action: "recreate_kb_file"
    message: "KB file corrupted, recreating"
  
  storage_permission_error:
    action: "return_error"
    message: "Cannot write to KB cache, check permissions"
  
  context7_api_error:
    action: "return_error"
    message: "Context7 API unavailable, try again later"
```

## Success Criteria
- KB cache hit rate > 70%
- Response time < 0.15s for cached content
- Automatic KB population from Context7 calls
- Proper metadata tracking and analytics
- Graceful fallback to Context7 API on cache miss
