<!-- Powered by BMAD™ Core -->

# Context7 KB Cleanup Task

## Purpose
Clean up old, unused, or low-value cached documentation from the Context7 knowledge base to maintain optimal performance and storage efficiency.

## Usage
When user types `*context7-kb-cleanup`, execute this workflow to clean up KB content.

## Workflow
1. **Analyze KB Content**: Scan all KB files and metadata
2. **Identify Cleanup Candidates**: Find old, unused, or low-value entries
3. **Calculate Cleanup Impact**: Estimate space savings and hit rate impact
4. **Execute Cleanup**: Remove identified entries (with confirmation)
5. **Update Indexes**: Update all KB indexes after cleanup
6. **Report Results**: Show cleanup statistics and recommendations

## Implementation

### Cleanup Analysis
```yaml
cleanup_analysis:
  steps:
    - name: "scan_kb_content"
      action: "scan_all_kb_files"
      parameters:
        libraries: "docs/kb/context7-cache/libraries/*"
        topics: "docs/kb/context7-cache/topics/*"
        index: "docs/kb/context7-cache/index.yaml"
    
    - name: "identify_cleanup_candidates"
      action: "find_cleanup_targets"
      criteria:
        - name: "old_entries"
          condition: "last_updated < (current_time - 30_days)"
          priority: "medium"
        
        - name: "low_hit_rate"
          condition: "cache_hits < 5 AND age > 7_days"
          priority: "high"
        
        - name: "large_files"
          condition: "file_size > 10MB"
          priority: "low"
        
        - name: "duplicate_content"
          condition: "content_hash_duplicate"
          priority: "medium"
        
        - name: "unused_libraries"
          condition: "total_hits = 0 AND age > 14_days"
          priority: "high"
    
    - name: "calculate_cleanup_impact"
      action: "estimate_cleanup_effects"
      parameters:
        candidates: "{cleanup_candidates}"
        current_hit_rate: "{current_hit_rate}"
        current_size: "{current_size}"
    
    - name: "show_cleanup_preview"
      action: "display_cleanup_plan"
      format: "markdown"
      include_impact_analysis: true
```

### Cleanup Execution
```yaml
cleanup_execution:
  steps:
    - name: "confirm_cleanup"
      action: "request_user_confirmation"
      parameters:
        cleanup_plan: "{cleanup_preview}"
        impact_analysis: "{impact_analysis}"
      options: ["proceed", "modify", "cancel"]
    
    - name: "execute_cleanup"
      action: "remove_cleanup_targets"
      parameters:
        targets: "{confirmed_targets}"
        backup: true
        dry_run: false
    
    - name: "update_indexes"
      action: "rebuild_kb_indexes"
      parameters:
        libraries: true
        topics: true
        master_index: true
        cross_references: true
    
    - name: "validate_cleanup"
      action: "verify_cleanup_results"
      parameters:
        expected_removals: "{cleanup_targets}"
        integrity_check: true
    
    - name: "report_results"
      action: "display_cleanup_report"
      format: "markdown"
      include_statistics: true
```

### Cleanup Criteria
```yaml
cleanup_criteria:
  age_based:
    - name: "very_old"
      condition: "age > 90_days"
      action: "remove"
      priority: "high"
    
    - name: "old"
      condition: "age > 30_days AND hits < 10"
      action: "remove"
      priority: "medium"
    
    - name: "recent_unused"
      condition: "age > 7_days AND hits = 0"
      action: "remove"
      priority: "high"
  
  usage_based:
    - name: "low_hit_rate"
      condition: "hit_rate < 0.1 AND age > 14_days"
      action: "remove"
      priority: "high"
    
    - name: "never_used"
      condition: "hits = 0 AND age > 7_days"
      action: "remove"
      priority: "medium"
  
  size_based:
    - name: "very_large"
      condition: "size > 50MB"
      action: "archive"
      priority: "low"
    
    - name: "large_unused"
      condition: "size > 10MB AND hits < 5"
      action: "remove"
      priority: "medium"
  
  quality_based:
    - name: "duplicate_content"
      condition: "content_hash_duplicate"
      action: "remove_duplicate"
      priority: "medium"
    
    - name: "corrupted_files"
      condition: "file_corruption_detected"
      action: "remove"
      priority: "high"
```

## Output Format

### Cleanup Preview
```markdown
# KB Cleanup Preview

## Cleanup Candidates (12 entries)

### High Priority (5 entries)
1. **MongoDB Aggregation** - `libraries/mongodb/aggregation.md`
   - Age: 45 days, Hits: 0, Size: 2.1MB
   - Reason: Never used, old entry
   - Impact: +2.1MB freed, no hit rate impact

2. **Vue Components** - `libraries/vue/components.md`
   - Age: 38 days, Hits: 2, Size: 1.8MB
   - Reason: Very low usage, old entry
   - Impact: +1.8MB freed, -0.1% hit rate

### Medium Priority (4 entries)
1. **Express Security** - `libraries/express/security.md`
   - Age: 25 days, Hits: 8, Size: 1.2MB
   - Reason: Low usage, approaching age threshold
   - Impact: +1.2MB freed, -0.3% hit rate

### Low Priority (3 entries)
1. **React Architecture** - `libraries/react/architecture.md`
   - Age: 15 days, Hits: 45, Size: 3.2MB
   - Reason: Large file, but good usage
   - Impact: +3.2MB freed, -2.1% hit rate

## Impact Analysis
- **Space Freed**: 8.3MB (12.3% of total)
- **Hit Rate Impact**: -2.5% (from 87.2% to 84.7%)
- **Entries Removed**: 12 of 45 (26.7%)
- **Libraries Affected**: 4 of 8 (50%)

## Recommendations
- ✅ **Proceed with High Priority**: Safe cleanup, good space savings
- ⚠️ **Review Medium Priority**: Consider keeping if security is important
- ❌ **Skip Low Priority**: Good usage, not worth the hit rate loss
```

### Cleanup Report
```markdown
# KB Cleanup Report

## Cleanup Results
- **Entries Removed**: 9 of 12 planned (75%)
- **Space Freed**: 6.1MB (9.2% of total)
- **Hit Rate Impact**: -1.8% (from 87.2% to 85.4%)
- **Cleanup Time**: 2.3 seconds
- **Index Updates**: 4 files updated

## Removed Entries
1. ✅ MongoDB Aggregation (2.1MB, 0 hits)
2. ✅ Vue Components (1.8MB, 2 hits)
3. ✅ Express Security (1.2MB, 8 hits)
4. ✅ Angular Hooks (0.9MB, 1 hit)
5. ✅ Node.js Performance (0.1MB, 0 hits)

## Preserved Entries
1. ⚠️ React Architecture (3.2MB, 45 hits) - Kept due to good usage
2. ⚠️ Vue Router (1.1MB, 12 hits) - Kept due to recent usage
3. ⚠️ MongoDB Queries (0.8MB, 15 hits) - Kept due to good usage

## Recommendations
- ✅ **Cleanup Successful**: Hit rate remains above 85%
- 💡 **Next Cleanup**: Schedule in 30 days
- 📊 **Monitor**: Watch hit rate recovery over next week
- 🔄 **Consider**: Running `*context7-kb-rebuild` to optimize indexes
```

## Error Handling
- KB files not accessible
- Cleanup target still in use
- Index corruption during cleanup
- Insufficient disk space for backup

## Success Criteria
- Cleanup candidates identified correctly
- Impact analysis accurate
- Cleanup executed safely with backup
- Indexes updated correctly
- Hit rate remains above target threshold
