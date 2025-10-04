<!-- Powered by BMAD™ Core -->

# Context7 KB Search Task

## Purpose
Search the local knowledge base for documentation content, libraries, and topics with intelligent matching and relevance scoring.

## Usage
When user types `*context7-kb-search {query}`, execute this workflow to search KB content.

## Workflow
1. **Parse Search Query**: Extract search terms and parameters
2. **Multi-Source Search**: Search libraries, topics, and content
3. **Relevance Scoring**: Score results by relevance
4. **Format Results**: Display results in organized format
5. **Provide Suggestions**: Suggest related searches

## Implementation

### Search System
```yaml
kb_search:
  steps:
    - name: "parse_search_query"
      action: "parse_search_parameters"
      parameters:
        query: "{user_query}"
        type: "all"  # library, topic, content, all
        limit: 10
    
    - name: "search_libraries"
      action: "search_library_names"
      parameters:
        query: "{search_terms}"
        fuzzy_match: true
        confidence_threshold: 0.5
    
    - name: "search_topics"
      action: "search_topic_names"
      parameters:
        query: "{search_terms}"
        fuzzy_match: true
        confidence_threshold: 0.5
    
    - name: "search_content"
      action: "search_documentation_content"
      parameters:
        query: "{search_terms}"
        libraries: "{matched_libraries}"
        topics: "{matched_topics}"
    
    - name: "score_relevance"
      action: "calculate_relevance_scores"
      parameters:
        results: "{all_search_results}"
        query: "{original_query}"
        scoring_factors: ["exact_match", "fuzzy_match", "content_relevance"]
    
    - name: "format_results"
      action: "format_search_results"
      format: "markdown"
      sections: ["exact_matches", "fuzzy_matches", "content_matches", "suggestions"]
    
    - name: "display_results"
      action: "show_search_results"
      limit: "{search_limit}"
      include_suggestions: true
```

### Search Types
```yaml
search_types:
  library_search:
    sources: ["libraries/*/meta.yaml"]
    fields: ["name", "description", "context7_id"]
    fuzzy_matching: true
    cross_references: true
  
  topic_search:
    sources: ["topics/*/index.yaml"]
    fields: ["name", "description", "category"]
    fuzzy_matching: true
    cross_references: true
  
  content_search:
    sources: ["libraries/*/*.md", "topics/*/*.md"]
    fields: ["title", "content", "code_examples"]
    full_text_search: true
    snippet_extraction: true
```

### Relevance Scoring
```yaml
relevance_scoring:
  scoring_factors:
    exact_match:
      weight: 0.4
      description: "Exact string match"
    
    fuzzy_match:
      weight: 0.3
      description: "Fuzzy string match"
    
    content_relevance:
      weight: 0.2
      description: "Content relevance score"
    
    usage_frequency:
      weight: 0.1
      description: "Usage frequency bonus"
  
  scoring_algorithm:
    - name: "calculate_exact_match_score"
      weight: 0.4
      formula: "exact_matches / total_terms"
    
    - name: "calculate_fuzzy_match_score"
      weight: 0.3
      formula: "fuzzy_confidence * fuzzy_matches / total_terms"
    
    - name: "calculate_content_relevance"
      weight: 0.2
      formula: "content_matches / total_content_length"
    
    - name: "calculate_usage_bonus"
      weight: 0.1
      formula: "log(cache_hits + 1) / 10"
```

## Output Format

### Search Results
```markdown
# KB Search Results for "react hooks"

## Exact Matches (2 results)
1. **React Hooks** - `libraries/react/hooks.md`
   - Relevance: 1.0
   - Cache Hits: 45
   - Last Updated: 2025-01-27T09:15:00Z
   - Snippet: React Hooks are functions that let you "hook into" React state and lifecycle features...

2. **Hooks Topic** - `topics/hooks/index.yaml`
   - Relevance: 0.9
   - Related Libraries: React, Vue, Angular
   - Cross-References: state-management, lifecycle

## Fuzzy Matches (3 results)
1. **React Components** - `libraries/react/components.md`
   - Relevance: 0.7
   - Match Reason: "hooks" found in component lifecycle content
   - Cache Hits: 32

2. **Vue Composition API** - `libraries/vue/composition-api.md`
   - Relevance: 0.6
   - Match Reason: Similar to React hooks concept
   - Cache Hits: 18

## Content Matches (5 results)
1. **React Hooks Documentation** - `libraries/react/hooks.md`
   - Relevance: 0.8
   - Snippet: "useState hook allows you to add state to functional components..."
   - Line: 45-47

2. **React Architecture** - `libraries/react/architecture.md`
   - Relevance: 0.6
   - Snippet: "Hooks provide a way to use state and other React features..."
   - Line: 123-125

## Suggestions
- Try searching for: "state management", "useEffect", "custom hooks"
- Related topics: "components", "lifecycle", "testing"
- Popular libraries: "redux", "react-query", "swr"
```

## Error Handling
- Invalid search query
- No results found
- KB files not accessible
- Search index corruption

## Success Criteria
- Search results displayed with relevance scoring
- Multiple search types supported (library, topic, content)
- Fuzzy matching works correctly
- Suggestions provided for related searches
- User can easily find relevant documentation
