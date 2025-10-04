<!-- Powered by BMAD™ Core -->

# Context7 KB Status Task

## Purpose
Show comprehensive knowledge base statistics, hit rates, and performance metrics for the Context7 KB cache system.

## Usage
When user types `*context7-kb-status`, execute this workflow to display KB statistics.

## Workflow
1. **Read KB Index**: Load master index file
2. **Calculate Statistics**: Compute hit rates and performance metrics
3. **Format Output**: Display statistics in user-friendly format
4. **Show Recommendations**: Provide optimization suggestions

## Implementation

### KB Status Display
```yaml
kb_status:
  steps:
    - name: "load_kb_index"
      action: "read_yaml_file"
      path: "docs/kb/context7-cache/index.yaml"
    
    - name: "calculate_statistics"
      action: "compute_kb_stats"
      parameters:
        total_entries: "{index.total_entries}"
        total_hits: "{index.cache_stats.total_hits}"
        total_misses: "{index.cache_stats.total_misses}"
        total_size: "{index.total_size}"
    
    - name: "format_output"
      action: "format_status_display"
      format: "markdown"
      sections:
        - "overview"
        - "performance_metrics"
        - "top_libraries"
        - "top_topics"
        - "recommendations"
    
    - name: "display_results"
      action: "show_formatted_status"
      include_recommendations: true
```

### Statistics Calculation
```yaml
statistics_calculation:
  hit_rate: "{total_hits / (total_hits + total_misses) * 100}"
  avg_response_time: "{index.cache_stats.avg_response_time}"
  cache_efficiency: "{total_hits / total_entries * 100}"
  size_utilization: "{current_size / max_cache_size * 100}"
  
  top_libraries:
    calculation: "sort_by_cache_hits"
    limit: 5
    include_metrics: true
  
  top_topics:
    calculation: "sort_by_usage_frequency"
    limit: 5
    include_metrics: true
  
  recommendations:
    - condition: "hit_rate < 70%"
      suggestion: "Consider running KB cleanup to remove unused entries"
    - condition: "size_utilization > 80%"
      suggestion: "Consider increasing cache size or running cleanup"
    - condition: "avg_response_time > 0.2s"
      suggestion: "Consider optimizing KB structure or running rebuild"
```

## Output Format

### Overview Section
```markdown
# Context7 Knowledge Base Status

## Overview
- **Total Entries**: 45
- **Total Size**: 12.3MB / 100MB (12.3%)
- **Hit Rate**: 87.2%
- **Average Response Time**: 0.15s
- **Last Updated**: 2025-01-27T15:01:00Z
```

### Performance Metrics
```markdown
## Performance Metrics
- **Cache Hits**: 156
- **Cache Misses**: 23
- **Context7 Calls**: 23
- **Fuzzy Matches**: 12
- **Cross-References**: 8
- **Cleanup Operations**: 2
```

### Top Libraries
```markdown
## Top Libraries
1. **React** - 45 hits, 2.3MB
2. **Express** - 32 hits, 1.8MB
3. **MongoDB** - 28 hits, 1.2MB
4. **Vue** - 15 hits, 0.9MB
5. **Node.js** - 12 hits, 0.7MB
```

### Top Topics
```markdown
## Top Topics
1. **Hooks** - 67 hits, 3.2MB
2. **Routing** - 45 hits, 2.1MB
3. **Security** - 38 hits, 1.9MB
4. **Testing** - 29 hits, 1.4MB
5. **Performance** - 22 hits, 1.1MB
```

### Recommendations
```markdown
## Recommendations
- ✅ **Hit Rate Excellent**: 87.2% exceeds target of 70%
- ✅ **Response Time Good**: 0.15s meets target
- ⚠️ **Size Growth**: Consider cleanup if approaching 80MB
- 💡 **Optimization**: Run `*context7-kb-rebuild` monthly
```

## Error Handling
- KB index file not found
- Invalid YAML format in index
- Missing statistics data
- Calculation errors

## Success Criteria
- KB statistics displayed accurately
- Performance metrics calculated correctly
- Recommendations provided based on current state
- User can understand KB health and performance
