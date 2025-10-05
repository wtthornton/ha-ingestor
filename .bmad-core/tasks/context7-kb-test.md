<!-- Powered by BMAD™ Core -->

# Context7 KB Test Task

## Purpose
Test the KB integration and cache functionality to ensure it works properly.

## Usage
When user types `*context7-kb-test`, execute this testing workflow.

## Test Workflow

### Step 1: Test KB Cache Check
```yaml
test_kb_cache:
  action: "test_kb_lookup"
  parameters:
    library: "react"
    topic: "hooks"
  expected_result: "cached_content_found"
  success_action: "test_kb_hit_count"
  failure_action: "test_context7_fallback"
```

### Step 2: Test Context7 Fallback
```yaml
test_context7_fallback:
  action: "test_context7_api"
  parameters:
    library: "new_library"
    topic: "new_topic"
  expected_result: "context7_api_success"
  success_action: "test_kb_storage"
  failure_action: "report_error"
```

### Step 3: Test KB Storage
```yaml
test_kb_storage:
  action: "test_kb_write"
  parameters:
    library: "new_library"
    topic: "new_topic"
    content: "test_content"
  expected_result: "kb_file_created"
  success_action: "test_metadata_update"
  failure_action: "report_error"
```

### Step 4: Test Metadata Update
```yaml
test_metadata_update:
  action: "test_metadata_operations"
  parameters:
    master_index: "docs/kb/context7-cache/index.yaml"
    library_meta: "docs/kb/context7-cache/libraries/{library}/meta.yaml"
    topic_index: "docs/kb/context7-cache/topics/{topic}/index.yaml"
  expected_result: "metadata_updated"
  success_action: "test_fuzzy_matching"
  failure_action: "report_error"
```

### Step 5: Test Fuzzy Matching
```yaml
test_fuzzy_matching:
  action: "test_fuzzy_search"
  parameters:
    query: "react hooks"
    threshold: 0.7
  expected_result: "fuzzy_match_found"
  success_action: "test_performance_metrics"
  failure_action: "report_error"
```

### Step 6: Test Performance Metrics
```yaml
test_performance_metrics:
  action: "test_metrics_calculation"
  parameters:
    hit_count: "increment"
    miss_count: "increment"
    response_time: "measure"
  expected_result: "metrics_updated"
  success_action: "generate_test_report"
  failure_action: "report_error"
```

## Test Scenarios

### Scenario 1: KB Cache Hit
```yaml
kb_cache_hit_test:
  description: "Test retrieving cached documentation from KB"
  steps:
    - call: "*context7-docs react hooks"
    - expect: "KB cache hit (response time < 0.15s)"
    - verify: "Hit count incremented"
    - verify: "Last accessed timestamp updated"
```

### Scenario 2: KB Cache Miss with Context7 Fallback
```yaml
kb_cache_miss_test:
  description: "Test KB cache miss with Context7 API fallback"
  steps:
    - call: "*context7-docs new_library new_topic"
    - expect: "KB cache miss"
    - expect: "Context7 API call"
    - expect: "Content stored in KB"
    - verify: "Metadata updated"
```

### Scenario 3: Fuzzy Matching
```yaml
fuzzy_matching_test:
  description: "Test fuzzy matching for similar topics"
  steps:
    - call: "*context7-docs react hook"
    - expect: "Fuzzy match found for 'hooks'"
    - expect: "Confidence score > 0.7"
    - verify: "Fuzzy match count incremented"
```

### Scenario 4: Performance Metrics
```yaml
performance_test:
  description: "Test performance metrics calculation"
  steps:
    - call: "*context7-kb-status"
    - expect: "Hit rate calculated correctly"
    - expect: "Response time < 0.15s for cached content"
    - verify: "Total entries updated"
    - verify: "Cache size calculated"
```

## Error Handling Tests

### Error Scenario 1: KB File Corruption
```yaml
kb_corruption_test:
  description: "Test handling of corrupted KB files"
  steps:
    - corrupt: "docs/kb/context7-cache/libraries/react/hooks.md"
    - call: "*context7-docs react hooks"
    - expect: "Error detected and handled"
    - expect: "Fallback to Context7 API"
    - expect: "KB file recreated"
```

### Error Scenario 2: Context7 API Failure
```yaml
context7_failure_test:
  description: "Test handling of Context7 API failures"
  steps:
    - simulate: "Context7 API timeout"
    - call: "*context7-docs unknown_library unknown_topic"
    - expect: "Graceful error handling"
    - expect: "User-friendly error message"
    - verify: "No KB corruption"
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

## Test Report Generation

### Test Results Format
```yaml
test_report:
  timestamp: "{current_timestamp}"
  total_tests: number
  passed_tests: number
  failed_tests: number
  success_rate: percentage
  
  performance_metrics:
    avg_kb_response_time: seconds
    avg_context7_response_time: seconds
    kb_hit_rate: percentage
    cache_efficiency: percentage
  
  recommendations:
    - improvement_suggestions: array
    - optimization_opportunities: array
    - maintenance_actions: array
```
