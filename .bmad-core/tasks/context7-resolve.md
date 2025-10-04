<!-- Powered by BMAD™ Core -->

# Context7 Library Resolution Task

## Purpose
Resolve a library name to its Context7-compatible library ID for subsequent documentation retrieval.

## Workflow
1. **Input Validation**: Validate library name parameter
2. **Cache Check**: Check if library ID is already cached
3. **Context7 Resolution**: Call `mcp_Context7_resolve-library-id` if not cached
4. **Cache Storage**: Store resolved ID in session cache
5. **Output**: Return Context7-compatible library ID

## Implementation
```yaml
steps:
  - name: "validate_input"
    action: "check_library_name_format"
    error_handling: "return_error_if_invalid"
  
  - name: "check_cache"
    action: "lookup_cached_library_id"
    condition: "library_name_in_cache"
    success_action: "return_cached_id"
  
  - name: "resolve_library"
    action: "call_context7_resolve"
    tool: "mcp_Context7_resolve-library-id"
    parameters:
      libraryName: "{library_name}"
  
  - name: "cache_result"
    action: "store_in_session_cache"
    key: "context7_library_ids"
    value: "{resolved_id}"
  
  - name: "return_result"
    action: "display_library_id"
    format: "Context7 ID: {library_id}"
```

## Error Handling
- Invalid library name format
- Context7 service unavailable
- Library not found in Context7
- Cache storage failures

## Success Criteria
- Library ID successfully resolved
- ID cached for future use
- Clear output format provided
