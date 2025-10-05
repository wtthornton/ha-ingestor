<!-- Powered by BMAD™ Core -->

# Context7 KB Integration Utilities

## Purpose
Provides KB-first lookup system for Context7 documentation with intelligent caching, fuzzy matching, and automatic KB storage.

## Core Functions

### KB-First Lookup System

#### check_kb_cache(library, topic)
```yaml
function: check_kb_cache
parameters:
  library: string
  topic: string
returns:
  cached_content: string | null
  metadata: object | null
  cache_hit: boolean
```

#### store_in_kb_cache(library, topic, content, metadata)
```yaml
function: store_in_kb_cache
parameters:
  library: string
  topic: string
  content: string
  metadata: object
returns:
  success: boolean
  file_path: string
```

#### update_kb_metadata(library, topic, hit_count)
```yaml
function: update_kb_metadata
parameters:
  library: string
  topic: string
  hit_count: number
returns:
  success: boolean
```

#### fuzzy_match_kb(library, topic, threshold)
```yaml
function: fuzzy_match_kb
parameters:
  library: string
  topic: string
  threshold: float (default: 0.7)
returns:
  matches: array
  best_match: object | null
```

## Implementation Workflow

### KB-First Documentation Retrieval
```yaml
workflow:
  1. check_kb_cache(library, topic)
     - if cache_hit: return cached_content + update_hit_count
     - if miss: proceed to step 2
  
  2. fuzzy_match_kb(library, topic)
     - if match above threshold: return fuzzy_match + update_hit_count
     - if no match: proceed to step 3
  
  3. call_context7_api(library, topic)
     - get fresh documentation from Context7
     - proceed to step 4
  
  4. store_in_kb_cache(library, topic, content, metadata)
     - store in sharded KB structure
     - update master index
     - return fresh content
```

### KB Cache Structure
```
docs/kb/context7-cache/
├── libraries/
│   ├── {library}/
│   │   ├── {topic}.md
│   │   └── meta.yaml
├── topics/
│   └── {topic}/
│       └── index.yaml
├── index.yaml
└── cross-references.yaml
```

## Error Handling
- KB cache file not found
- Invalid YAML format
- Storage permission issues
- Context7 API failures
- Fuzzy matching errors

## Success Criteria
- KB cache hit rate > 70%
- Response time < 0.15s for cached content
- Automatic KB population from Context7 calls
- Proper metadata tracking and analytics
