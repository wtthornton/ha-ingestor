<!-- Powered by BMAD™ Core -->

# Context7 Knowledge Base Integration Task

## Purpose
Provide KB-first integration of Context7 MCP tools into BMad workflows with intelligent caching, sharding, and fuzzy matching capabilities.

## Usage
When user types `*context7-docs {library} {topic}` or `*context7-resolve {library}`, execute this workflow.

## Workflow

### For Library Resolution (*context7-resolve)
1. **Input Validation**: Validate library name parameter
2. **KB Cache Check**: Check if library ID is cached in KB
3. **Context7 Resolution**: Call `mcp_Context7_resolve-library-id` if not cached
4. **KB Storage**: Store resolved library ID in KB cache
5. **Display Results**: Show resolved library ID

### For Documentation Retrieval (*context7-docs)
1. **KB-First Lookup**: Check local KB cache for documentation
2. **Fuzzy Matching**: Try fuzzy matching if exact match not found
3. **Library Resolution**: Resolve library name to Context7 ID (if needed)
4. **Context7 Retrieval**: Call `mcp_Context7_get-library-docs` if cache miss
5. **KB Storage**: Store Context7 results in sharded KB structure
6. **Index Update**: Update KB index and metadata
7. **Display Results**: Show documentation in formatted output

## Implementation

### KB-First Lookup System
```yaml
kb_lookup:
  steps:
    - name: "check_kb_cache"
      action: "lookup_in_kb"
      parameters:
        library: "{library}"
        topic: "{topic}"
      success_action: "return_cached_docs"
      failure_action: "fuzzy_match_lookup"
    
    - name: "fuzzy_match_lookup"
      action: "fuzzy_match_in_kb"
      parameters:
        library: "{library}"
        topic: "{topic}"
        confidence_threshold: 0.7
      success_action: "return_fuzzy_matched_docs"
      failure_action: "fetch_from_context7"
    
    - name: "fetch_from_context7"
      action: "call_context7_get_docs"
      tool: "mcp_Context7_get-library-docs"
      parameters:
        context7CompatibleLibraryID: "{library_id}"
        topic: "{topic}"
        tokens: "{token_limit}"
      success_action: "store_in_kb"
      failure_action: "return_error"
    
    - name: "store_in_kb"
      action: "store_sharded_docs"
      parameters:
        library: "{library}"
        topic: "{topic}"
        content: "{docs_content}"
        metadata: "{docs_metadata}"
      success_action: "update_kb_index"
      failure_action: "return_docs_without_cache"
    
    - name: "update_kb_index"
      action: "update_kb_metadata"
      parameters:
        library: "{library}"
        topic: "{topic}"
        cache_hit: false
        file_size: "{content_size}"
        token_count: "{token_count}"
      success_action: "return_docs"
      failure_action: "return_docs_without_index_update"
```

### Library Resolution with KB Cache
```yaml
library_resolution:
  steps:
    - name: "check_kb_library_cache"
      action: "lookup_library_in_kb"
      parameters:
        library: "{library}"
      success_action: "return_cached_library_id"
      failure_action: "resolve_with_context7"
    
    - name: "resolve_with_context7"
      action: "call_context7_resolve"
      tool: "mcp_Context7_resolve-library-id"
      parameters:
        libraryName: "{library_name}"
      success_action: "store_library_in_kb"
      failure_action: "return_error"
    
    - name: "store_library_in_kb"
      action: "store_library_metadata"
      parameters:
        library: "{library}"
        context7_id: "{library_id}"
        metadata: "{library_metadata}"
      success_action: "return_library_id"
      failure_action: "return_library_id_without_cache"
```

### Sharded Storage System
```yaml
sharded_storage:
  steps:
    - name: "create_library_directory"
      action: "ensure_directory_exists"
      path: "docs/kb/context7-cache/libraries/{library}"
    
    - name: "store_sharded_documentation"
      action: "write_sharded_file"
      path: "docs/kb/context7-cache/libraries/{library}/{topic}.md"
      content: "{formatted_docs_content}"
      format: "markdown_with_metadata"
    
    - name: "update_library_metadata"
      action: "update_meta_yaml"
      path: "docs/kb/context7-cache/libraries/{library}/meta.yaml"
      updates:
        topics:
          "{topic}":
            file: "{topic}.md"
            size: "{content_size}"
            last_updated: "{current_timestamp}"
            cache_hits: 0
            token_count: "{token_count}"
            context7_source: "{context7_url}"
    
    - name: "update_topic_index"
      action: "update_topic_index"
      path: "docs/kb/context7-cache/topics/{topic}/index.yaml"
      updates:
        libraries:
          - name: "{library}"
            file: "../../libraries/{library}/{topic}.md"
            relevance: 1.0
            last_updated: "{current_timestamp}"
            cache_hits: 0
    
    - name: "update_master_index"
      action: "update_master_index"
      path: "docs/kb/context7-cache/index.yaml"
      updates:
        libraries:
          "{library}":
            topics: ["{topic}"]
            last_fetched: "{current_timestamp}"
            cache_hits: 0
        total_entries: "{incremented_count}"
        last_updated: "{current_timestamp}"
```

## Error Handling
- Invalid library name format
- Context7 service unavailable
- Library not found in Context7
- Invalid topic parameter
- Token limit exceeded

## Success Criteria
- Library ID successfully resolved (for resolve command)
- Documentation retrieved and displayed (for docs command)
- Clear error messages if issues occur
- User can easily understand and use the results

## Usage Examples
```bash
# Resolve a library name
*context7-resolve react

# Get documentation for a library
*context7-docs react hooks

# Get documentation with specific topic
*context7-docs express.js scalability
```