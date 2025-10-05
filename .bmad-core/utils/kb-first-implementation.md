<!-- Powered by BMAD™ Core -->

# KB-First Implementation Guide

## Purpose
This document provides the actual implementation logic for KB-first Context7 integration that agents should follow.

## Implementation Logic

### KB-First Context7 Documentation Retrieval

When a user calls `*context7-docs {library} {topic}`, execute this workflow:

#### Step 1: Check KB Cache
```yaml
kb_cache_check:
  action: "read_file"
  path: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
  
  on_success:
    - extract_metadata: "from file comments"
    - update_hit_count: "increment in metadata"
    - update_last_accessed: "set to current timestamp"
    - return_content: "cached documentation"
    - log_performance: "response_time < 0.15s"
  
  on_failure:
    - action: "fuzzy_match_lookup"
```

#### Step 2: Fuzzy Match Lookup
```yaml
fuzzy_match_lookup:
  action: "search_kb_index"
  search_strategy:
    - search_library_directories: "docs/kb/context7-cache/libraries/*/"
    - find_similar_topics: "using string similarity > 0.7"
    - check_cross_references: "docs/kb/context7-cache/cross-references.yaml"
  
  on_success:
    - return_fuzzy_match: "with confidence score"
    - update_hit_count: "increment fuzzy match count"
    - log_performance: "fuzzy match found"
  
  on_failure:
    - action: "context7_api_call"
```

#### Step 3: Context7 API Call
```yaml
context7_api_call:
  action: "mcp_Context7_get-library-docs"
  parameters:
    context7CompatibleLibraryID: "{resolved_library_id}"
    topic: "{topic}"
    tokens: "{token_limit}"
  
  on_success:
    - action: "store_in_kb"
    - log_performance: "context7_api_call_time"
  
  on_failure:
    - return_error: "Context7 API unavailable"
    - suggest_alternatives: "try different library/topic"
```

#### Step 4: Store in KB Cache
```yaml
store_in_kb:
  steps:
    - create_directory: "docs/kb/context7-cache/libraries/{library}"
    - write_content: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
    - update_library_metadata: "docs/kb/context7-cache/libraries/{library}/meta.yaml"
    - update_topic_index: "docs/kb/context7-cache/topics/{topic}/index.yaml"
    - update_master_index: "docs/kb/context7-cache/index.yaml"
    - update_cross_references: "docs/kb/context7-cache/cross-references.yaml"
  
  success_action: "return_content"
  failure_action: "return_content_without_cache"
```

## KB File Operations

### Read KB Cache File
```yaml
read_kb_cache_file:
  file_path: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
  
  extract_metadata:
    - library: "extract from file comments"
    - topic: "extract from file comments"
    - context7_id: "extract from file comments"
    - trust_score: "extract from file comments"
    - snippet_count: "extract from file comments"
    - last_updated: "extract from file comments"
    - cache_hits: "extract from file comments"
    - token_count: "extract from file comments"
  
  return_format: |
    # KB Cache Hit
    **Source**: {context7_id} (Trust Score: {trust_score})
    **Cache Hits**: {cache_hits} | **Last Updated**: {last_updated}
    
    {content}
```

### Write KB Cache File
```yaml
write_kb_cache_file:
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

### Update KB Metadata Files
```yaml
update_kb_metadata:
  library_meta: "docs/kb/context7-cache/libraries/{library}/meta.yaml"
  topic_index: "docs/kb/context7-cache/topics/{topic}/index.yaml"
  master_index: "docs/kb/context7-cache/index.yaml"
  
  updates:
    hit_count: "increment"
    last_accessed: "{current_timestamp}"
    total_hits: "increment"
    hit_rate: "recalculate as total_hits / (total_hits + total_misses)"
    cache_size: "recalculate total file sizes"
    last_updated: "{current_timestamp}"
```

## Performance Tracking

### Track KB Performance Metrics
```yaml
performance_tracking:
  metrics_to_track:
    - cache_hits: "number"
    - cache_misses: "number"
    - fuzzy_matches: "number"
    - hit_rate: "percentage"
    - avg_response_time: "seconds"
    - kb_size: "bytes"
    - total_entries: "number"
  
  update_triggers:
    - on_cache_hit: "increment_hits, measure_response_time"
    - on_cache_miss: "increment_misses"
    - on_fuzzy_match: "increment_fuzzy_matches"
    - on_kb_store: "update_size_and_entries"
    - on_kb_cleanup: "recalculate_metrics"
  
  performance_targets:
    - hit_rate: "> 70%"
    - avg_response_time: "< 0.15s for cached content"
    - cache_efficiency: "> 80%"
    - storage_utilization: "< 80% of max_cache_size"
```

## Error Handling

### Common Error Scenarios and Responses
```yaml
error_handling:
  kb_file_not_found:
    action: "fuzzy_match_lookup"
    message: "KB cache miss, trying fuzzy match"
    log_level: "info"
  
  kb_file_corrupted:
    action: "recreate_kb_file"
    message: "KB file corrupted, recreating from Context7"
    log_level: "warning"
  
  storage_permission_error:
    action: "return_error"
    message: "Cannot write to KB cache, check permissions"
    log_level: "error"
  
  context7_api_error:
    action: "return_error"
    message: "Context7 API unavailable, try again later"
    log_level: "error"
    suggest_retry: true
  
  invalid_library_name:
    action: "suggest_alternatives"
    message: "Library not found, did you mean: {suggestions}"
    log_level: "info"
  
  fuzzy_match_threshold_not_met:
    action: "context7_api_call"
    message: "No similar topics found, fetching from Context7"
    log_level: "info"
```

## Agent Integration Instructions

### For BMad Master Agent
```yaml
bmad_master_integration:
  command: "*context7-docs {library} {topic}"
  workflow:
    1. execute_kb_first_lookup
    2. return_results_with_performance_metrics
    3. log_usage_statistics
  
  additional_commands:
    - "*context7-kb-status": "show detailed KB analytics"
    - "*context7-kb-test": "test KB integration functionality"
```

### For Dev Agent
```yaml
dev_agent_integration:
  usage: "When implementing external libraries"
  workflow:
    1. check_kb_for_library_docs
    2. use_cached_patterns_if_available
    3. cache_new_patterns_for_future_use
  
  focus_areas:
    - "hooks, routing, authentication, testing"
    - "token_limit: 3000"
    - "kb_priority: true"
```

### For Architect Agent
```yaml
architect_agent_integration:
  usage: "When researching design patterns and technologies"
  workflow:
    1. check_kb_for_architecture_patterns
    2. use_cached_design_patterns
    3. cache_new_architecture_insights
  
  focus_areas:
    - "architecture, design-patterns, scalability"
    - "token_limit: 4000"
    - "kb_priority: true"
```

### For QA Agent
```yaml
qa_agent_integration:
  usage: "When researching testing frameworks and security patterns"
  workflow:
    1. check_kb_for_testing_patterns
    2. use_cached_security_patterns
    3. cache_new_testing_insights
  
  focus_areas:
    - "testing, security, performance"
    - "token_limit: 2500"
    - "kb_priority: true"
```

## Success Criteria

### Functional Requirements
- ✅ KB cache hit rate > 70%
- ✅ Response time < 0.15s for cached content
- ✅ Automatic KB population from Context7 calls
- ✅ Proper metadata tracking and analytics
- ✅ Graceful fallback to Context7 API on cache miss
- ✅ Fuzzy matching with confidence threshold
- ✅ Error handling for all failure scenarios

### Performance Requirements
- ✅ KB cache operations complete in < 0.15s
- ✅ Context7 API calls complete in < 2.0s
- ✅ KB storage operations complete in < 0.5s
- ✅ Metadata updates complete in < 0.1s
- ✅ Fuzzy matching complete in < 0.2s

### Reliability Requirements
- ✅ No data corruption on errors
- ✅ Graceful degradation on failures
- ✅ Consistent metadata across all files
- ✅ Proper cleanup on errors
- ✅ Recovery from corrupted files
