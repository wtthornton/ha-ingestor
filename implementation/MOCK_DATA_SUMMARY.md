# Mock Data Quick Reference

**See full analysis:** [implementation/analysis/MOCK_DATA_ANALYSIS.md](analysis/MOCK_DATA_ANALYSIS.md)

## Critical Issues (🔴 Fix Immediately)

| Component | Location | Issue | Action Required |
|-----------|----------|-------|-----------------|
| **Data Sources Panel** | `health-dashboard/src/components/DataSourcesPanel.tsx:26` | Uses `getMockDataSources()` instead of real API | Create `/api/v1/data-sources/status` endpoint |
| **Analytics Metrics** | `data-api/src/analytics_endpoints.py:266-280` | 3 of 4 metrics use `generate_mock_series()` | Store API times, DB latency, error rates in InfluxDB |
| **Docker Management** | `admin-api/src/docker_service.py:400-436` | Returns mock containers when Docker unavailable | Fix Docker socket access, remove mock fallback |

## High Priority Issues (🟡 Next Sprint)

| Component | Location | Issue |
|-----------|----------|-------|
| **Service Restart** | `admin-api/src/service_controller.py:158-195` | Placeholder implementation, returns instructions not actions |
| **Realtime Metrics** | `data-api/src/monitoring_endpoints.py:122` | Incomplete active source detection |
| **Quality History** | `enrichment-pipeline/src/quality_dashboard.py:530-560` | Historical trends are fabricated |

## Medium Priority Issues (🟢 Future)

| Component | Location | Issue |
|-----------|----------|-------|
| **MetricsChart** | `health-dashboard/src/components/MetricsChart.tsx:46-62` | Generates sample data as fallback |
| **Data Retention** | `data-retention/src/*.py` (multiple files) | Mock implementations when InfluxDB unavailable |
| **Storage Monitor** | `data-retention/src/storage_monitor.py:186` | Returns `None` placeholder |

## Files to Delete (Potentially Unused)

- `services/health-dashboard/src/mocks/dataSourcesMock.ts` - Once real endpoint implemented
- `services/health-dashboard/src/mocks/alertsMock.ts` - May be unused (verify)
- `services/health-dashboard/src/mocks/analyticsMock.ts` - May be partially unused (verify)

## Quick Fix Checklist

### To Remove DataSources Mock:

- [ ] Create backend service to aggregate data source status
- [ ] Implement `/api/v1/data-sources/status` endpoint in data-api
- [ ] Update `DataSourcesPanel.tsx` to call real endpoint (replace line 26)
- [ ] Delete `mocks/dataSourcesMock.ts`
- [ ] Test with real external services (weather, sports, etc.)

### To Complete Analytics Metrics:

- [ ] Add API response time tracking to shared middleware
- [ ] Store response times in InfluxDB `api_metrics` measurement
- [ ] Add DB write latency tracking to InfluxDB wrapper
- [ ] Implement error tracking in InfluxDB `error_events` measurement
- [ ] Replace `generate_mock_series()` calls with real queries
- [ ] Calculate actual uptime from service health data (line 216)

### To Fix Docker Management:

- [ ] Ensure `/var/run/docker.sock` mounted in docker-compose
- [ ] Test Docker API access from admin-api container
- [ ] Remove `_get_mock_containers()` method or mark as fallback
- [ ] Implement real service restart operations
- [ ] Add clear UI indicators when Docker unavailable

## Search Patterns Used

```bash
# Find mock/fake/stub patterns
grep -r "mock|Mock|fake|Fake|dummy|stub" services/

# Find placeholder/sample data
grep -r "placeholder|sample data|test data" services/

# Find TODO comments about mocks
grep -r "TODO.*mock|FIXME.*mock" services/

# Find NotImplementedError
grep -r "NotImplementedError" services/

# Find mock data generators
grep -r "generate_mock|generate_sample" services/
```

## Impact Assessment

| Area | Real Data % | Mock Data % | User Impact |
|------|-------------|-------------|-------------|
| **Event Streaming** | 100% | 0% | ✅ No issues |
| **Device/Entity Browser** | 100% | 0% | ✅ No issues |
| **Sports Data** | 100% | 0% | ✅ No issues |
| **Analytics Dashboard** | 25% | 75% | ⚠️ Misleading metrics |
| **Data Sources Status** | 0% | 100% | ❌ Fake status shown |
| **Docker Management** | Variable | Variable | ⚠️ Broken when Docker unavailable |
| **Service Controls** | 0% | 100% | ❌ Buttons don't work |

## Estimated Effort

| Issue | Effort | Complexity | Dependencies |
|-------|--------|------------|--------------|
| Data Sources API | 2-3 days | Medium | Service status aggregation |
| Analytics Metrics | 3-4 days | High | InfluxDB schema changes, metrics collection |
| Docker Management | 1-2 days | Medium | Docker socket access, deployment config |
| Service Restart | 1 day | Low | Docker API integration |
| Quality History | 2 days | Medium | InfluxDB storage implementation |

**Total Estimated Effort:** 9-12 days for critical + high priority issues

---

**Status:** Analysis complete. Ready for implementation planning.

