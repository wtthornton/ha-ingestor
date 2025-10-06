<!-- Powered by BMAD™ Core -->

# Context7 Documentation Retrieval Task

## Purpose
MANDATORY: Retrieve focused documentation for a library using Context7 MCP tools with token-efficient parameters. FAILURE to use Context7 KB for library research is FORBIDDEN.

## MANDATORY Workflow
1. **MANDATORY Library Resolution**: MUST resolve library name to Context7 ID (if needed) - FORBIDDEN to skip
2. **MANDATORY Parameter Setup**: MUST configure token limits and topic focus - REQUIRED for efficiency
3. **MANDATORY Documentation Retrieval**: MUST call `mcp_Context7_get-library-docs` - FORBIDDEN to use generic knowledge
4. **MANDATORY Cache Management**: MUST store documentation in cache - REQUIRED for performance
5. **MANDATORY Output Formatting**: MUST present documentation in structured format - REQUIRED for usability

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
