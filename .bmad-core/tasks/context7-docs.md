<!-- Powered by BMAD™ Core -->

# Context7 Documentation Retrieval Task

## Purpose
Retrieve focused documentation for a library using Context7 MCP tools with token-efficient parameters.

## Workflow
1. **Library Resolution**: Resolve library name to Context7 ID (if needed)
2. **Parameter Setup**: Configure token limits and topic focus
3. **Documentation Retrieval**: Call `mcp_Context7_get-library-docs`
4. **Cache Management**: Store documentation in cache
5. **Output Formatting**: Present documentation in structured format

## Implementation
```yaml
steps:
  - name: "resolve_library"
    action: "get_or_resolve_library_id"
    fallback: "call_context7_resolve_task"
  
  - name: "setup_parameters"
    action: "configure_context7_params"
    defaults:
      tokens: 3000
      topic: "{user_topic_or_default}"
  
  - name: "retrieve_docs"
    action: "call_context7_get_docs"
    tool: "mcp_Context7_get-library-docs"
    parameters:
      context7CompatibleLibraryID: "{library_id}"
      topic: "{topic}"
      tokens: "{token_limit}"
  
  - name: "cache_documentation"
    action: "store_docs_in_cache"
    key: "context7_docs_{library_id}_{topic}"
    ttl: 3600
  
  - name: "format_output"
    action: "present_documentation"
    format: "structured_markdown"
    include_metadata: true
```

## Token Management
- Default token limit: 3000
- Topic-focused retrieval
- Progressive loading (start small, expand if needed)
- Cache to avoid repeated calls

## Error Handling
- Library not found
- Context7 service unavailable
- Token limit exceeded
- Invalid topic parameter

## Success Criteria
- Documentation retrieved successfully
- Token usage within limits
- Documentation cached for future use
- Clear, structured output provided
