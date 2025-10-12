# E2E Testing Guide - HA Ingestor Dashboard

## Overview

This directory contains comprehensive end-to-end tests using Playwright that verify the entire dashboard functionality with **REAL DATA** (no mocks).

## Test Files

- **`dashboard-full.spec.ts`** - Comprehensive full dashboard test suite (RECOMMENDED)
  - Tests all tabs and navigation
  - Verifies real API data
  - Tests interactive features
  - Responsive design tests
  - Performance validation
  - ~40+ test cases

- **`services-tab-phase1.spec.ts`** - Services tab Phase 1 tests
- **`services-tab-phase2.spec.ts`** - Services tab Phase 2 tests
- **`services-tab-phase3.spec.ts`** - Services tab Phase 3 tests

## Prerequisites

### 1. Install Playwright

```bash
cd services/health-dashboard
npm install
npx playwright install
```

### 2. Ensure Backend Services are Running

The dashboard needs to connect to real backend services:

```bash
# From project root
docker-compose up -d
```

Or start individual services as needed.

### 3. Start the Dashboard

```bash
cd services/health-dashboard
npm run dev
```

The dashboard should be accessible at http://localhost:3000

## Running Tests

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Specific Test File

```bash
# Full dashboard tests (recommended)
npx playwright test dashboard-full

# Services tab tests
npx playwright test services-tab-phase1
```

### Run in UI Mode (Interactive)

```bash
npx playwright test --ui
```

This opens a GUI where you can:
- See tests run in real-time
- Debug failed tests
- Inspect DOM
- View network requests

### Run in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

### Run on Specific Browser

```bash
# Chromium
npx playwright test --project=chromium

# Firefox
npx playwright test --project=firefox

# WebKit (Safari)
npx playwright test --project=webkit
```

### Run Single Test

```bash
npx playwright test --grep "should verify NO mock data"
```

### Debug Mode

```bash
npx playwright test --debug
```

## Test Reports

After running tests, view the HTML report:

```bash
npx playwright show-report
```

Reports are also saved to:
- `test-results/` - Screenshots, videos, traces
- `playwright-report/` - HTML report

## Key Test Scenarios

### ✅ Real Data Verification

The tests verify that **NO MOCK DATA** is being used:

1. **API Data Validation**
   - Checks `/api/health` returns recent timestamps
   - Verifies `/api/statistics` returns real data
   - Validates `/api/data-sources` endpoint

2. **Timestamp Freshness**
   - Health data timestamp must be < 5 minutes old
   - UI timestamps must match API timestamps

3. **No Placeholder Detection**
   - Tests scan for common mock indicators
   - Flags suspicious patterns like "Mock", "Fake", "N/A"

### 📊 Tab Coverage

All dashboard tabs are tested:

- **Overview** - System health cards, metrics
- **Services** - Service cards, status, details
- **Dependencies** - Service dependency graph
- **Data Sources** - External API integrations
- **Analytics** - Advanced metrics (placeholder)
- **Alerts** - System alerts and notifications
- **Configuration** - API credentials, service control

### 🎨 Interactive Features

- Dark mode toggle
- Auto-refresh toggle
- Time range selector
- Tab navigation
- Service detail modals
- Configuration forms

### 📱 Responsive Design

Tests run on multiple viewports:
- Mobile (375x667) - iPhone
- Tablet (768x1024) - iPad
- Desktop (1920x1080)

## Test Configuration

Configuration is in `playwright.config.ts`:

```typescript
{
  baseURL: 'http://localhost:3000',
  timeout: 30000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
}
```

## Debugging Failed Tests

### View Last Test Run

```bash
npx playwright show-report
```

### View Test Artifacts

When tests fail, Playwright captures:

1. **Screenshots** - `test-results/*/test-failed-*.png`
2. **Videos** - `test-results/*/video.webm`
3. **Traces** - `test-results/*/trace.zip`

View trace files:

```bash
npx playwright show-trace test-results/*/trace.zip
```

### Common Issues

#### ❌ "Navigation timeout exceeded"

**Problem**: Backend services not running

**Solution**:
```bash
# Start backend services
docker-compose up -d

# Verify services are healthy
curl http://localhost:3000/api/health
```

#### ❌ "expect(received).toBeTruthy() - received: undefined"

**Problem**: API endpoint not returning expected data

**Solution**:
1. Check service logs: `docker-compose logs`
2. Verify API manually: `curl http://localhost:3000/api/health`
3. Check backend configuration

#### ❌ "Timeout waiting for element"

**Problem**: Dashboard taking too long to load

**Solution**:
1. Increase timeout in test
2. Check network performance
3. Verify no errors in browser console

## CI/CD Integration

For GitHub Actions or other CI:

```yaml
- name: Install Playwright
  run: |
    cd services/health-dashboard
    npm ci
    npx playwright install --with-deps

- name: Run E2E Tests
  run: |
    cd services/health-dashboard
    npm run test:e2e

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: playwright-report
    path: services/health-dashboard/playwright-report/
```

## Writing New Tests

### Test Structure

```typescript
test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await page.click('button:has-text("Services")');
    
    // Act
    await page.click('button:has-text("View Details")').first();
    
    // Assert
    await expect(page.locator('text=Details')).toBeVisible();
  });
});
```

### Best Practices

1. **Wait for Network Idle**: `await page.waitForLoadState('networkidle')`
2. **Use Specific Selectors**: Prefer text selectors over CSS
3. **Add Timeouts**: `{ timeout: 10000 }` for slow operations
4. **Verify Real Data**: Always check timestamps and data freshness
5. **Console Logs**: Add `console.log()` for debugging
6. **Screenshot on Failure**: Automatically captured by Playwright

## Useful Commands

```bash
# List all tests
npx playwright test --list

# Run tests matching pattern
npx playwright test --grep "real data"

# Run tests in specific file
npx playwright test dashboard-full

# Update snapshots
npx playwright test --update-snapshots

# Generate test code (record interactions)
npx playwright codegen http://localhost:3000

# Check Playwright version
npx playwright --version
```

## Test Coverage

Current coverage:

- ✅ All 7 tabs tested
- ✅ API endpoint validation (3 endpoints)
- ✅ Real data verification
- ✅ Interactive features (dark mode, refresh, etc.)
- ✅ Responsive design (3 viewports)
- ✅ Navigation and routing
- ✅ Performance checks
- ✅ Error handling

## Support

For issues or questions:

1. Check test output: `npx playwright show-report`
2. Review test artifacts in `test-results/`
3. Enable debug mode: `npx playwright test --debug`
4. Check backend logs: `docker-compose logs`

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Tests](https://playwright.dev/docs/debug)
- [Test Selectors](https://playwright.dev/docs/selectors)

