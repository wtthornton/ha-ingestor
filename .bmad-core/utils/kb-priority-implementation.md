<!-- Powered by BMAD™ Core -->

# KB Priority Implementation Guide

## Purpose
This document defines how BMAD agents should respect the `kb_priority: true` setting from the core configuration.

## Configuration Reference

From `.bmad-core/core-config.yaml`:
```yaml
context7:
  agentLimits:
    architect:
      tokenLimit: 4000
      topics: ["architecture", "design-patterns", "scalability"]
      kb_priority: true
    dev:
      tokenLimit: 3000
      topics: ["hooks", "routing", "authentication", "testing"]
      kb_priority: true
    qa:
      tokenLimit: 2500
      topics: ["testing", "security", "performance"]
      kb_priority: true
```

## KB Priority Behavior Implementation

### When kb_priority: true

Agents with `kb_priority: true` must follow this workflow for ANY external library documentation needs:

#### Step 1: Always Check KB First
```yaml
kb_priority_workflow:
  for_any_library_documentation:
    1. check_kb_cache: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
    2. if_cache_hit: "use_cached_content + update_hit_count"
    3. if_cache_miss: "proceed_to_fuzzy_match"
    4. if_fuzzy_match: "use_fuzzy_match + update_hit_count"
    5. if_no_match: "call_context7_api + store_in_kb"
```

#### Step 2: Automatic KB Population
```yaml
automatic_kb_population:
  when_context7_called:
    1. fetch_from_context7: "get documentation"
    2. store_in_kb: "cache for future use"
    3. update_metadata: "track usage statistics"
    4. return_content: "provide to user"
```

#### Step 3: Performance Monitoring
```yaml
performance_monitoring:
  track_metrics:
    - kb_hit_rate: "must exceed 70%"
    - response_time: "cached content < 0.15s"
    - cache_efficiency: "optimize for speed"
    - storage_utilization: "monitor cache size"
```

## Agent-Specific Implementation

### Dev Agent (kb_priority: true)
```yaml
dev_agent_kb_priority:
  focus_areas: ["hooks", "routing", "authentication", "testing"]
  token_limit: 3000
  
  implementation_workflow:
    when_implementing_library:
      1. check_kb_for_patterns: "look for similar implementations"
      2. use_cached_examples: "if available in KB"
      3. cache_new_patterns: "store for future development"
      4. optimize_for_speed: "prefer KB over Context7 API"
  
  example_usage:
    - "*context7-docs react hooks": "check KB first, then Context7"
    - "*context7-docs fastapi authentication": "use cached patterns if available"
    - "*context7-docs pytest fixtures": "leverage KB for testing patterns"
```

### Architect Agent (kb_priority: true)
```yaml
architect_agent_kb_priority:
  focus_areas: ["architecture", "design-patterns", "scalability"]
  token_limit: 4000
  
  implementation_workflow:
    when_researching_patterns:
      1. check_kb_for_architecture: "look for design patterns"
      2. use_cached_insights: "if available in KB"
      3. cache_new_patterns: "store architectural decisions"
      4. optimize_for_comprehensiveness: "prefer KB over Context7 API"
  
  example_usage:
    - "*context7-docs react architecture": "check KB for component patterns"
    - "*context7-docs fastapi scalability": "use cached scaling patterns"
    - "*context7-docs docker deployment": "leverage KB for infrastructure patterns"
```

### QA Agent (kb_priority: true)
```yaml
qa_agent_kb_priority:
  focus_areas: ["testing", "security", "performance"]
  token_limit: 2500
  
  implementation_workflow:
    when_researching_testing:
      1. check_kb_for_testing: "look for testing patterns"
      2. use_cached_security: "if available in KB"
      3. cache_new_insights: "store testing strategies"
      4. optimize_for_thoroughness: "prefer KB over Context7 API"
  
  example_usage:
    - "*context7-docs playwright testing": "check KB for e2e patterns"
    - "*context7-docs pytest security": "use cached security testing"
    - "*context7-docs performance testing": "leverage KB for load testing"
```

## KB Priority Enforcement

### Mandatory Behaviors
```yaml
mandatory_behaviors:
  kb_priority_true_agents:
    - always_check_kb_first: "before any Context7 API call"
    - cache_all_results: "store Context7 results in KB"
    - respect_token_limits: "use configured token limits"
    - track_performance: "monitor hit rates and response times"
    - optimize_for_speed: "prefer cached content when possible"
```

### Performance Targets
```yaml
performance_targets:
  kb_hit_rate: "> 70%"
  cached_response_time: "< 0.15s"
  context7_api_time: "< 2.0s"
  kb_storage_time: "< 0.5s"
  metadata_update_time: "< 0.1s"
```

### Error Handling
```yaml
error_handling:
  kb_unavailable:
    action: "fallback_to_context7"
    message: "KB temporarily unavailable, using Context7 API"
    log_level: "warning"
  
  context7_unavailable:
    action: "return_error"
    message: "Both KB and Context7 unavailable"
    log_level: "error"
    suggest_retry: true
  
  performance_degradation:
    action: "optimize_kb"
    message: "KB performance below targets, consider cleanup"
    log_level: "info"
```

## Implementation Checklist

### For Each Agent with kb_priority: true
- [ ] Implement KB-first lookup workflow
- [ ] Add automatic KB population from Context7 calls
- [ ] Track performance metrics (hit rate, response time)
- [ ] Respect token limits from configuration
- [ ] Handle errors gracefully with fallbacks
- [ ] Optimize for speed over API calls
- [ ] Cache all Context7 results for future use

### For BMad Master Agent
- [ ] Provide KB-first Context7 commands
- [ ] Implement KB status and analytics commands
- [ ] Support KB cleanup and maintenance commands
- [ ] Monitor overall KB performance
- [ ] Provide KB testing functionality

### For Core Configuration
- [ ] Ensure kb_priority setting is respected
- [ ] Configure appropriate token limits per agent
- [ ] Set performance targets and thresholds
- [ ] Enable analytics and monitoring
- [ ] Configure cleanup and maintenance schedules

## Success Criteria

### Functional Requirements
- ✅ All agents with kb_priority: true use KB-first approach
- ✅ KB hit rate > 70% for priority agents
- ✅ Response time < 0.15s for cached content
- ✅ Automatic KB population from Context7 calls
- ✅ Proper performance monitoring and analytics

### Performance Requirements
- ✅ KB operations complete in < 0.15s
- ✅ Context7 API calls minimized through caching
- ✅ Metadata updates complete in < 0.1s
- ✅ Cache efficiency optimized for speed
- ✅ Storage utilization monitored and managed

### Reliability Requirements
- ✅ Graceful fallback to Context7 API on KB issues
- ✅ No data corruption on errors
- ✅ Consistent metadata across all files
- ✅ Proper cleanup and maintenance
- ✅ Recovery from corrupted files
